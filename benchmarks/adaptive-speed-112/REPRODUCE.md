# Adaptive engine trial112: rejected release qualification

Supported main remains0.3.16. This isolated candidate retains107's finite
three-phase collector,109's query-shape fusion and110's borrowed durable-ID
replay. It replaces111's window-to-scratch copy with borrowed block views in
long-scan windows:512KiB total logical payload,at most eight blocks per column,
needed-column/range-dependent selection,CRC before decoding every consumed
block,and query-local lifetime. The original pre111 Reader structure,
constructors,Drop and single-block method remain byte-exact. Short,wide,
prefix,verification and compaction fallbacks remain. There is no file-format,
WAL,ACK,publication,Cargo or inherited collector/filter/replay change.

Fresh772 executions across eight configurations,five strict lints and all
normal/fault artifacts passed. All359 recovery/corruption/legacy/byte-equivalence
native commands actually waited/exited and passed;the original preflight tool
return was unobserved across context compaction,so its shell exit is not
claimed. A fresh strict idle guard0 and independent unchanged pure recovery
auditor0 reproduce the completed proof without relaunching a workload. The
honest observation and both raw logs are retained. Excluded four Native/two
service smokes,48 order checks,29 negative controls and the complete80-statement
pre-timing prefix passed. All12,735 preexisting frozen inputs remain exact.

All324 Native cases completed once and the pure audit actually exited0:
479,232 ACKs and2,921,356,800 full CRC bytes are correct. Performance fails25/153
controls,13/171 guards and1/42 goals. Every252 service spec is UNSTARTED/UNTESTED.
Eight goals pass controls and targets in full and both halves:small anonymous
wall26.63%,small named wall31.47%/p9911.27%,replay p9512.13%,ordered grouped
median14.00%,late grouped median11.36%/p9510.58%,late filter median24.10%.
Percentages use full paired ratios. Ordered group p95/filter gains and replay
p99 remain control-inconclusive. Calibrated write tails and late all-aggregates
p95 half2 regressions remain. Causes are not established. The sole goal miss
is small-anonymous p99 half2(C/A .978975,target .95,A/A1.040604).
No selected round/scope,extra measurement,numerical retry or gate change occurred.

Verify ZIP SHA sidecars and every member CRC/order/offset/size. Restore64MiB
chunks from80MiB logical parts using archive-layout.json and all directory
entries. Check every original/restored file SHA,size and file/directory set
before and after importing audit_complete_112_v3 solely from the restored tree
with Python3.12.10/NumPy2.2.5. audit(ABSOLUTE_RESTORED_PATH) must exactly equal
complete-audit-proof.json without Native,timers or existing-file writes. All42
goals,171 comparisons,153 controls,171 guards and252 unstarted service specs
are independently replayed with complete source/build/recovery/smoke provenance.
Only inventoried regenerable target/Python caches are excluded;originals remain.
Final closed preserver log is supplemented after its observed actual exit.
No complete private GitHub raw backup is verified;no raw deletion is allowed.
This is not a supported0.3.17 release or a new competitor/universal comparison.
