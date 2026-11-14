# Bounded receipt-loader comparison, 082

**Fresh D: loader comparison:** 082 rejects the bounded bulk reader: all 20 reader goals, nine guards and 14 A/A checks fail. Peak process memory falls about 12%, but migration/recovery regress. 081 fresh correctness qualification passes 60 debug and 60 release tests, 15 injected errors, 15 owned kills and 30 independent corruptions. Supported 0.3.16 remains unchanged.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/LOAD_COMPARE_082.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
