//! In-memory diagnostic only. This does not measure durable Archive compaction.
use std::ffi::c_void;
use std::hint::black_box;
use std::ops::Range;
use std::time::Instant;

const BLOCK_ROWS: usize = 4096;
#[path = "merge_runs_122.rs"]
mod merge_runs_122;

#[link(name = "kernel32")]
unsafe extern "system" {
    fn GetCurrentThread() -> *mut c_void;
    fn QueryThreadCycleTime(thread: *mut c_void, cycles: *mut u64) -> i32;
}

fn thread_cycles() -> u64 {
    let mut cycles = 0;
    // The pseudo-handle belongs to this running thread; the output is valid
    // writable storage. No other process or thread is opened or modified.
    assert_ne!(unsafe { QueryThreadCycleTime(GetCurrentThread(), &mut cycles) }, 0);
    cycles
}

fn supported_publish_layout(columns: &mut [Vec<i64>]) {
    let rows = columns[0].len();
    if !columns[0].windows(2).all(|pair| pair[0] <= pair[1]) {
        let mut order: Vec<usize> = (0..rows).collect();
        order.sort_unstable_by_key(|index| columns[0][*index]);
        for column in columns {
            *column = order.iter().map(|index| column[*index]).collect();
        }
    }
}

fn input(name: &str, seed: usize) -> (Vec<Vec<i64>>, Vec<Range<usize>>) {
    assert!((1..=12).contains(&seed));
    let mut all = vec![Vec::with_capacity(32768); 3];
    let mut spans = Vec::new();
    for run in 0..32 {
        let part = (run * 13 + seed * 7) % 32;
        let keys: Vec<_> = (0..1024).map(|row| match name {
            "ordered" => (run * 1024 + row) as i64,
            "clustered" | "extreme" => ((row / 64) * 2048 + part * 64 + row % 64) as i64,
            "interleaved" => (row * 32 + part) as i64,
            "duplicates" => ((row / 64) * 64 + row % 8) as i64,
            "late" => (part % 8 * 512 + row) as i64 - (part / 8 * 8192) as i64,
            _ => panic!("undeclared workload"),
        }).collect();
        let values = (0..1024).map(|row| if name == "extreme" {
            [i64::MIN, -7, 0, 11, i64::MAX][row % 5]
        } else { ((run * 1024 + row) as i64 * 37) % 1000 - 500 }).collect();
        let mut columns = vec![keys, values, vec![run as i64 - 16; 1024]];
        // Archive.append sorts each input run before compaction can read it.
        // This prerequisite matters for the duplicate shape's internal ties.
        supported_publish_layout(&mut columns);
        let start = all[0].len();
        for (destination, column) in all.iter_mut().zip(columns) {
            destination.extend(column);
        }
        spans.push(start..all[0].len());
    }
    (all, spans)
}

fn canonical(columns: &[Vec<i64>]) -> Vec<(i64, i64, i64)> {
    assert_eq!(columns.len(), 3);
    assert!(columns.iter().all(|column| column.len() == 32768));
    let mut rows: Vec<_> = (0..32768).map(|row| (columns[0][row], columns[1][row], columns[2][row])).collect();
    rows.sort_unstable();
    rows
}

fn fingerprint(rows: &[(i64, i64, i64)]) -> u64 {
    let mut result = 14695981039346656037_u64;
    for &(key, value, device) in rows {
        for item in [key, value, device] {
            result ^= item as u64;
            result = result.wrapping_mul(1099511628211);
        }
    }
    result
}

fn main() {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(args.len(), 4, "WORKLOAD SEED baseline|candidate");
    let name = &args[1];
    let seed: usize = args[2].parse().unwrap();
    let candidate = match args[3].as_str() {
        "baseline" => false,
        "candidate" => true,
        _ => panic!("unknown variant"),
    };
    let (fixture, spans) = input(name, seed);
    let expected = canonical(&fixture);
    let expected_sum: i128 = fixture[1].iter().map(|&value| i128::from(value)).sum();
    let mut wall_ns = Vec::new();
    let mut cycles = Vec::new();
    let mut arranged_count = 0;
    for _ in 0..32 {
        let mut columns = black_box(fixture.clone());
        let before_cycles = thread_cycles();
        let started = Instant::now();
        let arranged = candidate && merge_runs_122::arrange(&mut columns, &spans);
        // Keep the supported final independent monotonic check/sort/gather.
        supported_publish_layout(&mut columns);
        let elapsed_ns = started.elapsed().as_nanos();
        let after_cycles = thread_cycles();
        assert!(elapsed_ns > 0 && after_cycles > before_cycles);
        wall_ns.push(elapsed_ns);
        cycles.push(after_cycles - before_cycles);
        arranged_count += usize::from(arranged);
        assert!(columns[0].windows(2).all(|pair| pair[0] <= pair[1]));
        assert_eq!(canonical(black_box(&columns)), expected);
        assert_eq!(columns[1].iter().map(|&value| i128::from(value)).sum::<i128>(), expected_sum);
    }
    println!("{{\"trial\":126,\"diagnostic_only\":true,\"workload\":\"{name}\",\"seed\":{seed},\"candidate\":{candidate},\"iterations\":32,\"rows_per_iteration\":32768,\"full_native_multiset_checks\":32,\"sortedness_checks\":32,\"canonical_fingerprint\":{},\"value_sum_i128\":{expected_sum},\"arranged_iterations\":{arranged_count},\"wall_ns\":{wall_ns:?},\"thread_cycles\":{cycles:?},\"all_checks_passed\":true}}", fingerprint(&expected));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn both_layouts_preserve_exact_rows_for_all_shapes_and_valid_seeds() {
        for name in ["ordered", "clustered", "interleaved", "duplicates", "late", "extreme"] {
            for seed in 1..=12 {
                let (input, spans) = input(name, seed);
                let expected = canonical(&input);
                for candidate in [false, true] {
                    let mut columns = input.clone();
                    if candidate { merge_runs_122::arrange(&mut columns, &spans); }
                    supported_publish_layout(&mut columns);
                    assert!(columns[0].windows(2).all(|pair| pair[0] <= pair[1]));
                    assert_eq!(canonical(&columns), expected, "{name}, seed={seed}, candidate={candidate}");
                }
            }
        }
    }
}
