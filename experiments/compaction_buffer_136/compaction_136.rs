#![cfg(feature = "adaptive-compaction-phase-131")]

use kestrel_sql::archive::{Archive, BLOCK_ROWS};
use kestrel_sql::Database;
use std::path::{Path, PathBuf};

fn temp(label: &str) -> PathBuf {
    let root = std::env::var_os("KESTREL_TEST_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    let path = root.join(format!(
        "compaction131-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir_all(&path).unwrap();
    path
}

fn open(path: &Path) -> Archive {
    Archive::open(path, "events", &["ts", "value", "device"]).unwrap()
}

fn reference() -> Database {
    let mut db = Database::memory();
    db.execute("CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)").unwrap();
    db
}

fn data(rows: usize, seed: i64) -> Vec<Vec<i64>> {
    vec![
        (0..rows).map(|r| seed - r as i64 * 3).collect(),
        (0..rows)
            .map(|r| [i64::MIN, -13, 0, 7, i64::MAX][r % 5])
            .collect(),
        (0..rows).map(|r| r as i64 % 19 - 9).collect(),
    ]
}

const QUERIES: [&str; 4] = [
    "SELECT COUNT(*), SUM(value), SUM(device), MIN(ts), MAX(ts) FROM events",
    "SELECT COUNT(*), SUM(value), MIN(value), MAX(value) FROM events WHERE ts >= -12345 AND ts < 8192 AND device <> 0",
    "SELECT device, COUNT(*), SUM(value), MIN(value), MAX(value) FROM events GROUP BY device ORDER BY device",
    "SELECT device, COUNT(*), SUM(value) FROM events WHERE ts >= -21000 AND value >= 0 GROUP BY device ORDER BY device",
];

fn check(archive: &Archive, db: &Database) {
    for sql in QUERIES {
        assert_eq!(
            archive.query(sql).unwrap().result.rows,
            db.query(sql).unwrap().rows,
            "{sql}"
        );
    }
    assert_eq!(archive.verify().unwrap(), archive.stats().unwrap().logical_data_bytes);
}

fn catalogs(path: &Path) -> Vec<(String, Vec<u8>)> {
    let mut files: Vec<_> = std::fs::read_dir(path)
        .unwrap()
        .map(|e| e.unwrap().path())
        .filter(|p| p.file_name().unwrap().to_string_lossy().starts_with("catalog-"))
        .map(|p| (p.file_name().unwrap().to_string_lossy().into_owned(), std::fs::read(p).unwrap()))
        .collect();
    files.sort();
    files
}

fn segments(path: &Path) -> Vec<PathBuf> {
    let mut files: Vec<_> = std::fs::read_dir(path)
        .unwrap()
        .map(|e| e.unwrap().path())
        .filter(|p| p.file_name().unwrap().to_string_lossy().starts_with("segment-"))
        .collect();
    files.sort();
    files
}

#[test]
fn compaction_workspace_preserves_sql_receipts_pinned_views_and_reopen() {
    let path = temp("pinned-retry");
    let mut archive = open(&path);
    let mut db = reference();
    let mut receipts = Vec::new();
    let mut rows = 0usize;
    for (n, size) in [1, BLOCK_ROWS - 1, BLOCK_ROWS, BLOCK_ROWS + 17].into_iter().enumerate() {
        let columns = data(size, 18000 - n as i64 * 5000);
        let id = format!("compact131:{n}");
        let receipt = archive.append_once(&id, columns.clone()).unwrap();
        assert!(!receipt.duplicate);
        db.append("events", columns.clone()).unwrap();
        receipts.push((id, columns, receipt.generation));
        rows += size;
    }
    check(&archive, &db);
    let pinned = archive.snapshot().unwrap();
    let old_files = segments(&path);
    let old_results: Vec<_> = QUERIES.iter().map(|sql| db.query(sql).unwrap().rows).collect();
    let before = archive.stats().unwrap().generation;
    assert_eq!(archive.compact_small().unwrap(), 3);
    assert_eq!(archive.stats().unwrap().generation, before + 1);
    check(&archive, &db);
    let late = data(BLOCK_ROWS * 2 + 1, -30000);
    let receipt = archive.append_once("compact131:late", late.clone()).unwrap();
    db.append("events", late.clone()).unwrap();
    receipts.push(("compact131:late".into(), late, receipt.generation));
    rows += BLOCK_ROWS * 2 + 1;
    assert_eq!(archive.compact_small().unwrap(), 1);
    let stable = archive.stats().unwrap().generation;
    assert_eq!(archive.compact_small().unwrap(), 0);
    assert_eq!(archive.stats().unwrap().generation, stable);
    for (id, columns, generation) in &receipts {
        let replay = archive.append_once(id, columns.clone()).unwrap();
        assert!(replay.duplicate);
        assert_eq!(replay.generation, *generation);
        assert_eq!(replay.rows, columns[0].len());
    }
    assert_eq!(archive.stats().unwrap().generation, stable);
    let mut changed = receipts[0].1.clone();
    changed[1][0] = 123;
    assert!(archive.append_once(&receipts[0].0, changed).is_err());
    archive.reclaim().unwrap();
    assert!(old_files.iter().all(|p| p.exists()));
    for (sql, expected) in QUERIES.iter().zip(old_results) {
        assert_eq!(pinned.query(sql).unwrap().result.rows, expected);
    }
    assert_eq!(pinned.verify().unwrap(), u64::try_from(rows - (BLOCK_ROWS * 2 + 1)).unwrap() * 24);
    check(&archive, &db);
    drop(pinned);
    archive.reclaim().unwrap();
    assert!(old_files.iter().all(|p| !p.exists()));
    drop(archive);
    let mut reopened = open(&path);
    assert_eq!(reopened.stats().unwrap().rows, u64::try_from(rows).unwrap());
    check(&reopened, &db);
    for (id, columns, generation) in receipts {
        let replay = reopened.append_once(&id, columns).unwrap();
        assert!(replay.duplicate);
        assert_eq!(replay.generation, generation);
    }
    assert_eq!(reopened.stats().unwrap().generation, stable);
}

#[test]
fn compaction_late_crc_and_truncation_fail_before_publish_then_recover() {
    let path = temp("late-corruption");
    let mut archive = open(&path);
    let mut db = reference();
    for (n, size) in [BLOCK_ROWS + 17, BLOCK_ROWS, BLOCK_ROWS + 3].into_iter().enumerate() {
        let columns = data(size, 20000 - n as i64 * 15000);
        archive.append(columns.clone()).unwrap();
        db.append("events", columns).unwrap();
    }
    let pinned = archive.snapshot().unwrap();
    let before = archive.stats().unwrap();
    let before_catalogs = catalogs(&path);
    let before_segments = segments(&path);
    let target = before_segments.last().unwrap();
    let original = std::fs::read(target).unwrap();
    let mut damaged = original.clone();
    *damaged.last_mut().unwrap() ^= 1;
    let evidence = path.join("failure-evidence-131");
    std::fs::create_dir(&evidence).unwrap();
    std::fs::write(evidence.join("crc-input.ks2"), &damaged).unwrap();
    std::fs::write(target, damaged).unwrap();
    let error = archive.compact_small().unwrap_err().to_string();
    assert!(error.contains("checksum"), "{error}");
    std::fs::write(evidence.join("crc-error.txt"), error).unwrap();
    assert_eq!(archive.stats().unwrap().generation, before.generation);
    assert_eq!(archive.stats().unwrap().rows, before.rows);
    assert_eq!(catalogs(&path), before_catalogs);
    assert_eq!(segments(&path), before_segments);
    assert!(archive.verify().is_err());
    std::fs::write(target, &original).unwrap();
    check(&archive, &db);
    let truncated = &original[..original.len() - 1];
    std::fs::write(evidence.join("truncated-input.ks2"), truncated).unwrap();
    std::fs::write(target, truncated).unwrap();
    let error = archive.compact_small().unwrap_err().to_string();
    std::fs::write(evidence.join("truncation-error.txt"), error).unwrap();
    assert_eq!(archive.stats().unwrap().generation, before.generation);
    assert_eq!(catalogs(&path), before_catalogs);
    assert_eq!(segments(&path), before_segments);
    std::fs::write(target, &original).unwrap();
    assert_eq!(archive.compact_small().unwrap(), 2);
    assert_eq!(archive.stats().unwrap().generation, before.generation + 1);
    check(&archive, &db);
    for sql in QUERIES {
        assert_eq!(pinned.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows);
    }
    assert_eq!(pinned.verify().unwrap(), before.logical_data_bytes);
    drop(pinned);
    archive.reclaim().unwrap();
    drop(archive);
    check(&open(&path), &db);
}


#[test]
fn ordered_equal_signed_boundaries_still_validate_all_crc_rows_receipts_and_pins() {
    let path = temp("ordered-boundary-crc");
    let mut archive = open(&path);
    let mut db = reference();
    let mut receipts = Vec::new();
    for (run, size) in [1, BLOCK_ROWS, BLOCK_ROWS + 1].into_iter().enumerate() {
        let first = if run < 2 { i64::MIN } else { i64::MIN + BLOCK_ROWS as i64 - 1 };
        let columns: Vec<Vec<i64>> = vec![
            (0..size).map(|row| first + row as i64).collect(),
            (0..size).map(|row| [i64::MIN, -7, 0, 11, i64::MAX][row % 5]).collect(),
            (0..size).map(|row| row as i64 % 19 - 9).collect(),
        ];
        let id = format!("phase131:ordered:{run}");
        let receipt = archive.append_once(&id, columns.clone()).unwrap();
        db.append("events", columns.clone()).unwrap();
        receipts.push((id, columns, receipt.generation));
    }
    check(&archive, &db);
    let pinned = archive.snapshot().unwrap();
    let before = archive.stats().unwrap();
    let before_catalogs = catalogs(&path);
    let before_segments = segments(&path);
    let target = before_segments.last().unwrap();
    let original = std::fs::read(target).unwrap();
    let mut corrupt = original.clone();
    *corrupt.last_mut().unwrap() ^= 1;
    std::fs::write(target, corrupt).unwrap();
    let error = archive.compact_small().unwrap_err().to_string();
    assert!(error.contains("checksum"), "{error}");
    assert_eq!(archive.stats().unwrap().generation, before.generation);
    assert_eq!(catalogs(&path), before_catalogs);
    assert_eq!(segments(&path), before_segments);
    std::fs::write(target, original).unwrap();
    assert_eq!(archive.compact_small().unwrap(), 2);
    assert_eq!(archive.stats().unwrap().generation, before.generation + 1);
    check(&archive, &db);
    let sql = "SELECT ts, COUNT(*), SUM(value), SUM(device), MIN(value), MAX(value), MIN(device), MAX(device) FROM events GROUP BY ts ORDER BY ts";
    assert_eq!(archive.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows);
    archive.reclaim().unwrap();
    assert!(before_segments.iter().all(|segment| segment.exists()));
    assert_eq!(pinned.verify().unwrap(), before.logical_data_bytes);
    drop(pinned);
    archive.reclaim().unwrap();
    assert!(before_segments.iter().all(|segment| !segment.exists()));
    drop(archive);
    let mut reopened = open(&path);
    check(&reopened, &db);
    for (id, columns, generation) in receipts {
        let retry = reopened.append_once(&id, columns).unwrap();
        assert!(retry.duplicate);
        assert_eq!(retry.generation, generation);
    }
    assert_eq!(reopened.stats().unwrap().generation, before.generation + 1);
}


#[test]
fn unequal_unordered_runs_preserve_every_column_receipt_pin_and_cold_reopen() {
    let path = temp("unequal-unordered");
    let mut archive = open(&path);
    let mut db = reference();
    let mut receipts = Vec::new();
    for (run, size) in [1, BLOCK_ROWS + 1, 37, BLOCK_ROWS * 2 + 3].into_iter().enumerate() {
        let first = [30_000, 10_000, -10_000, -30_000][run];
        let columns: Vec<Vec<i64>> = vec![
            (0..size).map(|row| first + row as i64).collect(),
            (0..size).map(|row| [i64::MIN, -7, 0, 11, i64::MAX][row % 5]).collect(),
            (0..size).map(|row| (row % 23) as i64 - run as i64 * 9).collect(),
        ];
        let id = format!("phase131:unequal:{run}");
        let receipt = archive.append_once(&id, columns.clone()).unwrap();
        db.append("events", columns.clone()).unwrap();
        receipts.push((id, columns, receipt.generation));
    }
    check(&archive, &db);
    let before = archive.stats().unwrap();
    let old_files = segments(&path);
    let pinned = archive.snapshot().unwrap();
    assert_eq!(archive.compact_small().unwrap(), 3);
    assert_eq!(archive.stats().unwrap().generation, before.generation + 1);
    check(&archive, &db);
    let sql = "SELECT ts, COUNT(*), SUM(value), SUM(device), MIN(value), MAX(value), MIN(device), MAX(device) FROM events GROUP BY ts ORDER BY ts";
    assert_eq!(archive.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows);
    assert_eq!(pinned.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows);
    assert_eq!(pinned.verify().unwrap(), before.logical_data_bytes);
    archive.reclaim().unwrap();
    assert!(old_files.iter().all(|p| p.exists()));
    drop(pinned);
    archive.reclaim().unwrap();
    assert!(old_files.iter().all(|p| !p.exists()));
    drop(archive);
    let mut reopened = open(&path);
    check(&reopened, &db);
    for (id, columns, generation) in receipts {
        let replay = reopened.append_once(&id, columns.clone()).unwrap();
        assert!(replay.duplicate);
        assert_eq!(replay.generation, generation);
        let mut mismatch = columns;
        mismatch[2][0] += 1;
        assert!(reopened.append_once(&id, mismatch).is_err());
    }
    assert_eq!(reopened.stats().unwrap().generation, before.generation + 1);
}


#[cfg(feature = "adaptive-segment-buffer-136")]
#[test]
fn small_and_large_compactions_keep_rows_receipts_pins_and_cold_reopen() {
    for (label, size) in [("buffer136-small", 1024), ("buffer136-large", 32767)] {
        let path = temp(label);
        let mut archive = open(&path);
        let mut db = reference();
        let mut receipts = Vec::new();
        for run in 0..2 {
            let first = if run == 0 { 200_000 } else { -200_000 };
            let columns: Vec<Vec<i64>> = vec![
                (0..size).map(|row| first + row as i64).collect(),
                (0..size).map(|row| [i64::MIN, -7, 0, 11, i64::MAX][row % 5]).collect(),
                (0..size).map(|row| (row % 19) as i64 + run as i64 * 31 - 9).collect(),
            ];
            let id = format!("buffer136:{label}:{run}");
            let receipt = archive.append_once(&id, columns.clone()).unwrap();
            db.append("events", columns.clone()).unwrap();
            receipts.push((id, columns, receipt.generation));
        }
        check(&archive, &db);
        let before = archive.stats().unwrap();
        let old_files = segments(&path);
        let pinned = archive.snapshot().unwrap();
        assert_eq!(archive.compact_small().unwrap(), 1);
        assert_eq!(archive.stats().unwrap().generation, before.generation + 1);
        check(&archive, &db);
        let sql = "SELECT ts, COUNT(*), SUM(value), SUM(device), MIN(value), MAX(value), MIN(device), MAX(device) FROM events GROUP BY ts ORDER BY ts";
        assert_eq!(archive.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows);
        assert_eq!(pinned.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows);
        assert_eq!(pinned.verify().unwrap(), before.logical_data_bytes);
        archive.reclaim().unwrap();
        assert!(old_files.iter().all(|p| p.exists()));
        drop(pinned);
        archive.reclaim().unwrap();
        assert!(old_files.iter().all(|p| !p.exists()));
        drop(archive);
        let mut reopened = open(&path);
        check(&reopened, &db);
        for (id, columns, generation) in receipts {
            let replay = reopened.append_once(&id, columns.clone()).unwrap();
            assert!(replay.duplicate);
            assert_eq!(replay.generation, generation);
            let mut mismatch = columns;
            mismatch[1][0] = 123;
            assert!(reopened.append_once(&id, mismatch).is_err());
        }
        assert_eq!(reopened.stats().unwrap().generation, before.generation + 1);
    }
}
