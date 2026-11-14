# Compaction merge 122 — experimental

Apply candidate.patch using git apply --unidiff-zero to an isolated copy of
supported 0.3.16; add merge_runs_122.rs under src and compaction_122.rs under
tests. Build offline/locked with adaptive-compaction-merge-122. Fault tests also
enable fault-injection. Reuse the identical compaction_stage_121.rs driver and
archive_audit_099.py from ../compaction_merge_121 in both candidate/baseline.
Driver inputs and receipt domain stay identical to trial 121.

Candidate now stops fragmented planning after run_count slices if their mean
width is below 64 rows. Nonpartitioned malformed keys fall back on zero
progress. Publication still checks sortedness, preserves all attached columns,
durability, receipts, CRCs and ACK order. The six tests include fragmented and
malformed input checks. Previous failures and source remain under trial 121.

Controllers retain the original run's local proof paths. Regenerate explicit
declarations/freezes for a new trial; never call old results fresh. Twelve
rounds, all six A/B/C permutations per half, identical A/B binary, six input
shapes, fixed 120-second cooldown after preparation, same controls and guards.
No builds, copies, hashing or cleanup during timing. Completed raw fixtures
are cleared only after the short private outcome and source are verified.
This component evidence does not replace full release qualification.
