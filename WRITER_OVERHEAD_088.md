# Controlled service compatibility and writer overhead 088

October 8, 2026. **Qualification fails. Supported KestrelSQL remains 0.3.16; 0.3.17 is not qualified and has no justified calendar ETA.** All 288 fresh cases pass scoped correctness and recovery, but 15 of 156 identical-binary checks and 12 of 156 candidate guards fail. Six candidate failures have passing corresponding controls. No new engine change, low-overhead qualification or competitor win is established.

The full-cohort default released-core build has a calibrated write-heavy overall p99 regression: paired candidate/A 1.234137, about **23.4% higher**. Its matching A/A is 0.928233 and passes the fixed 10% range. The clean-core default build's overall regression is also calibrated at paired 1.202270, about 20.2% higher. Its append difference is unqualified because that control fails. These compare preserved original executables with fresh 087 default artifacts; they do not isolate an engine change, compiler/layout effect or physical cause.

## Frozen comparison

The six exact executables come from released 0.3.16, clean query fix 061 and the corrected 087 default/writer builds. No compilation ran for 088. [Policy](benchmarks/writer-overhead-088/policy.json) and [timing freeze](benchmarks/writer-overhead-088/timing-freeze.json) identify every binary/source/harness SHA and case. Each family uses the same baseline executable twice, as A and B:

| Family | A and B | Candidate |
| --- | --- | --- |
| compatibility-released | Exact original 0.3.16 | 087 released-core default build |
| compatibility-clean | Exact original 0.3.17-dev.61 | 087 clean-core default build |
| overhead-released | Exact 087 released-core default | Exact 087 released-core writer tracing |
| overhead-clean | Exact 087 clean-core default | Exact 087 clean-core writer tracing |

Twelve rounds contain all six A/B/C permutations twice. Each six-round half independently includes every permutation and balances both pair order and slot. Four families, two profiles and three variants yield 288 fresh serial stores: 1M seed rows, 64 clients, 100-row anonymous append batches, zero deliberate grouping delay; read 2,000 offers/s for 8 s and 25%-write 500 offers/s for 8 s. The first six-round draft was strengthened before any native run, with every numerical limit unchanged. Both six-binary setup-smoke cohorts are preserved and excluded from all gates.

Compatibility A/A p99/rate limits are 0.90–1.10, candidate p99 <=1.10 and achieved-window rate >=0.90. Tracer A/A limits are 0.95–1.05, candidate p99 <=1.05 and rate >=0.95. Both require zero losses; native peak-working-set ratio and additional 2 MiB guards also apply. Every family must pass the full cohort and both halves. Candidate/B is diagnostic only and cannot replace candidate/A. Counts include overlapping full/half checks and read overall/query metrics with the same population; they are not independent statistical observations.

The cohort ran from 2026-10-08T13:01:57.545145+00:00 through 2026-10-08T13:46:18.125957+00:00. Builds, copying, hashing, packaging, cleanup and other timed jobs were stopped throughout. Resource callbacks, trace getters, correctness/reopen checks and final audits run outside arrival/drain timing. Python records the append receipt already returned by the native bridge; all variants use the same wrapper.

## Correctness and complete outcome accounting

All **2,880,000/2,880,000 offers** succeed, with zero errors, drops, expiries or unexecuted requests. All **147,024 acknowledged 100-row batches** are present after reopen, with exact count/sum atomicity and no unacknowledged-but-committed batch. Independent NumPy comparisons cover **5,760 windows**, and full CRC checks cover **7,264,857,600 row-data bytes**.

All 24,504 traced append ACKs map exactly to unique fixture keys and publication generations. The audit checks chronological complete event ranges, attempt/generation conservation, all seven aggregate stage totals, catalog bytes, append/compaction/reclaim counts, inactive cycles and zero dropped records. Native tests, byte/retry/controlled-failure and original-version reopen qualification from 087 are reused, not newly rerun. This scoped cohort omits minute mixed, overload, scans, competitor refresh and full crash/source/power-loss qualification.

## Fixed full and half decisions

| Family | Scope | Failed A/A checks | Failed candidate guards | Required decision |
| --- | --- | ---: | ---: | --- |
| compatibility-released | full | 0/13 | 1/13 | Fail |
| compatibility-released | block_0 | 1/13 | 0/13 | Fail |
| compatibility-released | block_1 | 0/13 | 2/13 | Fail |
| compatibility-clean | full | 1/13 | 2/13 | Fail |
| compatibility-clean | block_0 | 0/13 | 2/13 | Fail |
| compatibility-clean | block_1 | 2/13 | 0/13 | Fail |
| overhead-released | full | 2/13 | 2/13 | Fail |
| overhead-released | block_0 | 2/13 | 1/13 | Fail |
| overhead-released | block_1 | 2/13 | 2/13 | Fail |
| overhead-clean | full | 2/13 | 0/13 | Fail |
| overhead-clean | block_0 | 2/13 | 0/13 | Fail |
| overhead-clean | block_1 | 1/13 | 0/13 | Fail |

All failures are write-heavy overall or append p99. Read latency, write-profile query p99, achieved-window rate, zero-loss and both memory criteria pass in every full/half scope. Passing individual criteria do not override the failed required scopes.

## Full-cohort latency

Times are medians of case p99 values. Ratios are medians of within-round pairs and therefore need not equal the quotient of displayed medians. A failed corresponding control makes the difference unqualified, including apparent improvements.

| Family | Profile/metric | A median ms | C median ms | Paired C/A | Paired B/A | Matching control |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| compatibility-released | read/overall | 1.1077 | 1.1206 | 0.994210 | 1.001441 | Pass |
| compatibility-released | write/overall | 23.0845 | 23.8261 | 1.234137 | 0.928233 | Pass |
| compatibility-released | write/append | 76.4916 | 69.7343 | 1.066161 | 0.909967 | Pass |
| compatibility-clean | read/overall | 1.1081 | 1.1195 | 1.012589 | 1.003022 | Pass |
| compatibility-clean | write/overall | 22.6101 | 29.7314 | 1.202270 | 0.943786 | Pass |
| compatibility-clean | write/append | 64.8764 | 73.3658 | 1.196921 | 0.827936 | Fail / unqualified |
| overhead-released | read/overall | 1.1067 | 1.1085 | 1.002541 | 0.997982 | Pass |
| overhead-released | write/overall | 15.0617 | 16.5252 | 1.100953 | 1.780018 | Fail / unqualified |
| overhead-released | write/append | 59.6303 | 53.6615 | 1.085313 | 1.175976 | Fail / unqualified |
| overhead-clean | read/overall | 1.0975 | 1.1183 | 1.008609 | 1.001991 | Pass |
| overhead-clean | write/overall | 30.5354 | 19.6664 | 0.858242 | 0.917608 | Fail / unqualified |
| overhead-clean | write/append | 84.1024 | 56.7790 | 0.869980 | 0.843140 | Fail / unqualified |

The released tracing build numerically exceeds its 5% write limits, while the clean tracing build appears faster. Their write controls fail, so neither establishes latency overhead or a speed gain. All slow samples remain included: **2,209 individual service samples exceed 100 ms**.

| Failed candidate criterion | Scope | Metric | Corresponding A/A |
| --- | --- | --- | --- |
| compatibility-released | full | write/overall_p99 | passes |
| compatibility-released | block_1 | write/overall_p99 | passes |
| compatibility-released | block_1 | write/append_p99 | passes |
| compatibility-clean | full | write/overall_p99 | passes |
| compatibility-clean | full | write/append_p99 | fails; unqualified difference |
| compatibility-clean | block_0 | write/overall_p99 | passes |
| compatibility-clean | block_0 | write/append_p99 | passes |
| overhead-released | full | write/overall_p99 | fails; unqualified difference |
| overhead-released | full | write/append_p99 | fails; unqualified difference |
| overhead-released | block_0 | write/overall_p99 | fails; unqualified difference |
| overhead-released | block_1 | write/overall_p99 | fails; unqualified difference |
| overhead-released | block_1 | write/append_p99 | fails; unqualified difference |

## Native resource observations

[Windows GetProcessMemoryInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo) supplies native process memory counters; [PROCESS_MEMORY_COUNTERS](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters) defines the peak working-set field. The sample before any trace getter includes native startup, seed and workload through the post-load resource sample, and excludes trace serialization and reopen. It does not isolate tracer allocation or measure full-lifetime peak RSS. Every paired ratio and additional-memory criterion passes in full and both halves.

| Family | Profile | Paired C/A peak | Median paired difference KiB | Both full memory guards |
| --- | --- | ---: | ---: | --- |
| compatibility-released | read | 0.999854 | -6.0 | Pass |
| compatibility-released | write | 0.998662 | -58.0 | Pass |
| compatibility-clean | read | 1.000147 | 6.0 | Pass |
| compatibility-clean | write | 0.997162 | -122.0 | Pass |
| overhead-released | read | 1.002159 | 88.0 | Pass |
| overhead-released | write | 1.007157 | 310.0 | Pass |
| overhead-clean | read | 1.002357 | 96.0 | Pass |
| overhead-clean | write | 1.012244 | 526.0 | Pass |

[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes) supplies charged native user/kernel CPU with a 100 ns representation unit; that unit is not measurement resolution. CPU stays diagnostic only. Many read windows report zero charged increments, so their CPU ratios cannot establish zero cost or an overhead bound. Host resource observations use the unchanged harness monitor.

## Descriptive writer observations and next experiment

Optional tracing records 22,283 append groups, 677 compactions and 688 reclamations. The post-cohort [trace analysis](benchmarks/writer-overhead-088/trace-diagnostic-summary.json) retains each group in the evidence ZIPs. It associates 205 service samples over 100 ms with 43 distinct append groups. Pooled traced enqueue-to-completed-collection p99 is 46.1861 ms. That wait excludes pre-enqueue validation and includes collection; clock domains are not aligned for an exclusive end-to-end decomposition. Recorded synchronization contributes 58.2–66.7% of summed stage time across released traced write cases and 64.1–96.7% across clean traced cases. These observations come from instruments whose write-latency overhead failed qualification: they motivate hypotheses, not attribution of uninstrumented p99 or a storage/OS cause.

Next use a new experiment number, 089 or later, to inspect default source/build differences and compare a fresh untouched 0.3.16 build with feature-disabled diagnostic sources under the same declared toolchain/flags. Preserve the original artifacts as controls. Establish default-build compatibility and calibrated write controls before revising tracer overhead or interpreting instrumented tails. Predeclare fresh complete balanced controls, retain every failed block and keep all synchronization, ACK/receipt and queue-budget contracts. No selective repeat of 088, no lower durability and no relaxed limits. A concrete writer improvement still needs all integrated native, six-profile service, memory, source/retry/crash/corruption, historical-format, competitor and restored-audit release checks.

## Preserved evidence

All raw offer/results, ACK generations, native stores, post-load snapshots, initial/final policies, smoke stores, six executables, four exact source/lock/test trees, harness changes, qualification proofs and logs remain at `D:\Codex\Kestrel\work\perf-088`. The frozen auditor is unchanged and passed on its first run. One read-only polling JavaScript syntax error stopped before any tool action; the native cohort continued uninterrupted and its record is retained. Every prior experiment, release and failure remains intact.

[Restoration instructions](benchmarks/writer-overhead-088/REPRODUCE.md), [complete inventory](benchmarks/writer-overhead-088/evidence-inventory.json), [preservation proof](benchmarks/writer-overhead-088/preservation-proof.json) and [restored audit proof](benchmarks/writer-overhead-088/restored-audit-proof.json) specify all ZIP/member CRC, SHA, size and exact-set checks. The restored tree is `D:\Codex\Kestrel\work\restored-writer-088-v2`; raw quantiles, conservation, correlations, scopes and descriptive group analysis must replay exactly without launching native processes or rerunning timing. Only regenerable Python caches are excluded and remain in the original tree. The private repository, supported engine and frozen overnight report remain unchanged; the separate profile reset is still waiting for full Codex exit.

[087 diagnostic correctness](WRITER_TRACE_087.md), [086 service regressions](SERVICE_D_086.md), [0.3.17 release requirements](RELEASE_TARGET_0_3_17.md), [complete history](BENCHMARK_HISTORY.md).

The first packaging attempt overwrote the frozen empty preparation-log copy with the completed stdout log. All 98 initial archive parts passed CRC/member hash/size/set checks, but the restored frozen-file audit correctly stopped on that log hash. Every initial archive and the failed restoration remain retained. The empty log's exact known zero-byte content is restored; completed stdout, original inventory, helper and failure log are kept separately. Corrected full archives use `benchmarks/writer-overhead-088/corrected-evidence`, with a fresh `work/restored-writer-088-v2` restoration. Binaries, sources, policy, harness, auditor, raw timing and all qualification decisions are unchanged; no native workload is rerun.
