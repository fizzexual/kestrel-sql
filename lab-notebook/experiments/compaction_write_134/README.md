# Isolated bounded Windows compaction writer134

Apply candidate.patch with git apply --unidiff-zero to an isolated supported
source copy. Put merge_runs_131.rs under src and compaction_134.rs under tests;
use adaptive-segment-write-134, which enables retained131 phase selection.
The unchanged durable driver/independent decoder are in compaction_merge_121.
The Windows safe OpenOptionsExt custom flag is FILE_FLAG_WRITE_THROUGH only.
No NO_BUFFERING, alignment/padding, unsafe code, new dependency or format/API
change. Only compaction and existing wire<=1MiB uses an exact-size bounded
BufWriter; ordinary append, larger payloads and nonWindows retain64KiB.
Both explicit segment sync_all and catalog sync/rename/ACK/fault points stay.

All344 fresh tests/two strict lints pass; all16 stores have complete independent
tuple/index/CRC/original receipt/generation proofs. Twelve additional excluded
correctness preflights cover every shape, comparing all remaining segment and
catalog bytes exactly against131. These are NOT performance samples.

Fourteen fresh owned recovery cases cover7 publication points times controlled
exit86/injected IO error87, with named input receipts and unordered input. All
56 commands meet expected exits. Every cold query and full independent audit
passes; head is2 before final rename and3 after publication, input rows/receipt
generations remain exact. IO error cases check poisoned writer/old snapshot.
No unrelated process killed, no physical power-loss or full service proof.
Both failed and corrected auditor/controllers remain. See FAILED_ATTEMPTS.md.

Choose new numbers/paths and current provenance for reproduction; never rerun
these frozen attempts in place. Benchmark all writes plus explicit sync and
whole compaction with same-D balanced131A/B versus134C, full/both-half identity
and median/tail/setup/write+sync guards. Benefit may move/worsen latency and is
UNMEASURED. Original016 whole-engine Native/service/sustained/recovery gates
remain required. Supported0.3.16 unchanged;0.3.17 unreleased. Concise private
save/fresh byte verification precedes native scoped completed fixture cleanup.
