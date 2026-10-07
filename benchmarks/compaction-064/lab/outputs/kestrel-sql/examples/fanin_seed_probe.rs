use kestrel_sql::archive::Archive;
use kestrel_sql::{Result, Value};

fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    let path = args.get(1).expect("store path");
    let mode = args.get(2).expect("seed or check");
    let mut archive = Archive::open(path, "events", &["ts", "value", "device"])?;
    if mode == "seed" {
        assert_eq!(archive.stats()?.rows, 0);
    } else {
        assert_eq!(mode, "check");
    }
    for batch in 0..64_i64 {
        let lo = batch * 100;
        let receipt = archive.append_once(
            &format!("fanin64:{batch}"),
            vec![
                (lo..lo + 100).collect(),
                (lo..lo + 100).map(|i| i * 2).collect(),
                vec![batch; 100],
            ],
        )?;
        assert_eq!(receipt.duplicate, mode == "check");
        assert_eq!(receipt.generation, (batch + 1) as u64);
    }
    assert_eq!(
        archive
            .query("SELECT COUNT(*), SUM(value) FROM events")?
            .result
            .rows,
        vec![vec![Value::Int(6400), Value::Int(6400 * 6399)]]
    );
    let stats = archive.stats()?;
    assert_eq!(
        stats.generation,
        args.get(3).map_or(64, |v| v.parse().unwrap())
    );
    assert_eq!(stats.segments, if stats.generation == 64 { 64 } else { 1 });
    assert_eq!(archive.verify()?, 6400 * 24);
    println!(
        "{}",
        serde_json::json!({"version":env!("CARGO_PKG_VERSION"),"mode":mode,"rows":stats.rows,"segments":stats.segments,"generation":stats.generation,"original_receipts_rows_sum_and_crc_passed":true})
    );
    Ok(())
}
