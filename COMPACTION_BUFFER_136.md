# Buffer-only compaction136 — October12,2026

**New isolated alternative passed344 fresh tests, two strict lints,16 independent
test stores, six exact legacy wire pairs and14 recovery cases. Speed remains
UNMEASURED; zero performance cases declared. Supported0.3.16 unchanged,
0.3.17 unreleased.**

[135 rejected the combined write-through/buffer strategy](COMPACTION_WRITE_COMPARE_135.md):
whole medians0.64–5.21% slower,24/144 controls,35/144 guards and all6 goals fail.
This removes WRITE_THROUGH while retaining bounded buffering, separating the
effects. Windows compaction wire<=1MiB uses an exact-size buffer; ordinary
append, larger segments and nonWindows keep64KiB streaming. Both explicit
segment/catalog syncs, rename/ACK/receipt order, format and cutpoints stay.
No unsafe code, dependency/API or global setting change. Buffering may still
regress; neither elapsed gains nor actual syscall counts have been measured.

| Fresh136 correctness check | Result |
| --- | --- |
| Normal/fault debug/release suites |86 each;344 passed; both strict all-target lints passed |
|16 independently decoded test stores |352,424 exact rows/8,458,176 CRC bytes |
|12 excluded legacy131/new136 stores |393,216 rows/9,437,184 CRC bytes; all six wire pairs byte-exact |
|14 owned publication fault/reopen cases |7 controlled exits86/7 injected IO errors87; all56 expected command exits |
|Independent recovery stores |28,672 rows/688,128 CRC bytes; original receipt generations/head preserved |

Tests retain signed boundaries, unequal unordered runs and full grouped tuple
reference results, retries/mismatch rejection, pinned snapshots, reclaim and
cold reopen. New buffer136 small2048-row and65534-row fallback stores pass in
all four modes. Fault checks retain acknowledged named input receipts; head2
before final publication/head3 afterward. IO errors poison the current writer,
old snapshot stays readable. Controlled exits are not physical power loss.
Earlier131340/134344 tests are historical prerequisites, not added to these344.
Corrected flat CLI auditor source reused; no failure in the136 attempts and
no passed identical build repeated. All source bytes unchanged after freezing.

Candidate SHA256:`9fdd3b9596901ad4e42f7b4b9a0bc63bcccd4a08d13e671ee91bb5c3d8b3b86d`.
Policy SHA256:`17f472d45bfeada3d527e82e6033d45cf04adf3aefa35c7468c490edf4e67020`.
[Actual patch/tests/controllers](experiments/compaction_buffer_136/README.md).
Future137+ qualification compares exact131A/B versus136C with full/both-half
identity and median/tail/setup/write+sync guards. All phase/input/write/flush
work charged. Original016 whole-engine324Native/252service/42goals/153AA/171guards
plus correctness/recovery/sustained service remain before adoption or release.
Concise private source/outcome freshly byte verified before native scoped
completed fixture/build removal. Useful binaries retained; no raw bundle or
historical private ref/tag/release deletion.
