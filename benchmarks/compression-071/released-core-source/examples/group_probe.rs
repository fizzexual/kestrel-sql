//! Local, single-thread query timings. JSON framing and full scrubs are untimed.
use kestrel_sql::archive::{Archive, MAX_SEGMENT_ROWS};
use serde_json::json;
use std::io::{self, BufRead, Write};
use std::time::Instant;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().collect();
    let path = args.get(1).ok_or("pass an archive directory")?;
    let schema = args.get(2).map_or("ts,value,device", String::as_str);
    let mut archive = Archive::open(path, "events", &schema.split(',').collect::<Vec<_>>())?;
    if let Some(rows) = args.get(3) {
        let rows: i64 = rows.parse()?;
        let domain: i64 = args.get(4).ok_or("pass key domain")?.parse()?;
        let step: i64 = args.get(5).ok_or("pass key spacing")?.parse()?;
        assert_eq!(schema, "ts,value,device");
        assert!((1000..=100_000_000).contains(&rows));
        assert!((1..=100_000).contains(&domain) && (1..=1_000_003).contains(&step));
        assert_eq!(archive.stats()?.rows, 0, "seed only a fresh archive");
        for lo in (0..rows).step_by(MAX_SEGMENT_ROWS) {
            let hi = (lo + MAX_SEGMENT_ROWS as i64).min(rows);
            archive.append(vec![
                (lo..hi).collect(),
                (lo..hi).map(|i| i * 37 % 1000 - 500).collect(),
                (lo..hi)
                    .map(|i| (i * 17 % domain) * step - domain / 2)
                    .collect(),
            ])?;
        }
    }
    let snapshot = archive.snapshot()?;
    let mut out = io::BufWriter::new(io::stdout().lock());
    writeln!(
        out,
        "{}",
        json!({"version": env!("CARGO_PKG_VERSION"), "stats": snapshot.stats()?})
    )?;
    out.flush()?;
    for line in io::stdin().lock().lines() {
        let request: serde_json::Value = serde_json::from_str(&line?)?;
        let response = match request["op"].as_str() {
            Some("verify") => json!({"verified_bytes": snapshot.verify()?}),
            Some("query") => {
                let sql = request["sql"].as_str().ok_or("pass SQL")?;
                let repeats = request["repeats"].as_u64().unwrap_or(11) as usize;
                assert!((1..=101).contains(&repeats));
                let profiled = request["profile"].as_bool().unwrap_or(false);
                for _ in 0..3 {
                    std::hint::black_box(snapshot.query(sql)?);
                }
                let expected = snapshot.query(sql)?;
                let mut samples = Vec::with_capacity(repeats);
                let mut profiles = Vec::new();
                for _ in 0..repeats {
                    let started = Instant::now();
                    let result = if profiled {
                        let (result, profile) = snapshot.query_profiled(sql)?;
                        let elapsed_ms = started.elapsed().as_secs_f64() * 1000.0;
                        samples.push(elapsed_ms);
                        profiles.push(profile);
                        result
                    } else {
                        let result = snapshot.query(sql)?;
                        samples.push(started.elapsed().as_secs_f64() * 1000.0);
                        result
                    };
                    assert_eq!(result.result.rows, expected.result.rows);
                    assert_eq!(result.bytes_read, expected.bytes_read);
                }
                json!({"sql": sql, "result": expected, "samples_ms": samples, "profiles": profiles})
            }
            _ => return Err("unknown probe operation".into()),
        };
        writeln!(out, "{response}")?;
        out.flush()?;
    }
    Ok(())
}
