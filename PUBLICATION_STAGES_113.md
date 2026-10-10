# Publication-stage diagnostic 113

The unchanged trial 112 engine spends most measured publication-stage time in
its two durable flushes. **This diagnostic qualifies no engine improvement or
release.** Supported main remains 0.3.16; the isolated 0.3.17 candidate is unreleased.
Twenty of 144 baseline controls and twenty of 156 diagnostic guards fail.
No old rejection, release gate or raw measurement is reclassified.

The cohort contains 144 fixed D: cases: sparse and pressure ingestion, anonymous
and named batches, twelve rounds, A/A/C, all six orders balanced in full and both
halves. All 331,776 ACKs and 796,262,400 full CRC bytes independently pass complete
row multisets, indexes, receipt digests and original generations, current metadata,
SQLite cold SQL, quantiles and stage counts/histograms/max bounds. The sole timed
controller and independent audits actually exited zero. Every maximum and stall
is retained; there was no selected round, extra timing or numerical retry.

Both binaries use the same three common-driver edits: capture the seven existing
publication stages after the actual writer join and before releasing the initial
pin, and serialize the already computed cold SQL result. All engine/Cargo/lock/
test/runtime-feature bytes remain exact to 112. Exact inverses independently pass.
Four fresh driver test executions, two strict lints/two release binaries and eight
excluded correctness smokes pass. Trial 112's 772 core tests, five lints and 359
recovery commands are reused, not new 113 executions. Its original preflight API
return was unobserved; no shell exit is invented, while every native exit and
the unchanged independent audit passed.

## Where publication time goes

The following candidate medians are milliseconds across twelve complete cases.
Stage totals include compaction and final maintenance after the last ACK. Summed
stage medians can differ from the median of summed stages. Stage costs describe
aggregate elapsed work; they do not prove exclusive CPU, physical disk I/O or an
ACK-tail cause. Group sizes confound per-publication averages.

| Workload | ACKs/case | Durable groups | Final compactions | Prepare | Segment write | Segment sync | Catalog encode | Catalog write | Catalog sync | Rename | Total stages |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| sparse-anonymous | 512 | 512 | 15 | 16.104 | 97.101 | 354.865 | 2.561 | 99.834 | 307.413 | 139.243 | 1021.563 |
| sparse-named | 512 | 512 | 15 | 21.130 | 95.324 | 358.130 | 4.452 | 95.714 | 302.218 | 136.597 | 1014.803 |
| pressure-anonymous | 4,096 | 148 | 4 | 35.169 | 38.172 | 135.249 | 0.915 | 29.172 | 97.192 | 40.407 | 373.731 |
| pressure-named | 4,096 | 150 | 4 | 77.750 | 43.644 | 143.715 | 6.345 | 31.735 | 102.698 | 43.530 | 456.870 |

The two sync stages account for approximately 54–65% of measured stage cost.
Their per-ACK baseline controls pass in full and both halves for all four workloads.
This supports a separately declared experiment overlapping durable flushes while
requiring both successful actual joins before catalog rename or ACK. It does not
establish that overlap will improve this disk or fix every tail regression.
[Rust scoped threads](https://doc.rust-lang.org/std/thread/fn.scope.html) provide
bounded borrowed lifetimes and joins; [Builder::spawn_scoped](https://doc.rust-lang.org/std/thread/struct.Builder.html#method.spawn_scoped)
reports thread-creation errors. [File::sync_all](https://doc.rust-lang.org/std/fs/struct.File.html#method.sync_all)
remains required. [Microsoft's flush documentation](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)
supports investigating flush cost, not an observed Kestrel speed gain. Current Rust
documentation is 1.99.0; local builds use 1.97.1 and longstanding stable APIs.

The unchanged candidate still shows a full-cohort pressure-named p99 regression
of 21.52% with passing full A/A. Half 1 also regresses; half 2's baseline control
fails, so an all-scope p99 claim is inconclusive. Full pressure-named completion
is 5.27% slower with passing A/A. Every other failed control/guard follows below.

## Every before/after and diagnostic gate

ACK latency/completion units are milliseconds; stage units are milliseconds per
ACK; disk units are bytes. Within-round paired ratios need not equal quotients
of displayed medians. A/A requires 0.95–1.05; candidate guards require at most 1.05.
These are diagnostic gates, not replacement or loosened release gates.

| Scope | Workload | Metric | Unit | Baseline median | Candidate median | A/A | Control | C/A | Guard |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| full | sparse-anonymous | p50 | ms | 1.891800 | 1.899000 | 0.99958820 | pass | 0.99534242 | pass |
| full | sparse-anonymous | p95 | ms | 5.353000 | 5.237550 | 0.99356941 | pass | 0.96302722 | pass |
| full | sparse-anonymous | p99 | ms | 14.062200 | 13.479800 | 0.97733142 | pass | 1.00382750 | pass |
| full | sparse-anonymous | wall | ms | 1248.979700 | 1218.368600 | 0.98902727 | pass | 0.98851999 | pass |
| full | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass |
| full | sparse-anonymous | stage/prepare/ms_per_ACK | ms/ACK | 0.031123 | 0.031453 | 0.98847204 | pass | 1.01551625 | pass |
| full | sparse-anonymous | stage/segment_write/ms_per_ACK | ms/ACK | 0.193317 | 0.189650 | 0.97746385 | pass | 0.98826827 | pass |
| full | sparse-anonymous | stage/segment_sync/ms_per_ACK | ms/ACK | 0.720964 | 0.693096 | 0.99045879 | pass | 0.98036035 | pass |
| full | sparse-anonymous | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.005248 | 0.005003 | 0.98622181 | pass | 0.96181853 | pass |
| full | sparse-anonymous | stage/catalog_write/ms_per_ACK | ms/ACK | 0.192519 | 0.194988 | 1.03116134 | pass | 1.01281599 | pass |
| full | sparse-anonymous | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.615784 | 0.600416 | 0.98994116 | pass | 1.00277944 | pass |
| full | sparse-anonymous | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.279394 | 0.271959 | 0.97999945 | pass | 0.98619451 | pass |
| full | sparse-anonymous | stage/total/ms_per_ACK | ms/ACK | 2.063070 | 1.995239 | 0.99336007 | pass | 0.98649332 | pass |
| full | sparse-named | p50 | ms | 1.898500 | 1.859850 | 1.01295532 | pass | 0.99087757 | pass |
| full | sparse-named | p95 | ms | 5.655650 | 5.209300 | 0.95120532 | pass | 0.91936360 | pass |
| full | sparse-named | p99 | ms | 13.391650 | 13.116750 | 0.99953358 | pass | 0.98526766 | pass |
| full | sparse-named | wall | ms | 1248.308550 | 1202.483350 | 1.00580700 | pass | 0.98437852 | pass |
| full | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass |
| full | sparse-named | stage/prepare/ms_per_ACK | ms/ACK | 0.042834 | 0.041269 | 0.97530606 | pass | 0.96205099 | pass |
| full | sparse-named | stage/segment_write/ms_per_ACK | ms/ACK | 0.191010 | 0.186180 | 0.98037317 | pass | 0.98494913 | pass |
| full | sparse-named | stage/segment_sync/ms_per_ACK | ms/ACK | 0.721101 | 0.699472 | 0.99779518 | pass | 0.99031577 | pass |
| full | sparse-named | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.008813 | 0.008696 | 1.01293539 | pass | 0.98860972 | pass |
| full | sparse-named | stage/catalog_write/ms_per_ACK | ms/ACK | 0.192314 | 0.186941 | 0.98475734 | pass | 0.97865246 | pass |
| full | sparse-named | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.639979 | 0.590270 | 1.01459313 | pass | 0.96633189 | pass |
| full | sparse-named | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.273647 | 0.266791 | 0.98897371 | pass | 0.98000483 | pass |
| full | sparse-named | stage/total/ms_per_ACK | ms/ACK | 2.067747 | 1.982036 | 1.00200864 | pass | 0.98200111 | pass |
| full | pressure-anonymous | p50 | ms | 2.310400 | 2.309100 | 0.99913775 | pass | 1.00169863 | pass |
| full | pressure-anonymous | p95 | ms | 9.562150 | 10.644400 | 0.97238852 | pass | 0.98980684 | pass |
| full | pressure-anonymous | p99 | ms | 14.041350 | 14.491400 | 1.01700501 | pass | 1.04031982 | pass |
| full | pressure-anonymous | wall | ms | 432.629200 | 425.600800 | 0.97057915 | pass | 1.00509080 | pass |
| full | pressure-anonymous | disk | bytes | 11475566.000000 | 11479575.500000 | 1.00109615 | n/a | 1.00071892 | pass |
| full | pressure-anonymous | stage/prepare/ms_per_ACK | ms/ACK | 0.008656 | 0.008586 | 0.98329439 | pass | 1.00686884 | pass |
| full | pressure-anonymous | stage/segment_write/ms_per_ACK | ms/ACK | 0.009556 | 0.009319 | 1.01108028 | pass | 1.00317846 | pass |
| full | pressure-anonymous | stage/segment_sync/ms_per_ACK | ms/ACK | 0.033609 | 0.033020 | 1.00816313 | pass | 1.01302534 | pass |
| full | pressure-anonymous | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.000230 | 0.000223 | 1.08727403 | FAIL | 1.03141291 | pass |
| full | pressure-anonymous | stage/catalog_write/ms_per_ACK | ms/ACK | 0.007018 | 0.007122 | 0.98402250 | pass | 0.99466549 | pass |
| full | pressure-anonymous | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.023089 | 0.023728 | 0.98594324 | pass | 1.00016128 | pass |
| full | pressure-anonymous | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.009864 | 0.009865 | 0.99660571 | pass | 0.98215977 | pass |
| full | pressure-anonymous | stage/total/ms_per_ACK | ms/ACK | 0.092913 | 0.091243 | 0.98062252 | pass | 1.00511659 | pass |
| full | pressure-named | p50 | ms | 2.675350 | 2.675700 | 0.99747307 | pass | 1.00761530 | pass |
| full | pressure-named | p95 | ms | 9.007650 | 11.608600 | 1.03769788 | pass | 1.00318236 | pass |
| full | pressure-named | p99 | ms | 15.418250 | 19.771250 | 0.98794278 | pass | 1.21517899 | FAIL |
| full | pressure-named | wall | ms | 482.170450 | 517.130750 | 0.99350018 | pass | 1.05265365 | FAIL |
| full | pressure-named | disk | bytes | 12179989.000000 | 12183769.500000 | 0.99929059 | n/a | 1.00066795 | pass |
| full | pressure-named | stage/prepare/ms_per_ACK | ms/ACK | 0.018444 | 0.018982 | 0.99947520 | pass | 1.00952400 | pass |
| full | pressure-named | stage/segment_write/ms_per_ACK | ms/ACK | 0.009866 | 0.010655 | 1.01696031 | pass | 1.06834248 | FAIL |
| full | pressure-named | stage/segment_sync/ms_per_ACK | ms/ACK | 0.033640 | 0.035087 | 0.98898417 | pass | 1.06053404 | FAIL |
| full | pressure-named | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.001347 | 0.001549 | 0.99471497 | pass | 1.07505306 | FAIL |
| full | pressure-named | stage/catalog_write/ms_per_ACK | ms/ACK | 0.007572 | 0.007748 | 1.02921151 | pass | 1.03632806 | pass |
| full | pressure-named | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.023615 | 0.025073 | 0.97690816 | pass | 1.05949312 | FAIL |
| full | pressure-named | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.010390 | 0.010627 | 0.99752934 | pass | 1.03436029 | pass |
| full | pressure-named | stage/total/ms_per_ACK | ms/ACK | 0.104954 | 0.111540 | 1.00730922 | pass | 1.05334981 | FAIL |
| half_1 | sparse-anonymous | p50 | ms | 1.937050 | 1.936400 | 1.01414169 | pass | 1.00852088 | pass |
| half_1 | sparse-anonymous | p95 | ms | 5.327750 | 5.273350 | 1.00482598 | pass | 1.00103930 | pass |
| half_1 | sparse-anonymous | p99 | ms | 13.727500 | 14.203900 | 1.02141693 | pass | 1.02155813 | pass |
| half_1 | sparse-anonymous | wall | ms | 1255.630350 | 1237.632950 | 1.01007118 | pass | 1.01033400 | pass |
| half_1 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass |
| half_1 | sparse-anonymous | stage/prepare/ms_per_ACK | ms/ACK | 0.031905 | 0.032526 | 1.05858810 | FAIL | 1.02094524 | pass |
| half_1 | sparse-anonymous | stage/segment_write/ms_per_ACK | ms/ACK | 0.198993 | 0.198568 | 1.03336328 | pass | 0.99444100 | pass |
| half_1 | sparse-anonymous | stage/segment_sync/ms_per_ACK | ms/ACK | 0.720964 | 0.695347 | 0.96843398 | pass | 0.99363171 | pass |
| half_1 | sparse-anonymous | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.005227 | 0.005102 | 1.02977557 | pass | 0.96181853 | pass |
| half_1 | sparse-anonymous | stage/catalog_write/ms_per_ACK | ms/ACK | 0.195371 | 0.201214 | 1.03456522 | pass | 1.04358739 | pass |
| half_1 | sparse-anonymous | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.617882 | 0.608196 | 0.98093223 | pass | 1.01928626 | pass |
| half_1 | sparse-anonymous | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.277434 | 0.277726 | 1.02123834 | pass | 1.00303278 | pass |
| half_1 | sparse-anonymous | stage/total/ms_per_ACK | ms/ACK | 2.069393 | 2.030357 | 0.99884206 | pass | 1.01239990 | pass |
| half_1 | sparse-named | p50 | ms | 1.932600 | 1.849650 | 0.96654360 | pass | 0.97016212 | pass |
| half_1 | sparse-named | p95 | ms | 5.687900 | 5.183150 | 0.93394762 | FAIL | 0.90357484 | pass |
| half_1 | sparse-named | p99 | ms | 13.867200 | 13.116750 | 0.97545497 | pass | 0.95971183 | pass |
| half_1 | sparse-named | wall | ms | 1264.520450 | 1195.240600 | 0.97365043 | pass | 0.96528923 | pass |
| half_1 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass |
| half_1 | sparse-named | stage/prepare/ms_per_ACK | ms/ACK | 0.045416 | 0.041269 | 0.90877024 | FAIL | 0.92346603 | pass |
| half_1 | sparse-named | stage/segment_write/ms_per_ACK | ms/ACK | 0.200537 | 0.186180 | 0.93624046 | FAIL | 0.96409731 | pass |
| half_1 | sparse-named | stage/segment_sync/ms_per_ACK | ms/ACK | 0.720835 | 0.694462 | 0.97930474 | pass | 0.97985020 | pass |
| half_1 | sparse-named | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.009100 | 0.008678 | 0.93463150 | FAIL | 0.95330956 | pass |
| half_1 | sparse-named | stage/catalog_write/ms_per_ACK | ms/ACK | 0.200053 | 0.186941 | 0.93474081 | FAIL | 0.95022916 | pass |
| half_1 | sparse-named | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.626766 | 0.590270 | 0.98610137 | pass | 0.96633189 | pass |
| half_1 | sparse-named | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.285752 | 0.266791 | 0.93901656 | FAIL | 0.93253283 | pass |
| half_1 | sparse-named | stage/total/ms_per_ACK | ms/ACK | 2.078745 | 1.969191 | 0.96785217 | pass | 0.96604571 | pass |
| half_1 | pressure-anonymous | p50 | ms | 2.312900 | 2.293250 | 0.99422392 | pass | 1.00067577 | pass |
| half_1 | pressure-anonymous | p95 | ms | 9.092100 | 9.808550 | 1.22201244 | FAIL | 0.98980684 | pass |
| half_1 | pressure-anonymous | p99 | ms | 13.788100 | 16.517100 | 1.08264140 | FAIL | 1.05173730 | FAIL |
| half_1 | pressure-anonymous | wall | ms | 432.629200 | 428.203800 | 0.97057915 | pass | 1.01424202 | pass |
| half_1 | pressure-anonymous | disk | bytes | 11472334.000000 | 11482309.000000 | 1.00064708 | n/a | 1.00166240 | pass |
| half_1 | pressure-anonymous | stage/prepare/ms_per_ACK | ms/ACK | 0.008656 | 0.008567 | 0.98329439 | pass | 1.01077416 | pass |
| half_1 | pressure-anonymous | stage/segment_write/ms_per_ACK | ms/ACK | 0.009569 | 0.009294 | 0.99053423 | pass | 0.98824928 | pass |
| half_1 | pressure-anonymous | stage/segment_sync/ms_per_ACK | ms/ACK | 0.032787 | 0.033757 | 1.03199316 | pass | 1.04500143 | pass |
| half_1 | pressure-anonymous | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.000227 | 0.000235 | 0.93913236 | FAIL | 1.10522140 | FAIL |
| half_1 | pressure-anonymous | stage/catalog_write/ms_per_ACK | ms/ACK | 0.007018 | 0.006784 | 0.99178917 | pass | 0.99871481 | pass |
| half_1 | pressure-anonymous | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.023089 | 0.023095 | 0.97959063 | pass | 1.00016128 | pass |
| half_1 | pressure-anonymous | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.009864 | 0.009567 | 0.99210262 | pass | 0.99631393 | pass |
| half_1 | pressure-anonymous | stage/total/ms_per_ACK | ms/ACK | 0.092913 | 0.091915 | 0.98062252 | pass | 1.01256773 | pass |
| half_1 | pressure-named | p50 | ms | 2.723050 | 2.817800 | 1.00331434 | pass | 1.01946544 | pass |
| half_1 | pressure-named | p95 | ms | 8.404650 | 10.949300 | 1.12001400 | FAIL | 1.15356632 | FAIL |
| half_1 | pressure-named | p99 | ms | 14.803750 | 16.998950 | 1.02007131 | pass | 1.14624348 | FAIL |
| half_1 | pressure-named | wall | ms | 482.948600 | 500.757250 | 1.02169282 | pass | 1.04416307 | pass |
| half_1 | pressure-named | disk | bytes | 12176290.500000 | 12183769.500000 | 1.00032674 | n/a | 1.00168815 | pass |
| half_1 | pressure-named | stage/prepare/ms_per_ACK | ms/ACK | 0.018259 | 0.018850 | 1.02666234 | pass | 1.01807711 | pass |
| half_1 | pressure-named | stage/segment_write/ms_per_ACK | ms/ACK | 0.009851 | 0.010958 | 1.04514139 | pass | 1.08540964 | FAIL |
| half_1 | pressure-named | stage/segment_sync/ms_per_ACK | ms/ACK | 0.033122 | 0.033799 | 1.02039479 | pass | 1.02669724 | pass |
| half_1 | pressure-named | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.001384 | 0.001409 | 0.98336869 | pass | 1.01309877 | pass |
| half_1 | pressure-named | stage/catalog_write/ms_per_ACK | ms/ACK | 0.007561 | 0.007696 | 1.05137990 | FAIL | 1.03448460 | pass |
| half_1 | pressure-named | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.023473 | 0.025126 | 1.01645923 | pass | 1.08745048 | FAIL |
| half_1 | pressure-named | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.010436 | 0.010737 | 1.02924456 | pass | 1.04957399 | pass |
| half_1 | pressure-named | stage/total/ms_per_ACK | ms/ACK | 0.104303 | 0.108533 | 1.03495516 | pass | 1.04292905 | pass |
| half_2 | sparse-anonymous | p50 | ms | 1.883000 | 1.862500 | 0.99179310 | pass | 0.98852720 | pass |
| half_2 | sparse-anonymous | p95 | ms | 5.361800 | 5.051750 | 0.97840452 | pass | 0.93299381 | pass |
| half_2 | sparse-anonymous | p99 | ms | 14.062200 | 13.479800 | 0.94709181 | FAIL | 0.95876875 | pass |
| half_2 | sparse-anonymous | wall | ms | 1246.406600 | 1210.906850 | 0.98257380 | pass | 0.98595094 | pass |
| half_2 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass |
| half_2 | sparse-anonymous | stage/prepare/ms_per_ACK | ms/ACK | 0.031123 | 0.031453 | 0.97943458 | pass | 0.99813326 | pass |
| half_2 | sparse-anonymous | stage/segment_write/ms_per_ACK | ms/ACK | 0.193317 | 0.189212 | 0.96394783 | pass | 0.97361766 | pass |
| half_2 | sparse-anonymous | stage/segment_sync/ms_per_ACK | ms/ACK | 0.718420 | 0.693096 | 1.01889481 | pass | 0.96014038 | pass |
| half_2 | sparse-anonymous | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.005254 | 0.005003 | 0.95483533 | pass | 0.97113568 | pass |
| half_2 | sparse-anonymous | stage/catalog_write/ms_per_ACK | ms/ACK | 0.192519 | 0.192459 | 1.03116134 | pass | 0.98006842 | pass |
| half_2 | sparse-anonymous | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.607804 | 0.595952 | 1.00793439 | pass | 0.98395592 | pass |
| half_2 | sparse-anonymous | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.279394 | 0.271959 | 0.94811458 | FAIL | 0.96971826 | pass |
| half_2 | sparse-anonymous | stage/total/ms_per_ACK | ms/ACK | 2.047890 | 1.987464 | 0.99336007 | pass | 0.97265562 | pass |
| half_2 | sparse-named | p50 | ms | 1.876450 | 1.864850 | 1.01747028 | pass | 0.99087757 | pass |
| half_2 | sparse-named | p95 | ms | 5.634800 | 5.323500 | 0.98180278 | pass | 0.95761821 | pass |
| half_2 | sparse-named | p99 | ms | 13.123650 | 13.177900 | 1.00152533 | pass | 0.98948305 | pass |
| half_2 | sparse-named | wall | ms | 1248.308550 | 1223.002450 | 1.00826458 | pass | 0.98437852 | pass |
| half_2 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass |
| half_2 | sparse-named | stage/prepare/ms_per_ACK | ms/ACK | 0.041883 | 0.041497 | 1.00216270 | pass | 0.97058110 | pass |
| half_2 | sparse-named | stage/segment_write/ms_per_ACK | ms/ACK | 0.186761 | 0.187040 | 0.99670137 | pass | 0.98567328 | pass |
| half_2 | sparse-named | stage/segment_sync/ms_per_ACK | ms/ACK | 0.725541 | 0.705984 | 0.99779518 | pass | 0.99031577 | pass |
| half_2 | sparse-named | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.008753 | 0.008726 | 1.03855760 | pass | 0.99064343 | pass |
| half_2 | sparse-named | stage/catalog_write/ms_per_ACK | ms/ACK | 0.186633 | 0.187373 | 1.00048802 | pass | 0.99267217 | pass |
| half_2 | sparse-named | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.644111 | 0.597335 | 1.01459313 | pass | 0.96774060 | pass |
| half_2 | sparse-named | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.267103 | 0.265826 | 1.01044823 | pass | 0.98970457 | pass |
| half_2 | sparse-named | stage/total/ms_per_ACK | ms/ACK | 2.067747 | 2.018107 | 1.00542657 | pass | 0.98200111 | pass |
| half_2 | pressure-anonymous | p50 | ms | 2.305650 | 2.359300 | 0.99972881 | pass | 1.01038315 | pass |
| half_2 | pressure-anonymous | p95 | ms | 11.048150 | 10.988050 | 0.89140882 | FAIL | 0.95232572 | pass |
| half_2 | pressure-anonymous | p99 | ms | 15.325850 | 14.424550 | 0.99920598 | pass | 1.02130550 | pass |
| half_2 | pressure-anonymous | wall | ms | 432.516350 | 425.600800 | 0.97816097 | pass | 0.99631967 | pass |
| half_2 | pressure-anonymous | disk | bytes | 11484683.000000 | 11479426.000000 | 1.00121259 | n/a | 0.99987901 | pass |
| half_2 | pressure-anonymous | stage/prepare/ms_per_ACK | ms/ACK | 0.008648 | 0.008595 | 0.99643372 | pass | 0.98770057 | pass |
| half_2 | pressure-anonymous | stage/segment_write/ms_per_ACK | ms/ACK | 0.009314 | 0.009645 | 1.04933389 | pass | 1.01432919 | pass |
| half_2 | pressure-anonymous | stage/segment_sync/ms_per_ACK | ms/ACK | 0.034597 | 0.032613 | 0.97698765 | pass | 0.95380596 | pass |
| half_2 | pressure-anonymous | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.000233 | 0.000220 | 1.13447953 | FAIL | 0.93861615 | pass |
| half_2 | pressure-anonymous | stage/catalog_write/ms_per_ACK | ms/ACK | 0.007122 | 0.007579 | 0.94758273 | FAIL | 0.99466549 | pass |
| half_2 | pressure-anonymous | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.023330 | 0.024029 | 0.99734023 | pass | 1.01766090 | pass |
| half_2 | pressure-anonymous | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.009984 | 0.010047 | 0.99660571 | pass | 0.98215977 | pass |
| half_2 | pressure-anonymous | stage/total/ms_per_ACK | ms/ACK | 0.093139 | 0.091243 | 0.97523427 | pass | 0.99648715 | pass |
| half_2 | pressure-named | p50 | ms | 2.660650 | 2.662200 | 0.98222105 | pass | 1.00256699 | pass |
| half_2 | pressure-named | p95 | ms | 11.574350 | 11.716300 | 0.86126460 | FAIL | 0.99776071 | pass |
| half_2 | pressure-named | p99 | ms | 17.237600 | 23.660450 | 0.90091401 | FAIL | 1.29953789 | FAIL |
| half_2 | pressure-named | wall | ms | 481.387350 | 541.845500 | 0.97767673 | pass | 1.07020507 | FAIL |
| half_2 | pressure-named | disk | bytes | 12194827.000000 | 12182201.500000 | 0.99748381 | n/a | 0.99992901 | pass |
| half_2 | pressure-named | stage/prepare/ms_per_ACK | ms/ACK | 0.018679 | 0.018982 | 0.98427598 | pass | 0.99963975 | pass |
| half_2 | pressure-named | stage/segment_write/ms_per_ACK | ms/ACK | 0.009997 | 0.010655 | 1.00740873 | pass | 1.06045185 | FAIL |
| half_2 | pressure-named | stage/segment_sync/ms_per_ACK | ms/ACK | 0.034508 | 0.040123 | 0.96707508 | pass | 1.08575650 | FAIL |
| half_2 | pressure-named | stage/catalog_encode/ms_per_ACK | ms/ACK | 0.001328 | 0.001650 | 1.01427457 | pass | 1.23320311 | FAIL |
| half_2 | pressure-named | stage/catalog_write/ms_per_ACK | ms/ACK | 0.007612 | 0.007884 | 1.00851789 | pass | 1.05727750 | FAIL |
| half_2 | pressure-named | stage/catalog_sync/ms_per_ACK | ms/ACK | 0.023615 | 0.024947 | 0.95044811 | pass | 1.04211189 | pass |
| half_2 | pressure-named | stage/catalog_rename/ms_per_ACK | ms/ACK | 0.010390 | 0.010627 | 0.98734101 | pass | 1.01762681 | pass |
| half_2 | pressure-named | stage/total/ms_per_ACK | ms/ACK | 0.106726 | 0.115975 | 0.96418582 | pass | 1.05777684 | FAIL |

## Exact preservation

12,662 files, 180 directories,
13 bounded ZIP parts and 1,010,319,996 logical
bytes pass every member CRC/order/offset/size and exact original/restored file
hash and directory set before and after a complete independent restored pure
audit. No native processes, timers or existing-file writes were used in replay.
All originals and failed/unexecuted drafts remain; only inventoried regenerable
build/Python caches are excluded. Closed raw logs are byte-exact gzip supplements.

The full parent 324 Native/252 service cases and all 42 release goals remain
required. All 252 service cases are unstarted and untested. No supported upgrade,
competitor ranking, universal benchmark win, release ETA, Native CPU/RSS, physical
power-loss guarantee, complete private GitHub raw backup or recent deletion is
claimed. See [reproduction instructions](benchmarks/publication-stages-113/REPRODUCE.md)
and [complete raw audit](benchmarks/publication-stages-113/complete-audit-proof.json).
