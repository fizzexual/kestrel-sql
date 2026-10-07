use kestrel_sql::{Database, Value};
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};

fn temp(label: &str) -> PathBuf {
    static SEQ: AtomicU64 = AtomicU64::new(0);
    let root = std::env::var_os("KESTREL_TEST_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    let path = root.join(format!(
        "ksql-{}-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
        SEQ.fetch_add(1, Ordering::Relaxed)
    ));
    std::fs::create_dir_all(&path).unwrap();
    path
}
fn schema(db: &mut Database) {
    db.execute(
        "CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)",
    )
    .unwrap();
}
fn fixture() -> Database {
    let mut db = Database::memory();
    schema(&mut db);
    db.execute("INSERT INTO events VALUES (-1, 10, 1), (0, -2, 2), (0, 7, 1), (3, 20, 2)")
        .unwrap();
    db
}
fn ints(values: &[i128]) -> Vec<Value> {
    values.iter().copied().map(Value::Int).collect()
}

#[test]
fn prefix_handles_duplicates_and_closed_open_ranges() {
    let db = fixture();
    let r = db
        .query("SELECT COUNT(*), SUM(value), AVG(value) FROM events WHERE ts >= 0 AND ts < 3")
        .unwrap();
    assert_eq!(
        r.rows,
        vec![vec![Value::Int(2), Value::Int(5), Value::Float(2.5)]]
    );
    assert_eq!(r.rows_scanned, 0);
    assert_eq!(r.plan, "prefix-range-aggregate");
    assert_eq!(
        db.query("SELECT SUM(value) FROM events WHERE ts = 0")
            .unwrap()
            .rows,
        vec![ints(&[5])]
    );
    assert_eq!(
        db.query("SELECT SUM(value) FROM events WHERE ts <= 0 AND ts > -1")
            .unwrap()
            .rows,
        vec![ints(&[5])]
    );
}

#[test]
fn empty_and_contradictory_ranges_use_sql_null_semantics() {
    let db = fixture();
    for filter in ["ts > 100", "ts >= 3 AND ts < -1", "ts > 0 AND ts <= 0"] {
        let r = db.query(&format!("SELECT COUNT(*), SUM(value), AVG(value), MIN(value), MAX(value) FROM events WHERE {filter}")).unwrap();
        assert_eq!(
            r.rows,
            vec![vec![
                Value::Int(0),
                Value::Null,
                Value::Null,
                Value::Null,
                Value::Null
            ]]
        );
    }
    let mut empty = Database::memory();
    schema(&mut empty);
    assert_eq!(
        empty
            .query("SELECT COUNT(*), SUM(value) FROM events")
            .unwrap()
            .rows,
        vec![vec![Value::Int(0), Value::Null]]
    );
}

#[test]
fn signed_extremes_do_not_overflow() {
    let mut db = Database::memory();
    schema(&mut db);
    db.append(
        "events",
        vec![
            vec![i64::MIN, i64::MAX, i64::MAX],
            vec![i64::MAX, i64::MAX, i64::MAX],
            vec![1, 1, 1],
        ],
    )
    .unwrap();
    assert_eq!(
        db.query("SELECT COUNT(*), SUM(value) FROM events WHERE ts >= 9223372036854775807")
            .unwrap()
            .rows,
        vec![ints(&[2, i128::from(i64::MAX) * 2])]
    );
    assert_eq!(
        db.query("SELECT SUM(value) FROM events").unwrap().rows,
        vec![ints(&[i128::from(i64::MAX) * 3])]
    );
}

#[test]
fn late_events_fall_back_without_stale_index_results() {
    let mut db = fixture();
    db.execute("INSERT INTO events VALUES (1, 100, 1)").unwrap();
    let r = db
        .query("SELECT SUM(value) FROM events WHERE ts >= 0 AND ts < 3")
        .unwrap();
    assert_eq!(r.rows, vec![ints(&[105])]);
    assert_eq!(r.rows_scanned, 5);
    assert_eq!(r.plan, "filtered-column-scan");
}

#[test]
fn groups_projections_sort_and_limit() {
    let db = fixture();
    assert_eq!(db.query("SELECT device, SUM(value) AS total FROM events GROUP BY device ORDER BY total DESC LIMIT 1").unwrap().rows, vec![ints(&[2,18])]);
    assert_eq!(
        db.query("SELECT ts, value FROM events WHERE value <> 7 ORDER BY value DESC LIMIT 2")
            .unwrap()
            .rows,
        vec![ints(&[3, 20]), ints(&[-1, 10])]
    );
    assert_eq!(
        db.query("SELECT * FROM events LIMIT 1").unwrap().rows,
        vec![ints(&[-1, 10, 1])]
    );
    assert_eq!(
        db.query("SELECT MIN(value), MAX(value) FROM events WHERE ts >= 0")
            .unwrap()
            .rows,
        vec![ints(&[-2, 20])]
    );
    assert!(
        db.query("SELECT * FROM events LIMIT 0")
            .unwrap()
            .rows
            .is_empty()
    );
    assert!(
        db.query("SELECT device FROM events GROUP BY device ORDER BY device")
            .is_ok()
    );
}

#[test]
fn rejects_unsupported_or_ambiguous_sql_even_for_empty_data() {
    let mut db = Database::memory();
    schema(&mut db);
    for sql in [
        "SELECT unknown FROM events",
        "SELECT COUNT(*) FROM events WHERE unknown = 1",
        "SELECT value, SUM(value) FROM events",
        "SELECT * AS x FROM events",
        "SELECT *, ts FROM events",
        "SELECT SUM(value) AS x, COUNT(*) AS x FROM events ORDER BY x",
        "SELECT * FROM events LIMIT -1",
        "SELECT * FROM events JOIN other",
        "SELECT * FROM events WHERE ts = 1 OR ts = 2",
        "SELECT COUNT(*) FROM events; INSERT INTO events VALUES (1,2,3)",
        "SELECT COUNT(*) FROM events ORDER BY missing LIMIT 0",
        "SELECT SUM(value) FROM events WHERE ts = 9223372036854775808",
    ] {
        assert!(db.execute(sql).is_err(), "accepted: {sql}");
    }
    assert!(db.execute("CREATE TABLE bad (x BIGINT)").is_err());
    assert!(
        db.execute("CREATE TABLE bad (x BIGINT NOT NULL, x BIGINT NOT NULL)")
            .is_err()
    );
}

#[test]
fn malformed_batches_are_atomic() {
    let mut db = fixture();
    assert!(
        db.execute("INSERT INTO events VALUES (5,1,1), (6,2)")
            .is_err()
    );
    assert!(
        db.append("events", vec![vec![4], vec![2, 3], vec![1]])
            .is_err()
    );
    assert!(db.append("events", vec![]).is_err());
    assert_eq!(
        db.query("SELECT COUNT(*), SUM(value) FROM events")
            .unwrap()
            .rows,
        vec![ints(&[4, 35])]
    );
    db.execute("INSERT INTO events VALUES (4,1,1)").unwrap();
    assert_eq!(
        db.query("SELECT COUNT(*) FROM events").unwrap().rows,
        vec![ints(&[5])]
    );
}

#[test]
fn rollback_restores_catalog_data_and_order_detection() {
    let mut db = fixture();
    db.begin().unwrap();
    assert!(db.begin().is_err());
    db.execute("CREATE TABLE scratch (v BIGINT NOT NULL)")
        .unwrap();
    db.execute("INSERT INTO events VALUES (-100, 100, 1)")
        .unwrap();
    assert_eq!(
        db.query("SELECT COUNT(*) FROM events").unwrap().rows,
        vec![ints(&[5])]
    );
    assert!(db.execute("INSERT INTO events VALUES (1,2)").is_err());
    db.rollback().unwrap();
    assert!(db.query("SELECT * FROM scratch").is_err());
    let r = db
        .query("SELECT COUNT(*) FROM events WHERE ts >= 0")
        .unwrap();
    assert_eq!(r.rows, vec![ints(&[3])]);
    assert_eq!(r.rows_scanned, 0);
    assert!(db.commit().is_err());
    assert!(db.rollback().is_err());
}

#[test]
fn committed_transactions_recover_and_uncommitted_drop_does_not() {
    let path = temp("reopen");
    {
        let mut db = Database::open(&path).unwrap();
        schema(&mut db);
        db.begin().unwrap();
        db.execute("INSERT INTO events VALUES (1,10,1), (2,20,1)")
            .unwrap();
        db.commit().unwrap();
        db.begin().unwrap();
        db.execute("INSERT INTO events VALUES (3,999,1)").unwrap();
    }
    let db = Database::open(&path).unwrap();
    let r = db
        .query("SELECT COUNT(*), SUM(value) FROM events WHERE ts >= 1")
        .unwrap();
    assert_eq!(r.rows, vec![ints(&[2, 30])]);
    assert_eq!(r.rows_scanned, 0);
}

#[test]
fn exclusive_lock_is_released_on_drop() {
    let path = temp("lock");
    let db = Database::open(&path).unwrap();
    assert!(Database::open(&path).is_err());
    drop(db);
    assert!(Database::open(&path).is_ok());
}

#[test]
fn every_partial_final_frame_is_discarded_and_all_prior_commits_survive() {
    let source = temp("source");
    let before;
    {
        let mut db = Database::open(&source).unwrap();
        schema(&mut db);
        db.execute("INSERT INTO events VALUES (1,10,1)").unwrap();
        before = std::fs::metadata(source.join("events.ksql")).unwrap().len() as usize;
        db.begin().unwrap();
        db.execute("INSERT INTO events VALUES (2,20,1)").unwrap();
        db.execute("INSERT INTO events VALUES (3,30,1)").unwrap();
        db.commit().unwrap();
    }
    let bytes = std::fs::read(source.join("events.ksql")).unwrap();
    for cut in before..bytes.len() {
        let path = temp("cut");
        std::fs::write(path.join("events.ksql"), &bytes[..cut]).unwrap();
        let mut db = Database::open(&path).unwrap();
        assert_eq!(
            db.query("SELECT COUNT(*), SUM(value) FROM events")
                .unwrap()
                .rows,
            vec![ints(&[1, 10])],
            "cut: {cut}"
        );
        db.execute("INSERT INTO events VALUES (4,40,1)").unwrap();
        drop(db);
        assert_eq!(
            Database::open(&path)
                .unwrap()
                .query("SELECT SUM(value) FROM events")
                .unwrap()
                .rows,
            vec![ints(&[50])]
        );
    }
}

#[test]
fn complete_corruption_is_rejected_without_modifying_the_wal() {
    let source = temp("corruption-source");
    {
        let mut db = Database::open(&source).unwrap();
        schema(&mut db);
        db.execute("INSERT INTO events VALUES (1,2,3)").unwrap();
    }
    let bytes = std::fs::read(source.join("events.ksql")).unwrap();
    // Flip every byte, including the signature, frame headers and JSON payload.
    for offset in 0..bytes.len() {
        let path = temp("corrupt");
        let mut damaged = bytes.clone();
        damaged[offset] ^= 1;
        std::fs::write(path.join("events.ksql"), &damaged).unwrap();
        assert!(
            Database::open(&path).is_err(),
            "accepted corruption at {offset}"
        );
        assert_eq!(std::fs::read(path.join("events.ksql")).unwrap(), damaged);
    }
}

#[test]
fn process_kill_preserves_acknowledged_commit_and_releases_lock() {
    let path = temp("kill");
    let mut child = Command::new(env!("CARGO_BIN_EXE_kestrel"))
        .arg("--db")
        .arg(&path)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    let mut input = child.stdin.take().unwrap();
    let mut output = BufReader::new(child.stdout.take().unwrap());
    for sql in [
        "CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)",
        "INSERT INTO events VALUES (1,10,1)",
        "BEGIN",
        "INSERT INTO events VALUES (2,999,1)",
    ] {
        writeln!(input, "{sql}").unwrap();
        input.flush().unwrap();
        let mut line = String::new();
        output.read_line(&mut line).unwrap();
        assert_eq!(
            serde_json::from_str::<serde_json::Value>(&line).unwrap()["ok"],
            true
        );
    }
    child.kill().unwrap();
    child.wait().unwrap();
    drop(input);
    drop(output);
    assert_eq!(
        Database::open(&path)
            .unwrap()
            .query("SELECT COUNT(*), SUM(value) FROM events")
            .unwrap()
            .rows,
        vec![ints(&[1, 10])]
    );
}

#[test]
fn random_ranges_match_an_independent_scan() {
    let mut seed = 0xdecafbad_u64;
    let mut next = || {
        seed ^= seed << 13;
        seed ^= seed >> 7;
        seed ^= seed << 17;
        seed
    };
    let mut db = Database::memory();
    schema(&mut db);
    let ts: Vec<_> = (0..1000_i64).map(|i| i / 3 - 150).collect();
    let values: Vec<_> = (0..1000).map(|_| (next() % 2001) as i64 - 1000).collect();
    db.append("events", vec![ts.clone(), values.clone(), vec![1; 1000]])
        .unwrap();
    for _ in 0..1000 {
        let lo = (next() % 600) as i64 - 250;
        let hi = (next() % 600) as i64 - 250;
        let matching: Vec<_> = ts
            .iter()
            .zip(&values)
            .filter(|(t, _)| **t >= lo && **t < hi)
            .map(|(_, v)| i128::from(*v))
            .collect();
        let expected_sum = if matching.is_empty() {
            Value::Null
        } else {
            Value::Int(matching.iter().sum())
        };
        let r = db
            .query(&format!(
                "SELECT COUNT(*), SUM(value) FROM events WHERE ts >= {lo} AND ts < {hi}"
            ))
            .unwrap();
        assert_eq!(
            r.rows,
            vec![vec![Value::Int(matching.len() as i128), expected_sum]]
        );
    }
}
