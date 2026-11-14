# Reproduce the isolated144 source

Apply candidate.patch to supported016 with git apply --unidiff-zero, copy
merge_runs_131.rs to src and compaction_144.rs to tests. Feature:
reuse-publish-extrema-144. The smaller index-only-change.patch shows the delta
from exact131. Use original compaction_stage_121 driver/independent099 decoder.
Use new experiment numbers/current provenance and paths; never overwrite or
rerun these completed cases. Base64 sources preserve exact failed CRLF bytes.

Correctness344/two strict lints, all28 independent stores, six supported016
wire pairs and14 publication recovery cases passed. Read the parent concise
COMPACTION_EXTREMA_144.md and FAILED_ATTEMPTS.md for limits and every hold.
No performance cases declared or speed/release qualification.
