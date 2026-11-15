//! Embedded, append-only SQL engine for integer time series, with exact running totals that answer
//! range `COUNT` / `SUM` / `AVG` without reading rows. Durable through a checksummed write-ahead log
//! and checkpoints. Scope and limits: see the README ("What it does not do").
pub mod archive;
pub mod live;
mod query;
pub mod source;
pub mod sql;
mod wal;

pub use query::{MAX_RESULT_ROWS, QueryResult, Value, result_bytes};
use serde::{Deserialize, Serialize};
use sql::Statement;
use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::path::Path;
pub use wal::CheckpointInfo;

pub type Result<T> = std::result::Result<T, Error>;

#[derive(Debug)]
pub struct Error(String);
impl Error {
    pub(crate) fn new(s: impl Into<String>) -> Self {
        Self(s.into())
    }
}
impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(f)
    }
}
impl std::error::Error for Error {}
impl From<std::io::Error> for Error {
    fn from(e: std::io::Error) -> Self {
        Self(e.to_string())
    }
}

const MAX_ROWS: usize = 10_000_000;
const MAX_COLUMNS: usize = 64;
const MAX_TABLES: usize = 64;

#[derive(Debug)]
pub(crate) struct Column {
    name: String,
    data: Vec<i64>,
    prefix: Vec<i128>,
    monotonic: bool,
}

#[cfg(test)]
mod failure_tests {
    use super::*;
    #[test]
    fn io_failures_poison_the_handle_and_report_unknown_commit_outcome() {
        let root = std::env::var_os("KESTREL_TEST_ROOT")
            .map(std::path::PathBuf::from)
            .unwrap_or_else(std::env::temp_dir);
        for bytes in [0, 5, 16, 25, usize::MAX] {
            let path = root.join(format!(
                "io-failure-{}-{bytes}-{}",
                std::process::id(),
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_nanos()
            ));
            let mut db = Database::open(&path).unwrap();
            db.execute("CREATE TABLE events (v BIGINT NOT NULL)")
                .unwrap();
            db.wal.as_mut().unwrap().fail_after_bytes = Some(bytes);
            let error = db
                .execute("INSERT INTO events VALUES (1)")
                .unwrap_err()
                .to_string();
            assert!(error.contains("outcome unknown"));
            assert!(db.query("SELECT COUNT(*) FROM events").is_err());
            assert!(db.execute("INSERT INTO events VALUES (2)").is_err());
            assert!(db.rollback().is_err());
            drop(db);
            let recovered = Database::open(&path).unwrap();
            // A complete unacknowledged transaction may survive. Callers must reconcile.
            let expected = if bytes == usize::MAX { 1 } else { 0 };
            assert_eq!(
                recovered.query("SELECT COUNT(*) FROM events").unwrap().rows,
                vec![vec![Value::Int(expected)]]
            );
        }
    }
}

impl Column {
    fn new(name: String) -> Self {
        Self {
            name,
            data: Vec::new(),
            prefix: vec![0],
            monotonic: true,
        }
    }
    fn append(&mut self, values: &[i64]) {
        for &value in values {
            if self.data.last().is_some_and(|prev| *prev > value) {
                self.monotonic = false;
            }
            self.prefix
                .push(self.prefix.last().copied().unwrap() + i128::from(value));
            self.data.push(value);
        }
    }
    fn truncate(&mut self, len: usize) {
        self.data.truncate(len);
        self.prefix.truncate(len + 1);
        self.monotonic = self.data.windows(2).all(|x| x[0] <= x[1]);
    }
}

#[derive(Debug)]
pub(crate) struct Table {
    columns: Vec<Column>,
}
impl Table {
    fn len(&self) -> usize {
        self.columns[0].data.len()
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub(crate) enum Mutation {
    Create {
        table: String,
        columns: Vec<String>,
    },
    Append {
        table: String,
        columns: Vec<Vec<i64>>,
    },
}

struct Transaction {
    before: BTreeMap<String, usize>,
    changes: Vec<Mutation>,
}

#[derive(Debug, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Outcome {
    Query {
        #[serde(flatten)]
        result: QueryResult,
    },
    Affected {
        rows: usize,
    },
    Transaction {
        state: String,
    },
    Checkpoint {
        generation: u64,
        snapshot_bytes: u64,
    },
}

/// Smallest log size that triggers an automatic checkpoint. The log must also have outgrown the
/// last snapshot, so rewriting the snapshot never costs more than the log it replaces.
pub const DEFAULT_CHECKPOINT_BYTES: u64 = 64 * 1024 * 1024;

pub struct Database {
    tables: BTreeMap<String, Table>,
    wal: Option<wal::Wal>,
    transaction: Option<Transaction>,
    poisoned: bool,
    checkpoint_bytes: Option<u64>,
    /// Log size before which no automatic checkpoint is retried after one failed.
    retry_checkpoint_at: u64,
    last_checkpoint_error: Option<String>,
}

pub(crate) fn valid_identifier(name: &str) -> bool {
    let mut chars = name.bytes();
    !name.is_empty()
        && name.len() <= 63
        && chars
            .next()
            .is_some_and(|x| x.is_ascii_lowercase() || x == b'_')
        && chars.all(|x| x.is_ascii_lowercase() || x.is_ascii_digit() || x == b'_')
}

impl Database {
    pub fn memory() -> Self {
        Self {
            tables: BTreeMap::new(),
            wal: None,
            transaction: None,
            poisoned: false,
            checkpoint_bytes: Some(DEFAULT_CHECKPOINT_BYTES),
            retry_checkpoint_at: 0,
            last_checkpoint_error: None,
        }
    }
    pub fn open(path: impl AsRef<Path>) -> Result<Self> {
        let mut db = Self::memory();
        db.wal = Some(wal::Wal::open(path.as_ref(), |changes| {
            if changes.is_empty() {
                return Err(Error::new("empty WAL transaction"));
            }
            for change in changes {
                db.apply(&change)?;
            }
            Ok(())
        })?);
        Ok(db)
    }
    fn healthy(&self) -> Result<()> {
        if self.poisoned {
            Err(Error::new(
                "database is poisoned after an I/O failure; commit outcome is unknown; close and reopen",
            ))
        } else {
            Ok(())
        }
    }
    pub fn begin(&mut self) -> Result<()> {
        self.healthy()?;
        if self.transaction.is_some() {
            return Err(Error::new("nested transactions are unsupported"));
        }
        self.transaction = Some(Transaction {
            before: self
                .tables
                .iter()
                .map(|(k, v)| (k.clone(), v.len()))
                .collect(),
            changes: Vec::new(),
        });
        Ok(())
    }
    pub fn commit(&mut self) -> Result<()> {
        self.healthy()?;
        let tx = self
            .transaction
            .as_ref()
            .ok_or_else(|| Error::new("no active transaction"))?;
        if let Some(wal) = &mut self.wal
            && !tx.changes.is_empty()
        {
            let payload = match wal::Wal::encode(&tx.changes) {
                Ok(payload) => payload,
                Err(e) => {
                    // Nothing was written, so the transaction can be undone completely; leaving
                    // it open would keep its rows visible and block every later write.
                    self.rollback()?;
                    return Err(Error::new(format!("{e}; the transaction was rolled back")));
                }
            };
            if let Err(e) = wal.commit(&payload) {
                self.poisoned = true;
                return Err(Error::new(format!(
                    "commit outcome unknown; close and reopen: {e}"
                )));
            }
        }
        self.transaction = None;
        self.automatic_checkpoint();
        Ok(())
    }
    /// Minimum log size for automatic checkpoints; `None` turns them off.
    pub fn set_checkpoint_threshold(&mut self, bytes: Option<u64>) {
        self.checkpoint_bytes = bytes;
        self.retry_checkpoint_at = 0;
    }
    /// Bytes of an unfinished last write that were cut off when the database was opened, which
    /// happens after a crash or power cut during a commit that was never acknowledged.
    pub fn recovered_tail_bytes(&self) -> u64 {
        self.wal.as_ref().map_or(0, |w| w.recovered_tail_bytes)
    }
    /// Why the last automatic or manual checkpoint failed, until one succeeds. A failed
    /// automatic checkpoint never fails the commit that triggered it; this is where it shows.
    pub fn last_checkpoint_error(&self) -> Option<&str> {
        self.last_checkpoint_error.as_deref()
    }
    /// Current log size in bytes, header included (0 for an in-memory database).
    pub fn log_bytes(&self) -> u64 {
        self.wal.as_ref().map_or(0, |w| w.log_bytes)
    }
    fn automatic_checkpoint(&mut self) {
        let (Some(min), Some(wal)) = (self.checkpoint_bytes, &self.wal) else {
            return;
        };
        let due = wal.log_bytes >= min.max(wal.snapshot_bytes).max(self.retry_checkpoint_at);
        if due && self.checkpoint().is_err() && !self.poisoned {
            // The commit itself is durable. Retry once the log has grown by another threshold.
            self.retry_checkpoint_at = self.log_bytes().saturating_add(min);
        }
    }
    /// Writes all tables to a binary snapshot and starts an empty log, so the next open reads
    /// the snapshot instead of replaying every transaction since the last one.
    pub fn checkpoint(&mut self) -> Result<CheckpointInfo> {
        self.healthy()?;
        if self.transaction.is_some() {
            return Err(Error::new("CHECKPOINT cannot run inside a transaction"));
        }
        let wal = self
            .wal
            .as_mut()
            .ok_or_else(|| Error::new("an in-memory database has no log to checkpoint"))?;
        let result = wal.checkpoint(&self.tables).map_err(|e| {
            if e.poison {
                self.poisoned = true;
                Error::new(format!(
                    "checkpoint failed after its snapshot was published; close and reopen: {}",
                    e.error
                ))
            } else {
                Error::new(format!(
                    "checkpoint failed; the database is unchanged: {}",
                    e.error
                ))
            }
        });
        match &result {
            Ok(_) => {
                self.retry_checkpoint_at = 0;
                self.last_checkpoint_error = None;
            }
            Err(e) => self.last_checkpoint_error = Some(e.to_string()),
        }
        result
    }
    pub fn rollback(&mut self) -> Result<()> {
        self.healthy()?;
        let tx = self
            .transaction
            .take()
            .ok_or_else(|| Error::new("no active transaction"))?;
        self.tables.retain(|name, _| tx.before.contains_key(name));
        for (name, len) in tx.before {
            for c in &mut self.tables.get_mut(&name).unwrap().columns {
                c.truncate(len);
            }
        }
        Ok(())
    }
    fn apply(&mut self, change: &Mutation) -> Result<()> {
        match change {
            Mutation::Create { table, columns } => {
                if !valid_identifier(table) || columns.iter().any(|c| !valid_identifier(c)) {
                    return Err(Error::new("invalid identifier; use lowercase ASCII names"));
                }
                if self.tables.contains_key(table) {
                    return Err(Error::new("table already exists"));
                }
                if self.tables.len() >= MAX_TABLES {
                    return Err(Error::new("table budget exceeded"));
                }
                if columns.is_empty() || columns.len() > MAX_COLUMNS {
                    return Err(Error::new("tables require 1 to 64 columns"));
                }
                if columns.iter().collect::<BTreeSet<_>>().len() != columns.len() {
                    return Err(Error::new("duplicate column name"));
                }
                self.tables.insert(
                    table.clone(),
                    Table {
                        columns: columns.iter().cloned().map(Column::new).collect(),
                    },
                );
            }
            Mutation::Append { table, columns } => {
                let t = self
                    .tables
                    .get_mut(table)
                    .ok_or_else(|| Error::new("unknown table"))?;
                if columns.len() != t.columns.len() {
                    return Err(Error::new("column count mismatch"));
                }
                let count = columns[0].len();
                if columns.iter().any(|c| c.len() != count) {
                    return Err(Error::new("column lengths differ"));
                }
                if count > MAX_ROWS - t.len() {
                    return Err(Error::new("table exceeds 10 million row budget"));
                }
                // Reserve every column before changing any logical state.
                for c in &mut t.columns {
                    c.data
                        .try_reserve(count)
                        .map_err(|_| Error::new("allocation failed"))?;
                    c.prefix
                        .try_reserve(count)
                        .map_err(|_| Error::new("allocation failed"))?;
                }
                for (c, values) in t.columns.iter_mut().zip(columns) {
                    c.append(values);
                }
            }
        }
        Ok(())
    }
    fn mutate(&mut self, change: Mutation) -> Result<usize> {
        self.healthy()?;
        let automatic = self.transaction.is_none();
        if automatic {
            self.begin()?;
        }
        let rows = match &change {
            Mutation::Append { columns, .. } => columns.first().map_or(0, Vec::len),
            _ => 0,
        };
        if let Err(e) = self.apply(&change) {
            if automatic {
                self.rollback()?;
            }
            return Err(e);
        }
        self.transaction.as_mut().unwrap().changes.push(change);
        if automatic && let Err(e) = self.commit() {
            if !self.poisoned && self.transaction.is_some() {
                self.rollback()?;
            }
            return Err(e);
        }
        Ok(rows)
    }
    /// Append a column-oriented batch. In durable mode, autocommit synchronizes the WAL.
    pub fn append(&mut self, table: &str, columns: Vec<Vec<i64>>) -> Result<usize> {
        self.mutate(Mutation::Append {
            table: table.to_ascii_lowercase(),
            columns,
        })
    }
    /// Rows and columns of a table, for sizing a query before it runs.
    pub fn table_shape(&self, table: &str) -> Option<(usize, usize)> {
        self.tables.get(table).map(|t| (t.len(), t.columns.len()))
    }
    pub fn query(&self, sql: &str) -> Result<QueryResult> {
        self.healthy()?;
        match sql::parse(sql)? {
            Statement::Select(q) => {
                let t = self
                    .tables
                    .get(&q.table)
                    .ok_or_else(|| Error::new("unknown table"))?;
                query::execute(t, query::plan(t, &q)?)
            }
            _ => Err(Error::new("query() requires SELECT")),
        }
    }
    pub fn execute(&mut self, sql: &str) -> Result<Outcome> {
        self.healthy()?;
        match sql::parse(sql)? {
            Statement::Create { table, columns } => Ok(Outcome::Affected {
                rows: self.mutate(Mutation::Create { table, columns })?,
            }),
            Statement::Insert { table, rows } => {
                let width = self
                    .tables
                    .get(&table)
                    .ok_or_else(|| Error::new("unknown table"))?
                    .columns
                    .len();
                if rows.iter().any(|r| r.len() != width) {
                    return Err(Error::new("row width differs from schema"));
                }
                let mut columns = vec![Vec::with_capacity(rows.len()); width];
                for row in rows {
                    for (c, v) in columns.iter_mut().zip(row) {
                        c.push(v);
                    }
                }
                Ok(Outcome::Affected {
                    rows: self.append(&table, columns)?,
                })
            }
            Statement::Select(q) => {
                let t = self
                    .tables
                    .get(&q.table)
                    .ok_or_else(|| Error::new("unknown table"))?;
                Ok(Outcome::Query {
                    result: query::execute(t, query::plan(t, &q)?)?,
                })
            }
            Statement::Explain(q) => {
                let t = self
                    .tables
                    .get(&q.table)
                    .ok_or_else(|| Error::new("unknown table"))?;
                let p = query::plan(t, &q)?;
                Ok(Outcome::Query {
                    result: QueryResult {
                        columns: vec!["plan".into()],
                        rows: vec![vec![Value::Text(p.describe().into())]],
                        plan: "explain".into(),
                        rows_scanned: 0,
                    },
                })
            }
            Statement::Begin => {
                self.begin()?;
                Ok(Outcome::Transaction {
                    state: "begun".into(),
                })
            }
            Statement::Commit => {
                self.commit()?;
                Ok(Outcome::Transaction {
                    state: "committed".into(),
                })
            }
            Statement::Rollback => {
                self.rollback()?;
                Ok(Outcome::Transaction {
                    state: "rolled_back".into(),
                })
            }
            Statement::Checkpoint => {
                let info = self.checkpoint()?;
                Ok(Outcome::Checkpoint {
                    generation: info.generation,
                    snapshot_bytes: info.snapshot_bytes,
                })
            }
        }
    }
    /// Logical used bytes for column values and prefix entries; excludes allocator slack, WAL,
    /// transaction buffers, catalog, query results, and the process runtime.
    pub fn logical_index_bytes(&self) -> usize {
        self.tables
            .values()
            .flat_map(|t| &t.columns)
            .map(|c| c.data.len() * 8 + c.prefix.len() * 16)
            .sum()
    }
}
