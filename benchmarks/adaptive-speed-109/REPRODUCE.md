# Adaptive engine trial 109: rejected release qualification

Supported main remains 0.3.16. This isolated 0.3.17 candidate retains the exact
bounded three-phase collector from trial 107 and adds optional query fusion.
The public adaptive-engine feature enables adaptive-collection and adaptive-filter.
Queries choose the existing prefix path first, a fused single-column ungrouped
COUNT/SUM/AVG path when eligible, or the existing selection/group fallback.
The fused path avoids selected-position allocation and a second aggregate pass.
The same CRC-checked pages, signed predicates, exact i128 totals, snapshot pins,
durable publication, source/WAL/ACK behavior and disk formats remain protected.

724 fresh full debug/release test executions, five strict full-target lints,
independent normal/fault artifacts, the fresh 359-command recovery cohort and
excluded smoke/order/negative controls passed. All 324 Native cases completed
exactly once. Every one of 479,232 ACKs and 2,921,356,800 full CRC bytes passed the
independent row, receipt, index, query-model, quantile and provenance replay.

Release qualification failed: 27 A/A controls, eight regression guards and one
of the 24 mandatory improvement goals failed. All failures and all raw samples
remain retained. Every original trial 107 gate and all 12 small-group goals were
kept; 12 required filter goals were added before work. There were no numerical
reruns, selected rounds or retuned gates. All 252 service cases are explicitly
preserved as UNSTARTED and untested because the mandatory Native cohort failed.

Individually controlled full-run paired comparisons, also passing their controls
and targets in both halves: anonymous small-write p99 CA 0.92970506; anonymous
small-write wall CA 0.73680287; named small-write wall CA 0.67418750; ordered
filter median CA 0.88131744; late-data filter median CA 0.87851442; late-data
filter p95 CA 0.85525172. These are per-round paired ratios, distinct from a
ratio of displayed medians. Named write p99 and ordered filter p95 have failing
half controls; ordered filter p95 half 1 also misses its target. Calibrated
regressions include identified replay full p95 CA 1.09375 and late-data grouped
query half 2 p95 CA 1.08289641. Causation is not established. This is not a
fresh competitor comparison or a claim of winning every benchmark.

The first pure Native auditor invocation omitted the required workspace argument
and exited 1 before audit() ran. Its raw log is preserved. The corrected
invocation used the identical frozen auditor and gates, exited 0 and retained
the complete failed performance verdict. No Native or timer was rerun.

Verify ZIP SHA sidecars, member CRC/order/offset/size; restore 64 MiB chunks from
80 MiB logical parts using archive-layout.json and every directory entry.
Verify every original/restored file SHA, size and file/directory set before and
after importing audit_complete_109_v3 solely from the restored tree, using
Python 3.12.10/NumPy 2.2.5. audit(ABSOLUTE_RESTORED_PATH) must exactly equal
complete-audit-proof.json, without Native, timers or existing-file writes.
The replay recomputes every Native gate, all 24 goals, controlled subresults,
profile, source/build/recovery/smoke proofs and explicit service nonexecution.
Only inventoried regenerable build/Python caches are excluded; originals remain.
Final closed preserver output is supplemented after actual exit. There is no
complete verified private GitHub backup and no raw deletion.
