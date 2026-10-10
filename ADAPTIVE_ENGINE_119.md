# Bounded compaction workspace trial 119

All 828 fresh test executions, five strict lints, 359 recovery commands and
324 Native cases pass correctness. Performance qualification fails **21/153
A/A checks, 5/171 guards and 2/42 goals**. All 252 service cases are unstarted.
Supported main remains byte-exact **0.3.16**; **0.3.17 is unqualified and unreleased**.

Compaction previously allocated a decoded vector for every input block.
The isolated candidate reuses one 4096-integer workspace across input runs
and columns through the unchanged CRC-first decoder. Its logical payload
capacity is 32 KiB. The original allocating feature-disabled path is exact.
Archive/Cargo byte inverses pass; all other corrected117 source, Reader,
collector, query, live writer, receipt, lock and common-driver bytes are exact.
Selection limits, reads/checksums, output order, maintenance/publication counts,
ACK timing and writer joins are unchanged. The stable
[Vec::clear API](https://doc.rust-lang.org/std/vec/struct.Vec.html#method.clear)
retains capacity. This uses existing APIs and the installed Rust1.97.1 toolchain.

The complete untimed118 diagnosis associated pressure tails with maintenance
gaps. It did not establish exclusive CPU/IO attribution or allocation causality.
This cohort compares the combined collector/filter/replay/scan/group-range/digest/
compaction candidate against fresh D: 016 A/A baselines. It does not isolate
the compaction change versus117 or establish a fresh competitor ranking.

Two new compaction integration tests check independent RAM SQL over full and
partial blocks, signed extrema and late data; repeat compaction, original receipt
identity/mismatch, pinned snapshots, reclaim and reopen; late-input CRC and
truncation rejection before publication with exact catalogs/generation, then
repair/retry. Damaged input bytes and error messages are preserved in test stores.
The complete eight-mode suite and all five strict lints passed on fresh targets.
Recovery includes28 publication injected-error/owned-exit cases,10 corruptions,
two legacy formats, two byte fixtures,256 concurrent ACKs, two named scenarios,
300 cold SQL checks and69,360 CRC bytes. This is not physical power-loss proof.

Four Native/two service excluded smokes,48 balanced-order checks,six invalid
outcome controls,two invalid-order rejections and frozen input provenance pass.
All324 cases ran once, twelve rounds/all six orders/full and both halves.
All479,232 ACKs and2,921,356,800 CRC bytes pass complete independent payload,
index, receipt, digest, generation, cold SQL and raw quantile checks. Every
controller actually exited0. No selected timing rerun or gate relaxation.

## Controlled goals

Eight metrics meet their targets and corresponding A/A controls in full and
both halves. Reductions use median within-round paired ratios; they need not
equal the quotient of displayed medians. These combined gains do not qualify
the release while other mandatory gates fail.

| Workload | Metric | Unit | 016 median | Candidate median | Full paired reduction | Full A/A | Full/both-half targets and controls |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| identified-replay | p95 | us | 1.650000 | 1.500000 | 12.50% | 1.00000000 | pass |
| queries-late | grouped/median_us | us | 6120.100000 | 4692.850000 | 22.54% | 1.00178390 | pass |
| queries-late | unordered_filter/median_us | us | 2789.200000 | 2037.800000 | 25.68% | 1.01135451 | pass |
| queries-ordered | grouped/median_us | us | 6224.600000 | 4757.700000 | 23.72% | 1.00017447 | pass |
| queries-ordered | grouped/p95_us | us | 7248.100000 | 5867.950000 | 17.51% | 1.03106513 | pass |
| queries-ordered | unordered_filter/median_us | us | 2810.950000 | 2047.000000 | 26.15% | 0.99474858 | pass |
| small-anonymous | wall | ms | 2453.046000 | 1826.392700 | 24.98% | 1.00355103 | pass |
| small-named | wall | ms | 2595.346550 | 1753.133300 | 32.03% | 0.98203740 | pass |

## All failures

Passing controls with failed guards are calibrated regressions. Failed controls make a comparison inconclusive. Service remains unstarted because Native qualification fails.

- full pressure-anonymous p95: C/A 1.05228849 (+5.23%); A/A 0.94384872; inconclusive: control fails.

- half_1 sparse-named p95: C/A 1.09087164 (+9.09%); A/A 1.03683590; calibrated regression.

- half_1 pressure-anonymous p95: C/A 1.06871642 (+6.87%); A/A 0.85195882; inconclusive: control fails.

- half_1 pressure-anonymous p99: C/A 1.06854869 (+6.85%); A/A 1.01560744; calibrated regression.

- half_1 pressure-named p95: C/A 1.15181086 (+15.18%); A/A 0.83102417; inconclusive: control fails.

- Goal miss: full small-anonymous p99, C/A 0.96606275 versus 0.95; A/A 1.01943879; control passes.

- Goal miss: half_2 small-anonymous p99, C/A 0.99226408 versus 0.95; A/A 1.08046308; inconclusive: control fails.


## Every before/after comparison

All171 full/half comparisons follow. A/A requires0.95-1.05; candidate guards
require C/A at most1.05; goals retain their stricter metric-specific limits.
Disk has no A/A control. All failed guards remain even when controls fail.

| Scope | Workload | Metric | Unit | Baseline median | Candidate median | A/A | Control | C/A | Guard | Goal limit | Goal |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | ---: | --- |
| full | sparse-anonymous | p50 | ms | 1.963150 | 1.933400 | 0.99776561 | pass | 0.99385391 | pass | n/a | n/a |
| full | sparse-anonymous | p95 | ms | 5.503800 | 5.154200 | 0.93063249 | FAIL | 0.93445988 | pass | n/a | n/a |
| full | sparse-anonymous | p99 | ms | 14.483200 | 14.039850 | 0.98798818 | pass | 0.95055645 | pass | n/a | n/a |
| full | sparse-anonymous | wall | ms | 1283.581000 | 1264.168900 | 0.97834587 | pass | 0.99249522 | pass | n/a | n/a |
| full | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| full | sparse-named | p50 | ms | 1.981800 | 1.924900 | 0.99568903 | pass | 0.98431339 | pass | n/a | n/a |
| full | sparse-named | p95 | ms | 5.674050 | 5.571200 | 0.99062755 | pass | 1.00217644 | pass | n/a | n/a |
| full | sparse-named | p99 | ms | 14.584800 | 14.156100 | 0.98220938 | pass | 0.97958093 | pass | n/a | n/a |
| full | sparse-named | wall | ms | 1312.747000 | 1274.790700 | 0.97669371 | pass | 0.99270152 | pass | n/a | n/a |
| full | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| full | small-anonymous | p50 | ms | 3.885050 | 2.213650 | 1.00443256 | pass | 0.56260760 | pass | n/a | n/a |
| full | small-anonymous | p95 | ms | 14.044100 | 9.129900 | 1.01941299 | pass | 0.67197318 | pass | n/a | n/a |
| full | small-anonymous | p99 | ms | 17.137900 | 16.712600 | 1.01943879 | pass | 0.96606275 | pass | 0.95 | FAIL |
| full | small-anonymous | wall | ms | 2453.046000 | 1826.392700 | 1.00355103 | pass | 0.75016691 | pass | 0.9 | pass |
| full | small-anonymous | disk | bytes | 5817621.000000 | 5319406.500000 | 0.99838676 | n/a | 0.97390989 | pass | n/a | n/a |
| full | small-named | p50 | ms | 4.121200 | 2.237300 | 0.98957064 | pass | 0.53965439 | pass | n/a | n/a |
| full | small-named | p95 | ms | 14.603050 | 9.332600 | 0.99152858 | pass | 0.63751656 | pass | n/a | n/a |
| full | small-named | p99 | ms | 19.708150 | 16.165150 | 0.97964869 | pass | 0.82017450 | pass | 0.95 | pass |
| full | small-named | wall | ms | 2595.346550 | 1753.133300 | 0.98203740 | pass | 0.67973486 | pass | 0.9 | pass |
| full | small-named | disk | bytes | 6462144.500000 | 6211838.000000 | 1.00381619 | n/a | 0.94865592 | pass | n/a | n/a |
| full | pressure-anonymous | p50 | ms | 2.376400 | 2.323550 | 1.00216648 | pass | 1.00114204 | pass | n/a | n/a |
| full | pressure-anonymous | p95 | ms | 9.855200 | 11.228950 | 0.94384872 | FAIL | 1.05228849 | FAIL | n/a | n/a |
| full | pressure-anonymous | p99 | ms | 15.515750 | 16.171500 | 1.01560744 | pass | 0.97353933 | pass | n/a | n/a |
| full | pressure-anonymous | wall | ms | 446.144500 | 444.089100 | 1.00286013 | pass | 1.00975697 | pass | n/a | n/a |
| full | pressure-anonymous | disk | bytes | 11486213.000000 | 11485746.500000 | 0.99855651 | n/a | 1.00040523 | pass | n/a | n/a |
| full | pressure-named | p50 | ms | 2.875050 | 2.949200 | 0.99259118 | pass | 1.01116653 | pass | n/a | n/a |
| full | pressure-named | p95 | ms | 12.246250 | 12.263800 | 0.94945681 | FAIL | 0.95623331 | pass | n/a | n/a |
| full | pressure-named | p99 | ms | 18.069300 | 16.365400 | 1.06065268 | FAIL | 0.95107522 | pass | n/a | n/a |
| full | pressure-named | wall | ms | 520.527300 | 521.558300 | 0.98575577 | pass | 1.00238355 | pass | n/a | n/a |
| full | pressure-named | disk | bytes | 12176144.500000 | 12175778.500000 | 0.99960242 | n/a | 1.00048612 | pass | n/a | n/a |
| full | queries-ordered | all_aggregates/median_us | us | 4.700000 | 4.700000 | 1.00000000 | pass | 1.00000000 | pass | n/a | n/a |
| full | queries-ordered | all_aggregates/p95_us | us | 5.200000 | 5.200000 | 1.00000000 | pass | 1.00000000 | pass | n/a | n/a |
| full | queries-ordered | broad_window/median_us | us | 4.900000 | 5.000000 | 1.00000000 | pass | 1.01020408 | pass | n/a | n/a |
| full | queries-ordered | broad_window/p95_us | us | 5.100000 | 5.200000 | 1.00980392 | pass | 1.00980392 | pass | n/a | n/a |
| full | queries-ordered | narrow_window/median_us | us | 4.100000 | 4.100000 | 1.00000000 | pass | 1.00000000 | pass | n/a | n/a |
| full | queries-ordered | narrow_window/p95_us | us | 4.300000 | 4.300000 | 1.00000000 | pass | 1.00000000 | pass | n/a | n/a |
| full | queries-ordered | unordered_filter/median_us | us | 2810.950000 | 2047.000000 | 0.99474858 | pass | 0.73853841 | pass | 0.9 | pass |
| full | queries-ordered | unordered_filter/p95_us | us | 3133.000000 | 2460.150000 | 0.98583245 | pass | 0.76164361 | pass | 0.9 | pass |
| full | queries-ordered | grouped/median_us | us | 6224.600000 | 4757.700000 | 1.00017447 | pass | 0.76283020 | pass | 0.9 | pass |
| full | queries-ordered | grouped/p95_us | us | 7248.100000 | 5867.950000 | 1.03106513 | pass | 0.82492004 | pass | 0.9 | pass |
| full | queries-ordered | min_max/median_us | us | 7.400000 | 7.550000 | 1.01463675 | pass | 1.01360607 | pass | n/a | n/a |
| full | queries-ordered | min_max/p95_us | us | 7.700000 | 7.800000 | 1.01342342 | pass | 1.00649351 | pass | n/a | n/a |
| full | queries-late | all_aggregates/median_us | us | 4.600000 | 4.800000 | 0.98979592 | pass | 1.01153505 | pass | n/a | n/a |
| full | queries-late | all_aggregates/p95_us | us | 5.400000 | 5.300000 | 0.99074074 | pass | 0.99074074 | pass | n/a | n/a |
| full | queries-late | broad_window/median_us | us | 5.000000 | 5.000000 | 1.00000000 | pass | 1.02000000 | pass | n/a | n/a |
| full | queries-late | broad_window/p95_us | us | 5.200000 | 5.200000 | 1.00000000 | pass | 1.00000000 | pass | n/a | n/a |
| full | queries-late | narrow_window/median_us | us | 4.150000 | 4.150000 | 1.00000000 | pass | 1.02380952 | pass | n/a | n/a |
| full | queries-late | narrow_window/p95_us | us | 4.300000 | 4.300000 | 1.00026427 | pass | 1.00000000 | pass | n/a | n/a |
| full | queries-late | unordered_filter/median_us | us | 2789.200000 | 2037.800000 | 1.01135451 | pass | 0.74323431 | pass | 0.9 | pass |
| full | queries-late | unordered_filter/p95_us | us | 3343.400000 | 2340.450000 | 1.05971575 | FAIL | 0.76422882 | pass | 0.9 | pass |
| full | queries-late | grouped/median_us | us | 6120.100000 | 4692.850000 | 1.00178390 | pass | 0.77458092 | pass | 0.9 | pass |
| full | queries-late | grouped/p95_us | us | 6693.000000 | 5388.250000 | 1.00404899 | pass | 0.82913158 | pass | 0.9 | pass |
| full | queries-late | min_max/median_us | us | 6.950000 | 7.000000 | 1.00000000 | pass | 1.00704225 | pass | n/a | n/a |
| full | queries-late | min_max/p95_us | us | 7.250000 | 7.250000 | 1.00000000 | pass | 1.00675676 | pass | n/a | n/a |
| full | identified-replay | p50 | us | 1.300000 | 1.000000 | 1.00000000 | pass | 0.80128205 | pass | n/a | n/a |
| full | identified-replay | p95 | us | 1.650000 | 1.500000 | 1.00000000 | pass | 0.87500000 | pass | 0.9 | pass |
| full | identified-replay | p99 | us | 2.000000 | 1.700000 | 1.00000000 | pass | 0.89473684 | pass | 0.9 | pass |
| half_1 | sparse-anonymous | p50 | ms | 1.968800 | 1.922400 | 0.99256246 | pass | 0.97761007 | pass | n/a | n/a |
| half_1 | sparse-anonymous | p95 | ms | 5.527650 | 5.165400 | 0.91807925 | FAIL | 0.93445988 | pass | n/a | n/a |
| half_1 | sparse-anonymous | p99 | ms | 14.845600 | 14.039850 | 0.97403914 | pass | 0.92656565 | pass | n/a | n/a |
| half_1 | sparse-anonymous | wall | ms | 1299.215200 | 1243.488850 | 0.97808175 | pass | 0.95352034 | pass | n/a | n/a |
| half_1 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| half_1 | sparse-named | p50 | ms | 1.911950 | 1.875350 | 0.99737308 | pass | 0.98431339 | pass | n/a | n/a |
| half_1 | sparse-named | p95 | ms | 5.354300 | 5.477550 | 1.03683590 | pass | 1.09087164 | FAIL | n/a | n/a |
| half_1 | sparse-named | p99 | ms | 13.990800 | 13.911200 | 0.99838587 | pass | 0.97958093 | pass | n/a | n/a |
| half_1 | sparse-named | wall | ms | 1279.342200 | 1259.040400 | 1.00228949 | pass | 0.99308661 | pass | n/a | n/a |
| half_1 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| half_1 | small-anonymous | p50 | ms | 3.803600 | 2.213650 | 1.00900586 | pass | 0.57097909 | pass | n/a | n/a |
| half_1 | small-anonymous | p95 | ms | 13.807550 | 9.029150 | 1.01941299 | pass | 0.67623044 | pass | n/a | n/a |
| half_1 | small-anonymous | p99 | ms | 17.137900 | 16.390500 | 1.01943879 | pass | 0.93704208 | pass | 0.95 | pass |
| half_1 | small-anonymous | wall | ms | 2412.375300 | 1823.711000 | 0.99917393 | pass | 0.75269579 | pass | 0.9 | pass |
| half_1 | small-anonymous | disk | bytes | 5824472.000000 | 5677762.000000 | 0.99721037 | n/a | 0.97363964 | pass | n/a | n/a |
| half_1 | small-named | p50 | ms | 4.098800 | 2.237300 | 0.98060268 | pass | 0.54069320 | pass | n/a | n/a |
| half_1 | small-named | p95 | ms | 14.244400 | 8.926550 | 0.97949388 | pass | 0.62018875 | pass | n/a | n/a |
| half_1 | small-named | p99 | ms | 19.708150 | 16.283900 | 0.93022449 | FAIL | 0.82017450 | pass | 0.95 | pass |
| half_1 | small-named | wall | ms | 2565.480300 | 1733.565400 | 0.97122302 | pass | 0.67144068 | pass | 0.9 | pass |
| half_1 | small-named | disk | bytes | 6466770.000000 | 5535075.000000 | 0.99976771 | n/a | 0.90462926 | pass | n/a | n/a |
| half_1 | pressure-anonymous | p50 | ms | 2.339850 | 2.332450 | 1.00926606 | pass | 1.01780961 | pass | n/a | n/a |
| half_1 | pressure-anonymous | p95 | ms | 9.777350 | 11.229800 | 0.85195882 | FAIL | 1.06871642 | FAIL | n/a | n/a |
| half_1 | pressure-anonymous | p99 | ms | 14.786200 | 16.160850 | 1.01560744 | pass | 1.06854869 | FAIL | n/a | n/a |
| half_1 | pressure-anonymous | wall | ms | 436.734250 | 443.707100 | 1.01575356 | pass | 1.00975697 | pass | n/a | n/a |
| half_1 | pressure-anonymous | disk | bytes | 11491735.500000 | 11485051.000000 | 0.99774386 | n/a | 1.00007165 | pass | n/a | n/a |
| half_1 | pressure-named | p50 | ms | 2.779750 | 2.907100 | 1.00473206 | pass | 1.03119487 | pass | n/a | n/a |
| half_1 | pressure-named | p95 | ms | 10.745750 | 12.446400 | 0.83102417 | FAIL | 1.15181086 | FAIL | n/a | n/a |
| half_1 | pressure-named | p99 | ms | 19.009000 | 16.365400 | 0.79261086 | FAIL | 0.92435605 | pass | n/a | n/a |
| half_1 | pressure-named | wall | ms | 517.542400 | 521.777050 | 0.98844668 | pass | 1.01797489 | pass | n/a | n/a |
| half_1 | pressure-named | disk | bytes | 12181256.000000 | 12186263.000000 | 0.99960242 | n/a | 1.00064823 | pass | n/a | n/a |
| half_1 | queries-ordered | all_aggregates/median_us | us | 4.700000 | 4.700000 | 1.00000000 | pass | 1.00000000 | pass | n/a | n/a |
| half_1 | queries-ordered | all_aggregates/p95_us | us | 5.200000 | 5.200000 | 1.05769231 | FAIL | 1.00000000 | pass | n/a | n/a |
| half_1 | queries-ordered | broad_window/median_us | us | 4.900000 | 5.000000 | 1.00000000 | pass | 1.02040816 | pass | n/a | n/a |
| half_1 | queries-ordered | broad_window/p95_us | us | 5.100000 | 5.200000 | 1.00980392 | pass | 1.02941176 | pass | n/a | n/a |
| half_1 | queries-ordered | narrow_window/median_us | us | 4.050000 | 4.100000 | 1.00000000 | pass | 1.01250000 | pass | n/a | n/a |
| half_1 | queries-ordered | narrow_window/p95_us | us | 4.250000 | 4.300000 | 1.00000000 | pass | 1.00000000 | pass | n/a | n/a |
| half_1 | queries-ordered | unordered_filter/median_us | us | 2746.650000 | 2047.000000 | 1.01639095 | pass | 0.74579696 | pass | 0.9 | pass |
| half_1 | queries-ordered | unordered_filter/p95_us | us | 3078.100000 | 2516.300000 | 1.05926440 | FAIL | 0.78963397 | pass | 0.9 | pass |
| half_1 | queries-ordered | grouped/median_us | us | 6167.150000 | 4665.700000 | 1.00017447 | pass | 0.75533095 | pass | 0.9 | pass |
| half_1 | queries-ordered | grouped/p95_us | us | 7263.750000 | 5718.650000 | 1.03106513 | pass | 0.78456046 | pass | 0.9 | pass |
| half_1 | queries-ordered | min_max/median_us | us | 7.400000 | 7.550000 | 1.01463675 | pass | 1.02721214 | pass | n/a | n/a |
| half_1 | queries-ordered | min_max/p95_us | us | 7.700000 | 7.800000 | 1.01342342 | pass | 1.02649351 | pass | n/a | n/a |
| half_1 | queries-late | all_aggregates/median_us | us | 4.750000 | 4.700000 | 0.97959184 | pass | 0.97892635 | pass | n/a | n/a |
| half_1 | queries-late | all_aggregates/p95_us | us | 5.450000 | 5.300000 | 0.99074074 | pass | 0.95565302 | pass | n/a | n/a |
| half_1 | queries-late | broad_window/median_us | us | 5.000000 | 5.050000 | 0.99000000 | pass | 1.02000000 | pass | n/a | n/a |
| half_1 | queries-late | broad_window/p95_us | us | 5.200000 | 5.200000 | 0.97115385 | pass | 0.99056604 | pass | n/a | n/a |
| half_1 | queries-late | narrow_window/median_us | us | 4.150000 | 4.200000 | 0.98780488 | pass | 1.02409988 | pass | n/a | n/a |
| half_1 | queries-late | narrow_window/p95_us | us | 4.300000 | 4.300000 | 0.97674419 | pass | 1.00000000 | pass | n/a | n/a |
| half_1 | queries-late | unordered_filter/median_us | us | 2765.750000 | 2027.150000 | 1.01837657 | pass | 0.74571487 | pass | 0.9 | pass |
| half_1 | queries-late | unordered_filter/p95_us | us | 3173.600000 | 2414.500000 | 1.08344021 | FAIL | 0.79141022 | pass | 0.9 | pass |
| half_1 | queries-late | grouped/median_us | us | 6075.400000 | 4688.900000 | 1.00024709 | pass | 0.76806214 | pass | 0.9 | pass |
| half_1 | queries-late | grouped/p95_us | us | 6693.000000 | 5388.250000 | 0.99632904 | pass | 0.82913158 | pass | 0.9 | pass |
| half_1 | queries-late | min_max/median_us | us | 6.900000 | 7.000000 | 0.99305556 | pass | 1.00724638 | pass | n/a | n/a |
| half_1 | queries-late | min_max/p95_us | us | 7.200000 | 7.200000 | 1.00000000 | pass | 1.00704225 | pass | n/a | n/a |
| half_1 | identified-replay | p50 | us | 1.250000 | 1.000000 | 1.00000000 | pass | 0.80128205 | pass | n/a | n/a |
| half_1 | identified-replay | p95 | us | 1.600000 | 1.400000 | 1.03125000 | pass | 0.87500000 | pass | 0.9 | pass |
| half_1 | identified-replay | p99 | us | 1.950000 | 1.700000 | 1.05263158 | FAIL | 0.89473684 | pass | 0.9 | pass |
| half_2 | sparse-anonymous | p50 | ms | 1.937150 | 1.969000 | 0.99776561 | pass | 1.02120053 | pass | n/a | n/a |
| half_2 | sparse-anonymous | p95 | ms | 5.434100 | 5.154200 | 0.97631865 | pass | 0.95660645 | pass | n/a | n/a |
| half_2 | sparse-anonymous | p99 | ms | 14.256050 | 14.178500 | 0.99214834 | pass | 0.97561966 | pass | n/a | n/a |
| half_2 | sparse-anonymous | wall | ms | 1269.549150 | 1280.712600 | 0.98411490 | pass | 1.00511755 | pass | n/a | n/a |
| half_2 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| half_2 | sparse-named | p50 | ms | 1.996250 | 1.959800 | 0.99324512 | pass | 0.98895311 | pass | n/a | n/a |
| half_2 | sparse-named | p95 | ms | 5.878350 | 5.571200 | 0.94010388 | FAIL | 0.97588258 | pass | n/a | n/a |
| half_2 | sparse-named | p99 | ms | 14.845950 | 14.463850 | 0.96201929 | pass | 0.97569426 | pass | n/a | n/a |
| half_2 | sparse-named | wall | ms | 1321.116350 | 1309.217900 | 0.96525573 | pass | 0.99270152 | pass | n/a | n/a |
| half_2 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| half_2 | small-anonymous | p50 | ms | 3.957800 | 2.218700 | 0.99615718 | pass | 0.56118544 | pass | n/a | n/a |
| half_2 | small-anonymous | p95 | ms | 14.115850 | 9.286850 | 1.01697126 | pass | 0.66421930 | pass | n/a | n/a |
| half_2 | small-anonymous | p99 | ms | 17.438450 | 16.862450 | 1.08046308 | FAIL | 0.99226408 | pass | 0.95 | FAIL |
| half_2 | small-anonymous | wall | ms | 2490.877850 | 1862.936200 | 1.01913537 | pass | 0.74981388 | pass | 0.9 | pass |
| half_2 | small-anonymous | disk | bytes | 5805505.000000 | 4971174.000000 | 0.99938396 | n/a | 0.97555517 | pass | n/a | n/a |
| half_2 | small-named | p50 | ms | 4.121200 | 2.244950 | 1.00534137 | pass | 0.53564607 | pass | n/a | n/a |
| half_2 | small-named | p95 | ms | 14.774650 | 9.536300 | 0.99980026 | pass | 0.65064679 | pass | n/a | n/a |
| half_2 | small-named | p99 | ms | 19.630800 | 16.030350 | 0.99112657 | pass | 0.79692020 | pass | 0.95 | pass |
| half_2 | small-named | wall | ms | 2625.801850 | 1762.348550 | 0.98793612 | pass | 0.68533827 | pass | 0.9 | pass |
| half_2 | small-named | disk | bytes | 6462144.500000 | 6232730.500000 | 1.01548344 | n/a | 0.95790048 | pass | n/a | n/a |
| half_2 | pressure-anonymous | p50 | ms | 2.404000 | 2.321700 | 0.98105013 | pass | 0.97859040 | pass | n/a | n/a |
| half_2 | pressure-anonymous | p95 | ms | 10.025050 | 11.114150 | 1.21175661 | FAIL | 1.01909947 | pass | n/a | n/a |
| half_2 | pressure-anonymous | p99 | ms | 18.882550 | 16.171500 | 1.02068183 | pass | 0.84040300 | pass | n/a | n/a |
| half_2 | pressure-anonymous | wall | ms | 455.643300 | 444.089100 | 0.97187626 | pass | 0.98254996 | pass | n/a | n/a |
| half_2 | pressure-anonymous | disk | bytes | 11458328.000000 | 11489181.000000 | 1.00027403 | n/a | 1.00206556 | pass | n/a | n/a |
| half_2 | pressure-named | p50 | ms | 2.903100 | 2.978650 | 0.96827013 | pass | 0.99169074 | pass | n/a | n/a |
| half_2 | pressure-named | p95 | ms | 12.476750 | 12.126300 | 0.94945681 | FAIL | 0.91769155 | pass | n/a | n/a |
| half_2 | pressure-named | p99 | ms | 17.439650 | 16.243650 | 1.21224242 | FAIL | 0.96865059 | pass | n/a | n/a |
| half_2 | pressure-named | wall | ms | 520.527300 | 517.167700 | 0.97545091 | pass | 0.98336313 | pass | n/a | n/a |
| half_2 | pressure-named | disk | bytes | 12169866.000000 | 12173183.000000 | 0.99963849 | n/a | 1.00013100 | pass | n/a | n/a |
| half_2 | queries-ordered | all_aggregates/median_us | us | 4.700000 | 4.750000 | 1.00000000 | pass | 0.98958333 | pass | n/a | n/a |
| half_2 | queries-ordered | all_aggregates/p95_us | us | 5.350000 | 5.200000 | 0.99074074 | pass | 0.97204752 | pass | n/a | n/a |
| half_2 | queries-ordered | broad_window/median_us | us | 5.000000 | 5.000000 | 0.99000000 | pass | 1.00000000 | pass | n/a | n/a |
| half_2 | queries-ordered | broad_window/p95_us | us | 5.150000 | 5.100000 | 1.00980392 | pass | 0.98129371 | pass | n/a | n/a |
| half_2 | queries-ordered | narrow_window/median_us | us | 4.100000 | 4.100000 | 0.97619048 | pass | 0.97590012 | pass | n/a | n/a |
| half_2 | queries-ordered | narrow_window/p95_us | us | 4.300000 | 4.300000 | 0.98837209 | pass | 1.00000000 | pass | n/a | n/a |
| half_2 | queries-ordered | unordered_filter/median_us | us | 2853.400000 | 2050.450000 | 0.97738007 | pass | 0.73601375 | pass | 0.9 | pass |
| half_2 | queries-ordered | unordered_filter/p95_us | us | 3215.400000 | 2375.550000 | 0.94783124 | FAIL | 0.74674703 | pass | 0.9 | pass |
| half_2 | queries-ordered | grouped/median_us | us | 6249.600000 | 4809.700000 | 1.00177855 | pass | 0.77270337 | pass | 0.9 | pass |
| half_2 | queries-ordered | grouped/p95_us | us | 7248.100000 | 5939.550000 | 1.02209220 | pass | 0.84981961 | pass | 0.9 | pass |
| half_2 | queries-ordered | min_max/median_us | us | 7.400000 | 7.550000 | 1.02597403 | pass | 1.00675676 | pass | n/a | n/a |
| half_2 | queries-ordered | min_max/p95_us | us | 7.850000 | 7.800000 | 1.02501203 | pass | 0.98765432 | pass | n/a | n/a |
| half_2 | queries-late | all_aggregates/median_us | us | 4.600000 | 4.800000 | 1.01153505 | pass | 1.04396135 | pass | n/a | n/a |
| half_2 | queries-late | all_aggregates/p95_us | us | 5.400000 | 5.350000 | 1.00017470 | pass | 1.00892857 | pass | n/a | n/a |
| half_2 | queries-late | broad_window/median_us | us | 5.000000 | 5.000000 | 1.01020408 | pass | 1.01980392 | pass | n/a | n/a |
| half_2 | queries-late | broad_window/p95_us | us | 5.150000 | 5.200000 | 1.00000000 | pass | 1.01923788 | pass | n/a | n/a |
| half_2 | queries-late | narrow_window/median_us | us | 4.150000 | 4.100000 | 1.01219512 | pass | 1.01190476 | pass | n/a | n/a |
| half_2 | queries-late | narrow_window/p95_us | us | 4.300000 | 4.300000 | 1.02353267 | pass | 1.01136364 | pass | n/a | n/a |
| half_2 | queries-late | unordered_filter/median_us | us | 2799.200000 | 2079.200000 | 1.00749907 | pass | 0.73832700 | pass | 0.9 | pass |
| half_2 | queries-late | unordered_filter/p95_us | us | 3402.600000 | 2314.450000 | 1.04559124 | pass | 0.76422882 | pass | 0.9 | pass |
| half_2 | queries-late | grouped/median_us | us | 6170.850000 | 4739.350000 | 1.00555061 | pass | 0.77476736 | pass | 0.9 | pass |
| half_2 | queries-late | grouped/p95_us | us | 6740.350000 | 5464.100000 | 1.13165109 | FAIL | 0.81902427 | pass | 0.9 | pass |
| half_2 | queries-late | min_max/median_us | us | 7.050000 | 7.050000 | 1.00724638 | pass | 1.00704225 | pass | n/a | n/a |
| half_2 | queries-late | min_max/p95_us | us | 7.350000 | 7.400000 | 1.00694444 | pass | 1.00675676 | pass | n/a | n/a |
| half_2 | identified-replay | p50 | us | 1.300000 | 1.000000 | 1.00000000 | pass | 0.80128205 | pass | n/a | n/a |
| half_2 | identified-replay | p95 | us | 1.700000 | 1.500000 | 0.97058824 | pass | 0.88235294 | pass | 0.9 | pass |
| half_2 | identified-replay | p99 | us | 2.050000 | 1.750000 | 0.97619048 | pass | 0.89736842 | pass | 0.9 | pass |

## Exact preservation

33,887 files,3,712 directories,
52 bounded ZIP parts and3,959,254,311
logical bytes pass every member CRC/order/offset/size and whole original/restored
SHA/size/file/directory sets before and after complete pure replay. Sources,
binaries, full raw streams/stores, damaged compaction inputs, all prerequisites,
controls/guards/goals/profile and252 unstarted service specs are preserved.
Only inventoried regenerable target/Python caches are excluded; originals remain.
Closed logs are byte-exact gzip supplements. Display-only copied text may have
one final newline; every changed original is additionally byte-exact gzip.
Internal ZIP raw bytes and frozen sources are unchanged. No119 raw cleanup is
eligible until fresh complete private remote content verification.

See [reproduction](benchmarks/adaptive-speed-119/REPRODUCE.md) and
[complete audit](benchmarks/adaptive-speed-119/complete-audit-proof.json).
No release ETA, universal win, new competitor ranking or adoption is established.
