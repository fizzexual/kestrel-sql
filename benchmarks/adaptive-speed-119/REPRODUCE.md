# Bounded compaction workspace trial119: rejected release qualification

Supported main remains0.3.16. The isolated candidate extends corrected117
serial query/collector/receipt improvements with a private
adaptive-compaction-119 feature. compact_small reuses one BLOCK_ROWS=4096 i64
decode Vec through unchanged CRC-first read_block_into. Its logical workspace
payload is32768bytes; allocator capacity is not claimed exact. No unsafe,
dependency, format, digest, receipt, lock, Reader, query, live writer, input
selection, output ordering, ACK timing, publication count or deferred
maintenance change. Original allocating feature-disabled code remains exact.
Archive/Cargo byte inverses and all other corrected117 source hashes pass.
Stable Vec::clear retains capacity:
https://doc.rust-lang.org/std/vec/struct.Vec.html#method.clear .
Untimed118 maintenance-gap association motivated this trial; it did not prove
exclusive CPU/IO or that allocations caused all latency failures. This combined
candidate-versus-supported016 comparison does not isolate119-versus117.

Exactly two new feature-gated compaction integration tests cover independent
RAM SQL across full/partial blocks, signed extrema and late timestamps;
repeated compaction, original receipt retry/mismatch, reopen, pinned snapshots
and reclaim; CRC and truncation late in selected inputs before publication,
unchanged catalogs/generation, then payload repair and successful compaction.
Both damaged input bytes/error messages are retained in test stores. All828
fresh test executions/eight modes, five strict lints and normal/fault artifacts
pass. All359 fresh recovery commands pass:28 publication injection/owned exit
cases,ten corruptions,two historical formats,two byte-equivalence fixtures,
256 anonymous ACKs,two named scenarios,300 cold SQL checks and69360CRCbytes.
These are not physical power-loss guarantees. Four Native/two service excluded
smokes,48 balanced order controls,six outcome negatives/two invalid orders,
normal-binary fault-hook absence and all frozen input checks pass. Every
current controller API exit is observed0. No historical failed117 build is
misclassified as a119 attempt; previous failures remain in prior archives.

All324 balanced D: Native cases ran once in12 rounds/all six orders, full and
both halves. All479232ACKs/2921356800CRCbytes pass independent complete payload,
receipt/index/digest/generation/cold SQL/raw quantile checks. Performance fails
21/153 A/A checks,
5/171 guards and
2/42 goals. All252 service cases remain
UNSTARTED/UNTESTED. Every stall/max/failing scope retained; no gate changed,
selected round retimed, engine adopted or universal/competitor ranking claimed.

Verify every ZIP SHA/member CRC/order/offset/size. Reconstruct64MiB chunks
from80MiB logical parts using archive-layout.json and exact directory inventory.
Every original/restored whole-file SHA/size/file and directory set passes
before/after importing audit_complete_119 solely from restored tree.
audit(ABSOLUTE_RESTORED_PATH) equals complete-audit-proof.json without Native,
timers or existing-file writes. All fresh prerequisites, all raw Native results,
153controls/171guards/42goals/profile/252unstarted service specifications replay.
Only inventoried regenerable target/Python caches excluded; originals remain.
Private upload alone does not permit cleanup; fresh remote full raw verification
is still required. No119 raw files deleted.0.3.17 unqualified/unreleased.
