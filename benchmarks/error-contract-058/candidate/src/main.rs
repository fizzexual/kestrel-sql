use kestrel_sql::Database;
use serde_json::json;
use std::io::{self, BufRead, Write};
use std::path::PathBuf;
use std::time::Instant;
mod scale;
mod wire_json;

fn benchmark(
    mut db: Database,
    rows: usize,
    repeats: usize,
    path: Option<PathBuf>,
) -> Result<(), Box<dyn std::error::Error>> {
    if !(1..=10_000_000).contains(&rows) || !(3..=1000).contains(&repeats) {
        return Err("rows must be 1..10000000 and repeats 3..1000".into());
    }
    db.execute(
        "CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL)",
    )?;
    let ts: Vec<i64> = (0..rows as i64).collect();
    let value: Vec<i64> = (0..rows as i64).map(|i| (i * 37) % 1000 - 500).collect();
    let device: Vec<i64> = (0..rows as i64).map(|i| (i * 17) % 97).collect();
    let start = Instant::now();
    db.append("events", vec![ts, value, device])?;
    let ingest_ms = start.elapsed().as_secs_f64() * 1000.0;
    let mut reopen_ms = None;
    if let Some(path) = &path {
        drop(db);
        let start = Instant::now();
        db = Database::open(path)?;
        reopen_ms = Some(start.elapsed().as_secs_f64() * 1000.0);
    }
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
            "SELECT COUNT(*) AS n, SUM(value) AS total FROM events WHERE value >= 0".to_string(),
        ),
        (
            "grouped",
            "SELECT device, SUM(value) AS total FROM events GROUP BY device ORDER BY device"
                .to_string(),
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
        for _ in 0..3 {
            std::hint::black_box(db.query(&sql)?);
        }
        let mut samples = Vec::new();
        for _ in 0..repeats {
            let start = Instant::now();
            std::hint::black_box(db.query(&sql)?);
            samples.push(start.elapsed().as_secs_f64() * 1_000_000.0);
        }
        let mut ordered = samples.clone();
        ordered.sort_by(f64::total_cmp);
        let result = db.query(&sql)?;
        let median = if repeats.is_multiple_of(2) {
            (ordered[repeats / 2 - 1] + ordered[repeats / 2]) / 2.0
        } else {
            ordered[repeats / 2]
        };
        measurements.push(json!({"name": name, "sql": sql, "median_us": median,
            "p95_us": ordered[(repeats * 95).div_ceil(100).saturating_sub(1)], "samples_us": samples,
            "result": result.rows, "plan": result.plan, "rows_scanned": result.rows_scanned}));
    }
    println!(
        "{}",
        json!({"engine": "KestrelSQL", "version": env!("CARGO_PKG_VERSION"),
        "mode": if path.is_some() { "durable" } else { "memory" }, "rows": rows, "repeats": repeats,
        "warmups": 3, "threads": 1, "ingest_ms": ingest_ms, "reopen_ms": reopen_ms,
        "logical_index_bytes": db.logical_index_bytes(), "queries": measurements})
    );
    Ok(())
}

fn run() -> Result<bool, Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let mut path = None;
    let mut sql = None;
    let mut file = None;
    let mut bench = None;
    let mut archive_path = None;
    let mut scale_bench = None;
    let mut import = None;
    let mut late = false;
    let mut column_names = "ts,value,device".to_string();
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--archive" => {
                i += 1;
                archive_path = Some(PathBuf::from(
                    args.get(i).ok_or("--archive needs a directory")?,
                ));
            }
            "--columns" => {
                i += 1;
                column_names = args
                    .get(i)
                    .ok_or("--columns needs comma-separated names")?
                    .clone();
            }
            "--import-i64" => {
                i += 1;
                import = Some(PathBuf::from(
                    args.get(i).ok_or("--import-i64 needs a file")?,
                ));
            }
            "--late" => late = true,
            "--scale" => {
                i += 1;
                let n = args
                    .get(i)
                    .ok_or("--scale needs rows and repeats")?
                    .parse()?;
                i += 1;
                let r = args
                    .get(i)
                    .ok_or("--scale needs rows and repeats")?
                    .parse()?;
                scale_bench = Some((n, r));
            }
            "--db" => {
                i += 1;
                path = Some(PathBuf::from(args.get(i).ok_or("--db needs a path")?));
            }
            "--sql" => {
                i += 1;
                sql = Some(args.get(i).ok_or("--sql needs a statement")?.clone());
            }
            "--file" => {
                i += 1;
                file = Some(PathBuf::from(args.get(i).ok_or("--file needs a path")?));
            }
            "--bench" => {
                i += 1;
                let n = args
                    .get(i)
                    .ok_or("--bench needs rows and repeats")?
                    .parse()?;
                i += 1;
                let r = args
                    .get(i)
                    .ok_or("--bench needs rows and repeats")?
                    .parse()?;
                bench = Some((n, r));
            }
            "--help" => {
                println!(
                    "KestrelSQL — experimental, not production-ready\nkestrel [--db DIRECTORY] [--sql STATEMENT | --file FILE]\nkestrel [--db EMPTY_DIRECTORY] --bench ROWS REPEATS\nkestrel --archive DIRECTORY [--sql STATEMENT | --file FILE]\nkestrel --archive EMPTY_DIRECTORY --scale ROWS REPEATS [--late]\nkestrel --archive DIRECTORY --import-i64 FILE [--columns ts,value,device]\nWithout --sql/--file: one SQL statement per stdin line; JSON lines on stdout.\nBinary import: headerless row-major signed little-endian i64 values. One atomic batch per segment."
                );
                return Ok(false);
            }
            other => return Err(format!("unknown argument: {other}").into()),
        }
        i += 1;
    }
    if [
        sql.is_some(),
        file.is_some(),
        bench.is_some(),
        scale_bench.is_some(),
        import.is_some(),
    ]
    .iter()
    .filter(|x| **x)
    .count()
        > 1
    {
        return Err("choose one of --sql, --file, --bench, --scale, --import-i64".into());
    }
    if archive_path.is_some() && (path.is_some() || bench.is_some()) {
        return Err("--archive is incompatible with --db and --bench".into());
    }
    if archive_path.is_none() && (scale_bench.is_some() || import.is_some() || late) {
        return Err("archive options require --archive".into());
    }
    let mut archive = if let Some(p) = &archive_path {
        Some(kestrel_sql::archive::Archive::open(
            p,
            "events",
            &column_names.split(',').collect::<Vec<_>>(),
        )?)
    } else {
        None
    };
    if let Some((n, r)) = scale_bench {
        scale::run(
            archive.as_mut().unwrap(),
            archive_path.as_ref().unwrap(),
            n,
            r,
            late,
        )?;
        return Ok(false);
    }
    if let Some(p) = import {
        scale::import_i64(
            archive.as_mut().unwrap(),
            &p,
            column_names.split(',').count(),
        )?;
        return Ok(false);
    }
    let mut db = match &path {
        Some(p) => Database::open(p)?,
        None => Database::memory(),
    };
    if let Some((n, r)) = bench {
        benchmark(db, n, r, path)?;
        return Ok(false);
    }
    let reader: Box<dyn BufRead> = if let Some(sql) = sql {
        Box::new(io::Cursor::new(sql))
    } else if let Some(file) = file {
        Box::new(io::BufReader::new(std::fs::File::open(file)?))
    } else {
        Box::new(io::BufReader::new(io::stdin()))
    };
    let mut failed = false;
    let mut out = io::BufWriter::new(io::stdout().lock());
    for line in reader.lines() {
        let line = line?;
        if line.trim().is_empty() || line.trim_start().starts_with("--") {
            continue;
        }
        let result: Result<String, String> = if let Some(store) = &archive {
            store
                .query(&line)
                .map_err(|e| e.to_string())
                .and_then(|r| wire_json::success(&r).map_err(|e| e.to_string()))
        } else {
            db.execute(&line)
                .map_err(|e| e.to_string())
                .and_then(|r| wire_json::success(&r).map_err(|e| e.to_string()))
        };
        match result {
            Ok(response) => writeln!(out, "{response}")?,
            Err(e) => {
                failed = true;
                writeln!(out, "{}", wire_json::failure(&e)?)?;
            }
        }
        out.flush()?;
    }
    Ok(failed)
}

fn main() {
    match run() {
        Ok(false) => (),
        Ok(true) => std::process::exit(1),
        Err(e) => {
            eprintln!("{e}");
            std::process::exit(1);
        }
    }
}
