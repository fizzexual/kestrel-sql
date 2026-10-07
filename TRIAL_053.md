# Compact receipt CAT6 experiment 053

**Useful checkpoint gains, but the native qualification fails its typical-latency guard.** This isolated development candidate derives from frozen **050**, retaining its restore-identity hardening and synchronized retained file handle. It does not contain rejected 052 file sizing. Supported **0.3.16** and all previous snapshots remain unchanged. No supported engine release or service promotion is made.

The [051 native profile](PUBLICATION_051.md) linked 50 of 52 >500 ms appends to large full receipt checkpoints. A read-only model independently reproduced the old JSON byte-for-byte and round-tripped all identifiers, SHA256 digest bytes, row counts and original generations. New CAT6 encodes each receipt as `[lowercase_hex_sha256, rows, original_generation]`, replacing the object and 32-element decimal array. It retains the same SHA256 input domain/order, 100,000-ID budget, 32-catalog chain, metadata limits, CRCs, `sync_all`, pending-file rename, directory synchronization policy and pinned-reader retention. Every persisted receipt keeps its full digest; the compact encoding adds no probabilistic retry check.

New readers accept CAT2/3/4/5/6. New writers emit CAT6. Older supported and CAT5 trial writers reject a CAT6 upgrade without modifying frames; **downgrade is unsupported**. This encoding change is isolated from SQL kernels, live queueing and source acknowledgment APIs.

## Fresh before/after, all rounds retained

18 fresh serial native fixtures: three alternating pairs at 0, 50,000 and 99,000 starting receipt IDs, each appending **256 identified 100-row batches**. Size order rotates. The byte-identical driver times only `append_once`; setup, external allocations, compact/reclaim every 32 appends, stats, two full CRC scrubs and cold reopen are outside those timers. No build, correctness run, audit, packaging or Git compression runs concurrently with timed workloads.

All values are milliseconds and are medians of three run values. Ratios are medians of within-round 053/050 ratios, **not ratios of the displayed medians**. Append total sums 256 append timers per run. Reopen is a separate untimed-by-append measurement. This is a closed-loop native diagnostic against development 050, not an open-loop requests/s, 1M-row/64-client service or fresh competitor comparison.

| Starting receipt IDs | p50, 050 → 053 | p99, 050 → 053 | Append total, 050 → 053 | Paired total | Paired p50 | Paired p99 | Paired reopen |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1.2304 → 1.1957 | 5.4745 → 1.9108 | 408.6796 → 317.5682 | 0.834559 | 1.008777 | 0.349037 | 0.875031 |
| 50,000 | 1.5209 → 1.4126 | 47.2740 → 22.5980 | 795.8976 → 607.0474 | 0.701777 | 0.975936 | 0.446718 | 0.630260 |
| 99,000 | 1.5408 → 1.6345 | 104.5557 → 49.1763 | 1417.3419 → 915.8519 | 0.645303 | 1.058960 | 0.470336 | 0.722283 |

At 99,000 IDs, the full receipt checkpoint decreases from **16,290,582 to 8,525,608 JSON bytes**: ratio **0.523346**, 47.665% fewer bytes. At 50,000 IDs it decreases from **8,242,026 to 4,311,608 bytes**, ratio **0.523125**. An independent post-run audit verifies **84 paired catalogs with equal logical metadata and byte-identical embedded segment frames/payloads**. Catalog metadata bytes intentionally differ by encoding.

The 99,000-ID paired append-total ratio **0.645303** corresponds to 35.470% less time, and paired p99 **0.470336** to 52.966% less. All three large-ledger total ratios (0.645303, 0.696647, 0.502523) and p99 ratios (0.470336, 0.480120, 0.443200) are retained. But paired p50 **1.058960** means **5.896% slower**, exceeding the predeclared 1.05 guard. First-round 0-ID maximum latency also worsens from **3.4291 to 70.5958 ms**; the later paired maximum median passes, and that slower round remains visible. No >500 ms native append appears in either variant of this new sample; earlier 051/052 stalls are still preserved and are not declared fixed.

The six criteria were declared before timing:

- ✅ `large_checkpoint_bytes`
- ✅ `large_ledger_append_total`
- ✅ `large_ledger_append_p99`
- ❌ `all_typical_latency_guards`
- ✅ `all_maximum_latency_guards`
- ✅ `all_reopen_guards`

Five of six criteria pass. **No service advancement or promotion** follows this failed gate. Stage deltas include eight maintenance publications; maxima include prefill and cannot be subtracted. At 99,000 IDs the median catalog-encoding stage total changes from 350.7287 to 174.5960 ms, and bundle-sync total from 771.8545 to 421.4976 ms. These are append-plus-maintenance totals, not evidence that encoding caused the p50 regression or that the underlying device stalls have disappeared.

## Correctness, migration and durable retry

- ✅ **88 release Rust tests**, formatting and strict Clippy for ordinary and fault-enabled configurations. The debug suite is explicitly unrun because this local drive has limited free space.
- ✅ **4,000 SQL queries against each of DuckDB and SQLite**, plus **104 manual/concurrent reader oracles**, including eight clients, signed wide output, warm corruption, handle invalidation, reopen and pinned reads.
- ✅ CAT2/3/4 migration and three CAT5→CAT6 migrations from frozen 048/049/050 preserve old frame bytes, source positions and original receipt generations. Old writers/source adapters reject the upgrade without changing frames.
- ✅ The preserved generation-alias restore is rejected before data access; the valid distinct-generation legacy upgrade retains its original receipt. The earlier wrong sums are evidence from 048/049, not freshly rerun here.
- ✅ **64 publication-cut cases**, **22 corruptions**, **16 source fault cases**, **8 source forced kills** and **32 concurrent forced-kill cycles** pass. Exact output/source-position atomicity, acknowledged batches, retry generations and cold scrubs survive the tested faults.
- ✅ **4,608 fresh timed native appends / 460,800 rows**, **54 cold duplicate retries**, and **65,030,400 CRC-scrubbed bytes** pass. All 18 original local fixtures and raw stdout/stderr/status files are retained; full native frames also appear in the supplemental ZIP.
- Preserved maintenance failures: the first new test failed to compile because a `serde_json::json!` array-repeat expression is unsupported; the source/log remain under `test-first-compile-failure`. An executable-count assertion initially included the linker PDB; the corrected audit verifies ten executable hashes separately from the PDB. A source-adapter copy referenced an absent filename before using the correct unchanged driver. These failures occurred before timing and did not change any released engine or prior evidence.

Faults use injected I/O errors and process termination on the live filesystem, not physical power loss or actual disk exhaustion. The raw source-fault report retains older seven-cut wording; its actual case list proves eight boundaries and sixteen cases. All 14 external gates and frozen default/candidate hashes were independently checked before timing and are independently rechecked after timing.

[Predeclared trial gates](benchmarks/trial-053-compact-receipts/trial-policy.json), [native timing policy/binary hashes](benchmarks/trial-053-compact-receipts/policy.json), [all raw timings and statuses](benchmarks/trial-053-compact-receipts/raw/), [all paired ratios and logical/frame equivalence](benchmarks/trial-053-compact-receipts/advance-audit.json), [native quantile and stage audit](benchmarks/trial-053-compact-receipts/native-audit.json), [correctness audit](benchmarks/trial-053-compact-receipts/correctness-audit.json), [all 14 gate commands/log hashes](benchmarks/trial-053-compact-receipts/correctness-gates.json), [complete native fixture inventory](benchmarks/trial-053-compact-receipts/fixture-inventory.json), [source/binary provenance](benchmarks/trial-053-compact-receipts/build-provenance.json), [read-only byte model](benchmarks/trial-053-compact-receipts/layout-footprint.json).

## Reproduce without replacing evidence

Download the supplemental ZIP, verify its sidecar SHA256 and internal `TRIAL_053_MANIFEST.sha256`, then extract into a separate directory. Frozen driver source, ordinary/fault binaries, all raw outputs and native database frames are included. This workspace's executed harness paths are recorded verbatim for provenance. For a new run, copy the harness to a fresh `work/perf-053` sibling layout, set its root/frozen-050/candidate binary paths, and leave any existing `policy.json`, `native-results.json`, `raw/` and `fixtures/` untouched. Declare new gates and call `native_publication.py --initialize` before running its single serial workload. Run audits only after the workload exits; they calculate Type-7 quantiles from all samples, never the best round. Full native frames are stored under `benchmarks/trial-053-compact-receipts/local-native-fixtures/` in the ZIP only, indexed by `fixture-inventory.json`.

Next work is to explain the small typical-latency regression with more targeted evidence before changing the hot path or loosening any gate. Fresh service, analytical and release qualification remain outstanding. No universal database-speed or production-readiness claim follows this experiment.

Private immutable [full development evidence and native database fixtures](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat6-053-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat6-053-evidence.zip.sha256). This distinct supplemental asset preserves the report before this final upload-link paragraph and does not replace any supported engine archive.
