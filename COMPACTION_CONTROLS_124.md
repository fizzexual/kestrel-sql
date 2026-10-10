# Fixed-CPU control calibration 124 — October 10, 2026

**Not stable enough for qualification. Supported 0.3.16; no candidate engine.**
This tests a workaround for [122's unstable controls](COMPACTION_MERGE_122.md).
All three labels use one identical baseline executable. Only this controller
and its children use fixed logical CPU8; every child mask was verified. Windows
power/security settings and other apps are untouched. A fixed 120-second cooldown
precedes 36 balanced rounds, repeating 12 valid input seeds three times; all six
A/B/C orders appear three times in each half for each of six input shapes.
Placement and sample density changed together, so their separate effects are
not isolated. All original release gates remain unchanged.

**16/72 B/A and 8/72 C/A identity checks fail (24/144).** Both families require
paired ratios within [0.90,1.10], for wall/preparation/segment-sync/catalog-sync
in the full run and both halves. Every p50/p95/p99/max and every case was
evaluated; no selected retiming. This result cannot show a database speedup.

| Input | Full paired B/A wall | Full paired C/A wall | Both controls |
| --- | ---: | ---: | --- |
| ordered | 1.0159 | 1.0328 | pass |
| clustered | 0.9486 | 1.0823 | pass |
| interleaved | 0.9928 | 1.0369 | pass |
| duplicates | 1.0119 | 1.0554 | pass |
| late | 1.1204 | 1.0509 | FAIL |
| extreme | 0.8691 | 0.9110 | FAIL |

All failed checks: B/A ordered full prepare_ms 0.815; B/A ordered first_half prepare_ms 0.758; B/A ordered second_half prepare_ms 0.841; B/A ordered second_half catalog_sync_ms 1.117; B/A clustered first_half wall_ms 0.831; B/A clustered first_half prepare_ms 0.812; B/A duplicates second_half prepare_ms 1.102; B/A late full wall_ms 1.120; B/A late full catalog_sync_ms 1.116; B/A late first_half wall_ms 1.153; B/A late first_half segment_sync_ms 1.111; B/A late first_half catalog_sync_ms 1.120; B/A late second_half wall_ms 1.100; B/A extreme full wall_ms 0.869; B/A extreme second_half wall_ms 0.860; B/A extreme second_half prepare_ms 1.149; C/A ordered first_half prepare_ms 1.122; C/A ordered first_half catalog_sync_ms 1.205; C/A clustered full prepare_ms 1.200; C/A clustered first_half prepare_ms 1.296; C/A interleaved first_half prepare_ms 1.164; C/A interleaved first_half catalog_sync_ms 0.880; C/A late first_half prepare_ms 0.899; C/A late first_half catalog_sync_ms 1.143.

All 648 actual child exits were zero. The independent corrected audit checked
21,233,664 rows and 509,607,936 CRC bytes,
complete row multisets, indexes, receipts/generations, pinned snapshots and cold
recovery. No new Rust build/tests were counted: this is the exact 121/122 baseline
binary, SHA256 `2392cb6e53c0736a2d3bb67fd89369016848e6e12010989369b46a7a4ec2c1c7`.

Preserved failed work: trial123's excluded seed17 hit the unchanged driver's
1..12 assertion before any 648-case timing began; a seed5 preflight subsequently
passed full payload/CRC/affinity checks. Trial124's first postprocessor checked
all 648 payloads then failed at round 13 because it indexed timings by repeated
seed. Its narrow repair indexes timing by round; input generation still uses
seed. The original code/error remains; timings/policy/binary were unchanged.

Preparation starts at compaction entry and includes reads, CRCs and any merge
planning. Whole compaction also charges durable output/catalog syncs. Setup,
checks, reclaim and reopen remain outside this component timer. SQL/service,
physical power-loss and full 0.3.17 qualification remain outstanding.

Next investigate CPU work separately from input I/O and durable sync variability,
then require the full original Native/service/recovery gates before adoption.
Do not treat fixed CPU placement alone as the solved cause or choose a fast
core/round after seeing outcomes.
[Reusable and failed controllers](experiments/compaction_controls_124/README.md).
The [primary benchmark variance guide](https://github.com/google/benchmark/blob/main/docs/reducing_variance.md)
motivates fixed placement; its Linux-specific settings were not applied.
Policy SHA256: `bc3a05a94a215a3e675788c47d2b9f0e1d81d41ed35080988b3d977e80625507`.
Case journal SHA256: `f99907bcbe2f413a6fe00a797288148f1cd3cd426fb4f03655ddf4a7f7a9c246`.
Fixtures follow the user's concise private Markdown retention policy after
fresh remote-save verification; no multi-gigabyte raw bundle is uploaded.
