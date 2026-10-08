# Native reclamation phase controls 092

October 8, 2026. **All 12 identical-control checks and all 12 phase-profiler guards pass in the full cohort and both independently balanced halves.** Every one of 72 fresh D: stores passes exact data, receipt, pinning, checksum and reopening checks. File deletion accounts for about 83% of measured reclamation time in these native fixtures; enumeration accounts for about 1.4%. This supports a separate bounded-deletion LiveArchive experiment. It is not an engine speed gain, service-p99 decomposition, physical disk cause or release. Supported version remains **0.3.16**; 0.3.17 remains unqualified without a calendar ETA.

## Source and fixed design

The [policy](benchmarks/reclaim-phases-092/policy.json) was declared before any source copy/edit, build or timer. Exact 091/090 restored diagnostic source supplies the baseline. Only Cargo feature/example declarations, an opt-in reclaim phase method/type and a meaningful comparison unit test change; the original public reclaim body, Live scheduling, publication, synchronization, ACK, data formats and exclusive ownership remain byte-exact. Versions remain 0.3.16 and identify isolated artifacts. The unsupported new feature is `reclaim-profile`; no supported binary is replaced.

All A/B/C cases use the **same exact release probe binary**. A and B invoke original public reclaim; C invokes the same eligibility, directory and deletion operations with phase clocks. Twelve rounds form two complete six-permutation halves, seed 9208, with alternating anonymous/named profile order: 72 cases, 648 reclamation windows, 216 profiled windows. Every fresh fixture starts with 32,768 rows, adds 288 groups of 100 rows, compacts at the existing 64-small-run threshold and reclaims every 32 groups. A snapshot pinned at group 64 remains through reclamation at group 160. Final stores contain 61,568 exact rows.

The fixed limits are A/A paired median 0.90–1.10 and C/A <=1.10 for summed reclaim time and each case reclaim p99, required in full and both halves. A case has nine reclamations, so its nearest-rank p99 is its maximum, with limited sample precision. There are no extra rounds, exclusions, relaxed gates or selective repeats. Append, compaction, file inventories, queries, CRC and reopen checks occur outside reclaim clocks. Inventories warm the directory in all variants; these results qualify this native fixture scope, not service latency, memory, CPU or maximum throughput.

The cohort ran 2026-10-08T18:07:38.977196+00:00 through 2026-10-08T18:08:40.527634+00:00. No build/copy/hash/package/cleanup/Git/other benchmark overlapped. The separate offline reset remained waiting for full Codex exit; ownership and no-other-work checks passed before and after the cohort.

## Correctness and retained failures

The corrected build passes **314 native debug/release test executions and three strict lint configurations**, including combined diagnostic/fault features. New checks execute 32 external probe/CLI commands plus one bridge owner: two excluded complete smokes, two baseline/profile byte comparisons, eight old/new cross-opens, 16 SQLite comparisons and two cross-process second-writer rejections. Each timed case verifies pinned data, same-process lock retention after owner drop, exact named retries, full payload CRC and cold reopen. Independent Python/NumPy auditing checks all current metadata and block CRCs, 288 named receipts per named store, contiguous keys/values and **70,926,336 data bytes**. Current receipt chains and deletion inventories remain valid. Earlier broad service/crash/source qualification is reused, not newly rerun; there is no new process-kill or physical power-loss qualification here.

The initial extra unit test tried to read the held OS lockfile and failed with Windows error 33 after both default suites passed. Its exact failed source, unit fixture, logs and policy are retained. The corrected test compares data files and tests ownership separately. Two launch-wrapper errors stopped before Native work (existing empty binary directory; unset PowerShell LASTEXITCODE after a successful script check); their helpers/status/logs are retained. Harmless guessed read paths did not affect source, runs or gates. No timed case failed. All earlier experiments remain intact.

| History | Scope | Metric | Paired B/A | Paired C/A | Decision |
| --- | --- | --- | ---: | ---: | --- |
| anonymous | full | sum_reclaim_ns | 0.997692 | 1.009416 | Pass |
| anonymous | full | case_reclaim_p99_ns | 0.976645 | 1.014076 | Pass |
| anonymous | block_0 | sum_reclaim_ns | 0.991701 | 1.019900 | Pass |
| anonymous | block_0 | case_reclaim_p99_ns | 0.966536 | 1.067673 | Pass |
| anonymous | block_1 | sum_reclaim_ns | 1.014105 | 1.004470 | Pass |
| anonymous | block_1 | case_reclaim_p99_ns | 0.999772 | 1.006943 | Pass |
| named | full | sum_reclaim_ns | 0.983156 | 1.012334 | Pass |
| named | full | case_reclaim_p99_ns | 1.004193 | 1.006437 | Pass |
| named | block_0 | sum_reclaim_ns | 0.988428 | 1.016655 | Pass |
| named | block_0 | case_reclaim_p99_ns | 0.995404 | 1.028747 | Pass |
| named | block_1 | sum_reclaim_ns | 0.983156 | 0.990299 | Pass |
| named | block_1 | case_reclaim_p99_ns | 1.016503 | 0.999195 | Pass |

Passing medians does not mean every case/request passes the ratio. Every individual result and stall remains in the raw audit; none is removed.

## Measured operation cost and next implementation

These are fractions of summed profiled outer time, not exclusive service p99 or hardware attribution. File-close/drop and loop overhead remain in the residual.

| History | Catalog delete | Retired delete | Enumeration |
| --- | ---: | ---: | ---: |
| anonymous | 41.06% | 42.23% | 1.41% |
| named | 41.62% | 41.09% | 1.48% |

Test smaller Live cleanup bursts with spare steady-state deletion capacity. Preserve the public full reclaim call, protected receipt chains, snapshot-pinned segments, existing orphan treatment, exclusive writer lock, partial-error retry, disk ceilings, publication synchronization and ACK/source/retry contracts. A file-count budget cannot bound a slow filesystem call or directory scan in wall-clock time. An implementation requires a new experiment, fresh matched A/A and candidate controls, resource/correctness/recovery checks and all release gates before adoption. Competitor losses and historical overload/minute failures remain unresolved.

## Preserved evidence

All originals remain under D:/Codex/Kestrel/work/perf-092. **5 bounded ZIPs preserve 12,066 files / 348,288,342 logical bytes**, including raw stores, failed source/tests/helpers, exact successful source/lock/binaries, complete closed logs and policy. Only regenerable build/Python caches are excluded with explicit inventory; originals stay. [Restored audit proof](benchmarks/reclaim-phases-092/restored-audit-proof.json) verifies every member CRC/SHA/size/set, every raw measurement, independent store audit, phase count and full/half decision exactly, with **zero Native launches or timing reruns**, followed by every member hash/set check. No credentials/reset-control files are packaged. See [reproduction instructions](benchmarks/reclaim-phases-092/REPRODUCE.md).

Supported core and issued overnight report remain byte-exact. Everything remains private/local. [091](TRACE_CONTROLS_091.md), [release requirements](RELEASE_TARGET_0_3_17.md), [history](BENCHMARK_HISTORY.md).
