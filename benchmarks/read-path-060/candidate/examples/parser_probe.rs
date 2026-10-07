//! Parser-only batches, including lexing, AST construction and destruction.
//! This diagnostic is excluded from the engine and the network service.
use kestrel_sql::sql;
use serde_json::json;
use std::io::{self, BufRead, Write};
use std::time::Instant;

fn batch(text: &str, iterations: usize) -> kestrel_sql::Result<()> {
    for _ in 0..iterations {
        std::hint::black_box(sql::parse(std::hint::black_box(text))?);
    }
    Ok(())
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut out = io::BufWriter::new(io::stdout().lock());
    writeln!(out, "{}", json!({"version": env!("CARGO_PKG_VERSION")}))?;
    out.flush()?;
    for line in io::stdin().lock().lines() {
        let request: serde_json::Value = serde_json::from_str(&line?)?;
        let text = request["sql"].as_str().ok_or("pass SQL")?;
        let iterations = request["iterations"].as_u64().unwrap_or(1000) as usize;
        let repeats = request["repeats"].as_u64().unwrap_or(101) as usize;
        assert!((1..=10_000).contains(&iterations) && (1..=101).contains(&repeats));
        let ast = format!("{:?}", sql::parse(text)?);
        for _ in 0..3 {
            batch(text, iterations)?;
        }
        let mut elapsed_batch_ms = Vec::with_capacity(repeats);
        for _ in 0..repeats {
            let started = Instant::now();
            batch(text, iterations)?;
            elapsed_batch_ms.push(started.elapsed().as_secs_f64() * 1000.0);
        }
        writeln!(out, "{}", json!({"sql": text, "ast": ast, "iterations": iterations,
                                  "elapsed_batch_ms": elapsed_batch_ms}))?;
        out.flush()?;
    }
    Ok(())
}
