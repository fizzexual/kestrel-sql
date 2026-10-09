# Adaptive engine trial 110

The candidate implements workload-dependent collection, query dispatch and
verified duplicate replay. **Release qualification fails.** Supported main
remains0.3.16; candidate0.3.17 metadata is unreleased. This is not a fresh
competitor comparison or a claim of winning every benchmark.

The exact trial107 collector chooses immediate sparse work, bounded small-group
lookahead or ready pressure draining. Trial109 query dispatch chooses prefix
indexes first, eligible fused single-column ungrouped COUNT/SUM/AVG next, and
existing general selection/dense/sparse grouping otherwise. Trial110 adds a
borrowed lookup for already durable batch IDs, retaining the healthy-writer,
shape/budget/ID/full submitted-content checks and original receipt generation.
Unknown IDs keep the existing publication path. The optional adaptive-engine
feature enables adaptive-collection,adaptive-filter and adaptive-replay.
Publication,source/WAL/ACK semantics,formats and maintenance remain protected.

748 fresh tests across eight complete debug/release configurations,five strict
all-target lints and independent normal/fault artifact builds passed. Fresh
359-command external recovery passed28 publication interruptions,10 corruptions,
CAT2/CAT3 reads,two byte fixtures,256 concurrent anonymous ACKs,two named scenarios
and300 cold SQLite-model SQL checks. Physical power-loss and resource-exhaustion
guarantees were not tested. Native CPU/peak memory were not measured; service
resource/loss/capacity checks remain unstarted.

All324 predeclared Native cases completed exactly once. All479,232 ACKs and
2,921,356,800 full checksum bytes independently pass row,receipt,index,query,
quantile,order and provenance replay. All30 goals and every prior gate remain;
six required replay goals were added before code/copy/build. There were no
numerical retries,selected rounds or loosened gates. Performance fails93/153
A/A controls,35/171 regression guards and11/30 goals. All252 service specs are
preserved as UNSTARTED/UNTESTED because mandatory Native qualification failed.

## Promising full-run results, inconclusive across the required halves

| Replay metric | Before | After | Paired candidate/A | Full A/A | Required halves |
| --- | ---: | ---: | ---: | ---: | --- |
| p95 |2.35us|1.95us|0.82575758|0.96085859|half2 control FAIL|
| p99 |2.90us|2.35us|0.83501684|1.03146853|both half controls FAIL;half1 goal FAIL|

Paired ratios use within-round comparisons and can differ from quotients of
displayed medians. No improvement goal passes its target and baseline control
in full and both halves. The initial commentary claim that replayp95 passed
both half controls was incorrect and immediately corrected. Half2 p95 A/A
is0.93996416,outside the unchanged0.95..1.05 gate. These are not robust verified
wins. Calibrated regressions include sparse-writep95,pressure-namedp50/completion
and late-data grouped/extrema queries. Exclusive causes are not established.

The first build failed only in a new shared test checker,which tried to read the
held Windows lease file. Every original source,failed test,log,target and store
is preserved. The exact checker-only repair verifies the lease length is zero,
proving its complete empty bytes,and reads every other file byte. No runtime,
Cargo,file exclusion or gate change occurred. The full build was run afresh.

## Every before/after, control, regression check and goal

All171 full/half comparisons follow. Live operation units are milliseconds,
queries/replay are microseconds,and disk is bytes. A/A passes within0.95..1.05;
regression limits remain1.05. Goals remain0.95 for small-writep99 and0.90 for
small-write completion,filter and replay targets. Maxima/raw stalls are retained.

| Scope | Workload | Metric | Unit | Before median | After median | A/A | Control | Candidate/A | Regression | Goal |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- |
| full | sparse-anonymous | p50 | ms | 2.368950 | 2.436900 | 0.94340150 | FAIL | 1.00162069 | pass | - |
| full | sparse-anonymous | p95 | ms | 6.804400 | 7.050600 | 1.04796046 | pass | 1.06526401 | FAIL | - |
| full | sparse-anonymous | p99 | ms | 18.843950 | 21.141100 | 1.05859901 | FAIL | 1.05196834 | FAIL | - |
| full | sparse-anonymous | wall | ms | 1565.145600 | 1667.540500 | 1.01969556 | pass | 1.03377089 | pass | - |
| full | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| full | sparse-named | p50 | ms | 2.396050 | 2.273250 | 0.90197505 | FAIL | 0.94322693 | pass | - |
| full | sparse-named | p95 | ms | 6.840100 | 6.126100 | 0.95273420 | pass | 0.92699300 | pass | - |
| full | sparse-named | p99 | ms | 18.590600 | 18.666650 | 0.93163612 | FAIL | 0.96248657 | pass | - |
| full | sparse-named | wall | ms | 1552.576950 | 1525.581900 | 0.92382261 | FAIL | 0.96767973 | pass | - |
| full | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| full | small-anonymous | p50 | ms | 4.811800 | 2.368050 | 1.04387409 | pass | 0.54950028 | pass | - |
| full | small-anonymous | p95 | ms | 17.272100 | 10.731350 | 1.00897363 | pass | 0.65260231 | pass | - |
| full | small-anonymous | p99 | ms | 25.847700 | 19.694950 | 1.07264687 | FAIL | 0.85903917 | pass | pass <= 0.95 |
| full | small-anonymous | wall | ms | 3045.101300 | 1952.824450 | 1.04963653 | pass | 0.71173455 | pass | pass <= 0.90 |
| full | small-anonymous | disk | bytes | 5661781.000000 | 5463679.000000 | 1.00000478 | n/a | 0.94980753 | pass | - |
| full | small-named | p50 | ms | 4.812900 | 2.553350 | 0.99457863 | pass | 0.54188725 | pass | - |
| full | small-named | p95 | ms | 16.581450 | 11.949250 | 1.01224168 | pass | 0.65931173 | pass | - |
| full | small-named | p99 | ms | 26.325750 | 19.620700 | 1.03681486 | pass | 0.76087396 | pass | pass <= 0.95 |
| full | small-named | wall | ms | 3090.828000 | 2013.246100 | 1.00880902 | pass | 0.66850920 | pass | pass <= 0.90 |
| full | small-named | disk | bytes | 6408576.000000 | 6092631.500000 | 1.00387612 | n/a | 0.97210475 | pass | - |
| full | pressure-anonymous | p50 | ms | 3.191500 | 2.811900 | 0.89855897 | FAIL | 0.93609370 | pass | - |
| full | pressure-anonymous | p95 | ms | 11.868050 | 12.410600 | 1.02917044 | pass | 1.04637794 | pass | - |
| full | pressure-anonymous | p99 | ms | 26.640950 | 22.924650 | 0.98504742 | pass | 0.83140793 | pass | - |
| full | pressure-anonymous | wall | ms | 548.227950 | 505.282100 | 0.93751782 | FAIL | 0.95218283 | pass | - |
| full | pressure-anonymous | disk | bytes | 10657136.500000 | 11403276.000000 | 1.00134750 | n/a | 1.07579339 | FAIL | - |
| full | pressure-named | p50 | ms | 3.333400 | 3.607400 | 1.02705251 | pass | 1.11362661 | FAIL | - |
| full | pressure-named | p95 | ms | 12.198900 | 12.889000 | 0.94868067 | FAIL | 1.08858434 | FAIL | - |
| full | pressure-named | p99 | ms | 24.438400 | 24.220550 | 0.93544244 | FAIL | 0.81638951 | pass | - |
| full | pressure-named | wall | ms | 593.215500 | 641.986900 | 1.01289725 | pass | 1.09494215 | FAIL | - |
| full | pressure-named | disk | bytes | 12142666.000000 | 12163416.000000 | 1.00013977 | n/a | 1.03127308 | pass | - |
| full | queries-ordered | all_aggregates/median_us | us | 5.450000 | 4.900000 | 0.94916667 | FAIL | 1.00000000 | pass | - |
| full | queries-ordered | all_aggregates/p95_us | us | 7.100000 | 6.100000 | 0.99107143 | pass | 0.99115044 | pass | - |
| full | queries-ordered | broad_window/median_us | us | 5.550000 | 5.000000 | 1.10657596 | FAIL | 0.94265631 | pass | - |
| full | queries-ordered | broad_window/p95_us | us | 7.500000 | 5.750000 | 0.99846054 | pass | 0.87095238 | pass | - |
| full | queries-ordered | narrow_window/median_us | us | 4.400000 | 4.100000 | 1.01775068 | pass | 0.96399535 | pass | - |
| full | queries-ordered | narrow_window/p95_us | us | 4.650000 | 4.600000 | 1.06719368 | FAIL | 0.97646733 | pass | - |
| full | queries-ordered | unordered_filter/median_us | us | 3448.250000 | 3634.900000 | 1.10831042 | FAIL | 0.90891131 | pass | FAIL <= 0.90 |
| full | queries-ordered | unordered_filter/p95_us | us | 4412.150000 | 4994.650000 | 1.18695645 | FAIL | 1.06535395 | FAIL | FAIL <= 0.90 |
| full | queries-ordered | grouped/median_us | us | 8167.050000 | 8391.750000 | 1.00901926 | pass | 0.95518211 | pass | - |
| full | queries-ordered | grouped/p95_us | us | 12463.800000 | 11811.850000 | 0.84339806 | FAIL | 0.88582499 | pass | - |
| full | queries-ordered | min_max/median_us | us | 7.650000 | 9.050000 | 1.00666667 | pass | 0.99333333 | pass | - |
| full | queries-ordered | min_max/p95_us | us | 8.200000 | 10.000000 | 0.96913580 | pass | 0.97515237 | pass | - |
| full | queries-late | all_aggregates/median_us | us | 6.000000 | 5.400000 | 0.87992832 | FAIL | 0.98212005 | pass | - |
| full | queries-late | all_aggregates/p95_us | us | 8.100000 | 6.450000 | 0.79037736 | FAIL | 0.91707317 | pass | - |
| full | queries-late | broad_window/median_us | us | 6.100000 | 5.700000 | 0.98186275 | pass | 0.97295470 | pass | - |
| full | queries-late | broad_window/p95_us | us | 9.000000 | 6.350000 | 0.94736842 | FAIL | 0.93435859 | pass | - |
| full | queries-late | narrow_window/median_us | us | 4.950000 | 4.700000 | 0.97760080 | pass | 0.96938776 | pass | - |
| full | queries-late | narrow_window/p95_us | us | 6.150000 | 4.850000 | 0.93556772 | FAIL | 0.86657469 | pass | - |
| full | queries-late | unordered_filter/median_us | us | 4316.950000 | 4234.300000 | 0.97464513 | pass | 0.90256290 | pass | FAIL <= 0.90 |
| full | queries-late | unordered_filter/p95_us | us | 5963.100000 | 6042.850000 | 0.92404964 | FAIL | 0.91547859 | pass | FAIL <= 0.90 |
| full | queries-late | grouped/median_us | us | 8842.000000 | 9679.950000 | 0.97309417 | pass | 1.06975177 | FAIL | - |
| full | queries-late | grouped/p95_us | us | 13383.300000 | 14418.700000 | 0.98198437 | pass | 1.14548173 | FAIL | - |
| full | queries-late | min_max/median_us | us | 8.000000 | 9.150000 | 1.02993967 | pass | 1.13748597 | FAIL | - |
| full | queries-late | min_max/p95_us | us | 8.850000 | 12.800000 | 0.97943723 | pass | 1.10774213 | FAIL | - |
| full | identified-replay | p50 | us | 1.500000 | 1.250000 | 1.05555556 | FAIL | 0.82307692 | pass | - |
| full | identified-replay | p95 | us | 2.350000 | 1.950000 | 0.96085859 | pass | 0.82575758 | pass | pass <= 0.90 |
| full | identified-replay | p99 | us | 2.900000 | 2.350000 | 1.03146853 | pass | 0.83501684 | pass | pass <= 0.90 |
| half_1 | sparse-anonymous | p50 | ms | 2.368950 | 2.362250 | 1.03143245 | pass | 1.02837154 | pass | - |
| half_1 | sparse-anonymous | p95 | ms | 6.911900 | 7.224550 | 1.04796046 | pass | 1.08447232 | FAIL | - |
| half_1 | sparse-anonymous | p99 | ms | 18.843950 | 19.219700 | 1.16353457 | FAIL | 1.03517336 | pass | - |
| half_1 | sparse-anonymous | wall | ms | 1554.118900 | 1655.470200 | 1.06224786 | FAIL | 1.06899644 | FAIL | - |
| half_1 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_1 | sparse-named | p50 | ms | 2.535800 | 2.273250 | 0.90197505 | FAIL | 0.88614696 | pass | - |
| half_1 | sparse-named | p95 | ms | 7.140250 | 6.126100 | 0.91809275 | FAIL | 0.84297035 | pass | - |
| half_1 | sparse-named | p99 | ms | 20.847650 | 18.666650 | 0.93192532 | FAIL | 0.86489603 | pass | - |
| half_1 | sparse-named | wall | ms | 1698.215300 | 1525.581900 | 0.89524756 | FAIL | 0.88186184 | pass | - |
| half_1 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_1 | small-anonymous | p50 | ms | 5.001450 | 2.596550 | 1.13344097 | FAIL | 0.54950028 | pass | - |
| half_1 | small-anonymous | p95 | ms | 18.708250 | 12.697250 | 1.19208747 | FAIL | 0.65745978 | pass | - |
| half_1 | small-anonymous | p99 | ms | 26.592600 | 21.543050 | 1.11669720 | FAIL | 0.97195611 | pass | FAIL <= 0.95 |
| half_1 | small-anonymous | wall | ms | 3206.411050 | 2090.438450 | 1.15893095 | FAIL | 0.73471164 | pass | pass <= 0.90 |
| half_1 | small-anonymous | disk | bytes | 5747401.000000 | 5224829.000000 | 1.00102459 | n/a | 0.94482565 | pass | - |
| half_1 | small-named | p50 | ms | 5.082700 | 2.916450 | 0.93303753 | FAIL | 0.55866604 | pass | - |
| half_1 | small-named | p95 | ms | 18.716900 | 12.787200 | 0.94754678 | FAIL | 0.67313924 | pass | - |
| half_1 | small-named | p99 | ms | 29.749400 | 23.482300 | 0.92178755 | FAIL | 0.74747038 | pass | pass <= 0.95 |
| half_1 | small-named | wall | ms | 3293.843750 | 2209.613450 | 0.94975671 | FAIL | 0.66850920 | pass | pass <= 0.90 |
| half_1 | small-named | disk | bytes | 6403083.000000 | 6107730.000000 | 1.01652226 | n/a | 0.97766195 | pass | - |
| half_1 | pressure-anonymous | p50 | ms | 2.920950 | 2.687500 | 0.92448370 | FAIL | 0.94404414 | pass | - |
| half_1 | pressure-anonymous | p95 | ms | 13.960550 | 12.667150 | 0.90258649 | FAIL | 0.92997746 | pass | - |
| half_1 | pressure-anonymous | p99 | ms | 24.735000 | 22.573100 | 0.98914226 | pass | 0.83140793 | pass | - |
| half_1 | pressure-anonymous | wall | ms | 513.962450 | 477.714150 | 0.93751782 | FAIL | 0.95218283 | pass | - |
| half_1 | pressure-anonymous | disk | bytes | 10663320.500000 | 10642622.500000 | 0.93203289 | n/a | 1.00833603 | pass | - |
| half_1 | pressure-named | p50 | ms | 3.333400 | 3.473650 | 1.11155559 | FAIL | 1.06264423 | FAIL | - |
| half_1 | pressure-named | p95 | ms | 10.836050 | 12.889000 | 1.15740467 | FAIL | 1.24316162 | FAIL | - |
| half_1 | pressure-named | p99 | ms | 27.663850 | 24.089000 | 1.19199936 | FAIL | 1.07045030 | FAIL | - |
| half_1 | pressure-named | wall | ms | 593.215500 | 645.214500 | 1.12685199 | FAIL | 1.11148013 | FAIL | - |
| half_1 | pressure-named | disk | bytes | 11352776.500000 | 12169894.000000 | 1.00303686 | n/a | 1.10285610 | FAIL | - |
| half_1 | queries-ordered | all_aggregates/median_us | us | 6.150000 | 4.900000 | 0.90867925 | FAIL | 0.97959184 | pass | - |
| half_1 | queries-ordered | all_aggregates/p95_us | us | 9.800000 | 6.400000 | 0.86774194 | FAIL | 0.99115044 | pass | - |
| half_1 | queries-ordered | broad_window/median_us | us | 7.950000 | 4.950000 | 1.05555556 | FAIL | 0.77476415 | pass | - |
| half_1 | queries-ordered | broad_window/p95_us | us | 9.650000 | 5.700000 | 0.93307649 | FAIL | 0.73717514 | pass | - |
| half_1 | queries-ordered | narrow_window/median_us | us | 6.900000 | 4.100000 | 0.97258852 | pass | 0.79487179 | pass | - |
| half_1 | queries-ordered | narrow_window/p95_us | us | 7.450000 | 5.300000 | 1.04545455 | pass | 0.91144902 | pass | - |
| half_1 | queries-ordered | unordered_filter/median_us | us | 5049.950000 | 3573.050000 | 1.09073840 | FAIL | 0.85771364 | pass | pass <= 0.90 |
| half_1 | queries-ordered | unordered_filter/p95_us | us | 7356.150000 | 5531.000000 | 1.05997195 | FAIL | 0.88742130 | pass | pass <= 0.90 |
| half_1 | queries-ordered | grouped/median_us | us | 8167.050000 | 9484.650000 | 1.01548175 | pass | 1.03655910 | pass | - |
| half_1 | queries-ordered | grouped/p95_us | us | 14509.550000 | 13877.600000 | 0.87557339 | FAIL | 0.88582499 | pass | - |
| half_1 | queries-ordered | min_max/median_us | us | 7.750000 | 9.300000 | 1.51049075 | FAIL | 1.10809460 | FAIL | - |
| half_1 | queries-ordered | min_max/p95_us | us | 8.100000 | 10.900000 | 2.01898102 | FAIL | 1.15137473 | FAIL | - |
| half_1 | queries-late | all_aggregates/median_us | us | 6.050000 | 5.750000 | 0.92527979 | FAIL | 1.00580239 | pass | - |
| half_1 | queries-late | all_aggregates/p95_us | us | 8.250000 | 7.350000 | 0.87759047 | FAIL | 1.05751033 | FAIL | - |
| half_1 | queries-late | broad_window/median_us | us | 6.200000 | 6.000000 | 0.95134409 | pass | 0.92715054 | pass | - |
| half_1 | queries-late | broad_window/p95_us | us | 8.800000 | 7.000000 | 1.05943396 | FAIL | 0.94585569 | pass | - |
| half_1 | queries-late | narrow_window/median_us | us | 5.100000 | 5.000000 | 0.93210361 | FAIL | 0.92248823 | pass | - |
| half_1 | queries-late | narrow_window/p95_us | us | 7.300000 | 5.450000 | 0.90611495 | FAIL | 0.77696998 | pass | - |
| half_1 | queries-late | unordered_filter/median_us | us | 4469.550000 | 4259.350000 | 1.01748331 | pass | 0.89084789 | pass | pass <= 0.90 |
| half_1 | queries-late | unordered_filter/p95_us | us | 6404.250000 | 6042.850000 | 1.04911863 | pass | 0.91869182 | pass | FAIL <= 0.90 |
| half_1 | queries-late | grouped/median_us | us | 10485.100000 | 10190.150000 | 0.96157878 | pass | 1.08105082 | FAIL | - |
| half_1 | queries-late | grouped/p95_us | us | 14724.550000 | 15317.750000 | 0.98198437 | pass | 1.14548173 | FAIL | - |
| half_1 | queries-late | min_max/median_us | us | 8.750000 | 9.950000 | 1.02993967 | pass | 1.16987522 | FAIL | - |
| half_1 | queries-late | min_max/p95_us | us | 11.300000 | 14.000000 | 0.89160401 | FAIL | 1.38862403 | FAIL | - |
| half_1 | identified-replay | p50 | us | 1.550000 | 1.400000 | 0.92463235 | FAIL | 0.86160714 | pass | - |
| half_1 | identified-replay | p95 | us | 2.350000 | 2.250000 | 0.98863636 | pass | 0.85139860 | pass | pass <= 0.90 |
| half_1 | identified-replay | p99 | us | 2.850000 | 3.100000 | 1.19055944 | FAIL | 0.90871254 | pass | FAIL <= 0.90 |
| half_2 | sparse-anonymous | p50 | ms | 2.348650 | 2.436900 | 0.94340150 | FAIL | 0.99512302 | pass | - |
| half_2 | sparse-anonymous | p95 | ms | 6.519050 | 6.844300 | 1.05497050 | FAIL | 1.02350776 | pass | - |
| half_2 | sparse-anonymous | p99 | ms | 18.735250 | 21.751450 | 1.02947478 | pass | 1.09973818 | FAIL | - |
| half_2 | sparse-anonymous | wall | ms | 1596.373550 | 1667.540500 | 1.01969556 | pass | 1.00887393 | pass | - |
| half_2 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_2 | sparse-named | p50 | ms | 2.288850 | 2.288050 | 0.92277713 | FAIL | 1.02522215 | pass | - |
| half_2 | sparse-named | p95 | ms | 6.278150 | 6.170600 | 0.99392657 | pass | 1.00035778 | pass | - |
| half_2 | sparse-named | p99 | ms | 17.570100 | 18.114900 | 0.91286876 | FAIL | 1.01968183 | pass | - |
| half_2 | sparse-named | wall | ms | 1501.987000 | 1529.521600 | 0.97075120 | pass | 1.04947639 | pass | - |
| half_2 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | - |
| half_2 | small-anonymous | p50 | ms | 4.448600 | 2.324250 | 0.92982316 | FAIL | 0.53554506 | pass | - |
| half_2 | small-anonymous | p95 | ms | 15.570300 | 9.812500 | 0.92064150 | FAIL | 0.65260231 | pass | - |
| half_2 | small-anonymous | p99 | ms | 25.794750 | 17.749450 | 1.06691944 | FAIL | 0.77150739 | pass | pass <= 0.95 |
| half_2 | small-anonymous | wall | ms | 2874.127450 | 1877.476550 | 0.93888453 | FAIL | 0.68134196 | pass | pass <= 0.90 |
| half_2 | small-anonymous | disk | bytes | 4963997.500000 | 5484018.000000 | 0.99896952 | n/a | 1.05026110 | FAIL | - |
| half_2 | small-named | p50 | ms | 4.557750 | 2.358700 | 1.03879121 | pass | 0.51746745 | pass | - |
| half_2 | small-named | p95 | ms | 15.222650 | 9.891200 | 1.07472735 | FAIL | 0.64871321 | pass | - |
| half_2 | small-named | p99 | ms | 24.497450 | 17.892850 | 1.14462044 | FAIL | 0.83822534 | pass | pass <= 0.95 |
| half_2 | small-named | wall | ms | 2963.173550 | 1852.644500 | 1.09101837 | FAIL | 0.64598915 | pass | pass <= 0.90 |
| half_2 | small-named | disk | bytes | 6417548.500000 | 5953293.500000 | 0.99786875 | n/a | 0.96679915 | pass | - |
| half_2 | pressure-anonymous | p50 | ms | 3.255550 | 3.038300 | 0.85116394 | FAIL | 0.91874018 | pass | - |
| half_2 | pressure-anonymous | p95 | ms | 11.550800 | 12.081400 | 1.36632305 | FAIL | 1.04637794 | pass | - |
| half_2 | pressure-anonymous | p99 | ms | 28.586600 | 22.924650 | 0.91106003 | FAIL | 0.87647945 | pass | - |
| half_2 | pressure-anonymous | wall | ms | 557.483100 | 549.603350 | 0.96163342 | pass | 0.94794279 | pass | - |
| half_2 | pressure-anonymous | disk | bytes | 10657136.500000 | 11422469.500000 | 1.00323053 | n/a | 1.07929682 | FAIL | - |
| half_2 | pressure-named | p50 | ms | 3.224850 | 3.656800 | 1.00682271 | pass | 1.11362661 | FAIL | - |
| half_2 | pressure-named | p95 | ms | 13.300200 | 11.502000 | 0.87489885 | FAIL | 0.96220521 | pass | - |
| half_2 | pressure-named | p99 | ms | 24.438400 | 24.413250 | 0.86588299 | FAIL | 0.81262659 | pass | - |
| half_2 | pressure-named | wall | ms | 579.105600 | 622.829700 | 0.99526310 | pass | 1.09494215 | FAIL | - |
| half_2 | pressure-named | disk | bytes | 12170379.500000 | 12132428.500000 | 0.99988215 | n/a | 0.99741656 | pass | - |
| half_2 | queries-ordered | all_aggregates/median_us | us | 4.950000 | 5.050000 | 1.01041667 | pass | 1.00000000 | pass | - |
| half_2 | queries-ordered | all_aggregates/p95_us | us | 5.750000 | 5.900000 | 1.01785714 | pass | 1.00016234 | pass | - |
| half_2 | queries-ordered | broad_window/median_us | us | 5.200000 | 5.250000 | 1.11352041 | FAIL | 1.00000000 | pass | - |
| half_2 | queries-ordered | broad_window/p95_us | us | 6.600000 | 5.750000 | 1.17019608 | FAIL | 0.99434000 | pass | - |
| half_2 | queries-ordered | narrow_window/median_us | us | 4.150000 | 4.200000 | 1.09738372 | FAIL | 1.00000000 | pass | - |
| half_2 | queries-ordered | narrow_window/p95_us | us | 4.400000 | 4.400000 | 1.09490986 | FAIL | 1.00029036 | pass | - |
| half_2 | queries-ordered | unordered_filter/median_us | us | 3143.650000 | 3634.900000 | 1.10831042 | FAIL | 1.10508842 | FAIL | FAIL <= 0.90 |
| half_2 | queries-ordered | unordered_filter/p95_us | us | 3810.550000 | 4700.600000 | 1.20796702 | FAIL | 1.23958672 | FAIL | FAIL <= 0.90 |
| half_2 | queries-ordered | grouped/median_us | us | 8309.450000 | 7536.500000 | 0.90231182 | FAIL | 0.92040135 | pass | - |
| half_2 | queries-ordered | grouped/p95_us | us | 10848.000000 | 9779.050000 | 0.80544683 | FAIL | 0.93049146 | pass | - |
| half_2 | queries-ordered | min_max/median_us | us | 7.600000 | 7.650000 | 0.98051948 | pass | 0.98034632 | pass | - |
| half_2 | queries-ordered | min_max/p95_us | us | 9.150000 | 7.950000 | 0.84658678 | FAIL | 0.86383442 | pass | - |
| half_2 | queries-late | all_aggregates/median_us | us | 5.750000 | 5.250000 | 0.83788707 | FAIL | 0.94156041 | pass | - |
| half_2 | queries-late | all_aggregates/p95_us | us | 8.100000 | 6.400000 | 0.72126984 | FAIL | 0.76666667 | pass | - |
| half_2 | queries-late | broad_window/median_us | us | 5.450000 | 5.500000 | 0.99019608 | pass | 0.97295470 | pass | - |
| half_2 | queries-late | broad_window/p95_us | us | 9.050000 | 6.350000 | 0.73308271 | FAIL | 0.88520619 | pass | - |
| half_2 | queries-late | narrow_window/median_us | us | 4.500000 | 4.550000 | 1.00000000 | pass | 0.97959184 | pass | - |
| half_2 | queries-late | narrow_window/p95_us | us | 5.100000 | 4.700000 | 0.93556772 | FAIL | 0.86657469 | pass | - |
| half_2 | queries-late | unordered_filter/median_us | us | 3912.150000 | 3703.450000 | 0.97464513 | pass | 0.93337975 | pass | FAIL <= 0.90 |
| half_2 | queries-late | unordered_filter/p95_us | us | 5675.300000 | 5082.700000 | 0.83899621 | FAIL | 0.91080247 | pass | FAIL <= 0.90 |
| half_2 | queries-late | grouped/median_us | us | 7758.350000 | 8077.050000 | 0.97309417 | pass | 1.04560587 | pass | - |
| half_2 | queries-late | grouped/p95_us | us | 9903.100000 | 12266.550000 | 1.02354786 | pass | 1.18148179 | FAIL | - |
| half_2 | queries-late | min_max/median_us | us | 7.600000 | 8.350000 | 1.04775227 | pass | 1.07581290 | FAIL | - |
| half_2 | queries-late | min_max/p95_us | us | 8.400000 | 11.850000 | 1.01240426 | pass | 1.10030179 | FAIL | - |
| half_2 | identified-replay | p50 | us | 1.500000 | 1.150000 | 1.12222222 | FAIL | 0.82307692 | pass | - |
| half_2 | identified-replay | p95 | us | 2.450000 | 1.750000 | 0.93996416 | FAIL | 0.82407407 | pass | pass <= 0.90 |
| half_2 | identified-replay | p99 | us | 3.050000 | 2.200000 | 0.88311688 | FAIL | 0.79144385 | pass | pass <= 0.90 |

## Exact preservation and next work

The archive contains 36,694 files, 5,085
directories, 51 bounded ZIP parts and
3,937,957,371 logical bytes. All member checksums, order,
offsets, sizes, complete original/restored file hashes and directory sets passed
before and after the complete independent restored audit. It launched no Native
processes or timers and changed no existing files. Only inventoried regenerable
build/Python caches are excluded; all originals remain. Closed raw logs are
byte-exact gzip supplements with both raw and encoded hashes. No complete
verified private GitHub backup or recent raw deletion is claimed.

Next engineering target: bounded sequential per-column read-ahead for long
streamed scans. Diagnostic108 attributes roughly5.5ms of8ms grouped wall to
page work,with0.21ms selection and2.2ms aggregation; its grouped timing controls
fail,so this supports a stage-cost hypothesis rather than a speed or causal
claim. The actual reader alternates seek/read calls per column and4096-row block.
New work requires a new number,predeclared controls,unchanged fallback/CRC,
bounded memory,and complete qualification before adoption. Older106/107 rejection
and108 diagnostic archives remain pending; every original and failure is safe.

See [complete reproduction](benchmarks/adaptive-speed-110/REPRODUCE.md),
[complete original audit](benchmarks/adaptive-speed-110/complete-audit-proof.json),
[restored audit](benchmarks/adaptive-speed-110/restored-audit-proof.json),
[all native results](benchmarks/adaptive-speed-110/native-audit.json) and
[decision and unstarted service specs](benchmarks/adaptive-speed-110/native-rejection-decision.json).
Borrowed receipt lookup follows [Rust's BTreeMap API](https://doc.rust-lang.org/std/collections/struct.BTreeMap.html#method.get);
that documentation supports the design, not a Kestrel speed claim.
