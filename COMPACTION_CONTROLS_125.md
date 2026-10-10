# Random balanced control calibration 125 — October 10, 2026

**Controls still fail; no database speedup tested. Supported version remains 0.3.16; 0.3.17 is unreleased.**
After [124's 24/144 failed controls](COMPACTION_CONTROLS_124.md), this cohort
changes only execution order: one predeclared Python RNG seed 20261010 shuffles
workload order and permutation assignment inside six-round blocks. Each input
shape has every A/B/C order three times in each half. The same 648 input/label
multiset, 12 valid seeds repeated over 36 rounds, identical baseline executable,
D: fixtures, fixed logical CPU8 and 120-second cooldown remain.

**26/72 B/A and 25/72 C/A controls fail (51/144 total).**
All paired ratios must remain within [0.90,1.10] for wall, preparation,
segment sync and catalog sync, in the full run and both halves. Every declared
case and p50/p95/p99/max was evaluated. No selected retiming or threshold change.
These counts compare separate cohorts and do not isolate all background effects.

| Input | Full paired B/A wall | Full paired C/A wall | Both controls |
| --- | ---: | ---: | --- |
| ordered | 0.8980 | 1.0587 | FAIL |
| clustered | 0.9802 | 1.0929 | pass |
| interleaved | 1.1476 | 1.0866 | FAIL |
| duplicates | 0.9283 | 0.9746 | pass |
| late | 0.9662 | 1.0210 | pass |
| extreme | 1.0034 | 0.8570 | FAIL |

All failed checks: B/A ordered full wall_ms 0.8980; B/A ordered full prepare_ms 0.8926; B/A ordered first_half catalog_sync_ms 1.1785; B/A ordered second_half wall_ms 0.8773; B/A ordered second_half prepare_ms 0.8642; B/A ordered second_half segment_sync_ms 0.8037; B/A ordered second_half catalog_sync_ms 0.8501; B/A clustered first_half segment_sync_ms 0.8845; B/A clustered second_half catalog_sync_ms 1.1023; B/A interleaved full wall_ms 1.1476; B/A interleaved full segment_sync_ms 1.1836; B/A interleaved second_half wall_ms 1.3026; B/A interleaved second_half segment_sync_ms 1.3743; B/A interleaved second_half catalog_sync_ms 1.1335; B/A duplicates full prepare_ms 0.8956; B/A duplicates first_half prepare_ms 0.8115; B/A duplicates first_half catalog_sync_ms 1.1826; B/A duplicates second_half wall_ms 0.8646; B/A duplicates second_half catalog_sync_ms 0.8084; B/A late full prepare_ms 0.8753; B/A late first_half prepare_ms 0.8193; B/A late second_half wall_ms 1.1103; B/A late second_half segment_sync_ms 1.3467; B/A extreme full catalog_sync_ms 1.2112; B/A extreme first_half catalog_sync_ms 1.1120; B/A extreme second_half catalog_sync_ms 1.2900; C/A ordered first_half wall_ms 1.1164; C/A ordered first_half prepare_ms 0.8344; C/A ordered first_half segment_sync_ms 1.2205; C/A ordered first_half catalog_sync_ms 0.8955; C/A clustered full prepare_ms 1.1333; C/A clustered full catalog_sync_ms 1.2110; C/A clustered first_half catalog_sync_ms 1.3194; C/A clustered second_half wall_ms 1.3276; C/A clustered second_half prepare_ms 1.1762; C/A clustered second_half segment_sync_ms 1.1074; C/A interleaved first_half segment_sync_ms 1.1411; C/A interleaved first_half catalog_sync_ms 1.1532; C/A duplicates full catalog_sync_ms 0.8668; C/A duplicates first_half segment_sync_ms 0.7465; C/A duplicates first_half catalog_sync_ms 0.8798; C/A duplicates second_half wall_ms 0.8939; C/A duplicates second_half catalog_sync_ms 0.8534; C/A late full prepare_ms 1.1131; C/A late first_half prepare_ms 1.1131; C/A late second_half prepare_ms 1.1257; C/A extreme full wall_ms 0.8570; C/A extreme full segment_sync_ms 1.1316; C/A extreme first_half segment_sync_ms 1.2105; C/A extreme second_half wall_ms 0.8475; C/A extreme second_half catalog_sync_ms 0.8804.

All 648 children and the independent auditor exited zero. Complete independent
payload/index/receipt/generation checks covered 21,233,664
rows and 509,607,936 CRC bytes, with pinned snapshots,
reclaim and cold reopen. Timed cases ran from 2026-10-10T13:16:20.276853+00:00 to
2026-10-10T13:31:29.171459+00:00. No fresh Rust build or tests are claimed; the
exact supported baseline from 121/122 was reused. Binary SHA256:
`2392cb6e53c0736a2d3bb67fd89369016848e6e12010989369b46a7a4ec2c1c7`.

Reset remained terminal and inactive. No other build was visible before the
run or in sampled checks during it; those checks cannot exclude every brief
unobserved background task. No app was stopped or global machine setting changed.
An initial shell preflight returned before starting the controller; all 648
timings were still unstarted. The controller subsequently ran once to completion.
The freeze and policy remained unchanged; the independent audit needed no repair.

Preparation includes compaction input reads/CRCs and planning; the whole call
also charges durable output/catalog syncs. Setup, checks, reclaim and reopen
are outside this component timer. There is no SQL/service, competitor or physical
power-loss claim. The original full release gates remain 324 Native cases,
252 service cases, 42 goals, 153 A/A controls and 171 regression guards, plus
relevant correctness/recovery and sustained service qualification.

[Actual reusable controllers](experiments/compaction_controls_125/README.md).
The [primary randomized-interleaving guide](https://github.com/google/benchmark/blob/main/docs/random_interleaving.md)
motivated the declared ordering hypothesis; its results are not Kestrel results.
Policy SHA256: `2fda0e2b8ee9abe3bcf53c6ecd607663e3287f80199e8f1648e83a55de13d392`.
Journal SHA256: `07458d4602c6663a5896143d2fd6576205acb663bbe35035d1365772c48bdd39`.
Concise Markdown and useful source are saved privately, then freshly verified
before scoped fixture cleanup; no multi-gigabyte raw bundle is uploaded.
