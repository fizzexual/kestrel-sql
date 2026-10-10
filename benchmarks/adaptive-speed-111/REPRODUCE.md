# Adaptive engine trial111: rejected release qualification

Supported main remains0.3.16. This isolated candidate retains107's finite
three-phase collector,109's query-shape fusion and110's borrowed durable-ID
replay path. It adds bounded query-local long-scan read-ahead: window size
depends on needed columns, payload is capped at512KiB, and short/wide/prefix/
full-verification paths retain their original behavior. Per-block CRC remains.
Six meaningful new tests include counting reads, independent RAM answers,
signed data, bounds/tails, memory, generation pins, unchanged store bytes,
corruption, truncation and failed-load invalidation. Fresh772 executions across
eight configurations, five strict lints and normal/fault artifacts passed.
Fresh359-command recovery, excluded four Native/two service smokes,48 order
checks,29 negative controls and the full66-statement pre-timing prefix passed.

All324 Native cases completed once. The pure audit exited0:479,232 ACKs and
2,921,356,800 full CRC bytes are correct. Performance failed16 of153 controls,
6 of171 guards and17 of42 goals. All252 service specs are UNSTARTED/UNTESTED.
No numerical retry, selected round/scope or changed gate was used. Five goals
pass their targets and controls in full and both halves: anonymous wall,
named wall/p99, ordered/late filter medians. Full paired improvements are about
27.49%,31.52%,10.10%,14.75% and14.70% respectively. They are specific Native
results against0.3.16, not universal wins or complete release qualification.
Grouped full median paired improvements6.12% ordered and4.92% late miss the
declared10% goals. Group p95 half controls fail; no robust grouped goal passes.
Calibrated guard misses remain for sparse-anonymous p95 half1, pressure-anonymous
p99 half2, and late narrow-window median/p95 half2. Causes are not established.
Clock metadata QPC10MHz/100ns suggests short-interval quantization sensitivity;
it proves no exclusive failure cause and asserts no Rust clock implementation.
Both denied first metadata write and unchanged successful metadata helper/log
are retained. An unexecuted closure-output draft and its exact refinement are
also retained. They changed no source, Native result or performance gate.

Verify ZIP SHA sidecars and member CRC/order/offset/size. Restore64MiB chunks
from80MiB logical parts using archive-layout.json and all directory entries.
Check every original/restored file SHA,size and file/directory set before and
after importing audit_complete_111_v3 solely from the restored tree with
Python3.12.10/NumPy2.2.5. audit(ABSOLUTE_RESTORED_PATH) must exactly equal
complete-audit-proof.json without Native,timers or existing-file writes.
All42 goals,171 comparisons,153 controls,171 guards and252 unstarted service
specs are independently replayed with complete source/build/recovery/smoke
provenance. Only inventoried regenerable target/Python caches are excluded;
originals remain. Final closed preserver log is supplemented after actual exit.
No complete private GitHub raw backup is verified; no raw deletion is allowed.
This is not a supported0.3.17 release or a fresh competitor comparison.
