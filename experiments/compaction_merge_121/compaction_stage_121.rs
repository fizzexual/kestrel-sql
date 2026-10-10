//! Common component driver. All compaction reads/writes/syncs are charged.
use kestrel_sql::archive::Archive;
use kestrel_sql::{Result, Value};
use serde_json::json;
use std::time::Instant;

fn columns(name: &str, run: usize, seed: usize) -> Vec<Vec<i64>> {
    let part = (run * 13 + seed * 7) % 32;
    let keys = (0..1024).map(|row| match name {
        "ordered" => (run * 1024 + row) as i64,
        "clustered" | "extreme" => ((row / 64) * 2048 + part * 64 + row % 64) as i64,
        "interleaved" => (row * 32 + part) as i64,
        "duplicates" => ((row / 64) * 64 + row % 8) as i64,
        "late" => (part % 8 * 512 + row) as i64 - (part / 8 * 8192) as i64,
        _ => panic!("unknown declared workload"),
    }).collect();
    let values = (0..1024).map(|row| if name == "extreme" {
        [i64::MIN, -7, 0, 11, i64::MAX][row % 5]
    } else { ((run * 1024 + row) as i64 * 37) % 1000 - 500 }).collect();
    vec![keys, values, vec![run as i64 - 16; 1024]]
}

fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(args.len(), 4, "PATH WORKLOAD SEED");
    let path = &args[1]; let name = &args[2]; let seed: usize = args[3].parse().unwrap();
    assert!((1..=12).contains(&seed));
    let mut archive = Archive::open(path, "events", &["ts", "value", "device"])?;
    assert_eq!(archive.stats()?.rows, 0);
    let setup_started = Instant::now();
    let named = matches!(name.as_str(), "clustered" | "late");
    let mut receipts = Vec::new();
    let mut expected_sum = 0_i128;
    for run in 0..32 {
        let data = columns(name, run, seed);
        expected_sum += data[1].iter().map(|&value| i128::from(value)).sum::<i128>();
        if named {
            let id = format!("merge121:{run}");
            let receipt = archive.append_once(&id, data)?;
            receipts.push((id, run, receipt.generation));
        } else { archive.append(data)?; }
    }
    let setup_ns = setup_started.elapsed().as_nanos();
    let before = archive.stats()?;
    let pin = archive.snapshot()?;
    let started = Instant::now();
    let reduced = archive.compact_small()?;
    let compaction_ns = started.elapsed().as_nanos();
    let after = archive.stats()?;
    assert_eq!(reduced, 31);
    assert_eq!(after.rows, 32768);
    assert_eq!(after.generation, before.generation + 1);
    assert_eq!(pin.stats()?.generation, before.generation);
    let expected = vec![vec![Value::Int(32768), Value::Int(expected_sum)]];
    let sql = "SELECT COUNT(*), SUM(value) FROM events";
    assert_eq!(archive.query(sql)?.result.rows, expected);
    assert_eq!(pin.query(sql)?.result.rows, expected);
    assert_eq!(pin.verify()?, 32768 * 24);
    assert_eq!(archive.verify()?, 32768 * 24);
    archive.reclaim()?;
    assert_eq!(pin.query(sql)?.result.rows, expected);
    drop(pin); archive.reclaim()?; drop(archive);
    let mut reopened = Archive::open(path, "events", &["ts", "value", "device"])?;
    assert_eq!(reopened.query(sql)?.result.rows, expected);
    for (id, run, generation) in &receipts {
        let receipt = reopened.append_once(id, columns(name, *run, seed))?;
        assert!(receipt.duplicate && receipt.generation == *generation);
    }
    assert_eq!(reopened.verify()?, 32768 * 24);
    println!("{}", json!({"version":env!("CARGO_PKG_VERSION"),"workload":name,"seed":seed,"setup_ns":setup_ns,"compaction_ns":compaction_ns,"before":before,"after":after,"receipts":receipts,"reduced":reduced,"cold_rows":reopened.stats()?.rows,"full_crc_bytes":32768*24,"all_checks_passed":true,"component_only":true}));
    Ok(())
}
