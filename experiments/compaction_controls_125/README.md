# Random balanced control calibration 125

All A/B/C labels use the same supported 0.3.16 executable, not the candidate.
The shared driver and independent decoder are in ../compaction_merge_121.
The preparation source specifies all 648 cases and one RNG seed 20261010;
each six-round block uses every permutation once for every input shape.
The common driver only accepts seeds 1..12, repeated over 36 distinct rounds.
The auditor indexes timings by round and input rows by seed.

These are the actual sources, including the global build check added before
the freeze. The preparation script derives controller copies from the retained
124 root-work sources; use the published run/audit/smoke sources here instead
when reproducing. Its fixed source commit and previous cleanup proof describe
the original local workspace. Build the common driver from unchanged supported
source, regenerate declarations with a new experiment number and current paths,
and independently verify the declared schedule and executable before timing.
Do not rerun or overwrite trial 125. Check reset/task state and visible builds,
then use a 120-second cooldown. Only the controller and inherited children
use logical CPU8; restore the controller mask afterwards. All source checks,
builds, copies and hashes precede timing; payload audits follow actual exit.

Concise outcomes and useful source are retained privately. Completed fixtures
are cleared only after fresh byte-exact remote verification, without a raw ZIP.
