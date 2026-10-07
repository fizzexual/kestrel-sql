# Fresh 0.3.16 service qualification: read speed, write stalls and overload

This is post-release qualification of the unchanged 0.3.16 engine, not a new engine release or a version-to-version performance improvement. The 046 analytical matrix remains separate: 60 DuckDB median wins/0 losses over 60 supported shapes, with a modest closest-case margin. This report adds current service evidence and preserves failures.

52 serial fresh million-row cases offered **1,327,600 operations**. The audit recomputed accounting and percentiles from **1,199,823 executed raw request samples**, including unsuccessful executions. No build or another heavy job overlapped timed loads. All task-owned database processes were shut down afterward.

## Current six-engine comparison

Three rotated rounds per engine; 64 clients; 2,000 offered requests/s for 8 seconds per case; 95% timestamp-window COUNT/SUM queries and 5% synchronized 100-row appends. Five percent of append timestamps are late. One request is one query or a whole 100-row append. Values below are medians of the three run p99 values, not pooled percentiles. Successful-request latency starts at the scheduled arrival; failed, dropped and expired requests are reported separately.

✅ means Kestrel had a lower median run p99 for that column; ❌ means the reference had a lower value. These marks apply to this workload and interface comparison.

| Engine/version | Mixed p99 ms | Read p99 ms | Append p99 ms | Lost/failed out of 48,000 | Zero-loss ≤100 ms mixed-p99 runs |
|---|---:|---:|---:|---:|---:|
| kestrel 0.3.16 | 39.208 | 1.205 | 412.905 | 0 | 3/3 |
| postgres 17.6 | 13.686 ❌ | 2.892 ✅ | 173.930 ❌ | 3,184 | 2/3 |
| mysql 8.4.11 | 44.210 ✅ | 26.021 ✅ | 175.632 ❌ | 1,142 | 2/3 |
| mariadb 11.8.9-MariaDB | 113.971 ✅ | 97.806 ✅ | 519.204 ✅ | 6,005 | 1/3 |
| sqlite 3.49.1 | 3.711 ❌ | 0.959 ❌ | 853.444 ✅ | 0 | 3/3 |
| duckdb v1.5.6 | 75.798 ✅ | 75.698 ✅ | 81.148 ❌ | 2,868 | 2/3 |

By that declared median metric, Kestrel has **3 wins/2 losses for mixed p99**, **4 wins/1 loss for read p99**, and **2 wins/3 losses for append p99**. PostgreSQL and SQLite beat its mixed p99; SQLite beats its read p99; PostgreSQL, MySQL and DuckDB beat its append p99. Kestrel and SQLite lost no offered requests in this 18-case comparison. The arrival rate caps throughput near 2,000/s, so small endpoint differences in completed requests do not establish capacity superiority.

All per-round outcomes and within-round ratios are retained below. A median of run p99 values can disagree with the number of faster rounds because stalls differ across time.

| Reference | Mixed p99: Kestrel faster rounds | Read p99: faster rounds | Append p99: faster rounds |
|---|---:|---:|---:|
| duckdb | 3/3 | 3/3 | 1/3 |
| mariadb | 2/3 | 3/3 | 2/3 |
| mysql | 3/3 | 3/3 | 1/3 |
| postgres | 2/3 | 3/3 | 1/3 |
| sqlite | 0/3 | 0/3 | 2/3 |

Kestrel mixed p99 ranged from 5.848 to 87.374 ms, while its append p99 ranged from 217.452 to 461.765 ms. The same current binary failed identical short loads in the earlier policy runs. The three successful comparison rounds therefore do not establish a sustained service envelope.

## Initial sweep and failed soak

| Profile | Clients | Offered/s | Seconds | Successful/s in arrival window | Mixed/all p99 ms | Append p99 ms | Lost/failed |
|---|---:|---:|---:|---:|---:|---:|---:|
| read | 64 | 500 | 8 | 500.000 | 1.228 | n/a | 0 |
| mixed | 1 | 500 | 8 | 500.000 | 88.020 | 112.347 | 0 |
| mixed | 64 | 2000 | 8 | 1999.750 | 4.480 | 245.512 | 0 |
| mixed | 64 | 10000 | 8 | 7335.250 | 201.031 | 1597.374 | 21,084 |
| write | 64 | 500 | 8 | 499.875 | 145.841 | 222.369 | 0 |
| scan | 64 | 200 | 8 | 199.875 | 690.515 | 1125.736 | 0 |
| mixed | 64 | 500 | 60 | 233.517 | 6493.596 | 9044.115 | 15,925 |

The 60-second 500/s soak failed: **15,925/30,000 lost or failed**, comprising 13,883 queue drops, 1,948 expired requests and 94 append timeouts. All 604 acknowledged batches survived cold reopen. Another 94 timed-out batches had committed wholly. A timeout is an unknown outcome; identified receipts are needed for safe retry. This workload used anonymous appends to preserve the common historical/reference interface.

## Where publication time accumulated

Stage counts, histogram bins and totals are differenced against the diagnostic state after fixture setup and before the arrival window. Lifetime maxima include seed setup and are not treated as timed-window maxima. The failed soak performed no compaction.

| Failed-soak publication stage | Observations | Total ms |
|---|---:|---:|
| prepare | 24 | 8.946 |
| segment_write | 24 | 1044.600 |
| segment_sync | 24 | 25699.920 |
| catalog_encode | 24 | 0.160 |
| catalog_write | 24 | 1915.349 |
| catalog_sync | 24 | 32999.290 |
| catalog_rename | 24 | 1244.486 |

Segment/catalog synchronization contributed **93.30%** of these seven stage totals. This identifies measured waiting in the code, not its physical cause. Read service p99 in the failed soak was 3.731 ms, versus 1946.114 ms from scheduled arrival; client queueing behind blocked writers matters.

## Existing coalescing policies: exploratory repeats

All three options use the same 0.3.16 binary and unchanged synchronization-before-ACK contract. Three rotated fresh stores per profile/policy. These are configuration experiments, not candidate software or before/after version pairs.

| Profile/offered rate | Delay | Median successful/s | Median run p99 ms | Median append p99 ms | Lost/failed |
|---|---:|---:|---:|---:|---:|
| mixed/2000 | 0 ms | 1149.875 | 1052.058 | 3748.823 | 18,945/48,000 |
| mixed/2000 | 2 ms | 1889.250 | 383.881 | 927.005 | 7,028/48,000 |
| mixed/2000 | 8 ms | 1999.750 | 48.178 | 166.804 | 894/48,000 |
| mixed/10000 | 0 ms | 9560.250 | 102.686 | 255.762 | 17,327/240,000 |
| mixed/10000 | 2 ms | 9665.250 | 88.606 | 213.437 | 15,161/240,000 |
| mixed/10000 | 8 ms | 9643.625 | 89.547 | 190.875 | 7,712/240,000 |
| write/500 | 0 ms | 499.750 | 115.948 | 197.252 | 3,688/12,000 |
| write/500 | 2 ms | 499.750 | 373.865 | 540.877 | 3,465/12,000 |
| write/500 | 8 ms | 499.250 | 320.804 | 402.436 | 3,520/12,000 |

**Decision: retain zero delay as the default.** Optional waiting did not consistently fix write-tail/loss failures. All three policies failed the final write-heavy round; every 10K/s round lost requests. Some 8 ms outcomes improved, while others regressed badly. These outcomes and temporal variability do not qualify a promoted policy or an engine improvement.

## Environment, correctness and preserved evidence

The laptop initially had only 687 MB free. Two validated maintenance passes removed only old regenerable Cargo debug outputs, preserving release outputs, source, logs, raw reports, all test stores and immutable ZIPs. Free space rose to about 2.8 GB before the initial sweep and about 9.0 GB before the policy/reference phase. Results before and after this maintenance are labelled separately; freeing space alone did not consistently resolve stalls. Other processes were neither stopped nor attributed as the cause. A single passive formatted Windows-counter snapshot was insufficient for device-level attribution.

The audit checked **66,569 acknowledged batches**, 1,040 independent final NumPy reference windows, whole batches and exact sums in every case. It also reconciled 171 uncertain committed batches. All **37 Kestrel cases** underwent process restart and a full scrub, totaling **1,020,775,200 verified bytes**. Reference engines were checked through fresh connections after workload completion; their servers were shut down normally after the comparison, not crash-qualified by this report.

All 26 qualified engine/source files and seven supported binaries match the frozen released 0.3.16 baseline and existing qualification hashes. The existing 046 results remain 77 debug/77 release Rust tests, 4,000 SQL comparisons against each DuckDB/SQLite reference, publication/source injected failures and forced kills. No new engine change justified repeating those full suites here. This run adds load reconciliation and evidence-accounting checks; it does not add physical power-loss or production qualification.

The workload uses supported integer COUNT/SUM windows, different physical indexes and Kestrel’s loopback JSON test bridge versus native Python reference interfaces. It excludes authentication, distributed traffic, replication, failover, broad SQL and long endurance. No Facebook-scale or universal-database claim follows.

## Reproduce and inspect

Use this computer and run each command serially. The exact per-phase harness copies are preserved because disk guards and the reference ordering were added after the initial sweep. Choose a fresh output name; the drivers refuse to overwrite existing reports. The 0.3.16 package stays immutable.

```powershell
$env:PYTHONPATH='C:\Users\Frizer\Documents\Codex\2026-10-05\letys\work\stress-deps;C:\Users\Frizer\Documents\Codex\2026-10-05\letys\work\python-deps'
python benchmarks/service-047-baseline-harness.py --mode baseline --rounds 1 --output benchmarks/service-047-baseline-new.json
python benchmarks/service-047-policy-harness.py --mode policy --rounds 3 --output benchmarks/service-047-policy-new.json
python benchmarks/portable_servers.py start
python benchmarks/service-047-reference-harness.py --mode reference --rounds 3 --output benchmarks/service-047-reference-new.json
python benchmarks/portable_servers.py stop
python benchmarks/audit_service_047.py
```

The audit command checks the canonical preserved 047 reports, not newly named runs. If a comparison fails, always stop only the task-owned servers after verifying their data directories. Do not compile, rebuild, package or run another heavy job during timing.

- [Audit, recomputed metrics and per-round ratios](benchmarks/service-047-audit.json)
- [Initial sweep and failed 60-second soak](benchmarks/service-047-baseline.json) · [every raw request sample](benchmarks/service-047-baseline-samples/)
- [All 27 coalescing cases](benchmarks/service-047-policy.json) · [every raw request sample](benchmarks/service-047-policy-samples/)
- [Current six-engine comparison](benchmarks/service-047-reference.json) · [every raw request sample](benchmarks/service-047-reference-samples/)
- [Exact baseline harness](benchmarks/service-047-baseline-harness.py), [policy harness](benchmarks/service-047-policy-harness.py), [reference harness](benchmarks/service-047-reference-harness.py)
- [Frozen released baseline provenance](benchmarks/baseline-0.3.16-provenance.json), [qualification](verification-v046.json)
- [First maintenance record](benchmarks/service-047-space-maintenance.json), [second record](benchmarks/service-047-space-maintenance-2.json), [preparation and preserved display failure](benchmarks/service-047-preparation-notes.json)
- [Research-backed next publication-format hypothesis](PUBLICATION_EXPERIMENT.md), [previous unpromoted I/O primitive trials](benchmarks/sync-037-io-audit.json)
- [Released 0.3.16 package](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.16), [all 20 immutable historical releases](https://github.com/fizzexual/kestrel-sql/releases)
- [Prior 0.3.1 six-engine evidence](PERFORMANCE_031.md), [current separate analytical matrix](PERFORMANCE_046.md)

[Download the supplemental 047 evidence ZIP](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-0.3.16-service-047-evidence.zip) with the new reports, all raw samples, exact harnesses and frozen baseline. This supplements the immutable engine ZIP; it does not replace it.
