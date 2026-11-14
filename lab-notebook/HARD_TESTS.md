# KestrelSQL: local concurrency and failure qualification

Historical completed-run record.

**Kestrel does not meet the tested mixed-write performance target and is not production qualified.** At 2,000 offered requests/s with 64 clients it completed 881.12/s during the arrival window, with 611.30 ms p99 among successful requests and 53.94% unsuccessful or unexecuted requests. Several reference engines sustained this offered rate with no request loss. The earlier 100M-row aggregate advantage is specific to indexed range analytics; it does not establish fast transactional service performance.

This is an executed comparison on one Windows computer, as requested. **66 cases, 933,600 offered requests, up to 64 clients**, six database engines, 1M initial rows per fresh case, plus actual process-kill and integrity tests. SQL clients are interfaces to engines; this report compares the six engines through the interfaces below. It cannot cover every SQL product.

[Complete archived report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/HARD_TESTS.md). Current qualification and limitations: [version summary](VERSION_SUMMARY.md).
