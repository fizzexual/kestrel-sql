# KestrelSQL 0.3.3: bounded receipt deltas and checkpoints

In the 0.3.3 receipt-catalog experiment, 50,000 retained retry IDs and 96 new appends wrote 24.72 MB of catalogs versus 788.02 MB in the fresh 0.3.2 baseline (96.86% fewer bytes). CAT4 uses receipt deltas and bounded checkpoints, preserves synchronization before ACK, reads older catalogs and is rejected by pre-CAT4 writers. Checkpoint/storage stalls and service-target failures remain disclosed.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PERFORMANCE_033.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
