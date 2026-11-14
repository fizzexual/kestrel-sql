# KestrelSQL 0.3.7: atomic archive-local source positions

**The 0.3.7 source-checkpoint experiment.** `SourceArchive` commits each nonempty output and its source interval in one synchronized receipt publication. Reopening recovers the resume position with its data; gaps, overlaps, stale offsets and changed retries are rejected. It adds no checkpoint file or sync and preserves CAT4/SEG2. See PERFORMANCE_037.md for measured costs, 55 Rust tests, current recovery/Parquet checks and retained write stalls, and SOURCE_INGEST.md for the SDK. This is archive-local checkpoint atomicity; distributed consumer fencing and zero-output checkpointing remain work.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PERFORMANCE_037.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
