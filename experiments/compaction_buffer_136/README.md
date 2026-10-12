# Untimed bounded buffer-only alternative136

Apply candidate.patch with git apply --unidiff-zero to an isolated supported
source copy. Put merge_runs_131.rs under src and compaction_136.rs under tests.
Enable adaptive-segment-buffer-136, which retains byte-exact131 phase/merge.
Windows compaction with existing wire<=1MiB uses an exact-size BufWriter;
ordinary append/larger/nonWindows retain64KiB. There is NO WRITE_THROUGH flag.
Both explicit segment/catalog syncs, rename, ACK, receipts, format and existing
faultpoints remain. No unsafe/new dependency/API/global setting change.

All344 fresh tests/two strict lints pass; all16 stores independently decoded.
Twelve excluded six-shape legacy131/new136 stores fully checked and all remaining
segment/catalog bytes exact. Fourteen new owned fault cases cover7 points times
controlled exit86/IO error87, with56 expected command exits, cold queries and
full payload/index/CRC/original receipt audits. IO errors poison the writer
while its old pinned snapshot remains readable. No physical power-loss claim.
Corrected flat CLI JSON reader reused as source; prior134/135 failures preserved
in their own reports. No failure occurred in these136 attempts.

This isolates buffering alone after135 rejected the combined flag/buffer.
Performance is UNMEASURED, zero timing cases declared. Do not infer fewer OS
syscalls or a speedup from source-level coalescing. Use fresh137+ balanced131A/B
versus136C, full/both-half controls, median/tail/setup/write+sync guards and all
input/phase/write/flush work charged. Original324Native/252service/42goals/153AA/
171guards plus correctness/recovery/sustained service still required before
adoption; supported016 unchanged/017 unreleased. Fresh paths/provenance for
reproduction; never overwrite these frozen attempts or rerun passed same builds.
Private short outcome/source fresh-byte verification precedes scoped cleanup;
no multiGB raw bundle or historical ref/release deletion.
