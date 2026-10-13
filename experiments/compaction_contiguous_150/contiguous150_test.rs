#[cfg(feature = "contiguous-compaction-payload-150")]
#[test]
fn contiguous_compaction_payload_preserves_budget_boundaries_receipts_pins_and_reopen() {
    for total in [2, BLOCK_ROWS - 1, BLOCK_ROWS, BLOCK_ROWS + 1, 43_690, 43_691] {
        let path = temp(&format!("contiguous150-boundary-{total}"));
        let mut archive = open(&path);
        let mut db = reference();
        let mut receipts = Vec::new();
        for (run, count) in [total.div_ceil(2), total / 2].into_iter().enumerate() {
            let columns = data(count, if run == 0 { 200_000 } else { -200_000 });
            let id = format!("contiguous150:{total}:{run}");
            let receipt = archive.append_once(&id, columns.clone()).unwrap();
            assert_eq!(receipt.generation, run as u64 + 1);
            db.append("events", columns.clone()).unwrap();
            receipts.push((id, columns, receipt.generation));
        }
        check(&archive, &db);
        let pinned = archive.snapshot().unwrap();
        let old_files = segments(&path);
        assert_eq!(archive.compact_small().unwrap(), 1);
        assert_eq!(archive.stats().unwrap().generation, 3);
        check(&archive, &db);
        for sql in QUERIES {
            assert_eq!(pinned.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows);
        }
        assert_eq!(pinned.verify().unwrap(), total as u64 * 24);
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
            mismatch[1][0] ^= 1;
            assert!(reopened.append_once(&id, mismatch).is_err());
        }
        assert_eq!(reopened.stats().unwrap().generation, 3);
    }
}
