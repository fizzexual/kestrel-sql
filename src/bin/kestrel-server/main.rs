//! `kestrel-server`: PostgreSQL v3 wire protocol front end for KestrelSQL.
//! Plain TCP, SCRAM-SHA-256, no TLS: keep it on loopback or behind an SSH tunnel / stunnel.
//! See docs/SERVER.md.
mod backend;
mod memory;
mod scram;
mod session;
mod text;
mod wire;

use backend::{ArchiveBackend, Backend};
use kestrel_sql::Database;
use kestrel_sql::archive::Archive;
use kestrel_sql::live::LiveArchive;
use memory::Budget;
use session::{Shared, Slot, log, serve};
use std::io::{self, Write};
use std::net::{TcpListener, ToSocketAddrs};
use std::path::PathBuf;
use std::process::ExitCode;
use std::sync::Arc;
use std::sync::Mutex;
use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use wire::Fatal;

const USAGE: &str = "\
kestrel-server: PostgreSQL wire protocol server for KestrelSQL (no TLS)

usage:
  kestrel-server --db DIR --password-file FILE [options]
  kestrel-server --archive DIR [--columns ts,value,device] [--table events] --password-file FILE [options]

options:
  --db DIR              serve a Database (WAL in DIR); exactly one of --db / --archive
  --archive DIR         serve a LiveArchive: SELECT and INSERT into one fixed table
  --columns A,B,C       archive column names (default ts,value,device)
  --table NAME          archive table name (default events)
  --password-file FILE  first line is the password (required)
  --user NAME           the only accepted user name (default kestrel)
  --listen ADDR         default 127.0.0.1:5433 (port 0 picks a free port)
  --allow-remote        allow a non-loopback --listen address (there is still no TLS)
  --max-connections N   authenticated sessions, default 64; further logins get SQLSTATE 53300
  --max-memory MIB      memory all requests in flight may use together (message buffers, parsed
                        statements, results), default 1024; a request that cannot get its share
                        fails with SQLSTATE 53200 (busy, retry) or 54000 (too big, never fits)
";

struct Config {
    db: Option<PathBuf>,
    archive: Option<PathBuf>,
    columns: String,
    table: String,
    password_file: Option<PathBuf>,
    user: String,
    listen: String,
    allow_remote: bool,
    max_connections: usize,
    /// Transient memory budget in MiB.
    max_memory: usize,
}

fn parse_args() -> Result<Option<Config>, String> {
    let mut config = Config {
        db: None,
        archive: None,
        columns: "ts,value,device".into(),
        table: "events".into(),
        password_file: None,
        user: "kestrel".into(),
        listen: "127.0.0.1:5433".into(),
        allow_remote: false,
        max_connections: 64,
        max_memory: 1024,
    };
    let (mut columns_set, mut table_set) = (false, false);
    let mut args = std::env::args().skip(1);
    while let Some(flag) = args.next() {
        let mut value = || args.next().ok_or_else(|| format!("{flag} needs a value"));
        match flag.as_str() {
            "--help" | "-h" => return Ok(None),
            "--db" => config.db = Some(value()?.into()),
            "--archive" => config.archive = Some(value()?.into()),
            "--columns" => {
                config.columns = value()?;
                columns_set = true;
            }
            "--table" => {
                config.table = value()?;
                table_set = true;
            }
            "--password-file" => config.password_file = Some(value()?.into()),
            "--user" => config.user = value()?,
            "--listen" => config.listen = value()?,
            "--allow-remote" => config.allow_remote = true,
            "--max-connections" => {
                config.max_connections = value()?
                    .parse()
                    .ok()
                    .filter(|n| *n >= 1)
                    .ok_or("--max-connections needs an integer >= 1")?;
            }
            "--max-memory" => {
                // At most 2^30 MiB, so that the byte count cannot overflow on a 64-bit build.
                config.max_memory = value()?
                    .parse()
                    .ok()
                    .filter(|n| (1..=1 << 30).contains(n))
                    .ok_or("--max-memory needs a whole number of MiB, 1 or more")?;
            }
            other => return Err(format!("unknown argument {other}")),
        }
    }
    match (&config.db, &config.archive) {
        (Some(_), Some(_)) | (None, None) => {
            return Err("choose exactly one of --db DIR or --archive DIR".into());
        }
        (Some(_), None) if columns_set || table_set => {
            return Err("--columns and --table need --archive".into());
        }
        _ => {}
    }
    if config.user.is_empty() {
        return Err("--user must not be empty".into());
    }
    Ok(Some(config))
}

/// First line of the file, trailing newline removed. Printable ASCII only: the server does not
/// implement SASLprep, so other characters could not be matched against what a client sends.
fn read_password(path: &PathBuf) -> Result<Vec<u8>, String> {
    let raw = std::fs::read(path)
        .map_err(|e| format!("cannot read the password file {}: {e}", path.display()))?;
    let line = raw.split(|b| *b == b'\n').next().unwrap_or_default();
    let line = line.strip_suffix(b"\r").unwrap_or(line);
    if line.is_empty() {
        return Err("the first line of the password file is empty".into());
    }
    if !line.iter().all(|b| (0x20..0x7f).contains(b)) {
        return Err("the password must be printable ASCII (no SASLprep support)".into());
    }
    Ok(line.to_vec())
}

fn run() -> Result<(), String> {
    let Some(config) = parse_args()? else {
        print!("{USAGE}");
        return Ok(());
    };
    let password_file = config
        .password_file
        .as_ref()
        .ok_or("--password-file is required: the server never runs without authentication")?;
    let password = read_password(password_file)?;

    let addrs: Vec<_> = config
        .listen
        .to_socket_addrs()
        .map_err(|e| format!("invalid --listen {}: {e}", config.listen))?
        .collect();
    let remote = addrs.iter().any(|a| !a.ip().is_loopback());
    if remote && !config.allow_remote {
        return Err(format!(
            "refusing to listen on {}: not a loopback address and there is no TLS. \
             Use 127.0.0.1 with an SSH tunnel or stunnel, or pass --allow-remote.",
            config.listen
        ));
    }

    let mut salt = vec![0u8; 16];
    getrandom::fill(&mut salt).map_err(|e| format!("random source unavailable: {e}"))?;
    let mut mock_secret = [0u8; 32];
    getrandom::fill(&mut mock_secret).map_err(|e| format!("random source unavailable: {e}"))?;
    let verifier = scram::Verifier::derive(&password, salt, scram::ITERATIONS);
    drop(password);

    let backend = if let Some(dir) = &config.db {
        let db = Database::open(dir).map_err(|e| e.to_string())?;
        if db.recovered_tail_bytes() > 0 {
            eprintln!(
                "recovered: cut {} bytes of an unfinished last write from the log",
                db.recovered_tail_bytes()
            );
        }
        Backend::Db(Mutex::new(db))
    } else {
        let dir = config.archive.as_ref().unwrap();
        let columns: Vec<String> = config
            .columns
            .split(',')
            .map(|c| c.trim().to_ascii_lowercase())
            .collect();
        let names: Vec<&str> = columns.iter().map(String::as_str).collect();
        let archive = Archive::open(dir, &config.table, &names).map_err(|e| e.to_string())?;
        Backend::Archive(ArchiveBackend {
            live: LiveArchive::new(archive).map_err(|e| e.to_string())?,
            table: config.table.to_ascii_lowercase(),
            columns,
        })
    };

    // Bind the addresses that were just checked, not the text again: resolving a name twice can
    // give different answers.
    let listener = TcpListener::bind(&addrs[..])
        .map_err(|e| format!("cannot listen on {}: {e}", config.listen))?;
    let local = listener.local_addr().map_err(|e| e.to_string())?;
    if config.allow_remote && !local.ip().is_loopback() {
        eprintln!(
            "WARNING: listening on {local} without TLS; passwords are protected by SCRAM but queries and results travel in clear text"
        );
    }
    let version = env!("CARGO_PKG_VERSION");
    let shared = Arc::new(Shared {
        backend,
        verifier,
        mock_secret,
        user: config.user.clone(),
        server_version: format!("16.0 (KestrelSQL {version})"),
        active: Arc::new(AtomicUsize::new(0)),
        max_sessions: config.max_connections,
        preauth: Arc::new(AtomicUsize::new(0)),
        // Sockets still in startup or authentication each hold a thread for at most ten
        // seconds but do not count against --max-connections.
        preauth_cap: (2 * config.max_connections).max(16),
        budget: Budget::new(config.max_memory.saturating_mul(memory::MIB)),
    });
    // Hand-assembled so the keys keep the documented order.
    println!(
        "{{\"listening\":{},\"backend\":{},\"version\":{}}}",
        serde_json::Value::from(local.to_string()),
        serde_json::Value::from(shared.backend.name()),
        serde_json::Value::from(version)
    );
    io::stdout().flush().map_err(|e| e.to_string())?;

    let next_id = AtomicU64::new(1);
    for stream in listener.incoming() {
        let stream = match stream {
            Ok(stream) => stream,
            Err(e) => {
                eprintln!("accept failed: {e}");
                std::thread::sleep(std::time::Duration::from_millis(50));
                continue;
            }
        };
        let id = next_id.fetch_add(1, Ordering::Relaxed);
        // Too many sockets still authenticating: drop this one without a word (it has not
        // said who it is yet, and answering costs a thread).
        let Some(pre) = Slot::acquire(&shared.preauth, shared.preauth_cap) else {
            continue;
        };
        let shared = Arc::clone(&shared);
        let spawned = std::thread::Builder::new()
            .name(format!("conn-{id}"))
            .spawn(move || {
                match stream.peer_addr() {
                    Ok(peer) => log(id, &format!("open from {peer}")),
                    Err(_) => log(id, "open"),
                }
                let reason = match serve(stream, &shared, id, pre) {
                    Ok(()) => "closed".to_string(),
                    Err(Fatal::Io(e)) => format!("closed (io: {:?})", e.kind()),
                    Err(Fatal::Pg(e)) => format!("closed (error {})", e.code),
                };
                log(id, &reason);
                // Everything this connection reserved is back by now: what is left is held by
                // other connections, so the last connection to close reports 0.
                log(
                    id,
                    &format!(
                        "transient memory: {} in use, peak {}, limit {} bytes",
                        shared.budget.used(),
                        shared.budget.peak(),
                        shared.budget.limit()
                    ),
                );
            });
        if let Err(e) = spawned {
            // The closure, and the slot it owns, were dropped.
            eprintln!("cannot start a connection thread: {e}");
        }
    }
    Ok(())
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(message) => {
            eprintln!("kestrel-server: {message}");
            ExitCode::from(2)
        }
    }
}
