# Compaction merge 121 — experimental

Supported source remains 0.3.16. This component experiment does not qualify a
release. Use git apply --unidiff-zero candidate.patch on an isolated copy of supported source, add
merge_runs_121.rs under src and compaction_121.rs under tests. Put the identical
compaction_stage_121.rs driver in baseline and candidate examples. Build/test
with --offline --locked, adding adaptive-compaction-merge-121 only for candidate.
The driver takes fresh D: path, workload and seed1..12. Use the six workloads
in the report and all six A/B/C permutations in each six-round half; A/B use
one identical baseline executable. Build, copy, hash and clean outside timing.

The preserved controllers document exact timing, input generation, ownership,
full payload/receipt/CRC checks and full/half controls. Their local proof/input
paths describe the original run; regenerate declarations/freezes for a new
experiment number. Do not reuse old outputs as fresh tests or overwrite evidence.
failed-test-v1.rs preserves the original incorrect bulk-path expectation.
Completed raw fixtures are deleted after this short result is privately saved,
as the user requested. No ZIP bundle is produced.
