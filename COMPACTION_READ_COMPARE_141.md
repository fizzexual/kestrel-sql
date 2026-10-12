# Bounded-read comparison141 — October12,2026

**REJECTED:216 independently correct stores,20/144 A/A,15/144 guards and4/6
goals fail. Eight failed guards have passing controls. Supported0.3.16 remains
exact;0.3.17 is unreleased.140 is not adopted.**

Exact131 A/B versus [bounded reads140](COMPACTION_READ_140.md) isolates input
coalescing/direct decode on original64KiB writer. No rejected138 reuse or134/
136 writer code. This component cannot qualify whole-engine/service release.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Paired prepare change | Before/after whole p95 ms | Full p95 A/A |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| ordered | 5.49810 | 5.19815 | -4.98% | -14.15% | 5.7109/6.9718 | pass |
| clustered | 5.49210 | 5.23580 | -2.00% | -12.48% | 6.1000/6.2375 | pass |
| interleaved | 6.70065 | 6.75220 | +1.08% | -0.33% | 10.7537/8.4600 | FAIL / inconclusive |
| duplicates | 6.19675 | 5.99950 | -0.95% | -10.63% | 6.7310/6.6149 | pass |
| late | 6.15550 | 6.07090 | -0.86% | -5.37% | 7.5049/46.0325 | FAIL / inconclusive |
| extreme | 5.78135 | 5.68985 | -0.16% | -2.77% | 5.9314/6.0564 | pass |

Clustered full preparation is12.48% lower, first-half3.94% lower, second-half
14.41% lower. Full/second preparation goals pass; first-half fails10%. Whole
time is2.00% lower full,+2.91% first-half,-2.12% second-half, missing all three
5% goals. Corresponding controls pass. Full/both-half qualification therefore
fails. Displayed p50 quotients differ from medians of paired within-round ratios;
do not combine these ratios with133's separate combined131-versus016 results.

| Clustered scope | Metric | C/A | A/A | Goal |
| --- | --- | ---: | ---: | --- |
| full | wall_ms | 0.979958 | 0.987240 | FAIL |
| full | prepare_ms | 0.875246 | 0.976978 | pass |
| first_half | wall_ms | 1.029144 | 0.981733 | FAIL |
| first_half | prepare_ms | 0.960609 | 0.947385 | FAIL |
| second_half | wall_ms | 0.978751 | 1.032611 | FAIL |
| second_half | prepare_ms | 0.855918 | 1.015623 | pass |

All whole/prepare median controls pass.107/108 median controls pass overall;
one catalog-sync median/four whole-p95/15 setup-p95 controls fail. Ordered full
p95 is5.7109->6.9718ms,1.220788x with passing A/A0.973402. Late apparent full
p95 loss6.133659x has failed A/A0.894549 and is inconclusive. Interleaved full
apparent tail gain also has failed controls. Every stall stays; these intervals
do not identify an exclusive disk/allocator cause. The eight calibrated guards:

- ordered, full, wall_p95_ms: C/A1.220788, A/A0.973402.
- ordered, second_half, wall_p95_ms: C/A1.233860, A/A0.981099.
- clustered, first_half, wall_p95_ms: C/A1.108987, A/A0.965988.
- clustered, first_half, setup_p95_ms: C/A1.310442, A/A0.977705.
- interleaved, first_half, wall_p95_ms: C/A1.246244, A/A1.048627.
- duplicates, second_half, segment_write_ms: C/A1.111357, A/A1.012830.
- late, first_half, catalog_sync_ms: C/A1.127993, A/A0.987661.
- late, second_half, setup_p95_ms: C/A1.404614, A/A1.014796.

[Every39 failed check](experiments/compaction_read_compare_141/FAILED_CHECKS.md)
includes every identity/guard/failed goal. No discarded outliers, retiming or
threshold changes. Whole/setup p95 uses nearest-rank quantile ratios with12/full
or6/half samples=max. Both explicit syncs/receipts/ACK/format remain; no physical
power-loss proof. Preparation improves in several shapes; interleaved full
change is only-0.33%. Further read/merge/index profiling is needed to locate
the remaining costs; that difference alone is not an exclusive cause.

All216 native children/controller/two metadata workers/two auditors actually
exited0. Independently checked7,077,888 exact rows/169,869,312 CRC bytes, indexes,
head and original receipts. All457 probes vs every216 native lifetime (98,712
pairs),2304 original generations from declared run+1. Frozen sources/decoder/
binaries exact; zero actual pauses, all samples once. No failed timing/audit attempt. Publication attempt1 failed before commit
on extra CRLF EOF lines in three analysis helpers; separatev4 preserves exact
failed bytes/source/exit and normalizes those lines without changing results.
[Saved publication failure](experiments/compaction_read_compare_141/FAILED_PUBLICATION.md).

Complete216 same-D cases/12 balanced rounds/six shapes/32x1024rows/three columns,
RNG20261011/all6permutations per shape per half, ownedCPU8.120 continuous
observed quiet after preparation/freezes; strict reset/task/supervisor/global
checks before/after every case. Declared outside-lifetime waits unchanged.
All input/read/CRC/phase/index/write/flush/sync charged inside compact_small.
Six excluded preflights196608rows/4718592CRC bytes and idle-dummy/five boundary
tests pass.131340/140352 tests/two lints/36 independent stores/wire/recovery
explicitly REUSED, no Rust build. Audits followed actual exit and
126.76 continuously observed clear seconds.
Snapshots cannot exclude every brief unseen task; safety waits are not DB phases.

Policy SHA256:`b3f8978bf29a365a279afd20e044db2d0527228a6358faea4be477e1ca4ee179`.
Raw journal SHA256:`40e928687bef84eb41cd14e2b26d5a7759fb7dec583ab0a01041bced413fbbaf`.
131 SHA256:`d0bbe3f1899b333c87494d70eeaae1e5e4a65cd1dde7cf21b38c78de9c6336b5`.
140 SHA256:`52bb790fb84dabbcdcffbb604e174dffd0312654f48508bebbcdf01acf9450ce`.
[Actual controllers and auditors](experiments/compaction_read_compare_141/README.md).
Short source/outcomes/failures privately fresh-byte verified before native exact
completed cleanup; useful kits and all old history/tags/releases retained.
Original324Native/252service/42goals/153AA/171guards plus correctness/retry/
recovery/sustained service remain. No component-only release/universal-win/ETA.
Use new142+ numbers for justified changes, never overwrite or selected-retime141.
