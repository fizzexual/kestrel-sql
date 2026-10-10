# KestrelSQL 0.3: live ingestion and measured limits

Historical completed-run record.

**0.3 improves concurrent aggregate service and adds replayable ingestion; sustained service qualification remains a production gate.** In the final retained-handle 2,000-request/s mixed test, Kestrel completed 1,999.75 successful requests/s versus 881.12 in the 0.2 baseline. Its successful-request p99 was 134.31 ms, with 0/16,000 failed or unexecuted offers. A short local run is insufficient to qualify production service.

The final 2,000/s mixed and lower-rate broad-window analytics cases still miss the 100 ms p99 target. The single-client mixed and 10,000/s overload cases also lose work; all results are included below. These remaining failures are priorities for the next storage and scheduling experiments.

[Complete archived report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/V03_RESULTS.md). Current qualification and limitations: [version summary](VERSION_SUMMARY.md).
