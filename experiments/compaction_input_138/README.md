# Actual compaction input-workspace fix138

Apply candidate.patch to the byte-exact supported016 source with git apply
--unidiff-zero, copy merge_runs_131.rs to src, compaction_138.rs to tests and use
feature reuse-compaction-input-138. Same original compaction_stage_121 durable
driver and independent099 full payload/index/CRC/receipt decoder; use fresh
numbers/paths/current provenance, never overwrite these completed attempts.

This changes only the compaction input collection path on exact phase131.
It calls the unchanged CRC-checked read_block_into using a reused decoded Vec,
moves the byte scratch with mem::take between Readers and drops both before
arranging/publication. Retained segment handles, original Reader/Drop/error
code and publish code are exact. Final sortedness, indexes, output CRCs, both
explicit syncs, catalog rename, receipts/ACKs/format/faultpoints remain.
No unsafe/dependency/API/cache/global setting change.32x1024rows/three columns:
source96 decoded+32 byte-scratch lifetimes become one each; capacities can grow.
These are structural source counts, not measured allocator or elapsed numbers.

344 fresh normal/fault debug/release tests/two strict lints pass. New two-cycle
growth/shrink test covers block boundaries/late rows/full SQL/original receipts/
replay mismatch/pins/reclaim/cold reopen. All20 compaction stores independently
pass312252 exact rows/7494048 CRC bytes. This includes declared12 ordered/unequal/
growth stores181028 rows plus eight pinned/restored corruption stores. Six legacy
wire pairs pass12 excluded cases393216 rows/9437184 CRC bytes, exact remaining
segment/catalog bytes and original receipt generations from declared run+1.
Fourteen publication fault cases,56 expected commands, independent28672 rows/
688128 CRC bytes pass. Seven controlled owned exits86/seven IO errors87; cold
queries/original receipts/head2 before publication/head3 afterward. IO errors
poison writer while old snapshot remains readable. No physical power-loss proof.

Actual build/audit/wire/recovery-build/recovery controllers exit0, no forced
unrelated kills or repeated passed test suites. One checkpoint launch automatic
review timed out before process creation; identical retry appended the checkpoint.
No failed engine/build/audit/recovery case. No138 timed cases declared: SPEED
UNMEASURED. Future139+ isolates exact131 A/B versus138 C with complete balanced
same-D whole/prepare/stage/tail/setup controls; all CRC/read/input/phase/write/
sync work charged. Original324 Native/252 service/42 goals/153 A/A/171 guards,
correctness/recovery/sustained service still required before release.0.3.16
unchanged/0.3.17 unreleased; no universal-win or ETA claim. Save short outcomes/
failures/source privately, freshly verify then native scoped completed cleanup;
retain useful kit, no multiGB raw bundle or historical refs/releases removed.
