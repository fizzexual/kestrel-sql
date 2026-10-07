//! Untimed cross-version archive-format and cold retry oracle; retain every file.
use kestrel_sql::archive::{Archive, IngestBatch};
use kestrel_sql::{Result, Value};
use serde_json::json;

fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    let path = &args[1];
    let reopen = args.iter().any(|s| s == "reopen");
    let oversized = args.iter().any(|s| s == "oversized");
    let mut archive = Archive::open(path, "events", &["ts", "value"])?;
    if oversized {
        let id = |i: i64| format!("{:06}:{}", i, "x".repeat(121));
        if !reopen {
            assert_eq!(archive.stats()?.rows, 0);
            archive.append_group((0..70_000_i64).map(|i| IngestBatch {
                id: Some(id(i)), columns: vec![vec![i], vec![i * 2]],
            }).collect())?;
            archive.append_once("after-large", vec![vec![70_000], vec![140_000]])?;
        }
        let stats = archive.stats()?;
        assert_eq!(stats.rows, 70_001);
        assert_eq!(stats.recorded_batch_ids, 70_001);
        assert_eq!(archive.verify()?, 70_001 * 16);
        assert_eq!(archive.query("SELECT COUNT(*), SUM(value) FROM events")?.result.rows,
            vec![vec![Value::Int(70_001), Value::Int(70_001 * 70_000)]]);
        for i in [0, 35_000, 69_999] {
            let r = archive.append_once(&id(i), vec![vec![i], vec![i * 2]])?;
            assert!(r.duplicate && r.generation == 1);
        }
        assert!(archive.append_once(&id(0), vec![vec![0], vec![99]]).is_err());
        assert_eq!(archive.verify()?, 70_001 * 16);
        println!("{}", json!({"version":env!("CARGO_PKG_VERSION"),"reopen":reopen,
            "oversized":true,"rows":70_001,"receipts":70_001,"generation":stats.generation,
            "crc_scrubbed_bytes":70_001*16*2,"sql_exact":true,
            "original_generations_and_group_order_preserved":true,"retry_collision_rejected":true}));
        return Ok(());
    }
    if !reopen {
        assert_eq!(archive.stats()?.rows, 0);
        for i in 0..73_i64 {
            if i == 40 {
                archive.append_group(vec![
                    IngestBatch { id: Some("B:group/40".to_owned()), columns: vec![vec![i], vec![i * 2]] },
                    IngestBatch { id: Some("A:group/40".to_owned()), columns: vec![vec![i], vec![i * 2]] },
                ])?;
            } else {
                archive.append_once(&format!("id:{i:03}"), vec![vec![i], vec![i * 2]])?;
            }
            if i == 64 { assert_eq!(archive.compact_small()?, 31); }
        }
    }
    let stats = archive.stats()?;
    assert_eq!(stats.rows, 74);
    assert_eq!(stats.recorded_batch_ids, 74);
    assert_eq!(archive.verify()?, 74 * 16);
    assert_eq!(archive.query("SELECT COUNT(*), SUM(value) FROM events")?.result.rows,
        vec![vec![Value::Int(74), Value::Int(73 * 72 + 80)]]);
    for i in [0, 32, 72] {
        let r = archive.append_once(&format!("id:{i:03}"), vec![vec![i], vec![i * 2]])?;
        assert!(r.duplicate);
        assert_eq!(r.generation, i as u64 + 1 + u64::from(i > 64));
    }
    let group = archive.append_group(vec![
        IngestBatch { id: Some("B:group/40".to_owned()), columns: vec![vec![40], vec![80]] },
        IngestBatch { id: Some("A:group/40".to_owned()), columns: vec![vec![40], vec![80]] },
    ])?;
    assert!(group.iter().all(|r| r.duplicate && r.generation == 41));
    assert!(archive.append_once("id:000", vec![vec![0], vec![99]]).is_err());
    assert_eq!(archive.verify()?, 74 * 16);
    println!("{}", json!({"version":env!("CARGO_PKG_VERSION"),"reopen":reopen,
        "rows":74,"receipts":74,"generation":stats.generation,"crc_scrubbed_bytes":74*16*2,
        "sql_exact":true,"original_generations_and_group_order_preserved":true,
        "retry_collision_rejected":true,"checkpoints":stats.publication_profile.catalog_checkpoints,
        "deltas":stats.publication_profile.catalog_deltas}));
    Ok(())
}
