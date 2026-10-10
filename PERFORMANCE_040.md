# 0.3.10: direct first-filter selection

**The 0.3.10 direct-filter experiment.** Streaming scans generate matching row positions directly from the first residual predicate. In 21 alternating 1M-row pairs, the unordered scan changed from 3.154 to 2.893 ms; seven 100M-row pairs changed from 340.939 to 318.823 ms. The fresh matched DuckDB matrix has 29 median wins and 1 loss. PERFORMANCE_040.md keeps every loss, the rejected outlining trial, checks against 0.3.8, 70 Rust tests, 1,600 SQL cases against each reference and current retry/crash/Parquet evidence.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PERFORMANCE_040.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
