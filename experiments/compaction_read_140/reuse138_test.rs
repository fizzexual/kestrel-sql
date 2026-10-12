#[cfg(feature = "reuse-compaction-input-138")]
#[test]
fn reused_input_buffers_handle_growth_shrink_late_rows_and_two_compactions() {
    let path = temp("reuse138-growth");
    let mut archive = open(&path);
    let mut db = reference();
    let mut receipts = Vec::new();
    for (run, size) in [1, BLOCK_ROWS - 1, BLOCK_ROWS, BLOCK_ROWS + 1, 128, BLOCK_ROWS * 2 + 3, 3, 1].into_iter().enumerate() {
        let columns = data(size, 20000 - run as i64 * 5000);
        let id = format!("reuse138:{run}");
        let receipt = archive.append_once(&id, columns.clone()).unwrap();
        assert_eq!(receipt.generation, run as u64 + 1);
        db.append("events", columns.clone()).unwrap();
        receipts.push((id, columns, receipt.generation));
    }
    check(&archive, &db);
    let pinned = archive.snapshot().unwrap();
    let old_results: Vec<_> = QUERIES.iter().map(|sql| db.query(sql).unwrap().rows).collect();
    let old_bytes = archive.stats().unwrap().logical_data_bytes;
    let old_files = segments(&path);
    assert_eq!(archive.compact_small().unwrap(), 7);
    assert_eq!(archive.stats().unwrap().generation, 9);
    check(&archive, &db);
    for (offset, size) in [1, BLOCK_ROWS + 3, 17].into_iter().enumerate() {
        let run = offset + 8;
        let columns = data(size, -50000 - run as i64 * 5000);
        let id = format!("reuse138:{run}");
        let receipt = archive.append_once(&id, columns.clone()).unwrap();
        assert_eq!(receipt.generation, run as u64 + 2);
        db.append("events", columns.clone()).unwrap();
        receipts.push((id, columns, receipt.generation));
    }
    assert_eq!(archive.compact_small().unwrap(), 3);
    assert_eq!(archive.stats().unwrap().generation, 13);
    check(&archive, &db);
    let sql = "SELECT ts, COUNT(*), SUM(value), SUM(device), MIN(value), MAX(value), MIN(device), MAX(device) FROM events GROUP BY ts ORDER BY ts";
    assert_eq!(archive.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows);
    for (sql, expected) in QUERIES.iter().zip(old_results) {
        assert_eq!(pinned.query(sql).unwrap().result.rows, expected);
    }
    assert_eq!(pinned.verify().unwrap(), old_bytes);
    archive.reclaim().unwrap();
    assert!(old_files.iter().all(|p| p.exists()));
    drop(pinned);
    archive.reclaim().unwrap();
    assert!(old_files.iter().all(|p| !p.exists()));
    assert_eq!(archive.compact_small().unwrap(), 0);
    drop(archive);
    let mut reopened = open(&path);
    check(&reopened, &db);
    for (id, columns, generation) in receipts {
        let replay = reopened.append_once(&id, columns.clone()).unwrap();
        assert!(replay.duplicate);
        assert_eq!(replay.generation, generation);
        let mut wrong = columns;
        wrong[1][0] ^= 1;
        assert!(reopened.append_once(&id, wrong).is_err());
    }
    assert_eq!(reopened.stats().unwrap().generation, 13);
}
