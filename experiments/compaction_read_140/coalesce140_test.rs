#[cfg(feature = "coalesced-compaction-read-140")]
#[test]
fn bounded_compaction_reads_preserve_wide_rows_below_at_and_above_one_mib() {
    let names: Vec<String> = std::iter::once("ts".to_owned())
        .chain((1..16).map(|c| format!("c{c}"))).collect();
    let columns: Vec<&str> = names.iter().map(String::as_str).collect();
    let create = format!("CREATE TABLE events ({})", names.iter()
        .map(|name| format!("{name} BIGINT NOT NULL")).collect::<Vec<_>>().join(", "));
    let grouped = format!("SELECT ts, {} FROM events GROUP BY ts ORDER BY ts", names[1..].iter()
        .map(|name| format!("SUM({name})")).collect::<Vec<_>>().join(", "));
    for count in [8191, 8192, 8193] {
        let path = temp(&format!("coalesce140-threshold-{count}"));
        let mut archive = Archive::open(&path, "events", &columns).unwrap();
        let mut db = Database::memory();
        db.execute(&create).unwrap();
        let mut receipts = Vec::new();
        for run in 0..2 {
            let values: Vec<Vec<i64>> = (0..16).map(|column| (0..count).map(|row| {
                if column == 0 { 30000 - run as i64 * 20000 - row as i64 * 3 }
                else { [i64::MIN, -13, 0, 7, i64::MAX][(row + column + run) % 5] }
            }).collect()).collect();
            let id = format!("coalesce140:{count}:{run}");
            let receipt = archive.append_once(&id, values.clone()).unwrap();
            assert_eq!(receipt.generation, run as u64 + 1);
            db.append("events", values.clone()).unwrap();
            receipts.push((id, values, receipt.generation));
        }
        let expected = db.query(&grouped).unwrap().rows;
        assert_eq!(archive.query(&grouped).unwrap().result.rows, expected);
        let pinned = archive.snapshot().unwrap();
        assert_eq!(archive.compact_small().unwrap(), 1);
        assert_eq!(archive.stats().unwrap().generation, 3);
        assert_eq!(archive.query(&grouped).unwrap().result.rows, expected);
        assert_eq!(pinned.query(&grouped).unwrap().result.rows, expected);
        assert_eq!(archive.verify().unwrap(), count as u64 * 2 * 16 * 8);
        assert_eq!(pinned.verify().unwrap(), count as u64 * 2 * 16 * 8);
        drop(pinned);
        archive.reclaim().unwrap();
        drop(archive);
        let mut archive = Archive::open(&path, "events", &columns).unwrap();
        assert_eq!(archive.query(&grouped).unwrap().result.rows, expected);
        for (id, values, generation) in receipts {
            let replay = archive.append_once(&id, values.clone()).unwrap();
            assert!(replay.duplicate);
            assert_eq!(replay.generation, generation);
            let mut mismatch = values;
            mismatch[15][0] ^= 1;
            assert!(archive.append_once(&id, mismatch).is_err());
        }
        assert_eq!(archive.stats().unwrap().generation, 3);
    }
}

#[cfg(feature = "coalesced-compaction-read-140")]
#[test]
fn bounded_compaction_checks_last_column_partial_block_and_truncation_before_publication() {
    let path = temp("coalesce140-final-crc");
    let mut archive = open(&path);
    let mut db = reference();
    let mut receipts = Vec::new();
    for (run, count) in [4113, 17].into_iter().enumerate() {
        let values = data(count, 20000 - run as i64 * 21000);
        let id = format!("coalesce140:crc:{run}");
        let receipt = archive.append_once(&id, values.clone()).unwrap();
        db.append("events", values.clone()).unwrap();
        receipts.push((id, values, receipt.generation));
    }
    check(&archive, &db);
    let before = archive.stats().unwrap();
    let before_catalogs = catalogs(&path);
    let before_segments = segments(&path);
    let target = &before_segments[0];
    let original = std::fs::read(target).unwrap();
    let evidence = path.join("failure-evidence-140");
    std::fs::create_dir(&evidence).unwrap();
    let mut damaged = original.clone();
    *damaged.last_mut().unwrap() ^= 1;
    std::fs::write(evidence.join("crc-input.ks2"), &damaged).unwrap();
    std::fs::write(target, damaged).unwrap();
    let error = archive.compact_small().unwrap_err().to_string();
    assert!(error.contains("checksum"), "{error}");
    std::fs::write(evidence.join("crc-error.txt"), error).unwrap();
    assert_eq!(archive.stats().unwrap().generation, before.generation);
    assert_eq!(catalogs(&path), before_catalogs);
    assert_eq!(segments(&path), before_segments);
    std::fs::write(target, &original).unwrap();
    check(&archive, &db);
    std::fs::write(target, &original[..original.len() - 1]).unwrap();
    let error = archive.compact_small().unwrap_err().to_string();
    std::fs::write(evidence.join("truncation-error.txt"), error).unwrap();
    assert_eq!(archive.stats().unwrap().generation, before.generation);
    assert_eq!(catalogs(&path), before_catalogs);
    assert_eq!(segments(&path), before_segments);
    std::fs::write(target, &original).unwrap();
    assert_eq!(archive.compact_small().unwrap(), 1);
    check(&archive, &db);
    archive.reclaim().unwrap();
    drop(archive);
    let mut archive = open(&path);
    check(&archive, &db);
    for (id, values, generation) in receipts {
        let replay = archive.append_once(&id, values).unwrap();
        assert!(replay.duplicate);
        assert_eq!(replay.generation, generation);
    }
    assert_eq!(archive.stats().unwrap().generation, 3);
}
