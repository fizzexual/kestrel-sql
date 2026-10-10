# 0.3.13: fused dense GROUP SUM and AVG

**The 0.3.13 fused dense SUM experiment.** Dense GROUP SUM/AVG shares one exact counting and reduction pass. In 21 alternating 10M-row pairs, GROUP SUM changed from 73.730 to 66.423 ms (paired ratio 0.898); seven 100M-row pairs measured 733.970 to 666.307 ms (paired ratio 0.907). Fresh DuckDB scores are 58 wins/2 losses over 60 shapes. PERFORMANCE_043.md preserves every result and guard, 73 Rust tests, 3,400 SQL checks against each reference, signed wide JSON and current recovery/Parquet evidence.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PERFORMANCE_043.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
