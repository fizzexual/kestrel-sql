//! Bounded compaction preparation; durable publication remains in Archive.
use super::BLOCK_ROWS;
use std::cmp::Reverse;
use std::collections::BinaryHeap;
use std::ops::Range;

fn plan(keys: &[i64], runs: &[Range<usize>]) -> Option<Vec<Range<usize>>> {
    if keys.len() < BLOCK_ROWS || runs.len() < 2 {
        return None;
    }
    // Every selected immutable run is already sorted. Leave ordered concatenation
    // alone; publish retains its independent final monotonicity check.
    if runs.windows(2).all(|pair| keys[pair[0].end - 1] <= keys[pair[1].start]) {
        return None;
    }
    let limit = keys.len() / 64 + runs.len();
    let mut heap = BinaryHeap::with_capacity(runs.len());
    for (run, span) in runs.iter().enumerate() {
        heap.push(Reverse((keys[span.start], run, span.start)));
    }
    let mut slices = Vec::with_capacity(runs.len());
    let mut consumed = 0;
    while let Some(Reverse((_, run, start))) = heap.pop() {
        if slices.len() == limit {
            return None; // Highly interleaved keys keep the original sort.
        }
        let end = if let Some(&Reverse((next_key, next_run, _))) = heap.peek() {
            start + keys[start..runs[run].end].partition_point(|&key| {
                key < next_key || (key == next_key && run < next_run)
            })
        } else {
            runs[run].end
        };
        if end <= start {
            return None; // Nonpartitioned malformed input retains publish fallback.
        }
        slices.push(start..end);
        consumed += end - start;
        if slices.len() == runs.len() && consumed < slices.len() * 64 {
            return None; // Reject fragmented planning after one slice per run.
        }
        if end < runs[run].end {
            heap.push(Reverse((keys[end], run, end)));
        }
    }
    Some(slices)
}

pub(super) fn arrange(columns: &mut [Vec<i64>], runs: &[Range<usize>]) -> bool {
    let Some(slices) = plan(&columns[0], runs) else {
        return false;
    };
    for column in columns {
        let mut output = Vec::with_capacity(column.len());
        for span in &slices {
            output.extend_from_slice(&column[span.clone()]);
        }
        debug_assert_eq!(output.len(), column.len());
        *column = output;
    }
    true
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn chunked_merge_matches_independent_stable_sort_with_signed_keys_and_ties() {
        for width in [1, 3, 64] {
            let mut columns = vec![Vec::new(); width];
            let mut runs = Vec::new();
            for run in 0..8 {
                let start = columns[0].len();
                for row in 0..1024 {
                    // Four tied run pairs, in reverse interval order.
                    let key = (7 - run) / 2 * 2048 + row / 64;
                    columns[0].push(key as i64 - 8192);
                    for (column, values) in columns.iter_mut().enumerate().skip(1) {
                        values.push(if column.is_multiple_of(2) { i64::MAX } else { i64::MIN + (run * 1024 + row) as i64 });
                    }
                }
                runs.push(start..columns[0].len());
            }
            let mut order: Vec<_> = (0..columns[0].len()).collect();
            order.sort_by_key(|&row| columns[0][row]);
            let expected: Vec<Vec<i64>> = columns.iter().map(|column| order.iter().map(|&row| column[row]).collect()).collect();
            assert!(arrange(&mut columns, &runs));
            assert_eq!(columns, expected);
        }
    }

    #[test]
    fn ordered_small_and_highly_interleaved_fallbacks_leave_every_byte_unchanged() {
        for rows in [4095, 4096, 8192] {
            let ordered: Vec<_> = (0..rows).map(|value| value as i64).collect();
            let spans = [0..rows/2, rows/2..rows];
            let mut columns = vec![ordered.clone(), vec![i64::MIN; rows]];
            let original = columns.clone();
            assert!(!arrange(&mut columns, &spans));
            assert_eq!(columns, original);
            let keys: Vec<_> = (0..rows/2).map(|value| (value * 2 + 1) as i64).chain((0..rows-rows/2).map(|value| (value * 2) as i64)).collect();
            let mut columns = vec![keys, ordered];
            let original = columns.clone();
            assert!(!arrange(&mut columns, &spans));
            assert_eq!(columns, original);
        }
    }

    #[test]
    fn fragmented_overlap_falls_back_without_changing_any_column() {
        let mut columns = vec![Vec::new(), Vec::new()];
        let mut runs = Vec::new();
        for run in 0..32 {
            let start = columns[0].len();
            columns[0].extend((0..1024).map(|row| (run * 512 + row) as i64));
            columns[1].extend((0..1024).map(|row| (run * 1024 + row) as i64));
            runs.push(start..columns[0].len());
        }
        let original = columns.clone();
        assert!(!arrange(&mut columns, &runs));
        assert_eq!(columns, original);
    }

    #[test]
    fn malformed_nonpartitioned_keys_never_lose_rows_or_pairing() {
        for seed in 1..=16_u64 {
            let mut state = seed;
            let keys: Vec<_> = (0..4096).map(|_| {
                state ^= state << 13;
                state ^= state >> 7;
                state ^= state << 17;
                state as i64
            }).collect();
            let mut expected: Vec<_> = keys.iter().copied().zip(0..4096_i64).collect();
            expected.sort_unstable();
            let mut columns = vec![keys, (0..4096_i64).collect()];
            let ranges = [0..1024, 1024..2048, 2048..3072, 3072..4096];
            arrange(&mut columns, &ranges);
            let mut actual: Vec<_> = columns[0].iter().copied().zip(columns[1].iter().copied()).collect();
            actual.sort_unstable();
            assert_eq!(actual, expected);
        }
    }
}
