# Adaptive engine trial112

The candidate replaces long-scan window-to-scratch copies with borrowed block
views while preserving the original Reader structure and fallback method.
**Release qualification fails.** Supported main stays0.3.16;the isolated
0.3.17 candidate remains unreleased. This is not a new competitor comparison
or a universal benchmark win.

Workload-dependent collection,query-shape fusion and durable-ID replay remain
byte-exact from trials107,109 and110. Long streamed scans select query-local
read windows from requested range and needed-column count:at least eight
requested blocks,at most eight blocks per column,and512KiB total logical
payload. The new method borrows each block directly from the window and checks
its CRC before decoding. Short,wide,prefix,verification and compaction paths
retain their original behavior. The pre111 Reader structure,constructors,Drop
and single-block method are byte-exact;no new Reader state or global cache was
added. Cargo,file format,WAL,ACK and publication contracts stay unchanged.

Fresh772 tests across eight configurations,five strict all-target lints and
all normal/fault artifacts pass. The updated private counting test checks
exact signed bytes,six read/seek operations for38 consumed blocks,range/tails,
payload budget,truncation,failure invalidation and recovery;these are Read/
Seek operations,not an assertion of operating-system syscall counts. The five
parent scan integration tests and all other inherited tests remain byte-exact.
All359 recovery commands,28 fault cases,10 corruptions,CAT2/CAT3,two byte
fixtures,256 anonymous ACKs,two named scenarios and300 cold SQL checks pass.
The original preflight API return was unobserved across context compaction;
its shell exit is not claimed. A fresh strict idle guard0 and independent
unchanged pure recovery audit0 reproduce the completed proof and verify every
native actual wait/exit without relaunching workloads. The honest observation
and raw logs are retained. Excluded four Native/two service smokes,48 order
and29 negative controls pass. The complete80-statement pre-timing prefix
independently checks source inverses,fallback equality,build/recovery/smokes
and all12,735 frozen inputs.

All324 Native cases ran exactly once and the controller actually exited0.
479,232 ACKs and2,921,356,800 full CRC bytes independently pass raw rows,
receipt generations,indexes,SQL,quantiles,balanced orders and immutable inputs.
Performance fails25/153 A/A controls,13/171 regression guards and1/42 goals.
Every252 service case remains UNSTARTED/UNTESTED because Native qualification
failed. No selected scope/round,extra measurement,numerical retry or loosened
gate occurred. Native CPU/RSS,physical power loss and resource exhaustion were
not measured or tested. Supported0.3.17 remains unqualified.

## Goals verified in full and both halves

Eight goals pass targets and baseline controls in all three required scopes.
Percentages use paired within-round ratios and can differ from quotients of
displayed medians. These are specific Native results against0.3.16.

| Workload | Metric | Unit | Before median | After median | Full A/A | Paired candidate/A | Improvement | Halves |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| identified-replay | p95 | us | 1.700000 | 1.500000 | 0.97058824 | 0.87867647 | 12.13% | both pass |
| queries-late | grouped/median_us | us | 6512.200000 | 5842.500000 | 0.99316472 | 0.88642632 | 11.36% | both pass |
| queries-late | grouped/p95_us | us | 7946.800000 | 7407.600000 | 1.02702012 | 0.89416230 | 10.58% | both pass |
| queries-late | unordered_filter/median_us | us | 2929.850000 | 2234.300000 | 1.00178801 | 0.75902811 | 24.10% | both pass |
| queries-ordered | grouped/median_us | us | 6672.550000 | 5589.000000 | 0.96553496 | 0.86002926 | 14.00% | both pass |
| small-anonymous | wall | ms | 2539.592700 | 1853.972850 | 0.99714650 | 0.73372703 | 26.63% | both pass |
| small-named | p99 | ms | 19.738800 | 18.737650 | 0.98219222 | 0.88728840 | 11.27% | both pass |
| small-named | wall | ms | 2661.109650 | 1881.841350 | 0.99811852 | 0.68530556 | 31.47% | both pass |

Grouped medians now meet their10% goals with passing controls in full and both
halves:14.00% ordered and11.36% late. Late group p95 improves10.58% in full,
and its controls/targets also pass both halves. Ordered group p95/filter and
replay p99 gains remain control-inconclusive. This trial does not reclassify
earlier trials' failed or inconclusive results.

Calibrated guard misses remain:full sparse-named p95/p99 and pressure-anonymous
p99;half1 sparse-named p50/p95 and pressure-anonymous p99;half2 sparse-named,
pressure-anonymous and pressure-named p99,and late all-aggregates p95. Other
guard misses have failing controls and remain inconclusive. The sole goal
miss is small-anonymous p99 half2(C/A .978975,target .95,A/A1.040604).
No exclusive failure cause is established. The collector's chosen wait alone
does not explain durable publication,compaction,queueing or scheduling tails.

## Every before/after and gate

All171 full/half comparisons follow. Live units are milliseconds,queries and
replay microseconds,disk bytes. Controls require0.95..1.05;guards require at
most1.05. Small-write p99 goals require0.95;completion/filter/replay/grouped
goals require0.90. Every original maximum and raw stall remains preserved.

| Scope | Workload | Metric | Unit | Before median | After median | A/A | Control | Candidate/A | Regression | Goal |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- |
| full | sparse-anonymous | p50 | ms | 1.952550 | 1.993400 | 1.02452495 | pass | 1.01741477 | pass | - |
| full | sparse-anonymous | p95 | ms | 5.453350 | 5.739500 | 1.06241361 | FAIL | 1.03270142 | pass | - |
| full | sparse-anonymous | p99 | ms | 15.190750 | 14.797200 | 0.98215060 | pass | 0.99180452 | pass | - |
| full | sparse-anonymous | wall | ms | 1291.310800 | 1309.365300 | 1.02593369 | pass | 1.01099061 | pass | - |
| full | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| full | sparse-named | p50 | ms | 2.013450 | 2.175400 | 0.99028773 | pass | 1.04190592 | pass | - |
| full | sparse-named | p95 | ms | 5.740850 | 6.124600 | 0.99338336 | pass | 1.06398079 | FAIL | - |
| full | sparse-named | p99 | ms | 15.806000 | 16.977500 | 0.99552939 | pass | 1.06688256 | FAIL | - |
| full | sparse-named | wall | ms | 1331.128200 | 1412.264050 | 0.99579319 | pass | 1.01965704 | pass | - |
| full | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| full | small-anonymous | p50 | ms | 3.997600 | 2.274750 | 1.01377772 | pass | 0.56714227 | pass | - |
| full | small-anonymous | p95 | ms | 14.387900 | 9.848900 | 1.00267508 | pass | 0.68703576 | pass | - |
| full | small-anonymous | p99 | ms | 19.437050 | 17.534300 | 1.02387332 | pass | 0.93467496 | pass | pass <= 0.95 |
| full | small-anonymous | wall | ms | 2539.592700 | 1853.972850 | 0.99714650 | pass | 0.73372703 | pass | pass <= 0.90 |
| full | small-anonymous | disk | bytes | 5811311.000000 | 4974976.000000 | 1.00027195 | n/a | 0.90366114 | pass | - |
| full | small-named | p50 | ms | 4.263450 | 2.332200 | 0.99585617 | pass | 0.54661893 | pass | - |
| full | small-named | p95 | ms | 14.630450 | 9.660650 | 1.00590810 | pass | 0.63412914 | pass | - |
| full | small-named | p99 | ms | 19.738800 | 18.737650 | 0.98219222 | pass | 0.88728840 | pass | pass <= 0.95 |
| full | small-named | wall | ms | 2661.109650 | 1881.841350 | 0.99811852 | pass | 0.68530556 | pass | pass <= 0.90 |
| full | small-named | disk | bytes | 6491616.500000 | 5350409.500000 | 1.00128998 | n/a | 0.95226149 | pass | - |
| full | pressure-anonymous | p50 | ms | 2.428000 | 2.431550 | 1.02127725 | pass | 1.01501954 | pass | - |
| full | pressure-anonymous | p95 | ms | 9.227400 | 8.541150 | 1.00211944 | pass | 0.95530904 | pass | - |
| full | pressure-anonymous | p99 | ms | 19.095250 | 16.192900 | 1.03906376 | pass | 1.09296461 | FAIL | - |
| full | pressure-anonymous | wall | ms | 438.919000 | 440.959200 | 1.02368376 | pass | 1.00042762 | pass | - |
| full | pressure-anonymous | disk | bytes | 11465355.000000 | 11430466.000000 | 1.00024779 | n/a | 0.99649485 | pass | - |
| full | pressure-named | p50 | ms | 2.968450 | 3.013150 | 0.99643525 | pass | 0.99537050 | pass | - |
| full | pressure-named | p95 | ms | 10.845750 | 10.714600 | 0.95362830 | pass | 1.02248588 | pass | - |
| full | pressure-named | p99 | ms | 18.605500 | 18.244850 | 1.05436059 | FAIL | 1.01852979 | pass | - |
| full | pressure-named | wall | ms | 521.037850 | 525.521550 | 1.00035558 | pass | 0.99055914 | pass | - |
| full | pressure-named | disk | bytes | 12173285.000000 | 12159721.000000 | 1.00032196 | n/a | 0.99813204 | pass | - |
| full | queries-ordered | all_aggregates/median_us | us | 4.750000 | 4.700000 | 1.02105496 | pass | 0.97872340 | pass | - |
| full | queries-ordered | all_aggregates/p95_us | us | 5.550000 | 5.450000 | 1.01852487 | pass | 0.98181818 | pass | - |
| full | queries-ordered | broad_window/median_us | us | 5.000000 | 5.000000 | 1.00000000 | pass | 0.98039216 | pass | - |
| full | queries-ordered | broad_window/p95_us | us | 5.200000 | 5.150000 | 1.00000000 | pass | 1.00000000 | pass | - |
| full | queries-ordered | narrow_window/median_us | us | 4.050000 | 4.050000 | 1.00000000 | pass | 1.00000000 | pass | - |
| full | queries-ordered | narrow_window/p95_us | us | 4.200000 | 4.200000 | 1.00000000 | pass | 0.98837209 | pass | - |
| full | queries-ordered | unordered_filter/median_us | us | 2976.550000 | 2294.850000 | 0.94663444 | FAIL | 0.77249032 | pass | pass <= 0.90 |
| full | queries-ordered | unordered_filter/p95_us | us | 3877.250000 | 2801.000000 | 0.91794182 | FAIL | 0.78982553 | pass | pass <= 0.90 |
| full | queries-ordered | grouped/median_us | us | 6672.550000 | 5589.000000 | 0.96553496 | pass | 0.86002926 | pass | pass <= 0.90 |
| full | queries-ordered | grouped/p95_us | us | 9153.000000 | 6666.050000 | 0.88996906 | FAIL | 0.81785628 | pass | pass <= 0.90 |
| full | queries-ordered | min_max/median_us | us | 8.050000 | 7.350000 | 0.95428913 | pass | 0.94163293 | pass | - |
| full | queries-ordered | min_max/p95_us | us | 9.100000 | 7.550000 | 0.87871027 | FAIL | 0.84764001 | pass | - |
| full | queries-late | all_aggregates/median_us | us | 4.800000 | 4.750000 | 0.98000000 | pass | 0.97894504 | pass | - |
| full | queries-late | all_aggregates/p95_us | us | 5.700000 | 5.950000 | 0.96486903 | pass | 1.01851852 | pass | - |
| full | queries-late | broad_window/median_us | us | 5.150000 | 5.050000 | 0.99038462 | pass | 1.00000000 | pass | - |
| full | queries-late | broad_window/p95_us | us | 5.450000 | 5.200000 | 0.95385935 | pass | 0.96261356 | pass | - |
| full | queries-late | narrow_window/median_us | us | 4.200000 | 4.200000 | 1.00000000 | pass | 1.00000000 | pass | - |
| full | queries-late | narrow_window/p95_us | us | 4.400000 | 4.350000 | 0.98863636 | pass | 0.98888889 | pass | - |
| full | queries-late | unordered_filter/median_us | us | 2929.850000 | 2234.300000 | 1.00178801 | pass | 0.75902811 | pass | pass <= 0.90 |
| full | queries-late | unordered_filter/p95_us | us | 3532.750000 | 2848.000000 | 1.08372224 | FAIL | 0.78769409 | pass | pass <= 0.90 |
| full | queries-late | grouped/median_us | us | 6512.200000 | 5842.500000 | 0.99316472 | pass | 0.88642632 | pass | pass <= 0.90 |
| full | queries-late | grouped/p95_us | us | 7946.800000 | 7407.600000 | 1.02702012 | pass | 0.89416230 | pass | pass <= 0.90 |
| full | queries-late | min_max/median_us | us | 7.200000 | 7.150000 | 0.98611111 | pass | 0.97259760 | pass | - |
| full | queries-late | min_max/p95_us | us | 7.800000 | 7.450000 | 1.00694444 | pass | 0.94147737 | pass | - |
| full | identified-replay | p50 | us | 1.300000 | 1.100000 | 1.00000000 | pass | 0.83333333 | pass | - |
| full | identified-replay | p95 | us | 1.700000 | 1.500000 | 0.97058824 | pass | 0.87867647 | pass | pass <= 0.90 |
| full | identified-replay | p99 | us | 2.100000 | 1.900000 | 0.95238095 | pass | 0.87738095 | pass | pass <= 0.90 |
| half_1 | sparse-anonymous | p50 | ms | 1.942100 | 1.993400 | 1.01522393 | pass | 1.02077555 | pass | - |
| half_1 | sparse-anonymous | p95 | ms | 5.457300 | 5.574200 | 1.02474034 | pass | 1.01123675 | pass | - |
| half_1 | sparse-anonymous | p99 | ms | 15.238300 | 15.074900 | 0.95543668 | pass | 0.99526582 | pass | - |
| half_1 | sparse-anonymous | wall | ms | 1291.310800 | 1333.298450 | 1.00382219 | pass | 1.00762621 | pass | - |
| half_1 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_1 | sparse-named | p50 | ms | 2.010100 | 2.108000 | 1.01290575 | pass | 1.07066385 | FAIL | - |
| half_1 | sparse-named | p95 | ms | 6.023250 | 6.103850 | 0.97742783 | pass | 1.08143987 | FAIL | - |
| half_1 | sparse-named | p99 | ms | 16.477550 | 16.977500 | 0.97557002 | pass | 1.00438044 | pass | - |
| half_1 | sparse-named | wall | ms | 1331.128200 | 1403.622700 | 0.99221465 | pass | 1.03630641 | pass | - |
| half_1 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_1 | small-anonymous | p50 | ms | 3.991100 | 2.234200 | 1.00107933 | pass | 0.55185021 | pass | - |
| half_1 | small-anonymous | p95 | ms | 14.387900 | 9.896800 | 0.99810088 | pass | 0.69258135 | pass | - |
| half_1 | small-anonymous | p99 | ms | 20.275600 | 17.137250 | 0.98504582 | pass | 0.81734468 | pass | pass <= 0.95 |
| half_1 | small-anonymous | wall | ms | 2539.592700 | 1849.385700 | 0.97827066 | pass | 0.72190502 | pass | pass <= 0.90 |
| half_1 | small-anonymous | disk | bytes | 5816106.000000 | 5213739.500000 | 0.99988296 | n/a | 0.89622721 | pass | - |
| half_1 | small-named | p50 | ms | 4.263450 | 2.361900 | 1.01243068 | pass | 0.55149826 | pass | - |
| half_1 | small-named | p95 | ms | 14.257150 | 9.949900 | 1.03563130 | pass | 0.66205715 | pass | - |
| half_1 | small-named | p99 | ms | 21.745900 | 21.680350 | 0.98564547 | pass | 0.87550271 | pass | pass <= 0.95 |
| half_1 | small-named | wall | ms | 2963.383450 | 1888.666500 | 0.96921390 | pass | 0.65722229 | pass | pass <= 0.90 |
| half_1 | small-named | disk | bytes | 6435541.000000 | 5525574.000000 | 1.00319069 | n/a | 0.95354339 | pass | - |
| half_1 | pressure-anonymous | p50 | ms | 2.437500 | 2.413250 | 1.02741031 | pass | 1.01519236 | pass | - |
| half_1 | pressure-anonymous | p95 | ms | 8.142350 | 11.711650 | 1.21264806 | FAIL | 1.39141010 | FAIL | - |
| half_1 | pressure-anonymous | p99 | ms | 19.411050 | 16.059400 | 1.04922217 | pass | 1.06767888 | FAIL | - |
| half_1 | pressure-anonymous | wall | ms | 438.919000 | 458.737800 | 1.00883770 | pass | 1.00042762 | pass | - |
| half_1 | pressure-anonymous | disk | bytes | 11435407.500000 | 11419577.000000 | 1.00024779 | n/a | 0.99631501 | pass | - |
| half_1 | pressure-named | p50 | ms | 2.997600 | 3.044200 | 1.02187989 | pass | 1.00322320 | pass | - |
| half_1 | pressure-named | p95 | ms | 8.847200 | 10.714600 | 0.82231153 | FAIL | 1.21951365 | FAIL | - |
| half_1 | pressure-named | p99 | ms | 19.059100 | 18.375900 | 1.49115079 | FAIL | 0.97654595 | pass | - |
| half_1 | pressure-named | wall | ms | 519.457100 | 533.143400 | 1.09796735 | FAIL | 1.00989856 | pass | - |
| half_1 | pressure-named | disk | bytes | 12167349.500000 | 12159721.000000 | 1.00025063 | n/a | 0.99863301 | pass | - |
| half_1 | queries-ordered | all_aggregates/median_us | us | 4.850000 | 4.750000 | 0.98979592 | pass | 0.97915762 | pass | - |
| half_1 | queries-ordered | all_aggregates/p95_us | us | 5.700000 | 5.600000 | 1.05300128 | FAIL | 1.00000000 | pass | - |
| half_1 | queries-ordered | broad_window/median_us | us | 5.100000 | 5.000000 | 0.98039216 | pass | 0.98019608 | pass | - |
| half_1 | queries-ordered | broad_window/p95_us | us | 5.200000 | 5.250000 | 1.00000000 | pass | 0.99038462 | pass | - |
| half_1 | queries-ordered | narrow_window/median_us | us | 4.100000 | 4.000000 | 1.00000000 | pass | 0.97560976 | pass | - |
| half_1 | queries-ordered | narrow_window/p95_us | us | 4.300000 | 4.250000 | 1.00000000 | pass | 0.96511628 | pass | - |
| half_1 | queries-ordered | unordered_filter/median_us | us | 2976.550000 | 2320.550000 | 0.94663444 | FAIL | 0.79388409 | pass | pass <= 0.90 |
| half_1 | queries-ordered | unordered_filter/p95_us | us | 4014.650000 | 3245.450000 | 0.91794182 | FAIL | 0.85779326 | pass | pass <= 0.90 |
| half_1 | queries-ordered | grouped/median_us | us | 6672.550000 | 5726.750000 | 0.97357038 | pass | 0.87112373 | pass | pass <= 0.90 |
| half_1 | queries-ordered | grouped/p95_us | us | 9153.000000 | 6666.050000 | 0.88996906 | FAIL | 0.83107914 | pass | pass <= 0.90 |
| half_1 | queries-ordered | min_max/median_us | us | 8.350000 | 7.350000 | 0.94368132 | FAIL | 0.92578004 | pass | - |
| half_1 | queries-ordered | min_max/p95_us | us | 8.750000 | 7.550000 | 0.95631529 | pass | 0.91698595 | pass | - |
| half_1 | queries-late | all_aggregates/median_us | us | 4.800000 | 4.750000 | 0.97916667 | pass | 0.98958333 | pass | - |
| half_1 | queries-late | all_aggregates/p95_us | us | 5.700000 | 5.500000 | 0.96486903 | pass | 1.00942761 | pass | - |
| half_1 | queries-late | broad_window/median_us | us | 5.200000 | 5.050000 | 0.96153846 | pass | 0.98076923 | pass | - |
| half_1 | queries-late | broad_window/p95_us | us | 5.750000 | 5.250000 | 0.90736158 | FAIL | 0.96261356 | pass | - |
| half_1 | queries-late | narrow_window/median_us | us | 4.200000 | 4.200000 | 0.97674419 | pass | 0.98837209 | pass | - |
| half_1 | queries-late | narrow_window/p95_us | us | 4.350000 | 4.400000 | 0.98863636 | pass | 0.98888889 | pass | - |
| half_1 | queries-late | unordered_filter/median_us | us | 3003.700000 | 2387.650000 | 1.02281605 | pass | 0.77882876 | pass | pass <= 0.90 |
| half_1 | queries-late | unordered_filter/p95_us | us | 3532.750000 | 3437.150000 | 1.17164051 | FAIL | 0.88822642 | pass | pass <= 0.90 |
| half_1 | queries-late | grouped/median_us | us | 6667.650000 | 5842.500000 | 0.99270466 | pass | 0.85995615 | pass | pass <= 0.90 |
| half_1 | queries-late | grouped/p95_us | us | 8013.950000 | 8183.850000 | 1.04027830 | pass | 0.89314945 | pass | pass <= 0.90 |
| half_1 | queries-late | min_max/median_us | us | 7.300000 | 7.200000 | 0.98601330 | pass | 0.97240198 | pass | - |
| half_1 | queries-late | min_max/p95_us | us | 8.200000 | 7.700000 | 1.23239437 | FAIL | 0.92772792 | pass | - |
| half_1 | identified-replay | p50 | us | 1.300000 | 1.050000 | 1.00000000 | pass | 0.80128205 | pass | - |
| half_1 | identified-replay | p95 | us | 1.750000 | 1.500000 | 0.97058824 | pass | 0.87867647 | pass | pass <= 0.90 |
| half_1 | identified-replay | p99 | us | 2.100000 | 1.900000 | 0.97619048 | pass | 0.87738095 | pass | pass <= 0.90 |
| half_2 | sparse-anonymous | p50 | ms | 1.962900 | 1.963400 | 1.02452495 | pass | 1.01558796 | pass | - |
| half_2 | sparse-anonymous | p95 | ms | 5.400700 | 5.854300 | 1.11209719 | FAIL | 1.06208596 | FAIL | - |
| half_2 | sparse-anonymous | p99 | ms | 14.456550 | 14.478350 | 1.02554066 | pass | 0.98534583 | pass | - |
| half_2 | sparse-anonymous | wall | ms | 1288.047250 | 1300.434300 | 1.04520457 | pass | 1.01313019 | pass | - |
| half_2 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_2 | sparse-named | p50 | ms | 2.045600 | 2.175400 | 0.99028773 | pass | 1.02311902 | pass | - |
| half_2 | sparse-named | p95 | ms | 5.602850 | 6.130550 | 0.99835887 | pass | 1.04882511 | pass | - |
| half_2 | sparse-named | p99 | ms | 14.808100 | 16.672500 | 1.03435631 | pass | 1.09439228 | FAIL | - |
| half_2 | sparse-named | wall | ms | 1332.797950 | 1412.264050 | 1.00086626 | pass | 1.01965704 | pass | - |
| half_2 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_2 | small-anonymous | p50 | ms | 4.062850 | 2.307450 | 1.02053937 | pass | 0.57214198 | pass | - |
| half_2 | small-anonymous | p95 | ms | 14.530550 | 9.672050 | 1.00267508 | pass | 0.67287653 | pass | - |
| half_2 | small-anonymous | p99 | ms | 18.113200 | 18.307200 | 1.04060425 | pass | 0.97897512 | pass | FAIL <= 0.95 |
| half_2 | small-anonymous | wall | ms | 2537.839200 | 1871.847850 | 1.01784979 | pass | 0.74846041 | pass | pass <= 0.90 |
| half_2 | small-anonymous | disk | bytes | 5803353.500000 | 4959958.500000 | 1.00267016 | n/a | 0.90594867 | pass | - |
| half_2 | small-named | p50 | ms | 4.235000 | 2.332200 | 0.98843722 | pass | 0.54334043 | pass | - |
| half_2 | small-named | p95 | ms | 14.630450 | 9.086100 | 1.00367998 | pass | 0.61545599 | pass | - |
| half_2 | small-named | p99 | ms | 18.828600 | 16.902650 | 0.98219222 | pass | 0.90297274 | pass | pass <= 0.95 |
| half_2 | small-named | wall | ms | 2654.998450 | 1871.980250 | 1.01938881 | pass | 0.70282979 | pass | pass <= 0.90 |
| half_2 | small-named | disk | bytes | 6533689.500000 | 5350409.500000 | 1.00060327 | n/a | 0.95163864 | pass | - |
| half_2 | pressure-anonymous | p50 | ms | 2.396100 | 2.431550 | 1.00282723 | pass | 1.00834076 | pass | - |
| half_2 | pressure-anonymous | p95 | ms | 10.820700 | 6.659550 | 1.00211944 | pass | 0.63827029 | pass | - |
| half_2 | pressure-anonymous | p99 | ms | 17.479150 | 18.212250 | 0.95806470 | pass | 1.10831489 | FAIL | - |
| half_2 | pressure-anonymous | wall | ms | 443.191850 | 440.257250 | 1.03036683 | pass | 0.99665455 | pass | - |
| half_2 | pressure-anonymous | disk | bytes | 11475809.500000 | 11446496.500000 | 1.00019187 | n/a | 0.99745297 | pass | - |
| half_2 | pressure-named | p50 | ms | 2.955800 | 2.898100 | 0.96040225 | pass | 0.96979967 | pass | - |
| half_2 | pressure-named | p95 | ms | 11.861150 | 9.953850 | 0.99554292 | pass | 0.88464338 | pass | - |
| half_2 | pressure-named | p99 | ms | 17.056150 | 17.550800 | 1.01880582 | pass | 1.07202855 | FAIL | - |
| half_2 | pressure-named | wall | ms | 529.672550 | 513.848050 | 0.95133987 | pass | 0.95396334 | pass | - |
| half_2 | pressure-named | disk | bytes | 12173679.500000 | 12161472.500000 | 1.00032196 | n/a | 0.99813204 | pass | - |
| half_2 | queries-ordered | all_aggregates/median_us | us | 4.700000 | 4.600000 | 1.02127660 | pass | 0.97872340 | pass | - |
| half_2 | queries-ordered | all_aggregates/p95_us | us | 5.500000 | 5.300000 | 1.00016234 | pass | 0.96363636 | pass | - |
| half_2 | queries-ordered | broad_window/median_us | us | 5.000000 | 4.950000 | 1.02000000 | pass | 1.00000000 | pass | - |
| half_2 | queries-ordered | broad_window/p95_us | us | 5.200000 | 5.100000 | 1.00000000 | pass | 1.00000000 | pass | - |
| half_2 | queries-ordered | narrow_window/median_us | us | 4.000000 | 4.100000 | 1.00000000 | pass | 1.00000000 | pass | - |
| half_2 | queries-ordered | narrow_window/p95_us | us | 4.200000 | 4.200000 | 1.00000000 | pass | 1.00000000 | pass | - |
| half_2 | queries-ordered | unordered_filter/median_us | us | 2962.500000 | 2110.750000 | 0.94808251 | FAIL | 0.74613293 | pass | pass <= 0.90 |
| half_2 | queries-ordered | unordered_filter/p95_us | us | 3533.350000 | 2430.750000 | 0.94189930 | FAIL | 0.78982553 | pass | pass <= 0.90 |
| half_2 | queries-ordered | grouped/median_us | us | 6546.800000 | 5499.500000 | 0.96553496 | pass | 0.85122913 | pass | pass <= 0.90 |
| half_2 | queries-ordered | grouped/p95_us | us | 8881.150000 | 6727.100000 | 0.83047193 | FAIL | 0.80648856 | pass | pass <= 0.90 |
| half_2 | queries-ordered | min_max/median_us | us | 7.650000 | 7.350000 | 0.95428913 | pass | 0.94771018 | pass | - |
| half_2 | queries-ordered | min_max/p95_us | us | 12.600000 | 7.500000 | 0.64824364 | FAIL | 0.61475991 | pass | - |
| half_2 | queries-late | all_aggregates/median_us | us | 4.900000 | 4.700000 | 0.98000000 | pass | 0.96852837 | pass | - |
| half_2 | queries-late | all_aggregates/p95_us | us | 5.750000 | 6.750000 | 0.96313131 | pass | 1.15454545 | FAIL | - |
| half_2 | queries-late | broad_window/median_us | us | 5.050000 | 5.000000 | 1.01020408 | pass | 1.00980392 | pass | - |
| half_2 | queries-late | broad_window/p95_us | us | 5.400000 | 5.150000 | 0.97272727 | pass | 0.97115385 | pass | - |
| half_2 | queries-late | narrow_window/median_us | us | 4.200000 | 4.100000 | 1.01063830 | pass | 1.00000000 | pass | - |
| half_2 | queries-late | narrow_window/p95_us | us | 4.400000 | 4.250000 | 0.98809524 | pass | 0.98863636 | pass | - |
| half_2 | queries-late | unordered_filter/median_us | us | 2874.400000 | 2211.000000 | 1.00177156 | pass | 0.75902811 | pass | pass <= 0.90 |
| half_2 | queries-late | unordered_filter/p95_us | us | 3796.450000 | 2548.800000 | 0.98876847 | pass | 0.65947211 | pass | pass <= 0.90 |
| half_2 | queries-late | grouped/median_us | us | 6361.100000 | 5824.150000 | 1.00227194 | pass | 0.89522111 | pass | pass <= 0.90 |
| half_2 | queries-late | grouped/p95_us | us | 7946.800000 | 7407.600000 | 0.97657977 | pass | 0.89416230 | pass | pass <= 0.90 |
| half_2 | queries-late | min_max/median_us | us | 7.200000 | 7.050000 | 0.99305556 | pass | 0.97896825 | pass | - |
| half_2 | queries-late | min_max/p95_us | us | 7.700000 | 7.250000 | 1.00694444 | pass | 0.94202532 | pass | - |
| half_2 | identified-replay | p50 | us | 1.300000 | 1.100000 | 1.00000000 | pass | 0.83974359 | pass | - |
| half_2 | identified-replay | p95 | us | 1.700000 | 1.500000 | 0.99836601 | pass | 0.88541667 | pass | pass <= 0.90 |
| half_2 | identified-replay | p99 | us | 2.100000 | 1.950000 | 0.93452381 | FAIL | 0.89035088 | pass | pass <= 0.90 |

## Exact preservation and next work

The archive contains 32,436 files, 3,575
directories, 50 bounded ZIP parts and
3,916,904,484 logical bytes. All member checksums, order,
offsets, sizes, complete original/restored file hashes and directory sets passed
before and after the complete independent restored audit. It launched no Native
processes or timers and changed no existing files. Only inventoried regenerable
build/Python caches are excluded; all originals remain. Closed raw logs are
byte-exact gzip supplements with both raw and encoded hashes. No complete
verified private GitHub backup or recent raw deletion is claimed.

Next justified investigation: diagnose the remaining sparse/pressure ACK
tails by separating publication,compaction,queueing and scheduling evidence.
Avoid speculative collector tuning or declaring one aggregate phase the sole
cause. Query-shape dispatch and borrowed windows have specific verified gains,
but candidate adoption still needs every mandatory Native/service/correctness/
recovery/restoration gate. New engine work needs a new experiment number and
predeclared balanced baselines,controls,goals and complete raw preservation.
Older106/107 rejection and108 diagnostic archival closures remain pending;
every original and failure is safe.

See [reproduction](benchmarks/adaptive-speed-112/REPRODUCE.md),
[complete audit](benchmarks/adaptive-speed-112/complete-audit-proof.json),
[restored audit](benchmarks/adaptive-speed-112/restored-audit-proof.json),
[Native raw replay](benchmarks/adaptive-speed-112/native-audit.json) and
[decision/unstarted service](benchmarks/adaptive-speed-112/native-rejection-decision.json).
