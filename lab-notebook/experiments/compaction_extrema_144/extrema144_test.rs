#[cfg(feature = "reuse-publish-extrema-144")]
#[test]
fn block_derived_global_extrema_preserve_boundaries_receipts_pins_and_cold_queries() {
    for count in [1, BLOCK_ROWS - 1, BLOCK_ROWS, BLOCK_ROWS + 1, BLOCK_ROWS * 2 + 1] {
        let path = temp(&format!("extrema144-boundary-{count}"));
        let mut archive = open(&path);
        let mut db = reference();
        let mut receipts = Vec::new();
        for run in 0..2 {
            let columns = vec![
                (0..count).map(|row| if run == 0 { row as i64 + 10000 } else { -(row as i64) - 10000 }).collect(),
                (0..count).map(|row| [i64::MIN, -7, 0, 11, i64::MAX][(row + run) % 5]).collect(),
                (0..count).map(|row| if row % 4096 == 4095 { i64::MAX } else if row % 4096 == 0 { i64::MIN } else { row as i64 - 5000 }).collect(),
            ];
            let id = format!("extrema144:{count}:{run}");
            let receipt = archive.append_once(&id, columns.clone()).unwrap();
            assert_eq!(receipt.generation, run as u64 + 1);
            db.append("events", columns.clone()).unwrap();
            receipts.push((id, columns, receipt.generation));
        }
        let queries = [
            "SELECT ts, SUM(value), MIN(value), MAX(value), SUM(device), MIN(device), MAX(device), COUNT(*) FROM events GROUP BY ts ORDER BY ts",
            "SELECT ts, SUM(value), SUM(device), COUNT(*) FROM events WHERE value >= -7 AND value <= 11 GROUP BY ts ORDER BY ts",
            "SELECT ts, MIN(device), MAX(device), COUNT(*) FROM events WHERE device >= 0 GROUP BY ts ORDER BY ts",
        ];
        for sql in queries { assert_eq!(archive.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows); }
        let pinned = archive.snapshot().unwrap();
        assert_eq!(archive.compact_small().unwrap(), 1);
        assert_eq!(archive.stats().unwrap().generation, 3);
        for sql in queries {
            let expected = db.query(sql).unwrap().rows;
            assert_eq!(archive.query(sql).unwrap().result.rows, expected);
            assert_eq!(pinned.query(sql).unwrap().result.rows, expected);
        }
        assert_eq!(archive.verify().unwrap(), count as u64 * 2 * 3 * 8);
        assert_eq!(pinned.verify().unwrap(), count as u64 * 2 * 3 * 8);
        archive.reclaim().unwrap();
        drop(pinned);
        archive.reclaim().unwrap();
        drop(archive);
        let mut reopened = open(&path);
        for sql in queries { assert_eq!(reopened.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows); }
        for (id, columns, generation) in receipts {
            let replay = reopened.append_once(&id, columns.clone()).unwrap();
            assert!(replay.duplicate);
            assert_eq!(replay.generation, generation);
            let mut mismatch = columns;
            mismatch[1][0] ^= 1;
            assert!(reopened.append_once(&id, mismatch).is_err());
        }
        assert_eq!(reopened.stats().unwrap().generation, 3);
    }
}
