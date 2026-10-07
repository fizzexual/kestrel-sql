# Native durable publication profile 051

**The CAT5 development trial improves typical sequential append latency but does not remove receipt-checkpoint tail stalls. No candidate is promoted.** This fresh diagnostic compares immutable released **0.3.16** with the previously qualified **development 050** binary. The supported engine and all older measurements remain unchanged.

## Before/after, fresh measurements

**18 serial cases**, three alternating pairs at each starting ledger size, rotate size order. Every case adds **256 identified 100-row batches** into a fresh archive. Append timers are inside the same byte-identical native Rust driver; setup, allocations before the call, compact/reclaim every 32 batches, checks, two full scrubs and reopen are outside those timers. This is a closed-loop native diagnostic rather than a 1M-row/64-client service or maximum requests/s test. It compares Kestrel versions and adds no fresh DuckDB or other competitor claim.

Displayed values are medians of three run values in milliseconds. Ratios are medians of within-round development/released p99 ratios; they are not quotients of the displayed medians. All raw samples and every slow run are preserved.

| Starting receipt IDs | Append p50, released → trial | Append p99, released → trial | Paired p99 ratio | Appends >1s, released → trial | Cold reopen, released → trial |
|---:|---:|---:|---:|---:|---:|
| 0 | 2.1392 → 1.1786 | 19.5806 → 2.6680 | ✅ 0.553092 | 0 → 0 / 768 | 1.7918 → 2.2650 |
| 50,000 | 2.1703 → 1.3247 | 39.4036 → 38.8836 | ❌ 1.018303 | 6 → 7 / 768 | 61.6590 → 132.8616 |
| 99,000 | 2.8797 → 1.4877 | 2261.1979 → 2300.9184 | ❌ 1.001593 | 16 → 17 / 768 | 115.0247 → 217.9399 |

The paired p50 ratios are **0.569827, 0.610399 and 0.462461**, all favoring the trial. Tail latency is less consistent: the 99,000-ID p99 ratios by round are **26.052162, 1.001593 and 0.052919**. Those large swings are retained rather than treated as a stable speed gain. Median cold reopen is slower in the CAT5 trial at every ledger size; at 99,000 IDs it increases from **115.0247 to 217.9399 ms**.

## Measured bottleneck

Full receipt checkpoints grow to about **8.2 MB at 50,000 IDs and 16.3 MB at 99,000 IDs**. Of the **52 appends exceeding 500 ms**, **50** occur at these large checkpoint writes; two other trial appends write small delta files. In slow checkpoint-heavy runs, synchronization accounts for roughly **96–97% of recorded publication-stage time**. Both formats experience multi-second stalls, including a **3168.6316 ms** trial delta append. This local evidence identifies the synchronization stage; it does not establish the physical storage or OS cause.

Stage totals and histogram deltas are after-minus-before counters and **include eight maintenance publications** per case. They must not be labeled append-only. Final stage maxima include prefill and are not subtractable. The audit retains these limits explicitly.

The next controlled experiment sets the exact pending-file length before writing the full CAT5 frame, then performs the same `sync_all` and rename. Rust documents that [`File::set_len`](https://doc.rust-lang.org/std/fs/struct.File.html#method.set_len) preserves the cursor; it does not promise a performance gain or physical preallocation. Trial 052 remains isolated and will be rejected unless new paired measurements justify it. A separate metadata layout or persistent journal remains longer-term work requiring format/recovery qualification.

## Correctness and reproducibility

All **4,608 timed appends / 460,800 rows**, **54 duplicate retries after cold reopen**, exact COUNT/SUM and **65,030,400 CRC-scrubbed payload bytes** pass. No fresh forced-crash test was run in 051; development 050's earlier [crash/semantic qualification](TRIAL_050.md) remains separately labeled. Every fixture is retained locally, with its file sizes and hashes in [the inventory](benchmarks/publication-051-native/retained-fixture-inventory.json).

[Predeclared policy and hashes](benchmarks/publication-051-native/policy.json), [raw outputs and exit statuses](benchmarks/publication-051-native/raw/), [independent audit with per-round pairs and stage histograms](benchmarks/publication-051-native/native-audit.json), [exact harness](benchmarks/publication-051-native/native_publication.py). The preserved native probes link to the complete [released source](benchmarks/baseline-0.3.16-source/) and [development 050 source](benchmarks/trial-050-generation-identity/candidate/) through their build provenance.

All timings finished before this audit, fixture hashing and preservation. No compilation or CPU-heavy job ran concurrently with them. [Before](benchmarks/publication-051-native/pre-timing-process-check.json) and [after](benchmarks/publication-051-native/post-timing-process-check.json) process inventories confirm the database/compiler isolation and stopped task-owned probes. Full service stability, fresh analytical qualification and production readiness remain unproved.

Private immutable [development evidence download](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-publication-051-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-publication-051-evidence.zip.sha256). This distinct supplemental asset does not replace any supported engine archive. It preserves the report before this final upload-link paragraph; server publication proof is stored in the repository.

[Reproduce both diagnostics in fresh directories](REPRODUCE_NATIVE_051_052.md). Archive/publication maintenance script snapshots are retained under benchmarks/native-051-052-maintenance; their original execution location is work/perf-052, rather than the preservation directory.
