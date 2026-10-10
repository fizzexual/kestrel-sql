# Version summary — October 10, 2026

**Supported: 0.3.16. Version 0.3.17 has not been released. Work resumed at the user's request.**

New component trial 121 passed 478 tests and independently checked all 216 cases.
Clustered compaction wall improved 12.0%, preparation 35.6%, with full/half
controls. Nine controls/three guards still fail; it is experimental.
[Short result and remaining failures](COMPACTION_MERGE_121.md).

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
