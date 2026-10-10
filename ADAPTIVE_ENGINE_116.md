# Adaptive grouped-range trial 116

The isolated candidate improves grouped-query medians against supported
0.3.16, but fails full release qualification. **0.3.17 remains unqualified
and unreleased; supported main remains byte-exact 0.3.16.** All 324 cases
are correct. Performance fails 21 of 153 A/A controls, five of 171 guards
and three of 42 goals. All 252 service cases are unstarted and untested.

The new query path consumes contiguous decoded ranges when dense groups and
one shared SUM/AVG accumulator exist and sorted bounds enforce every predicate,
or there are no predicates. Other shapes retain the existing kernel. It avoids
the selected-row vector and indirect row loads. Existing dense/sparse groups
and shared SUM/AVG are already implemented and are not claimed as new.
Same memory/domain caps, checked equal-length slices, CRC validation before
reduction, i128 totals, counts, output order, limits and errors are preserved.
The original Reader, collector, serial flushing, formats and receipts remain.
Exact Archive/Cargo byte inverses to serial112 and all other hashes pass.

This is the combined experimental candidate (collector107/filter109/replay110/
borrowed scan112/group-range116) versus fresh same-D: supported016 baselines.
It does not isolate the 116-versus112 effect. Always-concurrent flushing from
rejected114 is separate. No old C: result is used as a direct baseline.

All 796 fresh test executions across eight configurations, five strict lints,
normal/fault binaries and 359 fresh recovery commands pass. Four private units
and two integration tests cover signed limits, wide sums, shared projections,
partial/empty/repeated ranges, multiple segments, unsupported filters/shapes,
sparse domains and cold CRC errors. Recovery includes 28 fault boundaries,
ten corruptions, two historical formats, byte-equivalence, concurrent ACKs and
300 cold SQL checks. Actual current controller API exits are observed zero.
The historical112 unobserved recovery API return remains recorded honestly.

Four Native/two service excluded smokes, 48 order checks, six conserved-outcome
negatives and two invalid orders pass. All 324 fixed D: cases ran once with
twelve rounds and all six A/A/C orders balanced in full and both halves.
All 479,232 ACKs and 2,921,356,800 CRC bytes independently pass complete rows,
indexes, receipt generations/digests, current metadata, cold SQLite SQL and
raw quantiles. All stalls, maxima, failed scopes and raw streams remain.
No selected round, extra timing, numerical retry or changed gate occurred.

## Controlled gains and remaining failures

These seven goal metrics meet targets with passing corresponding A/A controls
in full and both halves. Percentages use full within-round paired ratios,
which need not equal the quotient of the displayed medians.

| Workload | Metric | Unit | 016 baseline median | Candidate median | Full paired reduction | Full A/A | Full/both-half goal and controls |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| queries-late | grouped/median_us | us | 6433.200000 | 5153.150000 | 20.91% | 1.01824952 | pass |
| queries-late | unordered_filter/median_us | us | 2912.250000 | 2165.850000 | 25.91% | 1.02328696 | pass |
| queries-ordered | grouped/median_us | us | 6386.450000 | 5073.300000 | 21.94% | 1.01276905 | pass |
| queries-ordered | unordered_filter/median_us | us | 2898.150000 | 2132.000000 | 26.35% | 1.00602911 | pass |
| small-anonymous | p99 | ms | 18.095450 | 16.640150 | 6.42% | 1.00340645 | pass |
| small-anonymous | wall | ms | 2520.315600 | 1821.123250 | 27.82% | 0.99565441 | pass |
| small-named | wall | ms | 2592.871200 | 1860.145350 | 28.36% | 0.99529694 | pass |

Grouped p95 is not a controlled win across all required scopes: ordered full
and half1 controls fail; late half1 and half2 controls fail. Numerical target
passes do not override those failures. Calibrated guard regressions include
sparse-anonymous half1 p99 +5.39%, sparse-named half1 p95 +6.37% and
pressure-anonymous half2 p99 +7.61%. Full pressure p99 and named pressure
half1 p95 also fail guards with failing controls and remain inconclusive.
The three calibrated target misses are small-named half1 p99 and identified
replay half1 p95/p99. All controls, guards and goals remain mandatory.

Safe checked range access follows the primary [Rust slice documentation](https://doc.rust-lang.org/std/primitive.slice.html#method.get).
The [zip documentation](https://doc.rust-lang.org/std/iter/trait.Iterator.html#method.zip)
motivates the explicit equal-length/range checks. Online docs are 1.99;
the actual build uses stable APIs on local Rust1.97.1.

## Every before/after comparison

All 171 full/half comparisons follow. A/A requires 0.95–1.05; guards require
C/A at most 1.05. Goals retain their original metric-specific stricter limits.
Disk has no A/A control. A failed guard remains recorded when its control fails.

| Scope | Workload | Metric | Unit | Baseline median | Candidate median | A/A | Control | C/A | Guard | Goal limit | Goal |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | ---: | --- |
| full | sparse-anonymous | p50 | ms | 1.925000 | 1.987050 | 1.00862217 | pass | 1.02065775 | pass | n/a | n/a |
| full | sparse-anonymous | p95 | ms | 5.255000 | 5.644700 | 1.04370405 | pass | 0.99567766 | pass | n/a | n/a |
| full | sparse-anonymous | p99 | ms | 14.556200 | 15.051250 | 1.01199479 | pass | 1.02416056 | pass | n/a | n/a |
| full | sparse-anonymous | wall | ms | 1266.028100 | 1312.225350 | 1.01682869 | pass | 1.02279383 | pass | n/a | n/a |
| full | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| full | sparse-named | p50 | ms | 2.043800 | 2.000450 | 1.00383491 | pass | 1.00281560 | pass | n/a | n/a |
| full | sparse-named | p95 | ms | 5.729750 | 5.891750 | 0.97644602 | pass | 1.04210692 | pass | n/a | n/a |
| full | sparse-named | p99 | ms | 15.493000 | 14.744400 | 1.02760621 | pass | 0.97058010 | pass | n/a | n/a |
| full | sparse-named | wall | ms | 1350.611050 | 1316.314850 | 0.99838834 | pass | 1.00164993 | pass | n/a | n/a |
| full | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| full | small-anonymous | p50 | ms | 4.016550 | 2.205250 | 0.99337784 | pass | 0.55567760 | pass | n/a | n/a |
| full | small-anonymous | p95 | ms | 14.278200 | 9.541700 | 1.00792244 | pass | 0.65227599 | pass | n/a | n/a |
| full | small-anonymous | p99 | ms | 18.095450 | 16.640150 | 1.00340645 | pass | 0.93584683 | pass | 0.95 | pass |
| full | small-anonymous | wall | ms | 2520.315600 | 1821.123250 | 0.99565441 | pass | 0.72177264 | pass | 0.9 | pass |
| full | small-anonymous | disk | bytes | 5817146.500000 | 4966571.000000 | 1.00142431 | n/a | 0.89666743 | pass | n/a | n/a |
| full | small-named | p50 | ms | 4.213550 | 2.412900 | 0.99438740 | pass | 0.56885228 | pass | n/a | n/a |
| full | small-named | p95 | ms | 14.773000 | 9.867400 | 0.99792720 | pass | 0.66042410 | pass | n/a | n/a |
| full | small-named | p99 | ms | 18.264200 | 18.121650 | 0.99906335 | pass | 0.94934439 | pass | 0.95 | pass |
| full | small-named | wall | ms | 2592.871200 | 1860.145350 | 0.99529694 | pass | 0.71639655 | pass | 0.9 | pass |
| full | small-named | disk | bytes | 6417433.500000 | 6211676.500000 | 1.02063677 | n/a | 0.96939799 | pass | n/a | n/a |
| full | pressure-anonymous | p50 | ms | 2.374400 | 2.403250 | 1.00036370 | pass | 1.02971866 | pass | n/a | n/a |
| full | pressure-anonymous | p95 | ms | 7.917000 | 7.737750 | 1.05307932 | FAIL | 0.97801861 | pass | n/a | n/a |
| full | pressure-anonymous | p99 | ms | 19.566250 | 17.945600 | 0.85022172 | FAIL | 1.07611403 | FAIL | n/a | n/a |
| full | pressure-anonymous | wall | ms | 429.379950 | 438.435850 | 1.00452421 | pass | 1.02402818 | pass | n/a | n/a |
| full | pressure-anonymous | disk | bytes | 11440262.000000 | 11424515.500000 | 1.00069811 | n/a | 0.99907659 | pass | n/a | n/a |
| full | pressure-named | p50 | ms | 3.026300 | 3.020700 | 0.98948871 | pass | 1.02733937 | pass | n/a | n/a |
| full | pressure-named | p95 | ms | 12.231550 | 9.994250 | 1.07075494 | FAIL | 0.94197962 | pass | n/a | n/a |
| full | pressure-named | p99 | ms | 20.360300 | 16.673250 | 0.90231991 | FAIL | 0.95657381 | pass | n/a | n/a |
| full | pressure-named | wall | ms | 520.251150 | 520.067500 | 0.99715250 | pass | 1.00770840 | pass | n/a | n/a |
| full | pressure-named | disk | bytes | 12170486.500000 | 12171062.500000 | 1.00038098 | n/a | 0.99971350 | pass | n/a | n/a |
| full | queries-ordered | all_aggregates/median_us | us | 4.850000 | 4.700000 | 0.97916667 | pass | 0.97916667 | pass | n/a | n/a |
| full | queries-ordered | all_aggregates/p95_us | us | 5.550000 | 5.200000 | 0.98113208 | pass | 0.94541779 | pass | n/a | n/a |
| full | queries-ordered | broad_window/median_us | us | 5.050000 | 5.000000 | 0.97360656 | pass | 1.00000000 | pass | n/a | n/a |
| full | queries-ordered | broad_window/p95_us | us | 5.350000 | 5.200000 | 0.97475962 | pass | 1.00018854 | pass | n/a | n/a |
| full | queries-ordered | narrow_window/median_us | us | 4.150000 | 4.100000 | 0.98809524 | pass | 1.00000000 | pass | n/a | n/a |
| full | queries-ordered | narrow_window/p95_us | us | 4.400000 | 4.250000 | 0.96950417 | pass | 0.96564482 | pass | n/a | n/a |
| full | queries-ordered | unordered_filter/median_us | us | 2898.150000 | 2132.000000 | 1.00602911 | pass | 0.73650046 | pass | 0.9 | pass |
| full | queries-ordered | unordered_filter/p95_us | us | 3708.850000 | 2656.700000 | 1.05980394 | FAIL | 0.74572493 | pass | 0.9 | pass |
| full | queries-ordered | grouped/median_us | us | 6386.450000 | 5073.300000 | 1.01276905 | pass | 0.78055744 | pass | 0.9 | pass |
| full | queries-ordered | grouped/p95_us | us | 7688.650000 | 6237.000000 | 1.06027706 | FAIL | 0.83437527 | pass | 0.9 | pass |
| full | queries-ordered | min_max/median_us | us | 7.550000 | 7.500000 | 1.00649351 | pass | 1.00000000 | pass | n/a | n/a |
| full | queries-ordered | min_max/p95_us | us | 8.000000 | 7.800000 | 1.01258310 | pass | 0.98726063 | pass | n/a | n/a |
| full | queries-late | all_aggregates/median_us | us | 4.850000 | 4.750000 | 1.00000000 | pass | 1.00000000 | pass | n/a | n/a |
| full | queries-late | all_aggregates/p95_us | us | 5.400000 | 5.300000 | 0.99074074 | pass | 1.00000000 | pass | n/a | n/a |
| full | queries-late | broad_window/median_us | us | 5.050000 | 5.000000 | 1.01000000 | pass | 1.00000000 | pass | n/a | n/a |
| full | queries-late | broad_window/p95_us | us | 5.350000 | 5.200000 | 1.00980392 | pass | 0.97272727 | pass | n/a | n/a |
| full | queries-late | narrow_window/median_us | us | 4.200000 | 4.100000 | 0.97590012 | pass | 0.97619048 | pass | n/a | n/a |
| full | queries-late | narrow_window/p95_us | us | 4.400000 | 4.350000 | 0.97674419 | pass | 0.98863636 | pass | n/a | n/a |
| full | queries-late | unordered_filter/median_us | us | 2912.250000 | 2165.850000 | 1.02328696 | pass | 0.74091458 | pass | 0.9 | pass |
| full | queries-late | unordered_filter/p95_us | us | 3762.300000 | 2691.850000 | 1.06747230 | FAIL | 0.77758871 | pass | 0.9 | pass |
| full | queries-late | grouped/median_us | us | 6433.200000 | 5153.150000 | 1.01824952 | pass | 0.79088379 | pass | 0.9 | pass |
| full | queries-late | grouped/p95_us | us | 7915.050000 | 6779.650000 | 0.98699513 | pass | 0.85164001 | pass | 0.9 | pass |
| full | queries-late | min_max/median_us | us | 7.100000 | 7.150000 | 1.01853651 | pass | 1.02133088 | pass | n/a | n/a |
| full | queries-late | min_max/p95_us | us | 7.400000 | 7.500000 | 0.99324324 | pass | 1.00000000 | pass | n/a | n/a |
| full | identified-replay | p50 | us | 1.300000 | 1.050000 | 1.00000000 | pass | 0.76923077 | pass | n/a | n/a |
| full | identified-replay | p95 | us | 1.750000 | 1.500000 | 1.00000000 | pass | 0.82352941 | pass | 0.9 | pass |
| full | identified-replay | p99 | us | 2.150000 | 1.900000 | 1.04545455 | pass | 0.86038961 | pass | 0.9 | pass |
| half_1 | sparse-anonymous | p50 | ms | 1.956150 | 2.028950 | 1.01976014 | pass | 1.04556698 | pass | n/a | n/a |
| half_1 | sparse-anonymous | p95 | ms | 5.317500 | 5.720750 | 1.00765778 | pass | 1.00027300 | pass | n/a | n/a |
| half_1 | sparse-anonymous | p99 | ms | 14.792350 | 16.074450 | 1.02397952 | pass | 1.05387450 | FAIL | n/a | n/a |
| half_1 | sparse-anonymous | wall | ms | 1266.028100 | 1341.442900 | 1.03036573 | pass | 1.04181073 | pass | n/a | n/a |
| half_1 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| half_1 | sparse-named | p50 | ms | 2.140400 | 2.063250 | 0.98308038 | pass | 1.00740774 | pass | n/a | n/a |
| half_1 | sparse-named | p95 | ms | 5.975050 | 6.143400 | 0.96378216 | pass | 1.06372277 | FAIL | n/a | n/a |
| half_1 | sparse-named | p99 | ms | 16.560400 | 15.523300 | 1.03107842 | pass | 1.01649856 | pass | n/a | n/a |
| half_1 | sparse-named | wall | ms | 1418.828550 | 1349.798450 | 1.00637368 | pass | 1.02726264 | pass | n/a | n/a |
| half_1 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| half_1 | small-anonymous | p50 | ms | 4.064300 | 2.269100 | 0.99337784 | pass | 0.55613065 | pass | n/a | n/a |
| half_1 | small-anonymous | p95 | ms | 14.542800 | 9.126150 | 1.00792244 | pass | 0.64911555 | pass | n/a | n/a |
| half_1 | small-anonymous | p99 | ms | 18.455000 | 16.981600 | 1.00752303 | pass | 0.93584683 | pass | 0.95 | pass |
| half_1 | small-anonymous | wall | ms | 2540.400150 | 1821.123250 | 0.99844004 | pass | 0.72174847 | pass | 0.9 | pass |
| half_1 | small-anonymous | disk | bytes | 5820867.000000 | 4973696.500000 | 1.00223430 | n/a | 0.89552807 | pass | n/a | n/a |
| half_1 | small-named | p50 | ms | 4.256850 | 2.422500 | 0.99942644 | pass | 0.57113610 | pass | n/a | n/a |
| half_1 | small-named | p95 | ms | 15.025750 | 9.987100 | 0.99635042 | pass | 0.66333386 | pass | n/a | n/a |
| half_1 | small-named | p99 | ms | 18.572100 | 18.121650 | 0.99906335 | pass | 0.98397598 | pass | 0.95 | FAIL |
| half_1 | small-named | wall | ms | 2597.670200 | 1881.271500 | 0.99917514 | pass | 0.73938816 | pass | 0.9 | pass |
| half_1 | small-named | disk | bytes | 6430469.000000 | 6211676.500000 | 0.99401000 | n/a | 0.96036388 | pass | n/a | n/a |
| half_1 | pressure-anonymous | p50 | ms | 2.455750 | 2.481600 | 0.99811281 | pass | 1.03071384 | pass | n/a | n/a |
| half_1 | pressure-anonymous | p95 | ms | 6.891200 | 6.664500 | 1.03542073 | pass | 0.96002963 | pass | n/a | n/a |
| half_1 | pressure-anonymous | p99 | ms | 21.032600 | 20.318550 | 0.73143599 | FAIL | 1.04972474 | pass | n/a | n/a |
| half_1 | pressure-anonymous | wall | ms | 432.920100 | 433.111600 | 0.99318265 | pass | 1.01854180 | pass | n/a | n/a |
| half_1 | pressure-anonymous | disk | bytes | 9890213.500000 | 10651203.000000 | 1.15493555 | n/a | 1.00187246 | pass | n/a | n/a |
| half_1 | pressure-named | p50 | ms | 3.026300 | 3.088200 | 0.99671369 | pass | 1.03650965 | pass | n/a | n/a |
| half_1 | pressure-named | p95 | ms | 8.379900 | 11.098000 | 1.45881677 | FAIL | 1.51845602 | FAIL | n/a | n/a |
| half_1 | pressure-named | p99 | ms | 22.157500 | 16.390850 | 0.74424979 | FAIL | 0.86229179 | pass | n/a | n/a |
| half_1 | pressure-named | wall | ms | 520.251150 | 531.783750 | 1.02805261 | pass | 1.01963175 | pass | n/a | n/a |
| half_1 | pressure-named | disk | bytes | 12167500.000000 | 12165897.000000 | 1.00279190 | n/a | 1.00000134 | pass | n/a | n/a |
| half_1 | queries-ordered | all_aggregates/median_us | us | 4.950000 | 4.700000 | 0.97916667 | pass | 0.97916667 | pass | n/a | n/a |
| half_1 | queries-ordered | all_aggregates/p95_us | us | 5.450000 | 5.300000 | 1.02628032 | pass | 0.99056604 | pass | n/a | n/a |
| half_1 | queries-ordered | broad_window/median_us | us | 5.200000 | 5.000000 | 0.96473863 | pass | 0.99019608 | pass | n/a | n/a |
| half_1 | queries-ordered | broad_window/p95_us | us | 5.350000 | 5.200000 | 0.97475962 | pass | 1.00018854 | pass | n/a | n/a |
| half_1 | queries-ordered | narrow_window/median_us | us | 4.250000 | 4.100000 | 0.98809524 | pass | 0.98809524 | pass | n/a | n/a |
| half_1 | queries-ordered | narrow_window/p95_us | us | 4.400000 | 4.250000 | 0.98113208 | pass | 0.97727273 | pass | n/a | n/a |
| half_1 | queries-ordered | unordered_filter/median_us | us | 3058.850000 | 2199.700000 | 1.04134204 | pass | 0.74512391 | pass | 0.9 | pass |
| half_1 | queries-ordered | unordered_filter/p95_us | us | 3583.000000 | 3017.100000 | 1.04285801 | pass | 0.79357593 | pass | 0.9 | pass |
| half_1 | queries-ordered | grouped/median_us | us | 6532.500000 | 5176.900000 | 1.04008323 | pass | 0.79249850 | pass | 0.9 | pass |
| half_1 | queries-ordered | grouped/p95_us | us | 7593.150000 | 6438.200000 | 1.14937359 | FAIL | 0.85142102 | pass | 0.9 | pass |
| half_1 | queries-ordered | min_max/median_us | us | 7.600000 | 7.450000 | 1.00649351 | pass | 0.99342105 | pass | n/a | n/a |
| half_1 | queries-ordered | min_max/p95_us | us | 8.000000 | 7.750000 | 1.01258310 | pass | 0.98726063 | pass | n/a | n/a |
| half_1 | queries-late | all_aggregates/median_us | us | 5.000000 | 4.750000 | 0.97980442 | pass | 0.96938776 | pass | n/a | n/a |
| half_1 | queries-late | all_aggregates/p95_us | us | 5.550000 | 5.450000 | 0.97288360 | pass | 0.98148148 | pass | n/a | n/a |
| half_1 | queries-late | broad_window/median_us | us | 5.250000 | 5.100000 | 0.98113208 | pass | 0.99019608 | pass | n/a | n/a |
| half_1 | queries-late | broad_window/p95_us | us | 5.850000 | 5.300000 | 1.23275862 | FAIL | 0.90590298 | pass | n/a | n/a |
| half_1 | queries-late | narrow_window/median_us | us | 4.300000 | 4.200000 | 0.95346320 | pass | 0.96428571 | pass | n/a | n/a |
| half_1 | queries-late | narrow_window/p95_us | us | 4.650000 | 4.400000 | 0.95428118 | pass | 0.96614987 | pass | n/a | n/a |
| half_1 | queries-late | unordered_filter/median_us | us | 3116.150000 | 2248.100000 | 1.04485916 | pass | 0.73634152 | pass | 0.9 | pass |
| half_1 | queries-late | unordered_filter/p95_us | us | 4508.100000 | 3034.550000 | 0.93490740 | FAIL | 0.78028373 | pass | 0.9 | pass |
| half_1 | queries-late | grouped/median_us | us | 6453.700000 | 5264.150000 | 1.02369931 | pass | 0.80859580 | pass | 0.9 | pass |
| half_1 | queries-late | grouped/p95_us | us | 8609.950000 | 7703.250000 | 0.94129314 | FAIL | 0.85528655 | pass | 0.9 | pass |
| half_1 | queries-late | min_max/median_us | us | 7.100000 | 7.300000 | 1.01853651 | pass | 1.01983163 | pass | n/a | n/a |
| half_1 | queries-late | min_max/p95_us | us | 7.400000 | 8.300000 | 1.00000000 | pass | 1.01379119 | pass | n/a | n/a |
| half_1 | identified-replay | p50 | us | 1.300000 | 1.100000 | 1.00000000 | pass | 0.80769231 | pass | n/a | n/a |
| half_1 | identified-replay | p95 | us | 1.700000 | 1.550000 | 1.02777778 | pass | 0.91176471 | pass | 0.9 | FAIL |
| half_1 | identified-replay | p99 | us | 2.050000 | 1.900000 | 1.04772727 | pass | 0.90681818 | pass | 0.9 | FAIL |
| half_2 | sparse-anonymous | p50 | ms | 1.888050 | 1.879900 | 0.99842643 | pass | 1.00461095 | pass | n/a | n/a |
| half_2 | sparse-anonymous | p95 | ms | 5.157700 | 5.405150 | 1.05833116 | FAIL | 0.99508771 | pass | n/a | n/a |
| half_2 | sparse-anonymous | p99 | ms | 14.383850 | 14.295900 | 0.99702520 | pass | 0.99707373 | pass | n/a | n/a |
| half_2 | sparse-anonymous | wall | ms | 1250.492650 | 1241.863850 | 1.00523427 | pass | 1.00679758 | pass | n/a | n/a |
| half_2 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| half_2 | sparse-named | p50 | ms | 2.001600 | 1.979900 | 1.02379871 | pass | 0.98643037 | pass | n/a | n/a |
| half_2 | sparse-named | p95 | ms | 5.569800 | 5.679500 | 1.00081313 | pass | 1.00676483 | pass | n/a | n/a |
| half_2 | sparse-named | p99 | ms | 15.223950 | 14.298800 | 1.02760621 | pass | 0.95420172 | pass | n/a | n/a |
| half_2 | sparse-named | wall | ms | 1328.270800 | 1307.706550 | 0.99838834 | pass | 0.98275775 | pass | n/a | n/a |
| half_2 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| half_2 | small-anonymous | p50 | ms | 3.957450 | 2.181500 | 0.99538522 | pass | 0.54898381 | pass | n/a | n/a |
| half_2 | small-anonymous | p95 | ms | 14.111050 | 9.934200 | 1.00668515 | pass | 0.68513926 | pass | n/a | n/a |
| half_2 | small-anonymous | p99 | ms | 17.535750 | 16.431800 | 0.98230586 | pass | 0.94513401 | pass | 0.95 | pass |
| half_2 | small-anonymous | wall | ms | 2497.304650 | 1823.525100 | 0.99538877 | pass | 0.73022856 | pass | 0.9 | pass |
| half_2 | small-anonymous | disk | bytes | 5809140.500000 | 4962924.500000 | 0.99906050 | n/a | 0.90124872 | pass | n/a | n/a |
| half_2 | small-named | p50 | ms | 4.162950 | 2.325500 | 0.98330994 | pass | 0.54316604 | pass | n/a | n/a |
| half_2 | small-named | p95 | ms | 14.542950 | 9.688900 | 0.99792720 | pass | 0.65781303 | pass | n/a | n/a |
| half_2 | small-named | p99 | ms | 18.264200 | 17.594700 | 1.01330629 | pass | 0.89578398 | pass | 0.95 | pass |
| half_2 | small-named | wall | ms | 2570.137100 | 1860.145350 | 0.98767898 | pass | 0.70785165 | pass | 0.9 | pass |
| half_2 | small-named | disk | bytes | 5888970.500000 | 5784575.000000 | 1.04381995 | n/a | 0.98308859 | pass | n/a | n/a |
| half_2 | pressure-anonymous | p50 | ms | 2.334950 | 2.390450 | 1.00196360 | pass | 1.02971866 | pass | n/a | n/a |
| half_2 | pressure-anonymous | p95 | ms | 10.249200 | 11.421500 | 1.08749415 | FAIL | 1.00455415 | pass | n/a | n/a |
| half_2 | pressure-anonymous | p99 | ms | 15.977100 | 16.676950 | 1.03033257 | pass | 1.07611403 | FAIL | n/a | n/a |
| half_2 | pressure-anonymous | wall | ms | 425.295100 | 438.435850 | 1.04825923 | pass | 1.03854329 | pass | n/a | n/a |
| half_2 | pressure-anonymous | disk | bytes | 11487156.000000 | 11456484.500000 | 0.99780462 | n/a | 0.99809249 | pass | n/a | n/a |
| half_2 | pressure-named | p50 | ms | 2.947150 | 2.987150 | 0.98948871 | pass | 0.99869115 | pass | n/a | n/a |
| half_2 | pressure-named | p95 | ms | 12.589500 | 8.585600 | 0.98906678 | pass | 0.70228892 | pass | n/a | n/a |
| half_2 | pressure-named | p99 | ms | 18.167300 | 16.716550 | 1.02701755 | pass | 0.95657381 | pass | n/a | n/a |
| half_2 | pressure-named | wall | ms | 536.730950 | 518.093950 | 0.99715250 | pass | 0.97362855 | pass | n/a | n/a |
| half_2 | pressure-named | disk | bytes | 12180646.500000 | 12173815.000000 | 0.99732703 | n/a | 0.99953366 | pass | n/a | n/a |
| half_2 | queries-ordered | all_aggregates/median_us | us | 4.800000 | 4.700000 | 0.99063830 | pass | 0.99063830 | pass | n/a | n/a |
| half_2 | queries-ordered | all_aggregates/p95_us | us | 6.550000 | 5.200000 | 0.81483254 | FAIL | 0.80574163 | pass | n/a | n/a |
| half_2 | queries-ordered | broad_window/median_us | us | 4.950000 | 5.000000 | 0.99000000 | pass | 1.01020408 | pass | n/a | n/a |
| half_2 | queries-ordered | broad_window/p95_us | us | 5.300000 | 5.200000 | 0.96363636 | pass | 0.98253119 | pass | n/a | n/a |
| half_2 | queries-ordered | narrow_window/median_us | us | 4.050000 | 4.100000 | 0.98780488 | pass | 1.01250000 | pass | n/a | n/a |
| half_2 | queries-ordered | narrow_window/p95_us | us | 6.000000 | 4.250000 | 0.76759287 | FAIL | 0.76759287 | pass | n/a | n/a |
| half_2 | queries-ordered | unordered_filter/median_us | us | 2875.200000 | 2081.250000 | 0.99580653 | pass | 0.73244498 | pass | 0.9 | pass |
| half_2 | queries-ordered | unordered_filter/p95_us | us | 3708.850000 | 2511.500000 | 1.08982609 | FAIL | 0.67236845 | pass | 0.9 | pass |
| half_2 | queries-ordered | grouped/median_us | us | 6263.550000 | 4937.400000 | 1.00378977 | pass | 0.77358401 | pass | 0.9 | pass |
| half_2 | queries-ordered | grouped/p95_us | us | 7688.650000 | 6231.950000 | 1.01276022 | pass | 0.79367334 | pass | 0.9 | pass |
| half_2 | queries-ordered | min_max/median_us | us | 7.350000 | 7.550000 | 1.01369863 | pass | 1.01351351 | pass | n/a | n/a |
| half_2 | queries-ordered | min_max/p95_us | us | 8.000000 | 8.000000 | 1.00008325 | pass | 0.98717949 | pass | n/a | n/a |
| half_2 | queries-late | all_aggregates/median_us | us | 4.700000 | 4.750000 | 1.00000000 | pass | 1.02173913 | pass | n/a | n/a |
| half_2 | queries-late | all_aggregates/p95_us | us | 5.350000 | 5.300000 | 1.02040816 | pass | 1.00925926 | pass | n/a | n/a |
| half_2 | queries-late | broad_window/median_us | us | 4.900000 | 5.000000 | 1.02020408 | pass | 1.00000000 | pass | n/a | n/a |
| half_2 | queries-late | broad_window/p95_us | us | 5.100000 | 5.200000 | 1.00980392 | pass | 1.01000000 | pass | n/a | n/a |
| half_2 | queries-late | narrow_window/median_us | us | 4.100000 | 4.100000 | 1.00029036 | pass | 0.97646733 | pass | n/a | n/a |
| half_2 | queries-late | narrow_window/p95_us | us | 4.300000 | 4.350000 | 0.98837209 | pass | 1.03600465 | pass | n/a | n/a |
| half_2 | queries-late | unordered_filter/median_us | us | 2812.450000 | 2131.250000 | 1.01994602 | pass | 0.74323607 | pass | 0.9 | pass |
| half_2 | queries-late | unordered_filter/p95_us | us | 3283.550000 | 2647.600000 | 1.10727734 | FAIL | 0.77611751 | pass | 0.9 | pass |
| half_2 | queries-late | grouped/median_us | us | 6216.750000 | 4874.950000 | 0.99531028 | pass | 0.77428534 | pass | 0.9 | pass |
| half_2 | queries-late | grouped/p95_us | us | 7273.500000 | 6334.900000 | 1.06094704 | FAIL | 0.83500269 | pass | 0.9 | pass |
| half_2 | queries-late | min_max/median_us | us | 6.950000 | 7.050000 | 1.01470588 | pass | 1.02930520 | pass | n/a | n/a |
| half_2 | queries-late | min_max/p95_us | us | 7.350000 | 7.350000 | 0.98639393 | pass | 1.00000000 | pass | n/a | n/a |
| half_2 | identified-replay | p50 | us | 1.450000 | 1.000000 | 1.00000000 | pass | 0.74175824 | pass | n/a | n/a |
| half_2 | identified-replay | p95 | us | 1.850000 | 1.500000 | 1.00000000 | pass | 0.80065359 | pass | 0.9 | pass |
| half_2 | identified-replay | p99 | us | 2.250000 | 1.850000 | 1.02173913 | pass | 0.81385281 | pass | 0.9 | pass |

## Exact preservation

32,331 files, 3,603 directories,
51 bounded ZIP parts and 3,921,562,494
logical bytes pass every member CRC/order/offset/size, exact original/restored
file hashes and complete file/directory sets before and after the full pure
audit. Every fresh prerequisite, all raw correctness/quantiles/profile and
full/half controls/guards/42 goals/252 unstarted service specifications replay
exactly without Native, timers or existing-file writes. Original files remain;
only inventoried regenerable target/Python caches are excluded. Closed raw
logs are byte-exact gzip supplements. One declaration-only KeyError occurred
before engine copy; its original helper and key-only repair are retained,
as is an unexecuted helper-path draft correction. No engine-test retry occurred.

No new supported upgrade, reliable release ETA, fresh competitor ranking,
universal win, Native CPU/RSS or physical power-loss guarantee is claimed.
Recent raw GitHub backup remains unverified; no recent raw deletion is eligible.
See [reproduction](benchmarks/adaptive-speed-116/REPRODUCE.md) and the
[complete audit](benchmarks/adaptive-speed-116/complete-audit-proof.json).
