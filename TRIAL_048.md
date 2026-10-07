# CAT5 publication trial 048: unreleased development evidence

The supported engine is still **0.3.16**. The isolated candidate places a generation's catalog frame, segment metadata and column payload in one immutable `catalog-GENERATION.ks2` file, synchronizes that complete file once, then renames it before acknowledgment. It uses a distinct CAT5 magic, reads legacy archives and rejects invalid physical bounds. Shared-file reclamation protects active data, pinned readers and receipt dependencies. The default repository source and supported binaries are unchanged.

**Decision: performance gates failed; candidate rejected for promotion.** Reducing synchronization calls did not by itself qualify a service improvement. Every round, queue failure and slower case is retained. This report compares the candidate with released Kestrel, not with fresh DuckDB or other reference performance runs. The prior [60-shape analytical matrix](PERFORMANCE_046.md) and [six-engine service qualification](SERVICE_047.md) remain separate historical measurements.

## Fresh before/after service results

Each case starts with **1,000,000 rows**, 64 clients, synchronized acknowledgment, zero coalescing delay and 100-row append batches. Mixed traffic is 95% reads/5% appends; write traffic is 75% reads/25% appends, with late arrivals under the unchanged harness. Each of six configurations has three alternating baseline/candidate pairs on this Windows computer. P99 values below are **medians of three run p99s**, in milliseconds. Paired ratios are the median of within-round candidate/baseline ratios; they are not the quotient of displayed medians. Latency covers successful operations and includes scheduled-arrival queue time; losses remain explicit.

| Workload | Overall p99, baseline → trial (ms) | Append p99, baseline → trial (ms) | Paired append ratio | Lost, baseline → trial / offered per variant |
|---|---:|---:|---:|---:|
| mixed, 2000/s, 8 s | 4.5922 → 16.6423 | 168.6352 → 159.9023 | 1.0906 | 0 → 0 / 48000 |
| mixed, 10000/s, 8 s | 106.6145 → 33.2566 | 329.0753 → 198.9046 | 0.8296 | 11358 → 9178 / 240000 |
| write, 500/s, 8 s | 174.0843 → 86.1948 | 233.9276 → 130.6664 | 0.7042 | 0 → 51 / 12000 |
| mixed, 500/s, 60 s | 34.7899 → 36.8471 | 291.5033 → 263.1818 | 2.4359 | 11687 → 3625 / 90000 |
| read, 2000/s, 8 s | 1.0656 → 0.9876 | — → — | — | 0 → 0 / 48000 |
| scan, 100/s, 8 s | 62.0404 → 13.4595 | 84.7409 → 221.1762 | 2.6100 | 0 → 0 / 2400 |

[All 36 cases](benchmarks/trial-048-bundled-generation/paired-service.json), [independent audit and per-round ratios](benchmarks/trial-048-bundled-generation/paired-service-audit.json), [raw samples](benchmarks/trial-048-bundled-generation/paired-service-samples/), [predeclared policy](benchmarks/trial-048-bundled-generation/policy.json). The baseline is fresh paired 0.3.16, not the older 047 runs. Host sampling is passive and does not identify physical disk or filter-driver causes. No compilation, correctness job or packaging overlapped timed workloads.

The predeclared performance checks are:

- ❌ `all_append_profiles_below_0_90`
- ✅ `write_p99_below_0_90`
- ✅ `write_improves_at_least_two_rounds`
- ❌ `trial_all_soaks_zero_loss`
- ✅ `read_guards_below_1_05`

## Correctness and recovery evidence

- **82 debug and 82 release Rust tests** pass, including five new CAT5 tests for exact frame bounds, signed wide aggregates, legacy upgrade, schema validation outside the current receipt chain, active-file protection, bounded normal compaction/reclamation, pinned readers and owner drop. Both ordinary and fault-feature strict Clippy checks pass.
- **CAT2, CAT3 and CAT4 fixtures** are accepted by frozen 0.3.16 before upgrade. The trial reads them, preserves old data bytes, and appends mixed-format data. Frozen 0.3.16 then rejects upgraded archives without modifying any file.
- **64 publication cut-point cases** cover delta/checkpoint appends and compaction using eight cuts, both forced process exits and injected disk-full OS errors. Cuts include both frames, partial payload, flush, sync, rename, retained-file reopen and in-memory publication. **22 corrupt/truncated catalog cases** reject publication rather than skipping past it.
- **16 source fault cases**, **8 source forced kills** and **32 concurrent ingestion forced kills** preserve acknowledged whole batches, original identified retry generations, source positions and exact output sums. Pinned readers remain readable when an I/O error poisons their writer.
- **4,000 SQL differential queries against each of DuckDB and SQLite**, plus **104 independent/manual reader SQL oracles** including 96 concurrent requests, pass. Full verification bypasses warm cached pages, detects corruption, invalidates retained stream handles and succeeds after repair and reopen.
- In the 36 timed cases, all **42,552 acknowledged append batches** and **0 unacknowledged but committed batches** reconcile after cold process reopen. **720 NumPy window oracles** and **966,124,800 CRC-scrubbed payload bytes** pass. Timeout still does not mean failed commit; this anonymous benchmark interface cannot promise safe anonymous retry.

The [gates and exact commands](benchmarks/trial-048-bundled-generation/correctness-gates.json), [publication faults](benchmarks/trial-048-bundled-generation/publication-048-faults.json), [source faults/kills](benchmarks/trial-048-bundled-generation/source-048-faults.json), [concurrent kills](benchmarks/trial-048-bundled-generation/group-048-recovery.json), [compatibility](benchmarks/trial-048-bundled-generation/compatibility.json), [source/binary hashes](benchmarks/trial-048-bundled-generation/build-provenance.json) and [complete trial source](benchmarks/trial-048-bundled-generation/candidate/) are retained.

## Failures and remaining work

The first test run failed two legacy fixture expectations: receipt-free retired data must disappear after its last pinned reader, and missing referenced data now needs a later catalog because one bundle carries both roles. A fixture branch then triggered strict Clippy for identical paths. The first fault-harness adaptation accidentally changed `sha256` to `sha264`; the first reader harness still used the old segment filename and first-frame offset. All failures, exact source snapshots, incomplete reports and corrections are preserved alongside final results. No failed evidence was overwritten or selected as a speed win.

This is a format experiment with a larger shared catalog/data failure domain. Removing the only/latest catalog can be indistinguishable from an empty/older state in either design; the tests deliberately cover removal of referenced older payloads. Normal retention is bounded by active segments plus receipt dependencies plus pinned retired files; unreferenced crash orphans still require explicit inspection. Extreme filesystem/device failures, physical power loss, long-duration service, format migration release gates and the full new 60-shape analytical matrix are unfinished. Empty-output source checkpoints, distributed fencing and general SQL coverage remain unchanged limitations. No new engine release or production guarantee is claimed.

The next decision must use the retained publication-stage deltas and sustained service failures. The candidate will not replace 0.3.16 on the basis of one fast round, fewer synchronization calls or recovered timeouts.

Private immutable [development evidence download](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat5-048-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat5-048-evidence.zip.sha256); this supplements the [supported 0.3.16 release](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.16) without replacing it. The bundle contains the report as written before upload; this final download-link paragraph and server publication proof live in the repository.

Post-load profiling: the extra retained-file reopen accumulated **46661.287 ms**, **30.20%** of the candidate's combined writer/compaction counters. Synchronization accumulated 79511.647 ms (51.46%); unmatched stage time was only 923.277 ms. Totals cover differing commit groups and are not per-request speed ratios. This supersedes the earlier uninstrumented-close hypothesis retained in the immutable bundle. The next isolated trial will test retaining a standard read/write pending handle across rename, with full recovery gates before timing. [Measured follow-up](benchmarks/trial-048-follow-up.json). Rust documents delete/rename sharing in its default Windows file-open options; that motivates a test and does not qualify this database's rename behavior by itself. [Rust Windows open options](https://doc.rust-lang.org/std/os/windows/fs/trait.OpenOptionsExt.html).
