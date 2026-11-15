//! One client connection: startup, SCRAM authentication and the simple/extended query loops.
use crate::backend::{Backend, Op, Pending};
use crate::scram::{self, ScramError};
use crate::text::{float_text, placeholders, split_statements, substitute};
use crate::wire::{
    AUTH_TIMEOUT, Conn, Cursor, Fatal, MAX_MESSAGE, MAX_PREAUTH_MESSAGE, PgError, STARTUP_TIMEOUT,
    protocol_violation, put_cstr,
};
use kestrel_sql::sql::{self, Expr, Statement};
use kestrel_sql::{QueryResult, Value};
use std::collections::HashMap;
use std::io::{self, Write};
use std::net::TcpStream;
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::{Duration, Instant};

const INT8: u32 = 20;
const FLOAT8: u32 = 701;
const TEXT: u32 = 25;
const MAX_OBJECTS: usize = 1000;
/// Bytes one connection may keep alive between messages: prepared statement text, writes queued
/// in a transaction, and the unsent rows of suspended portals. An estimate, not an allocator
/// count, but it grows with the real memory, so a client cannot make the server allocate
/// without bound. Past it a statement fails with `54000` and the connection stays usable.
const CONNECTION_BUDGET: usize = 256 * 1024 * 1024;
/// Pause before a failed password is answered, in the connection's own thread, to slow down
/// online guessing.
pub const AUTH_FAILURE_DELAY: Duration = Duration::from_secs(1);

pub struct Shared {
    pub backend: Backend,
    pub verifier: scram::Verifier,
    /// Keys the stand-in verifiers handed to unknown user names.
    pub mock_secret: [u8; 32],
    pub user: String,
    pub server_version: String,
    /// Authenticated sessions (`--max-connections` counts only these).
    pub active: Arc<AtomicUsize>,
    pub max_sessions: usize,
    /// Connections still in startup / authentication, each held by its own thread.
    pub preauth: Arc<AtomicUsize>,
    pub preauth_cap: usize,
}

/// One unit of a connection counter; released on drop.
pub struct Slot(Arc<AtomicUsize>);

impl Slot {
    pub fn acquire(counter: &Arc<AtomicUsize>, max: usize) -> Option<Slot> {
        if counter.fetch_add(1, Ordering::SeqCst) >= max {
            counter.fetch_sub(1, Ordering::SeqCst);
            None
        } else {
            Some(Slot(Arc::clone(counter)))
        }
    }
}

impl Drop for Slot {
    fn drop(&mut self) {
        self.0.fetch_sub(1, Ordering::SeqCst);
    }
}

pub fn log(id: u64, message: &str) {
    let _ = writeln!(io::stderr(), "conn {id}: {message}");
}

fn clean(text: &str) -> String {
    text.chars()
        .take(48)
        .map(|c| {
            if c.is_ascii_graphic() || c == ' ' {
                c
            } else {
                '?'
            }
        })
        .collect()
}

enum SessErr {
    Soft(PgError),
    Fatal(Fatal),
}
impl From<PgError> for SessErr {
    fn from(e: PgError) -> Self {
        SessErr::Soft(e)
    }
}
impl From<Fatal> for SessErr {
    fn from(e: Fatal) -> Self {
        SessErr::Fatal(e)
    }
}
impl From<io::Error> for SessErr {
    fn from(e: io::Error) -> Self {
        SessErr::Fatal(e.into())
    }
}
type R<T = ()> = Result<T, SessErr>;

fn syntax(e: kestrel_sql::Error) -> PgError {
    PgError::new("42601", e.to_string())
}

fn aborted() -> PgError {
    PgError::new(
        "25P02",
        "current transaction is aborted, commands ignored until end of transaction block",
    )
}

/// A statement of the simple-query protocol: engine SQL, or a server-level command.
enum Parsed {
    Statement(Statement),
    Deallocate(Option<String>),
}

/// `DEALLOCATE [PREPARE] name` gives `Some(Some(name))`, `DEALLOCATE [PREPARE] ALL` `Some(None)`.
fn deallocate_target(sql: &str) -> Option<Option<String>> {
    let words: Vec<&str> = sql.split_whitespace().collect();
    let mut rest = words.as_slice();
    if !rest.first()?.eq_ignore_ascii_case("deallocate") {
        return None;
    }
    rest = &rest[1..];
    if rest
        .first()
        .is_some_and(|w| w.eq_ignore_ascii_case("prepare"))
    {
        rest = &rest[1..];
    }
    match rest {
        [name] if name.eq_ignore_ascii_case("all") => Some(None),
        [name] => Some(Some(name.trim_end_matches(';').to_string())),
        _ => None,
    }
}

// ---- startup and authentication ----------------------------------------------------------

struct Startup {
    user: String,
}

/// Reads the startup packet(s). `None` for a cancel request, which is accepted and ignored.
fn startup(conn: &mut Conn) -> Result<Option<Startup>, Fatal> {
    for _ in 0..4 {
        let body = conn.read_startup()?;
        let mut c = Cursor::new(&body);
        let code = c.i32()? as u32;
        match code {
            80877103 | 80877104 => {
                // SSLRequest / GSSENCRequest: there is no TLS, the client continues in clear.
                conn.raw(b"N")?;
                continue;
            }
            80877102 => return Ok(None),
            _ => {}
        }
        let (major, minor) = (code >> 16, code & 0xffff);
        if major != 3 {
            return Err(Fatal::Pg(PgError::fatal(
                "0A000",
                format!("unsupported frontend protocol {major}.{minor}: server supports 3.0"),
            )));
        }
        let mut user = None;
        let mut unknown = Vec::new();
        loop {
            let name = c.cstr()?;
            if name.is_empty() {
                break;
            }
            let value = c.cstr()?;
            if name == "user" {
                user = Some(value.to_string());
            } else if name.starts_with("_pq_.") {
                unknown.push(name);
            } else if name == "replication" && !matches!(value, "false" | "off" | "0" | "no") {
                return Err(Fatal::Pg(PgError::fatal(
                    "0A000",
                    "replication connections are not supported",
                )));
            }
        }
        if minor != 0 || !unknown.is_empty() {
            conn.message(b'v', |b| {
                b.extend_from_slice(&0i32.to_be_bytes());
                b.extend_from_slice(&(unknown.len() as i32).to_be_bytes());
                for name in &unknown {
                    put_cstr(b, name);
                }
            });
        }
        let user = user.filter(|u| !u.is_empty()).ok_or_else(|| {
            Fatal::Pg(PgError::fatal(
                "28000",
                "no user name specified in startup packet",
            ))
        })?;
        return Ok(Some(Startup { user }));
    }
    Err(protocol_violation("too many negotiation packets"))
}

fn auth_failed(user: &str) -> Fatal {
    Fatal::Pg(PgError::fatal(
        "28P01",
        format!(
            "password authentication failed for user \"{}\"",
            clean(user)
        ),
    ))
}

fn random<const N: usize>() -> Result<[u8; N], Fatal> {
    let mut buf = [0u8; N];
    getrandom::fill(&mut buf)
        .map_err(|_| Fatal::Pg(PgError::fatal("XX000", "random source unavailable")))?;
    Ok(buf)
}

fn read_sasl(conn: &mut Conn) -> Result<Vec<u8>, Fatal> {
    match conn.read_message(MAX_PREAUTH_MESSAGE)? {
        Some((b'p', body)) => Ok(body),
        Some(_) => Err(protocol_violation("expected a SASL response message")),
        None => Err(io::Error::from(io::ErrorKind::UnexpectedEof).into()),
    }
}

/// Runs the SCRAM exchange and returns the `server-final-message`. An unknown user name goes
/// through the same exchange against a stand-in verifier, so a wrong user and a wrong password
/// fail at the same step with the same message.
fn authenticate(conn: &mut Conn, shared: &Shared, user: &str) -> Result<String, Fatal> {
    let known = user == shared.user;
    let mock;
    let verifier = if known {
        &shared.verifier
    } else {
        mock = scram::Verifier::mock(&shared.mock_secret, user);
        &mock
    };
    conn.auth(10, b"SCRAM-SHA-256\0\0");
    conn.flush()?;
    let body = read_sasl(conn)?;
    let mut c = Cursor::new(&body);
    if c.cstr()? != "SCRAM-SHA-256" {
        return Err(Fatal::Pg(PgError::fatal(
            "28000",
            "client selected an unsupported SASL mechanism; only SCRAM-SHA-256 is offered",
        )));
    }
    let n = c.i32()?;
    let first = if n < 0 { &[][..] } else { c.bytes(n as usize)? };
    c.finish()?;
    let first = std::str::from_utf8(first)
        .map_err(|_| protocol_violation("SASL initial response is not UTF-8"))?;
    let nonce = scram::b64_encode(&random::<18>()?);
    let server = scram::Server::start(verifier, first, &nonce)
        .map_err(|_| protocol_violation("malformed SCRAM client-first-message"))?;
    conn.auth(11, server.server_first().as_bytes());
    conn.flush()?;
    let body = read_sasl(conn)?;
    let text =
        std::str::from_utf8(&body).map_err(|_| protocol_violation("SASL response is not UTF-8"))?;
    match server.finish(text) {
        Ok(final_message) if known => Ok(final_message),
        Ok(_) | Err(ScramError::BadProof) => Err(auth_failed(user)),
        Err(ScramError::Malformed(_)) => {
            Err(protocol_violation("malformed SCRAM client-final-message"))
        }
    }
}

/// Runs a whole connection. `pre` is this connection's place among those still authenticating;
/// it is released as soon as the session is accepted or the connection ends.
pub fn serve(stream: TcpStream, shared: &Shared, id: u64, pre: Slot) -> Result<(), Fatal> {
    let started = Instant::now();
    let mut conn = Conn::new(stream, started + STARTUP_TIMEOUT)?;
    let result = serve_inner(&mut conn, shared, id, started + AUTH_TIMEOUT, pre);
    if let Err(Fatal::Pg(e)) = &result {
        conn.error(e);
    }
    let _ = conn.flush();
    result
}

fn serve_inner(
    conn: &mut Conn,
    shared: &Shared,
    id: u64,
    auth_deadline: Instant,
    pre: Slot,
) -> Result<(), Fatal> {
    let Some(start) = startup(conn)? else {
        log(id, "cancel request ignored");
        return Ok(());
    };
    conn.set_deadline(auth_deadline);
    let too_many = || {
        log(id, "refused: too many connections");
        Fatal::Pg(PgError::fatal("53300", "sorry, too many clients already"))
    };
    // A cheap early answer for a full server; the binding check comes after authentication.
    if shared.active.load(Ordering::SeqCst) >= shared.max_sessions {
        return Err(too_many());
    }
    let final_message = match authenticate(conn, shared, &start.user) {
        Ok(message) => message,
        Err(e) => {
            if matches!(&e, Fatal::Pg(p) if p.code == "28P01") {
                log(
                    id,
                    &format!("auth failed for user \"{}\"", clean(&start.user)),
                );
                // Still holding the pre-authentication slot, so guessing is rate limited too.
                std::thread::sleep(AUTH_FAILURE_DELAY);
            }
            return Err(e);
        }
    };
    let Some(_session) = Slot::acquire(&shared.active, shared.max_sessions) else {
        return Err(too_many());
    };
    drop(pre);
    conn.auth(12, final_message.as_bytes());
    conn.auth(0, &[]);
    conn.authenticated()?;
    for (name, value) in [
        ("server_version", shared.server_version.as_str()),
        ("server_encoding", "UTF8"),
        ("client_encoding", "UTF8"),
        ("DateStyle", "ISO, MDY"),
        ("integer_datetimes", "on"),
        ("standard_conforming_strings", "on"),
        ("TimeZone", "UTC"),
        ("IntervalStyle", "postgres"),
        ("is_superuser", "off"),
    ] {
        conn.parameter_status(name, value);
    }
    let pid = i32::from_be_bytes(random::<4>()?) & 0x7fff_ffff;
    let secret = i32::from_be_bytes(random::<4>()?);
    conn.message(b'K', |b| {
        b.extend_from_slice(&pid.to_be_bytes());
        b.extend_from_slice(&secret.to_be_bytes());
    });
    conn.ready(b'I');
    conn.flush()?;
    log(
        id,
        &format!("authenticated user \"{}\"", clean(&start.user)),
    );
    Session {
        conn,
        shared,
        tx: Tx::Idle,
        statements: HashMap::new(),
        portals: HashMap::new(),
        skip: false,
    }
    .run()
}

// ---- the query loop ----------------------------------------------------------------------

enum Tx {
    Idle,
    /// Writes queued until COMMIT; reads see committed data only.
    Active(Pending),
    Failed,
}

/// A prepared statement keeps only its text and parameter types; the syntax tree is rebuilt
/// when it is needed, so that a statement costs about as many bytes as the client sent.
struct Prepared {
    sql: String,
    param_oids: Vec<u32>,
    /// Bytes charged to the connection budget.
    cost: usize,
}

enum PortalState {
    Fresh,
    Rows {
        cols: Vec<(String, u32)>,
        rows: Vec<Vec<Value>>,
        pos: usize,
        tag: String,
    },
    Done(String),
}

/// A bound statement. Its text (parameters substituted) is parsed again at `Execute`.
struct Portal {
    sql: String,
    formats: Vec<i16>,
    state: PortalState,
    /// Bytes charged to the connection budget, including any rows kept for a suspended portal.
    cost: usize,
}

/// Fixed bookkeeping per prepared statement or portal.
const OBJECT_BASE: usize = 256;

/// Bytes a materialised result keeps alive.
fn rows_cost(cols: &[(String, u32)], rows: &[Vec<Value>]) -> usize {
    let cells: usize = rows
        .iter()
        .map(|row| {
            row.len() * std::mem::size_of::<Value>()
                + row
                    .iter()
                    .map(|v| if let Value::Text(s) = v { s.len() } else { 0 })
                    .sum::<usize>()
        })
        .sum();
    cols.iter().map(|c| c.0.len() + 32).sum::<usize>() + std::mem::size_of_val(rows) + cells
}

/// The statement of a stored text; `None` for an empty query.
fn parse_stored(sql: &str) -> Result<Option<Statement>, PgError> {
    if sql.is_empty() {
        Ok(None)
    } else {
        sql::parse(sql).map(Some).map_err(syntax)
    }
}

fn budget_exceeded() -> PgError {
    PgError::new(
        "54000",
        "this connection holds too much memory (prepared statements, queued writes, open \
         portals); close some or end the transaction",
    )
}

enum Exec {
    Tag(String),
    Rows {
        cols: Vec<(String, u32)>,
        rows: Vec<Vec<Value>>,
        tag: String,
    },
}

struct Session<'a> {
    conn: &'a mut Conn,
    shared: &'a Shared,
    tx: Tx,
    statements: HashMap<String, Prepared>,
    portals: HashMap<String, Portal>,
    /// After an extended-protocol error everything is discarded until Sync.
    skip: bool,
}

fn result_oids(statement: &Statement, columns: usize) -> Vec<u32> {
    match statement {
        Statement::Select(q) if !matches!(q.items[0].expr, Expr::Star) => q
            .items
            .iter()
            .map(|i| {
                if matches!(i.expr, Expr::Avg(_)) {
                    FLOAT8
                } else {
                    INT8
                }
            })
            .collect(),
        Statement::Select(_) => vec![INT8; columns],
        _ => vec![TEXT; columns],
    }
}

/// Result columns before execution, from the schema and the parsed statement.
fn describe(
    backend: &Backend,
    statement: &Statement,
) -> Result<Option<Vec<(String, u32)>>, PgError> {
    match statement {
        Statement::Select(q) => {
            let schema = backend.schema(&q.table)?;
            let known = |c: &String| {
                if schema.contains(c) {
                    Ok(())
                } else {
                    Err(PgError::new(
                        "42703",
                        format!("column \"{c}\" does not exist"),
                    ))
                }
            };
            let mut cols = Vec::new();
            for item in &q.items {
                match &item.expr {
                    Expr::Star => cols.extend(schema.iter().map(|c| (c.clone(), INT8))),
                    Expr::Count => cols.push((item.alias.clone(), INT8)),
                    Expr::Column(c) | Expr::Sum(c) | Expr::Min(c) | Expr::Max(c) => {
                        known(c)?;
                        cols.push((item.alias.clone(), INT8));
                    }
                    Expr::Avg(c) => {
                        known(c)?;
                        cols.push((item.alias.clone(), FLOAT8));
                    }
                }
            }
            Ok(Some(cols))
        }
        Statement::Explain(_) => Ok(Some(vec![("plan".into(), TEXT)])),
        _ => Ok(None),
    }
}

fn row_description(conn: &mut Conn, cols: &[(String, u32)], formats: &[i16]) {
    conn.message(b'T', |b| {
        b.extend_from_slice(&(cols.len() as i16).to_be_bytes());
        for (i, (name, oid)) in cols.iter().enumerate() {
            put_cstr(b, name);
            b.extend_from_slice(&0i32.to_be_bytes());
            b.extend_from_slice(&0i16.to_be_bytes());
            b.extend_from_slice(&oid.to_be_bytes());
            b.extend_from_slice(&(if *oid == TEXT { -1i16 } else { 8 }).to_be_bytes());
            b.extend_from_slice(&(-1i32).to_be_bytes());
            b.extend_from_slice(&format_of(formats, i, cols.len()).to_be_bytes());
        }
    });
}

fn format_of(formats: &[i16], i: usize, n: usize) -> i16 {
    match formats.len() {
        0 => 0,
        1 => formats[0],
        k if k == n => formats[i],
        _ => 0,
    }
}

fn check_formats(formats: &[i16], columns: usize) -> Result<(), PgError> {
    if formats.len() > 1 && formats.len() != columns {
        return Err(PgError::new(
            "08P01",
            format!(
                "bind message has {} result formats but the query has {columns} columns",
                formats.len()
            ),
        ));
    }
    Ok(())
}

/// Integers outside bigint cannot be sent as int8 (SUM can exceed it; the engine uses i128).
fn check_rows(rows: &[Vec<Value>]) -> Result<(), PgError> {
    let bad = rows
        .iter()
        .flatten()
        .any(|v| matches!(v, Value::Int(i) if i64::try_from(*i).is_err()));
    if bad {
        Err(PgError::new(
            "22003",
            "bigint out of range: the result does not fit the int8 column type",
        ))
    } else {
        Ok(())
    }
}

fn put_cell(out: &mut Vec<u8>, value: &Value, oid: u32, binary: bool) {
    if matches!(value, Value::Null) {
        out.extend_from_slice(&(-1i32).to_be_bytes());
        return;
    }
    let at = out.len();
    out.extend_from_slice(&[0; 4]);
    match value {
        Value::Int(i) if oid == FLOAT8 => {
            let f = *i as f64;
            if binary {
                out.extend_from_slice(&f.to_bits().to_be_bytes());
            } else {
                out.extend_from_slice(float_text(f).as_bytes());
            }
        }
        Value::Int(i) if binary && oid != TEXT => {
            out.extend_from_slice(&(*i as i64).to_be_bytes());
        }
        Value::Int(i) => out.extend_from_slice(i.to_string().as_bytes()),
        Value::Float(f) if binary && oid != TEXT => {
            out.extend_from_slice(&f.to_bits().to_be_bytes());
        }
        Value::Float(f) => out.extend_from_slice(float_text(*f).as_bytes()),
        Value::Text(s) => out.extend_from_slice(s.as_bytes()),
        Value::Null => {}
    }
    let len = (out.len() - at - 4) as i32;
    out[at..at + 4].copy_from_slice(&len.to_be_bytes());
}

fn write_rows(conn: &mut Conn, rows: &[Vec<Value>], cols: &[(String, u32)], formats: &[i16]) {
    for row in rows {
        conn.message(b'D', |b| {
            b.extend_from_slice(&(row.len() as i16).to_be_bytes());
            for (i, value) in row.iter().enumerate() {
                let oid = cols.get(i).map_or(TEXT, |c| c.1);
                put_cell(b, value, oid, format_of(formats, i, row.len()) == 1);
            }
        });
    }
}

fn count(c: &mut Cursor) -> Result<usize, Fatal> {
    usize::try_from(c.i16()?).map_err(|_| protocol_violation("negative count in Bind"))
}

fn param_value(raw: Option<&[u8]>, binary: bool, oid: u32, n: usize) -> Result<i64, PgError> {
    let Some(raw) = raw else {
        return Err(PgError::new(
            "22P02",
            format!("parameter ${n} is NULL; only integer parameters are supported"),
        ));
    };
    if binary {
        return match (oid, raw.len()) {
            (21, 2) => Ok(i64::from(i16::from_be_bytes(raw.try_into().unwrap()))),
            (23, 4) => Ok(i64::from(i32::from_be_bytes(raw.try_into().unwrap()))),
            (INT8, 8) => Ok(i64::from_be_bytes(raw.try_into().unwrap())),
            (21 | 23 | INT8, _) => Err(PgError::new(
                "22P03",
                format!("incorrect binary data format for parameter ${n}"),
            )),
            _ => Err(PgError::new(
                "0A000",
                format!("binary parameter ${n} needs an int2, int4 or int8 type"),
            )),
        };
    }
    let text = std::str::from_utf8(raw).unwrap_or("");
    text.parse::<i64>().map_err(|_| {
        let shown: String = text.chars().take(60).collect();
        PgError::new(
            "22P02",
            format!("invalid input syntax for type bigint: \"{shown}\" (parameter ${n})"),
        )
    })
}

impl Session<'_> {
    fn status(&self) -> u8 {
        match self.tx {
            Tx::Idle => b'I',
            Tx::Active(_) => b'T',
            Tx::Failed => b'E',
        }
    }

    fn run(&mut self) -> Result<(), Fatal> {
        loop {
            if self.conn.out.len() > 1 << 20 {
                self.conn.flush()?;
            }
            let Some((tag, body)) = self.conn.read_message(MAX_MESSAGE)? else {
                return Ok(());
            };
            if tag == b'X' {
                return Ok(());
            }
            if self.skip && tag != b'S' {
                continue;
            }
            let result = match tag {
                b'Q' => {
                    self.simple_query(&body)?;
                    continue;
                }
                b'P' => self.on_parse(&body),
                b'B' => self.on_bind(&body),
                b'D' => self.on_describe(&body),
                b'E' => self.on_execute(&body),
                b'C' => self.on_close(&body),
                b'H' => self.conn.flush().map_err(SessErr::from),
                b'S' => {
                    self.skip = false;
                    // Outside a transaction block Sync ends the implicit transaction.
                    if matches!(self.tx, Tx::Idle) {
                        self.portals.clear();
                    }
                    self.conn.ready(self.status());
                    self.conn.flush().map_err(SessErr::from)
                }
                other => Err(SessErr::Fatal(protocol_violation(format!(
                    "invalid frontend message type {other}"
                )))),
            };
            match result {
                Ok(()) => {}
                Err(SessErr::Soft(e)) => {
                    self.fail(&e);
                    self.skip = true;
                }
                Err(SessErr::Fatal(f)) => return Err(f),
            }
        }
    }

    /// Bytes this connection keeps alive between messages (see `CONNECTION_BUDGET`).
    fn retained(&self) -> usize {
        let queued = match &self.tx {
            Tx::Active(pending) => pending.bytes(),
            _ => 0,
        };
        let statements: usize = self.statements.iter().map(|(n, s)| n.len() + s.cost).sum();
        let portals: usize = self.portals.iter().map(|(n, p)| n.len() + p.cost).sum();
        queued + statements + portals
    }

    fn fail(&mut self, e: &PgError) {
        self.conn.error(e);
        if matches!(self.tx, Tx::Active(_)) {
            self.tx = Tx::Failed;
        }
    }

    // ---- statement execution (shared by both protocols) ---------------------------------

    fn run_statement(&mut self, statement: &Statement, sql: &str) -> Result<Exec, PgError> {
        if matches!(self.tx, Tx::Failed) {
            return match statement {
                Statement::Commit | Statement::Rollback => {
                    self.tx = Tx::Idle;
                    self.portals.clear();
                    Ok(Exec::Tag("ROLLBACK".into()))
                }
                _ => Err(aborted()),
            };
        }
        let result = self.execute_in_tx(statement, sql);
        if result.is_err() && matches!(self.tx, Tx::Active(_)) {
            self.tx = Tx::Failed;
        }
        result
    }

    fn execute_in_tx(&mut self, statement: &Statement, sql: &str) -> Result<Exec, PgError> {
        let shared = self.shared;
        match statement {
            Statement::Begin => {
                if matches!(self.tx, Tx::Idle) {
                    self.tx = Tx::Active(Pending::default());
                }
                Ok(Exec::Tag("BEGIN".into()))
            }
            Statement::Commit => {
                let queue = match std::mem::replace(&mut self.tx, Tx::Idle) {
                    Tx::Active(queue) => queue,
                    _ => Pending::default(),
                };
                self.portals.clear();
                if !queue.is_empty() {
                    shared.backend.apply(queue.ops())?;
                }
                Ok(Exec::Tag("COMMIT".into()))
            }
            Statement::Rollback => {
                self.tx = Tx::Idle;
                self.portals.clear();
                Ok(Exec::Tag("ROLLBACK".into()))
            }
            Statement::Checkpoint => {
                if matches!(self.tx, Tx::Active(_)) {
                    return Err(PgError::new(
                        "25001",
                        "CHECKPOINT cannot run inside a transaction block",
                    ));
                }
                shared.backend.checkpoint()?;
                Ok(Exec::Tag("CHECKPOINT".into()))
            }
            Statement::Select(_) | Statement::Explain(_) => {
                let QueryResult { columns, rows, .. } = shared.backend.select(statement, sql)?;
                check_rows(&rows)?;
                let tag = if matches!(statement, Statement::Select(_)) {
                    format!("SELECT {}", rows.len())
                } else {
                    "EXPLAIN".into()
                };
                let oids = result_oids(statement, columns.len());
                let cols = columns.into_iter().zip(oids).collect();
                Ok(Exec::Rows { cols, rows, tag })
            }
            Statement::Create { .. } | Statement::Insert { .. } => {
                let op = Op::from_statement(statement, sql).expect("write statement");
                let empty = Pending::default();
                let pending = match &self.tx {
                    Tx::Active(queue) => queue,
                    _ => &empty,
                };
                shared.backend.check(&op, pending)?;
                if matches!(self.tx, Tx::Active(_))
                    && self.retained().saturating_add(op.cost()) > CONNECTION_BUDGET
                {
                    return Err(budget_exceeded());
                }
                let tag = match statement {
                    Statement::Insert { rows, .. } => format!("INSERT 0 {}", rows.len()),
                    _ => "CREATE TABLE".into(),
                };
                match &mut self.tx {
                    Tx::Active(queue) => queue.push(op),
                    _ => {
                        shared.backend.apply(&[op])?;
                    }
                }
                Ok(Exec::Tag(tag))
            }
        }
    }

    // ---- simple query -------------------------------------------------------------------

    fn simple_query(&mut self, body: &[u8]) -> Result<(), Fatal> {
        let mut c = Cursor::new(body);
        let sql = c.cstr()?;
        c.finish()?;
        match self.simple_inner(sql) {
            Ok(()) => {}
            Err(SessErr::Soft(e)) => self.fail(&e),
            Err(SessErr::Fatal(f)) => return Err(f),
        }
        // A simple query outside a transaction block is its own transaction.
        if matches!(self.tx, Tx::Idle) {
            self.portals.clear();
        }
        self.conn.ready(self.status());
        self.conn.flush()?;
        Ok(())
    }

    fn simple_inner(&mut self, sql: &str) -> R {
        let pieces = split_statements(sql);
        if pieces.is_empty() {
            self.conn.message(b'I', |_| {});
            return Ok(());
        }
        let mut parsed = Vec::with_capacity(pieces.len());
        for piece in &pieces {
            parsed.push(match deallocate_target(piece) {
                Some(target) => Parsed::Deallocate(target),
                None => Parsed::Statement(sql::parse(piece).map_err(syntax)?),
            });
        }
        let control = parsed.iter().any(|s| {
            matches!(
                s,
                Parsed::Statement(Statement::Begin | Statement::Commit | Statement::Rollback)
            )
        });
        // Like PostgreSQL, several statements in one simple query are one transaction unless
        // the string itself controls transactions.
        let implicit = parsed.len() > 1 && matches!(self.tx, Tx::Idle) && !control;
        let mark = self.conn.out.len();
        if implicit {
            self.tx = Tx::Active(Pending::default());
        }
        let mut failure = None;
        for (parsed, piece) in parsed.iter().zip(&pieces) {
            let result = match parsed {
                Parsed::Statement(statement) => self.run_statement(statement, piece),
                Parsed::Deallocate(target) => self.deallocate(target.as_deref()),
            };
            match result {
                Ok(exec) => self.send_exec(exec, &[]),
                Err(e) => {
                    failure = Some(e);
                    break;
                }
            }
        }
        if implicit {
            let queue = match std::mem::replace(&mut self.tx, Tx::Idle) {
                Tx::Active(queue) => queue,
                _ => Pending::default(),
            };
            if failure.is_none()
                && !queue.is_empty()
                && let Err(e) = self.shared.backend.apply(queue.ops())
            {
                // Nothing was applied, so do not report the statements as completed.
                self.conn.out.truncate(mark);
                failure = Some(e);
            }
        }
        failure.map_or(Ok(()), |e| Err(e.into()))
    }

    /// `DEALLOCATE [PREPARE] name | ALL`: drivers such as psycopg send it as plain SQL to drop
    /// statements they prepared through the extended protocol.
    fn deallocate(&mut self, target: Option<&str>) -> Result<Exec, PgError> {
        if matches!(self.tx, Tx::Failed) {
            return Err(aborted());
        }
        let result = match target {
            None => {
                self.statements.clear();
                Ok(Exec::Tag("DEALLOCATE ALL".into()))
            }
            Some(name) if self.statements.remove(name).is_some() => {
                Ok(Exec::Tag("DEALLOCATE".into()))
            }
            Some(name) => Err(PgError::new(
                "26000",
                format!("prepared statement \"{}\" does not exist", clean(name)),
            )),
        };
        if result.is_err() && matches!(self.tx, Tx::Active(_)) {
            self.tx = Tx::Failed;
        }
        result
    }

    fn send_exec(&mut self, exec: Exec, formats: &[i16]) {
        match exec {
            Exec::Tag(tag) => self.conn.command_complete(&tag),
            Exec::Rows { cols, rows, tag } => {
                row_description(self.conn, &cols, formats);
                write_rows(self.conn, &rows, &cols, formats);
                self.conn.command_complete(&tag);
            }
        }
    }

    // ---- extended query -----------------------------------------------------------------

    fn on_parse(&mut self, body: &[u8]) -> R {
        let mut c = Cursor::new(body);
        let name = c.cstr()?.to_string();
        let query = c.cstr()?.to_string();
        let declared = c.i16()?;
        if declared < 0 {
            return Err(protocol_violation("negative parameter count").into());
        }
        let mut oids = Vec::new();
        for _ in 0..declared {
            oids.push(c.i32()? as u32);
        }
        c.finish()?;
        if !name.is_empty() && self.statements.contains_key(&name) {
            return Err(PgError::new(
                "42P05",
                format!("prepared statement \"{}\" already exists", clean(&name)),
            )
            .into());
        }
        // A new Parse replaces the unnamed statement.
        self.statements.remove("");
        if self.statements.len() >= MAX_OBJECTS {
            return Err(PgError::new("54000", "too many prepared statements").into());
        }
        let cost = OBJECT_BASE + query.len() + 4 * oids.len();
        if self.retained().saturating_add(cost) > CONNECTION_BUDGET {
            return Err(budget_exceeded().into());
        }
        let pieces = split_statements(&query);
        if pieces.len() > 1 {
            return Err(PgError::new(
                "42601",
                "cannot insert multiple commands into a prepared statement",
            )
            .into());
        }
        let used = placeholders(&query);
        let count = used.iter().copied().max().unwrap_or(0).max(oids.len());
        for n in 1..=count {
            if !used.contains(&n) && oids.get(n - 1).is_none_or(|o| *o == 0) {
                return Err(PgError::new(
                    "42P18",
                    format!("could not determine data type of parameter ${n}"),
                )
                .into());
            }
        }
        let statement = match pieces.first() {
            None => None,
            // Validate the syntax now, with a stand-in value for every $n.
            Some(piece) => Some(sql::parse(&substitute(piece, &vec![0; count])).map_err(syntax)?),
        };
        if matches!(self.tx, Tx::Failed)
            && !matches!(
                statement,
                Some(Statement::Commit | Statement::Rollback) | None
            )
        {
            return Err(aborted().into());
        }
        oids.resize(count, 0);
        for oid in &mut oids {
            if *oid == 0 {
                *oid = INT8;
            }
        }
        let sql = pieces.first().map(|p| p.to_string()).unwrap_or_default();
        drop(statement);
        self.statements.insert(
            name,
            Prepared {
                cost: OBJECT_BASE + sql.len() + 4 * oids.len(),
                sql,
                param_oids: oids,
            },
        );
        self.conn.message(b'1', |_| {});
        Ok(())
    }

    fn on_bind(&mut self, body: &[u8]) -> R {
        let mut c = Cursor::new(body);
        let portal_name = c.cstr()?.to_string();
        let statement_name = c.cstr()?.to_string();
        let nformats = count(&mut c)?;
        let mut param_formats = Vec::new();
        for _ in 0..nformats {
            param_formats.push(c.i16()?);
        }
        let nparams = count(&mut c)?;
        let mut raw: Vec<Option<&[u8]>> = Vec::new();
        for _ in 0..nparams {
            let len = c.i32()?;
            raw.push(match len {
                -1 => None,
                0.. => Some(c.bytes(len as usize)?),
                _ => return Err(protocol_violation("negative parameter length").into()),
            });
        }
        let nresults = count(&mut c)?;
        let mut result_formats = Vec::new();
        for _ in 0..nresults {
            result_formats.push(c.i16()?);
        }
        c.finish()?;
        if param_formats
            .iter()
            .chain(&result_formats)
            .any(|f| !matches!(f, 0 | 1))
        {
            return Err(PgError::new("08P01", "unsupported format code in Bind").into());
        }
        if !portal_name.is_empty() && self.portals.contains_key(&portal_name) {
            return Err(PgError::new(
                "42P03",
                format!("portal \"{}\" already exists", clean(&portal_name)),
            )
            .into());
        }
        // The unnamed portal lives until the next Bind that names it (or the end of the
        // transaction), and its result rows go with it.
        self.portals.remove("");
        if self.portals.len() >= MAX_OBJECTS {
            return Err(PgError::new("54000", "too many open portals").into());
        }
        let prepared = self.statements.get(&statement_name).ok_or_else(|| {
            PgError::new(
                "26000",
                format!(
                    "prepared statement \"{}\" does not exist",
                    clean(&statement_name)
                ),
            )
        })?;
        if self
            .retained()
            .saturating_add(OBJECT_BASE + prepared.sql.len())
            > CONNECTION_BUDGET
        {
            return Err(budget_exceeded().into());
        }
        if nparams != prepared.param_oids.len() {
            return Err(PgError::new(
                "08P01",
                format!(
                    "bind message supplies {nparams} parameters, but prepared statement requires {}",
                    prepared.param_oids.len()
                ),
            )
            .into());
        }
        if param_formats.len() > 1 && param_formats.len() != nparams {
            return Err(PgError::new("08P01", "wrong number of parameter format codes").into());
        }
        let mut values = Vec::with_capacity(nparams);
        for (i, raw) in raw.into_iter().enumerate() {
            let binary = format_of(&param_formats, i, nparams) == 1;
            values.push(param_value(raw, binary, prepared.param_oids[i], i + 1)?);
        }
        let sql = if values.is_empty() {
            prepared.sql.clone()
        } else {
            // Substituting can change the meaning (`-$1` with a negative value is a comment), so
            // the final text is checked here, as it always was; Execute parses it again.
            let sql = substitute(&prepared.sql, &values);
            parse_stored(&sql)?;
            sql
        };
        let cost = OBJECT_BASE + sql.len() + 2 * result_formats.len();
        if self.retained().saturating_add(cost) > CONNECTION_BUDGET {
            return Err(budget_exceeded().into());
        }
        self.portals.insert(
            portal_name,
            Portal {
                sql,
                formats: result_formats,
                state: PortalState::Fresh,
                cost,
            },
        );
        self.conn.message(b'2', |_| {});
        Ok(())
    }

    fn on_describe(&mut self, body: &[u8]) -> R {
        let mut c = Cursor::new(body);
        let kind = c.u8()?;
        let name = c.cstr()?;
        c.finish()?;
        let shared = self.shared;
        let backend = &shared.backend;
        match kind {
            b'S' => {
                let prepared = self.statements.get(name).ok_or_else(|| {
                    PgError::new(
                        "26000",
                        format!("prepared statement \"{}\" does not exist", clean(name)),
                    )
                })?;
                let oids = prepared.param_oids.clone();
                // Parsed with a stand-in value for every parameter, as at Parse.
                let sql = substitute(&prepared.sql, &vec![0; oids.len()]);
                let cols = match parse_stored(&sql)? {
                    Some(s) => describe(backend, &s)?,
                    None => None,
                };
                self.conn.message(b't', |b| {
                    b.extend_from_slice(&(oids.len() as i16).to_be_bytes());
                    for oid in &oids {
                        b.extend_from_slice(&oid.to_be_bytes());
                    }
                });
                match cols {
                    Some(cols) => row_description(self.conn, &cols, &[]),
                    None => self.conn.message(b'n', |_| {}),
                }
            }
            b'P' => {
                let portal = self.portals.get(name).ok_or_else(|| {
                    PgError::new(
                        "34000",
                        format!("portal \"{}\" does not exist", clean(name)),
                    )
                })?;
                let cols = match &portal.state {
                    PortalState::Rows { cols, .. } => Some(cols.clone()),
                    _ => match parse_stored(&portal.sql)? {
                        Some(s) => describe(backend, &s)?,
                        None => None,
                    },
                };
                match cols {
                    Some(cols) => {
                        check_formats(&portal.formats, cols.len())?;
                        row_description(self.conn, &cols, &portal.formats);
                    }
                    None => self.conn.message(b'n', |_| {}),
                }
            }
            _ => return Err(protocol_violation("invalid Describe target").into()),
        }
        Ok(())
    }

    fn on_execute(&mut self, body: &[u8]) -> R {
        let mut c = Cursor::new(body);
        let name = c.cstr()?.to_string();
        let max_rows = usize::try_from(c.i32()?).unwrap_or(0);
        c.finish()?;
        let mut portal = self.portals.remove(&name).ok_or_else(|| {
            PgError::new(
                "34000",
                format!("portal \"{}\" does not exist", clean(&name)),
            )
        })?;
        let in_block = !matches!(self.tx, Tx::Idle);
        let result = self.execute_portal(&mut portal, max_rows);
        if in_block && matches!(self.tx, Tx::Idle) {
            // The statement ended the transaction block (COMMIT or ROLLBACK): every portal
            // goes with it, this one too.
            self.portals.clear();
        } else {
            self.portals.insert(name, portal);
        }
        result
    }

    fn execute_portal(&mut self, portal: &mut Portal, max_rows: usize) -> R {
        if matches!(portal.state, PortalState::Fresh) {
            let Some(statement) = parse_stored(&portal.sql)? else {
                self.conn.message(b'I', |_| {});
                portal.state = PortalState::Done(String::new());
                return Ok(());
            };
            match self.run_statement(&statement, &portal.sql)? {
                Exec::Tag(tag) => {
                    self.conn.command_complete(&tag);
                    portal.state = PortalState::Done(tag);
                    return Ok(());
                }
                Exec::Rows { cols, rows, tag } => {
                    check_formats(&portal.formats, cols.len())?;
                    // Only a portal that stays suspended keeps its rows; the others are sent
                    // below and dropped.
                    if max_rows != 0 && rows.len() > max_rows {
                        let kept = rows_cost(&cols, &rows);
                        if self
                            .retained()
                            .saturating_add(portal.cost)
                            .saturating_add(kept)
                            > CONNECTION_BUDGET
                        {
                            return Err(budget_exceeded().into());
                        }
                        portal.cost += kept;
                    }
                    portal.state = PortalState::Rows {
                        cols,
                        rows,
                        pos: 0,
                        tag,
                    };
                }
            }
        }
        let mut finished = None;
        match &mut portal.state {
            PortalState::Rows {
                cols,
                rows,
                pos,
                tag,
            } => {
                let end = if max_rows == 0 {
                    rows.len()
                } else {
                    (*pos + max_rows).min(rows.len())
                };
                write_rows(self.conn, &rows[*pos..end], cols, &portal.formats);
                *pos = end;
                if end < rows.len() {
                    self.conn.message(b's', |_| {});
                } else {
                    self.conn.command_complete(tag);
                    finished = Some(tag.clone());
                }
            }
            PortalState::Done(tag) => self.conn.command_complete(tag),
            PortalState::Fresh => {}
        }
        if let Some(tag) = finished {
            portal.state = PortalState::Done(tag);
            portal.cost = OBJECT_BASE + portal.sql.len() + 2 * portal.formats.len();
        }
        Ok(())
    }

    fn on_close(&mut self, body: &[u8]) -> R {
        let mut c = Cursor::new(body);
        let kind = c.u8()?;
        let name = c.cstr()?;
        c.finish()?;
        match kind {
            b'S' => {
                self.statements.remove(name);
            }
            b'P' => {
                self.portals.remove(name);
            }
            _ => return Err(protocol_violation("invalid Close target").into()),
        }
        self.conn.message(b'3', |_| {});
        Ok(())
    }
}
