# Buffer-only comparison137 — October12,2026

**REJECTED: all216 stores are independently correct, but32/144 identity checks,
13/144 guards and all six goals fail. Five failed guards have passing controls.
Supported0.3.16 stays unchanged;0.3.17 is unreleased.**

Exact131 A/B versus [bounded buffer136](COMPACTION_BUFFER_136.md) isolates
buffering without WRITE_THROUGH. It does not combine ratios across earlier
133/135 runs or qualify whole-engine/service/competitor performance.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Paired write+sync change | Before/after p95 ms | Full p95 A/A |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| ordered | 5.51545 | 5.49410 | +0.48% | +1.30% | 5.8461/6.1875 | FAIL / inconclusive |
| clustered | 5.59750 | 5.43275 | -3.15% | -4.26% | 7.0040/6.2191 | FAIL / inconclusive |
| interleaved | 7.15290 | 7.03695 | +1.76% | -2.63% | 40.7862/7.8491 | FAIL / inconclusive |
| duplicates | 6.31675 | 6.43285 | +0.49% | -2.15% | 7.8435/7.9450 | FAIL / inconclusive |
| late | 6.30170 | 6.42510 | +0.92% | -0.47% | 6.8066/7.3661 | FAIL / inconclusive |
| extreme | 5.74130 | 5.87915 | +1.86% | +1.35% | 7.6850/9.6952 | FAIL / inconclusive |

Clustered whole p50 is5.59750->5.43275ms; paired whole time is3.15% lower and
write+sync4.26% lower. Whole full/first-half/second-half ratios are0.968549,
0.956605,0.988157 with passing corresponding controls/guards. All six clustered
goals still FAIL: whole<=.95/write+sync<=.90. None of these ratios qualify release.
The other five full whole paired medians are0.48–1.86% higher.

Median changes use medians of within-round C/A, which can differ from quotients
of the displayed medians. P95 uses nearest-rank B/A,C/A quantile ratios; with12
full or6 half samples, p95/p99/max coincide. Every stall stays. All six full
whole p95 controls FAIL, so apparent full-tail gains/losses are inconclusive.
For example interleaved40.7862->7.8491ms has failed A/A1.269219; ordered baselineB
has a large stall (full p95 A/A8.751698), so neither establishes a reliable tail
improvement. Late second-half p95 has passing A/A and a calibrated loss below.
This locates measured intervals and comparisons, not an exclusive disk cause.

The five calibrated failed guards are:

- clustered, second_half, segment_write_ms: C/A1.105898, A/A1.004879.
- duplicates, first_half, catalog_sync_ms: C/A1.124759, A/A1.044306.
- late, second_half, wall_p95_ms: C/A1.149104, A/A1.033743.
- late, second_half, setup_p95_ms: C/A1.288084, A/A0.963631.
- extreme, full, prepare_ms: C/A1.131144, A/A1.038896.

[Every51 failed check](experiments/compaction_buffer_compare_137/FAILED_CHECKS.md)
includes32 identity failures,13 guards and six goals. No discarded outlier or
selected retiming. Other guard failures with failed corresponding controls are
inconclusive rather than established engine regressions.

All216 native children/controller/both metadata workers/main and additive
auditors actually exited0, no forced kills. Independently checked7,077,888 exact
rows /169,869,312 CRC bytes, all indexes, head generations and original receipts.
457 probe intervals checked against every native lifetime (98,712 pairs),2304
original receipt generations derived from declared run+1. All frozen controller,
decoder and binary bytes exact; zero actual between-case pauses. Both explicit
syncs/receipt/ACK ordering and format remain; no physical power-loss claim.

12 fixed balanced rounds/six shapes/32x1024 rows/three columns, same physicalD,
owned CPU8,120 continuous observed clear seconds after preparation/freezes.
Fresh six excluded preflights checked196608 rows /4718592 CRC bytes; owned idle
dummy busy-clear/five birth classification tests passed.131340/136344 tests,
two lints/six exact wire pairs/14 recovery cases are REUSED, no new Rust build.
No failed timing/preflight/audit attempt. Publication attempt1 failed on mixed
cleanup-helper line endings before commit; separatev2 corrects those three
lines and preserves the [actual failed source/exit](experiments/compaction_buffer_compare_137/FAILED_PUBLICATION.md). Audits followed actual controller exit and127.22 observed
clear seconds. Sampling cannot exclude every brief hidden background task.

Policy SHA256:`d6f7be41a11d8346d75b7f24929970e626b6c4501da26b47c5b85571b5de0a31`.
Raw journal SHA256:`d5f2906844aaaa91d15a74825ab1cd63ec41503a3676199ed83ca52c3d403773`.
131 SHA256:`d0bbe3f1899b333c87494d70eeaae1e5e4a65cd1dde7cf21b38c78de9c6336b5`.
136 SHA256:`9fdd3b9596901ad4e42f7b4b9a0bc63bcccd4a08d13e671ee91bb5c3d8b3b86d`.
[Actual controllers and independent auditors](experiments/compaction_buffer_compare_137/README.md).
Useful source/concise failures privately verified before exact native cleanup;
no new raw bundle or historical private refs/releases removed. Original324
Native/252 service/42 goals/153 A/A/171 guards plus recovery/sustained gates
remain. Next improvements must target measured preparation/merge/read costs
or service bottlenecks; no selected rerun of137 or unsupported adoption of136.
