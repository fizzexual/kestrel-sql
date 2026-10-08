# Maintenance source isolation and writer qualification 090

October 8, 2026. **The isolated corrective default build passes every compatibility gate in the full cohort and both independent halves. Complete writer-tracing qualification still fails: write overall p99 A/A misses its 5% range in both halves.** All 144 cases pass correctness and no candidate numerical guard fails. Supported KestrelSQL remains **0.3.16**. This is a scoped default compatibility milestone, not an engine speed improvement, qualified low-overhead tracer, competitor sweep or 0.3.17 release.

## Implemented correction

[089](BUILD_COMPARE_089.md) identified two unconditional maintenance-result/control-flow rewrites in otherwise feature-disabled diagnostic source. Trial090 changes only an isolated copy of `src/live.rs`: mutually exclusive compile-time blocks select the original supported `match archive.compact_small()` and short-circuit reclaim condition when writer tracing is disabled, while retaining the exact corrected 087 traced maintenance statements when enabled. There is no new runtime switch. Synchronization, ACK/receipt ordering, queue budgets, maintenance frequency, pinned read views, error/poison handling and package/dependency versions are unchanged.

[Source isolation proof](benchmarks/maintenance-isolation-090/maintenance-source-isolation-proof.json) preserves the original/default/traced statement blocks and exact before/after source hashes; the complete diff is in the evidence archives. Original stock statements are compared after newline decoding; original CRLF files remain untouched and the corrected 087 LF source retains its line endings. Every other copied source/lock/manifest/example/test file is byte-exact. A new source path/compiler layout remains a causality limit: passing compatibility does not prove that these statements caused 088's regressions. All prior results, including [088](WRITER_OVERHEAD_088.md) and 089's failures, remain intact.

Both new artifacts still report version 0.3.16 for a controlled comparison. They are clearly labeled `restored-default` and `restored-writer` isolated trial artifacts; they do not replace the supported executable or constitute adoption. The baseline is the exact untouched stock-016 artifact built and preserved in 089.

## Correctness before timing

[Build proof](benchmarks/maintenance-isolation-090/build-proof.json) records **322 fresh native test executions**: default 78 and writer 83 tests each in debug/release. Five strict lint modes pass: default, publication-only, writer, fault-only and writer+fault. Two fresh D: feature targets use rustc/cargo 1.97.1, x86_64-pc-windows-msvc, offline locked existing dependencies, thin LTO/one codegen unit and incremental off, with extra ambient flags absent. No formatting, installation, dependency upgrade or network work occurred. Timed default/writer service artifacts contain no fault environment hooks; optional diagnostic fields/getters remain absent from the default artifact.

[Oracle proof](benchmarks/maintenance-isolation-090/oracle-proof.json) records **104 external native commands**. Eight sequence/oversized Archive stores across original 016, untouched stock 089 and both 090 variants are byte-equivalent; **32 full cross-reopens** and **48 independent SQLite comparisons** pass, including empty ranges and signed-i64 bounds. Ten native live modes exercise 96 named batches, exact retry/collision/empty-validation/pinned views, eight concurrent producers, a real catalog-pending-directory failure with unknown outcome and poisoning, and cold reopen/retry. Six original 016 CLI checks reopen both variants' sequential/concurrent/failure stores. Default and traced sequential stores are byte-equivalent. All three bridge variants preserve Stats fields; only the traced build accepts the empty diagnostic request and it rejects extra parameters.

All three complete setup smokes pass and are excluded from every performance gate. Four invalid orders, four resource mutations and four traced-record mutations (wrong generation/key, drop count and invalid epoch) are rejected before timing. Historical broad source/crash/process-kill qualification is reused, not newly rerun; controlled directory failures are not physical power-loss tests.

## Fixed balanced cohort

[Policy](benchmarks/maintenance-isolation-090/policy.json) was declared before source copying/edits/native work. [Timing freeze](benchmarks/maintenance-isolation-090/timing-freeze.json) records every dependency hash after correctness and before the first timed case. Twelve rounds form two independently complete six-permutation halves, balancing pair order and slot in every family/profile:

| Family | A and B | Candidate | Limits |
| --- | --- | --- | --- |
| restored-default | Exact untouched stock-016 artifact from089 | Corrected090 feature-disabled default | 088 compatibility 10% |
| restored-trace | Exact corrected 090 default artifact | Same corrected source with writer-trace enabled | 088 overhead 5% |

The **144 fresh serial stores** each begin with 1M rows and use 64 clients, 100-row anonymous batches, group delay 0, retry index 0, queue capacity 256 and 2-second expiry. Read offers 2,000/s for 8 seconds. Write offers 500/s for 20 seconds with 25% writes. Longer write windows were declared before any native work; this is a complete new cohort, not a direct 088/089 before/after comparison or selective repeat. Offered-rate caps are not measured maximum capacity.

Compatibility A/A p99/rate ranges are 0.90–1.10; candidate p99 <=1.10 and achieved-window rate >=0.90. Tracing A/A ranges are 0.95–1.05; candidate p99 <=1.05 and rate >=0.95. Zero losses are required. Native peak ratio and additional 2 MiB guards remain exactly088. Every family must pass full and both halves; C/B remains diagnostic only. Counts overlap full/half scopes and read overall/query populations and are not independent statistical observations.

The cohort ran **2026-10-08T15:48:14.354245+00:00 through 2026-10-08T16:25:20.932821+00:00**. No builds, external copying/hashing/packaging/cleanup/Git or other benchmarks overlapped. Only light status-tail reads ran alongside timing. Resource callbacks/getters/reopen/reference/CRC checks run outside each arrival/drain window. Post-run process exclusion and waiting reset-worker identity/owner checks pass before the frozen raw audit.

## Complete accounting and decisions

All **1,872,000/1,872,000 offered requests succeed**, with zero errors/loss/drop/expiry/unexecuted requests. All **179,280 acknowledged 100-row batches** survive reopen with exact atomic counts/sums and no unacknowledged-but-committed batch. **2,880 NumPy windows** and **3,886,272,000 full-CRC row-data bytes** pass. All **29,880 traced ACKs** map exactly to retained fixture keys/publication generations with complete chronology, counters/stages and zero dropped events. Every **4,965 individual service sample above 100 ms** remains in the audit. A late untraced stock baseline has overall p99 = 390.4667 ms and append p99 = 474.7500 ms, with zero loss; it is preserved and included in every applicable decision.

| Family | Scope | Failed A/A | Failed candidate | Required decision |
| --- | --- | ---: | ---: | --- |
| restored-default | full | 0/13 | 0/13 | Pass |
| restored-default | block_0 | 0/13 | 0/13 | Pass |
| restored-default | block_1 | 0/13 | 0/13 | Pass |
| restored-trace | full | 0/13 | 0/13 | Pass |
| restored-trace | block_0 | 1/13 | 0/13 | Fail |
| restored-trace | block_1 | 1/13 | 0/13 | Fail |

Default compatibility passes every required scope. Across the complete study, **2/78 A/A checks fail and 0/78 candidate guards fail**. Both failures are tracing-family write overall p99: paired B/A=0.902647 in the first half and1.059271 in the second. Its full control=1.007443 passes because the deviations have opposing directions; that cannot override the required half failures. Read, write-query/append, rate, loss and both memory criteria pass every full/half scope. Complete tracing overhead remains unqualified.

## Full-cohort observations

Times are medians of case p99 values; ratios are medians of within-round pairs and need not equal the quotient of displayed medians. Passing compatibility does not establish a speed gain.

| Family | Profile/metric | A median ms | C median ms | Paired C/A | Paired B/A |
| --- | --- | ---: | ---: | ---: | ---: |
| restored-default | read/overall | 0.9974 | 1.0005 | 1.007701 | 0.986058 |
| restored-default | write/overall | 8.1863 | 8.2323 | 1.016062 | 0.982136 |
| restored-default | write/query | 1.2717 | 1.2955 | 1.007963 | 1.011246 |
| restored-default | write/append | 14.3913 | 14.6491 | 1.009796 | 0.983962 |
| restored-trace | read/overall | 1.0013 | 0.9966 | 0.999246 | 1.011588 |
| restored-trace | write/overall | 8.4076 | 7.9295 | 0.979034 | 1.007443 |
| restored-trace | write/query | 1.2671 | 1.2662 | 0.994522 | 1.010295 |
| restored-trace | write/append | 14.3240 | 14.2803 | 1.008033 | 1.005453 |

The corrected default's paired write overall p99 is 1.016062 (about 1.6% higher) and append p99 is 1.009796 (about 1.0% higher), with passing 10% controls and full/half guards. The tracer's apparently lower full write overall p99 is not a qualified gain or complete overhead bound because the independent half calibration fails. This study supplies no new competitor ranking and omits minute/mixed/overload/scans and the full integrated release matrix.

## Native resources and measurement limits

[GetProcessMemoryInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo) and [PROCESS_MEMORY_COUNTERS](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters) provide native peak working set. The sample includes startup/seed/workload through the post-load sample before trace serialization/reopen; it does not isolate allocations or measure full-lifetime peak RSS. Every full/half memory criterion passes. The traced full write paired peak ratio is 1.013953, within its fixed guard.

| Family | Profile | Paired C/A peak | Median paired difference KiB | Both full guards |
| --- | --- | ---: | ---: | --- |
| restored-default | read | 1.001228 | 50.0 | Pass |
| restored-default | write | 0.999590 | -18.0 | Pass |
| restored-trace | read | 0.999803 | -8.0 | Pass |
| restored-trace | write | 1.013953 | 608.0 | Pass |

[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes) supplies native charged CPU with a 100 ns representation unit, not guaranteed resolution. CPU remains diagnostic; zero read increments do not prove zero cost. Failed complete write-overhead qualification prevents exclusive interpretation of traced stalls as uninstrumented p99, a physical disk/OS cause or an end-to-end decomposition.

## Preserved evidence and next work

**64 bounded archive parts preserve 14,037 files/4,218,104,916 logical bytes.** Complete ZIP/member CRC/SHA/size/exact-set checks, original-byte revalidation, exact frozen raw-audit replay and post-replay member checks pass. The independent restored tree is `D:\Codex\Kestrel\work\restored-maintenance-090`; raw quantiles/conservation/resources/trace relations/all full/half decisions replay exactly with **zero Native launches or timing reruns**. [Inventory](benchmarks/maintenance-isolation-090/evidence-inventory.json), [preservation proof](benchmarks/maintenance-isolation-090/preservation-proof.json), [restored audit](benchmarks/maintenance-isolation-090/restored-audit-proof.json) and [instructions](benchmarks/maintenance-isolation-090/REPRODUCE.md) make all evidence reviewable.

Every raw result/store/test/oracle/smoke/source/binary/lock/log/proof/helper remains at `D:\Codex\Kestrel\work\perf-090`. Only regenerable target/Python caches are omitted with explicit path/size inventory; originals remain intact. The first preparation assertion expected reclaim as a separate if rather than the original && short-circuit. It failed before source correction or native work; its exact partial sources/policy/helper/error are preserved under failed-preparation-v1. Correctedv2 resumes with byte-identical original policy and unchanged thresholds. An earlier apply_patch context mismatch rejected atomically without mutation. The frozen native raw audit passed first try; no timed input/result or gate was edited or selectively rerun. Mutable stdout is excluded from frozen dependencies and copied only after processes end.

The source correction is now qualified for default compatibility in these two profiles. Keep it isolated pending complete integrated checks. Before relying on correlated writer traces for optimization, use 091 or later with stronger predeclared complete observations (for example, 24 rounds/two complete 12-round halves under the same limits) and exact unchanged repeated controls; preserve every090 failure. A concrete writer improvement must follow an actual measured bottleneck and preserve all synchronization, ACK/retry/source/pinned-view contracts. Do not substitute diagnostic work for an engine improvement, relax thresholds, lower durability or call passing read subsets all-benchmark wins.

Actual adoption/release still requires full native/six-profile service/minute/overload/scans/memory/source/retry/crash/corrupt/historical-format/exclusive-writer/competitor/restored-audit qualification. The supported core and frozen overnight report are byte-exact; the repository remains private/local with all history preserved. The separate fresh-profile reset is still prepared and waiting for full Codex exit, not executed.

[089](BUILD_COMPARE_089.md), [088](WRITER_OVERHEAD_088.md), [087](WRITER_TRACE_087.md), [086](SERVICE_D_086.md), [release requirements](RELEASE_TARGET_0_3_17.md), [complete history](BENCHMARK_HISTORY.md).
