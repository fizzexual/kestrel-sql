# 0.3.14: adaptive sparse SUM kernels and fewer cache writes

**The 0.3.14 adaptive sparse SUM experiment.** Cache hits avoid redundant writes; shared sparse SUM/AVG fuses into key lookup while the small cache is active at block entry, with the earlier wider mapper retained. In 21 alternating 1M-row pairs, small sparse SUM changed from 8.566 to 8.013 ms (paired ratio 0.931); wide sparse SUM changed from 12.475 to 12.179 ms (paired ratio 0.954). Fresh DuckDB scores are 58 wins/2 losses over 60 shapes. PERFORMANCE_044.md retains all results, rejected wider-fusion trials, 74 Rust tests, 4,000 SQL checks against each reference and current durable retry/crash/Parquet evidence.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PERFORMANCE_044.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
