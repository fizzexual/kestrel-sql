# Zero-filled file reservation 057: initialization defeats the improvement

**Six of ten predeclared primitive-model checks fail. No SQL engine code is changed or promoted.** This follows [056](PUBLICATION_056.md), whose persistent-file large-frame totals missed their criteria, and [055](SERVICE_TRIAL_055.md), whose CAT6 service stalls remain unresolved. The experiment tests growing a retained synchronized file against writing and synchronizing its entire planned capacity with zeros before committing records. It does not reuse the rejected [052 per-generation set_len experiment](TRIAL_052.md).

The hypothesis comes from [PostgreSQL's wal_init_zero documentation](https://www.postgresql.org/docs/current/runtime-config-wal.html#GUC-WAL-INIT-ZERO): initialization can reserve space before record writes on some filesystems, with different behavior on copy-on-write filesystems. That supports testing a hypothesis, not predicting a Windows result. This probe uses actual zero writes, no set_len, no privileged valid-data shortcut, no changed Windows flags and no disabled sync. Each measured commit flushes a 64 KiB BufWriter and calls sync_all in both modes.

## Twelve fresh serial cases

Two raw byte volumes, three alternating pairs each, 256 commits per case. The same standalone binary implements both modes. All frames remain identical to 056, but these are **new measurements with a new driver**, not timing ratios against historical 056. Values are medians of three run values in ms. Ratios are medians of within-round reserved/growing ratios; their values can differ from the quotient of displayed medians.

| Payload bytes | Metric | Growing file ms | File filled with zeros ms | Paired ratio | Declared result |
|---:|---|---:|---:|---:|---|
| 2,400 | 256-commit total | 113.1083 | 109.2073 | 0.965511 | ❌ > 0.85 |
| 2,400 | Bootstrap + commits | 115.2326 | 111.7299 | 0.969603 | ❌ > 0.90 |
| 2,400 | Setup/commit wall, including encoding | 116.4017 | 112.8820 | 0.969762 | ❌ > 0.90 |
| 2,400 | Commit p50 | 0.392550 | 0.390850 | 0.995416 | ✅ <= 1.05 |
| 2,400 | Commit p99 | 0.893080 | 0.746690 | 0.836084 | ✅ <= 0.95 |
| 153,600 | 256-commit total | 247.0609 | 245.8271 | 1.002072 | ❌ > 0.85 |
| 153,600 | Bootstrap + commits | 248.9525 | 374.6079 | 1.504021 | ❌ > 0.90 |
| 153,600 | Setup/commit wall, including encoding | 270.1567 | 397.9781 | 1.467388 | ❌ > 0.90 |
| 153,600 | Commit p50 | 0.839200 | 0.838750 | 0.999464 | ✅ <= 1.05 |
| 153,600 | Commit p99 | 1.432285 | 1.286215 | 0.931000 | ✅ <= 0.95 |

Bootstrap medians are **1.3218 vs 2.8518 ms** for small frames and **1.3595 vs 128.7808 ms** for large frames. All create/fill/sync/seek stages and total bootstrap cost remain visible. Bootstrap plus native commit totals charge the reservation cost. The separate setup/commit wall also charges equal frame generation, encoding and native control overhead, excluding only final cold verification. Directory creation precedes both lifecycle timers and is untimed.

The first large-frame pair favors reservation in commit-only total (ratio **0.693544**) and p99 (**0.089800**), but its charged total ratio is **1.052831**. The other large commit totals are **1.002072** and **1.020115**; their charged totals are **1.515726** and **1.504021**. All pairs contribute. The smaller-frame middle pair is also slower: charged total **1.149364**, p99 **1.217965**. Neither the favorable first pair nor the tail improvement qualifies this technique.

The fresh growing-file baseline is much faster in absolute terms than historical 056. Code, process history and measurement time differ; this is not an engine improvement or a paired comparison with 056. No physical device, OS, antivirus or background-activity cause is assigned. Shared-host variation remains a limitation.

## Independent checks and preservation

**3,072 raw samples** are independently recomputed with Type 7 quantiles. The auditor verifies predeclared order, source/binary/policy/raw hashes, finite nonnegative stage values and stage totals bounded by their outer timers. The bootstrap cost is independently added to each run's commit total, and setup/commit wall must cover both.

All **3,072 frames / 239,763,456 encoded bytes** independently pass header/footer CRCs, complements, sequence, size/bounds and EOF checks. Twenty-four first/last payload vectors match independent Python generation. All six mode pairs have byte-identical complete files; all twelve final files also match frozen 056 file hashes. The **12 full fixture files / 239,763,648 bytes** are retained. Cold byte equality does not implement or test crash recovery for partially overwritten reserved space.

[Predeclared policy](benchmarks/publication-057-reservation/policy.json), [all raw samples/statuses](benchmarks/publication-057-reservation/raw/), [paired audit and every stage](benchmarks/publication-057-reservation/model-audit.json), [standalone source](benchmarks/publication-057-reservation/reservation_probe.rs), [build and derivation](benchmarks/publication-057-reservation/build_model.py), [build provenance](benchmarks/publication-057-reservation/build-provenance.json), [runner](benchmarks/publication-057-reservation/run_model.py), [independent auditor](benchmarks/publication-057-reservation/audit_model.py), [fixture inventory](benchmarks/publication-057-reservation/fixture-inventory.json), [pre-timing process check](benchmarks/publication-057-reservation/pre-timing-process-check.json), [post-timing process check](benchmarks/publication-057-reservation/post-timing-process-check.json).

Reproduce only in a fresh directory with a new policy and recorded hashes. The original build uses Rust 1.97.1 and recorded cached serde_json 1.0.151/crc32fast 1.5.2 artifacts. The initial compiler wrapper prints a rustup path-canonicalization warning during toolchain discovery; strict compiler warnings and the build pass, and the message is retained in the build invocation record. A standalone locked Cargo project, a portable repository-path override for auditing and [fresh-directory instructions](benchmarks/publication-057-reservation/REPRODUCE.md) are now preserved. After the original series, an independent Cargo build passes strict warnings and both small-volume modes match frozen file bytes; its 512 diagnostic samples are excluded from competitive results. [Separate reproduction check](benchmarks/publication-057-reservation/cargo-reproduction-check.json). Rebuilding produces a new binary and measurement. All earlier evidence and the already-issued morning report remain unchanged.

No compilation, correctness tests, audits, packaging or Git compression overlap native timers. All task-owned probes have exited. This finite model knows its final capacity in advance and ends with no unused tail; a real Archive journal must support bounded rotation, checkpoint/reclamation, independent readers, durable receipts/source offsets, ambiguous outcomes, truncated-tail recovery and migration. None of those are implemented or qualified here. No requests/s, SQL, physical power-loss, distributed or production qualification follows from this model.

**Decision:** reject this reservation model as a demonstrated performance improvement. The next useful work is an archive-specific durable-journal design with explicit checkpoints/recovery and end-to-end service gates, rather than incorporating an unqualified file optimization.

Private immutable [all model/reproduction evidence and primitive fixtures](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-io-057-reservation-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-io-057-reservation-evidence.zip.sha256). This distinct supplemental asset preserves the report before this final upload-link paragraph and replaces no supported engine archive.
