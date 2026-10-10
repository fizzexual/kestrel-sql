# 0.3.9: wider bounded grouping and typed sparse states

**The 0.3.9 sparse-grouping experiment.** Compact domains now have a 65,536-slot ceiling with the existing 8 MiB state budget and row-count guard; wider keys use typed hash states and a bounded tagged cache that disables itself for poor hit rates or higher cardinality. In the fresh 1M-row full-grouping cases, sparse keys changed from 72.40 to 24.81 ms and 5,003 compact keys from 106.96 to 17.11 ms. The matched matrix has 22 median DuckDB wins and 8 losses; an additional wide/collision/high-cardinality matrix keeps its own score. PERFORMANCE_039.md includes every loss, cache regressions, 69 Rust tests, 1,000 SQL oracle cases and current recovery/Parquet checks.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PERFORMANCE_039.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
