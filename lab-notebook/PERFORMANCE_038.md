# 0.3.8: bounded adaptive integer grouping

**The 0.3.8 grouping experiment.** Compact integer group domains use bounded direct-address arrays, with exact shared SUM/AVG reductions and hash fallback for wider keys. In the fresh 100M-row full GROUP BY comparison, the median of three run medians changed from 5.504 s in 0.3.7 to 1.694 s; DuckDB measured 1.896 s. All results matched. PERFORMANCE_038.md includes every win/loss, raw samples, short control repeats, 63 Rust tests and current recovery/Parquet checks. No new network req/s or production-service claim is made.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PERFORMANCE_038.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
