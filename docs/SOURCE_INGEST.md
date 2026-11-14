# Source positions committed with their output

`SourceArchive` owns the embedded archive and commits output plus a half-open source interval together. After a lost ACK or process failure, reopen and read `position(source)` to resume. Known exact intervals remain retryable with their original generations. A new interval must begin at the current position; a gap, overlap or stale start fails before publication. The first nonempty interval anchors a previously unseen source at its supplied start.

```rust
use kestrel_sql::archive::Archive;
use kestrel_sql::source::SourceArchive;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut sink = SourceArchive::new(
        Archive::open("orders-store", "events", &["ts", "value", "device"])?
    )?;
    let start = sink.position("orders:partition0")?
        .map_or(0, |position| position.next_offset);
    // Read and transform the source beginning at `start`.
    sink.commit("orders:partition0", start, start + 100,
        vec![vec![1000, 1001], vec![12, 18], vec![1, 2]])?;
    println!("{:?}", sink.position("orders:partition0")?);
    Ok(())
}
```

The example maps 100 consumed records to two output rows; source offsets and output count are separate. Applications supply stable case-sensitive source identities (1..1024 UTF-8 bytes), start/next u64 offsets and deterministic output in schema order. Reopening must use the same source configuration. Exact input order remains part of payload identity. Changing output for an already committed interval fails. A replay's original receipt generation can precede the latest source position; always read the latest position when resuming.

The wrapper stores a versioned SHA-256 source hash and fixed-width hexadecimal start/next in reserved 104-byte `ksrc1:` receipt IDs. The existing catalog publishes that ID, payload digest, row count and original generation with the output. No extra checkpoint file or synchronization is needed. Source labels themselves are not persisted. Do not manually write reserved source IDs through generic or older writers: they bypass the source guard. Ordinary nonreserved receipts can coexist and do not affect source positions.

On opening, a borrowed BTreeMap prefix iterator reconstructs at most 4096 positions without cloning/scanning unrelated receipts. It validates continuity and strictly increasing original generations. Invalid reserved history fails closed. The global 100K-ID ceiling covers source and ordinary receipts; there is no silent eviction. Logical checkpoint bytes exclude tree nodes/allocator overhead and are not process RSS.

Rust mutable ownership serializes writes; callers can share the owner through a Mutex. Capture an immutable snapshot while holding that owner, then release the owner before querying. Source ingestion has no background queue or automatic maintenance; call `compact_small` and `reclaim` explicitly. Captured snapshots retain their data across later writes and maintenance. Source position reads and subsequent old/new commits fail after an unknown publication outcome until reopening; older pinned snapshots remain readable.

The API requires an advancing interval and nonempty output. Archive batch limits apply: at most 1M rows and 64MiB in 1..64 equal-length schema columns. Zero-output filtering cannot advance a checkpoint yet. Source reset/registration, receipt retention, external source transactions, multiple-sink atomicity, consumer leases and distributed fencing are not delivered. The local offset check does not identify a consumer owner or reject a stale owner who knows the current offset.

Run the [SDK example](../examples/source_ingest.rs) with a fresh directory:

```powershell
cargo run --release --example source_ingest -- FRESH_DIRECTORY
```

It verifies exact replay, gap rejection, a stable pinned view, late data and offset/data reopening. [The executed Parquet workflow](../lab-notebook/portfolio/source-pipeline-037-results.json) commits and replays 300 intervals from two sources, rejects changed/gapped input, resumes at 25K/5K offsets and matches 42 DuckDB SQL queries. Its stdin adapter is task-only tooling with limited error handling. Kestrel still has no native Parquet/Arrow or Kafka connector.

[PERFORMANCE_037.md](../lab-notebook/PERFORMANCE_037.md) includes matched-ID cost measurements, 55 Rust tests, 14 exact publication failures and eight forced process-kill/resume cycles. Write stalls remain unqualified; this release adds a useful recovery contract without claiming a new durable-write throughput record.
