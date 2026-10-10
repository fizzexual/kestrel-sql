# KestrelSQL 0.3.1: measured improvements and repeated comparisons

**Version 0.3.1 improves replay and compaction costs and adds publication-stage diagnostics.** `LiveArchive` combines immutable read snapshots, durable group commits, SHA-256 batch receipts, small-segment compaction and a bounded decoded-page cache. Late batches immediately contribute to new read views; exact retries do not add duplicate rows. Try the Rust and Parquet workflows, inspect current measured results, and read the primary-source design notebook.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PERFORMANCE_031.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
