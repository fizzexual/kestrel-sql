//! Experimental embedded, append-only SQL engine with automatic exact aggregate indexes.
//! This release is a research prototype, not a production-certified database.
pub mod archive;
pub mod live;
mod query;
pub mod source;
pub mod sql;
mod wal;

pub use query::{QueryResult, Value};
use serde::{Deserialize, Serialize};
use sql::Statement;
use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::path::Path;
use std::sync::Arc;

pub type Result<T> = std::result::Result<T, Error>;

/// Stable machine-readable categories for the explicitly classified operations.
/// Unclassified errors have no commit/admission guarantee; do not infer retry safety.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
#[serde(rename_all = "snake_case")]
pub enum ErrorKind {
    Unclassified,
    InvalidInput,
    BudgetExceeded,
    QueueFull,
    WriterUnavailable,
    RetryConflict,
    CommitOutcomeUnknown,
    #[serde(rename = "io_error")]
    Io,
}
impl ErrorKind {
    pub const fn code(self) -> &'static str {
        match self {
            Self::Unclassified => "unclassified",
            Self::InvalidInput => "invalid_input",
            Self::BudgetExceeded => "budget_exceeded",
            Self::QueueFull => "queue_full",
            Self::WriterUnavailable => "writer_unavailable",
            Self::RetryConflict => "retry_conflict",
            Self::CommitOutcomeUnknown => "commit_outcome_unknown",
            Self::Io => "io_error",
        }
    }
}

#[derive(Debug, Clone, Serialize)]
struct ErrorDetails {
    message: String,
    #[serde(rename = "code")]
    kind: ErrorKind,
    #[serde(skip_serializing_if = "Option::is_none")]
    raw_os_error: Option<i32>,
}

/// Human messages retain their preceding text; code and errno are separate metadata.
#[derive(Debug, Clone)]
pub struct Error(Arc<ErrorDetails>);
impl Error {
    pub(crate) fn new(s: impl Into<String>) -> Self {
        Self::classified(ErrorKind::Unclassified, s)
    }
    pub(crate) fn classified(kind: ErrorKind, s: impl Into<String>) -> Self {
        Self(Arc::new(ErrorDetails {
            message: s.into(),
            kind,
            raw_os_error: None,
        }))
    }
    pub(crate) fn context(mut self, kind: ErrorKind, s: impl Into<String>) -> Self {
        let details = Arc::make_mut(&mut self.0);
        details.message = s.into();
        details.kind = kind;
        self
    }
    pub fn kind(&self) -> ErrorKind {
        self.0.kind
    }
    pub fn code(&self) -> &'static str {
        self.kind().code()
    }
    /// Original OS error number when available; it is not a commit-outcome verdict.
    pub fn raw_os_error(&self) -> Option<i32> {
        self.0.raw_os_error
    }
}
impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.message.fmt(f)
    }
}
impl Serialize for Error {
    fn serialize<S: serde::Serializer>(
        &self,
        serializer: S,
    ) -> std::result::Result<S::Ok, S::Error> {
        self.0.as_ref().serialize(serializer)
    }
}
impl std::error::Error for Error {}
impl From<std::io::Error> for Error {
    fn from(e: std::io::Error) -> Self {
        Self(Arc::new(ErrorDetails {
            message: e.to_string(),
            kind: ErrorKind::Io,
            raw_os_error: e.raw_os_error(),
        }))
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
    fn os_error_context_and_fanout_preserve_metadata_without_mutating_clones() {
        let io = std::io::Error::from_raw_os_error(112);
        let message = io.to_string();
        let original = Error::from(io);
        let contextual = original
            .clone()
            .context(ErrorKind::CommitOutcomeUnknown, "outcome unknown");
        assert_eq!(original.kind(), ErrorKind::Io);
        assert_eq!(original.to_string(), message);
        assert_eq!(contextual.raw_os_error(), Some(112));
        let cloned = contextual.clone();
        let json = serde_json::to_value(cloned).unwrap();
        assert_eq!(
            json,
            serde_json::json!({"code":"commit_outcome_unknown", "message":"outcome unknown", "raw_os_error":112})
        );
        for kind in [
            ErrorKind::Unclassified,
            ErrorKind::InvalidInput,
            ErrorKind::BudgetExceeded,
            ErrorKind::QueueFull,
            ErrorKind::WriterUnavailable,
            ErrorKind::RetryConflict,
            ErrorKind::CommitOutcomeUnknown,
            ErrorKind::Io,
        ] {
            assert_eq!(serde_json::to_value(kind).unwrap(), kind.code());
        }
    }
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
            let error = db.execute("INSERT INTO events VALUES (1)").unwrap_err();
            assert_eq!(error.kind(), ErrorKind::CommitOutcomeUnknown);
            assert_eq!(error.code(), "commit_outcome_unknown");
            assert!(error.to_string().contains("outcome unknown"));
            assert_eq!(
                db.query("SELECT COUNT(*) FROM events").unwrap_err().kind(),
                ErrorKind::WriterUnavailable
            );
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
}

pub struct Database {
    tables: BTreeMap<String, Table>,
    wal: Option<wal::Wal>,
    transaction: Option<Transaction>,
    poisoned: bool,
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
            Err(Error::classified(
                ErrorKind::WriterUnavailable,
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
            let payload = wal::Wal::encode(&tx.changes)?;
            if let Err(e) = wal.commit(&payload) {
                self.poisoned = true;
                let message = format!("commit outcome unknown; close and reopen: {e}");
                return Err(e.context(ErrorKind::CommitOutcomeUnknown, message));
            }
        }
        self.transaction = None;
        Ok(())
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
            if !self.poisoned {
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
