# Write-through comparison135 — October12,2026

**REJECTED: all216 cases are independently correct, but24/144 identity checks,
35/144 guards and all6 speed goals fail. Shorter explicit sync moved cost into
writing; full whole-compaction medians are0.64–5.21% slower across six shapes.
Supported0.3.16 remains unchanged;0.3.17 is unreleased.**

This isolates [writer134](COMPACTION_WRITE_134.md) against exact131 A/B, not its
separate buffering/flag effects or whole-engine016 qualification. [133's earlier
controlled clustered gain](COMPACTION_COMPARE_133.md) remains separate.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Before/after p95 ms | Full p95 A/A |
| --- | ---: | ---: | ---: | ---: | --- |
| ordered | 5.45850 | 5.72325 | +3.43% | 10.8032/5.9122 | FAIL/inconclusive |
| clustered | 5.46350 | 5.59145 | +0.64% | 6.0314/52.4426 | pass |
| interleaved | 6.66300 | 6.98775 | +5.21% | 7.2562/7.4616 | pass |
| duplicates | 6.09060 | 6.41700 | +4.89% | 6.7334/22.5079 | pass |
| late | 6.40465 | 6.55990 | +3.96% | 6.6942/41.6088 | FAIL/inconclusive |
| extreme | 5.72275 | 6.03215 | +4.85% | 11.1571/59.5640 | FAIL/inconclusive |

Whole/prepare/write+sync median controls and whole/write+sync median guards pass
full/both halves for every shape. This is not a speed win: all6 clustered goals
(whole<=.95/write+sync<=.90) fail despite corresponding passing controls.
Median changes use medians of within-round C/A, not quotients of displayed
medians. P95 uses nearest-rank C/A and B/A quantile ratios. With12/full or6/half
samples, p95/p99/max coincide; all observations/spikes are retained.

| Shape | Paired write change | Paired explicit sync change | Paired write+sync change | Those median A/A full/both halves |
| --- | ---: | ---: | ---: | --- |
| ordered | +271.98% | -76.10% | +4.75% | pass |
| clustered | +259.48% | -76.04% | +1.64% | pass |
| interleaved | +270.65% | -75.54% | +3.73% | pass |
| duplicates | +270.39% | -74.18% | +5.98% | pass |
| late | +245.47% | -75.76% | +3.61% | pass |
| extreme | +276.80% | -76.11% | +5.43% | pass |

Every18 segment-write guard fails with passing controls. Clustered whole p95
6.0314->52.4426ms (8.694930x; A/A1.021388 passes), duplicates6.7334->22.5079ms
(3.342724x; A/A1.002525 passes) are calibrated full-tail regressions. Largest
candidate extreme59.5640ms contains56.1298ms writing; clustered52.4426ms contains
49.0223ms writing; late41.6088ms contains37.3773ms writing. This locates intervals
inside writes, not an exclusive physical-disk cause. Late full/extreme full tails
have failed corresponding controls; see every scope before generalizing.
Extreme second-half prepare guard also fails, C/A1.138891 with A/A1.028692.
Setup p95 failures remain; none were discarded as unrelated to the candidate.
[All65 failed checks](experiments/compaction_write_compare_135/FAILED_CHECKS.md).

All216 native children, controller, both owned metadata workers and both auditors
actually exited0; no forced kills. Independent full tuple/index/CRC/original
receipt/generation audits checked7,077,888 rows/169,869,312 CRC bytes. Additive
audit compared647 metadata probes against every native lifetime (139,752 pairs)
and independently checked2304 original receipt generations as declared run+1.
All frozen bytes unchanged. Ten predeclared waits handled outside-lifetime
activity; no timed case repeated, no outlier/metric selection or gate change.
Snapshot sampling cannot exclude every brief hidden task. Both explicit syncs,
ACK order and format remain. No physical power-loss/service/competitor claim.

12 fixed balanced rounds/six shapes/32x1024rows/three columns, same physicalD,
CPU8 only on owned processes,120 continuously observed clear seconds after
prep/freeze and each safety pause. Six fresh excluded preflights passed196608
rows/4718592 CRC bytes, plus idle dummy/birth classification checks. Baseline
131340/candidate134344 tests/two lints/exact wire/recovery are REUSED; no new
Rust tests/build. Initial missing-filename preparation failure is retained;
its completion preserved policy/order/binary/controller bytes before timing.
Audits began after actual cohort exit and a fresh126.25-second quiet interval.

Policy SHA256:`987702a68210395460977aa51e72e551e5e116826e9e15993e4536b4a931897a`.
Raw journal SHA256:`336c98251758371fb3e2f2c753dfe9cc6b4bfd134c3de91f1cdc2ce5b60fb1a2`.
131 SHA256:`d0bbe3f1899b333c87494d70eeaae1e5e4a65cd1dde7cf21b38c78de9c6336b5`.
134 SHA256:`78a1b5dcab8d77410881ab0040ac08ba0426a653e84c9b2b4f684eb24ae05f0f`.
[Actual controllers and independent auditors](experiments/compaction_write_compare_135/README.md).
Next test bounded buffering without write-through, keeping explicit sync/ACK/
format and all actual write+sync costs charged. Do not adopt134 or relabel short
flush time as improved durability. Original324Native/252service/42goals/153AA/
171guards plus correctness/recovery/sustained gates remain before release.
Concise failure/source privately freshly verified before native scoped completed
cleanup. No new raw bundle or historical private ref/tag/release deletion.
