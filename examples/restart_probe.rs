//! Restart time of a durable `Database`: replaying the whole log versus reading a checkpoint.
//!
//! `cargo run --release --example restart_probe -- EMPTY_DIRECTORY [ROWS] [BATCH_ROWS] [REPEATS] [synthetic]`
//!
//! With `synthetic` the log is written directly, frame by frame, exactly as that many autocommit
//! appends would write it, but without one fsync per commit, so a log of a million small commits
//! takes seconds to build. The probe first checks that a small synthetic log is byte-identical to
//! one written through `Database`.
use kestrel_sql::Database;
use serde_json::json;
use std::io::Write;
use std::time::Instant;

type Res<T> = Result<T, Box<dyn std::error::Error>>;

fn median(mut samples: Vec<f64>) -> f64 {
    samples.sort_by(f64::total_cmp);
    samples[samples.len() / 2]
}

fn reopen(dir: &str, repeats: usize) -> Res<(f64, Vec<f64>)> {
    let mut samples = Vec::new();
    for _ in 0..repeats {
        let start = Instant::now();
        let db = Database::open(dir)?;
        samples.push(start.elapsed().as_secs_f64() * 1000.0);
        std::hint::black_box(db.query("SELECT COUNT(*) AS n FROM events")?);
    }
    Ok((median(samples.clone()), samples))
}

fn size(dir: &str) -> Res<u64> {
    let mut total = 0;
    for entry in std::fs::read_dir(dir)? {
        total += entry?.metadata()?.len();
    }
    Ok(total)
}

fn columns(lo: usize, hi: usize) -> Vec<Vec<i64>> {
    vec![
        (lo as i64..hi as i64).collect(),
        (lo as i64..hi as i64)
            .map(|i| (i * 37) % 1000 - 500)
            .collect(),
        (lo as i64..hi as i64).map(|i| (i * 17) % 97).collect(),
    ]
}

fn frame(out: &mut impl Write, payload: &str) -> std::io::Result<()> {
    let size = payload.len() as u32;
    out.write_all(b"KTX1")?;
    out.write_all(&size.to_le_bytes())?;
    out.write_all(&(!size).to_le_bytes())?;
    out.write_all(&crc32fast::hash(payload.as_bytes()).to_le_bytes())?;
    out.write_all(payload.as_bytes())
}

fn synthesize(dir: &str, rows: usize, batch: usize) -> Res<()> {
    std::fs::create_dir_all(dir)?;
    let file = std::fs::File::create(std::path::Path::new(dir).join("events.ksql"))?;
    let mut out = std::io::BufWriter::with_capacity(1 << 20, file);
    out.write_all(b"KestrelSQL-WAL\0\x01")?;
    frame(
        &mut out,
        r#"[{"Create":{"table":"events","columns":["ts","value","device"]}}]"#,
    )?;
    for lo in (0..rows).step_by(batch) {
        let c = columns(lo, (lo + batch).min(rows));
        frame(
            &mut out,
            &format!(
                r#"[{{"Append":{{"table":"events","columns":{}}}}}]"#,
                serde_json::to_string(&c)?
            ),
        )?;
    }
    out.into_inner()?.sync_all()?;
    Ok(())
}

fn real(dir: &str, rows: usize, batch: usize) -> Res<()> {
    let mut db = Database::open(dir)?;
    db.set_checkpoint_threshold(None);
    db.execute(
        "CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)",
    )?;
    for lo in (0..rows).step_by(batch) {
        db.append("events", columns(lo, (lo + batch).min(rows)))?;
    }
    Ok(())
}

fn main() -> Res<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let dir = args
        .first()
        .ok_or("usage: restart_probe EMPTY_DIRECTORY [ROWS] [BATCH] [REPEATS] [synthetic]")?;
    let rows: usize = args.get(1).map_or(Ok(10_000_000), |v| v.parse())?;
    let batch: usize = args.get(2).map_or(Ok(10_000), |v| v.parse())?;
    let repeats: usize = args.get(3).map_or(Ok(5), |v| v.parse())?;
    let synthetic = args.get(4).is_some_and(|v| v == "synthetic");
    if std::fs::read_dir(dir).is_ok_and(|mut d| d.next().is_some()) {
        return Err("the directory must be empty or absent".into());
    }
    let start = Instant::now();
    if synthetic {
        let a = format!("{dir}-check-real");
        let b = format!("{dir}-check-synthetic");
        real(&a, batch * 3 + 1, batch)?;
        synthesize(&b, batch * 3 + 1, batch)?;
        let same = std::fs::read(format!("{a}/events.ksql"))?
            == std::fs::read(format!("{b}/events.ksql"))?;
        std::fs::remove_dir_all(&a)?;
        std::fs::remove_dir_all(&b)?;
        if !same {
            return Err("the synthetic log differs from a real one".into());
        }
        synthesize(dir, rows, batch)?;
    } else {
        real(dir, rows, batch)?;
    }
    let load_ms = start.elapsed().as_secs_f64() * 1000.0;
    let log_bytes = size(dir)?;
    let (log_ms, log_samples) = reopen(dir, repeats)?;
    let mut db = Database::open(dir)?;
    let start = Instant::now();
    let info = db.checkpoint()?;
    let checkpoint_ms = start.elapsed().as_secs_f64() * 1000.0;
    drop(db);
    let snapshot_bytes = size(dir)?;
    let (snapshot_ms, snapshot_samples) = reopen(dir, repeats)?;
    println!(
        "{}",
        json!({"rows": rows, "batch_rows": batch, "commits": rows.div_ceil(batch),
            "synthetic_log": synthetic, "load_ms": load_ms,
            "log_only": {"disk_bytes": log_bytes, "reopen_median_ms": log_ms, "samples_ms": log_samples},
            "checkpoint_ms": checkpoint_ms, "generation": info.generation,
            "after_checkpoint": {"disk_bytes": snapshot_bytes, "reopen_median_ms": snapshot_ms, "samples_ms": snapshot_samples},
            "version": env!("CARGO_PKG_VERSION")})
    );
    Ok(())
}
