# Isolated Archive phase repair 127

Supported main is still 0.3.16. Apply candidate.patch with git apply --unidiff-zero to an isolated supported
source copy, add merge_runs_127.rs under src and compaction_127.rs under tests.
Use feature adaptive-compaction-phase-127. The merge module is byte-identical
to experimental 122; the change is in Archive.compact_small's input collector.
It tracks ordered concatenation from already decoded/CRC-validated first-block
values, short-circuits further boundary work after a disorder, and bypasses the
merge planner when ordered. This remains inside charged compaction preparation;
the final publish monotonicity check/sort/CRCs/indexes/syncs are unchanged.

The three actual Archive integration tests cover retry/pins/reclaim/cold opens,
late corruption/truncation, and signed/equal ordered boundaries with CRC
rejection before publication. The new test uses supported grouped SQL; full
row/value/device pairing is separately checked by the independent 099 decoder
from ../compaction_merge_121 on all four final ordered stores.

Run locked offline tests in debug/release, both normal and fault-injection modes,
plus clippy --all-targets -D warnings for both feature modes. The common durable
driver from ../compaction_merge_121 is reused. All build/test/temporary paths
belong on D:. Original controller paths and policy commit are historical; choose
a fresh experiment number and regenerate declarations before reproducing.
The final test/patch here are authoritative. prepare_phase_127.py is the original
failed test generation, retained for history; do not overwrite failed evidence.
failed-test-v1.rs lacked a column type; v2 used unsupported Archive row projection.
The failed repair controller also had an artifact-path derivation assertion.
Both engine-source copies were identical to the final engine implementation.

No timed benchmark cohort was declared or run in 127. Future comparisons must
charge input/phase selection and retain original full release gates and balanced
full/both-half controls. Save concise results and useful source privately,
freshly verify remote bytes, then clear regenerable test/build outputs.
