//! CPU-only comparison: identical SHA-256 byte domain, bounded LE staging.
use serde_json::json;
use sha2::{Digest, Sha256};
use std::hint::black_box;
use std::time::{Duration, Instant};

fn original(columns: &[Vec<i64>]) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update((columns.len() as u64).to_le_bytes());
    digest.update((columns[0].len() as u64).to_le_bytes());
    for column in columns {
        for value in column {
            digest.update(value.to_le_bytes());
        }
    }
    digest.finalize().into()
}

fn chunked<const BYTES: usize>(columns: &[Vec<i64>]) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update((columns.len() as u64).to_le_bytes());
    digest.update((columns[0].len() as u64).to_le_bytes());
    let mut bytes = [0u8; BYTES];
    for column in columns {
        for values in column.chunks(BYTES / 8) {
            for (value, destination) in values.iter().zip(bytes.chunks_exact_mut(8)) {
                destination.copy_from_slice(&value.to_le_bytes());
            }
            digest.update(&bytes[..values.len() * 8]);
        }
    }
    digest.finalize().into()
}

fn main() {
    let mut cases = Vec::new();
    for round in 0..5 {
        for (width, rows) in [(3, 1), (3, 100), (3, 10_000), (64, 100), (1, 131_073)] {
            let columns: Vec<Vec<i64>> = (0..width)
                .map(|col| (0..rows).map(|row| (row as i64).wrapping_mul(-1_234_567) ^ col as i64).collect())
                .collect();
            let expected = original(&columns);
            assert_eq!(expected, chunked::<512>(&columns));
            assert_eq!(expected, chunked::<4096>(&columns));
            let variants: [(&str, fn(&[Vec<i64>]) -> [u8; 32]); 3] = [
                ("original", original), ("chunk512", chunked::<512>), ("chunk4096", chunked::<4096>)];
            for index in 0..3 {
                let (name, function) = variants[(index + round) % 3];
                for _ in 0..8 { black_box(function(black_box(&columns))); }
                let started = Instant::now();
                let mut calls = 0;
                loop {
                    for _ in 0..16 {
                        black_box(function(black_box(&columns)));
                    }
                    calls += 16;
                    if started.elapsed() >= Duration::from_millis(300) { break; }
                }
                let elapsed_ns = started.elapsed().as_nanos() as u64;
                cases.push(json!({"round": round, "width": width, "rows": rows, "variant": name,
                    "calls": calls, "elapsed_ns": elapsed_ns, "ns_per_digest": elapsed_ns as f64 / calls as f64,
                    "sha256": expected}));
            }
        }
    }
    println!("{}", json!({"all_domains_equal": true, "cases": cases}));
}
