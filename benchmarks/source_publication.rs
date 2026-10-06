//! Identical manual IDs versus archive-local checkpoint validation; test-only.
use kestrel_sql::archive::{Archive, ArchiveSnapshot, IngestBatch, IngestReceipt};
#[cfg(not(kestrel_baseline))]
use kestrel_sql::source::SourceArchive;
use kestrel_sql::{Result, Value};
use sha2::{Digest, Sha256};
use std::time::Instant;

enum Sink {
    Ordinary(Archive),
    #[cfg(not(kestrel_baseline))]
    Checkpoint(SourceArchive),
}
fn manual_id(source: &str, start: u64, next: u64) -> String {
    let mut hash = Sha256::new();
    hash.update(b"kestrelsql.source.v1\0");
    hash.update(source.as_bytes());
    let key: String = hash
        .finalize()
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect();
    format!("ksrc1:{key}:{start:016x}:{next:016x}")
}
impl Sink {
    fn new(archive: Archive, mode: &str) -> Result<Self> {
        #[cfg(not(kestrel_baseline))]
        if mode == "checkpoint" {
            return Ok(Self::Checkpoint(SourceArchive::new(archive)?));
        }
        assert_eq!(mode, "ordinary");
        Ok(Self::Ordinary(archive))
    }
    fn commit(
        &mut self,
        source: &str,
        start: u64,
        next: u64,
        columns: Vec<Vec<i64>>,
    ) -> Result<IngestReceipt> {
        match self {
            Self::Ordinary(archive) => {
                archive.append_once(&manual_id(source, start, next), columns)
            }
            #[cfg(not(kestrel_baseline))]
            Self::Checkpoint(archive) => archive.commit(source, start, next, columns),
        }
    }
    fn snapshot(&self) -> Result<ArchiveSnapshot> {
        match self {
            Self::Ordinary(archive) => archive.snapshot(),
            #[cfg(not(kestrel_baseline))]
            Self::Checkpoint(archive) => archive.snapshot(),
        }
    }
    fn maintenance(&mut self) -> Result<()> {
        match self {
            Self::Ordinary(archive) => {
                archive.compact_small()?;
                archive.reclaim()?;
            }
            #[cfg(not(kestrel_baseline))]
            Self::Checkpoint(archive) => {
                archive.compact_small()?;
                archive.reclaim()?;
            }
        };
        Ok(())
    }
}
fn open(path: &str) -> Result<Archive> {
    Archive::open(path, "events", &["ts", "value", "device"])
}
fn payload(ids: i64, batch: usize) -> Vec<Vec<i64>> {
    let lo = ids + batch as i64 * 100;
    vec![
        (lo..lo + 100).collect(),
        (lo..lo + 100).map(|i| i * 2).collect(),
        (lo..lo + 100).map(|i| i % 97).collect(),
    ]
}
fn main() -> Result<()> {
    let args: Vec<_> = std::env::args().collect();
    let path = &args[1];
    let ids: i64 = args[2].parse().unwrap();
    let mode = &args[3];
    assert!([0, 50_000].contains(&ids));
    let mut archive = open(path)?;
    assert_eq!(archive.stats()?.rows, 0);
    if ids > 0 {
        archive.append_group(
            (0..ids)
                .map(|index| IngestBatch {
                    id: Some(format!("seed:{index}")),
                    columns: vec![vec![index], vec![index * 2], vec![index % 97]],
                })
                .collect(),
        )?;
    }
    let started = Instant::now();
    let mut sink = Sink::new(archive, mode)?;
    let source_map_initialization_ms = started.elapsed().as_secs_f64() * 1000.;
    let before = sink.snapshot()?.stats()?;
    let mut raw_latency_ms = Vec::new();
    let mut raw_catalog_bytes = Vec::new();
    let mut receipts = Vec::new();
    let mut maintenance_ms = Vec::new();
    let mut expected_sum = i128::from(ids) * i128::from(ids - 1);
    for batch in 0..96 {
        let source = format!("partition{}", batch % 4);
        let start = (batch / 4 * 100) as u64;
        let columns = payload(ids, batch);
        let started = Instant::now();
        let receipt = sink.commit(&source, start, start + 100, columns)?;
        raw_latency_ms.push(started.elapsed().as_secs_f64() * 1000.);
        assert!(!receipt.duplicate && receipt.rows == 100);
        raw_catalog_bytes.push(
            std::fs::metadata(
                std::path::Path::new(path).join(format!("catalog-{:020}.ks2", receipt.generation)),
            )?
            .len(),
        );
        expected_sum += i128::from(2 * (ids + batch as i64 * 100) + 99) * 100;
        receipts.push(receipt);
        if (batch + 1).is_multiple_of(32) {
            let started = Instant::now();
            sink.maintenance()?;
            maintenance_ms.push(started.elapsed().as_secs_f64() * 1000.);
        }
    }
    let after = sink.snapshot()?.stats()?;
    let expected_rows = ids as u64 + 9600;
    assert_eq!(after.rows, expected_rows);
    assert_eq!(after.recorded_batch_ids, ids as usize + 96);
    assert_eq!(
        sink.snapshot()?
            .query("SELECT COUNT(*), SUM(value) FROM events")?
            .result
            .rows,
        vec![vec![
            Value::Int(expected_rows.into()),
            Value::Int(expected_sum)
        ]]
    );
    assert_eq!(sink.snapshot()?.verify()?, expected_rows * 24);
    drop(sink);
    let started = Instant::now();
    let archive = open(path)?;
    let archive_reopen_ms = started.elapsed().as_secs_f64() * 1000.;
    let started = Instant::now();
    let mut sink = Sink::new(archive, mode)?;
    let source_map_rebuild_ms = started.elapsed().as_secs_f64() * 1000.;
    for batch in [0, 48, 95] {
        let source = format!("partition{}", batch % 4);
        let start = (batch / 4 * 100) as u64;
        let replay = sink.commit(&source, start, start + 100, payload(ids, batch))?;
        assert!(replay.duplicate && replay.generation == receipts[batch].generation);
    }
    let mut raw_retry_ns = Vec::new();
    for _ in 0..1000 {
        let columns = payload(ids, 0);
        let started = Instant::now();
        let replay = sink.commit("partition0", 0, 100, columns)?;
        raw_retry_ns.push(started.elapsed().as_nanos() as u64);
        assert!(replay.duplicate && replay.generation == receipts[0].generation);
    }
    assert_eq!(sink.snapshot()?.verify()?, expected_rows * 24);
    drop(sink);
    #[cfg(not(kestrel_baseline))]
    let positions = {
        let source = SourceArchive::new(open(path)?)?;
        let positions: Vec<_> = (0..4)
            .map(|index| {
                source
                    .position(&format!("partition{index}"))
                    .unwrap()
                    .unwrap()
            })
            .collect();
        assert!(
            positions
                .iter()
                .all(|p| p.next_offset == 2400 && p.committed_batches == 24)
        );
        Some(positions)
    };
    #[cfg(kestrel_baseline)]
    let positions: Option<Vec<serde_json::Value>> = None;
    println!(
        "{}",
        serde_json::json!({"version":env!("CARGO_PKG_VERSION"),"mode":mode,"prefill_ids":ids,
        "raw_latency_ms":raw_latency_ms,"raw_catalog_bytes":raw_catalog_bytes,"raw_retry_ns":raw_retry_ns,
        "maintenance_ms":maintenance_ms,"archive_reopen_ms":archive_reopen_ms,
        "source_map_initialization_ms":source_map_initialization_ms,"source_map_rebuild_ms":source_map_rebuild_ms,
        "before":before,"after":after,"source_positions":positions,"all_receipts_valid":true,
        "rows_and_sums_match":true,"full_scrubs_passed":true})
    );
    Ok(())
}
