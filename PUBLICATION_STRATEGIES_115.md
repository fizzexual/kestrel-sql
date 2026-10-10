# Publication strategies diagnostic 115

Concurrent durable flushing modestly reduces completion time compared with
serial flushing, but does not consistently protect pressure tails. **This
diagnostic qualifies no release or adoption.** Supported main stays 0.3.16;
isolated 0.3.17 remains unreleased. Twelve of 144 A/A controls and 39 of 156
diagnostic guards fail. Both previous rejections and all release gates remain.

This comparison uses experimental serial trial 112 for both A/A baselines,
and experimental concurrent trial 114 as C. All three variants are package
0.3.17, compiled with benchmark-shutdown,adaptive-engine and runtime adaptive=1.
Supported 0.3.16 is **not** the timed comparator. Every engine/Cargo/lock/test
byte is unchanged from its respective parent. The same three common-driver
edits capture existing publication stages after actual writer join/before
the original pin is released, and serialize the existing cold SQL answer
after timing. Exact driver byte and harness text inverses independently pass.

Four fresh common-driver test executions, two strict lints/two release binaries,
eight excluded smokes, four invalid order/stage fixtures and a complete frozen
input prefix pass. Serial 112's 772 and concurrent 114's 796 core tests, five
lints and 359 recovery commands each are reused, not fresh 115 executions.
Current 115 build/Native/audit actual API exits are observed zero; the old
112 unobserved preflight API return is not reclassified. Both experimental
parents' complete 324 Native/252 service/all 42 goal requirements and failures
remain unchanged. Every 252 service case is unstarted and untested.

All 144 fixed D: cases ran once: four sparse/pressure anonymous/named modes,
twelve rounds, all six A/A/C orders balanced in full and both halves. All
331,776 ACKs and 796,262,400 CRC bytes independently pass complete rows,
indexes, original receipt generations/digests, current metadata, cold SQLite
SQL, raw quantiles and post-join stage counts/histograms/max bounds. Every
raw maximum and stall remains. No selected scope, extra timing, numerical
retry or changed control occurred.

## Direct latency/completion comparison

The four completion improvements have A/A passing and C/A below 1 in full
and both halves. Pressure-anonymous p99 instead regresses 6.61% in half 1
with passing A/A (0.99595612), while full and half 2 remain within the 5%
guard. This prevents a claim that concurrency consistently improves tails.
The full pressure-anonymous p95 comparison is control-inconclusive.
Percentages below use full within-round paired ratios, not median quotients.

| Workload | Serial112 completion median (ms) | Concurrent114 completion median (ms) | Paired reduction | Full A/A | Controls pass full/both halves |
| --- | ---: | ---: | ---: | ---: | --- |
| sparse-anonymous | 1199.818200 | 1157.964700 | 4.45% | 1.01418100 | pass |
| sparse-named | 1199.337850 | 1187.751850 | 1.55% | 1.00920100 | pass |
| pressure-anonymous | 419.787050 | 407.130800 | 2.13% | 1.00525612 | pass |
| pressure-named | 496.916950 | 477.589750 | 3.16% | 0.98211887 | pass |

The internal stage regressions are retained below. Concurrent sync durations
overlap: their sum describes aggregate elapsed stage cost, not sequential
publication wall time, physical disk I/O, exclusive CPU or an ACK-tail cause.
Totals include final compaction/maintenance. These results support testing a
workload-dependent selector in a new experiment; they do not establish which
runtime condition safely selects the strategy or qualify a supported upgrade.

## Every before/after and diagnostic gate

ACK/completion units are milliseconds; stages use milliseconds per ACK; disk
uses bytes. A/A requires 0.95–1.05 and candidate guards require at most 1.05.
Both full and half scopes remain required. No release goals are replaced by
these diagnostic guards. Every one of the 156 comparisons follows.

| Scope | Workload | Metric | Unit | Serial112 baseline median | Concurrent114 candidate median | A/A | Control | C/A | Guard |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| full | sparse-anonymous | p50 | ms | 1.849400 | 1.793600 | 0.98797133 | pass | 0.96475986 | pass |
| full | sparse-anonymous | p95 | ms | 5.120600 | 5.019650 | 1.00245526 | pass | 0.96294999 | pass |
| full | sparse-anonymous | p99 | ms | 13.351200 | 13.251100 | 0.99264822 | pass | 0.98820330 | pass |
| full | sparse-anonymous | wall | ms | 1199.818200 | 1157.964700 | 1.01418100 | pass | 0.95553924 | pass |
| full | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass |
| full | sparse-anonymous | stage/prepare/ms_per_ACK | ms/ACK | 0.031407 | 0.031115 | 0.97783998 | pass | 0.98347052 | pass |
| full | sparse-anonymous | stage/segment_write/ms_per_ACK | ms/ACK | 0.187975 | 0.190733 | 0.98344407 | pass | 0.99890157 | pass |
| full | sparse-anonymous | stage/segment_sync/ms_per_ACK | ms/ACK | 0.688510 | 0.740082 | 1.01238144 | pass | 1.08161326 | FAIL |
| full | sparse-anonymous | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.005089 | 0.004085 | 0.97236156 | pass | 0.79194439 | pass |
| full | sparse-anonymous | stage/catalog_write/ms_per_ACK | ms/ACK | 0.185675 | 0.176543 | 0.99208504 | pass | 0.93710958 | pass |
| full | sparse-anonymous | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.596818 | 1.090424 | 1.01522514 | pass | 1.84802966 | FAIL |
| full | sparse-anonymous | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.265227 | 0.272232 | 0.99100866 | pass | 1.00904752 | pass |
| full | sparse-anonymous | stage/total/ms_per_ACK | ms/ACK | 1.962289 | 2.500636 | 1.00438280 | pass | 1.27295041 | FAIL |
| full | sparse-named | p50 | ms | 1.863250 | 1.824500 | 0.99388903 | pass | 0.97043619 | pass |
| full | sparse-named | p95 | ms | 5.130100 | 4.931250 | 1.00687604 | pass | 0.95143744 | pass |
| full | sparse-named | p99 | ms | 12.990050 | 13.143400 | 1.01056881 | pass | 0.99887763 | pass |
| full | sparse-named | wall | ms | 1199.337850 | 1187.751850 | 1.00920100 | pass | 0.98449985 | pass |
| full | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass |
| full | sparse-named | stage/prepare/ms_per_ACK | ms/ACK | 0.041684 | 0.041560 | 0.99513048 | pass | 0.98636356 | pass |
| full | sparse-named | stage/segment_write/ms_per_ACK | ms/ACK | 0.184976 | 0.191787 | 1.00518973 | pass | 1.02262089 | pass |
| full | sparse-named | stage/segment_sync/ms_per_ACK | ms/ACK | 0.686045 | 0.750226 | 0.99913461 | pass | 1.08478722 | FAIL |
| full | sparse-named | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.008895 | 0.007674 | 0.96739024 | pass | 0.85201309 | pass |
| full | sparse-named | stage/catalog_write/ms_per_ACK | ms/ACK | 0.187570 | 0.179630 | 1.00050685 | pass | 0.94548902 | pass |
| full | sparse-named | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.605633 | 1.096310 | 0.98330171 | pass | 1.82240491 | FAIL |
| full | sparse-named | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.268139 | 0.273628 | 0.98747060 | pass | 1.00656596 | pass |
| full | sparse-named | stage/total/ms_per_ACK | ms/ACK | 1.976364 | 2.556573 | 1.00750717 | pass | 1.28384508 | FAIL |
| full | pressure-anonymous | p50 | ms | 2.292800 | 2.257600 | 0.99747963 | pass | 0.98157021 | pass |
| full | pressure-anonymous | p95 | ms | 8.499750 | 10.119850 | 1.27007701 | FAIL | 0.99454304 | pass |
| full | pressure-anonymous | p99 | ms | 13.851150 | 14.037700 | 1.00149022 | pass | 1.01259234 | pass |
| full | pressure-anonymous | wall | ms | 419.787050 | 407.130800 | 1.00525612 | pass | 0.97870280 | pass |
| full | pressure-anonymous | disk | bytes | 11460611.000000 | 11470326.500000 | 1.00245904 | n/a | 1.00064475 | pass |
| full | pressure-anonymous | stage/prepare/ms_per_ACK | ms/ACK | 0.008357 | 0.008349 | 1.01055493 | pass | 1.00342502 | pass |
| full | pressure-anonymous | stage/segment_write/ms_per_ACK | ms/ACK | 0.009292 | 0.009183 | 0.99417425 | pass | 0.98133194 | pass |
| full | pressure-anonymous | stage/segment_sync/ms_per_ACK | ms/ACK | 0.033246 | 0.038137 | 1.02251969 | pass | 1.15035059 | FAIL |
| full | pressure-anonymous | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.000224 | 0.000145 | 0.98510769 | pass | 0.66986197 | pass |
| full | pressure-anonymous | stage/catalog_write/ms_per_ACK | ms/ACK | 0.006850 | 0.006345 | 1.00428305 | pass | 0.90625524 | pass |
| full | pressure-anonymous | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.022242 | 0.046003 | 0.99949778 | pass | 2.03314292 | FAIL |
| full | pressure-anonymous | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.009666 | 0.009743 | 1.02429396 | pass | 1.00348720 | pass |
| full | pressure-anonymous | stage/total/ms_per_ACK | ms/ACK | 0.089866 | 0.117770 | 1.00699209 | pass | 1.31054113 | FAIL |
| full | pressure-named | p50 | ms | 2.703100 | 2.600250 | 0.99243100 | pass | 0.98711443 | pass |
| full | pressure-named | p95 | ms | 11.680750 | 11.693850 | 0.95000770 | pass | 0.98035589 | pass |
| full | pressure-named | p99 | ms | 16.555050 | 16.573700 | 0.95577039 | pass | 0.98624614 | pass |
| full | pressure-named | wall | ms | 496.916950 | 477.589750 | 0.98211887 | pass | 0.96835317 | pass |
| full | pressure-named | disk | bytes | 12177163.500000 | 12161580.000000 | 0.99887801 | n/a | 0.99867616 | pass |
| full | pressure-named | stage/prepare/ms_per_ACK | ms/ACK | 0.018291 | 0.018101 | 0.99244945 | pass | 0.98965764 | pass |
| full | pressure-named | stage/segment_write/ms_per_ACK | ms/ACK | 0.010124 | 0.010300 | 0.99362177 | pass | 0.99397779 | pass |
| full | pressure-named | stage/segment_sync/ms_per_ACK | ms/ACK | 0.035034 | 0.040681 | 0.94613001 | FAIL | 1.21783972 | FAIL |
| full | pressure-named | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.001433 | 0.001348 | 0.99236686 | pass | 0.93587829 | pass |
| full | pressure-named | stage/catalog_write/ms_per_ACK | ms/ACK | 0.007779 | 0.007006 | 0.99067553 | pass | 0.91863745 | pass |
| full | pressure-named | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.024618 | 0.047776 | 0.97018401 | pass | 1.93424774 | FAIL |
| full | pressure-named | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.010471 | 0.010555 | 0.99250425 | pass | 1.01639899 | pass |
| full | pressure-named | stage/total/ms_per_ACK | ms/ACK | 0.107636 | 0.135747 | 0.97017645 | pass | 1.25325330 | FAIL |
| half_1 | sparse-anonymous | p50 | ms | 1.837700 | 1.792600 | 1.00995143 | pass | 0.96850909 | pass |
| half_1 | sparse-anonymous | p95 | ms | 5.067100 | 5.019650 | 1.03473000 | pass | 0.96294999 | pass |
| half_1 | sparse-anonymous | p99 | ms | 13.255850 | 13.199950 | 1.00292345 | pass | 0.98997843 | pass |
| half_1 | sparse-anonymous | wall | ms | 1199.818200 | 1147.051800 | 1.02083184 | pass | 0.95553924 | pass |
| half_1 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass |
| half_1 | sparse-anonymous | stage/prepare/ms_per_ACK | ms/ACK | 0.030458 | 0.030724 | 0.99693421 | pass | 0.98839530 | pass |
| half_1 | sparse-anonymous | stage/segment_write/ms_per_ACK | ms/ACK | 0.187975 | 0.189802 | 1.02485821 | pass | 0.99890157 | pass |
| half_1 | sparse-anonymous | stage/segment_sync/ms_per_ACK | ms/ACK | 0.687590 | 0.725319 | 1.01822993 | pass | 1.08161326 | FAIL |
| half_1 | sparse-anonymous | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.004935 | 0.004083 | 1.00681181 | pass | 0.80129030 | pass |
| half_1 | sparse-anonymous | stage/catalog_write/ms_per_ACK | ms/ACK | 0.185634 | 0.176267 | 1.00671587 | pass | 0.93710958 | pass |
| half_1 | sparse-anonymous | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.593521 | 1.090424 | 1.01724837 | pass | 1.82137176 | FAIL |
| half_1 | sparse-anonymous | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.265227 | 0.271826 | 1.00438078 | pass | 1.01020149 | pass |
| half_1 | sparse-anonymous | stage/total/ms_per_ACK | ms/ACK | 1.961542 | 2.472679 | 1.02102730 | pass | 1.26742568 | FAIL |
| half_1 | sparse-named | p50 | ms | 1.888000 | 1.829000 | 0.98709294 | pass | 0.97043619 | pass |
| half_1 | sparse-named | p95 | ms | 5.350750 | 5.085600 | 0.93746065 | FAIL | 0.94064452 | pass |
| half_1 | sparse-named | p99 | ms | 13.248750 | 13.286250 | 1.00846294 | pass | 1.00588205 | pass |
| half_1 | sparse-named | wall | ms | 1216.369050 | 1189.249200 | 0.98619111 | pass | 0.97566201 | pass |
| half_1 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass |
| half_1 | sparse-named | stage/prepare/ms_per_ACK | ms/ACK | 0.042963 | 0.041505 | 0.98414077 | pass | 0.95555854 | pass |
| half_1 | sparse-named | stage/segment_write/ms_per_ACK | ms/ACK | 0.188047 | 0.189571 | 1.00184860 | pass | 1.00661853 | pass |
| half_1 | sparse-named | stage/segment_sync/ms_per_ACK | ms/ACK | 0.696784 | 0.750002 | 0.98802192 | pass | 1.07741411 | FAIL |
| half_1 | sparse-named | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.009055 | 0.007674 | 0.95371198 | pass | 0.84919508 | pass |
| half_1 | sparse-named | stage/catalog_write/ms_per_ACK | ms/ACK | 0.187570 | 0.179578 | 0.99604413 | pass | 0.93565897 | pass |
| half_1 | sparse-named | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.608276 | 1.106143 | 0.97558968 | pass | 1.78592294 | FAIL |
| half_1 | sparse-named | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.270398 | 0.273438 | 0.98318369 | pass | 1.00505686 | pass |
| half_1 | sparse-named | stage/total/ms_per_ACK | ms/ACK | 2.004890 | 2.558649 | 0.98462308 | pass | 1.27407772 | FAIL |
| half_1 | pressure-anonymous | p50 | ms | 2.320950 | 2.323900 | 0.98922374 | pass | 0.98949986 | pass |
| half_1 | pressure-anonymous | p95 | ms | 6.602400 | 10.007000 | 1.34586159 | FAIL | 1.57393390 | FAIL |
| half_1 | pressure-anonymous | p99 | ms | 13.851150 | 14.611900 | 0.99595612 | pass | 1.06612065 | FAIL |
| half_1 | pressure-anonymous | wall | ms | 417.174150 | 418.427100 | 1.01026115 | pass | 0.98662863 | pass |
| half_1 | pressure-anonymous | disk | bytes | 11470300.500000 | 11483019.000000 | 1.00375675 | n/a | 1.00064475 | pass |
| half_1 | pressure-anonymous | stage/prepare/ms_per_ACK | ms/ACK | 0.008357 | 0.008340 | 1.00754602 | pass | 1.00342502 | pass |
| half_1 | pressure-anonymous | stage/segment_write/ms_per_ACK | ms/ACK | 0.009316 | 0.009457 | 0.98209522 | pass | 1.02595816 | pass |
| half_1 | pressure-anonymous | stage/segment_sync/ms_per_ACK | ms/ACK | 0.032475 | 0.039221 | 1.02450607 | pass | 1.17741329 | FAIL |
| half_1 | pressure-anonymous | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.000241 | 0.000151 | 0.94983621 | FAIL | 0.67481995 | pass |
| half_1 | pressure-anonymous | stage/catalog_write/ms_per_ACK | ms/ACK | 0.006826 | 0.006437 | 0.99418523 | pass | 0.93696663 | pass |
| half_1 | pressure-anonymous | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.022225 | 0.046481 | 1.01796386 | pass | 2.04920311 | FAIL |
| half_1 | pressure-anonymous | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.009626 | 0.010298 | 0.98620156 | pass | 1.07028286 | FAIL |
| half_1 | pressure-anonymous | stage/total/ms_per_ACK | ms/ACK | 0.088990 | 0.120277 | 1.01752333 | pass | 1.33397721 | FAIL |
| half_1 | pressure-named | p50 | ms | 2.654950 | 2.589100 | 1.00358010 | pass | 0.98270674 | pass |
| half_1 | pressure-named | p95 | ms | 11.680750 | 9.841350 | 0.97322490 | pass | 0.83407907 | pass |
| half_1 | pressure-named | p99 | ms | 17.721850 | 16.306900 | 0.85298410 | FAIL | 0.98993486 | pass |
| half_1 | pressure-named | wall | ms | 485.066100 | 468.824750 | 0.98211887 | pass | 0.96835317 | pass |
| half_1 | pressure-named | disk | bytes | 12189719.500000 | 12157326.500000 | 0.99887801 | n/a | 0.99865202 | pass |
| half_1 | pressure-named | stage/prepare/ms_per_ACK | ms/ACK | 0.018226 | 0.018101 | 0.99405952 | pass | 0.99510681 | pass |
| half_1 | pressure-named | stage/segment_write/ms_per_ACK | ms/ACK | 0.010124 | 0.010321 | 0.98108416 | pass | 1.01401130 | pass |
| half_1 | pressure-named | stage/segment_sync/ms_per_ACK | ms/ACK | 0.034298 | 0.039974 | 0.93604324 | FAIL | 1.18001009 | FAIL |
| half_1 | pressure-named | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.001399 | 0.001355 | 0.99839845 | pass | 0.96356833 | pass |
| half_1 | pressure-named | stage/catalog_write/ms_per_ACK | ms/ACK | 0.007742 | 0.007190 | 0.99122826 | pass | 0.93335002 | pass |
| half_1 | pressure-named | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.024109 | 0.045873 | 0.97018401 | pass | 1.87873501 | FAIL |
| half_1 | pressure-named | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.010460 | 0.010537 | 0.99558425 | pass | 1.03629652 | pass |
| half_1 | pressure-named | stage/total/ms_per_ACK | ms/ACK | 0.105459 | 0.132554 | 0.97017645 | pass | 1.25325330 | FAIL |
| half_2 | sparse-anonymous | p50 | ms | 1.856900 | 1.795900 | 0.98648162 | pass | 0.96260770 | pass |
| half_2 | sparse-anonymous | p95 | ms | 5.238500 | 4.973200 | 0.97823980 | pass | 0.97980810 | pass |
| half_2 | sparse-anonymous | p99 | ms | 13.813800 | 13.355950 | 0.97559109 | pass | 0.96838939 | pass |
| half_2 | sparse-anonymous | wall | ms | 1214.908500 | 1164.927250 | 0.99557764 | pass | 0.95769271 | pass |
| half_2 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass |
| half_2 | sparse-anonymous | stage/prepare/ms_per_ACK | ms/ACK | 0.032403 | 0.031115 | 0.96145514 | pass | 0.97966446 | pass |
| half_2 | sparse-anonymous | stage/segment_write/ms_per_ACK | ms/ACK | 0.191154 | 0.190807 | 0.97374192 | pass | 0.99697609 | pass |
| half_2 | sparse-anonymous | stage/segment_sync/ms_per_ACK | ms/ACK | 0.688581 | 0.751371 | 0.99652024 | pass | 1.08865546 | FAIL |
| half_2 | sparse-anonymous | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.005333 | 0.004085 | 0.92925752 | FAIL | 0.76779831 | pass |
| half_2 | sparse-anonymous | stage/catalog_write/ms_per_ACK | ms/ACK | 0.190332 | 0.176572 | 0.97238473 | pass | 0.92869622 | pass |
| half_2 | sparse-anonymous | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.603199 | 1.096163 | 1.01522514 | pass | 1.85068090 | FAIL |
| half_2 | sparse-anonymous | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.272834 | 0.272232 | 0.98027643 | pass | 0.99283746 | pass |
| half_2 | sparse-anonymous | stage/total/ms_per_ACK | ms/ACK | 1.988295 | 2.525295 | 0.98479943 | pass | 1.28506977 | FAIL |
| half_2 | sparse-named | p50 | ms | 1.863250 | 1.824500 | 0.99437441 | pass | 0.97558335 | pass |
| half_2 | sparse-named | p95 | ms | 5.081350 | 4.893000 | 1.06159571 | FAIL | 0.95143744 | pass |
| half_2 | sparse-named | p99 | ms | 12.990050 | 12.998350 | 1.01056881 | pass | 0.99271394 | pass |
| half_2 | sparse-named | wall | ms | 1194.759000 | 1183.302900 | 1.02540217 | pass | 0.99196737 | pass |
| half_2 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass |
| half_2 | sparse-named | stage/prepare/ms_per_ACK | ms/ACK | 0.041295 | 0.041745 | 1.00151603 | pass | 1.01346117 | pass |
| half_2 | sparse-named | stage/segment_write/ms_per_ACK | ms/ACK | 0.183579 | 0.194613 | 1.00518973 | pass | 1.04397218 | pass |
| half_2 | sparse-named | stage/segment_sync/ms_per_ACK | ms/ACK | 0.683043 | 0.756618 | 1.02002191 | pass | 1.10190286 | FAIL |
| half_2 | sparse-named | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.008815 | 0.007667 | 0.99332597 | pass | 0.85876752 | pass |
| half_2 | sparse-named | stage/catalog_write/ms_per_ACK | ms/ACK | 0.187298 | 0.179742 | 1.00359333 | pass | 0.96000034 | pass |
| half_2 | sparse-named | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.596669 | 1.094259 | 1.04238783 | pass | 1.85130228 | FAIL |
| half_2 | sparse-named | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.266708 | 0.273628 | 0.98747060 | pass | 1.02166394 | pass |
| half_2 | sparse-named | stage/total/ms_per_ACK | ms/ACK | 1.964553 | 2.556573 | 1.02400383 | pass | 1.30284399 | FAIL |
| half_2 | pressure-anonymous | p50 | ms | 2.292050 | 2.247150 | 1.00533521 | pass | 0.97455596 | pass |
| half_2 | pressure-anonymous | p95 | ms | 9.878800 | 10.633600 | 1.14846312 | FAIL | 0.87712263 | pass |
| half_2 | pressure-anonymous | p99 | ms | 14.191350 | 14.021150 | 1.02856959 | pass | 0.97653286 | pass |
| half_2 | pressure-anonymous | wall | ms | 424.037750 | 403.416100 | 1.00372215 | pass | 0.95512246 | pass |
| half_2 | pressure-anonymous | disk | bytes | 11459849.000000 | 11460553.000000 | 1.00152841 | n/a | 1.00043030 | pass |
| half_2 | pressure-anonymous | stage/prepare/ms_per_ACK | ms/ACK | 0.008357 | 0.008349 | 1.01055493 | pass | 1.00039851 | pass |
| half_2 | pressure-anonymous | stage/segment_write/ms_per_ACK | ms/ACK | 0.009240 | 0.009011 | 1.01149777 | pass | 0.96440247 | pass |
| half_2 | pressure-anonymous | stage/segment_sync/ms_per_ACK | ms/ACK | 0.033495 | 0.036995 | 1.00314354 | pass | 1.10042484 | FAIL |
| half_2 | pressure-anonymous | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.000218 | 0.000142 | 1.09785420 | FAIL | 0.65166949 | pass |
| half_2 | pressure-anonymous | stage/catalog_write/ms_per_ACK | ms/ACK | 0.006857 | 0.006158 | 1.01555938 | pass | 0.88424204 | pass |
| half_2 | pressure-anonymous | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.022781 | 0.045179 | 0.95163365 | pass | 2.02046964 | FAIL |
| half_2 | pressure-anonymous | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.009666 | 0.009590 | 1.03152836 | pass | 0.99102688 | pass |
| half_2 | pressure-anonymous | stage/total/ms_per_ACK | ms/ACK | 0.090993 | 0.116010 | 1.00159782 | pass | 1.28572496 | FAIL |
| half_2 | pressure-named | p50 | ms | 2.777900 | 2.668250 | 0.97289628 | pass | 0.99059553 | pass |
| half_2 | pressure-named | p95 | ms | 11.286050 | 11.782600 | 0.82764891 | FAIL | 1.02998241 | pass |
| half_2 | pressure-named | p99 | ms | 16.555050 | 16.573700 | 0.97938751 | pass | 0.95739757 | pass |
| half_2 | pressure-named | wall | ms | 507.363800 | 481.107250 | 0.98370913 | pass | 0.96731082 | pass |
| half_2 | pressure-named | disk | bytes | 12177085.000000 | 12161580.000000 | 0.99892497 | n/a | 0.99867616 | pass |
| half_2 | pressure-named | stage/prepare/ms_per_ACK | ms/ACK | 0.018729 | 0.018192 | 0.97808795 | pass | 0.97581524 | pass |
| half_2 | pressure-named | stage/segment_write/ms_per_ACK | ms/ACK | 0.010152 | 0.010218 | 0.99414972 | pass | 0.98813140 | pass |
| half_2 | pressure-named | stage/segment_sync/ms_per_ACK | ms/ACK | 0.035596 | 0.040700 | 0.96466591 | pass | 1.28354697 | FAIL |
| half_2 | pressure-named | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.001469 | 0.001346 | 0.95961728 | pass | 0.92240439 | pass |
| half_2 | pressure-named | stage/catalog_write/ms_per_ACK | ms/ACK | 0.007843 | 0.006890 | 0.99067553 | pass | 0.88664238 | pass |
| half_2 | pressure-named | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.024618 | 0.049095 | 0.97867897 | pass | 1.94264111 | FAIL |
| half_2 | pressure-named | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.010471 | 0.010555 | 0.98325965 | pass | 1.00923613 | pass |
| half_2 | pressure-named | stage/total/ms_per_ACK | ms/ACK | 0.109779 | 0.136709 | 0.98472145 | pass | 1.27158015 | FAIL |

## Exact preservation

12,559 files, 180 directories,
13 bounded ZIP parts and 1,003,680,083
logical bytes pass every member CRC/order/offset/size and exact original/restored
file hash and directory set before and after complete pure replay. The restored
audit reproduces all source/fresh-driver/reused-parent/smoke/raw/quantile/stage
and full/half control/guard values exactly, with no Native, timer or existing
file write. All originals and failures remain. Only inventoried regenerable
build/Python caches are excluded. Closed logs are byte-exact gzip supplements.

No complete recent private remote backup, recent deletion, supported upgrade,
reliable release ETA, fresh competitor ranking, universal benchmark win,
Native CPU/RSS or physical power-loss guarantee is claimed. See
[reproduction](benchmarks/publication-strategies-115/REPRODUCE.md) and
[complete audit](benchmarks/publication-strategies-115/complete-audit-proof.json).
