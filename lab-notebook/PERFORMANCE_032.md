# KestrelSQL 0.3.2: faster filtered scans, unresolved service stalls

The 0.3.2 scan experiment reduced unordered-filter median time from 6.49 to 3.69 ms on a paired 1M-row fixture, while failing repeated service targets. The 0.3.1 measurements below describe an earlier release and run; they do not describe the current service envelope.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PERFORMANCE_032.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
