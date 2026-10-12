# Reproduce isolated payload147

Apply candidate.patch to supported016 with git apply --unidiff-zero. Copy
merge_runs_131.rs to src and compaction_147.rs to tests. Feature:
reuse-compaction-payload-147. Original compaction_stage_121 driver and099
independent decoder apply. Use fresh numbers/paths, never rerun historical147.

348 fresh tests/two lints,52 complete independent stores, six exact supported
wire pairs and14 recovery cases pass. Performance is unmeasured; no adoption.
Payload-only-change.patch isolates the delta from144. Read policy for capacity,
unchanged flush/sync/fault semantics, acceptance and primary Rust documentation.
Every actual source and first held recovery attempt is preserved. No raw bundle.
