# Compaction input reuse138 — October12,2026

**Actual allocation fix implemented; correctness and recovery passed. Speed is
unmeasured. Supported0.3.16 is unchanged;0.3.17 remains unreleased.**

Exact131 compaction creates a decoded vector per input block and byte scratch
per selected run.138 reuses one of each through the operation, then releases
them before merge/publication. For32 runs/1024rows/three columns, source temporary
lifetimes change96->1 decoded and32->1 byte scratch. Capacity can grow; this is
not measured allocator-call/syscall counts or an elapsed speedup. Original64KiB
writer remains; rejected134/136 writer changes are absent.

Existing Reader.read_block_into still performs every read/CRC/decode, and the
phase choice uses validated values. Original publish and Reader code are exact,
including final sortedness/index/output CRC, both explicit segment/catalog syncs,
rename/ACK/receipts/format/cutpoints. No public API/dependency/unsafe/cache/global
setting change. Rust documents that [clear retains vector capacity](https://doc.rust-lang.org/std/vec/struct.Vec.html#method.clear)
and [take transfers the previous value while leaving its default](https://doc.rust-lang.org/std/mem/fn.take.html).

| Completed prerequisite | Fresh evidence |
| --- | --- |
| Normal/fault debug/release |86 each,344 tests; two strict lints; actual build exit0 |
| Full independent test stores |20 stores,312252 exact rows,7494048 CRC bytes |
| Compatibility |Six exact legacy131/138 wire pairs;12 excluded cases,393216 rows |
| Recovery |14 fresh faults,56 expected commands;28672 rows,688128 CRC bytes |

New growth/shrink test crosses4095/4096/4097-row boundaries and two compactions
with late rows (final24733 rows/head13); full SQL references, original retry/
mismatch receipts, pinned old results/reclaim and cold reopen pass. Existing
late CRC/truncation, ordered signed boundaries and unequal runs pass too. Full
auditor independently checks all original tuples/indexes/CRCs/receipt digests
and generations. All original wire/catalog bytes match legacy131. Recovery uses
seven controlled owned exits86 and seven IO errors87; all acknowledged rows/
original receipts survive, head2 before publication/head3 after. IO errors poison
writer while old snapshot stays readable. This is not physical power-loss proof.

All actual controllers exited0; no passed suite repeated or unrelated process
killed. A checkpoint launch review timeout occurred before process creation;
identical retry succeeded, with no engine/test rerun. Candidate source stayed
frozen through all checks. Candidate SHA256:`b186c283da4008414214d56c7c3b527fe018664a3b5400d12d560982b2f85523`.
[Actual patch, tests and controllers](experiments/compaction_input_138/README.md).

Future139+ must predeclare complete balanced same-D131 A/B versus138 C, full/
both-half A/A and stage/whole/setup-tail guards, clustered whole<=.95 and
preparation<=.90 goals. All input/read/CRC/phase/index/write/sync costs charged;
no selected retiming/outlier removal. This source fix alone cannot qualify
0.3.17. Original324Native/252service/42goals/153AA/171guards plus retry/recovery/
sustained service remain. Useful source and short outcome privately freshly
verified before native exact completed cleanup, keeping reusable binaries.
No new multiGB raw bundle or historical private ref/tag/release deletion.
