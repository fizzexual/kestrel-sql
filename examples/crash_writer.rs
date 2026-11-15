//! Writer and checker for crash tests on a fault-injecting file system such as LazyFS
//! (see `benchmarks/lazyfs/`).
//!
//! `cargo run --release --example crash_writer -- write DIR [CHECKPOINT_BYTES]`
//! commits batches of rows forever. Row `i` is `(ts = i, value = 3 * i, device = i % 7)`, batches
//! hold 1 to 50 rows. After each commit returns it prints `ack N`, the number of rows that are now
//! acknowledged as durable. With `CHECKPOINT_BYTES` the database checkpoints automatically each
//! time the log reaches that size, so crashes also land inside checkpoints.
//!
//! `cargo run --release --example crash_writer -- check DIR ACKED`
//! opens what is left on disk and checks that it holds exactly rows `0..n` for some `n >= ACKED`:
//! nothing acknowledged is lost and nothing is half there. Prints one JSON line; exit 1 on failure.
use kestrel_sql::{Database, Value};
use serde_json::json;
use std::io::Write;

type Res<T> = Result<T, Box<dyn std::error::Error>>;

fn int(v: &Value) -> Option<i128> {
    match v {
        Value::Int(i) => Some(*i),
        _ => None,
    }
}

fn write(dir: &str, checkpoint: Option<u64>) -> Res<()> {
    let mut db = Database::open(dir)?;
    db.set_checkpoint_threshold(checkpoint);
    let exists = db.query("SELECT COUNT(*) FROM events").is_ok();
    if !exists {
        db.execute(
            "CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)",
        )?;
    }
    let mut next: i64 = match db.query("SELECT COUNT(*) FROM events")?.rows[0].first() {
        Some(v) => int(v).unwrap_or(0) as i64,
        None => 0,
    };
    let out = std::io::stdout();
    let mut out = out.lock();
    writeln!(out, "ack {next}")?;
    out.flush()?;
    let mut round: i64 = 0;
    loop {
        let batch = round % 50 + 1;
        let ts: Vec<i64> = (next..next + batch).collect();
        let value = ts.iter().map(|t| 3 * t).collect();
        let device = ts.iter().map(|t| t % 7).collect();
        db.append("events", vec![ts, value, device])?;
        next += batch;
        round += 1;
        writeln!(out, "ack {next}")?;
        out.flush()?;
    }
}

fn check(dir: &str, acked: i128) -> Res<bool> {
    let db = Database::open(dir)?;
    let (n, sum_ts, sum_value, min, max) =
        match db.query("SELECT COUNT(*), SUM(ts), SUM(value), MIN(ts), MAX(ts) FROM events") {
            Ok(r) => {
                let row = &r.rows[0];
                (
                    int(&row[0]).unwrap_or(0),
                    int(&row[1]).unwrap_or(0),
                    int(&row[2]).unwrap_or(0),
                    int(&row[3]),
                    int(&row[4]),
                )
            }
            // The table itself was never made durable: only valid if nothing was acknowledged.
            Err(_) => (0, 0, 0, None, None),
        };
    let contiguous = n == 0 && min.is_none()
        || (min == Some(0)
            && max == Some(n - 1)
            && sum_ts == n * (n - 1) / 2
            && sum_value == 3 * sum_ts);
    let ok = contiguous && n >= acked;
    let mut files: Vec<String> = std::fs::read_dir(dir)?
        .filter_map(|e| e.ok().map(|e| e.file_name().to_string_lossy().into_owned()))
        .collect();
    files.sort();
    println!(
        "{}",
        json!({"ok": ok, "rows": n.to_string(), "acked": acked.to_string(), "contiguous": contiguous,
               "recovered_tail_bytes": db.recovered_tail_bytes(), "files": files})
    );
    Ok(ok)
}

fn main() -> Res<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match args.first().map(String::as_str) {
        Some("write") if args.len() >= 2 => {
            let checkpoint = args.get(2).map(|s| s.parse()).transpose()?;
            write(&args[1], checkpoint)
        }
        Some("check") if args.len() == 3 => {
            if check(&args[1], args[2].parse()?)? {
                Ok(())
            } else {
                std::process::exit(1)
            }
        }
        _ => {
            eprintln!("usage: crash_writer write DIR [CHECKPOINT_BYTES] | check DIR ACKED");
            std::process::exit(2)
        }
    }
}
