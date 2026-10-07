# Retained-handle CAT5 trial 049: unreleased development evidence

The supported engine remains **0.3.16**. This isolated successor to [trial 048](TRIAL_048.md) opens the pending bundle for read/write, flushes and synchronizes the complete catalog/metadata/payload, then retains that file handle across rename. It removes the extra post-rename reopen measured at 46,661.287 ms in 048, without changing the CAT5 bytes or moving acknowledgment ahead of synchronization. Unix directory synchronization is unchanged. Candidate binaries inherit a 0.3.16 version string and are explicitly marked development trials.

**Decision: additional correctness probe failed; candidate blocked from promotion.** The repository's default source and supported binaries remain unchanged. No new supported engine, broad database superiority or production qualification is claimed.

## Fresh paired service measurements

Each case starts with **1,000,000 rows**, 64 clients, 100-row append batches, synchronized acknowledgment and zero coalescing delay. Mixed traffic is 95% reads/5% appends; write traffic is 75% reads/25% appends; scan traffic includes 10% appends. Six configurations each have three alternating baseline/candidate pairs on this Windows computer. P99s are medians of three run p99s in milliseconds. Paired ratios are medians of within-round candidate/baseline ratios, not quotients of the displayed medians. Successful-request latency includes scheduled-arrival queue time; overload losses are separate. Fresh 049 versus released 0.3.16 measurements cannot be treated as a paired comparison with historical 048 or 047 runs.

| Workload | Overall p99, baseline → trial (ms) | Append p99, baseline → trial (ms) | Paired append ratio | Lost, baseline → trial / offered per variant |
|---|---:|---:|---:|---:|
| mixed, 2000/s, 8 s | 3.6178 → 2.5811 | 78.7518 → 71.5595 | 0.7682 | 0 → 0 / 48000 |
| mixed, 10000/s, 8 s | 70.6796 → 34.7814 | 240.6588 → 123.1775 | 0.5118 | 7211 → 3920 / 240000 |
| write, 500/s, 8 s | 66.7407 → 40.2713 | 180.6373 → 106.1283 | 0.5224 | 0 → 0 / 12000 |
| mixed, 500/s, 60 s | 38.7316 → 2.8635 | 375.7501 → 63.0879 | 0.1652 | 836 → 0 / 90000 |
| read, 2000/s, 8 s | 0.9944 → 1.0266 | — → — | — | 0 → 0 / 48000 |
| scan, 100/s, 8 s | 31.2471 → 18.0986 | 62.4429 → 36.2730 | 0.5809 | 0 → 0 / 2400 |

[All 36 cases](benchmarks/trial-049-retained-handle/paired-service.json), [independent raw-sample audit and per-round ratios](benchmarks/trial-049-retained-handle/paired-service-audit.json), [raw samples](benchmarks/trial-049-retained-handle/paired-service-samples/), [predeclared policy](benchmarks/trial-049-retained-handle/policy.json). No compilation, correctness job or packaging overlapped timed workloads. Passive host sampling does not identify a physical storage or filter-driver cause.

- ✅ `all_append_profiles_below_0_90`
- ✅ `write_p99_below_0_90`
- ✅ `write_improves_at_least_two_rounds`
- ✅ `trial_all_soaks_zero_loss`
- ❌ `read_guards_below_1_05`

## Correctness and recovery

- **82 debug and 82 release Rust tests** pass. Strict Clippy passes for ordinary and fault builds.
- **64 publication cut-point cases and 22 corruption/truncation cases** pass, including flush, synchronization, rename, retained handle and memory publication. **16 source faults, 8 source forced kills and 32 concurrent ingestion forced kills** preserve whole batches, acknowledged data, original identified retry generations and source positions.
- **4,000 SQL differential queries per DuckDB and SQLite**, plus **104 independent/manual reader oracles** including 96 concurrent requests, pass. Full scrubs bypass page caches, detect corruption and recover after repair/reopen.
- CAT2/3/4 upgrade fixtures pass; frozen 0.3.16 rejects CAT5 without file mutation. **Both 048-to-049 and 049-to-048 cold reopen/source receipt checks** pass.
- All **44,173 acknowledged batches** and **0 unacknowledged but committed batches** reconcile after the 36 timed cases. **720 NumPy windows** and **970,015,200 fresh CRC-verified payload bytes** pass. Anonymous timeout still does not imply an uncommitted append or permit a safe anonymous retry.

**Additional semantic recovery probe failed.** A checksum-valid mixed restore references `catalog-1.ks2` and `segment-1.ks2`, whose distinct payloads share generation 1. The cache identifies pages by generation, column and block, so a partial SUM returned **[[400]] instead of [[2000]]**, although a fresh full payload scrub verified 24600 bytes and the metadata full SUM returned [[5123]]. This is a catalog identity validation defect in the isolated CAT5 design shared by 048/049, not evidence of a failure in released 0.3.16. Normal writers allocate unique generations; the failing fixture models an inconsistent checksum-valid restore. The exact failing frames, binary and reproducible probe are retained. A passing CRC is insufficient to establish correct semantic identity. An isolated successor must reject duplicate physical generations before any data/cache access and pass a regression test plus all recovery gates. The completed 048 ZIP remains immutable; this finding supplements it.

[Correctness commands/results](benchmarks/trial-049-retained-handle/correctness-gates.json), [cross-candidate compatibility](benchmarks/trial-049-retained-handle/cross-candidate.json), [publication faults](benchmarks/trial-049-retained-handle/publication-049-faults.json), [source recovery](benchmarks/trial-049-retained-handle/source-049-faults.json), [concurrent kills](benchmarks/trial-049-retained-handle/group-049-recovery.json), [semantic probe](benchmarks/trial-049-retained-handle/generation-alias-probe.json), [reproducer](benchmarks/trial-049-retained-handle/harness/check_generation_alias.py), [source/binary provenance](benchmarks/trial-049-retained-handle/build-provenance.json), [complete isolated source](benchmarks/trial-049-retained-handle/candidate/).

## Unfinished work and preserved evidence

Automatic approval review rejected the first correctness-gate launch because its view still contained the prior compiler session. No gate process started. An explicit process inventory proved the compiler and all task-owned database processes had exited before the accepted retry. [Inventory evidence](benchmarks/trial-049-retained-handle/pre-gate-process-check.json). No test/build or performance evidence was overwritten.

CAT5 remains an experimental format with a shared catalog/data failure domain. Removing the only/latest catalog can be indistinguishable from empty/older state; crash orphans still require inspection. Physical power loss, extreme filesystem/device failures, the full fresh 60-shape analytical matrix, supported migration and longer sustained service qualification remain unfinished. Historical [released 60-shape analytical wins](PERFORMANCE_046.md) and [six-engine service wins/losses](SERVICE_047.md) remain separate results; this trial adds no fresh DuckDB speed comparison.

Private immutable [development evidence download](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat5-049-evidence.zip) and [SHA-256](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat5-049-evidence.zip.sha256); this supplements the [supported 0.3.16 release](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.16) without replacing it. The bundle contains the report as written before upload; this final download-link paragraph and server publication proof live in the repository.

Post-timing counters confirm **zero retained-file reopen calls**. Synchronization consumed 44,748.187 ms, **75.29%** of 59,430.855 ms combined writer/compaction time; stage counts and commit groups differ from the baseline, so these totals are not per-request speed ratios. [Measured follow-up](benchmarks/trial-049-follow-up.json). The restore identity defect is fixed and fully correctness-tested in [isolated successor 050](TRIAL_050.md); neither candidate is promoted, and 050 has no fresh speed results yet.
