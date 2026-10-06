use kestrel_sql::archive::{Archive, BLOCK_ROWS};
use kestrel_sql::{Database, Value};
use std::path::PathBuf;

fn temp(label: &str) -> PathBuf {
    let root = std::env::var_os("KESTREL_TEST_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    let path = root.join(format!(
        "archive-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir_all(&path).unwrap();
    path
}
fn open(path: &std::path::Path) -> Archive {
    Archive::open(path, "events", &["ts", "value", "device"]).unwrap()
}
fn int(n: i128) -> Vec<Vec<Value>> {
    vec![vec![Value::Int(n)]]
}

#[test]
fn sparse_prefix_crosses_pages_duplicates_and_segment_boundaries() {
    let path = temp("bounds");
    let mut archive = open(&path);
    let mut reference = Database::memory();
    reference.execute("CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)").unwrap();
    for batch in 0..3 {
        let ts: Vec<_> = (0..BLOCK_ROWS * 3 + 17)
            .map(|i| i as i64 / 3 + batch * 2000 - 3000)
            .collect();
        let values: Vec<_> = (0..ts.len())
            .map(|i| (i as i64 * 13) % 4001 - 2000)
            .collect();
        let devices: Vec<_> = (0..ts.len()).map(|i| i as i64 % 7).collect();
        reference
            .append("events", vec![ts.clone(), values.clone(), devices.clone()])
            .unwrap();
        archive.append(vec![ts, values, devices]).unwrap();
    }
    for lo in [-9000, -3000, -1635, 0, 1097, 3500, 9000] {
        for hi in [-5000, -1000, 0, 1098, 5000, 12000] {
            let sql = format!(
                "SELECT COUNT(*), SUM(value), AVG(value), MIN(value), MAX(value) FROM events WHERE ts >= {lo} AND ts < {hi}"
            );
            assert_eq!(
                archive.query(&sql).unwrap().result.rows,
                reference.query(&sql).unwrap().rows,
                "{sql}"
            );
        }
    }
    assert_eq!(
        archive.verify().unwrap(),
        archive.stats().unwrap().logical_data_bytes
    );
    let count = archive.stats().unwrap().rows;
    drop(archive);
    let reopened = open(&path);
    assert_eq!(reopened.stats().unwrap().rows, count);
    assert_eq!(
        reopened
            .query("SELECT COUNT(*) FROM events")
            .unwrap()
            .bytes_read,
        0
    );
}

#[test]
fn out_of_order_input_and_late_batches_preserve_fast_exact_results() {
    let path = temp("late");
    let mut archive = open(&path);
    archive
        .append(vec![
            vec![4, 1, 3, 2],
            vec![40, 10, 30, 20],
            vec![2, 1, 2, 1],
        ])
        .unwrap();
    archive
        .append(vec![vec![-10, 0, 2], vec![5, 6, 7], vec![1, 2, 1]])
        .unwrap();
    let r = archive
        .query("SELECT COUNT(*), SUM(value), AVG(value) FROM events WHERE ts >= 1 AND ts <= 3")
        .unwrap();
    assert_eq!(
        r.result.rows,
        vec![vec![Value::Int(4), Value::Int(67), Value::Float(16.75)]]
    );
    assert_eq!(r.result.plan, "segmented-sparse-prefix");
    assert_eq!(archive.verify().unwrap(), 7 * 3 * 8);
}

#[test]
fn grouped_scans_filters_and_empty_input_match_memory_engine() {
    let path = temp("scans");
    let mut archive = open(&path);
    let mut reference = Database::memory();
    reference.execute("CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)").unwrap();
    for batch in 0..4 {
        let ts: Vec<_> = (0..5000).map(|i| i + batch * 6000).collect();
        let values: Vec<_> = ts.iter().map(|i| (i * 17) % 200 - 100).collect();
        let groups: Vec<_> = ts.iter().map(|i| i % 11 - 5).collect();
        reference
            .append("events", vec![ts.clone(), values.clone(), groups.clone()])
            .unwrap();
        archive.append(vec![ts, values, groups]).unwrap();
    }
    for sql in [
        "SELECT device, COUNT(*) AS n, SUM(value) AS s, AVG(value) AS a, MIN(value), MAX(value) FROM events GROUP BY device ORDER BY device",
        "SELECT SUM(value), COUNT(*) FROM events WHERE value >= 0",
        "SELECT COUNT(*), SUM(value) FROM events WHERE ts <> 1000",
        "SELECT device, SUM(value) AS s FROM events WHERE ts >= 1500 AND value < 40 GROUP BY device ORDER BY s DESC LIMIT 3",
        "SELECT COUNT(*), SUM(value), MIN(value) FROM events WHERE ts < -1",
        "SELECT SUM(value) FROM events LIMIT 0",
    ] {
        assert_eq!(
            archive.query(sql).unwrap().result.rows,
            reference.query(sql).unwrap().rows,
            "{sql}"
        );
    }
    assert!(archive.query("SELECT value FROM events").is_err());
    assert!(archive.query("SELECT COUNT(*) FROM missing").is_err());
    assert!(
        archive
            .query("SELECT SUM(value) FROM events ORDER BY missing LIMIT 0")
            .is_err()
    );
    assert!(archive.append(vec![vec![1], vec![2, 3], vec![1]]).is_err());
    assert!(archive.append(vec![vec![], vec![1], vec![]]).is_err());
}

#[test]
fn extreme_sums_survive_disk_metadata_serialization() {
    let path = temp("extremes");
    let mut archive = open(&path);
    archive
        .append(vec![
            vec![i64::MIN, i64::MAX, i64::MAX],
            vec![i64::MAX; i64::BITS as usize],
            vec![1; 3],
        ])
        .unwrap_err();
    archive
        .append(vec![
            vec![i64::MIN, i64::MAX, i64::MAX],
            vec![i64::MAX; 3],
            vec![1; 3],
        ])
        .unwrap();
    drop(archive);
    let archive = open(&path);
    assert_eq!(
        archive
            .query("SELECT SUM(value) FROM events")
            .unwrap()
            .result
            .rows,
        int(i128::from(i64::MAX) * 3)
    );
    assert_eq!(
        archive
            .query("SELECT COUNT(*) FROM events WHERE ts >= 9223372036854775807")
            .unwrap()
            .result
            .rows,
        int(2)
    );
}

#[test]
fn orphan_segments_and_pending_catalogs_are_not_published() {
    let path = temp("orphans");
    let mut archive = open(&path);
    archive.append(vec![vec![1], vec![10], vec![1]]).unwrap();
    drop(archive);
    std::fs::write(
        path.join("segment-00000000000000000002.ks2"),
        b"partial uncommitted segment",
    )
    .unwrap();
    std::fs::write(
        path.join("catalog-00000000000000000002.pending"),
        b"partial catalog",
    )
    .unwrap();
    let mut archive = open(&path);
    assert_eq!(
        archive
            .query("SELECT SUM(value) FROM events")
            .unwrap()
            .result
            .rows,
        int(10)
    );
    archive.append(vec![vec![2], vec![20], vec![1]]).unwrap();
    drop(archive);
    assert_eq!(
        open(&path)
            .query("SELECT SUM(value) FROM events")
            .unwrap()
            .result
            .rows,
        int(30)
    );
}

#[test]
fn data_corruption_is_detected_on_read_and_full_verification() {
    let path = temp("corruption");
    let mut archive = open(&path);
    let ts: Vec<_> = (0..10000).collect();
    archive
        .append(vec![ts.clone(), ts, vec![1; 10000]])
        .unwrap();
    drop(archive);
    let segment = path.join("segment-00000000000000000001.ks2");
    let mut bytes = std::fs::read(&segment).unwrap();
    let offset = 16 + u32::from_le_bytes(bytes[8..12].try_into().unwrap()) as usize;
    bytes[offset + 10000 * 8 + 6000 * 8] ^= 1;
    std::fs::write(segment, bytes).unwrap();
    let archive = open(&path);
    assert!(
        archive
            .query("SELECT SUM(value) FROM events WHERE ts >= 5000 AND ts < 7000")
            .is_err()
    );
    assert!(archive.verify().is_err());
}

#[test]
fn metadata_corruption_and_missing_referenced_files_fail_closed() {
    for damage in ["catalog", "metadata", "missing"] {
        let path = temp(damage);
        let mut archive = open(&path);
        archive.append(vec![vec![1], vec![2], vec![3]]).unwrap();
        drop(archive);
        let name = if damage == "catalog" {
            "catalog-00000000000000000001.ks2"
        } else {
            "segment-00000000000000000001.ks2"
        };
        let file = path.join(name);
        if damage == "missing" {
            std::fs::rename(&file, path.join("unreferenced.ks2")).unwrap();
        } else {
            let mut bytes = std::fs::read(&file).unwrap();
            bytes[20] ^= 1;
            std::fs::write(file, bytes).unwrap();
        }
        assert!(Archive::open(&path, "events", &["ts", "value", "device"]).is_err());
    }
}

#[test]
fn empty_archives_schema_and_locks_have_explicit_behavior() {
    let case_path = temp("schema-case");
    assert!(Archive::open(&case_path, "events", &["TS", "ts"]).is_err());
    let mut uppercase = Archive::open(&case_path, "EVENTS", &["TS", "Value", "Device"]).unwrap();
    uppercase.append(vec![vec![1], vec![2], vec![3]]).unwrap();
    assert_eq!(
        uppercase
            .query("SELECT SUM(VALUE) FROM EVENTS")
            .unwrap()
            .result
            .rows,
        int(2)
    );
    drop(uppercase);
    assert_eq!(open(&case_path).stats().unwrap().rows, 1);
    let path = temp("empty");
    let archive = open(&path);
    assert_eq!(
        archive
            .query("SELECT COUNT(*), SUM(value), AVG(value) FROM events")
            .unwrap()
            .result
            .rows,
        vec![vec![Value::Int(0), Value::Null, Value::Null]]
    );
    assert!(Archive::open(&path, "events", &["ts", "value", "device"]).is_err());
    drop(archive);
    let mut archive = open(&path);
    archive.append(vec![vec![1], vec![2], vec![3]]).unwrap();
    drop(archive);
    assert!(Archive::open(&path, "events", &["ts", "other", "device"]).is_err());
}
