//! Profile scan stages against identical fixtures; not a service benchmark.
use kestrel_sql::archive::Archive;
use kestrel_sql::{Result, Value};
use serde_json::json;
use std::time::Instant;

fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    let path = args.get(1).expect("pass a fresh store directory");
    let rows: i64 = args.get(2).map_or(1_000_000, |s| s.parse().unwrap());
    assert!((1000..=1_000_000).contains(&rows));
    let mut archive = Archive::open(path, "events", &["ts", "value", "device"])?;
    assert_eq!(archive.stats()?.rows, 0, "use a fresh store");
    archive.append(vec![
        (0..rows).collect(),
        (0..rows).map(|i| i * 37 % 1000 - 500).collect(),
        (0..rows).map(|i| i * 17 % 97).collect(),
    ])?;
    let snapshot = archive.snapshot()?;
    let queries = [
        (
            "unordered_filter",
            "SELECT COUNT(*), SUM(value) FROM events WHERE value >= 0",
        ),
        (
            "sparse_filter",
            "SELECT COUNT(*), SUM(value), AVG(value), MIN(value), MAX(value) FROM events WHERE device = 7",
        ),
        (
            "multi_filter",
            "SELECT COUNT(*), SUM(value), SUM(device) FROM events WHERE ts >= 200317 AND ts < 700123 AND value >= 0 AND device <> 7",
        ),
        (
            "grouped",
            "SELECT device, COUNT(*), SUM(value), MIN(value), MAX(value) FROM events GROUP BY device ORDER BY device",
        ),
        (
            "filtered_group",
            "SELECT device, COUNT(*), SUM(value) FROM events WHERE value >= 0 GROUP BY device ORDER BY device",
        ),
    ];
    let mut cases = Vec::new();
    for (name, sql) in queries {
        for _ in 0..3 {
            std::hint::black_box(snapshot.query_profiled(sql)?);
        }
        // Boundary pages can become cached during warmup; compare byte counts
        // against the same warm state rather than the initial cold query.
        let normal = snapshot.query(sql)?;
        let mut samples = Vec::new();
        for _ in 0..11 {
            let started = Instant::now();
            let (result, profile) = snapshot.query_profiled(sql)?;
            let elapsed_ms = started.elapsed().as_secs_f64() * 1000.0;
            assert_eq!(result.result.rows, normal.result.rows);
            assert_eq!(result.bytes_read, normal.bytes_read);
            samples.push(json!({"elapsed_ms":elapsed_ms,"profile":profile}));
        }
        cases.push(json!({"name":name,"sql":sql,"result":normal,"samples":samples}));
    }
    assert_eq!(
        snapshot.query("SELECT COUNT(*) FROM events")?.result.rows,
        vec![vec![Value::Int(rows.into())]]
    );
    let verified_bytes = snapshot.verify()?;
    assert_eq!(verified_bytes, rows as u64 * 24);
    println!(
        "{}",
        json!({"version":env!("CARGO_PKG_VERSION"),"rows":rows,
        "verified_bytes":verified_bytes,"cases":cases,
        "methodology":"opt-in per-block timings; baseline row loop combines selection and aggregation; stage times exclude planning/index operations; three warmups and eleven samples; full scrub outside timings"})
    );
    Ok(())
}
