# Native reclamation phase controls 092

**Reclamation measurement milestone:** 092 passes all native phase controls, 314 tests, both balanced halves and all 72 exact stores. File deletion accounts for about 83% of native reclaim time; this justifies a separate bounded Live cleanup candidate. Diagnostics are qualified in this scope; no engine gain or supported upgrade is claimed. All earlier failures remain preserved; supported 0.3.16 is unchanged.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/RECLAIM_PHASES_092.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
