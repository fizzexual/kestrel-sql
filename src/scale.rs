use kestrel_sql::archive::{Archive, MAX_SEGMENT_ROWS};
use serde_json::json;
use std::io::{BufReader, Read};
use std::path::Path;
use std::time::Instant;

pub fn import_i64(
    store: &mut Archive,
    path: &Path,
    width: usize,
) -> Result<(), Box<dyn std::error::Error>> {
    let file = std::fs::File::open(path)?;
    let bytes = file.metadata()?.len();
    if !bytes.is_multiple_of(width as u64 * 8) {
        return Err("binary input ends in a partial row".into());
    }
    let mut file = BufReader::new(file);
    let mut left = bytes / (width as u64 * 8);
    let started = Instant::now();
    let mut rows = 0;
    while left > 0 {
        let n = left
            .min(MAX_SEGMENT_ROWS as u64)
            .min((64 * 1024 * 1024 / (width * 8)) as u64) as usize;
        let mut raw = vec![0; n * width * 8];
        file.read_exact(&mut raw)?;
        let mut columns = vec![Vec::with_capacity(n); width];
        for row in raw.chunks_exact(width * 8) {
            for (c, value) in columns.iter_mut().zip(row.as_chunks::<8>().0) {
                c.push(i64::from_le_bytes(*value));
            }
        }
        drop(raw);
        store.append(columns)?;
        left -= n as u64;
        rows += n as u64;
    }
    let verified_bytes = store.verify()?;
    println!(
        "{}",
        json!({"ok":true,"imported_rows":rows,"verified_bytes":verified_bytes,"elapsed_ms":started.elapsed().as_secs_f64()*1000.0,"stats":store.stats()?})
    );
    Ok(())
}

pub fn run(
    store: &mut Archive,
    path: &Path,
    rows: usize,
    repeats: usize,
    late: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    if rows == 0 || rows > 1_000_000_000 || !(3..=1000).contains(&repeats) {
        return Err("scale rows must be 1..1000000000; repeats 3..1000".into());
    }
    if store.stats()?.rows != 0 {
        return Err("--scale needs an empty archive directory".into());
    }
    let start = Instant::now();
    for lo in (0..rows).step_by(MAX_SEGMENT_ROWS) {
        let hi = (lo + MAX_SEGMENT_ROWS).min(rows);
        let ts: Vec<_> = (lo as i64..hi as i64)
            .map(|i| if late && i % 20 == 0 { i - 10000 } else { i })
            .collect();
        let value: Vec<_> = (lo as i64..hi as i64)
            .map(|i| (i * 37) % 1000 - 500)
            .collect();
        let device: Vec<_> = (lo as i64..hi as i64).map(|i| (i * 17) % 97).collect();
        store.append(vec![ts, value, device])?;
        if hi.is_multiple_of(10_000_000) || hi == rows {
            eprintln!("Published {hi} of {rows} rows");
        }
    }
    let ingest_ms = start.elapsed().as_secs_f64() * 1000.0;
    let cases = [
        (
            "all_aggregates",
            "SELECT COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean FROM events".to_string(),
        ),
        (
            "broad_window",
            format!(
                "SELECT COUNT(*) AS n, SUM(value) AS total, AVG(value) AS mean FROM events WHERE ts >= {} AND ts < {}",
                rows / 4,
                rows * 3 / 4
            ),
        ),
        (
            "narrow_window",
            format!(
                "SELECT COUNT(*) AS n, SUM(value) AS total FROM events WHERE ts >= {} AND ts < {}",
                rows.saturating_sub(1000),
                rows
            ),
        ),
        (
            "unordered_filter",
            "SELECT COUNT(*) AS n, SUM(value) AS total FROM events WHERE value >= 0".into(),
        ),
        (
            "grouped",
            "SELECT device, SUM(value) AS total FROM events GROUP BY device ORDER BY device".into(),
        ),
        (
            "min_max",
            format!(
                "SELECT MIN(value) AS smallest, MAX(value) AS largest FROM events WHERE ts >= {}",
                rows / 2
            ),
        ),
    ];
    let mut measurements = Vec::new();
    for (name, sql) in cases {
        eprintln!("Measuring {name}");
        let first = Instant::now();
        let result = store.query(&sql)?;
        let first_us = first.elapsed().as_secs_f64() * 1e6;
        for _ in 0..3 {
            std::hint::black_box(store.query(&sql)?);
        }
        let mut samples = Vec::new();
        for _ in 0..repeats {
            let start = Instant::now();
            std::hint::black_box(store.query(&sql)?);
            samples.push(start.elapsed().as_secs_f64() * 1e6);
        }
        let mut ordered = samples.clone();
        ordered.sort_by(f64::total_cmp);
        let median = if repeats.is_multiple_of(2) {
            (ordered[repeats / 2 - 1] + ordered[repeats / 2]) / 2.0
        } else {
            ordered[repeats / 2]
        };
        measurements.push(
            json!({"name":name,"sql":sql,"first_query_us":first_us,"median_us":median,
            "p95_us":ordered[(repeats*95).div_ceil(100)-1],"samples_us":samples,"result":result}),
        );
    }
    eprintln!("Verifying every persisted block");
    let start = Instant::now();
    let verified_bytes = store.verify()?;
    let verify_ms = start.elapsed().as_secs_f64() * 1000.0;
    println!(
        "{}",
        json!({"engine":"KestrelSQL archive","version":env!("CARGO_PKG_VERSION"),"rows":rows,
        "scenario":if late {"five_percent_late"} else {"ordered"},"repeats":repeats,"threads":1,"warmups":3,
        "archive_directory":path,"ingest_ms":ingest_ms,"stats":store.stats()?,"verified_bytes":verified_bytes,
        "verify_ms":verify_ms,"queries":measurements})
    );
    Ok(())
}
