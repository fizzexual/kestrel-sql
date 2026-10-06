//! Sequential durable publications at fixed receipt-ledger sizes. Setup, checks,
//! stats, reclaim and reopen are outside the per-append timing.
use kestrel_sql::archive::{Archive, IngestBatch};
use kestrel_sql::{Result, Value};
use serde_json::json;
use std::time::Instant;

fn open(path: &str) -> Result<Archive> {
    Archive::open(path, "events", &["ts", "value", "device"])
}

fn main() -> Result<()> {
    let arguments: Vec<_> = std::env::args().collect();
    let path = arguments.get(1).expect("pass a fresh store directory");
    let ids: i64 = arguments.get(2).map_or(50_000, |s| s.parse().unwrap());
    let repetitions: usize = arguments.get(3).map_or(96, |s| s.parse().unwrap());
    assert!((0..=99_000).contains(&ids) && (32..=512).contains(&repetitions));
    let mut archive = open(path)?;
    assert_eq!(archive.stats()?.rows, 0, "use a fresh store");
    if ids > 0 {
        archive.append_group(
            (0..ids)
                .map(|i| IngestBatch {
                    id: Some(format!("seed:{i}")),
                    columns: vec![vec![i], vec![i * 2], vec![i % 97]],
                })
                .collect(),
        )?;
    }
    let before = archive.stats()?;
    let mut samples = Vec::new();
    let mut catalog_bytes = Vec::new();
    let mut maintenance_ms = Vec::new();
    let mut expected_sum = i128::from(ids) * i128::from(ids - 1);
    for batch in 0..repetitions {
        let lo = ids + batch as i64 * 100;
        let data = vec![
            (lo..lo + 100).collect(),
            (lo..lo + 100).map(|i| i * 2).collect(),
            (lo..lo + 100).map(|i| i % 97).collect(),
        ];
        let started = Instant::now();
        let receipt = archive.append_once(&format!("new:{batch}"), data)?;
        samples.push(started.elapsed().as_secs_f64() * 1000.0);
        assert!(!receipt.duplicate && receipt.rows == 100);
        expected_sum += i128::from(2 * lo + 99) * 100;
        let file =
            std::path::Path::new(path).join(format!("catalog-{:020}.ks2", receipt.generation));
        catalog_bytes.push(std::fs::metadata(file)?.len());
        if (batch + 1).is_multiple_of(32) {
            let started = Instant::now();
            archive.compact_small()?;
            archive.reclaim()?;
            maintenance_ms.push(started.elapsed().as_secs_f64() * 1000.0);
        }
    }
    let after = archive.stats()?;
    let expected_rows = ids as u64 + repetitions as u64 * 100;
    assert_eq!(after.rows, expected_rows);
    assert_eq!(after.recorded_batch_ids, ids as usize + repetitions);
    assert_eq!(
        archive
            .query("SELECT COUNT(*), SUM(value) FROM events")?
            .result
            .rows,
        vec![vec![
            Value::Int(expected_rows.into()),
            Value::Int(expected_sum)
        ]]
    );
    assert_eq!(archive.verify()?, expected_rows * 24);
    drop(archive);
    let started = Instant::now();
    let mut archive = open(path)?;
    let reopen_ms = started.elapsed().as_secs_f64() * 1000.0;
    assert_eq!(
        archive.stats()?.recorded_batch_ids,
        ids as usize + repetitions
    );
    for batch in [0, repetitions / 2, repetitions - 1] {
        let lo = ids + batch as i64 * 100;
        assert!(
            archive
                .append_once(
                    &format!("new:{batch}"),
                    vec![
                        (lo..lo + 100).collect(),
                        (lo..lo + 100).map(|i| i * 2).collect(),
                        (lo..lo + 100).map(|i| i % 97).collect(),
                    ]
                )?
                .duplicate
        );
    }
    assert_eq!(archive.verify()?, expected_rows * 24);
    println!(
        "{}",
        json!({
            "version":env!("CARGO_PKG_VERSION"), "probe":"new_identified_publication",
            "prefill_receipt_count":ids,"repetitions":repetitions,
            "raw_latency_ms":samples,"raw_catalog_bytes":catalog_bytes,
            "maintenance_ms":maintenance_ms,"reopen_ms":reopen_ms,
            "before":before,"after":after,"rows_and_sum_match":true,
            "reopen_retry_and_full_scrub_passed":true,
        })
    );
    Ok(())
}
