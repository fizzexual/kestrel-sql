# Reproduce isolated contiguous150

Apply candidate.patch to supported016 using git apply --unidiff-zero; copy
merge_runs_131.rs to src and compaction_150.rs to tests. Feature:
contiguous-compaction-payload-150. Original121 driver and099 independent
decoder apply. Use fresh paths/numbers; never rerun historical150. Actual
source, fixed untimed policy and complete correctness/wire/recovery proofs
saved.348 fresh tests/two lints/52 stores/six wire pairs/14 recovery cases pass.
Speed unmeasured, no adoption. See declaration clarification; no raw bundle.
