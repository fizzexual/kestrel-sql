# Receipt reader CPU diagnostic, isolated development 083

**Reader CPU diagnostic:** 083 identifies parsing/map lifetime as the main anchor cost. All 108 cases and 648 phase windows pass complete ledger checks. Large parse/anchor CPU and wall controls pass in the full cohort and both halves; other diagnostic failures and short CPU windows remain visible. The diagnostic does not override the rejected full-workload candidates.

[Archived complete report](https://github.com/fizzexual/kestrel-sql/blob/bb25f1547be393a6e6607a4ce54cf179abb85666/READER_CPU_083.md). Current release status: [version summary](VERSION_SUMMARY.md). Completed local run artifacts follow the storage policy.
