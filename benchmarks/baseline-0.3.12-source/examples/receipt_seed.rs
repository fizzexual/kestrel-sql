//! Fresh benchmark fixture with the standard row formula and retained retry IDs.
use kestrel_sql::Result;
use kestrel_sql::archive::{Archive, IngestBatch};
use serde_json::json;

fn main() -> Result<()> {
    let arguments: Vec<_> = std::env::args().collect();
    let path = arguments.get(1).expect("fresh archive directory");
    let ids: usize = arguments.get(2).expect("receipt count").parse().unwrap();
    let rows: usize = arguments.get(3).expect("row count").parse().unwrap();
    assert!((1..=99_000).contains(&ids) && (ids..=1_000_000).contains(&rows));
    let mut archive = Archive::open(path, "events", &["ts", "value", "device"])?;
    assert_eq!(archive.stats()?.rows, 0);
    archive.append_group(
        (0..ids)
            .map(|i| {
                let lo = (i * rows / ids) as i64;
                let hi = ((i + 1) * rows / ids) as i64;
                IngestBatch {
                    id: Some(format!("seed:{i}")),
                    columns: vec![
                        (lo..hi).collect(),
                        (lo..hi).map(|r| (r * 37) % 1000 - 500).collect(),
                        (lo..hi).map(|r| (r * 17) % 97).collect(),
                    ],
                }
            })
            .collect(),
    )?;
    assert_eq!(archive.verify()?, rows as u64 * 24);
    let stats = archive.stats()?;
    assert_eq!(stats.recorded_batch_ids, ids);
    println!(
        "{}",
        json!({"version":env!("CARGO_PKG_VERSION"),"rows":rows,"receipt_count":ids,"full_scrub_passed":true})
    );
    Ok(())
}
