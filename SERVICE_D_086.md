# Fresh D: service release check 086

Measured **October 8, 2026**, `2026-10-08T10:53:38.252438+00:00` through `2026-10-08T11:17:18.649834+00:00`. **Advance fails. Supported KestrelSQL remains 0.3.16; 0.3.17 has no justified release date.** The existing query-parser fix from isolated 061 is reused exactly; this trial makes no engine edit or release promotion.

**900,000/900,000 offered operations succeed, with zero drops, expiries or errors. All 45,072 acknowledged 100-row batches survive process reopen and independent exact SQL checks.** Full-cohort identical-binary A/A controls all pass, but candidate/A write-heavy overall p99 and append p99 exceed the fixed regression bound. Paired regressions are **15.75% / 24.32%**. The second block passes; the first block and full cohort fail. Neither a passing block nor the candidate/B diagnostic can replace the predeclared decision.

## Workload and controls

54 fresh serial physical D: stores; six rounds, three profiles, three labels. Each starts with 1M signed-i64 event rows and 64 clients. Append batches contain 100 rows, including late timestamps. Zero deliberate group delay; client queue capacity 256, expiry 2s. The two A/A labels use the **same exact executable path and SHA-256**. Candidate is unchanged `0.3.17-dev.61`. All six permutations occur once per profile, balancing pair order and positions. Each three-round block balances positions; it does not independently balance every pair order.

Primary comparison is candidate/A. B/A identity checks require p99 and window-throughput ratios in 0.90..1.10, with absolute loss difference ≤1% of offered requests. Candidate guards require p99 ≤1.10, window throughput ≥0.90, and loss increase ≤1 percentage point. All 14 checks per type must pass in the full cohort **and both blocks**. Policy, sources, binaries, relocated harness, independent auditor and order validator were frozen before timing. Three altered schedules are rejected. Two smoke stores are excluded from every gate.

Latency starts at scheduled arrival and includes client dispatch and queueing. p99 is nearest-rank `ceil(n*0.99)` over successful operations; every unsuccessful or unexecuted request is accounted separately. Table values are medians of case p99s. Paired ratios are medians of within-round ratios and need not equal the quotient of the displayed medians.

| Workload | Metric | A, ms | Candidate, ms | Paired C/A | Paired B/A | Fixed 10% guard |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Read, 2,000/s, 8s | overall p99 | 1.0903 | 1.0890 | 0.979992 | 0.990878 | ✅ Guard passes |
| Read, 2,000/s, 8s | query p99 | 1.0903 | 1.0890 | 0.979992 | 0.990878 | ✅ Guard passes |
| 25% append, 500/s, 8s | overall p99 | 12.9946 | 16.2953 | 1.157463 | 1.043887 | ❌ Regression guard fails |
| 25% append, 500/s, 8s | query p99 | 1.3213 | 1.3058 | 0.998427 | 0.989892 | ✅ Guard passes |
| 25% append, 500/s, 8s | append p99 | 40.8475 | 59.4091 | 1.243198 | 1.090132 | ❌ Regression guard fails |
| 5% append, 500/s, 60s | overall p99 | 3.5358 | 3.5400 | 0.997598 | 0.987433 | ✅ Guard passes |
| 5% append, 500/s, 60s | query p99 | 1.2925 | 1.2800 | 0.991601 | 1.001657 | ✅ Guard passes |
| 5% append, 500/s, 60s | append p99 | 15.9978 | 18.3250 | 1.018582 | 1.001735 | ✅ Guard passes |

All nine label/profile combinations lose 0 requests. Median completed throughput within the arrival window is 2,000/s for reads and 500/s for both other profiles. These capped rates are not maximum sustainable capacity. The write profile is 25% appends, not pure writes.

## Full and block decisions

| Scope | Failed identity checks | Failed candidate guards |
| --- | ---: | ---: |
| full | 0 / 14 | 2 / 14 |
| first_block | 1 / 14 | 3 / 14 |
| second_block | 0 / 14 | 0 / 14 |

The first block fails write overall p99, write append p99 and minute-mixed append p99; write append identity calibration also fails in that block. Full-cohort write overall/append regressions have passing matching A/A controls. First-block minute-mixed append regression is calibrated. The second block's pass remains visible but does not override the failure. All six rounds, large stalls and slower samples remain preserved.

## Correctness and measured write work

Every case reconciles complete seed/device groups, acknowledged versus actually committed batches, atomic batch counts/sums, exact total row count, 20 independent NumPy range windows and full native segment CRC after process reopen. Totals: **1,080 independent windows and 1,404,172,800 verified data bytes**. No uncertain unacknowledged committed batch remains. All benchmark child servers have exited; pre/post checks show no other task-owned build, copy, hash, packaging or migration workload. The fresh-profile helper stays waiting for full Codex exit. Seed, reopen, SQL/CRC validation and raw compression are outside arrival windows.

The existing 061 debug/release, SQL differential, named-retry, source, crash and compatibility qualification is **reused**, not rerun. These anonymous-append service cases add fresh ACK/atomicity/reopen evidence, not a new named-retry or forced-kill suite. OS caches may remain warm after a process reopen. No physical power-loss qualification is established.

Post-cohort diagnostic sums for the write-heavy profile:

| Label | Publication attempts | Compactions | Synchronization share of seven-stage sum | Summed catalog encoding, ms |
| --- | ---: | ---: | ---: | ---: |
| baseline_a | 5964 | 178 | 65.86% | 46.3852 |
| baseline_b | 5222 | 154 | 78.10% | 38.9646 |
| candidate | 5545 | 163 | 73.13% | 40.9039 |

Synchronization remains the largest recorded cost; catalog encoding is a small fraction. These sums include appends and compactions and **do not decompose p99 or prove a physical storage/OS cause**. The candidate changes the query parser, not publication policy; this measurement does not prove the parser caused the tail regression. Raw client-dispatch and response quantiles, all stage histograms/counts, ingest/queue/index/disk bounds and 1 Hz whole-host CPU/available-memory observations remain in the reports. Process peak RSS was not measured.

## Reproduction and next release

Exact binaries: A/B `081ed43e56d45f1c57ed10e0bebe80ad59487aa92b3215b13bbde06d74e76024`; candidate `b9f14feff962217ca8d4792a76b78bba5bebe9a7539eef18541b7338d6ebf8fc`. Python 3.12.10 / NumPy 2.2.5 are freshly recorded, including runtime executable hash. This is a new D: cohort; old C: timings, older NumPy versions and PostgreSQL results are separate evidence.

[Frozen policy](benchmarks/service-d-086/policy.json), [complete case report](benchmarks/service-d-086/paired-service.json), [independent audit](benchmarks/service-d-086/audit.json), [stage/resource diagnostic](benchmarks/service-d-086/publication-diagnostic.json), [reproduction and full-store preservation](benchmarks/service-d-086/REPRODUCE.md). Original stores, samples, failures and binaries remain in `D:\Codex\Kestrel\work\perf-086`.

Next: correlate individual service publication/compaction and writer-wait events against unchanged released and clean-core controls, with bounded diagnostics and separately declared overhead/calibration checks. Preserve synchronization, receipts and queue budgets; choose a write-path change from that evidence. Do not rerun only the failed block, erase 061/062 failures, or merge rejected 084. A complete six-profile service suite (including overload), actual engine integration, native/query, memory, source/retry/crash and compatibility gates precede supported adoption. [0.3.17 release target](RELEASE_TARGET_0_3_17.md).

The historical [60-shape analytical comparison](PERFORMANCE_046.md) and [PostgreSQL service losses](SERVICE_047.md) remain unchanged. No competitor ran here and no universal benchmark win is established. Every previous trial and release remains in [history](BENCHMARK_HISTORY.md).
