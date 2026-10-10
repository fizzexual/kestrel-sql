# Adaptive publication trial 114

**Release qualification failed.** Supported main remains 0.3.16; isolated
0.3.17 is unreleased. All 324 native cases are correct, but 12 of 153 A/A
controls, five of 171 regression guards and nine of 42 goals fail. Every
252 service case is UNSTARTED/UNTESTED. No selected scope, extra round,
numerical retry or gate change occurred. Every raw stall and failure remains.

The measured publication stages in diagnostic 113 justified testing concurrent
durable flushes. Trial 114 retains exact 112 collector/filter/replay/scan and
the identical common native driver. Only the private publication feature,
archive dispatch, scoped flush helper and two integration tests change.
Both BufWriters flush before the pair; both existing sync_all successes and
the actual worker join precede catalog rename, read-view update and ACK.
Spawn errors, either flush error or either panic prevent success. At most
one borrowed worker exists per pair; no detached worker, unsafe code,
durability weakening, persistent thread or file-format change is introduced.
Archive/Cargo exact inverses and every other source hash independently pass.

796 fresh test executions across eight configurations, five strict lints,
all normal/fault binaries and 359 fresh recovery commands pass. Faults,
corruptions, CAT2/CAT3, byte fixtures, concurrent ACKs, original receipt
generations and cold SQLite answers pass. Four Native/two service excluded
smokes, 48 order checks, two invalid order fixtures and **six** invalid
conserved-outcome cases pass. Earlier prose saying 29 negative cases was
incorrect; the original raw dictionaries contained six. Historical reports
and all failed/unexecuted drafts remain preserved. Actual build argv confirms
benchmark-shutdown plus adaptive-engine for the candidate, and fault-injection
for the fault build; the policy's inherited features field is contextual.

The build, recovery, smoke and Native controllers and independent audits
actually exited zero. This does not reclassify the old 112 preflight API
return that was unobserved. Independent raw auditing passes all 479,232
acknowledgements and 2,921,356,800 CRC bytes, full row multisets, indexes,
named receipt digests/original generations, current metadata, cold SQL,
quantiles, direct Archive byte equivalence and balanced full/half orders.

## Controlled goals and remaining failures

Nine goal metrics pass targets and A/A in full and both halves. Displayed
medians use the indicated units; percentages use full within-round paired
ratios, which need not equal quotients of displayed medians. These compare
the complete experimental candidate with supported 0.3.16 and **do not
isolate a 114-versus-112 flush gain**. Earlier optimizations are included.

| Workload | Metric | Unit | Baseline median | Candidate median | Paired reduction |
| --- | --- | --- | ---: | ---: | ---: |
| queries-late | unordered_filter/median_us | us | 2713.250000 | 2004.100000 | 25.91% |
| queries-late | unordered_filter/p95_us | us | 3099.600000 | 2317.650000 | 24.42% |
| queries-ordered | grouped/median_us | us | 6015.150000 | 5273.300000 | 11.82% |
| queries-ordered | unordered_filter/median_us | us | 2684.950000 | 2021.400000 | 25.28% |
| queries-ordered | unordered_filter/p95_us | us | 3012.450000 | 2369.150000 | 21.21% |
| small-anonymous | p99 | ms | 16.483250 | 15.107800 | 5.76% |
| small-anonymous | wall | ms | 2348.347700 | 1689.572900 | 27.98% |
| small-named | p99 | ms | 16.823150 | 15.202150 | 11.37% |
| small-named | wall | ms | 2412.042750 | 1628.044100 | 32.79% |

Three failed guards have passing A/A in half 2: pressure-anonymous p95 is
10.96% slower and p99 11.53% slower; pressure-named p99 is 8.61% slower.
The other two guard failures have failing A/A. Ordered/late grouped p95
still miss the 10% target with passing full controls; late grouped median
and original-ID replay goals also miss required halves. Unstable replay
baseline controls prevent an all-scope replay-speed claim. Causes and any
benefit of selectively choosing a publication strategy are not established.

## Every before/after and mandatory gate

Latency/completion units are milliseconds; queries use microseconds; disk
uses bytes. A/A requires 0.95–1.05. Candidate guards require at most 1.05.
Every goal's own frozen limit is shown. All full and both-half results follow.

| Scope | Workload | Metric | Unit | Baseline median | Candidate median | A/A | Control | C/A | Guard | Goal limit/result |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- |
| full | sparse-anonymous | p50 | ms | 1.834800 | 1.812050 | 1.00624256 | pass | 0.98380741 | pass | n/a |
| full | sparse-anonymous | p95 | ms | 5.324850 | 5.160400 | 1.00784337 | pass | 1.00531677 | pass | n/a |
| full | sparse-anonymous | p99 | ms | 13.567750 | 13.410450 | 0.98196997 | pass | 0.98871387 | pass | n/a |
| full | sparse-anonymous | wall | ms | 1208.434900 | 1187.208650 | 1.00668066 | pass | 0.99387637 | pass | n/a |
| full | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a |
| full | sparse-named | p50 | ms | 1.851700 | 1.815500 | 1.00947768 | pass | 0.97469244 | pass | n/a |
| full | sparse-named | p95 | ms | 5.254200 | 4.940950 | 0.99281482 | pass | 0.94673450 | pass | n/a |
| full | sparse-named | p99 | ms | 13.411700 | 13.053450 | 0.98801295 | pass | 0.98193552 | pass | n/a |
| full | sparse-named | wall | ms | 1206.619500 | 1174.085600 | 1.00629646 | pass | 0.97727457 | pass | n/a |
| full | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a |
| full | small-anonymous | p50 | ms | 3.751750 | 2.073250 | 0.99268766 | pass | 0.55608245 | pass | n/a |
| full | small-anonymous | p95 | ms | 13.230000 | 8.719800 | 0.98927309 | pass | 0.65556901 | pass | n/a |
| full | small-anonymous | p99 | ms | 16.483250 | 15.107800 | 0.98002451 | pass | 0.94243615 | pass | 0.95 / pass |
| full | small-anonymous | wall | ms | 2348.347700 | 1689.572900 | 0.98934998 | pass | 0.72015382 | pass | 0.9 / pass |
| full | small-anonymous | disk | bytes | 5815124.500000 | 5222222.500000 | 0.99834694 | n/a | 0.95750698 | pass | n/a |
| full | small-named | p50 | ms | 3.912250 | 2.066850 | 1.00991433 | pass | 0.53463942 | pass | n/a |
| full | small-named | p95 | ms | 13.485100 | 8.547900 | 1.01552294 | pass | 0.63887033 | pass | n/a |
| full | small-named | p99 | ms | 16.823150 | 15.202150 | 1.00885443 | pass | 0.88631041 | pass | 0.95 / pass |
| full | small-named | wall | ms | 2412.042750 | 1628.044100 | 1.01740187 | pass | 0.67209805 | pass | 0.9 / pass |
| full | small-named | disk | bytes | 6546490.000000 | 5958309.000000 | 0.99822794 | n/a | 0.94753984 | pass | n/a |
| full | pressure-anonymous | p50 | ms | 2.297750 | 2.265050 | 1.00374416 | pass | 0.97801139 | pass | n/a |
| full | pressure-anonymous | p95 | ms | 7.558350 | 8.775500 | 1.18574287 | FAIL | 1.05492852 | FAIL | n/a |
| full | pressure-anonymous | p99 | ms | 13.816100 | 14.028000 | 1.02886234 | pass | 1.04576794 | pass | n/a |
| full | pressure-anonymous | wall | ms | 417.285450 | 412.521100 | 1.02627276 | pass | 0.98436336 | pass | n/a |
| full | pressure-anonymous | disk | bytes | 11486668.000000 | 11475403.500000 | 1.00017125 | n/a | 0.99920709 | pass | n/a |
| full | pressure-named | p50 | ms | 2.647700 | 2.582700 | 1.00395197 | pass | 0.98171136 | pass | n/a |
| full | pressure-named | p95 | ms | 9.572000 | 9.698500 | 1.07319042 | FAIL | 0.92256044 | pass | n/a |
| full | pressure-named | p99 | ms | 15.496350 | 15.986500 | 1.04315537 | pass | 1.00040141 | pass | n/a |
| full | pressure-named | wall | ms | 494.414900 | 477.942000 | 1.00940551 | pass | 0.97731172 | pass | n/a |
| full | pressure-named | disk | bytes | 12181091.000000 | 12160639.000000 | 1.00112786 | n/a | 0.99954535 | pass | n/a |
| full | queries-ordered | all_aggregates/median_us | us | 4.800000 | 4.800000 | 1.00000000 | pass | 0.98979592 | pass | n/a |
| full | queries-ordered | all_aggregates/p95_us | us | 5.300000 | 5.400000 | 1.00000000 | pass | 1.01886792 | pass | n/a |
| full | queries-ordered | broad_window/median_us | us | 5.000000 | 5.000000 | 1.00000000 | pass | 1.00000000 | pass | n/a |
| full | queries-ordered | broad_window/p95_us | us | 5.200000 | 5.200000 | 1.00000000 | pass | 1.00000000 | pass | n/a |
| full | queries-ordered | narrow_window/median_us | us | 4.100000 | 4.100000 | 1.00000000 | pass | 1.00000000 | pass | n/a |
| full | queries-ordered | narrow_window/p95_us | us | 4.300000 | 4.300000 | 1.00000000 | pass | 0.98863636 | pass | n/a |
| full | queries-ordered | unordered_filter/median_us | us | 2684.950000 | 2021.400000 | 0.99357349 | pass | 0.74720408 | pass | 0.9 / pass |
| full | queries-ordered | unordered_filter/p95_us | us | 3012.450000 | 2369.150000 | 0.99436576 | pass | 0.78785613 | pass | 0.9 / pass |
| full | queries-ordered | grouped/median_us | us | 6015.150000 | 5273.300000 | 0.98388112 | pass | 0.88183584 | pass | 0.9 / pass |
| full | queries-ordered | grouped/p95_us | us | 6719.250000 | 6026.450000 | 1.00856490 | pass | 0.93195435 | pass | 0.9 / FAIL |
| full | queries-ordered | min_max/median_us | us | 7.500000 | 7.300000 | 1.00000000 | pass | 0.98648649 | pass | n/a |
| full | queries-ordered | min_max/p95_us | us | 7.750000 | 7.600000 | 1.00000000 | pass | 0.98701080 | pass | n/a |
| full | queries-late | all_aggregates/median_us | us | 4.700000 | 4.600000 | 1.00000000 | pass | 0.98979592 | pass | n/a |
| full | queries-late | all_aggregates/p95_us | us | 5.400000 | 5.500000 | 1.00000000 | pass | 1.01851852 | pass | n/a |
| full | queries-late | broad_window/median_us | us | 5.000000 | 5.100000 | 0.97076923 | pass | 1.00000000 | pass | n/a |
| full | queries-late | broad_window/p95_us | us | 5.200000 | 5.250000 | 0.96261356 | pass | 1.00000000 | pass | n/a |
| full | queries-late | narrow_window/median_us | us | 4.200000 | 4.150000 | 0.97646733 | pass | 0.98837209 | pass | n/a |
| full | queries-late | narrow_window/p95_us | us | 4.300000 | 4.350000 | 0.98837209 | pass | 1.00000000 | pass | n/a |
| full | queries-late | unordered_filter/median_us | us | 2713.250000 | 2004.100000 | 0.98877144 | pass | 0.74093688 | pass | 0.9 / pass |
| full | queries-late | unordered_filter/p95_us | us | 3099.600000 | 2317.650000 | 0.97927069 | pass | 0.75575905 | pass | 0.9 / pass |
| full | queries-late | grouped/median_us | us | 5976.000000 | 5371.650000 | 1.00153281 | pass | 0.89598108 | pass | 0.9 / pass |
| full | queries-late | grouped/p95_us | us | 6721.650000 | 6812.850000 | 1.01118123 | pass | 0.96507571 | pass | 0.9 / FAIL |
| full | queries-late | min_max/median_us | us | 7.000000 | 7.000000 | 1.00000000 | pass | 0.99295775 | pass | n/a |
| full | queries-late | min_max/p95_us | us | 7.400000 | 7.200000 | 0.99324324 | pass | 0.97297297 | pass | n/a |
| full | identified-replay | p50 | ms | 0.000000 | 0.000000 | 0.96153846 | pass | 0.76923077 | pass | n/a |
| full | identified-replay | p95 | ms | 0.000000 | 0.000000 | 0.91666667 | FAIL | 0.79513889 | pass | 0.9 / pass |
| full | identified-replay | p99 | ms | 0.000000 | 0.000000 | 0.90476190 | FAIL | 0.78571429 | pass | 0.9 / pass |
| half_1 | sparse-anonymous | p50 | ms | 1.829750 | 1.808350 | 1.02486743 | pass | 0.98380741 | pass | n/a |
| half_1 | sparse-anonymous | p95 | ms | 5.080750 | 5.131700 | 1.04101651 | pass | 1.01143737 | pass | n/a |
| half_1 | sparse-anonymous | p99 | ms | 13.407200 | 13.388050 | 0.99259277 | pass | 0.99225209 | pass | n/a |
| half_1 | sparse-anonymous | wall | ms | 1186.849550 | 1183.944700 | 1.02419775 | pass | 0.99387637 | pass | n/a |
| half_1 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a |
| half_1 | sparse-named | p50 | ms | 1.852850 | 1.809350 | 0.99348772 | pass | 0.96915597 | pass | n/a |
| half_1 | sparse-named | p95 | ms | 5.080850 | 5.087100 | 0.98492584 | pass | 0.98207017 | pass | n/a |
| half_1 | sparse-named | p99 | ms | 13.411700 | 12.967100 | 0.97973408 | pass | 0.98133154 | pass | n/a |
| half_1 | sparse-named | wall | ms | 1195.187200 | 1167.940550 | 0.98606752 | pass | 0.97727457 | pass | n/a |
| half_1 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a |
| half_1 | small-anonymous | p50 | ms | 3.751750 | 2.107750 | 0.99342255 | pass | 0.56147195 | pass | n/a |
| half_1 | small-anonymous | p95 | ms | 13.191850 | 8.724000 | 0.98837776 | pass | 0.65556901 | pass | n/a |
| half_1 | small-anonymous | p99 | ms | 16.121900 | 15.190100 | 0.99643664 | pass | 0.94243615 | pass | 0.95 / pass |
| half_1 | small-anonymous | wall | ms | 2330.376800 | 1704.632550 | 1.01226127 | pass | 0.72655975 | pass | 0.9 / pass |
| half_1 | small-anonymous | disk | bytes | 5809522.500000 | 5566801.500000 | 0.99845371 | n/a | 0.97435405 | pass | n/a |
| half_1 | small-named | p50 | ms | 3.922550 | 2.060500 | 1.00038772 | pass | 0.52584325 | pass | n/a |
| half_1 | small-named | p95 | ms | 13.485100 | 8.608450 | 1.00361665 | pass | 0.63930694 | pass | n/a |
| half_1 | small-named | p99 | ms | 16.575550 | 15.167550 | 0.96913061 | pass | 0.90428519 | pass | 0.95 / pass |
| half_1 | small-named | wall | ms | 2427.556800 | 1614.317700 | 0.99050641 | pass | 0.67295858 | pass | 0.9 / pass |
| half_1 | small-named | disk | bytes | 6547735.000000 | 5768461.500000 | 0.99927801 | n/a | 0.94827966 | pass | n/a |
| half_1 | pressure-anonymous | p50 | ms | 2.297750 | 2.258600 | 1.01325847 | pass | 0.98979938 | pass | n/a |
| half_1 | pressure-anonymous | p95 | ms | 7.164150 | 8.775500 | 1.47872066 | FAIL | 1.03069938 | pass | n/a |
| half_1 | pressure-anonymous | p99 | ms | 13.816100 | 13.723600 | 1.00935251 | pass | 1.01285276 | pass | n/a |
| half_1 | pressure-anonymous | wall | ms | 415.460400 | 410.877050 | 1.02906244 | pass | 0.99301980 | pass | n/a |
| half_1 | pressure-anonymous | disk | bytes | 11486668.000000 | 11477501.000000 | 0.99999305 | n/a | 0.99928024 | pass | n/a |
| half_1 | pressure-named | p50 | ms | 2.633800 | 2.582700 | 0.99805453 | pass | 0.98125120 | pass | n/a |
| half_1 | pressure-named | p95 | ms | 11.775450 | 8.615200 | 0.98346828 | pass | 0.73494668 | pass | n/a |
| half_1 | pressure-named | p99 | ms | 15.335300 | 14.546250 | 1.20411251 | FAIL | 0.98449125 | pass | n/a |
| half_1 | pressure-named | wall | ms | 503.685300 | 468.996700 | 0.99433141 | pass | 0.93130572 | pass | n/a |
| half_1 | pressure-named | disk | bytes | 12191175.000000 | 12158731.000000 | 1.00018237 | n/a | 0.94008664 | pass | n/a |
| half_1 | queries-ordered | all_aggregates/median_us | us | 4.800000 | 4.700000 | 1.00000000 | pass | 1.00000000 | pass | n/a |
| half_1 | queries-ordered | all_aggregates/p95_us | us | 5.300000 | 5.400000 | 0.99056604 | pass | 1.01886792 | pass | n/a |
| half_1 | queries-ordered | broad_window/median_us | us | 5.000000 | 5.000000 | 1.00000000 | pass | 1.00000000 | pass | n/a |
| half_1 | queries-ordered | broad_window/p95_us | us | 5.200000 | 5.300000 | 0.99056604 | pass | 1.00961538 | pass | n/a |
| half_1 | queries-ordered | narrow_window/median_us | us | 4.150000 | 4.100000 | 1.00000000 | pass | 1.00000000 | pass | n/a |
| half_1 | queries-ordered | narrow_window/p95_us | us | 4.300000 | 4.250000 | 1.00000000 | pass | 0.97674419 | pass | n/a |
| half_1 | queries-ordered | unordered_filter/median_us | us | 2684.950000 | 2030.950000 | 0.99212284 | pass | 0.75170358 | pass | 0.9 / pass |
| half_1 | queries-ordered | unordered_filter/p95_us | us | 3012.450000 | 2364.750000 | 1.00734879 | pass | 0.78785613 | pass | 0.9 / pass |
| half_1 | queries-ordered | grouped/median_us | us | 6044.100000 | 5272.750000 | 0.98209532 | pass | 0.87889213 | pass | 0.9 / pass |
| half_1 | queries-ordered | grouped/p95_us | us | 6655.800000 | 5889.100000 | 1.08295218 | FAIL | 0.90829692 | pass | 0.9 / FAIL |
| half_1 | queries-ordered | min_max/median_us | us | 7.500000 | 7.350000 | 1.00000000 | pass | 0.98657658 | pass | n/a |
| half_1 | queries-ordered | min_max/p95_us | us | 7.700000 | 7.650000 | 1.00000000 | pass | 0.99358974 | pass | n/a |
| half_1 | queries-late | all_aggregates/median_us | us | 4.650000 | 4.550000 | 1.01153505 | pass | 0.98913043 | pass | n/a |
| half_1 | queries-late | all_aggregates/p95_us | us | 5.400000 | 5.650000 | 1.00000000 | pass | 1.00000000 | pass | n/a |
| half_1 | queries-late | broad_window/median_us | us | 5.050000 | 5.100000 | 0.97076923 | pass | 1.00000000 | pass | n/a |
| half_1 | queries-late | broad_window/p95_us | us | 5.250000 | 5.250000 | 0.96261356 | pass | 0.99038462 | pass | n/a |
| half_1 | queries-late | narrow_window/median_us | us | 4.200000 | 4.150000 | 0.97617697 | pass | 0.98837209 | pass | n/a |
| half_1 | queries-late | narrow_window/p95_us | us | 4.350000 | 4.300000 | 1.01162791 | pass | 0.98888889 | pass | n/a |
| half_1 | queries-late | unordered_filter/median_us | us | 2688.250000 | 2024.150000 | 1.00016402 | pass | 0.74996662 | pass | 0.9 / pass |
| half_1 | queries-late | unordered_filter/p95_us | us | 2890.200000 | 2317.650000 | 1.02334917 | pass | 0.77311769 | pass | 0.9 / pass |
| half_1 | queries-late | grouped/median_us | us | 5974.100000 | 5347.300000 | 1.00153281 | pass | 0.89516613 | pass | 0.9 / pass |
| half_1 | queries-late | grouped/p95_us | us | 6729.050000 | 6362.200000 | 0.96354872 | pass | 0.94319206 | pass | 0.9 / FAIL |
| half_1 | queries-late | min_max/median_us | us | 7.000000 | 7.000000 | 0.99295775 | pass | 1.00000000 | pass | n/a |
| half_1 | queries-late | min_max/p95_us | us | 7.300000 | 7.250000 | 0.99305556 | pass | 0.98648649 | pass | n/a |
| half_1 | identified-replay | p50 | ms | 0.000000 | 0.000000 | 1.04166667 | pass | 0.80128205 | pass | n/a |
| half_1 | identified-replay | p95 | ms | 0.000000 | 0.000000 | 1.00000000 | pass | 0.90625000 | pass | 0.9 / FAIL |
| half_1 | identified-replay | p99 | ms | 0.000000 | 0.000000 | 0.97368421 | pass | 0.97368421 | pass | 0.9 / FAIL |
| half_2 | sparse-anonymous | p50 | ms | 1.844400 | 1.833950 | 1.00494295 | pass | 0.97880844 | pass | n/a |
| half_2 | sparse-anonymous | p95 | ms | 5.366800 | 5.160400 | 0.98779379 | pass | 0.97201630 | pass | n/a |
| half_2 | sparse-anonymous | p99 | ms | 13.758350 | 13.550350 | 0.95985927 | pass | 0.96637580 | pass | n/a |
| half_2 | sparse-anonymous | wall | ms | 1228.505900 | 1189.198950 | 0.97717803 | pass | 0.98089791 | pass | n/a |
| half_2 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a |
| half_2 | sparse-named | p50 | ms | 1.851700 | 1.815500 | 1.01419074 | pass | 0.97469244 | pass | n/a |
| half_2 | sparse-named | p95 | ms | 5.425300 | 4.939200 | 1.00197294 | pass | 0.91039336 | pass | n/a |
| half_2 | sparse-named | p99 | ms | 13.451450 | 13.136500 | 0.98801295 | pass | 0.98193552 | pass | n/a |
| half_2 | sparse-named | wall | ms | 1212.373100 | 1177.675950 | 1.02528417 | pass | 0.97672554 | pass | n/a |
| half_2 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a |
| half_2 | small-anonymous | p50 | ms | 3.766350 | 2.039300 | 0.98279694 | pass | 0.55103196 | pass | n/a |
| half_2 | small-anonymous | p95 | ms | 13.235350 | 8.595850 | 0.98927309 | pass | 0.64549080 | pass | n/a |
| half_2 | small-anonymous | p99 | ms | 17.688550 | 15.084200 | 0.98002451 | pass | 0.92473562 | pass | 0.95 / pass |
| half_2 | small-anonymous | wall | ms | 2377.410500 | 1686.252450 | 0.97439112 | pass | 0.71016136 | pass | 0.9 / pass |
| half_2 | small-anonymous | disk | bytes | 5819920.000000 | 4968122.500000 | 0.99834694 | n/a | 0.86547448 | pass | n/a |
| half_2 | small-named | p50 | ms | 3.898650 | 2.141050 | 1.02729353 | pass | 0.54534358 | pass | n/a |
| half_2 | small-named | p95 | ms | 13.559750 | 8.461300 | 1.03693479 | pass | 0.63460592 | pass | n/a |
| half_2 | small-named | p99 | ms | 17.607650 | 15.539700 | 1.02939942 | pass | 0.82557144 | pass | 0.95 / pass |
| half_2 | small-named | wall | ms | 2404.077600 | 1670.810300 | 1.02665991 | pass | 0.67025526 | pass | 0.9 / pass |
| half_2 | small-named | disk | bytes | 6545468.000000 | 5962435.000000 | 0.94469036 | n/a | 0.90940395 | pass | n/a |
| half_2 | pressure-anonymous | p50 | ms | 2.309850 | 2.279150 | 0.99175196 | pass | 0.96532717 | pass | n/a |
| half_2 | pressure-anonymous | p95 | ms | 9.202950 | 9.652350 | 0.98596725 | pass | 1.10956788 | FAIL | n/a |
| half_2 | pressure-anonymous | p99 | ms | 14.016750 | 15.514400 | 1.03439697 | pass | 1.11525393 | FAIL | n/a |
| half_2 | pressure-anonymous | wall | ms | 422.873950 | 416.963150 | 1.02463243 | pass | 0.97282400 | pass | n/a |
| half_2 | pressure-anonymous | disk | bytes | 11485164.500000 | 11463262.000000 | 1.00075298 | n/a | 0.99920709 | pass | n/a |
| half_2 | pressure-named | p50 | ms | 2.657400 | 2.623800 | 1.00922184 | pass | 0.99337955 | pass | n/a |
| half_2 | pressure-named | p95 | ms | 7.401400 | 10.577750 | 1.53144335 | FAIL | 1.34411106 | FAIL | n/a |
| half_2 | pressure-named | p99 | ms | 18.780450 | 17.531000 | 0.98685343 | pass | 1.08606643 | FAIL | n/a |
| half_2 | pressure-named | wall | ms | 488.744300 | 490.621600 | 1.07232819 | FAIL | 1.01319509 | pass | n/a |
| half_2 | pressure-named | disk | bytes | 12162226.000000 | 12162049.500000 | 1.06505167 | n/a | 1.00074015 | pass | n/a |
| half_2 | queries-ordered | all_aggregates/median_us | us | 4.850000 | 4.850000 | 1.00000000 | pass | 0.98979592 | pass | n/a |
| half_2 | queries-ordered | all_aggregates/p95_us | us | 5.350000 | 5.450000 | 1.00000000 | pass | 1.03846154 | pass | n/a |
| half_2 | queries-ordered | broad_window/median_us | us | 5.000000 | 5.000000 | 0.99019608 | pass | 1.00000000 | pass | n/a |
| half_2 | queries-ordered | broad_window/p95_us | us | 5.200000 | 5.200000 | 1.00943396 | pass | 0.99056604 | pass | n/a |
| half_2 | queries-ordered | narrow_window/median_us | us | 4.100000 | 4.100000 | 0.98780488 | pass | 0.98809524 | pass | n/a |
| half_2 | queries-ordered | narrow_window/p95_us | us | 4.300000 | 4.300000 | 1.00000000 | pass | 1.00000000 | pass | n/a |
| half_2 | queries-ordered | unordered_filter/median_us | us | 2688.850000 | 1992.600000 | 0.99533881 | pass | 0.73913485 | pass | 0.9 / pass |
| half_2 | queries-ordered | unordered_filter/p95_us | us | 2997.450000 | 2400.700000 | 0.96782911 | pass | 0.77579048 | pass | 0.9 / pass |
| half_2 | queries-ordered | grouped/median_us | us | 6015.150000 | 5287.200000 | 0.98388112 | pass | 0.88269160 | pass | 0.9 / pass |
| half_2 | queries-ordered | grouped/p95_us | us | 6738.150000 | 6489.350000 | 0.97043175 | pass | 0.94312073 | pass | 0.9 / FAIL |
| half_2 | queries-ordered | min_max/median_us | us | 7.450000 | 7.300000 | 0.98701299 | pass | 0.98648649 | pass | n/a |
| half_2 | queries-ordered | min_max/p95_us | us | 7.850000 | 7.600000 | 1.00008114 | pass | 0.98060054 | pass | n/a |
| half_2 | queries-late | all_aggregates/median_us | us | 4.800000 | 4.650000 | 1.00000000 | pass | 0.98979592 | pass | n/a |
| half_2 | queries-late | all_aggregates/p95_us | us | 5.400000 | 5.450000 | 1.01851852 | pass | 1.01869322 | pass | n/a |
| half_2 | queries-late | broad_window/median_us | us | 5.000000 | 5.100000 | 0.98039216 | pass | 1.00980392 | pass | n/a |
| half_2 | queries-late | broad_window/p95_us | us | 5.200000 | 5.250000 | 0.98113208 | pass | 1.00943396 | pass | n/a |
| half_2 | queries-late | narrow_window/median_us | us | 4.200000 | 4.200000 | 0.98809524 | pass | 1.00000000 | pass | n/a |
| half_2 | queries-late | narrow_window/p95_us | us | 4.300000 | 4.400000 | 0.97727273 | pass | 1.01162791 | pass | n/a |
| half_2 | queries-late | unordered_filter/median_us | us | 2751.200000 | 1995.800000 | 0.98058170 | pass | 0.72822297 | pass | 0.9 / pass |
| half_2 | queries-late | unordered_filter/p95_us | us | 3232.750000 | 2349.700000 | 0.96178103 | pass | 0.71285819 | pass | 0.9 / pass |
| half_2 | queries-late | grouped/median_us | us | 5976.000000 | 5462.900000 | 0.99776422 | pass | 0.90134582 | pass | 0.9 / FAIL |
| half_2 | queries-late | grouped/p95_us | us | 6544.700000 | 6945.300000 | 1.04161360 | pass | 1.03159102 | pass | 0.9 / FAIL |
| half_2 | queries-late | min_max/median_us | us | 7.050000 | 7.000000 | 1.00714286 | pass | 0.98581489 | pass | n/a |
| half_2 | queries-late | min_max/p95_us | us | 7.450000 | 7.200000 | 0.99324324 | pass | 0.96648649 | pass | n/a |
| half_2 | identified-replay | p50 | ms | 0.000000 | 0.000000 | 0.92307692 | FAIL | 0.76923077 | pass | n/a |
| half_2 | identified-replay | p95 | ms | 0.000000 | 0.000000 | 0.84444444 | FAIL | 0.72953216 | pass | 0.9 / pass |
| half_2 | identified-replay | p99 | ms | 0.000000 | 0.000000 | 0.82367150 | FAIL | 0.70956522 | pass | 0.9 / pass |

## Exact preservation and limits

33,190 files, 3,583 directories,
50 bounded ZIP parts and 3,929,037,296
logical bytes pass member CRC/order/offset/size and exact original/restored
file hashes and directory sets before and after complete pure replay. Every
source/build/recovery/smoke and native gate replays identically, with no
Native, timer or existing-file write. All originals remain. Only inventoried
regenerable build/Python caches are excluded. Closed logs are byte-exact
gzip supplements. No recent complete private remote backup or deletion is claimed.

Automatic approval review rejected an attempted handoff update while the
build was live. The command did not execute. After the actual build exit and
a fresh idle guard, a corrected checkpoint executed successfully. Its
unexecuted rejected draft and resolution record are retained. No approval
barrier was bypassed, and the reset and all old task settings remain untouched.

There is no supported upgrade, new competitor ranking, universal benchmark
win, reliable release ETA, native CPU/RSS, physical I/O or power-loss claim.
The next justified measurement must isolate 112 serial versus 114 concurrent
publication with new predeclared balanced controls, before choosing a workload
dependent publication path. Neither old failure is reclassified.
See [reproduction](benchmarks/adaptive-speed-114/REPRODUCE.md) and
[complete audit](benchmarks/adaptive-speed-114/complete-audit-proof.json).
