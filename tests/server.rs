//! End-to-end tests of `kestrel-server`: the real binary, a raw-socket PostgreSQL client
//! (startup, SCRAM, simple and extended query) and the failure paths a production server meets.
use sha2::{Digest, Sha256};
use std::io::{BufRead, BufReader, Read, Write};
use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, ChildStdout, Command, Stdio};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::{Duration, Instant};

const PASSWORD: &str = "correct horse battery staple 7";
const USER: &str = "kestrel";

// ---- client-side crypto (independent of the server's implementation) ----------------------

fn hmac(key: &[u8], message: &[u8]) -> [u8; 32] {
    let mut block = [0u8; 64];
    if key.len() > 64 {
        block[..32].copy_from_slice(&Sha256::digest(key));
    } else {
        block[..key.len()].copy_from_slice(key);
    }
    let mut inner = Sha256::new();
    inner.update(block.map(|b| b ^ 0x36));
    inner.update(message);
    let mut outer = Sha256::new();
    outer.update(block.map(|b| b ^ 0x5c));
    outer.update(inner.finalize());
    outer.finalize().into()
}

fn pbkdf2(password: &[u8], salt: &[u8], iterations: u32) -> [u8; 32] {
    let mut first = salt.to_vec();
    first.extend_from_slice(&1u32.to_be_bytes());
    let mut u = hmac(password, &first);
    let mut t = u;
    for _ in 1..iterations {
        u = hmac(password, &u);
        for (a, b) in t.iter_mut().zip(u) {
            *a ^= b;
        }
    }
    t
}

const B64: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

fn b64(data: &[u8]) -> String {
    let mut out = String::new();
    for chunk in data.chunks(3) {
        let n = (u32::from(chunk[0]) << 16)
            | (u32::from(*chunk.get(1).unwrap_or(&0)) << 8)
            | u32::from(*chunk.get(2).unwrap_or(&0));
        for i in 0..4 {
            if i <= chunk.len() {
                out.push(B64[(n >> (18 - 6 * i)) as usize & 63] as char);
            } else {
                out.push('=');
            }
        }
    }
    out
}

fn unb64(text: &str) -> Vec<u8> {
    let mut out = Vec::new();
    let (mut acc, mut bits) = (0u32, 0);
    for c in text.bytes().filter(|c| *c != b'=') {
        acc = (acc << 6) | B64.iter().position(|b| *b == c).unwrap() as u32;
        bits += 6;
        if bits >= 8 {
            bits -= 8;
            out.push((acc >> bits) as u8);
        }
    }
    out
}

// ---- server harness ------------------------------------------------------------------------

static COUNTER: AtomicUsize = AtomicUsize::new(0);

struct TempDir(PathBuf);
impl TempDir {
    fn new() -> Self {
        let nanos = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let dir = std::env::temp_dir().join(format!(
            "kestrel-server-test-{}-{}-{nanos}",
            std::process::id(),
            COUNTER.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir_all(&dir).unwrap();
        std::fs::write(dir.join("pw"), format!("{PASSWORD}\n")).unwrap();
        Self(dir)
    }
    fn path(&self) -> &Path {
        &self.0
    }
    fn arg(&self, name: &str) -> String {
        self.0.join(name).to_string_lossy().into_owned()
    }
}
impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(&self.0);
    }
}

struct Server {
    child: Child,
    addr: SocketAddr,
    json: serde_json::Value,
    stderr: PathBuf,
    _stdout: BufReader<ChildStdout>,
}

impl Server {
    /// Starts the binary in `dir` (password file `pw` already there), listening on port 0.
    fn start(dir: &TempDir, extra: &[&str]) -> Self {
        static RUN: AtomicUsize = AtomicUsize::new(0);
        let stderr = dir.path().join(format!(
            "stderr-{}.log",
            RUN.fetch_add(1, Ordering::Relaxed)
        ));
        let mut args = vec!["--password-file".to_string(), dir.arg("pw")];
        if !extra.contains(&"--listen") {
            args.extend(["--listen".into(), "127.0.0.1:0".into()]);
        }
        args.extend(extra.iter().map(|a| a.to_string()));
        let mut child = Command::new(env!("CARGO_BIN_EXE_kestrel-server"))
            .args(&args)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(std::fs::File::create(&stderr).unwrap())
            .spawn()
            .unwrap();
        let mut stdout = BufReader::new(child.stdout.take().unwrap());
        let mut line = String::new();
        stdout.read_line(&mut line).unwrap();
        let json: serde_json::Value = serde_json::from_str(&line)
            .unwrap_or_else(|_| panic!("no JSON line from server, got {line:?}"));
        let addr = json["listening"].as_str().unwrap().parse().unwrap();
        Self {
            child,
            addr,
            json,
            stderr,
            _stdout: stdout,
        }
    }
    fn db(dir: &TempDir, extra: &[&str]) -> Self {
        let path = dir.arg("db");
        let mut args = vec!["--db", &path];
        args.extend_from_slice(extra);
        Self::start(dir, &args)
    }
    fn archive(dir: &TempDir, extra: &[&str]) -> Self {
        let path = dir.arg("archive");
        let mut args = vec!["--archive", &path];
        args.extend_from_slice(extra);
        Self::start(dir, &args)
    }
    fn login(&self) -> Client {
        Client::login(self.addr, USER, PASSWORD).unwrap_or_else(|e| panic!("login failed: {e:?}"))
    }
    fn log(&self) -> String {
        std::fs::read_to_string(&self.stderr).unwrap_or_default()
    }
    fn stop(mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
    /// True while the process has not exited.
    fn alive(&mut self) -> bool {
        self.child.try_wait().unwrap().is_none()
    }
}
impl Drop for Server {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

// ---- raw PostgreSQL client -----------------------------------------------------------------

#[derive(Debug, Clone, PartialEq)]
struct PgErr {
    severity: String,
    code: String,
    message: String,
}

fn cstr(buf: &[u8], pos: &mut usize) -> String {
    let end = buf[*pos..].iter().position(|b| *b == 0).unwrap() + *pos;
    let s = String::from_utf8_lossy(&buf[*pos..end]).into_owned();
    *pos = end + 1;
    s
}

fn parse_error(body: &[u8]) -> PgErr {
    let mut err = PgErr {
        severity: String::new(),
        code: String::new(),
        message: String::new(),
    };
    let mut pos = 0;
    while body[pos] != 0 {
        let field = body[pos];
        pos += 1;
        let value = cstr(body, &mut pos);
        match field {
            b'S' => err.severity = value,
            b'C' => err.code = value,
            b'M' => err.message = value,
            _ => {}
        }
    }
    err
}

#[derive(Debug, Default)]
struct Reply {
    /// (name, type oid, format code)
    fields: Vec<(String, u32, i16)>,
    rows: Vec<Vec<Option<Vec<u8>>>>,
    tags: Vec<String>,
    /// Every message tag received, in order.
    seen: Vec<u8>,
    error: Option<PgErr>,
    status: u8,
    param_oids: Vec<u32>,
}

impl Reply {
    fn text(&self) -> Vec<Vec<String>> {
        self.rows
            .iter()
            .map(|r| {
                r.iter()
                    .map(|c| {
                        c.as_ref()
                            .map_or("NULL".into(), |b| String::from_utf8_lossy(b).into_owned())
                    })
                    .collect()
            })
            .collect()
    }
    fn code(&self) -> &str {
        self.error.as_ref().map_or("", |e| e.code.as_str())
    }
}

struct Client {
    stream: TcpStream,
}

type Msg = (u8, Vec<u8>);

fn i32b(n: i32) -> [u8; 4] {
    n.to_be_bytes()
}
fn i16b(n: i16) -> [u8; 2] {
    n.to_be_bytes()
}

impl Client {
    fn connect_raw(addr: SocketAddr) -> Client {
        let stream = TcpStream::connect(addr).unwrap();
        stream
            .set_read_timeout(Some(Duration::from_secs(20)))
            .unwrap();
        stream.set_nodelay(true).unwrap();
        Client { stream }
    }

    fn send_startup(&mut self, user: &str) {
        let mut body = i32b(196608).to_vec();
        for (k, v) in [
            ("user", user),
            ("database", "kestrel"),
            ("client_encoding", "UTF8"),
        ] {
            body.extend_from_slice(k.as_bytes());
            body.push(0);
            body.extend_from_slice(v.as_bytes());
            body.push(0);
        }
        body.push(0);
        let mut packet = i32b(body.len() as i32 + 4).to_vec();
        packet.extend(body);
        self.stream.write_all(&packet).unwrap();
    }

    fn send(&mut self, tag: u8, body: &[u8]) {
        let mut packet = vec![tag];
        packet.extend_from_slice(&i32b(body.len() as i32 + 4));
        packet.extend_from_slice(body);
        self.stream.write_all(&packet).unwrap();
    }

    /// `None` when the server closed the connection (EOF or reset).
    fn recv(&mut self) -> Option<Msg> {
        let mut head = [0u8; 5];
        self.stream.read_exact(&mut head).ok()?;
        let len = u32::from_be_bytes(head[1..].try_into().unwrap()) as usize;
        let mut body = vec![0u8; len - 4];
        self.stream.read_exact(&mut body).ok()?;
        Some((head[0], body))
    }

    fn login(addr: SocketAddr, user: &str, password: &str) -> Result<Client, PgErr> {
        let mut c = Client::connect_raw(addr);
        c.send_startup(user);
        let (tag, body) = c.recv().expect("server closed during startup");
        if tag == b'E' {
            return Err(parse_error(&body));
        }
        assert_eq!(
            (tag, i32::from_be_bytes(body[..4].try_into().unwrap())),
            (b'R', 10)
        );
        assert_eq!(
            &body[4..],
            b"SCRAM-SHA-256\0\0",
            "only one mechanism, no channel binding"
        );

        let nonce = b64(&[7u8; 15]);
        let first_bare = format!("n=,r={nonce}");
        let first = format!("n,,{first_bare}");
        let mut init = b"SCRAM-SHA-256\0".to_vec();
        init.extend_from_slice(&i32b(first.len() as i32));
        init.extend_from_slice(first.as_bytes());
        c.send(b'p', &init);
        let (tag, body) = c.recv().expect("closed after SASLInitialResponse");
        if tag == b'E' {
            return Err(parse_error(&body));
        }
        assert_eq!(i32::from_be_bytes(body[..4].try_into().unwrap()), 11);
        let server_first = String::from_utf8(body[4..].to_vec()).unwrap();
        let attr = |name: &str| {
            server_first
                .split(',')
                .find_map(|p| p.strip_prefix(name))
                .unwrap()
                .to_string()
        };
        let (combined, salt, iterations) =
            (attr("r="), unb64(&attr("s=")), attr("i=").parse().unwrap());
        assert!(combined.starts_with(&nonce));
        assert_eq!(iterations, 4096);
        let salted = pbkdf2(password.as_bytes(), &salt, iterations);
        let client_key = hmac(&salted, b"Client Key");
        let stored: [u8; 32] = Sha256::digest(client_key).into();
        let without_proof = format!("c=biws,r={combined}");
        let auth = format!("{first_bare},{server_first},{without_proof}");
        let signature = hmac(&stored, auth.as_bytes());
        let proof: Vec<u8> = client_key
            .iter()
            .zip(signature)
            .map(|(a, b)| a ^ b)
            .collect();
        c.send(
            b'p',
            format!("{without_proof},p={}", b64(&proof)).as_bytes(),
        );
        let (tag, body) = c.recv().expect("closed after the proof");
        if tag == b'E' {
            return Err(parse_error(&body));
        }
        assert_eq!(i32::from_be_bytes(body[..4].try_into().unwrap()), 12);
        let expected = hmac(&hmac(&salted, b"Server Key"), auth.as_bytes());
        assert_eq!(
            String::from_utf8_lossy(&body[4..]),
            format!("v={}", b64(&expected))
        );
        let reply = c.collect();
        assert_eq!(reply.status, b'I');
        assert!(reply.seen.starts_with(b"R"), "AuthenticationOk first");
        for must in *b"SK" {
            assert!(reply.seen.contains(&must), "startup sends {}", must as char);
        }
        Ok(c)
    }

    /// Reads until the server closes the connection; only an ErrorResponse may come first.
    fn until_closed(&mut self) -> Option<PgErr> {
        let mut error = None;
        while let Some((tag, body)) = self.recv() {
            assert_eq!(
                tag, b'E',
                "unexpected message {} before the close",
                tag as char
            );
            error = Some(parse_error(&body));
        }
        error
    }

    /// Reads messages up to and including ReadyForQuery.
    fn collect(&mut self) -> Reply {
        let mut reply = Reply::default();
        loop {
            let (tag, body) = self.recv().expect("connection closed before ReadyForQuery");
            reply.seen.push(tag);
            match tag {
                b'T' => {
                    let n = i16::from_be_bytes(body[..2].try_into().unwrap());
                    let mut pos = 2;
                    for _ in 0..n {
                        let name = cstr(&body, &mut pos);
                        let oid = u32::from_be_bytes(body[pos + 6..pos + 10].try_into().unwrap());
                        let format =
                            i16::from_be_bytes(body[pos + 16..pos + 18].try_into().unwrap());
                        pos += 18;
                        reply.fields.push((name, oid, format));
                    }
                }
                b'D' => {
                    let n = i16::from_be_bytes(body[..2].try_into().unwrap());
                    let mut pos = 2;
                    let mut row = Vec::new();
                    for _ in 0..n {
                        let len = i32::from_be_bytes(body[pos..pos + 4].try_into().unwrap());
                        pos += 4;
                        if len < 0 {
                            row.push(None);
                        } else {
                            row.push(Some(body[pos..pos + len as usize].to_vec()));
                            pos += len as usize;
                        }
                    }
                    reply.rows.push(row);
                }
                b'C' => reply
                    .tags
                    .push(String::from_utf8_lossy(&body[..body.len() - 1]).into()),
                b'E' => reply.error = Some(parse_error(&body)),
                b't' => {
                    let n = i16::from_be_bytes(body[..2].try_into().unwrap()) as usize;
                    reply.param_oids = (0..n)
                        .map(|i| u32::from_be_bytes(body[2 + 4 * i..6 + 4 * i].try_into().unwrap()))
                        .collect();
                }
                b'Z' => {
                    reply.status = body[0];
                    return reply;
                }
                _ => {}
            }
        }
    }

    fn simple(&mut self, sql: &str) -> Reply {
        let mut body = sql.as_bytes().to_vec();
        body.push(0);
        self.send(b'Q', &body);
        self.collect()
    }

    /// One statement that must succeed; returns the text rows.
    fn ok(&mut self, sql: &str) -> Vec<Vec<String>> {
        let reply = self.simple(sql);
        assert!(reply.error.is_none(), "{sql}: {:?}", reply.error);
        reply.text()
    }

    fn count(&mut self) -> String {
        self.ok("SELECT COUNT(*) FROM events")[0][0].clone()
    }

    fn pipeline(&mut self, messages: &[Msg]) -> Reply {
        for (tag, body) in messages {
            self.send(*tag, body);
        }
        self.send(b'S', &[]);
        self.collect()
    }
}

fn parse_msg(name: &str, sql: &str, oids: &[i32]) -> Msg {
    let mut b = format!("{name}\0{sql}\0").into_bytes();
    b.extend_from_slice(&i16b(oids.len() as i16));
    for oid in oids {
        b.extend_from_slice(&i32b(*oid));
    }
    (b'P', b)
}

fn bind_msg(
    portal: &str,
    statement: &str,
    pformats: &[i16],
    params: &[Option<&[u8]>],
    rformats: &[i16],
) -> Msg {
    let mut b = format!("{portal}\0{statement}\0").into_bytes();
    b.extend_from_slice(&i16b(pformats.len() as i16));
    for f in pformats {
        b.extend_from_slice(&i16b(*f));
    }
    b.extend_from_slice(&i16b(params.len() as i16));
    for p in params {
        match p {
            None => b.extend_from_slice(&i32b(-1)),
            Some(bytes) => {
                b.extend_from_slice(&i32b(bytes.len() as i32));
                b.extend_from_slice(bytes);
            }
        }
    }
    b.extend_from_slice(&i16b(rformats.len() as i16));
    for f in rformats {
        b.extend_from_slice(&i16b(*f));
    }
    (b'B', b)
}

fn describe_msg(kind: u8, name: &str) -> Msg {
    (b'D', [&[kind][..], name.as_bytes(), &[0]].concat())
}

fn execute_msg(portal: &str, max_rows: i32) -> Msg {
    (b'E', [portal.as_bytes(), &[0], &i32b(max_rows)].concat())
}

fn close_msg(kind: u8, name: &str) -> Msg {
    (b'C', [&[kind][..], name.as_bytes(), &[0]].concat())
}

fn seed(c: &mut Client) {
    c.ok("CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)");
    c.ok("INSERT INTO events VALUES (100, 12, 1), (101, 18, 2), (102, 25, 1)");
}

fn wait_for_login(server: &Server) -> Client {
    // A closed connection frees its slot asynchronously.
    for _ in 0..100 {
        if let Ok(c) = Client::login(server.addr, USER, PASSWORD) {
            return c;
        }
        std::thread::sleep(Duration::from_millis(50));
    }
    panic!("server did not accept a new connection");
}

// ---- tests ---------------------------------------------------------------------------------

#[test]
fn simple_query_round_trip_and_logging() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    assert_eq!(server.json["backend"], "db");
    assert_eq!(server.json["version"], env!("CARGO_PKG_VERSION"));
    let mut c = server.login();

    // Unknown table before CREATE: an error, and the session stays usable.
    let r = c.simple("SELECT COUNT(*) FROM events");
    assert_eq!((r.code(), r.status), ("42P01", b'I'));

    let r = c.simple(
        "CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL);",
    );
    assert_eq!(r.tags, ["CREATE TABLE"]);
    let r = c.simple("INSERT INTO events VALUES (100, 12, 1), (101, 18, 2), (102, 25, 1)");
    assert_eq!(r.tags, ["INSERT 0 3"]);

    let r = c.simple("SELECT COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean FROM events WHERE ts >= 100 AND ts < 102");
    assert_eq!(
        r.fields
            .iter()
            .map(|f| (f.0.as_str(), f.1, f.2))
            .collect::<Vec<_>>(),
        [("n", 20, 0), ("total", 20, 0), ("mean", 701, 0)]
    );
    assert_eq!(r.text(), [["2", "30", "15"]]);
    assert_eq!((r.tags, r.status), (vec!["SELECT 1".to_string()], b'I'));

    let r =
        c.simple("SELECT device, SUM(value) AS total FROM events GROUP BY device ORDER BY device");
    assert_eq!(r.text(), [["1", "37"], ["2", "18"]]);
    assert_eq!(r.tags, ["SELECT 2"]);
    assert_eq!(
        c.ok("SELECT * FROM events WHERE ts = 101"),
        [["101", "18", "2"]]
    );
    assert_eq!(
        c.ok("SELECT MIN(value), MAX(value) FROM events WHERE ts > 1000"),
        [["NULL", "NULL"]]
    );
    assert_eq!(
        c.ok("EXPLAIN SELECT SUM(value) FROM events WHERE ts >= 100 AND ts < 102")[0][0],
        "prefix-range-aggregate"
    );

    // Empty queries, comments, repeated semicolons.
    for empty in ["", ";", " ;; ; ", "-- just a comment"] {
        let r = c.simple(empty);
        assert_eq!(
            (r.seen.as_slice(), r.status),
            (&b"IZ"[..], b'I'),
            "{empty:?}"
        );
    }
    let r = c.simple("SELECT COUNT(*) FROM events;;");
    assert_eq!(r.text(), [["3"]]);

    // Several statements: results in order, one implicit transaction.
    let r = c.simple("INSERT INTO events VALUES (103, 5, 3); SELECT COUNT(*) FROM events; SELECT SUM(value) FROM events");
    assert_eq!(r.tags, ["INSERT 0 1", "SELECT 1", "SELECT 1"]);
    assert_eq!(r.text(), [["3"], ["55"]]); // reads do not see the same string's writes
    let r = c.simple("INSERT INTO events VALUES (104, 1, 1); INSERT INTO nosuch VALUES (1)");
    assert_eq!(r.code(), "42P01");
    assert_eq!(
        c.count(),
        "4",
        "a failed multi-statement string applies nothing"
    );
    // A syntax error anywhere means nothing runs.
    let r = c.simple("INSERT INTO events VALUES (105, 1, 1); SELEKT");
    assert_eq!(r.code(), "42601");
    assert_eq!(c.count(), "4");

    for (bad, code) in [
        ("SELECT 1", "42601"),
        ("SELECT COUNT(*) FROM events WHERE nope = 1", "42703"),
        ("INSERT INTO events VALUES (1, 2)", "42601"),
        ("CREATE TABLE events (a BIGINT NOT NULL)", "42P07"),
        ("DROP TABLE events", "42601"),
    ] {
        let r = c.simple(bad);
        assert_eq!((r.code(), r.status), (code, b'I'), "{bad}");
        assert_eq!(r.error.unwrap().severity, "ERROR");
    }
    assert_eq!(c.count(), "4");

    // Autocommit statements from several connections at once.
    let addr = server.addr;
    let workers: Vec<_> = (0..6)
        .map(|w| {
            std::thread::spawn(move || {
                let mut c = Client::login(addr, USER, PASSWORD).unwrap();
                for i in 0..15 {
                    let r = c.simple(&format!(
                        "INSERT INTO events VALUES ({}, 1, 9)",
                        1000 + w * 100 + i
                    ));
                    assert!(r.error.is_none());
                }
            })
        })
        .collect();
    for w in workers {
        w.join().unwrap();
    }
    assert_eq!(c.count(), "94");
    drop(c);

    // The log names events, never SQL text or secrets.
    std::thread::sleep(Duration::from_millis(300));
    let log = server.log();
    assert!(log.contains("authenticated user \"kestrel\""), "{log}");
    assert!(log.contains("closed"), "{log}");
    for secret in [PASSWORD, "INSERT", "events", "SELECT"] {
        assert!(!log.contains(secret), "log leaks {secret:?}: {log}");
    }
}

#[test]
fn extended_protocol_with_binary_results() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    let mut c = server.login();
    seed(&mut c);
    let sql = "SELECT COUNT(*), SUM(value), AVG(value) FROM events WHERE ts >= $1 AND ts < $2";

    // Named statement, text parameters, binary result columns.
    let r = c.pipeline(&[
        parse_msg("range", sql, &[]),
        describe_msg(b'S', "range"),
        bind_msg("", "range", &[], &[Some(b"100"), Some(b"102")], &[1]),
        describe_msg(b'P', ""),
        execute_msg("", 0),
    ]);
    assert!(r.error.is_none(), "{:?}", r.error);
    assert_eq!(r.seen, *b"1tT2TDCZ");
    assert_eq!(r.param_oids, [20, 20]);
    assert_eq!(
        r.fields[..3].iter().map(|f| (f.1, f.2)).collect::<Vec<_>>(),
        [(20, 0), (20, 0), (701, 0)],
        "a statement describes text columns"
    );
    assert_eq!(
        r.fields[3..].iter().map(|f| (f.1, f.2)).collect::<Vec<_>>(),
        [(20, 1), (20, 1), (701, 1)],
        "portal formats are reported"
    );
    let row = &r.rows[0];
    assert_eq!(
        i64::from_be_bytes(row[0].clone().unwrap().try_into().unwrap()),
        2
    );
    assert_eq!(
        i64::from_be_bytes(row[1].clone().unwrap().try_into().unwrap()),
        30
    );
    assert_eq!(
        f64::from_bits(u64::from_be_bytes(
            row[2].clone().unwrap().try_into().unwrap()
        )),
        15.0
    );
    assert_eq!(r.tags, ["SELECT 1"]);

    // Reuse the statement: text results, binary int8 parameters, mixed per-column formats.
    let r = c.pipeline(&[
        bind_msg(
            "a",
            "range",
            &[1],
            &[Some(&100i64.to_be_bytes()), Some(&200i64.to_be_bytes())],
            &[],
        ),
        execute_msg("a", 0),
        bind_msg(
            "b",
            "range",
            &[0],
            &[Some(b"+100"), Some(b"-5")],
            &[0, 1, 0],
        ),
        execute_msg("b", 0),
    ]);
    assert!(r.error.is_none(), "{:?}", r.error);
    assert_eq!(r.text()[0], ["3", "55", "18.333333333333332"]);
    assert_eq!(r.rows[1][0].as_deref(), Some(&b"0"[..]));
    assert!(
        r.rows[1][1].is_none() && r.rows[1][2].is_none(),
        "SUM and AVG over no rows are NULL"
    );
}

#[test]
fn extended_protocol_edge_cases() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    let mut c = server.login();
    seed(&mut c);

    // Row-limited portal: PortalSuspended, then the rest.
    let r = c.pipeline(&[
        parse_msg("", "SELECT ts, value FROM events", &[]),
        bind_msg("cur", "", &[], &[], &[]),
        execute_msg("cur", 2),
        execute_msg("cur", 2),
    ]);
    assert_eq!(r.seen, *b"12DDsDCZ");
    assert_eq!(r.tags, ["SELECT 3"]);
    // Writes, an empty statement, Describe of a non-row statement, Close of unknown names.
    let r = c.pipeline(&[
        parse_msg("w", "INSERT INTO events VALUES ($1, $2, $3)", &[20, 0, 23]),
        describe_msg(b'S', "w"),
        bind_msg("", "w", &[], &[Some(b"7"), Some(b"8"), Some(b"9")], &[]),
        describe_msg(b'P', ""),
        execute_msg("", 0),
        parse_msg("e", "", &[]),
        bind_msg("", "e", &[], &[], &[]),
        execute_msg("", 0),
        close_msg(b'S', "w"),
        close_msg(b'P', "nope"),
    ]);
    assert!(r.error.is_none(), "{:?}", r.error);
    assert_eq!(r.param_oids, [20, 20, 23]);
    assert_eq!(r.tags, ["INSERT 0 1"]);
    assert_eq!(r.seen, *b"1tn2nC12I33Z");
    assert_eq!(c.count(), "4");

    // Drivers drop prepared statements with plain DEALLOCATE (psycopg does this).
    let r = c.pipeline(&[parse_msg("gone", "SELECT COUNT(*) FROM events", &[])]);
    assert!(r.error.is_none());
    assert_eq!(c.simple("DEALLOCATE gone").tags, ["DEALLOCATE"]);
    assert_eq!(c.simple("DEALLOCATE PREPARE gone").code(), "26000");
    let r = c.pipeline(&[bind_msg("", "gone", &[], &[], &[])]);
    assert_eq!(r.code(), "26000");
    let r = c.pipeline(&[parse_msg("k", "SELECT COUNT(*) FROM events", &[])]);
    assert!(r.error.is_none());
    assert_eq!(c.simple("deallocate all;").tags, ["DEALLOCATE ALL"]);
    let r = c.pipeline(&[bind_msg("", "k", &[], &[], &[])]);
    assert_eq!(r.code(), "26000");
    assert_eq!(c.simple("DEALLOCATE a b").code(), "42601");

    // Errors: duplicate named statement, unknown statement, wrong parameter count.
    for (messages, code) in [
        (
            vec![
                parse_msg("d", "SELECT COUNT(*) FROM events", &[]),
                parse_msg("d", "SELECT COUNT(*) FROM events", &[]),
            ],
            "42P05",
        ),
        (vec![bind_msg("", "ghost", &[], &[], &[])], "26000"),
        (
            vec![
                parse_msg("two", "SELECT COUNT(*) FROM events WHERE ts > $1", &[]),
                bind_msg("", "two", &[], &[], &[]),
            ],
            "08P01",
        ),
        (
            vec![parse_msg(
                "",
                "SELECT COUNT(*) FROM events WHERE ts > $2",
                &[],
            )],
            "42P18",
        ),
        (
            vec![parse_msg("", "SELECT COUNT(*) FROM events; SELECT 1", &[])],
            "42601",
        ),
        (vec![parse_msg("", "SELEKT", &[])], "42601"),
        (vec![execute_msg("ghost", 0)], "34000"),
        (vec![describe_msg(b'S', "ghost")], "26000"),
    ] {
        let r = c.pipeline(&messages);
        assert_eq!(r.code(), code, "{messages:?}");
        assert_eq!(r.status, b'I');
        // The connection is usable afterwards.
        assert_eq!(c.count(), "4");
    }
}

#[test]
fn non_integer_parameters_are_rejected_with_22p02_and_the_batch_is_skipped_to_sync() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    let mut c = server.login();
    seed(&mut c);
    for bad in [
        "abc",
        "1.5",
        "",
        "1e3",
        " 5",
        "5 ",
        "0x10",
        "9223372036854775808",
        "--1",
    ] {
        let r = c.pipeline(&[
            parse_msg("", "SELECT COUNT(*) FROM events WHERE ts >= $1", &[]),
            bind_msg("", "", &[], &[Some(bad.as_bytes())], &[]),
            execute_msg("", 0),
        ]);
        assert_eq!(r.code(), "22P02", "{bad:?}");
        assert_eq!(
            r.seen, *b"1EZ",
            "Execute after a failed Bind is discarded until Sync"
        );
    }
    // NULL and binary parameters of an unsupported type are errors too.
    let r = c.pipeline(&[
        parse_msg("", "SELECT COUNT(*) FROM events WHERE ts >= $1", &[]),
        bind_msg("", "", &[], &[None], &[]),
    ]);
    assert_eq!(r.code(), "22P02");
    let r = c.pipeline(&[
        parse_msg("", "SELECT COUNT(*) FROM events WHERE ts >= $1", &[25]),
        bind_msg("", "", &[1], &[Some(b"1")], &[]),
    ]);
    assert_eq!(r.code(), "0A000");
    // Plain integers, including negatives, are accepted.
    let r = c.pipeline(&[
        parse_msg("", "SELECT COUNT(*) FROM events WHERE ts >= $1", &[]),
        bind_msg("", "", &[], &[Some(b"-9223372036854775808")], &[]),
        execute_msg("", 0),
    ]);
    assert_eq!(r.text(), [["3"]]);
    // An error inside an explicit transaction aborts it.
    c.ok("BEGIN");
    let r = c.pipeline(&[
        parse_msg("", "SELECT COUNT(*) FROM events WHERE ts >= $1", &[]),
        bind_msg("", "", &[], &[Some(b"x")], &[]),
    ]);
    assert_eq!((r.code(), r.status), ("22P02", b'E'));
    assert_eq!(c.simple("ROLLBACK").tags, ["ROLLBACK"]);
}

#[test]
fn wrong_password_unknown_user_and_no_access() {
    let dir = TempDir::new();
    let mut server = Server::db(&dir, &[]);
    for (user, password) in [
        (USER, "wrong"),
        (USER, ""),
        ("someone", PASSWORD),
        ("", PASSWORD),
    ] {
        match Client::login(server.addr, user, password) {
            Err(e) => {
                assert_eq!(
                    e.code,
                    if user.is_empty() { "28000" } else { "28P01" },
                    "{user:?}"
                );
                assert_eq!(e.severity, "FATAL");
            }
            Ok(_) => panic!("{user:?}/{password:?} must not log in"),
        }
    }
    // After a failed proof the socket is dead: queries get no answer.
    let mut c = Client::connect_raw(server.addr);
    c.send_startup(USER);
    c.recv().unwrap();
    c.send(b'p', b"SCRAM-SHA-256\0\xff\xff\xff\xffxxxx");
    assert_eq!(c.until_closed().unwrap().code, "08P01");
    let mut c = Client::connect_raw(server.addr);
    c.send(b'Q', b"SELECT 1\0"); // skipping startup entirely
    assert_eq!(c.until_closed().unwrap().code, "08P01");
    // A startup that is not SCRAM-able (the client picks a mechanism that is not offered).
    let mut c = Client::connect_raw(server.addr);
    c.send_startup(USER);
    c.recv().unwrap();
    c.send(b'p', b"SCRAM-SHA-256-PLUS\0\xff\xff\xff\xff");
    let (tag, body) = c.recv().unwrap();
    assert_eq!((tag, parse_error(&body).code), (b'E', "28000".to_string()));
    // The server is unharmed and the right password still works.
    let mut ok = server.login();
    assert_eq!(
        ok.simple("EXPLAIN SELECT COUNT(*) FROM events").code(),
        "42P01"
    );
    assert!(server.alive());
    let log = server.log();
    assert!(log.contains("auth failed"), "{log}");
    assert!(
        !log.contains("wrong"),
        "no password material in the log: {log}"
    );
}

#[test]
fn too_many_connections_get_53300() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &["--max-connections", "2"]);
    let mut a = server.login();
    let mut b = server.login();
    let mut third = Client::connect_raw(server.addr);
    third.send_startup(USER);
    let (tag, body) = third.recv().unwrap();
    let err = parse_error(&body);
    assert_eq!(
        (tag, err.code.as_str(), err.severity.as_str()),
        (b'E', "53300", "FATAL")
    );
    assert!(third.recv().is_none(), "closed after the error");
    // Over-limit clients that open with SSLRequest still get an answer they understand.
    let mut fourth = Client::connect_raw(server.addr);
    fourth
        .stream
        .write_all(&[0, 0, 0, 8, 4, 210, 22, 47])
        .unwrap();
    let mut n = [0u8];
    fourth.stream.read_exact(&mut n).unwrap();
    assert_eq!(n, *b"N");
    fourth.send_startup(USER);
    assert_eq!(parse_error(&fourth.recv().unwrap().1).code, "53300");
    // Existing sessions are unaffected, and a freed slot is reusable.
    assert_eq!(a.simple("SELECT COUNT(*) FROM events").code(), "42P01");
    assert_eq!(b.simple("SELECT COUNT(*) FROM events").code(), "42P01");
    drop(a);
    drop(b);
    let mut c = wait_for_login(&server);
    assert_eq!(c.simple("SELECT COUNT(*) FROM events").code(), "42P01");
}

#[test]
fn oversized_and_garbage_input_closes_one_connection_only() {
    let dir = TempDir::new();
    let mut server = Server::db(&dir, &[]);
    let mut keeper = server.login();
    seed(&mut keeper);

    // 54000 for a message above 16 MiB; the body is never read.
    let mut c = server.login();
    c.stream.write_all(b"Q").unwrap();
    c.stream.write_all(&i32b(16 * 1024 * 1024 + 1)).unwrap();
    let (tag, body) = c.recv().unwrap();
    let err = parse_error(&body);
    assert_eq!(
        (tag, err.code.as_str(), err.severity.as_str()),
        (b'E', "54000", "FATAL")
    );
    assert!(c.recv().is_none());
    // A small message that is malformed (unterminated string) is a protocol violation.
    let mut c = server.login();
    c.stream.write_all(b"Q").unwrap();
    c.stream.write_all(&i32b(1024)).unwrap();
    c.stream.write_all(&[b'a'; 1020]).unwrap(); // unterminated string
    assert_eq!(parse_error(&c.recv().unwrap().1).code, "08P01");

    // Garbage before startup, an unknown message type, a short body, an invalid length.
    let mut c = Client::connect_raw(server.addr);
    c.stream
        .write_all(b"GET / HTTP/1.1\r\nHost: x\r\n\r\n")
        .unwrap();
    let _ = c.recv();
    assert!(c.recv().is_none());
    let mut c = Client::connect_raw(server.addr);
    c.stream.write_all(&[0xff; 64]).unwrap();
    assert!(c.recv().is_none() || c.recv().is_none());
    for (tag, body) in [
        (0xffu8, &b""[..]),
        (b'Q', &b"SELECT 1"[..]),                    // no terminating NUL
        (b'B', &[0, 0, 0, 0, 0, 0, 0, 0, 0xff][..]), // trailing byte after a Bind
        (b'P', &b"\0SELECT 1\0\xff\xff"[..]),        // negative parameter count
        (b'D', &b"Z\0"[..]),                         // bad Describe target
    ] {
        let mut c = server.login();
        c.send(tag, body);
        let err = c.recv().map(|(t, b)| (t, parse_error(&b).code));
        assert_eq!(err, Some((b'E', "08P01".to_string())), "tag {tag}");
        assert!(c.recv().is_none());
    }
    let mut c = server.login();
    c.stream.write_all(&[b'Q', 0, 0, 0, 2]).unwrap(); // length below the 4-byte minimum
    assert_eq!(parse_error(&c.recv().unwrap().1).code, "08P01");
    // Random bytes after authentication.
    let mut c = server.login();
    c.stream
        .write_all(&(0..200u32).map(|i| (i * 37 + 11) as u8).collect::<Vec<_>>())
        .unwrap();
    let _ = c.recv();
    assert!(c.recv().is_none());

    assert!(server.alive());
    assert_eq!(keeper.count(), "3", "the other session never noticed");
    assert_eq!(server.login().count(), "3");
}

#[test]
fn ssl_gssenc_and_cancel_requests() {
    let dir = TempDir::new();
    let mut server = Server::db(&dir, &[]);
    // SSLRequest then GSSENCRequest both get 'N'; the same socket then starts up normally.
    let mut c = Client::connect_raw(server.addr);
    for code in [80877103i32, 80877104] {
        c.stream
            .write_all(&[&i32b(8)[..], &i32b(code)[..]].concat())
            .unwrap();
        let mut answer = [0u8];
        c.stream.read_exact(&mut answer).unwrap();
        assert_eq!(answer, *b"N");
    }
    c.send_startup(USER);
    assert_eq!(c.recv().unwrap().0, b'R');
    drop(c);
    // CancelRequest: accepted, ignored, connection closed without an error message.
    let mut c = Client::connect_raw(server.addr);
    c.stream
        .write_all(&[&i32b(16)[..], &i32b(80877102), &i32b(1234), &i32b(5678)].concat())
        .unwrap();
    assert!(c.recv().is_none());
    // Protocol 3.2 asks for negotiation; protocol 2.0 is refused.
    let mut c = Client::connect_raw(server.addr);
    let mut body = i32b(196610).to_vec();
    body.extend_from_slice(b"user\0kestrel\0_pq_.test\0on\0\0");
    c.stream
        .write_all(&[&i32b(body.len() as i32 + 4)[..], &body].concat())
        .unwrap();
    let (tag, body) = c.recv().unwrap();
    assert_eq!(tag, b'v');
    assert_eq!(&body[..8], &[0, 0, 0, 0, 0, 0, 0, 1]);
    assert!(body.ends_with(b"_pq_.test\0"));
    let mut c = Client::connect_raw(server.addr);
    c.stream
        .write_all(&[&i32b(8)[..], &i32b(131072)].concat())
        .unwrap();
    assert_eq!(parse_error(&c.recv().unwrap().1).code, "0A000");
    assert!(server.alive());
    server.login();
}

#[test]
fn startup_must_arrive_within_two_seconds_and_authentication_finish_within_ten() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    // Silent connection: closed by the short startup deadline.
    let started = Instant::now();
    let mut idle = Client::connect_raw(server.addr);
    assert!(idle.recv().is_none());
    let waited = started.elapsed();
    assert!(
        waited >= Duration::from_millis(1500) && waited < Duration::from_secs(5),
        "{waited:?}"
    );
    // A client that starts up promptly but then stalls in the SASL exchange gets the whole ten
    // seconds, not more.
    let started = Instant::now();
    let mut stalled = Client::connect_raw(server.addr);
    stalled.send_startup(USER);
    assert_eq!(stalled.recv().unwrap().0, b'R');
    assert!(stalled.recv().is_none());
    let waited = started.elapsed();
    assert!(
        waited >= Duration::from_secs(9) && waited < Duration::from_secs(16),
        "{waited:?}"
    );
    // A drip-feeding client does not extend the startup deadline.
    let started = Instant::now();
    let mut slow = Client::connect_raw(server.addr);
    slow.stream
        .set_read_timeout(Some(Duration::from_secs(1)))
        .unwrap();
    // Announces a 200-byte startup packet and sends one byte per second.
    let mut packet = [&i32b(200)[..], &i32b(196608)].concat();
    packet.extend_from_slice(&[b'x'; 40]);
    let mut closed = false;
    for byte in &packet {
        if slow.stream.write_all(&[*byte]).is_err() {
            closed = true;
            break;
        }
        let mut one = [0u8; 1];
        match slow.stream.read(&mut one) {
            Ok(0) => closed = true,
            Ok(_) => panic!("no data is expected before the close"),
            Err(e)
                if matches!(
                    e.kind(),
                    std::io::ErrorKind::WouldBlock | std::io::ErrorKind::TimedOut
                ) => {}
            Err(_) => closed = true, // reset
        }
        if closed || started.elapsed() > Duration::from_secs(16) {
            break;
        }
    }
    let waited = started.elapsed();
    assert!(
        closed && waited >= Duration::from_millis(1500) && waited < Duration::from_secs(5),
        "{waited:?}"
    );
    // Authenticated sessions have no timeout and the server is still fine.
    let mut c = server.login();
    assert_eq!(c.simple("SELECT COUNT(*) FROM events").code(), "42P01");
}

#[test]
fn failed_transactions_return_25p02_until_rollback() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    let mut c = server.login();
    seed(&mut c);

    let r = c.simple("BEGIN");
    assert_eq!((r.tags, r.status), (vec!["BEGIN".to_string()], b'T'));
    let r = c.simple("INSERT INTO events VALUES (200, 1, 1)");
    assert_eq!((r.tags, r.status), (vec!["INSERT 0 1".to_string()], b'T'));
    let r = c.simple("SELECT SUM(nope) FROM events");
    assert_eq!((r.code(), r.status), ("42703", b'E'));
    for sql in [
        "SELECT COUNT(*) FROM events",
        "INSERT INTO events VALUES (201, 1, 1)",
        "BEGIN",
    ] {
        let r = c.simple(sql);
        assert_eq!((r.code(), r.status), ("25P02", b'E'), "{sql}");
    }
    let r = c.simple("COMMIT");
    assert_eq!(
        (r.tags, r.status, r.error),
        (vec!["ROLLBACK".to_string()], b'I', None)
    );
    assert_eq!(
        c.count(),
        "3",
        "nothing from the failed transaction was applied"
    );

    // ROLLBACK works from the failed state too, and an unknown table fails at statement time.
    c.ok("BEGIN");
    assert_eq!(c.simple("INSERT INTO nosuch VALUES (1)").code(), "42P01");
    assert_eq!(c.simple("ROLLBACK").tags, ["ROLLBACK"]);
    c.ok("BEGIN");
    c.ok("INSERT INTO events VALUES (300, 1, 1)");
    assert_eq!(c.simple("ROLLBACK").tags, ["ROLLBACK"]);
    assert_eq!(c.count(), "3");
    // COMMIT / ROLLBACK outside a transaction are harmless.
    assert_eq!(c.simple("COMMIT").tags, ["COMMIT"]);
    assert_eq!(c.simple("ROLLBACK").tags, ["ROLLBACK"]);

    // A good transaction: reads inside do not see its own writes; COMMIT applies it as one unit.
    c.ok("BEGIN");
    assert_eq!(
        c.simple("INSERT INTO events VALUES (400, 4, 4), (401, 5, 4)")
            .tags,
        ["INSERT 0 2"]
    );
    assert_eq!(c.simple("BEGIN").status, b'T'); // already in a transaction: no-op
    assert_eq!(c.count(), "3");
    // CREATE TABLE and INSERT inside one transaction.
    assert_eq!(
        c.simple("CREATE TABLE side (a BIGINT NOT NULL)").tags,
        ["CREATE TABLE"]
    );
    assert_eq!(
        c.simple("INSERT INTO side VALUES (1), (2)").tags,
        ["INSERT 0 2"]
    );
    assert_eq!(c.simple("INSERT INTO side VALUES (1, 2)").code(), "42601");
    assert_eq!(c.simple("COMMIT").tags, ["ROLLBACK"]);
    c.ok("BEGIN");
    c.ok("INSERT INTO events VALUES (400, 4, 4), (401, 5, 4)");
    c.ok("CREATE TABLE side (a BIGINT NOT NULL)");
    c.ok("INSERT INTO side VALUES (1), (2)");
    let r = c.simple("COMMIT");
    assert_eq!((r.tags, r.status), (vec!["COMMIT".to_string()], b'I'));
    assert_eq!(c.count(), "5");
    assert_eq!(c.ok("SELECT SUM(a) FROM side"), [["3"]]);
}

#[test]
fn concurrent_transactions_are_isolated_and_both_commit() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    let mut one = server.login();
    let mut two = server.login();
    seed(&mut one);

    one.ok("BEGIN");
    two.ok("BEGIN");
    one.ok("INSERT INTO events VALUES (500, 50, 5)");
    two.ok("INSERT INTO events VALUES (600, 60, 6), (601, 61, 6)");
    assert_eq!(
        one.count(),
        "3",
        "nobody sees uncommitted rows, not even their own"
    );
    assert_eq!(two.count(), "3");
    assert_eq!(one.simple("COMMIT").tags, ["COMMIT"]);
    assert_eq!(
        two.count(),
        "4",
        "a committed transaction becomes visible to others"
    );
    assert_eq!(
        two.ok("SELECT COUNT(*) FROM events WHERE ts >= 600"),
        [["0"]]
    );
    assert_eq!(two.simple("COMMIT").tags, ["COMMIT"]);
    assert_eq!(
        one.ok("SELECT COUNT(*), SUM(value) FROM events"),
        [["6", "226"]]
    );

    // A transaction that rolls back while another commits does not disturb it.
    one.ok("BEGIN");
    two.ok("BEGIN");
    one.ok("INSERT INTO events VALUES (700, 1, 7)");
    two.ok("INSERT INTO events VALUES (800, 2, 8)");
    assert_eq!(one.simple("ROLLBACK").tags, ["ROLLBACK"]);
    assert_eq!(two.simple("COMMIT").tags, ["COMMIT"]);
    assert_eq!(
        one.ok("SELECT COUNT(*), SUM(value) FROM events"),
        [["7", "228"]]
    );

    // Two transactions creating the same table: the second COMMIT reports the conflict,
    // returns the session to idle and applies nothing.
    one.ok("BEGIN");
    two.ok("BEGIN");
    one.ok("CREATE TABLE clash (a BIGINT NOT NULL)");
    two.ok("CREATE TABLE clash (a BIGINT NOT NULL)");
    two.ok("INSERT INTO events VALUES (900, 9, 9)");
    assert_eq!(one.simple("COMMIT").tags, ["COMMIT"]);
    let r = two.simple("COMMIT");
    assert_eq!((r.code(), r.status), ("42P07", b'I'));
    assert_eq!(
        two.count(),
        "7",
        "the conflicting transaction left no trace"
    );
}

#[test]
fn committed_rows_survive_a_restart_and_uncommitted_ones_do_not() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    let mut c = server.login();
    seed(&mut c);
    c.ok("BEGIN");
    c.ok("INSERT INTO events VALUES (150, 1, 1)");
    c.ok("COMMIT");
    let mut open = server.login();
    open.ok("BEGIN");
    open.ok("INSERT INTO events VALUES (999, 1, 1)");
    let mut failed = server.login();
    failed.ok("BEGIN");
    failed.ok("INSERT INTO events VALUES (998, 1, 1)");
    failed.simple("SELECT SUM(nope) FROM events");
    failed.simple("COMMIT");
    server.stop(); // killed: no clean shutdown

    let server = Server::db(&dir, &[]);
    let mut c = server.login();
    assert_eq!(
        c.ok("SELECT COUNT(*), SUM(value) FROM events"),
        [["4", "56"]]
    );
    assert_eq!(
        c.ok("SELECT * FROM events WHERE ts = 150"),
        [["150", "1", "1"]]
    );
    // The table keeps accepting data after recovery.
    assert_eq!(
        c.simple("INSERT INTO events VALUES (103, 1, 1)").tags,
        ["INSERT 0 1"]
    );
}

#[test]
fn sum_beyond_bigint_is_a_clean_22003_not_a_wrong_answer() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    let mut c = server.login();
    c.ok("CREATE TABLE big (a BIGINT NOT NULL)");
    c.ok("INSERT INTO big VALUES (9223372036854775807), (9223372036854775807)");
    let r = c.simple("SELECT SUM(a) FROM big");
    assert_eq!((r.code(), r.status), ("22003", b'I'));
    assert!(r.rows.is_empty() && r.tags.is_empty());
    assert_eq!(
        c.ok("SELECT MAX(a), COUNT(*) FROM big"),
        [["9223372036854775807", "2"]]
    );
    assert_eq!(c.ok("SELECT AVG(a) FROM big"), [["9.223372036854776e+18"]]);
}

#[test]
fn archive_backend_inserts_selects_and_refuses_create() {
    let dir = TempDir::new();
    let server = Server::archive(&dir, &["--columns", "ts,value,device"]);
    assert_eq!(server.json["backend"], "archive");
    let mut c = server.login();
    let r = c.simple("CREATE TABLE other (a BIGINT NOT NULL)");
    assert_eq!((r.code(), r.status), ("42601", b'I'));
    assert!(r.error.unwrap().message.contains("archive"));
    assert_eq!(
        c.simple("EXPLAIN SELECT COUNT(*) FROM events").code(),
        "42601"
    );
    assert_eq!(
        c.simple("INSERT INTO other VALUES (1, 2, 3)").code(),
        "42P01"
    );
    assert_eq!(c.simple("INSERT INTO events VALUES (1, 2)").code(), "42601");

    assert_eq!(
        c.simple("INSERT INTO events VALUES (100, 12, 1), (101, 18, 2), (102, 25, 1)")
            .tags,
        ["INSERT 0 3"]
    );
    let r = c.simple("SELECT COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean FROM events WHERE ts >= 100 AND ts < 102");
    assert_eq!(r.text(), [["2", "30", "15"]]);
    assert_eq!(
        r.fields.iter().map(|f| f.1).collect::<Vec<_>>(),
        [20, 20, 701]
    );
    assert_eq!(c.ok("SELECT device, COUNT(*) AS n, SUM(value) AS s FROM events GROUP BY device ORDER BY device"), [["1", "2", "37"], ["2", "1", "18"]]);

    // Transactions: queued, one atomic batch at COMMIT, reads see committed data only.
    c.ok("BEGIN");
    c.ok("INSERT INTO events VALUES (103, 1, 3)");
    c.ok("INSERT INTO events VALUES (104, 2, 3), (105, 3, 3)");
    assert_eq!(c.count(), "3");
    assert_eq!(c.simple("COMMIT").tags, ["COMMIT"]);
    assert_eq!(c.count(), "6");
    c.ok("BEGIN");
    c.ok("INSERT INTO events VALUES (106, 1, 3)");
    assert_eq!(c.simple("ROLLBACK").tags, ["ROLLBACK"]);
    c.ok("BEGIN");
    c.ok("INSERT INTO events VALUES (107, 1, 3)");
    assert_eq!(c.simple("SELECT bogus FROM events").status, b'E');
    assert_eq!(c.simple("COMMIT").tags, ["ROLLBACK"]);
    assert_eq!(c.count(), "6");

    // 10,000 rows is the live-append limit per statement or transaction.
    let rows = |n: usize| {
        (0..n)
            .map(|i| format!("({}, 1, 1)", 1000 + i))
            .collect::<Vec<_>>()
            .join(",")
    };
    let r = c.simple(&format!("INSERT INTO events VALUES {}", rows(10_001)));
    assert_eq!((r.code(), r.status), ("54000", b'I'));
    assert_eq!(
        c.simple(&format!("INSERT INTO events VALUES {}", rows(10_000)))
            .tags,
        ["INSERT 0 10000"]
    );
    assert_eq!(c.count(), "10006");

    // Concurrent writers on the shared live archive.
    let addr = server.addr;
    let workers: Vec<_> = (0..4)
        .map(|w| {
            std::thread::spawn(move || {
                let mut c = Client::login(addr, USER, PASSWORD).unwrap();
                for i in 0..10 {
                    let r = c.simple(&format!(
                        "INSERT INTO events VALUES ({}, 1, 2)",
                        50_000 + w * 100 + i
                    ));
                    assert!(r.error.is_none(), "{:?}", r.error);
                }
            })
        })
        .collect();
    for w in workers {
        w.join().unwrap();
    }
    assert_eq!(c.count(), "10046");
    drop(c);
    server.stop();

    // Restart on the same directory: data is durable.
    let server = Server::archive(&dir, &[]);
    let mut c = server.login();
    assert_eq!(c.count(), "10046");
}

#[test]
fn startup_refusals() {
    let dir = TempDir::new();
    let bin = env!("CARGO_BIN_EXE_kestrel-server");
    let run = |args: &[&str]| {
        let out = Command::new(bin)
            .args(args)
            .stdin(Stdio::null())
            .output()
            .unwrap();
        (
            out.status.code(),
            String::from_utf8_lossy(&out.stdout).into_owned(),
            String::from_utf8_lossy(&out.stderr).into_owned(),
        )
    };
    let db = dir.arg("db");
    let pw = dir.arg("pw");

    // Never without a password file.
    let (code, stdout, stderr) = run(&["--db", &db, "--listen", "127.0.0.1:0"]);
    assert_eq!((code, stdout.as_str()), (Some(2), ""), "{stderr}");
    assert!(stderr.contains("--password-file is required"), "{stderr}");
    let (code, stdout, stderr) = run(&["--db", &db, "--password-file", &dir.arg("missing")]);
    assert_eq!((code, stdout.as_str()), (Some(2), ""), "{stderr}");
    std::fs::write(dir.path().join("empty"), "\n").unwrap();
    let (code, _, stderr) = run(&["--db", &db, "--password-file", &dir.arg("empty")]);
    assert_eq!(code, Some(2), "{stderr}");

    // Non-loopback listening is refused without --allow-remote; nothing is printed or opened.
    for addr in ["0.0.0.0:0", "[::]:0", "192.0.2.1:5433"] {
        let (code, stdout, stderr) = run(&["--db", &db, "--password-file", &pw, "--listen", addr]);
        assert_eq!((code, stdout.as_str()), (Some(2), ""), "{addr}: {stderr}");
        assert!(stderr.contains("refusing to listen"), "{stderr}");
    }
    assert!(
        !Path::new(&db).exists(),
        "a refused start must not open the database"
    );

    // Option errors.
    for args in [
        vec!["--password-file", pw.as_str()],
        vec![
            "--db",
            db.as_str(),
            "--archive",
            db.as_str(),
            "--password-file",
            pw.as_str(),
        ],
        vec![
            "--db",
            db.as_str(),
            "--columns",
            "a",
            "--password-file",
            pw.as_str(),
        ],
        vec![
            "--db",
            db.as_str(),
            "--max-connections",
            "0",
            "--password-file",
            pw.as_str(),
        ],
        vec![
            "--db",
            db.as_str(),
            "--frobnicate",
            "--password-file",
            pw.as_str(),
        ],
    ] {
        let (code, stdout, stderr) = run(&args);
        assert_eq!((code, stdout.as_str()), (Some(2), ""), "{args:?}: {stderr}");
    }

    // --allow-remote is accepted (loopback here: binding a LAN address would trip firewalls).
    let server = Server::db(&dir, &["--allow-remote", "--user", "alice"]);
    assert!(
        Client::login(server.addr, USER, PASSWORD).is_err(),
        "--user restricts the account"
    );
    assert!(Client::login(server.addr, "alice", PASSWORD).is_ok());
}

#[test]
fn checkpoint_runs_outside_transactions_and_keeps_every_row() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    let mut c = server.login();
    seed(&mut c);
    let before = c.count();
    let reply = c.simple("CHECKPOINT");
    assert!(reply.error.is_none(), "{:?}", reply.error);
    assert_eq!(reply.tags, ["CHECKPOINT"]);
    c.ok("BEGIN");
    assert_eq!(c.simple("CHECKPOINT").code(), "25001");
    c.ok("ROLLBACK");
    c.ok("INSERT INTO events VALUES (900, 1, 1)");
    drop(c);
    server.stop();
    let server = Server::db(&dir, &[]);
    let mut c = server.login();
    assert_eq!(c.count(), (before.parse::<i64>().unwrap() + 1).to_string());
    drop(c);
    server.stop();
    let names: Vec<String> = std::fs::read_dir(dir.path().join("db"))
        .unwrap()
        .map(|e| e.unwrap().file_name().to_string_lossy().to_string())
        .collect();
    assert!(
        names.iter().any(|n| n.starts_with("snapshot-")),
        "{names:?}"
    );
}

// ---- connection slots, memory budgets, transaction limits ------------------------------------

/// `CREATE TABLE wide` with 64 integer columns, the engine's maximum.
fn wide_create() -> String {
    let columns: Vec<String> = (0..64).map(|i| format!("c{i} BIGINT NOT NULL")).collect();
    format!("CREATE TABLE wide ({})", columns.join(", "))
}

/// `INSERT INTO wide` with `rows` rows of 64 copies of `value`.
fn wide_insert(rows: usize, value: &str) -> String {
    let row = format!("({})", vec![value; 64].join(","));
    let mut sql = String::from("INSERT INTO wide VALUES ");
    sql.push_str(&vec![row; rows].join(","));
    sql
}

/// A wide INSERT of about `bytes` bytes of SQL text.
fn wide_insert_of(bytes: usize) -> String {
    let value = "9223372036854775807";
    wide_insert(bytes / (64 * (value.len() + 1) + 3), value)
}

/// True once the server has closed this socket (nothing is consumed otherwise).
fn closed_by_peer(client: &Client) -> bool {
    client.stream.set_nonblocking(true).unwrap();
    let mut byte = [0u8; 1];
    let closed = match (&client.stream).read(&mut byte) {
        Ok(0) => true,
        Ok(_) => false,
        Err(e) => e.kind() != std::io::ErrorKind::WouldBlock,
    };
    client.stream.set_nonblocking(false).unwrap();
    closed
}

#[test]
fn silent_sockets_do_not_take_connection_slots() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &["--max-connections", "4"]);
    // Four sockets that never say anything used to fill all four slots for the whole deadline.
    let silent: Vec<Client> = (0..4).map(|_| Client::connect_raw(server.addr)).collect();
    let started = Instant::now();
    let mut sessions = vec![server.login()];
    assert!(
        started.elapsed() < Duration::from_millis(1800),
        "a valid login had to wait for the silent sockets: {:?}",
        started.elapsed()
    );
    // Authenticated sessions are what --max-connections counts.
    for _ in 0..3 {
        sessions.push(server.login());
    }
    match Client::login(server.addr, USER, PASSWORD) {
        Err(e) => assert_eq!(e.code, "53300"),
        Ok(_) => panic!("a fifth session must be refused"),
    }
    assert_eq!(
        sessions[0].simple("SELECT COUNT(*) FROM nope").code(),
        "42P01"
    );
    drop(silent);
}

#[test]
fn connections_still_authenticating_have_their_own_cap() {
    let dir = TempDir::new();
    // The cap is max(16, 2 * --max-connections) = 16.
    let server = Server::db(&dir, &["--max-connections", "1"]);
    let silent: Vec<Client> = (0..24).map(|_| Client::connect_raw(server.addr)).collect();
    std::thread::sleep(Duration::from_millis(500));
    let closed = silent.iter().filter(|c| closed_by_peer(c)).count();
    assert_eq!(closed, 8, "16 may wait, the other 8 are dropped at once");
    // The waiting ones are cut off by the two-second startup deadline and the door opens again.
    let started = Instant::now();
    while silent.iter().any(|c| !closed_by_peer(c)) {
        assert!(started.elapsed() < Duration::from_secs(6), "still waiting");
        std::thread::sleep(Duration::from_millis(100));
    }
    let mut c = server.login();
    assert_eq!(c.simple("SELECT COUNT(*) FROM nope").code(), "42P01");
}

/// Startup, then the first SASL round with a made-up proof. Returns the salt the server offered
/// and the error that ended the exchange.
fn failed_exchange(addr: SocketAddr, user: &str) -> (String, PgErr) {
    let mut c = Client::connect_raw(addr);
    c.send_startup(user);
    let (tag, body) = c.recv().expect("closed after startup");
    assert_eq!(
        (tag, i32::from_be_bytes(body[..4].try_into().unwrap())),
        (b'R', 10),
        "{user:?} must be offered SCRAM like everybody else"
    );
    let nonce = b64(&[9u8; 15]);
    let first = format!("n,,n=,r={nonce}");
    let mut init = b"SCRAM-SHA-256\0".to_vec();
    init.extend_from_slice(&i32b(first.len() as i32));
    init.extend_from_slice(first.as_bytes());
    c.send(b'p', &init);
    let (tag, body) = c.recv().expect("closed after SASLInitialResponse");
    assert_eq!(
        (tag, i32::from_be_bytes(body[..4].try_into().unwrap())),
        (b'R', 11)
    );
    let server_first = String::from_utf8(body[4..].to_vec()).unwrap();
    let field = |name: &str| {
        server_first
            .split(',')
            .find_map(|p| p.strip_prefix(name))
            .unwrap()
            .to_string()
    };
    let final_message = format!("c=biws,r={},p={}", field("r="), b64(&[0u8; 32]));
    c.send(b'p', final_message.as_bytes());
    let (tag, body) = c.recv().expect("closed after the proof");
    assert_eq!(tag, b'E');
    (field("s="), parse_error(&body))
}

#[test]
fn unknown_user_fails_at_the_same_step_as_a_wrong_password() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    let (real_salt, real) = failed_exchange(server.addr, USER);
    let (ghost_salt, ghost) = failed_exchange(server.addr, "someone");
    let (ghost_again, _) = failed_exchange(server.addr, "someone");
    let (other_salt, _) = failed_exchange(server.addr, "another");
    assert_eq!(
        (real.code.as_str(), ghost.code.as_str()),
        ("28P01", "28P01")
    );
    assert_eq!(real.severity, ghost.severity);
    assert_eq!(
        real.message.replace(USER, "X"),
        ghost.message.replace("someone", "X"),
        "same text apart from the name"
    );
    // The salt of a name that does not exist is stable (a real user's is) and still differs from
    // name to name, so comparing salts does not reveal which name is real.
    assert_eq!(ghost_salt, ghost_again);
    assert_ne!(ghost_salt, other_salt);
    assert_ne!(ghost_salt, real_salt);
    // The real password still gets in.
    server.login();
}

#[test]
fn a_failed_login_is_answered_after_a_delay() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    for (user, password) in [(USER, "wrong"), ("someone", PASSWORD)] {
        let started = Instant::now();
        let err = Client::login(server.addr, user, password).err().unwrap();
        let took = started.elapsed();
        assert_eq!(err.code, "28P01");
        assert!(took >= Duration::from_millis(900), "{user}: {took:?}");
        assert!(took < Duration::from_secs(5), "{user}: {took:?}");
    }
    // A correct login is not slowed down.
    let started = Instant::now();
    server.login();
    assert!(started.elapsed() < Duration::from_millis(900));
}

#[test]
fn prepared_statements_are_limited_by_bytes_not_only_by_count() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &["--max-connections", "4"]);
    let mut keeper = server.login();
    seed(&mut keeper);
    let mut c = server.login();
    // 64 statements of 8 MiB would be 512 MiB held by one connection; 1000 allowed 8 GB.
    let sql = wide_insert_of(8 * 1024 * 1024);
    for i in 0..64 {
        let (tag, body) = parse_msg(&format!("s{i}"), &sql, &[]);
        c.send(tag, &body);
    }
    c.send(b'S', &[]);
    let r = c.collect();
    assert_eq!(r.code(), "54000", "{:?}", r.error);
    let accepted = r.seen.iter().filter(|t| **t == b'1').count();
    assert!(
        (16..=40).contains(&accepted),
        "{accepted} statements were accepted before the budget tripped"
    );
    assert_eq!(r.status, b'I');
    // The connection is still usable: free the memory and carry on.
    assert_eq!(c.simple("DEALLOCATE ALL").tags, ["DEALLOCATE ALL"]);
    let r = c.pipeline(&[parse_msg("again", &sql, &[])]);
    assert!(r.error.is_none(), "{:?}", r.error);
    assert_eq!(c.count(), "3");
    // And so is the rest of the server.
    assert_eq!(keeper.count(), "3");
    assert_eq!(server.login().count(), "3");
}

#[test]
fn queued_transaction_bytes_are_budgeted() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &["--max-connections", "4"]);
    let mut c = server.login();
    c.ok(&wide_create());
    c.ok("BEGIN");
    let sql = wide_insert_of(8 * 1024 * 1024);
    let mut accepted = 0;
    let mut failure = None;
    for _ in 0..64 {
        let r = c.simple(&sql);
        if r.error.is_some() {
            failure = Some(r);
            break;
        }
        accepted += 1;
    }
    let r = failure.expect("the budget never tripped");
    assert_eq!((r.code(), r.status), ("54000", b'E'));
    assert!((5..=40).contains(&accepted), "{accepted} statements queued");
    // The failed transaction is dropped by ROLLBACK, which frees the memory again.
    assert_eq!(c.simple("ROLLBACK").tags, ["ROLLBACK"]);
    assert_eq!(c.ok("SELECT COUNT(*) FROM wide")[0][0], "0");
    c.ok("BEGIN");
    assert_eq!(c.simple(&sql).code(), "");
    c.ok("ROLLBACK");
    assert_eq!(server.login().ok("SELECT COUNT(*) FROM wide")[0][0], "0");
}

#[test]
fn rows_kept_for_suspended_portals_are_budgeted() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &["--max-connections", "4"]);
    let mut c = server.login();
    c.ok(&wide_create());
    c.ok(&wide_insert(50_000, "1"));
    let reply = c.pipeline(&[parse_msg("q", "SELECT * FROM wide", &[])]);
    assert!(reply.error.is_none(), "{:?}", reply.error);
    // Each open portal holds the whole result (50,000 rows of 64 values, about 100 MB).
    let r = c.pipeline(&[
        bind_msg("p1", "q", &[], &[], &[]),
        execute_msg("p1", 1),
        bind_msg("p2", "q", &[], &[], &[]),
        execute_msg("p2", 1),
        bind_msg("p3", "q", &[], &[], &[]),
        execute_msg("p3", 1),
    ]);
    assert_eq!(r.code(), "54000", "{:?}", r.error);
    assert_eq!(r.rows.len(), 2, "two portals fit, the third is refused");
    assert_eq!(r.status, b'I');
    // Sync ended the implicit transaction and closed the portals, so the memory is free again.
    let r = c.pipeline(&[bind_msg("p1", "q", &[], &[], &[]), execute_msg("p1", 1)]);
    assert!(r.error.is_none(), "{:?}", r.error);
    assert_eq!(r.rows.len(), 1);
}

#[test]
fn portals_die_with_their_transaction_and_the_unnamed_one_at_the_next_bind() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    let mut c = server.login();
    seed(&mut c);
    let r = c.pipeline(&[
        parse_msg("s", "SELECT COUNT(*) FROM events", &[]),
        bind_msg("p", "s", &[], &[], &[]),
    ]);
    assert!(r.error.is_none(), "{:?}", r.error);
    // Outside a transaction block Sync ends the implicit transaction and closes every portal.
    assert_eq!(c.pipeline(&[execute_msg("p", 0)]).code(), "34000");
    // Within one batch a portal works, and a second Bind of the unnamed portal replaces the first.
    let r = c.pipeline(&[
        bind_msg("", "s", &[], &[], &[]),
        bind_msg("", "s", &[], &[], &[]),
        execute_msg("", 0),
    ]);
    assert!(r.error.is_none(), "{:?}", r.error);
    assert_eq!(r.text(), [["3"]]);
    // In a transaction block portals live until COMMIT or ROLLBACK, not until Sync.
    c.ok("BEGIN");
    let r = c.pipeline(&[bind_msg("p", "s", &[], &[], &[])]);
    assert!(r.error.is_none(), "{:?}", r.error);
    let r = c.pipeline(&[execute_msg("p", 0)]);
    assert_eq!((r.code(), r.text()), ("", vec![vec!["3".to_string()]]));
    let r = c.pipeline(&[bind_msg("q", "s", &[], &[], &[])]);
    assert!(r.error.is_none(), "{:?}", r.error);
    c.ok("COMMIT");
    assert_eq!(c.pipeline(&[execute_msg("p", 0)]).code(), "34000");
    assert_eq!(c.pipeline(&[execute_msg("q", 0)]).code(), "34000");
    // The same through the extended protocol's own COMMIT.
    c.ok("BEGIN");
    let r = c.pipeline(&[
        parse_msg("commit", "COMMIT", &[]),
        bind_msg("p", "s", &[], &[], &[]),
        bind_msg("c", "commit", &[], &[], &[]),
        execute_msg("c", 0),
    ]);
    assert!(r.error.is_none(), "{:?}", r.error);
    assert_eq!(r.status, b'I');
    assert_eq!(c.pipeline(&[execute_msg("p", 0)]).code(), "34000");
    assert_eq!(c.pipeline(&[execute_msg("c", 0)]).code(), "34000");
}

#[test]
fn twenty_thousand_inserts_in_one_transaction_commit_quickly() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    let mut c = server.login();
    c.ok("CREATE TABLE t (a BIGINT NOT NULL)");
    let mut sql = String::from("BEGIN;");
    for i in 0..20_000 {
        sql.push_str(&format!("INSERT INTO t VALUES ({i});"));
    }
    sql.push_str("COMMIT");
    let started = Instant::now();
    let r = c.simple(&sql);
    let took = started.elapsed();
    assert!(r.error.is_none(), "{:?}", r.error);
    assert_eq!(r.tags.len(), 20_002);
    assert!(took < Duration::from_secs(10), "{took:?}");
    eprintln!("20,000 queued INSERTs and COMMIT took {took:?}");
    assert_eq!(server.login().ok("SELECT COUNT(*) FROM t")[0][0], "20000");
}

#[test]
fn a_transaction_may_queue_100000_statements() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &[]);
    let mut c = server.login();
    c.ok("CREATE TABLE t (a BIGINT NOT NULL)");
    let inserts = |n: usize| {
        let mut sql = String::from("BEGIN;");
        for i in 0..n {
            sql.push_str(&format!("INSERT INTO t VALUES ({i});"));
        }
        sql
    };
    let started = Instant::now();
    let r = c.simple(&inserts(100_001));
    assert_eq!((r.code(), r.status), ("54000", b'E'), "{:?}", r.error);
    assert_eq!(
        r.tags.len(),
        100_001,
        "BEGIN and 100,000 INSERTs, then the refusal"
    );
    eprintln!("100,001 queued INSERTs took {:?}", started.elapsed());
    assert!(
        started.elapsed() < Duration::from_secs(20),
        "{:?}",
        started.elapsed()
    );
    assert_eq!(c.simple("ROLLBACK").tags, ["ROLLBACK"]);
    assert_eq!(c.ok("SELECT COUNT(*) FROM t")[0][0], "0");
    // Exactly the cap is fine.
    let mut sql = inserts(100_000);
    sql.push_str("COMMIT");
    let r = c.simple(&sql);
    assert!(r.error.is_none(), "{:?}", r.error);
    assert_eq!(c.ok("SELECT COUNT(*) FROM t")[0][0], "100000");
}

#[test]
fn a_commit_over_the_wal_record_limit_fails_cleanly() {
    let dir = TempDir::new();
    let server = Server::db(&dir, &["--max-connections", "4"]);
    let mut c = server.login();
    c.ok(&wide_create());
    c.ok("BEGIN");
    // 6 x 10,000 rows x 64 values of -2^63 is about 80 MB of log record: over the 64 MiB limit
    // although the queue itself (about 115 MB) is inside the connection budget.
    let sql = wide_insert(10_000, "-9223372036854775808");
    for _ in 0..6 {
        let r = c.simple(&sql);
        assert!(r.error.is_none(), "{:?}", r.error);
    }
    let r = c.simple("COMMIT");
    assert_eq!(r.code(), "54000", "{:?}", r.error);
    assert!(
        r.error.as_ref().unwrap().message.contains("64 MiB"),
        "{:?}",
        r.error
    );
    assert_eq!(r.status, b'I', "the session is idle again");
    // Nothing was applied, for this connection and for another one, and the database is not
    // stuck inside a transaction: autocommit writes work.
    let mut other = server.login();
    assert_eq!(other.ok("SELECT COUNT(*) FROM wide")[0][0], "0");
    other.ok(&wide_insert(1, "7"));
    assert_eq!(c.ok("SELECT COUNT(*) FROM wide")[0][0], "1");
    c.ok("BEGIN");
    c.ok(&wide_insert(2, "8"));
    c.ok("COMMIT");
    assert_eq!(other.ok("SELECT COUNT(*) FROM wide")[0][0], "3");
}
