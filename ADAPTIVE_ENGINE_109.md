# Adaptive engine trial 109

The isolated candidate implements workload-dependent write collection and query
execution. It passes correctness and recovery, and several improvements hold
across the full cohort and both balanced halves. **Release qualification fails.**
Supported main remains 0.3.16; this candidate's 0.3.17 metadata is unreleased.

The writer uses the exact trial 107 collector: immediate sparse work, bounded
small-group lookahead, or draining ready pressure work. Lookahead is capped at
the minimum of the configured cap, half observed successful publication cost,
100 microseconds and 1,024 empty polls. It uses a fixed deadline and the existing
64-command limit. Ordinary queries choose the existing prefix path first,
then fused filtering/aggregation for eligible ungrouped single-column COUNT,
SUM and AVG, otherwise the existing general selection or grouping path.
The public adaptive-engine feature enables adaptive-collection and adaptive-filter.

The fused scan avoids selected-position storage and a second aggregate traversal.
Signed predicates, exact i128 totals, CRC-checked pages, immutable snapshots,
publication, source/WAL/ACK semantics, disk formats and maintenance stay protected.
Default/fixed paths remain available. Native CPU and peak memory were not measured;
the service resource and loss checks remain unstarted because Native qualification
failed. No new competitor or universal benchmark victory is claimed.

724 fresh test executions across eight full debug/release configurations, five
strict all-target lints and independent normal/fault artifact builds passed.
The fresh 359-command external cohort passed 28 publication interruptions,
10 corruptions, CAT2/CAT3 reads, two byte fixtures, 256 concurrent anonymous ACKs,
two named scenarios and 300 cold SQLite-model SQL checks. This does not establish
physical power-loss or resource-exhaustion guarantees.

All 324 predeclared Native cases completed once, with 479,232 acknowledged batches
and 2,921,356,800 full checksum bytes independently verified. All rows, receipts,
indexes, query answers, timing quantiles, raw samples, order and provenance were
replayed. Original gates and 12 small-write goals were retained; 12 required
filter goals were added before source, copies or builds. There were no selected
rounds, extra timers or relaxed gates.

## Measured gains with controls passing in the full run and both halves

The improvement percentages below use the median of within-round candidate/A
ratios. Displayed before/after values are separate medians and their quotient
can differ from that paired comparison.

| Workload and metric | Before | After | Paired improvement |
| --- | ---: | ---: | ---: |
| Small anonymous writes, completion | 2.498380 s | 1.766688 s | 26.32% |
| Small named writes, completion | 2.524958 s | 1.734931 s | 32.58% |
| Small anonymous writes, p99 | 18.597800 ms | 16.615500 ms | 7.03% |
| Ordered data, value-filter median | 2.814350 ms | 2.464050 ms | 11.87% |
| Late data, value-filter median | 2.819800 ms | 2.480050 ms | 12.15% |
| Late data, value-filter p95 | 3.249000 ms | 2.798200 ms | 14.47% |

These individual gains do not qualify the complete candidate. It fails 27 A/A
controls, eight regression guards and one of 24 improvement goals. The ordered
filter p95 half-1 target fails, with its baseline control also failing. Named
write p99 has a failed half-2 control. Calibrated regressions include full-run
receipt replay p95, paired ratio 1.09375, and late-data grouped-query half-2 p95,
ratio 1.08289641. Their exclusive causes are not established. Every failure and
all 252 service specifications remain preserved; those service cases are UNSTARTED
and their correctness/performance are untested.

The first auditor invocation omitted its workspace argument and exited 1 before
audit() ran. The corrected invocation used the exact same frozen auditor and
gates, exited 0 and retained the rejected performance result. Its failed log
remains. No benchmark was rerun for this correction.

## Every before/after, control, regression check and goal

All full-run and half-run metrics follow. Timing units are milliseconds for live
operations, microseconds for queries and receipt replay, and bytes for disk.
A/A passes only within 0.95..1.05. Candidate/A regression limits remain 1.05.
Improvement targets remain 0.95 for small-write p99 and 0.90 for small-write
completion and filter metrics. Raw samples and maxima remain in the archive.

| Scope | Workload | Metric | Unit | Before median | After median | A/A | Control | Candidate/A | Regression | Goal |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- |
| full | sparse-anonymous | p50 | ms | 1.914200 | 1.903500 | 1.01435137 | pass | 0.98999942 | pass | - |
| full | sparse-anonymous | p95 | ms | 5.349600 | 5.341500 | 0.99808007 | pass | 0.95174987 | pass | - |
| full | sparse-anonymous | p99 | ms | 14.628400 | 14.158100 | 0.99535550 | pass | 0.97488669 | pass | - |
| full | sparse-anonymous | wall | ms | 1267.391450 | 1274.563850 | 1.00052414 | pass | 0.97884157 | pass | - |
| full | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| full | sparse-named | p50 | ms | 1.919650 | 1.926300 | 0.99490207 | pass | 1.00403000 | pass | - |
| full | sparse-named | p95 | ms | 5.746150 | 5.418850 | 1.01716509 | pass | 0.97066098 | pass | - |
| full | sparse-named | p99 | ms | 14.208600 | 13.854300 | 1.00836018 | pass | 0.96871986 | pass | - |
| full | sparse-named | wall | ms | 1281.679750 | 1259.077500 | 1.00816807 | pass | 0.98928535 | pass | - |
| full | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| full | small-anonymous | p50 | ms | 3.818350 | 2.154650 | 0.99702389 | pass | 0.55368136 | pass | - |
| full | small-anonymous | p95 | ms | 13.868400 | 9.186400 | 0.97989082 | pass | 0.64875705 | pass | - |
| full | small-anonymous | p99 | ms | 18.597800 | 16.615500 | 0.99940215 | pass | 0.92970506 | pass | pass <= 0.95 |
| full | small-anonymous | wall | ms | 2498.380300 | 1766.688400 | 1.00293843 | pass | 0.73680287 | pass | pass <= 0.90 |
| full | small-anonymous | disk | bytes | 5804141.000000 | 5469581.000000 | 1.00141179 | n/a | 0.95873296 | pass | - |
| full | small-named | p50 | ms | 4.036400 | 2.185450 | 1.00508975 | pass | 0.54426584 | pass | - |
| full | small-named | p95 | ms | 13.878600 | 8.878300 | 1.02188748 | pass | 0.64107624 | pass | - |
| full | small-named | p99 | ms | 18.403250 | 16.278700 | 1.02599861 | pass | 0.91196076 | pass | pass <= 0.95 |
| full | small-named | wall | ms | 2524.957750 | 1734.931400 | 1.00315238 | pass | 0.67418750 | pass | pass <= 0.90 |
| full | small-named | disk | bytes | 6538327.500000 | 5957490.500000 | 0.99098576 | n/a | 0.95063355 | pass | - |
| full | pressure-anonymous | p50 | ms | 2.360950 | 2.357500 | 0.99528621 | pass | 1.00749543 | pass | - |
| full | pressure-anonymous | p95 | ms | 11.106250 | 7.424550 | 1.11252812 | FAIL | 0.94786138 | pass | - |
| full | pressure-anonymous | p99 | ms | 17.157550 | 17.165650 | 1.00615707 | pass | 1.03122576 | pass | - |
| full | pressure-anonymous | wall | ms | 443.194300 | 436.863250 | 0.99112028 | pass | 0.99348693 | pass | - |
| full | pressure-anonymous | disk | bytes | 11481153.000000 | 11473403.000000 | 1.00058751 | n/a | 0.99945262 | pass | - |
| full | pressure-named | p50 | ms | 2.866550 | 2.796500 | 1.00033581 | pass | 0.99416879 | pass | - |
| full | pressure-named | p95 | ms | 11.972600 | 11.758950 | 0.66994831 | FAIL | 0.95745748 | pass | - |
| full | pressure-named | p99 | ms | 18.527850 | 17.861400 | 0.91867107 | FAIL | 1.01399028 | pass | - |
| full | pressure-named | wall | ms | 526.325900 | 501.941100 | 0.95080196 | pass | 0.96141800 | pass | - |
| full | pressure-named | disk | bytes | 12183078.000000 | 12170877.500000 | 0.99979684 | n/a | 0.99944002 | pass | - |
| full | queries-ordered | all_aggregates/median_us | us | 4.700000 | 4.750000 | 1.00000000 | pass | 1.02127660 | pass | - |
| full | queries-ordered | all_aggregates/p95_us | us | 5.500000 | 5.400000 | 1.00000000 | pass | 0.99090909 | pass | - |
| full | queries-ordered | broad_window/median_us | us | 4.950000 | 4.900000 | 0.99000000 | pass | 1.00000000 | pass | - |
| full | queries-ordered | broad_window/p95_us | us | 5.100000 | 5.050000 | 1.00000000 | pass | 1.00000000 | pass | - |
| full | queries-ordered | narrow_window/median_us | us | 4.000000 | 4.000000 | 1.00000000 | pass | 0.97560976 | pass | - |
| full | queries-ordered | narrow_window/p95_us | us | 4.200000 | 4.150000 | 1.00000000 | pass | 0.98809524 | pass | - |
| full | queries-ordered | unordered_filter/median_us | us | 2814.350000 | 2464.050000 | 1.01491474 | pass | 0.88131744 | pass | pass <= 0.90 |
| full | queries-ordered | unordered_filter/p95_us | us | 3135.050000 | 2761.950000 | 1.06951882 | FAIL | 0.87033889 | pass | pass <= 0.90 |
| full | queries-ordered | grouped/median_us | us | 6264.900000 | 6342.600000 | 1.00735216 | pass | 1.00453731 | pass | - |
| full | queries-ordered | grouped/p95_us | us | 7314.700000 | 7536.850000 | 1.15113427 | FAIL | 1.06733712 | FAIL | - |
| full | queries-ordered | min_max/median_us | us | 7.400000 | 7.500000 | 1.00000000 | pass | 1.00675676 | pass | - |
| full | queries-ordered | min_max/p95_us | us | 7.800000 | 7.750000 | 0.99358974 | pass | 1.00008325 | pass | - |
| full | queries-late | all_aggregates/median_us | us | 4.700000 | 4.650000 | 1.00000000 | pass | 0.98958333 | pass | - |
| full | queries-late | all_aggregates/p95_us | us | 5.350000 | 5.350000 | 1.00909091 | pass | 0.99090909 | pass | - |
| full | queries-late | broad_window/median_us | us | 4.900000 | 4.950000 | 1.00000000 | pass | 0.99038462 | pass | - |
| full | queries-late | broad_window/p95_us | us | 5.150000 | 5.200000 | 1.01980392 | pass | 0.98076212 | pass | - |
| full | queries-late | narrow_window/median_us | us | 4.050000 | 4.000000 | 1.00000000 | pass | 0.98780488 | pass | - |
| full | queries-late | narrow_window/p95_us | us | 4.200000 | 4.200000 | 1.00000000 | pass | 1.00000000 | pass | - |
| full | queries-late | unordered_filter/median_us | us | 2819.800000 | 2480.050000 | 0.99462910 | pass | 0.87851442 | pass | pass <= 0.90 |
| full | queries-late | unordered_filter/p95_us | us | 3249.000000 | 2798.200000 | 0.99208748 | pass | 0.85525172 | pass | pass <= 0.90 |
| full | queries-late | grouped/median_us | us | 6213.000000 | 6231.100000 | 1.00527292 | pass | 0.99980257 | pass | - |
| full | queries-late | grouped/p95_us | us | 7415.950000 | 7990.800000 | 1.00577958 | pass | 1.03116001 | pass | - |
| full | queries-late | min_max/median_us | us | 7.050000 | 7.200000 | 1.00000000 | pass | 1.02877847 | pass | - |
| full | queries-late | min_max/p95_us | us | 7.300000 | 7.400000 | 1.02064307 | pass | 1.00684932 | pass | - |
| full | identified-replay | p50 | us | 1.300000 | 1.300000 | 1.00000000 | pass | 1.00000000 | pass | - |
| full | identified-replay | p95 | us | 1.600000 | 1.800000 | 1.03125000 | pass | 1.09375000 | FAIL | - |
| full | identified-replay | p99 | us | 2.000000 | 2.150000 | 1.05131579 | FAIL | 1.07500000 | FAIL | - |
| half_1 | sparse-anonymous | p50 | ms | 1.889400 | 1.914050 | 1.02106936 | pass | 0.98999942 | pass | - |
| half_1 | sparse-anonymous | p95 | ms | 5.428000 | 5.383950 | 0.96366315 | pass | 0.94705689 | pass | - |
| half_1 | sparse-anonymous | p99 | ms | 15.035950 | 14.649400 | 0.98564440 | pass | 0.97512606 | pass | - |
| half_1 | sparse-anonymous | wall | ms | 1321.884000 | 1323.741100 | 0.97917528 | pass | 0.97001823 | pass | - |
| half_1 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_1 | sparse-named | p50 | ms | 1.922900 | 1.903250 | 1.00557777 | pass | 1.00144055 | pass | - |
| half_1 | sparse-named | p95 | ms | 5.835150 | 5.340100 | 1.07204064 | FAIL | 0.95159389 | pass | - |
| half_1 | sparse-named | p99 | ms | 14.406300 | 13.840550 | 1.03210412 | pass | 0.95388163 | pass | - |
| half_1 | sparse-named | wall | ms | 1281.679750 | 1241.983950 | 1.04364358 | pass | 0.95969368 | pass | - |
| half_1 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_1 | small-anonymous | p50 | ms | 4.039400 | 2.154650 | 0.96538064 | pass | 0.55368136 | pass | - |
| half_1 | small-anonymous | p95 | ms | 14.412100 | 10.268050 | 0.93897054 | FAIL | 0.66383748 | pass | - |
| half_1 | small-anonymous | p99 | ms | 19.433150 | 18.037850 | 1.02995939 | pass | 0.92269108 | pass | pass <= 0.95 |
| half_1 | small-anonymous | wall | ms | 2567.594350 | 1838.131750 | 0.97798953 | pass | 0.71628638 | pass | pass <= 0.90 |
| half_1 | small-anonymous | disk | bytes | 5811603.000000 | 5564473.500000 | 1.00141179 | n/a | 0.95873296 | pass | - |
| half_1 | small-named | p50 | ms | 3.996950 | 2.211400 | 1.00508975 | pass | 0.54751541 | pass | - |
| half_1 | small-named | p95 | ms | 13.776150 | 9.151250 | 1.01070825 | pass | 0.66819136 | pass | - |
| half_1 | small-named | p99 | ms | 20.549650 | 16.994100 | 1.01602979 | pass | 0.81772162 | pass | pass <= 0.95 |
| half_1 | small-named | wall | ms | 2541.207050 | 1756.300550 | 0.98882670 | pass | 0.68797093 | pass | pass <= 0.90 |
| half_1 | small-named | disk | bytes | 6545286.500000 | 6224613.000000 | 0.84503020 | n/a | 0.95063355 | pass | - |
| half_1 | pressure-anonymous | p50 | ms | 2.360950 | 2.319900 | 0.99528621 | pass | 0.99841880 | pass | - |
| half_1 | pressure-anonymous | p95 | ms | 8.015800 | 7.081950 | 1.25848197 | FAIL | 0.98720977 | pass | - |
| half_1 | pressure-anonymous | p99 | ms | 17.455700 | 20.111750 | 1.06452538 | FAIL | 1.19106804 | FAIL | - |
| half_1 | pressure-anonymous | wall | ms | 441.885550 | 439.135850 | 0.99112028 | pass | 1.04304500 | pass | - |
| half_1 | pressure-anonymous | disk | bytes | 11483225.500000 | 11473403.000000 | 1.00194584 | n/a | 0.99927076 | pass | - |
| half_1 | pressure-named | p50 | ms | 2.866550 | 2.808950 | 1.00007719 | pass | 1.00449889 | pass | - |
| half_1 | pressure-named | p95 | ms | 12.102300 | 11.646450 | 0.82303954 | FAIL | 0.72863177 | pass | - |
| half_1 | pressure-named | p99 | ms | 28.059050 | 20.242950 | 0.80861631 | FAIL | 0.78861453 | pass | - |
| half_1 | pressure-named | wall | ms | 572.415750 | 519.797200 | 0.89700706 | FAIL | 0.88561306 | pass | - |
| half_1 | pressure-named | disk | bytes | 12183078.000000 | 12168345.500000 | 0.99979684 | n/a | 0.99789895 | pass | - |
| half_1 | queries-ordered | all_aggregates/median_us | us | 4.700000 | 4.800000 | 1.02127660 | pass | 1.02150786 | pass | - |
| half_1 | queries-ordered | all_aggregates/p95_us | us | 5.450000 | 5.700000 | 1.00000000 | pass | 1.04514825 | pass | - |
| half_1 | queries-ordered | broad_window/median_us | us | 4.950000 | 4.950000 | 1.01020408 | pass | 1.02000000 | pass | - |
| half_1 | queries-ordered | broad_window/p95_us | us | 5.200000 | 5.250000 | 1.00961538 | pass | 1.00961538 | pass | - |
| half_1 | queries-ordered | narrow_window/median_us | us | 4.000000 | 4.000000 | 1.01250000 | pass | 1.01250000 | pass | - |
| half_1 | queries-ordered | narrow_window/p95_us | us | 4.200000 | 4.150000 | 1.00000000 | pass | 0.98809524 | pass | - |
| half_1 | queries-ordered | unordered_filter/median_us | us | 2767.350000 | 2461.750000 | 1.02146881 | pass | 0.89724047 | pass | pass <= 0.90 |
| half_1 | queries-ordered | unordered_filter/p95_us | us | 3079.500000 | 3127.050000 | 1.11857749 | FAIL | 1.00233483 | pass | FAIL <= 0.90 |
| half_1 | queries-ordered | grouped/median_us | us | 6264.900000 | 6244.950000 | 1.00634110 | pass | 0.99825833 | pass | - |
| half_1 | queries-ordered | grouped/p95_us | us | 7485.550000 | 7536.850000 | 1.20448167 | FAIL | 1.00955086 | pass | - |
| half_1 | queries-ordered | min_max/median_us | us | 7.850000 | 7.500000 | 0.94363223 | FAIL | 0.94980507 | pass | - |
| half_1 | queries-ordered | min_max/p95_us | us | 9.700000 | 7.750000 | 0.83410698 | FAIL | 0.99375843 | pass | - |
| half_1 | queries-late | all_aggregates/median_us | us | 4.750000 | 4.650000 | 0.98936170 | pass | 0.98958333 | pass | - |
| half_1 | queries-late | all_aggregates/p95_us | us | 5.350000 | 5.500000 | 1.00000000 | pass | 1.00942761 | pass | - |
| half_1 | queries-late | broad_window/median_us | us | 4.900000 | 5.000000 | 1.00000000 | pass | 1.01020408 | pass | - |
| half_1 | queries-late | broad_window/p95_us | us | 5.100000 | 5.200000 | 1.01980392 | pass | 0.97167756 | pass | - |
| half_1 | queries-late | narrow_window/median_us | us | 4.000000 | 4.050000 | 1.00000000 | pass | 0.98750000 | pass | - |
| half_1 | queries-late | narrow_window/p95_us | us | 4.200000 | 4.250000 | 1.01190476 | pass | 1.01190476 | pass | - |
| half_1 | queries-late | unordered_filter/median_us | us | 2731.200000 | 2494.100000 | 0.99333988 | pass | 0.88732153 | pass | pass <= 0.90 |
| half_1 | queries-late | unordered_filter/p95_us | us | 3140.400000 | 2898.450000 | 0.96648008 | pass | 0.87970408 | pass | pass <= 0.90 |
| half_1 | queries-late | grouped/median_us | us | 6195.850000 | 6175.800000 | 0.99796459 | pass | 0.99408687 | pass | - |
| half_1 | queries-late | grouped/p95_us | us | 7697.950000 | 8549.100000 | 0.98993280 | pass | 1.00631641 | pass | - |
| half_1 | queries-late | min_max/median_us | us | 7.000000 | 7.150000 | 1.02837314 | pass | 1.02919864 | pass | - |
| half_1 | queries-late | min_max/p95_us | us | 7.300000 | 7.300000 | 1.02758752 | pass | 1.00694444 | pass | - |
| half_1 | identified-replay | p50 | us | 1.300000 | 1.250000 | 1.00000000 | pass | 1.00000000 | pass | - |
| half_1 | identified-replay | p95 | us | 1.650000 | 1.700000 | 1.00000000 | pass | 1.00000000 | pass | - |
| half_1 | identified-replay | p99 | us | 1.950000 | 2.050000 | 1.05131579 | FAIL | 1.00000000 | pass | - |
| half_2 | sparse-anonymous | p50 | ms | 1.925350 | 1.903500 | 1.00739474 | pass | 0.98842481 | pass | - |
| half_2 | sparse-anonymous | p95 | ms | 5.349600 | 5.239050 | 1.02421126 | pass | 0.97166560 | pass | - |
| half_2 | sparse-anonymous | p99 | ms | 14.628400 | 14.059200 | 0.99698681 | pass | 0.96976225 | pass | - |
| half_2 | sparse-anonymous | wall | ms | 1250.571300 | 1246.312350 | 1.02271170 | pass | 0.98429690 | pass | - |
| half_2 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_2 | sparse-named | p50 | ms | 1.913150 | 1.927950 | 0.99490207 | pass | 1.00403000 | pass | - |
| half_2 | sparse-named | p95 | ms | 5.514800 | 5.418850 | 0.92543438 | FAIL | 1.02462899 | pass | - |
| half_2 | sparse-named | p99 | ms | 14.034550 | 13.854300 | 1.00836018 | pass | 0.98726750 | pass | - |
| half_2 | sparse-named | wall | ms | 1279.447750 | 1259.077500 | 0.98710966 | pass | 1.01715162 | pass | - |
| half_2 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_2 | small-anonymous | p50 | ms | 3.816400 | 2.144050 | 1.01076756 | pass | 0.56344810 | pass | - |
| half_2 | small-anonymous | p95 | ms | 13.731350 | 8.907550 | 1.01825099 | pass | 0.64875705 | pass | - |
| half_2 | small-anonymous | p99 | ms | 18.446300 | 16.615500 | 0.97656135 | pass | 0.92970506 | pass | pass <= 0.95 |
| half_2 | small-anonymous | wall | ms | 2446.478100 | 1765.135550 | 1.01198771 | pass | 0.76013490 | pass | pass <= 0.90 |
| half_2 | small-anonymous | disk | bytes | 5801463.000000 | 5215393.500000 | 1.00154833 | n/a | 0.91612130 | pass | - |
| half_2 | small-named | p50 | ms | 4.062100 | 2.164450 | 1.00769049 | pass | 0.54426584 | pass | - |
| half_2 | small-named | p95 | ms | 14.092900 | 8.463500 | 1.03608969 | pass | 0.61260492 | pass | - |
| half_2 | small-named | p99 | ms | 18.403250 | 15.665000 | 1.07522476 | FAIL | 0.91196076 | pass | pass <= 0.95 |
| half_2 | small-named | wall | ms | 2524.957750 | 1687.657650 | 1.03109970 | pass | 0.67418750 | pass | pass <= 0.90 |
| half_2 | small-named | disk | bytes | 6057094.500000 | 5345110.000000 | 1.01354180 | n/a | 0.91698792 | pass | - |
| half_2 | pressure-anonymous | p50 | ms | 2.360500 | 2.447600 | 0.99663910 | pass | 1.02544382 | pass | - |
| half_2 | pressure-anonymous | p95 | ms | 11.671100 | 8.962800 | 0.99558899 | pass | 0.80086057 | pass | - |
| half_2 | pressure-anonymous | p99 | ms | 17.157550 | 15.375950 | 0.90129114 | FAIL | 0.96073309 | pass | - |
| half_2 | pressure-anonymous | wall | ms | 451.081050 | 436.863250 | 0.99832467 | pass | 0.95630963 | pass | - |
| half_2 | pressure-anonymous | disk | bytes | 11477399.500000 | 11472210.500000 | 1.00008644 | n/a | 0.99945262 | pass | - |
| half_2 | pressure-named | p50 | ms | 2.830000 | 2.796100 | 1.02016664 | pass | 0.98582165 | pass | - |
| half_2 | pressure-named | p95 | ms | 11.832050 | 11.765550 | 0.66350495 | FAIL | 0.97727782 | pass | - |
| half_2 | pressure-named | p99 | ms | 15.566200 | 17.272650 | 1.20925594 | FAIL | 1.03411884 | pass | - |
| half_2 | pressure-named | wall | ms | 515.428850 | 495.740800 | 0.95888349 | pass | 0.97894427 | pass | - |
| half_2 | pressure-named | disk | bytes | 12185942.500000 | 12174615.000000 | 0.99946272 | n/a | 0.99944002 | pass | - |
| half_2 | queries-ordered | all_aggregates/median_us | us | 4.700000 | 4.700000 | 1.00000000 | pass | 1.00000000 | pass | - |
| half_2 | queries-ordered | all_aggregates/p95_us | us | 5.500000 | 5.400000 | 1.00000000 | pass | 0.98181818 | pass | - |
| half_2 | queries-ordered | broad_window/median_us | us | 4.950000 | 4.900000 | 0.98000000 | pass | 0.99000000 | pass | - |
| half_2 | queries-ordered | broad_window/p95_us | us | 5.100000 | 5.050000 | 1.00000000 | pass | 1.00000000 | pass | - |
| half_2 | queries-ordered | narrow_window/median_us | us | 4.000000 | 3.950000 | 0.98780488 | pass | 0.97530488 | pass | - |
| half_2 | queries-ordered | narrow_window/p95_us | us | 4.200000 | 4.150000 | 0.98809524 | pass | 0.98809524 | pass | - |
| half_2 | queries-ordered | unordered_filter/median_us | us | 2844.900000 | 2472.550000 | 1.01491474 | pass | 0.88131744 | pass | pass <= 0.90 |
| half_2 | queries-ordered | unordered_filter/p95_us | us | 3602.350000 | 2761.950000 | 0.89588758 | FAIL | 0.86990864 | pass | pass <= 0.90 |
| half_2 | queries-ordered | grouped/median_us | us | 6271.600000 | 6431.600000 | 1.00735216 | pass | 1.02414579 | pass | - |
| half_2 | queries-ordered | grouped/p95_us | us | 7163.700000 | 8077.100000 | 1.06878367 | FAIL | 1.15896656 | FAIL | - |
| half_2 | queries-ordered | min_max/median_us | us | 7.400000 | 7.500000 | 1.00000000 | pass | 1.01351351 | pass | - |
| half_2 | queries-ordered | min_max/p95_us | us | 7.800000 | 7.750000 | 1.00000000 | pass | 1.00008325 | pass | - |
| half_2 | queries-late | all_aggregates/median_us | us | 4.700000 | 4.650000 | 1.01063830 | pass | 0.98936170 | pass | - |
| half_2 | queries-late | all_aggregates/p95_us | us | 5.350000 | 5.300000 | 1.02866473 | pass | 0.98148148 | pass | - |
| half_2 | queries-late | broad_window/median_us | us | 5.000000 | 4.900000 | 0.98019608 | pass | 0.97039216 | pass | - |
| half_2 | queries-late | broad_window/p95_us | us | 5.250000 | 5.200000 | 1.00056604 | pass | 1.01056604 | pass | - |
| half_2 | queries-late | narrow_window/median_us | us | 4.100000 | 4.000000 | 0.97590012 | pass | 0.98780488 | pass | - |
| half_2 | queries-late | narrow_window/p95_us | us | 4.250000 | 4.150000 | 0.98863636 | pass | 0.97674419 | pass | - |
| half_2 | queries-late | unordered_filter/median_us | us | 2852.850000 | 2480.050000 | 1.00898921 | pass | 0.86440066 | pass | pass <= 0.90 |
| half_2 | queries-late | unordered_filter/p95_us | us | 3363.700000 | 2786.300000 | 1.01697625 | pass | 0.82944397 | pass | pass <= 0.90 |
| half_2 | queries-late | grouped/median_us | us | 6213.000000 | 6249.400000 | 1.00720011 | pass | 1.00634357 | pass | - |
| half_2 | queries-late | grouped/p95_us | us | 7162.700000 | 7486.550000 | 1.00577958 | pass | 1.08289641 | FAIL | - |
| half_2 | queries-late | min_max/median_us | us | 7.050000 | 7.200000 | 1.00000000 | pass | 1.02132797 | pass | - |
| half_2 | queries-late | min_max/p95_us | us | 7.400000 | 7.400000 | 1.00694444 | pass | 1.00684932 | pass | - |
| half_2 | identified-replay | p50 | us | 1.300000 | 1.300000 | 1.03846154 | pass | 1.00000000 | pass | - |
| half_2 | identified-replay | p95 | us | 1.600000 | 1.800000 | 1.06250000 | FAIL | 1.12500000 | FAIL | - |
| half_2 | identified-replay | p99 | us | 2.000000 | 2.150000 | 1.07763158 | FAIL | 1.10263158 | FAIL | - |

## Exact preservation and next work

The archive contains 32,718 files, 3,519
directories, 49 bounded ZIP parts and
3,830,039,810 logical bytes. All member checksums, order,
offsets, sizes, complete original/restored file hashes and directory sets passed
before and after the complete independent restored audit. It launched no Native
processes or timers and changed no existing files. Only inventoried regenerable
build/Python caches are excluded; all originals remain. Closed raw logs are
byte-exact gzip supplements with both raw and encoded hashes. No complete
verified private GitHub backup or recent raw deletion is claimed.

Next engineering target: avoid general publication-buffer allocation for a
verified duplicate receipt while retaining full submitted-content validation,
the unhealthy-writer check, original generations and the normal publication path
for new IDs. Diagnose grouping separately before attributing or changing it.
New work requires a new experiment number and predeclared controls. Older
106/107 rejection and 108 diagnostic exact-archive closures remain pending;
their original raw data, source and every failure remain stored on D:.

See [complete reproduction](benchmarks/adaptive-speed-109/REPRODUCE.md),
[complete original audit](benchmarks/adaptive-speed-109/complete-audit-proof.json),
[restored audit](benchmarks/adaptive-speed-109/restored-audit-proof.json),
[all native results](benchmarks/adaptive-speed-109/native-audit.json) and
[decision and unstarted service specs](benchmarks/adaptive-speed-109/native-rejection-decision.json).
Borrowed receipt lookup follows [Rust's BTreeMap API](https://doc.rust-lang.org/std/collections/struct.BTreeMap.html#method.get);
that documentation supports the design, not a Kestrel speed claim.
