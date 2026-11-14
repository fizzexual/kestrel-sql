# 0.3.11: seeded sparse-group cache indexing

**The 0.3.11 seeded group-cache experiment.** Sparse GROUP BY cache indexing now uses a per-query multiplier while retaining exact key tags and randomized hash-table fallback. In 21 alternating 1M-row collision pairs, GROUP SUM changed from 18.115 to 8.972 ms. Fresh DuckDB scores are 28 wins/2 losses on matched shapes, 14/1 on prior stress shapes and 10/0 on added key patterns. PERFORMANCE_041.md retains all 55 shapes, every loss, guard measurements, 70 Rust tests, 2,200 SQL cases against each reference and retry/crash/Parquet evidence.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PERFORMANCE_041.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
