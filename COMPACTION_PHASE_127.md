# Compaction phase repair 127 — October 10, 2026

**Implemented and correctness prerequisites pass; performance is unmeasured.
Keep experimental. Supported 0.3.16 is unchanged; 0.3.17 is unreleased.**
[126](KERNEL_LAYOUT_126.md) found controlled clustered kernel gains but an
ordered elapsed guard regression (+12.27% full, +14.60% second half). This
workaround decides the ordered phase while collecting actual CRC-validated
input, avoiding a separate late probe of all run boundaries.

| Actual input | Isolated Archive behavior |
| --- | --- |
| Already ordered concatenation | Bypass merge planning; retain final publication checks |
| Unordered, sufficiently contiguous slices | Use unchanged bounded 122 merge |
| Small, fragmented or zero-progress plan | Retain original sort fallback |

The decision is derived from values, not benchmark labels, and remains inside
compact_small's charged preparation. Every selected input block is still read
and CRC checked. Row/value pairing, final monotonic checking/sort, index/CRC
construction, durable output/catalog syncs, receipts and ACK boundary are
unchanged. No public API/format/dependency/unsafe code change or deferred work.

**336 fresh complete-suite test executions pass**: 84 each in debug/release,
normal/fault modes. **Both strict clippy checks pass.** A release common-driver
artifact was built. Baseline 154 tests and executable are explicitly reused;
not fresh 127 results. Four existing merge unit tests and two actual Archive
integration tests remain, plus one new signed/equal-boundary ordered test.

The new test checks supported SQL/reference aggregates, ordered duplicate
boundaries near i64::MIN, extreme signed values, CRC rejection before catalog
publication, unchanged generation on error, receipts, pinned snapshots,
reclaim and cold reopen. A separate full wire audit of all four final stores
verified **32,776 rows and 786,624 CRC bytes**,
complete row/value/device multisets, prefix/block indexes and all original
receipt digests/generations. Build controller and auditor actually exited zero.
These tests do not establish physical power-loss behavior.

All unsuccessful work remains recorded: the first test compile lacked an
explicit Vec<Vec<i64>> type; a repair-controller path assertion failed before
starting the next build; the repaired test then used unsupported Archive raw
row projection after successful compaction. That interrupted suite had 61
passing executions and one failing test, separate from the final 336. Narrow
test repairs preserved all engine bytes. Final grouped SQL plus independent
wire decoding replace that unsupported test query; no engine feature was added
to make the query pass. Original failed test/controller source is included.
The initial publication whitespace check rejected two blank patch-context lines
before any commit; a zero-context patch repaired its presentation without
changing engine/test bytes.

**Zero timed cases were declared or run in 127.** There is no before/after
speed claim for this repair. [125's 51/144 failed durable identity controls](COMPACTION_CONTROLS_125.md)
remain unresolved. Fresh fair performance and the original full 324 Native,
252 service, 42 goals, 153 controls and 171 guards, plus relevant recovery and
sustained-service qualification, remain required before adoption. No release ETA.

[Actual patch, tests and controllers](experiments/compaction_phase_127/README.md).
Policy SHA256: `857cdafafe0742cf9875d9e263069671f7bfd6f6edb77d012c064ef53edeb98e`.
Candidate driver SHA256: `c39997c0dff47dd29683590f7501734fbb964235a712aec28d155ef3652085cd`.
Concise outcome/failures and useful source are saved privately and freshly
verified, then completed test stores/build outputs are removed. A small verified
candidate driver may be kept for the next comparison; no raw bundle is created.
