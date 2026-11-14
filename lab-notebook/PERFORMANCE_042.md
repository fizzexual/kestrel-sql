# 0.3.12: reuse-triggered sparse GROUP BY acceleration

**The 0.3.12 medium-group cache experiment.** Sparse groups promote a wider exact-tag cache after measured key reuse, deferring allocation until the next nonempty block. In 21 alternating 1M-row wide-key pairs, GROUP SUM changed from 27.704 to 16.834 ms (paired ratio 0.616). Fresh DuckDB scores are 56 wins/4 losses over 60 shapes. PERFORMANCE_042.md retains every result, the rejected tiny-query regression, all guards, 72 Rust tests, 2,800 SQL checks against each reference and current recovery/Parquet evidence. Promoted queries allocate an additional 384 KiB on this computer.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PERFORMANCE_042.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
