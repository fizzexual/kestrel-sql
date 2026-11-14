# Large-data qualification: KestrelSQL 0.2

Historical completed-run record.

Local qualification completed on 6 October 2026. Kestrel persists up to **100 million rows**, keeps raw values on disk, and answers exact time-window aggregates through automatically maintained indexes. This is a specialized advantage over the measured DuckDB configuration; it is not a general database ranking or production certification.

Environment: Windows-10-10.0.19045-SP0; Intel64 Family 6 Model 165 Stepping 5, GenuineIntel; 20 logical CPUs available, **one query execution thread per engine**. Machine physical RAM was approximately 31.9 GiB. Reference: DuckDB 1.5.6, Python 3.12.10; Rust 1.97.1. No CPU affinity, dedicated host, or OS-cache clearing.

[Complete archived report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/SCALE.md). Current qualification and limitations: [version summary](VERSION_SUMMARY.md).
