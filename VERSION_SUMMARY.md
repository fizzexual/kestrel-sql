# Version summary — October 12, 2026

**Supported: 0.3.16. Version 0.3.17 has not been released. Work resumed at the user's request.**

New buffer-only alternative136 passed344 fresh tests/two lints,16 independent
store audits, six exact legacy wire pairs and14 recovery cases. Speed remains
unmeasured. [Code and correctness](COMPACTION_BUFFER_136.md).

Complete135 is REJECTED: all216 stores pass independent correctness;24/144
A/A,35/144 guards and all6 goals fail. Write-through moves stalls into writes;
whole medians are0.64–5.21% slower. [Complete before/after and failures](COMPACTION_WRITE_COMPARE_135.md).

Isolated bounded writer134 passed344 fresh tests/two lints,16 independent
store audits, six exact legacy wire pairs and14 publication recovery cases.
Speed was measured and rejected in135;0.3.17 remains unreleased. [Source and correctness](COMPACTION_WRITE_134.md).

Complete133 independently passed216 stores/7,077,888 rows. Clustered whole
compaction is10.80% lower and preparation29.37% lower with passing full/both-half
goals/controls. Overall7/72 A/A and1/72 guard fail; large sync tails remain.
[Before/after and every failure](COMPACTION_COMPARE_133.md).

Comparison132 passed independent correctness for all88 completed cases;128
remain unstarted. Post-case activity began after native exit but the conservative
protocol held the run. Full performance qualification is unevaluated.
[Full prefix/protocol finding](COMPACTION_PREFIX_132.md).

New isolated phase131 defers merge workspace until disorder is known.340 fresh
tests/two strict lints and eight full independent store audits pass. Combined speed is now measured in133, whose overall
qualification fails. [Code and correctness](COMPACTION_PHASE_131.md).

Comparison130 independently passed all44 completed stores but a different
PowerShell process held the remaining172 cases. No complete speed/control
qualification is available. [Full prefix outcome](COMPACTION_PREFIX_130.md).

Comparison129 stopped after seven independently correct cases when our own
read-only status query triggered the idle guard.209 timings remain unstarted;
no speed or release qualification is claimed.
[Complete prefix and harness correction](COMPACTION_PREFIX_129.md).

Fresh phase comparison128 passed six independent preflights, but a new
external build triggered the guard after cooldown. All216 timings are unstarted;
performance remains unmeasured. Supervisor detection is repaired.
[Preflight outcome](COMPACTION_PREFLIGHT_128.md).

Latest isolated Archive phase repair 127 passed 336 fresh tests, two strict
lints and independent exact row/CRC/receipt audits of all four new ordered
stores. It bypasses merge planning for already ordered input while preserving
publication checks. Performance is unmeasured; no timed cases were declared.
[Code and correctness outcome](COMPACTION_PHASE_127.md).

New isolated kernel diagnostic 126 found controlled clustered layout reductions
of 62.46% elapsed work and 65.16% thread cycles. Ordered full elapsed regressed
12.27%; 10/72 controls, 5/72 guards and 3/12 goals failed. This excludes input
reads/CRCs, indexes and durable sync; it is not a whole-database gain.
[Outcome and next code target](KERNEL_LAYOUT_126.md).

Latest randomized baseline calibration 125 independently passed all 648 stores.
51/144 identity controls failed; no candidate speedup was tested.
[Complete outcome](COMPACTION_CONTROLS_125.md).

New baseline calibration 124 passed all 648 independent correctness checks,
but 24/144 identity controls failed despite fixed CPU placement. No engine
candidate was involved. [Timing investigation](COMPACTION_CONTROLS_124.md).

Latest component trial 122 passed 332 fresh candidate tests and all 216
independent correctness checks. 24/72 A/A controls and 10/72 guards fail;
it remains experimental. Trial 121's controlled clustered compaction gain was
12.0%, with outstanding regressions. [Latest result](COMPACTION_MERGE_122.md).

KestrelSQL is a Rust embedded analytics prototype with BIGINT SQL, exact range
aggregates, immutable archive snapshots, checksummed segments and retryable
batch ingestion. Transactions belong to its separate RAM-resident Database API.
Existing source, tests, dependencies and supplied binaries remain unchanged.

Isolated development now contains workload-dependent collection phases,
selective filter/range paths, replay lookup, grouped-range scans, buffered receipt
hashing, and a publication index builder selected by actual row count. These
are experimental; rejected changes have not been promoted into supported code.

Latest full qualification trial 120 passed 836 fresh tests, five strict lints, 359 recovery commands
and correctness for all 324 Native cases. Performance failed 84/153 A/A controls,
22/171 regression guards and 7/42 goals. All 252 service cases remain unstarted.
It cannot qualify 0.3.17.

| Controlled late grouped query | 0.3.16 | Combined candidate | Paired reduction |
| --- | ---: | ---: | ---: |
| Median latency | 9,701.00 us | 6,713.25 us | 18.80% |
| p95 latency | 13,337.95 us | 9,885.95 us | 25.01% |

Both goals and controls pass in the full run and both halves. Paired reductions
use within-round ratios. They do not isolate the latest code change. Calibrated
regressions include ordered aggregate p95 (+19.23%).

Historical warm analytic comparisons recorded 60/60 median wins against DuckDB
in their tested subset, with different layouts/API boundaries. The PostgreSQL
service comparison still loses mixed and append p99. We do not win every
benchmark. Physical power-loss qualification is also absent.

Release still needs reproducible performance without material regressions,
followed by complete controlled service, sustained-load and recovery gates.
No evidence supports a reliable release ETA.

Completed runs are represented by concise Markdown. Existing full evidence and
failed attempts remain in private GitHub history, without history rewriting.
Continuation has been authorized again; Actions has a verified account-wide $0 cap
with Stop usage enabled. [Cleanup](STORAGE_CLEANUP_FINAL.md),
[latest trial](ADAPTIVE_ENGINE_120.md), [history](BENCHMARK_HISTORY.md).
