# KestrelSQL 0.3.4: bounded group-commit policy experiment

The 0.3.4 coalescing experiment adds an explicit `LiveOptions` window and collection diagnostics. Optional waiting can regress latency and loss, so the default remains zero delay.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PERFORMANCE_034.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
