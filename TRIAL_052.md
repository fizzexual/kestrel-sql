# Rejected pending-file sizing experiment 052

**Rejected: none of the four predeclared native performance gates pass.** This isolated development trial sets the exact CAT5 pending-file length before writing all frames and payloads, then performs the unchanged `sync_all` and rename. It compares against frozen development **050**, rather than supported **0.3.16**. The supported source/binaries, 050 snapshots and all previous evidence remain unchanged.

The preceding [native profile 051](PUBLICATION_051.md) found large receipt-checkpoint synchronization stalls. [`File::set_len`](https://doc.rust-lang.org/std/fs/struct.File.html#method.set_len) preserves the file cursor, but it neither guarantees physical preallocation nor promises faster publication. This bounded experiment tested that hypothesis without altering checksums, file format, acknowledgment semantics or reader kernels. Only `src/archive.rs` changes; the feature-only driver has an additional `bundle_sized` failure boundary.

## Fresh before/after

**18 fresh serial native cases**, three alternating pairs at **0, 50,000 and 99,000 starting receipt IDs**, each adding **256 identified 100-row batches**. Size order rotates. The byte-identical Rust driver's append timers exclude setup, external allocations, compact/reclaim every 32 batches, correctness checks and reopen. All timings complete before audits, hashing and packaging. This is not a sustained open-loop requests/s or 1M-row/64-client service comparison and adds no competitor speed claim.

Values are medians of three run values in milliseconds. Ratios are medians of within-round trial/base values, not ratios of displayed medians. Total time sums all 256 append timers in each run; it does not include the maintenance timers.

| Starting receipt IDs | Append p50, 050 → 052 | Append p99, 050 → 052 | Paired append-total ratio | Paired p99 ratio | Paired maximum ratio |
|---:|---:|---:|---:|---:|---:|
| 0 | 1.1990 → 1.2862 | 16.8635 → 10.8854 | ✅ 0.950750 | 0.845041 | 0.480466 |
| 50,000 | 1.2379 → 1.3085 | 48.4131 → 52.1034 | ✅ 0.992741 | 0.978200 | 0.855699 |
| 99,000 | 1.3254 → 1.2969 | 93.7197 → 92.2752 | ❌ 1.082421 | 0.984587 | 1.153630 |

- ❌ `large_ledger_append_total`
- ❌ `large_ledger_append_p99`
- ❌ `all_typical_latency_guards`
- ❌ `all_maximum_latency_guards`

At 99,000 IDs the paired total-time ratios are **0.067943, 1.082421 and 1.150979**. The first round's striking improvement is preserved alongside two slower rounds. The median paired total ratio is **1.082421** (8.24% slower), exceeding the required 0.90. The paired p99 ratio is **0.984587**, exceeding the required 0.90, and the paired maximum ratio is **1.153630**, exceeding the 1.10 guard. The 50,000-ID p50 ratio **1.050395** slightly exceeds the 1.05 guard. These criteria were declared before timing; no favorable rerun replaces a failed round.

All eight trial appends over one second occur in the 50,000-ID first round; the baseline has fourteen such appends across its 50,000/99,000-ID first rounds. The absence of >1s trial appends in this particular 99,000-ID sample does not establish removal of the underlying tail problem. Trial 052 will not advance to service qualification.

## Correctness and preserved failures

- ✅ **85 release Rust tests**, formatting and strict Clippy for ordinary/fault configurations pass. The debug suite and the complete 050 external SQL/source suite were not repeated for this rejected experiment.
- ✅ **72 publication-cut cases**: four append/compaction and delta/checkpoint scenarios, nine boundaries, process exit/injected I/O error. Eight cases cover the new `bundle_sized` boundary. Original receipt generations, exact rows/sums, idempotent retry, writer poisoning and pinned readers pass.
- ✅ **22 corruption/truncation cases** are rejected and **32 concurrent forced-kill cycles** preserve every acknowledged batch and whole-batch sums, including retries after a second reopen.
- ✅ **4,608 timed native appends / 460,800 rows**, **54 cold duplicate retries** and **65,030,400 fresh CRC-scrubbed bytes** pass. All **84 final database-frame comparisons across nine pairs** are byte-identical between 050 and 052. Every raw result and local fixture is retained.
- Preserved harness failures: the completed cut run exited 1 at its obsolete final 64-case assertion after all 72 cuts and 22 corruptions passed. The corrected harness derives the expected count from its scenarios and boundaries. Independent coverage/hash/flag auditing verifies the completed cases without rerunning them. A first coverage-auditor attempt used `cases` instead of the existing `cycles` field; its source and log are also retained. Neither failure is recorded as an engine failure or hidden as an exit-0 test run.

[Trial policy and advance criteria](benchmarks/trial-052-pending-length/trial-policy.json), [timing policy and binary hashes](benchmarks/trial-052-pending-length/policy.json), [all raw timings/statuses](benchmarks/trial-052-pending-length/raw/), [native quantile/stage audit](benchmarks/trial-052-pending-length/native-audit.json), [all paired ratios and frame equivalence](benchmarks/trial-052-pending-length/advance-audit.json), [independent recovery coverage audit](benchmarks/trial-052-pending-length/qualification-audit.json), [preserved harness failures](benchmarks/trial-052-pending-length/harness-count-failure/), [source and binary provenance](benchmarks/trial-052-pending-length/build-provenance.json).

Fault injection uses the live OS/filesystem, not physical power failure or actual device exhaustion. Only task-owned processes ran and all stopped; [pre-timing](benchmarks/trial-052-pending-length/pre-timing-process-check.json) and [post-timing](benchmarks/trial-052-pending-length/post-timing-process-check.json) inventories are preserved. Stage counters include maintenance and cumulative maxima include prefill, as in 051. No service or production-readiness qualification is claimed.

Next work should reduce the amount of receipt history rewritten and synchronized at checkpoints, with a separately specified format/migration and full recovery qualification. The rejected file-sizing path is not merged into 050 or the supported engine. No new supported release is created.

Private immutable [development evidence download](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat5-052-rejected-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat5-052-rejected-evidence.zip.sha256). This distinct supplemental asset does not replace any supported engine archive. It preserves the report before this final upload-link paragraph; server publication proof is stored in the repository.

[Reproduce both diagnostics in fresh directories](REPRODUCE_NATIVE_051_052.md). Archive/publication maintenance script snapshots are retained under benchmarks/native-051-052-maintenance; their original execution location is work/perf-052, rather than the preservation directory.
