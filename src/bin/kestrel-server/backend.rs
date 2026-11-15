//! The two storage backends behind the wire protocol, and the mapping of engine errors
//! to SQLSTATE codes.
use crate::wire::PgError;
use kestrel_sql::archive::IngestBatch;
use kestrel_sql::live::LiveArchive;
use kestrel_sql::sql::Statement;
use kestrel_sql::{Database, Outcome, QueryResult};
use std::collections::{BTreeSet, HashMap};
use std::sync::{Mutex, MutexGuard};

/// Largest INSERT / transaction in `--archive` mode: one live append is one segment of at
/// most this many rows.
pub const ARCHIVE_BATCH_ROWS: usize = 10_000;
/// Rows one connection may queue inside a `BEGIN` block (memory bound).
pub const MAX_QUEUED_ROWS: usize = 1_000_000;
/// Statements one connection may queue inside a `BEGIN` block (memory and commit-time bound).
pub const MAX_QUEUED_OPS: usize = 100_000;

pub enum Backend {
    Db(Mutex<Database>),
    Archive(ArchiveBackend),
}

pub struct ArchiveBackend {
    pub live: LiveArchive,
    pub table: String,
    pub columns: Vec<String>,
}

/// A write validated at statement time and applied at commit time.
pub enum Op {
    Create {
        table: String,
        columns: Vec<String>,
        sql: String,
    },
    Insert {
        table: String,
        rows: Vec<Vec<i64>>,
        sql: String,
    },
}

impl Op {
    pub fn from_statement(statement: &Statement, sql: &str) -> Option<Op> {
        match statement {
            Statement::Create { table, columns } => Some(Op::Create {
                table: table.clone(),
                columns: columns.clone(),
                sql: sql.to_string(),
            }),
            Statement::Insert { table, rows } => Some(Op::Insert {
                table: table.clone(),
                rows: rows.clone(),
                sql: sql.to_string(),
            }),
            _ => None,
        }
    }
    fn rows(&self) -> usize {
        match self {
            Op::Insert { rows, .. } => rows.len(),
            Op::Create { .. } => 0,
        }
    }
    /// Bytes this queued write keeps alive: the SQL text plus the parsed rows (a `Vec<i64>` per
    /// row costs its header, a typical allocator overhead and 8 bytes per value).
    pub fn cost(&self) -> usize {
        const BASE: usize = 128;
        match self {
            Op::Create {
                table,
                columns,
                sql,
            } => {
                BASE + table.len() + sql.len() + columns.iter().map(|c| c.len() + 24).sum::<usize>()
            }
            Op::Insert { table, rows, sql } => {
                BASE + table.len()
                    + sql.len()
                    + rows.iter().map(|r| 40 + 8 * r.len()).sum::<usize>()
            }
        }
    }
}

/// The writes a connection queued since `BEGIN`, with running totals so that checking one more
/// statement costs the same however long the queue already is.
#[derive(Default)]
pub struct Pending {
    ops: Vec<Op>,
    rows: usize,
    bytes: usize,
    /// Tables created inside this transaction and their column counts.
    creates: HashMap<String, usize>,
}

impl Pending {
    pub fn push(&mut self, op: Op) {
        self.rows += op.rows();
        self.bytes += op.cost();
        if let Op::Create { table, columns, .. } = &op {
            self.creates.insert(table.clone(), columns.len());
        }
        self.ops.push(op);
    }
    pub fn ops(&self) -> &[Op] {
        &self.ops
    }
    pub fn is_empty(&self) -> bool {
        self.ops.is_empty()
    }
    /// Bytes the queue keeps alive (see [`Op::cost`]).
    pub fn bytes(&self) -> usize {
        self.bytes
    }
}

/// Maps an engine error message to a SQLSTATE. The engine only has message strings.
pub fn engine_error(e: kestrel_sql::Error) -> PgError {
    let m = e.to_string();
    let code = if m.contains("poisoned")
        || m.contains("outcome unknown")
        || m.contains("unhealthy")
        || m.contains("writer stopped")
    {
        "XX000"
    } else if m == "unknown table" {
        "42P01"
    } else if m.starts_with("unknown column") {
        "42703"
    } else if m.contains("already exists") {
        "42P07"
    } else if m.contains("exceeds") || m.contains("budget") || m.contains("queue full") {
        "54000"
    } else if m.starts_with("projected column must occur in GROUP BY") {
        "42803"
    } else if m.starts_with("SELECT * must")
        || m.starts_with("ORDER BY requires")
        || m.contains("requires SELECT")
        || m.contains("row width differs")
        || m.contains("column count mismatch")
    {
        "42601"
    } else {
        "XX000"
    };
    PgError::new(code, m)
}

fn no_relation(table: &str) -> PgError {
    PgError::new("42P01", format!("relation \"{table}\" does not exist"))
}

fn lock(db: &Mutex<Database>) -> Result<MutexGuard<'_, Database>, PgError> {
    db.lock().map_err(|_| {
        PgError::new(
            "XX000",
            "internal error: an earlier request panicked inside the database; restart the server",
        )
    })
}

impl Backend {
    pub fn name(&self) -> &'static str {
        match self {
            Backend::Db(_) => "db",
            Backend::Archive(_) => "archive",
        }
    }

    /// Column names of a table as the engine sees them (also proves the table exists).
    pub fn schema(&self, table: &str) -> Result<Vec<String>, PgError> {
        match self {
            Backend::Db(db) => lock(db)?
                .query(&format!("SELECT * FROM {table} LIMIT 0"))
                .map(|r| r.columns)
                .map_err(|e| {
                    let e = engine_error(e);
                    if e.code == "42P01" {
                        no_relation(table)
                    } else {
                        e
                    }
                }),
            Backend::Archive(a) => {
                if table == a.table {
                    Ok(a.live.snapshot().columns().to_vec())
                } else {
                    Err(no_relation(table))
                }
            }
        }
    }

    /// Runs a SELECT or EXPLAIN against committed data.
    pub fn select(&self, statement: &Statement, sql: &str) -> Result<QueryResult, PgError> {
        match self {
            Backend::Db(db) => match lock(db)?.execute(sql).map_err(engine_error)? {
                Outcome::Query { result } => Ok(result),
                _ => Err(PgError::new("XX000", "engine returned no result set")),
            },
            Backend::Archive(a) => {
                if matches!(statement, Statement::Explain(_)) {
                    return Err(PgError::new(
                        "42601",
                        "EXPLAIN is not supported in --archive mode",
                    ));
                }
                a.live
                    .snapshot()
                    .query(sql)
                    .map(|r| r.result)
                    .map_err(engine_error)
            }
        }
    }

    /// Statement-time checks for a write, so errors surface where the client issued it.
    /// `pending` holds the earlier writes of the same transaction.
    pub fn check(&self, op: &Op, pending: &Pending) -> Result<(), PgError> {
        if pending.ops.len() >= MAX_QUEUED_OPS {
            return Err(PgError::new(
                "54000",
                format!("a transaction may queue at most {MAX_QUEUED_OPS} statements"),
            ));
        }
        let queued_create = |table: &str| pending.creates.get(table).copied();
        match (self, op) {
            (Backend::Archive(_), Op::Create { .. }) => Err(PgError::new(
                "42601",
                "CREATE TABLE is not supported in --archive mode: the table is fixed at server start (--table, --columns)",
            )),
            (Backend::Archive(a), Op::Insert { table, rows, .. }) => {
                if *table != a.table {
                    return Err(no_relation(table));
                }
                if rows.iter().any(|r| r.len() != a.columns.len()) {
                    return Err(PgError::new(
                        "42601",
                        format!("INSERT needs {} values per row", a.columns.len()),
                    ));
                }
                if rows.len() + pending.rows > ARCHIVE_BATCH_ROWS {
                    return Err(PgError::new(
                        "54000",
                        format!(
                            "--archive mode accepts at most {ARCHIVE_BATCH_ROWS} rows per INSERT or transaction"
                        ),
                    ));
                }
                Ok(())
            }
            (Backend::Db(_), Op::Create { table, columns, .. }) => {
                if queued_create(table).is_some() || self.schema(table).is_ok() {
                    return Err(PgError::new(
                        "42P07",
                        format!("relation \"{table}\" already exists"),
                    ));
                }
                if columns.iter().collect::<BTreeSet<_>>().len() != columns.len() {
                    return Err(PgError::new(
                        "42701",
                        "column name specified more than once",
                    ));
                }
                if columns.len() > 64 {
                    return Err(PgError::new("54011", "tables allow at most 64 columns"));
                }
                Ok(())
            }
            (Backend::Db(_), Op::Insert { table, rows, .. }) => {
                let width = match queued_create(table) {
                    Some(width) => width,
                    None => self.schema(table)?.len(),
                };
                if rows.iter().any(|r| r.len() != width) {
                    return Err(PgError::new(
                        "42601",
                        format!("INSERT needs {width} values per row"),
                    ));
                }
                if pending.rows + rows.len() > MAX_QUEUED_ROWS {
                    return Err(PgError::new(
                        "54000",
                        format!("a transaction may queue at most {MAX_QUEUED_ROWS} rows"),
                    ));
                }
                Ok(())
            }
        }
    }

    /// Writes a snapshot and starts an empty log (`CHECKPOINT`). Only `--db` has a log.
    pub fn checkpoint(&self) -> Result<(), PgError> {
        match self {
            Backend::Db(db) => lock(db)?.checkpoint().map(|_| ()).map_err(engine_error),
            Backend::Archive(_) => Err(PgError::new(
                "0A000",
                "CHECKPOINT applies to --db mode; the archive has no log to checkpoint",
            )),
        }
    }

    /// Applies writes atomically: one WAL transaction (db) or one segment (archive).
    /// Returns the number of rows inserted.
    pub fn apply(&self, ops: &[Op]) -> Result<usize, PgError> {
        match self {
            Backend::Db(db) => {
                let mut db = lock(db)?;
                db.begin().map_err(engine_error)?;
                let mut rows = 0;
                for op in ops {
                    let sql = match op {
                        Op::Create { sql, .. } | Op::Insert { sql, .. } => sql,
                    };
                    match db.execute(sql) {
                        Ok(Outcome::Affected { rows: n }) => rows += n,
                        Ok(_) => {}
                        Err(e) => {
                            // A failed rollback means the handle is poisoned; the commit error
                            // we are about to return is the more useful message.
                            let _ = db.rollback();
                            return Err(engine_error(e));
                        }
                    }
                }
                if let Err(e) = db.commit() {
                    // The engine rolls back a commit it refuses (too large) and poisons itself
                    // when the outcome is unknown. Either way the shared handle must not stay
                    // inside a transaction, so undo here too; it fails harmlessly when there
                    // is nothing to undo.
                    let _ = db.rollback();
                    return Err(engine_error(e));
                }
                Ok(rows)
            }
            Backend::Archive(a) => {
                let mut columns = vec![Vec::new(); a.columns.len()];
                for op in ops {
                    if let Op::Insert { rows, .. } = op {
                        for row in rows {
                            for (column, value) in columns.iter_mut().zip(row) {
                                column.push(*value);
                            }
                        }
                    }
                }
                if columns[0].is_empty() {
                    return Ok(0);
                }
                a.live
                    .append(IngestBatch { id: None, columns })
                    .map(|receipt| receipt.rows)
                    .map_err(engine_error)
            }
        }
    }
}
