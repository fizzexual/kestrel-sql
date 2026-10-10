# Next publication experiment: one immutable generation file

Historical completed-run record.

The design has now been implemented in an isolated, unreleased CAT5 development trial 048. No supported format or durability change is released by this document. The supported engine remains 0.3.16. The fresh service qualification and older primitive I/O experiment motivate testing publication I/O separately from the already improved grouping kernels.

Current publication writes and synchronizes an immutable segment, writes and synchronizes its catalog, then publishes the catalog name. The failed 60-second 047 soak spent 93.30% of the seven measured stage totals in those two synchronization stages (about 92% of the broader writer publication-call time). This identifies where time accumulated; it does not identify the underlying device, OS, filter driver or physical cause. Compaction contributed no work in that failed soak. Existing 2/8 ms coalescing policies did not consistently resolve the failures.

[Complete archived report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/PUBLICATION_EXPERIMENT.md). Current qualification and limitations: [version summary](VERSION_SUMMARY.md).
