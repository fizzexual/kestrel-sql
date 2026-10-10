# Adaptive engine trial111

The candidate implements workload-dependent collection, query-shape dispatch,
validated duplicate replay and bounded long-scan read-ahead. **Release
qualification fails.** Supported main stays0.3.16; isolated0.3.17 metadata is
unreleased. This is not a new competitor comparison or universal benchmark win.

The exact107 collector chooses immediate isolated work, finite small-group
lookahead or pressure draining. Exact109 query fusion and110 durable-ID replay
remain. Trial111 chooses read-ahead only for at least eight requested blocks,
with the window chosen from needed-column count, at most eight blocks per
column and512KiB total payload. Short/wide/prefix/full-verification fallbacks
remain; per-consumed-block CRC is checked. Read buffers remain query-local.
No source/WAL/ACK, publication, file-format or maintenance contract changes.

Fresh772 tests across eight debug/release configurations and five strict
all-target lints passed, including six new dispatch/correctness/bounds/memory/
corruption tests. Fresh359-command recovery,28 fault cases,10 corruptions,
CAT2/CAT3,two byte fixtures,256 anonymous ACKs,two named scenarios and300 cold
SQLite SQL checks pass. Excluded four Native/two service smokes,48 order and29
negative checks pass. The complete66-statement pre-timing provenance prefix
passes. All324 Native cases ran once;479,232 ACKs and2,921,356,800 full CRC bytes
independently pass exact rows,receipt generations,indexes,SQL,quantiles,balanced
orders and frozen provenance. Native CPU/RSS were not measured. Physical power
loss and resource exhaustion were not tested.

Performance fails16/153 A/A controls,6/171 guards and17/42 goals. All prior
controls/guards/goals remain;12 grouped-query goals were added before code.
All252 service cases remain UNSTARTED/UNTESTED. No numerical retry, selected
round/scope or loosened gate occurred. Supported0.3.17 is not qualified.

## Goals verified in full and both halves

Five goals pass their targets and baseline controls in all three required
scopes. These are specific Native comparisons against0.3.16. Percentages use
paired within-round ratios and can differ from quotients of displayed medians.

| Workload | Metric | Unit | Before median | After median | Full A/A | Paired candidate/A | Improvement | Halves |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| queries-late | unordered_filter/median_us | us | 2828.950000 | 2408.100000 | 1.00526145 | 0.85300663 | 14.70% | both pass |
| queries-ordered | unordered_filter/median_us | us | 2853.550000 | 2437.950000 | 1.00977647 | 0.85250309 | 14.75% | both pass |
| small-anonymous | wall | ms | 2436.953500 | 1789.996350 | 0.98934451 | 0.72510750 | 27.49% | both pass |
| small-named | p99 | ms | 17.715300 | 16.030250 | 0.99396439 | 0.89903946 | 10.10% | both pass |
| small-named | wall | ms | 2564.520950 | 1742.365950 | 0.99992169 | 0.68482613 | 31.52% | both pass |

Grouped full median paired improvements are6.12% ordered and4.92% late. Both
miss their10% goals. Group p95 half controls fail; no grouped goal qualifies
across all scopes. Calibrated regressions remain in sparse-anonymous p95 half1,
pressure-anonymous p99 half2,late narrow-window median/p95 half2. Their causes
are not established. Pressure profiles show about143 pressure groups and only
two coalescing groups with at most100us selected wait; this does not justify
attributing the pressure tail exclusively to intentional collection waiting.

QPC metadata returns10MHz/100ns ticks, and Python perf_counter reports QPC.
Quantization may affect very short intervals; this is not a causal proof or a
claim about Rust's implementation. The first sandbox-denied metadata write,
unchanged successful helper and both logs are retained. An unexecuted negative
closure output draft and exact output-key refinement are also retained. No
source, Native result or gate changed.

## Every before/after and gate

All171 full/half comparisons follow. Live units are milliseconds,queries/replay
microseconds,disk bytes. Controls require0.95..1.05; guards require at most1.05.
Small-write p99 goals require0.95; completion/filter/replay/grouped goals0.90.
All maxima/raw stalls remain preserved.

| Scope | Workload | Metric | Unit | Before median | After median | A/A | Control | Candidate/A | Regression | Goal |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- |
| full | sparse-anonymous | p50 | ms | 1.928800 | 1.905850 | 1.00230593 | pass | 0.99678168 | pass | - |
| full | sparse-anonymous | p95 | ms | 5.375400 | 5.427900 | 1.00531294 | pass | 1.00309643 | pass | - |
| full | sparse-anonymous | p99 | ms | 14.253700 | 14.097250 | 1.01894980 | pass | 1.00604360 | pass | - |
| full | sparse-anonymous | wall | ms | 1250.234200 | 1245.719850 | 1.01236038 | pass | 1.00120081 | pass | - |
| full | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| full | sparse-named | p50 | ms | 1.945200 | 1.929150 | 1.00292611 | pass | 0.99578155 | pass | - |
| full | sparse-named | p95 | ms | 5.646950 | 5.414100 | 0.98728397 | pass | 0.96619718 | pass | - |
| full | sparse-named | p99 | ms | 14.311350 | 13.898650 | 1.02446193 | pass | 0.99983002 | pass | - |
| full | sparse-named | wall | ms | 1280.765650 | 1266.118600 | 1.00718131 | pass | 0.97896336 | pass | - |
| full | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| full | small-anonymous | p50 | ms | 3.957000 | 2.250100 | 0.99422238 | pass | 0.55830486 | pass | - |
| full | small-anonymous | p95 | ms | 13.902900 | 9.430900 | 0.99128693 | pass | 0.67762420 | pass | - |
| full | small-anonymous | p99 | ms | 17.227500 | 16.572200 | 0.98335686 | pass | 0.97064219 | pass | FAIL <= 0.95 |
| full | small-anonymous | wall | ms | 2436.953500 | 1789.996350 | 0.98934451 | pass | 0.72510750 | pass | pass <= 0.90 |
| full | small-anonymous | disk | bytes | 5818515.000000 | 5228120.000000 | 0.99962570 | n/a | 0.91024782 | pass | - |
| full | small-named | p50 | ms | 4.132250 | 2.227150 | 1.00603717 | pass | 0.54486658 | pass | - |
| full | small-named | p95 | ms | 14.343350 | 9.472650 | 0.99912125 | pass | 0.65141928 | pass | - |
| full | small-named | p99 | ms | 17.715300 | 16.030250 | 0.99396439 | pass | 0.89903946 | pass | pass <= 0.95 |
| full | small-named | wall | ms | 2564.520950 | 1742.365950 | 0.99992169 | pass | 0.68482613 | pass | pass <= 0.90 |
| full | small-named | disk | bytes | 6545092.500000 | 5532624.500000 | 0.99382466 | n/a | 0.89467055 | pass | - |
| full | pressure-anonymous | p50 | ms | 2.432600 | 2.348500 | 1.00501015 | pass | 0.97754070 | pass | - |
| full | pressure-anonymous | p95 | ms | 9.537750 | 6.832850 | 0.73716331 | FAIL | 0.97690300 | pass | - |
| full | pressure-anonymous | p99 | ms | 15.976350 | 19.642900 | 0.93706462 | FAIL | 1.28945414 | FAIL | - |
| full | pressure-anonymous | wall | ms | 436.268550 | 432.430800 | 1.02894853 | pass | 0.99147782 | pass | - |
| full | pressure-anonymous | disk | bytes | 11462985.000000 | 11467307.000000 | 0.99909770 | n/a | 1.00020382 | pass | - |
| full | pressure-named | p50 | ms | 2.823950 | 2.803450 | 1.01435960 | pass | 1.00308316 | pass | - |
| full | pressure-named | p95 | ms | 11.800350 | 11.604050 | 0.99191893 | pass | 0.93957478 | pass | - |
| full | pressure-named | p99 | ms | 18.258550 | 16.194050 | 0.89947268 | FAIL | 0.88643335 | pass | - |
| full | pressure-named | wall | ms | 515.295600 | 496.256850 | 0.98452597 | pass | 0.97049308 | pass | - |
| full | pressure-named | disk | bytes | 12180844.500000 | 12176893.500000 | 0.99944965 | n/a | 0.99939204 | pass | - |
| full | queries-ordered | all_aggregates/median_us | us | 5.000000 | 4.700000 | 1.02000000 | pass | 0.94000000 | pass | - |
| full | queries-ordered | all_aggregates/p95_us | us | 5.800000 | 5.450000 | 1.00000000 | pass | 0.92299825 | pass | - |
| full | queries-ordered | broad_window/median_us | us | 5.100000 | 5.000000 | 1.01904935 | pass | 0.97096531 | pass | - |
| full | queries-ordered | broad_window/p95_us | us | 5.300000 | 5.200000 | 1.01887464 | pass | 0.96296296 | pass | - |
| full | queries-ordered | narrow_window/median_us | us | 4.100000 | 4.100000 | 1.02409988 | pass | 0.97619048 | pass | - |
| full | queries-ordered | narrow_window/p95_us | us | 4.300000 | 4.300000 | 1.01136364 | pass | 0.97700846 | pass | - |
| full | queries-ordered | unordered_filter/median_us | us | 2853.550000 | 2437.950000 | 1.00977647 | pass | 0.85250309 | pass | pass <= 0.90 |
| full | queries-ordered | unordered_filter/p95_us | us | 3340.050000 | 2812.050000 | 0.99180460 | pass | 0.81647852 | pass | pass <= 0.90 |
| full | queries-ordered | grouped/median_us | us | 6280.350000 | 5921.200000 | 0.98228294 | pass | 0.93878625 | pass | FAIL <= 0.90 |
| full | queries-ordered | grouped/p95_us | us | 7224.750000 | 6942.350000 | 1.02814498 | pass | 0.92705437 | pass | FAIL <= 0.90 |
| full | queries-ordered | min_max/median_us | us | 7.500000 | 7.350000 | 1.00000000 | pass | 0.97367965 | pass | - |
| full | queries-ordered | min_max/p95_us | us | 7.900000 | 7.600000 | 1.00641026 | pass | 0.96178189 | pass | - |
| full | queries-late | all_aggregates/median_us | us | 4.900000 | 4.700000 | 1.00000000 | pass | 0.95875850 | pass | - |
| full | queries-late | all_aggregates/p95_us | us | 5.700000 | 5.350000 | 1.00877193 | pass | 0.93763955 | pass | - |
| full | queries-late | broad_window/median_us | us | 5.100000 | 5.100000 | 1.01941931 | pass | 0.99038462 | pass | - |
| full | queries-late | broad_window/p95_us | us | 5.300000 | 5.300000 | 1.01886792 | pass | 1.00000000 | pass | - |
| full | queries-late | narrow_window/median_us | us | 4.050000 | 4.250000 | 1.00000000 | pass | 1.03689024 | pass | - |
| full | queries-late | narrow_window/p95_us | us | 4.200000 | 4.400000 | 1.01136364 | pass | 1.04819977 | pass | - |
| full | queries-late | unordered_filter/median_us | us | 2828.950000 | 2408.100000 | 1.00526145 | pass | 0.85300663 | pass | pass <= 0.90 |
| full | queries-late | unordered_filter/p95_us | us | 3234.400000 | 2712.600000 | 0.98684688 | pass | 0.83494358 | pass | pass <= 0.90 |
| full | queries-late | grouped/median_us | us | 6223.650000 | 5926.350000 | 1.00406933 | pass | 0.95083040 | pass | FAIL <= 0.90 |
| full | queries-late | grouped/p95_us | us | 6907.550000 | 7061.050000 | 1.00908201 | pass | 0.97030669 | pass | FAIL <= 0.90 |
| full | queries-late | min_max/median_us | us | 7.200000 | 7.100000 | 1.00684932 | pass | 0.98591549 | pass | - |
| full | queries-late | min_max/p95_us | us | 7.400000 | 7.350000 | 1.00675676 | pass | 0.97981735 | pass | - |
| full | identified-replay | p50 | us | 1.300000 | 1.100000 | 1.00000000 | pass | 0.84615385 | pass | - |
| full | identified-replay | p95 | us | 1.700000 | 1.500000 | 1.05882353 | FAIL | 0.88235294 | pass | pass <= 0.90 |
| full | identified-replay | p99 | us | 1.950000 | 1.800000 | 1.07631579 | FAIL | 0.89736842 | pass | pass <= 0.90 |
| half_1 | sparse-anonymous | p50 | ms | 1.954000 | 1.944000 | 1.01718964 | pass | 0.99744812 | pass | - |
| half_1 | sparse-anonymous | p95 | ms | 5.391850 | 5.601800 | 1.01227952 | pass | 1.07764377 | FAIL | - |
| half_1 | sparse-anonymous | p99 | ms | 14.253700 | 14.234450 | 1.02532665 | pass | 1.02931481 | pass | - |
| half_1 | sparse-anonymous | wall | ms | 1265.185650 | 1269.773900 | 1.02560492 | pass | 1.02071080 | pass | - |
| half_1 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_1 | sparse-named | p50 | ms | 1.976900 | 2.038000 | 1.02125336 | pass | 1.04526354 | pass | - |
| half_1 | sparse-named | p95 | ms | 5.646950 | 5.711450 | 0.98728397 | pass | 0.99733561 | pass | - |
| half_1 | sparse-named | p99 | ms | 14.333200 | 14.712000 | 1.03112667 | pass | 1.04683022 | pass | - |
| half_1 | sparse-named | wall | ms | 1284.968500 | 1313.145200 | 1.00843348 | pass | 1.02975233 | pass | - |
| half_1 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_1 | small-anonymous | p50 | ms | 4.056800 | 2.265400 | 0.98836777 | pass | 0.55830486 | pass | - |
| half_1 | small-anonymous | p95 | ms | 14.396100 | 9.874300 | 0.99518149 | pass | 0.68810904 | pass | - |
| half_1 | small-anonymous | p99 | ms | 17.956450 | 16.768350 | 1.03326080 | pass | 0.97623720 | pass | FAIL <= 0.95 |
| half_1 | small-anonymous | wall | ms | 2541.278800 | 1812.817350 | 0.98597426 | pass | 0.71497740 | pass | pass <= 0.90 |
| half_1 | small-anonymous | disk | bytes | 5735745.000000 | 5226630.000000 | 1.00033087 | n/a | 0.91024782 | pass | - |
| half_1 | small-named | p50 | ms | 4.211400 | 2.303200 | 1.00603717 | pass | 0.54627495 | pass | - |
| half_1 | small-named | p95 | ms | 14.766550 | 9.472650 | 0.99484436 | pass | 0.65141928 | pass | - |
| half_1 | small-named | p99 | ms | 18.665550 | 16.979100 | 0.95302561 | pass | 0.91503467 | pass | pass <= 0.95 |
| half_1 | small-named | wall | ms | 2611.844900 | 1788.604300 | 0.99043196 | pass | 0.69390642 | pass | pass <= 0.90 |
| half_1 | small-named | disk | bytes | 6474923.500000 | 5677546.500000 | 0.94551005 | n/a | 0.94385539 | pass | - |
| half_1 | pressure-anonymous | p50 | ms | 2.471100 | 2.394450 | 0.98926789 | pass | 0.96992267 | pass | - |
| half_1 | pressure-anonymous | p95 | ms | 9.537750 | 7.126750 | 0.70081281 | FAIL | 0.97690300 | pass | - |
| half_1 | pressure-anonymous | p99 | ms | 15.194000 | 19.008200 | 0.93706462 | FAIL | 1.29491809 | FAIL | - |
| half_1 | pressure-anonymous | wall | ms | 439.425400 | 436.330250 | 0.97921778 | pass | 0.98147939 | pass | - |
| half_1 | pressure-anonymous | disk | bytes | 11465034.000000 | 11447602.000000 | 0.99909770 | n/a | 0.99843900 | pass | - |
| half_1 | pressure-named | p50 | ms | 2.875300 | 2.829750 | 0.99855435 | pass | 0.98524629 | pass | - |
| half_1 | pressure-named | p95 | ms | 11.598300 | 11.198800 | 1.01270579 | pass | 0.93947833 | pass | - |
| half_1 | pressure-named | p99 | ms | 17.734250 | 16.004000 | 0.89947268 | FAIL | 0.88643335 | pass | - |
| half_1 | pressure-named | wall | ms | 526.105050 | 496.201550 | 0.98452597 | pass | 0.95330525 | pass | - |
| half_1 | pressure-named | disk | bytes | 12180616.500000 | 12179464.000000 | 0.99965859 | n/a | 0.99939204 | pass | - |
| half_1 | queries-ordered | all_aggregates/median_us | us | 5.000000 | 4.700000 | 1.02000000 | pass | 0.94000000 | pass | - |
| half_1 | queries-ordered | all_aggregates/p95_us | us | 5.800000 | 5.500000 | 1.00000000 | pass | 0.91692137 | pass | - |
| half_1 | queries-ordered | broad_window/median_us | us | 5.100000 | 5.000000 | 1.00000000 | pass | 0.98039216 | pass | - |
| half_1 | queries-ordered | broad_window/p95_us | us | 5.250000 | 5.200000 | 1.00925926 | pass | 0.98095065 | pass | - |
| half_1 | queries-ordered | narrow_window/median_us | us | 4.150000 | 4.100000 | 1.01190476 | pass | 0.98809524 | pass | - |
| half_1 | queries-ordered | narrow_window/p95_us | us | 4.300000 | 4.300000 | 1.01136364 | pass | 0.98863636 | pass | - |
| half_1 | queries-ordered | unordered_filter/median_us | us | 2853.550000 | 2453.600000 | 1.01116905 | pass | 0.85932123 | pass | pass <= 0.90 |
| half_1 | queries-ordered | unordered_filter/p95_us | us | 3172.850000 | 2929.200000 | 1.05150657 | FAIL | 0.90064445 | pass | FAIL <= 0.90 |
| half_1 | queries-ordered | grouped/median_us | us | 6370.450000 | 6270.400000 | 0.98228294 | pass | 0.95093751 | pass | FAIL <= 0.90 |
| half_1 | queries-ordered | grouped/p95_us | us | 7347.500000 | 7414.650000 | 0.97804146 | pass | 0.98133014 | pass | FAIL <= 0.90 |
| half_1 | queries-ordered | min_max/median_us | us | 7.550000 | 7.400000 | 1.00000000 | pass | 0.96727614 | pass | - |
| half_1 | queries-ordered | min_max/p95_us | us | 7.850000 | 7.600000 | 1.01282051 | pass | 0.96811100 | pass | - |
| half_1 | queries-late | all_aggregates/median_us | us | 4.900000 | 4.700000 | 1.00000000 | pass | 0.95918367 | pass | - |
| half_1 | queries-late | all_aggregates/p95_us | us | 5.750000 | 5.400000 | 0.99137931 | pass | 0.93011084 | pass | - |
| half_1 | queries-late | broad_window/median_us | us | 5.100000 | 5.050000 | 1.00980392 | pass | 0.98058069 | pass | - |
| half_1 | queries-late | broad_window/p95_us | us | 5.300000 | 5.250000 | 1.00943396 | pass | 0.99056604 | pass | - |
| half_1 | queries-late | narrow_window/median_us | us | 4.100000 | 4.150000 | 1.00000000 | pass | 1.01250000 | pass | - |
| half_1 | queries-late | narrow_window/p95_us | us | 4.200000 | 4.250000 | 1.00000000 | pass | 1.00000000 | pass | - |
| half_1 | queries-late | unordered_filter/median_us | us | 2845.900000 | 2459.450000 | 1.01425470 | pass | 0.86258000 | pass | pass <= 0.90 |
| half_1 | queries-late | unordered_filter/p95_us | us | 3255.700000 | 2949.400000 | 1.00227843 | pass | 0.90087735 | pass | FAIL <= 0.90 |
| half_1 | queries-late | grouped/median_us | us | 6238.200000 | 6113.300000 | 1.00088408 | pass | 0.96588844 | pass | FAIL <= 0.90 |
| half_1 | queries-late | grouped/p95_us | us | 7439.800000 | 7211.650000 | 0.97185067 | pass | 0.97030669 | pass | FAIL <= 0.90 |
| half_1 | queries-late | min_max/median_us | us | 7.300000 | 7.200000 | 1.01369863 | pass | 0.98630137 | pass | - |
| half_1 | queries-late | min_max/p95_us | us | 7.450000 | 7.450000 | 1.01351351 | pass | 0.99333333 | pass | - |
| half_1 | identified-replay | p50 | us | 1.300000 | 1.100000 | 1.00000000 | pass | 0.84615385 | pass | - |
| half_1 | identified-replay | p95 | us | 1.700000 | 1.500000 | 1.02941176 | pass | 0.88235294 | pass | pass <= 0.90 |
| half_1 | identified-replay | p99 | us | 1.950000 | 1.850000 | 1.07894737 | FAIL | 0.92368421 | pass | FAIL <= 0.90 |
| half_2 | sparse-anonymous | p50 | ms | 1.892850 | 1.871250 | 0.98445317 | pass | 0.99678168 | pass | - |
| half_2 | sparse-anonymous | p95 | ms | 5.349950 | 5.256700 | 1.00531294 | pass | 0.98580502 | pass | - |
| half_2 | sparse-anonymous | p99 | ms | 13.918550 | 13.637050 | 1.01177440 | pass | 1.00070348 | pass | - |
| half_2 | sparse-anonymous | wall | ms | 1230.296600 | 1231.467250 | 0.99816888 | pass | 0.99843039 | pass | - |
| half_2 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_2 | sparse-named | p50 | ms | 1.905700 | 1.868350 | 0.97879499 | pass | 0.97302744 | pass | - |
| half_2 | sparse-named | p95 | ms | 5.604550 | 5.067850 | 0.98263998 | pass | 0.89958717 | pass | - |
| half_2 | sparse-named | p99 | ms | 13.896450 | 13.487850 | 1.02446193 | pass | 0.97953678 | pass | - |
| half_2 | sparse-named | wall | ms | 1266.402700 | 1211.809750 | 0.98678731 | pass | 0.96623949 | pass | - |
| half_2 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_2 | small-anonymous | p50 | ms | 3.777900 | 2.208000 | 1.00069553 | pass | 0.57200442 | pass | - |
| half_2 | small-anonymous | p95 | ms | 13.338150 | 8.965650 | 0.98975877 | pass | 0.66262478 | pass | - |
| half_2 | small-anonymous | p99 | ms | 17.051500 | 16.041300 | 0.96193195 | pass | 0.95216824 | pass | FAIL <= 0.95 |
| half_2 | small-anonymous | wall | ms | 2362.299100 | 1785.244900 | 0.98990305 | pass | 0.74347083 | pass | pass <= 0.90 |
| half_2 | small-anonymous | disk | bytes | 5825851.000000 | 5315334.500000 | 0.99962570 | n/a | 0.91279083 | pass | - |
| half_2 | small-named | p50 | ms | 4.080500 | 2.177050 | 1.00748162 | pass | 0.53921423 | pass | - |
| half_2 | small-named | p95 | ms | 14.017850 | 9.338350 | 1.00655999 | pass | 0.65530798 | pass | - |
| half_2 | small-named | p99 | ms | 17.655700 | 15.554450 | 1.01154578 | pass | 0.89903946 | pass | pass <= 0.95 |
| half_2 | small-named | wall | ms | 2540.982050 | 1712.822600 | 1.01335073 | pass | 0.68066526 | pass | pass <= 0.90 |
| half_2 | small-named | disk | bytes | 6548401.000000 | 5531230.500000 | 0.99382466 | n/a | 0.84507744 | pass | - |
| half_2 | pressure-anonymous | p50 | ms | 2.359200 | 2.311500 | 1.03533473 | pass | 0.97754070 | pass | - |
| half_2 | pressure-anonymous | p95 | ms | 9.512450 | 6.512250 | 0.81109517 | FAIL | 0.92684120 | pass | - |
| half_2 | pressure-anonymous | p99 | ms | 18.886200 | 19.681350 | 0.98346403 | pass | 1.08705614 | FAIL | - |
| half_2 | pressure-anonymous | wall | ms | 425.762900 | 429.105350 | 1.04459174 | pass | 0.99147782 | pass | - |
| half_2 | pressure-anonymous | disk | bytes | 11462985.000000 | 11471402.500000 | 1.00056067 | n/a | 1.00194912 | pass | - |
| half_2 | pressure-named | p50 | ms | 2.700600 | 2.779050 | 1.01765960 | pass | 1.02545835 | pass | - |
| half_2 | pressure-named | p95 | ms | 11.800350 | 11.604050 | 0.97773678 | pass | 0.93988409 | pass | - |
| half_2 | pressure-named | p99 | ms | 20.228250 | 18.078050 | 1.02018558 | pass | 0.92211074 | pass | - |
| half_2 | pressure-named | wall | ms | 505.506650 | 497.760100 | 0.99408495 | pass | 0.97842481 | pass | - |
| half_2 | pressure-named | disk | bytes | 12180844.500000 | 12167134.500000 | 0.99831884 | n/a | 0.99893989 | pass | - |
| half_2 | queries-ordered | all_aggregates/median_us | us | 5.000000 | 4.700000 | 1.01000000 | pass | 0.94000000 | pass | - |
| half_2 | queries-ordered | all_aggregates/p95_us | us | 5.900000 | 5.350000 | 0.97500000 | pass | 0.93189655 | pass | - |
| half_2 | queries-ordered | broad_window/median_us | us | 5.150000 | 5.000000 | 1.01941931 | pass | 0.95246734 | pass | - |
| half_2 | queries-ordered | broad_window/p95_us | us | 5.300000 | 5.150000 | 1.02848331 | pass | 0.96226415 | pass | - |
| half_2 | queries-ordered | narrow_window/median_us | us | 4.100000 | 4.000000 | 1.03658537 | pass | 0.97560976 | pass | - |
| half_2 | queries-ordered | narrow_window/p95_us | us | 4.350000 | 4.200000 | 1.01162791 | pass | 0.97674419 | pass | - |
| half_2 | queries-ordered | unordered_filter/median_us | us | 2835.450000 | 2345.850000 | 1.00676658 | pass | 0.83122913 | pass | pass <= 0.90 |
| half_2 | queries-ordered | unordered_filter/p95_us | us | 3475.000000 | 2674.000000 | 0.90930385 | FAIL | 0.78536710 | pass | pass <= 0.90 |
| half_2 | queries-ordered | grouped/median_us | us | 6243.150000 | 5771.600000 | 0.98109056 | pass | 0.92413609 | pass | FAIL <= 0.90 |
| half_2 | queries-ordered | grouped/p95_us | us | 7224.750000 | 6486.000000 | 1.07933740 | FAIL | 0.88950526 | pass | pass <= 0.90 |
| half_2 | queries-ordered | min_max/median_us | us | 7.400000 | 7.350000 | 1.00675676 | pass | 0.98666667 | pass | - |
| half_2 | queries-ordered | min_max/p95_us | us | 8.000000 | 7.600000 | 0.96913580 | pass | 0.95014846 | pass | - |
| half_2 | queries-late | all_aggregates/median_us | us | 4.900000 | 4.700000 | 1.01943396 | pass | 0.94916667 | pass | - |
| half_2 | queries-late | all_aggregates/p95_us | us | 5.650000 | 5.300000 | 1.03540100 | pass | 0.93763955 | pass | - |
| half_2 | queries-late | broad_window/median_us | us | 5.100000 | 5.100000 | 1.01961538 | pass | 1.01000000 | pass | - |
| half_2 | queries-late | broad_window/p95_us | us | 5.250000 | 5.300000 | 1.03846154 | pass | 1.00961538 | pass | - |
| half_2 | queries-late | narrow_window/median_us | us | 4.000000 | 4.300000 | 1.03750000 | pass | 1.07500000 | FAIL | - |
| half_2 | queries-late | narrow_window/p95_us | us | 4.150000 | 4.400000 | 1.04707792 | pass | 1.06097561 | FAIL | - |
| half_2 | queries-late | unordered_filter/median_us | us | 2697.800000 | 2314.550000 | 0.99577729 | pass | 0.84396132 | pass | pass <= 0.90 |
| half_2 | queries-late | unordered_filter/p95_us | us | 3103.600000 | 2695.850000 | 0.97007352 | pass | 0.82071705 | pass | pass <= 0.90 |
| half_2 | queries-late | grouped/median_us | us | 6078.700000 | 5683.250000 | 1.00677577 | pass | 0.94652647 | pass | FAIL <= 0.90 |
| half_2 | queries-late | grouped/p95_us | us | 6647.600000 | 6715.300000 | 1.05621917 | FAIL | 0.97599533 | pass | FAIL <= 0.90 |
| half_2 | queries-late | min_max/median_us | us | 7.200000 | 7.000000 | 0.99305556 | pass | 0.97925912 | pass | - |
| half_2 | queries-late | min_max/p95_us | us | 7.350000 | 7.200000 | 1.00000000 | pass | 0.97315315 | pass | - |
| half_2 | identified-replay | p50 | us | 1.300000 | 1.000000 | 1.00000000 | pass | 0.80128205 | pass | - |
| half_2 | identified-replay | p95 | us | 1.650000 | 1.400000 | 1.05882353 | FAIL | 0.84926471 | pass | pass <= 0.90 |
| half_2 | identified-replay | p99 | us | 1.950000 | 1.700000 | 1.07631579 | FAIL | 0.87236842 | pass | pass <= 0.90 |

## Exact preservation and next work

The archive contains 33,118 files, 3,575
directories, 51 bounded ZIP parts and
3,926,608,556 logical bytes. All member checksums, order,
offsets, sizes, complete original/restored file hashes and directory sets passed
before and after the complete independent restored audit. It launched no Native
processes or timers and changed no existing files. Only inventoried regenerable
build/Python caches are excluded; all originals remain. Closed raw logs are
byte-exact gzip supplements with both raw and encoded hashes. No complete
verified private GitHub backup or recent raw deletion is claimed.

Next justified scan investigation: eliminate the additional window-to-scratch
copy and keep the original Reader/fallback layout and method unchanged. The
present source adds that copy for every consumed block; this motivates a new
bounded borrowed-block path, not an exclusive bottleneck claim. New work needs
a fresh number,predeclared controls and complete qualification. Ingestion tail
causes remain unresolved. Older106/107 rejection and108 diagnostic archival
closures remain pending; every original and failure is safe.

See [reproduction](benchmarks/adaptive-speed-111/REPRODUCE.md),
[complete audit](benchmarks/adaptive-speed-111/complete-audit-proof.json),
[restored audit](benchmarks/adaptive-speed-111/restored-audit-proof.json),
[Native raw replay](benchmarks/adaptive-speed-111/native-audit.json) and
[decision/unstarted service](benchmarks/adaptive-speed-111/native-rejection-decision.json).
The [Rust buffered-reader documentation](https://doc.rust-lang.org/std/io/struct.BufReader.html)
supports batching repeated small reads, not the size of a Kestrel improvement.
