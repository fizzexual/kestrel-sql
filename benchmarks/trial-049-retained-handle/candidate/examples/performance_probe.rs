//! Reproducible core timings; results and checks remain separate from bridge load.
use kestrel_sql::archive::{Archive, IngestBatch};
use kestrel_sql::{Result, Value};
use serde_json::json;
use std::time::Instant;

fn percentile(mut values: Vec<f64>, p: f64) -> f64 {
    values.sort_by(f64::total_cmp);
    values[(values.len() as f64 * p).ceil() as usize - 1]
}

fn main() -> Result<()> {
    let arguments: Vec<_> = std::env::args().collect();
    let path = arguments.get(1).expect("pass a fresh store directory");
    let ids: i64 = arguments.get(2).map_or(50_000, |s| s.parse().unwrap());
    let repetitions: usize = arguments.get(3).map_or(1000, |s| s.parse().unwrap());
    assert!((1..=100_000).contains(&ids) && (10..=10_000).contains(&repetitions));
    let mut archive = Archive::open(path, "events", &["ts", "value", "device"])?;
    assert_eq!(archive.stats()?.rows, 0, "use a fresh store");
    let batches = (0..ids)
        .map(|i| IngestBatch {
            id: Some(format!("probe:{i}")),
            columns: vec![vec![i], vec![i * 2], vec![i % 97]],
        })
        .collect();
    archive.append_group(batches)?;
    let generation = archive.stats()?.generation;
    let bytes_before = archive.stats()?.physical_bytes;
    let mut samples = Vec::with_capacity(repetitions);
    for i in 0..repetitions {
        let key = i as i64 * 7919 % ids;
        let started = Instant::now();
        let receipt = archive.append_once(
            &format!("probe:{key}"),
            vec![vec![key], vec![key * 2], vec![key % 97]],
        )?;
        samples.push(started.elapsed().as_secs_f64() * 1000.0);
        assert!(receipt.duplicate && receipt.generation == generation);
    }
    assert_eq!(archive.stats()?.generation, generation);
    assert_eq!(archive.stats()?.physical_bytes, bytes_before);
    assert_eq!(
        archive
            .query("SELECT COUNT(*), SUM(value) FROM events")?
            .result
            .rows,
        vec![vec![
            Value::Int(ids.into()),
            Value::Int(i128::from(ids) * i128::from(ids - 1))
        ]]
    );
    assert_eq!(archive.verify()?, ids as u64 * 24);
    println!(
        "{}",
        json!({"version":env!("CARGO_PKG_VERSION"), "probe":"identified_replay",
        "receipt_count":ids,"repetitions":repetitions,"latency_ms":{
            "p50":percentile(samples.clone(),0.5),"p95":percentile(samples.clone(),0.95),
            "p99":percentile(samples.clone(),0.99),"max":samples.iter().copied().fold(0.0,f64::max)},
        "no_new_publication":true,"rows_and_sum_match":true,"full_scrub_passed":true,
        "raw_latency_ms":samples})
    );
    Ok(())
}
