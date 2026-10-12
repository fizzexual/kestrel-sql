# Isolated actual Archive lazy workspace131

Apply candidate.patch with git apply --unidiff-zero to an isolated supported
source copy, put merge_runs_131.rs under src and compaction_131.rs under tests.
Use adaptive-compaction-phase-131. The bounded merge is byte identical to122/127;
only its actual Archive caller changes. Ordered concatenation, detected during
charged CRC/read collection, constructs no merge-only ranges. Only after a
disorder are cumulative selected metadata row counts collected into ranges.
The format reader enforces exact cardinality/read length/CRC for each block.
Final publication sortedness/sort/index/CRC/sync/receipt/ACK checks stay intact.

Four fresh suites (debug/release, normal/fault-injection) passed85 each; both
strict clippy --all-targets -- -D warnings checks passed. Eight retained test
stores were independently fully decoded: ordered signed/equal boundaries and
unequal unordered runs in every mode. Existing SQL/retry/pin/reclaim/cold-open,
corruption/truncation and fault tests remain. Native compiler/code details
are in the actual controllers; all outputs/temp/test stores belong on D:.

The first inline PowerShell launcher triggered the legacy .py command matcher,
before any Cargo job. The original failed build controller is retained. The
separate fixed-file launch_phase131_v2.ps1 invokes build_phase_131_v2.py without
embedding Python paths in its parent command. Engine source never changed;
the strict task/supervisor/reset guard was kept. Another project build held
timing but did not overlap any qualification benchmark (none declared).
An external timed run held the pending independent audit/save/cleanup after
the build exited. Its actual terminal state and a new observed127-second
clear interval were checked before resuming. The first quiet waiter falsely
reported reset change because JSON coerced its UTC string into a DateTime;
the separate v2 uses DateKind String. Reset bytes were unchanged and the failed
wait source is retained. The append-only no-hash checkpoint chain was verified
only after quiet. No passed builds were repeated.

No new allocation-count measurement or elapsed gain is claimed. Do not rerun
historical controllers in place; choose new paths/numbers and current source
provenance. All input/workspace selection stays within compact_small timing.
A fresh full/both-half A/A comparison and unchanged Native/service/sustained/
recovery gates remain required before adoption. No new public API/format or
unsafe code. Supported0.3.16 is untouched;0.3.17 remains unreleased.
