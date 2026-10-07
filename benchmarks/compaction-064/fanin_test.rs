use kestrel_sql::Value;
use kestrel_sql::archive::Archive;

#[test]
fn wider_compaction_keeps_row_ceiling_pinned_files_and_original_receipts() {
    for (batch_rows, expected_reduction) in [(100_i64, 63_usize), (2000, 31)] {
        let root = std::env::var_os("KESTREL_TEST_ROOT").map(std::path::PathBuf::from).unwrap_or_else(std::env::temp_dir);
        let path = root.join(format!("fanin64-{}-{batch_rows}-{}", std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos()));
        std::fs::create_dir_all(&path).unwrap();
        let mut archive = Archive::open(&path, "events", &["ts", "value", "device"]).unwrap();
        for batch in 0..70_i64 {
            let lo = batch * batch_rows;
            let receipt = archive.append_once(&format!("fanin:{batch}"), vec![(lo..lo+batch_rows).collect(), (lo..lo+batch_rows).map(|i| i*2).collect(), vec![batch; batch_rows as usize]]).unwrap();
            assert_eq!(receipt.generation, (batch+1) as u64);
        }
        let pinned = archive.snapshot().unwrap();
        let expected_rows = 70 * batch_rows;
        let expected = vec![vec![Value::Int(expected_rows.into()), Value::Int(i128::from(expected_rows)*i128::from(expected_rows-1))]];
        assert_eq!(archive.compact_small().unwrap(), expected_reduction);
        assert_eq!(archive.stats().unwrap().segments, 70-expected_reduction);
        archive.reclaim().unwrap();
        let first = path.join("segment-00000000000000000001.ks2");
        assert!(first.exists());
        assert_eq!(pinned.query("SELECT COUNT(*), SUM(value) FROM events").unwrap().result.rows, expected);
        assert_eq!(archive.query("SELECT COUNT(*), SUM(value) FROM events").unwrap().result.rows, expected);
        assert_eq!(archive.verify().unwrap(), expected_rows as u64*24);
        drop(pinned);
        archive.reclaim().unwrap();
        assert!(!first.exists());
        drop(archive);
        let mut archive = Archive::open(&path, "events", &["ts", "value", "device"]).unwrap();
        for batch in 0..70_i64 {
            let lo = batch * batch_rows;
            let receipt = archive.append_once(&format!("fanin:{batch}"), vec![(lo..lo+batch_rows).collect(), (lo..lo+batch_rows).map(|i| i*2).collect(), vec![batch; batch_rows as usize]]).unwrap();
            assert!(receipt.duplicate);
            assert_eq!(receipt.generation, (batch+1) as u64);
        }
        assert_eq!(archive.query("SELECT COUNT(*), SUM(value) FROM events").unwrap().result.rows, expected);
        assert_eq!(archive.verify().unwrap(), expected_rows as u64*24);
    }
}
