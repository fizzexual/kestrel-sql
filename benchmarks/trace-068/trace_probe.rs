//! Single-process stage diagnostics. Nothing is written to stdout during calls.
use kestrel_sql::archive::{Archive, IngestBatch, PublicationTrace, PUBLICATION_TRACE_STAGES};
use kestrel_sql::{Result, Value};
use serde::Serialize;
use serde_json::json;
use std::time::Instant;

#[derive(Serialize)]
struct Observation {
    operation: &'static str,
    batch: usize,
    outer_ms: f64,
    trace: PublicationTrace,
}

#[derive(Serialize)]
struct ReclaimObservation {
    after_batch: usize,
    outer_ms: f64,
    removed_files: usize,
}

fn open(path: &str) -> Result<Archive> {
    Archive::open(path, "events", &["ts", "value", "device"])
}

fn columns(lo: i64) -> Vec<Vec<i64>> {
    vec![
        (lo..lo + 100).collect(),
        (lo..lo + 100).map(|i| i * 2).collect(),
        (lo..lo + 100).map(|i| i % 97).collect(),
    ]
}

fn check_trace(trace: PublicationTrace, outer_ms: f64, prior_attempt: &mut u64) {
    assert!(trace.completed);
    assert_eq!(trace.attempt, *prior_attempt + 1);
    assert!(trace.stage_ms.iter().all(|x| x.is_finite() && *x >= 0.0));
    assert!(trace.stage_ms.iter().sum::<f64>() <= outer_ms + 0.000001);
    *prior_attempt = trace.attempt;
}

fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    let path = args.get(1).expect("pass a fresh store directory");
    let ids: i64 = args.get(2).expect("pass starting receipts").parse().unwrap();
    let repetitions: usize = args.get(3).expect("pass appends").parse().unwrap();
    assert!([0, 50_000, 99_000].contains(&ids) && repetitions == 128);
    let mut archive = open(path)?;
    assert_eq!(archive.stats()?.rows, 0, "use a fresh store");
    assert!(archive.last_publication_trace().is_none());
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
    let seed_trace = archive.last_publication_trace();
    let before = archive.stats()?;
    let mut prior_attempt = seed_trace.map_or(0, |t| t.attempt);
    let mut events = Vec::with_capacity(repetitions + 4);
    let mut reclaim = Vec::with_capacity(4);
    let mut generations = Vec::with_capacity(repetitions);
    let mut expected_sum = i128::from(ids) * i128::from(ids - 1);
    for batch in 0..repetitions {
        let lo = ids + batch as i64 * 100;
        let data = columns(lo);
        let started = Instant::now();
        let receipt = archive.append_once(&format!("new:{batch}"), data)?;
        let outer_ms = started.elapsed().as_secs_f64() * 1000.0;
        let trace = archive.last_publication_trace().unwrap();
        check_trace(trace, outer_ms, &mut prior_attempt);
        assert!(!receipt.duplicate && receipt.rows == 100);
        assert_eq!(trace.generation, receipt.generation);
        assert_eq!(trace.rows, 100);
        assert_eq!(trace.receipts_before, ids as usize + batch);
        assert_eq!(trace.new_receipts, 1);
        assert_eq!(trace.removed_segments, 0);
        assert_eq!(trace.segment_payload_bytes, 2400);
        assert_eq!(trace.receipt_base, if trace.checkpoint { None } else { Some(trace.generation - 1) });
        generations.push(receipt.generation);
        expected_sum += i128::from(2 * lo + 99) * 100;
        events.push(Observation { operation: "append", batch, outer_ms, trace });
        if archive.small_segments() >= 64 {
            let started = Instant::now();
            let removed = archive.compact_small()?;
            let outer_ms = started.elapsed().as_secs_f64() * 1000.0;
            let trace = archive.last_publication_trace().unwrap();
            check_trace(trace, outer_ms, &mut prior_attempt);
            assert_eq!(removed, 31);
            assert_eq!(trace.removed_segments, 32);
            assert_eq!(trace.new_receipts, 0);
            assert_eq!(trace.receipts_before, ids as usize + batch + 1);
            events.push(Observation { operation: "compact", batch, outer_ms, trace });
            let started = Instant::now();
            let removed_files = archive.reclaim()?;
            let outer_ms = started.elapsed().as_secs_f64() * 1000.0;
            assert_eq!(archive.last_publication_trace(), Some(trace));
            reclaim.push(ReclaimObservation { after_batch: batch, outer_ms, removed_files });
        }
    }
    assert_eq!(events.len(), 131);
    assert_eq!(reclaim.len(), 3);
    let after = archive.stats()?;
    let expected_rows = ids as u64 + repetitions as u64 * 100;
    assert_eq!(after.rows, expected_rows);
    assert_eq!(after.recorded_batch_ids, ids as usize + repetitions);
    assert_eq!(archive.query("SELECT COUNT(*), SUM(value) FROM events")?.result.rows,
        vec![vec![Value::Int(expected_rows.into()), Value::Int(expected_sum)]]);
    assert_eq!(archive.verify()?, expected_rows * 24);
    drop(archive);
    let started = Instant::now();
    let mut archive = open(path)?;
    let reopen_ms = started.elapsed().as_secs_f64() * 1000.0;
    assert!(archive.last_publication_trace().is_none());
    assert_eq!(archive.stats()?.recorded_batch_ids, ids as usize + repetitions);
    for batch in [0, repetitions / 2, repetitions - 1] {
        let receipt = archive.append_once(&format!("new:{batch}"), columns(ids + batch as i64 * 100))?;
        assert!(receipt.duplicate);
        assert_eq!(receipt.generation, generations[batch]);
        assert!(archive.last_publication_trace().is_none());
    }
    assert_eq!(archive.verify()?, expected_rows * 24);
    println!("{}", json!({
        "version": env!("CARGO_PKG_VERSION"), "probe": "KSQLTRACE068",
        "prefill_receipt_count": ids, "repetitions": repetitions,
        "stage_names": PUBLICATION_TRACE_STAGES, "seed_trace": seed_trace,
        "events": events, "reclaim": reclaim, "before": before, "after": after,
        "reopen_ms": reopen_ms, "rows_and_sum_match": true,
        "reopen_original_generations_retry_and_full_scrub_passed": true,
        "cold_trace_and_retry_remain_empty": true,
        "trace_option_bytes": std::mem::size_of::<Option<PublicationTrace>>(),
        "output_only_after_timed_calls": true, "feature_overhead_unmeasured": true,
        "performance_comparison": false,
    }));
    Ok(())
}
