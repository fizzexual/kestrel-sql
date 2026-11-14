//! Index-only diagnostic; no Archive I/O, durability or whole-engine claim.
use serde::Serialize;
use serde_json::json;
use sha2::{Digest, Sha256};
use std::hint::black_box;
use std::time::Instant;

const BLOCK_ROWS: usize = 4096;
const REPETITIONS: usize = 16;

#[derive(Debug, PartialEq, Eq, Serialize)]
struct Index {
    prefix: Vec<i128>,
    last: Vec<i64>,
    crc: Vec<u32>,
    block_min: Vec<i64>,
    block_max: Vec<i64>,
    min: i64,
    max: i64,
    monotonic: bool,
}

fn legacy(columns: &[Vec<i64>]) -> Vec<Index> {
            let mut indexes = Vec::new();
        for column in columns {
            let mut prefix = vec![0_i128];
            let mut last = Vec::new();
            let mut crc = Vec::new();
            let mut block_min = Vec::new();
            let mut block_max = Vec::new();
            for block in column.chunks(BLOCK_ROWS) {
                prefix.push(
                    prefix.last().copied().unwrap()
                        + block.iter().map(|x| i128::from(*x)).sum::<i128>(),
                );
                last.push(*block.last().unwrap());
                let bytes: Vec<_> = block.iter().flat_map(|x| x.to_le_bytes()).collect();
                crc.push(crc32fast::hash(&bytes));
                block_min.push(*block.iter().min().unwrap());
                block_max.push(*block.iter().max().unwrap());
            }
            indexes.push(Index {
                prefix,
                last,
                crc,
                block_min,
                block_max,
                min: *column.iter().min().unwrap(),
                max: *column.iter().max().unwrap(),
                monotonic: column.windows(2).all(|x| x[0] <= x[1]),
            });
        }
        indexes

}

fn reuse_extrema(columns: &[Vec<i64>]) -> Vec<Index> {
            let mut indexes = Vec::new();
        for column in columns {
            let mut prefix = vec![0_i128];
            let mut last = Vec::new();
            let mut crc = Vec::new();
            let mut block_min = Vec::new();
            let mut block_max = Vec::new();
            for block in column.chunks(BLOCK_ROWS) {
                prefix.push(
                    prefix.last().copied().unwrap()
                        + block.iter().map(|x| i128::from(*x)).sum::<i128>(),
                );
                last.push(*block.last().unwrap());
                let bytes: Vec<_> = block.iter().flat_map(|x| x.to_le_bytes()).collect();
                crc.push(crc32fast::hash(&bytes));
                block_min.push(*block.iter().min().unwrap());
                block_max.push(*block.iter().max().unwrap());
            }
            let low = *block_min.iter().min().unwrap();
            let high = *block_max.iter().max().unwrap();
            indexes.push(Index {
                prefix,
                last,
                crc,
                block_min,
                block_max,
                min: low,
                max: high,
                monotonic: column.windows(2).all(|x| x[0] <= x[1]),
            });
        }
        indexes

}

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



#[derive(Default, Serialize)]
struct Stages {
    sum_ns: u128,
    serialize_ns: u128,
    crc_ns: u128,
    block_extrema_ns: u128,
    global_extrema_ns: u128,
    monotonic_ns: u128,
    total_ns: u128,
}

// This separate diagnostic build is outside the primary kernel timer. Its
// per-stage Instant overhead is disclosed and no exclusive cause is inferred.
fn profile_legacy(columns: &[Vec<i64>]) -> (Vec<Index>, Stages) {
    let overall = Instant::now();
    let mut stages = Stages::default();
    let mut indexes = Vec::new();
    for column in columns {
        let mut prefix = vec![0_i128];
        let mut last = Vec::new();
        let mut crc = Vec::new();
        let mut block_min = Vec::new();
        let mut block_max = Vec::new();
        for block in column.chunks(BLOCK_ROWS) {
            let started = Instant::now();
            prefix.push(prefix.last().copied().unwrap() + block.iter().map(|x| i128::from(*x)).sum::<i128>());
            stages.sum_ns += started.elapsed().as_nanos();
            last.push(*block.last().unwrap());
            let started = Instant::now();
            let bytes: Vec<_> = block.iter().flat_map(|x| x.to_le_bytes()).collect();
            stages.serialize_ns += started.elapsed().as_nanos();
            let started = Instant::now();
            crc.push(crc32fast::hash(&bytes));
            stages.crc_ns += started.elapsed().as_nanos();
            let started = Instant::now();
            block_min.push(*block.iter().min().unwrap());
            block_max.push(*block.iter().max().unwrap());
            stages.block_extrema_ns += started.elapsed().as_nanos();
        }
        let started = Instant::now();
        let min = *column.iter().min().unwrap();
        let max = *column.iter().max().unwrap();
        stages.global_extrema_ns += started.elapsed().as_nanos();
        let started = Instant::now();
        let monotonic = column.windows(2).all(|x| x[0] <= x[1]);
        stages.monotonic_ns += started.elapsed().as_nanos();
        indexes.push(Index { prefix, last, crc, block_min, block_max, min, max, monotonic });
    }
    stages.total_ns = overall.elapsed().as_nanos();
    (indexes, stages)
}

fn digest(columns: &[Vec<i64>]) -> String {
    let mut hash = Sha256::new();
    hash.update((columns.len() as u64).to_le_bytes());
    hash.update((columns[0].len() as u64).to_le_bytes());
    for column in columns {
        for value in column { hash.update(value.to_le_bytes()); }
    }
    format!("{:x}", hash.finalize())
}

fn main() {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(args.len(), 4, "WORKLOAD SEED VARIANT");
    let shape = &args[1];
    let seed: usize = args[2].parse().unwrap();
    assert!((1..=12).contains(&seed));
    assert!(matches!(args[3].as_str(), "baseline_a" | "baseline_b" | "candidate"));
    let mut input = vec![Vec::new(); 3];
    for run in 0..32 {
        for (to, from) in input.iter_mut().zip(columns(shape, run, seed)) { to.extend(from); }
    }
    // Deterministic stable input layout. This preparation and its allocation/
    // sorting/hash are excluded from this index-only timer, unlike Archive.
    let mut order: Vec<_> = (0..input[0].len()).collect();
    order.sort_by_key(|&row| input[0][row]);
    let input: Vec<Vec<i64>> = input.iter().map(|column| order.iter().map(|&row| column[row]).collect()).collect();
    let input_sha256 = digest(&input);
    let oracle = legacy(&input);
    assert_eq!(oracle, reuse_extrema(&input));
    let build: fn(&[Vec<i64>]) -> Vec<Index> = if args[3] == "candidate" { reuse_extrema } else { legacy };
    let mut result = Vec::new();
    let started = Instant::now();
    for _ in 0..REPETITIONS {
        result = black_box(black_box(build)(black_box(&input)));
    }
    let elapsed_ns = started.elapsed().as_nanos();
    assert_eq!(result, oracle);
    let (profiled, stages) = profile_legacy(&input);
    assert_eq!(profiled, oracle);
    println!("{}", json!({"trial":142,"workload":shape,"seed":seed,"variant":args[3],
        "rows":32768,"columns":3,"repetitions":REPETITIONS,"elapsed_ns":elapsed_ns,
        "input_sha256":input_sha256,"indexes":result,"legacy_profile":stages,
        "all_checks_passed":true,"index_kernel_only":true,"archive_IO_sync_ACK_excluded":true,
        "input_generation_sort_sha_excluded":true,"profile_outside_primary_timer":true}));
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn extrema_reuse_matches_legacy_at_block_boundaries_and_wide_prefixes() {
        for rows in [1, 4095, 4096, 4097, 8193, 32768] {
            let values = vec![(0..rows).map(|r| r as i64 - 30000).collect(),
                (0..rows).map(|r| [i64::MIN, -13, 0, 7, i64::MAX][r % 5]).collect(),
                vec![i64::MAX; rows]];
            assert_eq!(legacy(&values), reuse_extrema(&values));
            assert_eq!(profile_legacy(&values).0, legacy(&values));
        }
    }
    #[test]
    fn all_six_shapes_and_seeds_preserve_every_index_field() {
        for shape in ["ordered", "clustered", "interleaved", "duplicates", "late", "extreme"] {
            for seed in 1..=12 {
                let values = columns(shape, seed, seed);
                assert_eq!(legacy(&values), reuse_extrema(&values));
                assert_eq!(profile_legacy(&values).0, legacy(&values));
            }
        }
    }
}
