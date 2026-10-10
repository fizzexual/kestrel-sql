# Byte-buffered receipt hashing trial 117

The combined experimental candidate improves identified-replay p99 against
supported 0.3.16, but fails full release qualification. **0.3.17 remains
unqualified and unreleased; supported main remains byte-exact 0.3.16.**
All 324 cases are correct. Performance fails 15 of 153 A/A controls,
six of 171 guards and four of 42 goals. All 252 service cases are unstarted.

Receipt hashing previously called SHA-256 update separately for the header
fields and every integer. A private fixed 64-byte buffer now feeds the same
width/row header and column-major submitted signed little-endian values in
larger chunks. Full and partial buffers, including cross-column boundaries,
preserve the exact message and digest. This changes neither validation nor
receipt identity. No unsafe, digest cache, new backend/dependency, wire/format,
budget, ACK, read-view, lock, flush, collection or public API change occurs.
The original scalar feature-disabled path remains byte-exact. Archive/Cargo
inverses and every other serial116 Reader/query/live/source/group/test hash pass.
The locked [sha2 0.10.9 API](https://docs.rs/sha2/0.10.9/sha2/) supports hashing
the canonical message with incremental or one-shot updates.

This measures collector107/filter109/replay110/scan112/group-range116/digest117
together against fresh same-D: supported016 A/A baselines. It does not isolate
the new digest change versus116. Rejected concurrent flushing114 stays separate.

All 820 fresh tests/eight configurations, five strict lints, normal/fault
binaries and 359 fresh recovery commands pass. Four new units compare flat
message oracles and independent Python hashlib goldens across signed limits,
empty/short/full/partial/cross-column buffers, shape/order, large/wide inputs
and repeated calls. Two integrations verify durable receipt bytes, mismatch
rejection, retry/reopen, Live prepared/indexed/unindexed and SourceArchive
recovery identity. Recovery covers 28 injected error/owned process exits,
ten corruptions, two old formats, exact byte fixtures, concurrent ACKs and
300 cold SQL checks. These do not establish physical power-loss guarantees.

The first build exited1 on a new test assertion comparing u64 to usize after
324 baseline/fixed executions. Its original sources/proofs/logs/targets remain.
A separate corrected input changes only that test conversion; all 820 required
tests were then run fresh. One pure closure invocation from the Root helper
directory exited1 on the required import-origin guard before auditing data.
The unchanged auditor launched from the experiment directory passes; both
logs and actual exits are retained. The preservation helper later exited1
after all archive/restore proofs passed, on the absent first-build success
summary. Its failed log is retained. A separate metadata completion verifies
all53 existing ZIP SHA/CRC/order/size and whole original/restored inventories
again, and indexes the failed-build record plus successful v3 proof. That
completion exits0; no archive, source, Native or timer is rewritten/rerun.

Four Native/two service excluded smokes, 48 order checks, six outcome negatives
and two invalid orders pass. All324 fixed cases ran once, twelve rounds/all
six balanced orders/full and both halves. All479,232 ACKs and2,921,356,800 CRC
bytes pass independent rows/indexes/receipt generations/digests/current metadata,
cold SQLite SQL and raw quantiles. Every stall, maximum and failed scope remains.

## Controlled goals

These eight metrics meet targets and corresponding controls in full and both
halves. Percentages use median within-round paired ratios and need not equal
the quotient of the displayed medians.

| Workload | Metric | Unit | 016 baseline median | Candidate median | Full paired reduction | Full A/A | Full/both-half goal and controls |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| identified-replay | p99 | us | 2.100000 | 1.900000 | 14.52% | 1.00000000 | pass |
| queries-late | grouped/median_us | us | 6163.100000 | 4758.500000 | 23.30% | 0.99583906 | pass |
| queries-late | unordered_filter/median_us | us | 2789.400000 | 2066.150000 | 26.42% | 1.02057890 | pass |
| queries-late | unordered_filter/p95_us | us | 3474.350000 | 2450.200000 | 22.92% | 1.01897054 | pass |
| queries-ordered | grouped/median_us | us | 6180.950000 | 4733.550000 | 22.46% | 1.00203201 | pass |
| queries-ordered | unordered_filter/median_us | us | 2773.500000 | 2048.550000 | 27.22% | 1.01448618 | pass |
| small-anonymous | wall | ms | 2399.071550 | 1780.894550 | 27.16% | 1.01564299 | pass |
| small-named | wall | ms | 2526.054400 | 1715.176550 | 32.28% | 0.99102957 | pass |

## Remaining failures

Every failed guard and goal follows. A passing control with a failing guard
is a calibrated regression. A failed control makes that comparison inconclusive.
Goals require both their numerical target and corresponding controls in every
declared scope. No gate has changed; service is unstarted because Native fails.

- full sparse-anonymous p95: C/A 1.05035050 (+5.04%); A/A 1.02037752; calibrated regression.

- half_1 pressure-anonymous p99: C/A 1.14987791 (+14.99%); A/A 1.01115786; calibrated regression.

- half_1 pressure-named p50: C/A 1.05589598 (+5.59%); A/A 1.00485175; calibrated regression.

- half_1 pressure-named p95: C/A 1.18975397 (+18.98%); A/A 1.11195674; inconclusive: control fails.

- half_1 queries-late broad_window/p95_us: C/A 1.06558442 (+6.56%); A/A 0.98245614; calibrated regression.

- half_2 sparse-anonymous p95: C/A 1.05985983 (+5.99%); A/A 1.03073489; calibrated regression.

- Goal miss: full small-anonymous p99, C/A 0.97709610 versus 0.95; A/A 1.03285191; control passes.

- Goal miss: half_1 small-anonymous p99, C/A 0.96174888 versus 0.95; A/A 1.02404682; control passes.

- Goal miss: half_1 identified-replay p95, C/A 0.91795666 versus 0.9; A/A 1.00000000; control passes.

- Goal miss: half_2 small-anonymous p99, C/A 0.97709610 versus 0.95; A/A 1.18265320; inconclusive: control fails.


## Every before/after comparison

All171 full/half comparisons follow. A/A requires0.95-1.05; candidate guards
require C/A at most1.05. Goals keep metric-specific stricter limits. Disk has
no A/A control. Every failed guard remains recorded even when controls fail.

| Scope | Workload | Metric | Unit | Baseline median | Candidate median | A/A | Control | C/A | Guard | Goal limit | Goal |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | ---: | --- |
| full | sparse-anonymous | p50 | ms | 1.877600 | 1.892450 | 1.01914025 | pass | 1.01350179 | pass | n/a | n/a |
| full | sparse-anonymous | p95 | ms | 5.148150 | 5.486200 | 1.02037752 | pass | 1.05035050 | FAIL | n/a | n/a |
| full | sparse-anonymous | p99 | ms | 13.657850 | 14.078950 | 1.01629955 | pass | 1.00309184 | pass | n/a | n/a |
| full | sparse-anonymous | wall | ms | 1214.725200 | 1254.737950 | 1.01907056 | pass | 1.01502935 | pass | n/a | n/a |
| full | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| full | sparse-named | p50 | ms | 1.872100 | 1.877700 | 1.00930300 | pass | 1.00305419 | pass | n/a | n/a |
| full | sparse-named | p95 | ms | 5.356900 | 5.319100 | 0.99993435 | pass | 0.95675605 | pass | n/a | n/a |
| full | sparse-named | p99 | ms | 13.514550 | 13.576750 | 1.02420527 | pass | 1.00573072 | pass | n/a | n/a |
| full | sparse-named | wall | ms | 1248.668600 | 1252.290800 | 0.99427485 | pass | 1.00558390 | pass | n/a | n/a |
| full | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| full | small-anonymous | p50 | ms | 3.874600 | 2.244100 | 1.00240889 | pass | 0.56681000 | pass | n/a | n/a |
| full | small-anonymous | p95 | ms | 13.469900 | 9.160850 | 1.03846305 | pass | 0.67634043 | pass | n/a | n/a |
| full | small-anonymous | p99 | ms | 16.488250 | 16.148100 | 1.03285191 | pass | 0.97709610 | pass | 0.95 | FAIL |
| full | small-anonymous | wall | ms | 2399.071550 | 1780.894550 | 1.01564299 | pass | 0.72838520 | pass | 0.9 | pass |
| full | small-anonymous | disk | bytes | 5745431.000000 | 4973507.500000 | 1.00436572 | n/a | 0.97855481 | pass | n/a | n/a |
| full | small-named | p50 | ms | 4.048300 | 2.216300 | 0.99779088 | pass | 0.55110655 | pass | n/a | n/a |
| full | small-named | p95 | ms | 13.949450 | 9.187200 | 1.01206369 | pass | 0.64287321 | pass | n/a | n/a |
| full | small-named | p99 | ms | 18.659100 | 15.789350 | 1.04150955 | pass | 0.88901365 | pass | 0.95 | pass |
| full | small-named | wall | ms | 2526.054400 | 1715.176550 | 0.99102957 | pass | 0.67723566 | pass | 0.9 | pass |
| full | small-named | disk | bytes | 6426406.000000 | 5712978.000000 | 0.99570388 | n/a | 0.93420424 | pass | n/a | n/a |
| full | pressure-anonymous | p50 | ms | 2.386050 | 2.329100 | 0.98658312 | pass | 0.99977234 | pass | n/a | n/a |
| full | pressure-anonymous | p95 | ms | 7.482750 | 6.560450 | 0.96010643 | pass | 0.89218629 | pass | n/a | n/a |
| full | pressure-anonymous | p99 | ms | 14.654250 | 16.742800 | 0.99800765 | pass | 1.00401114 | pass | n/a | n/a |
| full | pressure-anonymous | wall | ms | 432.407200 | 422.144150 | 0.99473733 | pass | 0.97977673 | pass | n/a | n/a |
| full | pressure-anonymous | disk | bytes | 11436261.500000 | 11452488.500000 | 1.00055289 | n/a | 1.00036622 | pass | n/a | n/a |
| full | pressure-named | p50 | ms | 2.858600 | 2.890050 | 1.00485175 | pass | 1.03255980 | pass | n/a | n/a |
| full | pressure-named | p95 | ms | 11.666850 | 11.897050 | 1.00196150 | pass | 0.97699489 | pass | n/a | n/a |
| full | pressure-named | p99 | ms | 20.494250 | 20.892750 | 0.90236901 | FAIL | 0.90789974 | pass | n/a | n/a |
| full | pressure-named | wall | ms | 529.361800 | 518.964150 | 1.00921079 | pass | 0.98529641 | pass | n/a | n/a |
| full | pressure-named | disk | bytes | 12168264.000000 | 12173486.000000 | 0.99946857 | n/a | 0.99761890 | pass | n/a | n/a |
| full | queries-ordered | all_aggregates/median_us | us | 5.000000 | 4.700000 | 1.00000000 | pass | 0.93938776 | pass | n/a | n/a |
| full | queries-ordered | all_aggregates/p95_us | us | 5.500000 | 5.200000 | 1.00909091 | pass | 0.94545455 | pass | n/a | n/a |
| full | queries-ordered | broad_window/median_us | us | 5.200000 | 4.950000 | 1.00000000 | pass | 0.94230769 | pass | n/a | n/a |
| full | queries-ordered | broad_window/p95_us | us | 5.400000 | 5.200000 | 1.00000000 | pass | 0.94494949 | pass | n/a | n/a |
| full | queries-ordered | narrow_window/median_us | us | 4.300000 | 4.000000 | 1.00000000 | pass | 0.93023256 | pass | n/a | n/a |
| full | queries-ordered | narrow_window/p95_us | us | 4.500000 | 4.200000 | 1.00000000 | pass | 0.95454545 | pass | n/a | n/a |
| full | queries-ordered | unordered_filter/median_us | us | 2773.500000 | 2048.550000 | 1.01448618 | pass | 0.72779750 | pass | 0.9 | pass |
| full | queries-ordered | unordered_filter/p95_us | us | 3509.400000 | 2425.000000 | 1.02884160 | pass | 0.70871862 | pass | 0.9 | pass |
| full | queries-ordered | grouped/median_us | us | 6180.950000 | 4733.550000 | 1.00203201 | pass | 0.77536825 | pass | 0.9 | pass |
| full | queries-ordered | grouped/p95_us | us | 7714.400000 | 6065.600000 | 0.93099273 | FAIL | 0.79028649 | pass | 0.9 | pass |
| full | queries-ordered | min_max/median_us | us | 7.750000 | 7.600000 | 0.97452126 | pass | 0.97402597 | pass | n/a | n/a |
| full | queries-ordered | min_max/p95_us | us | 8.150000 | 7.800000 | 0.97530488 | pass | 0.95030864 | pass | n/a | n/a |
| full | queries-late | all_aggregates/median_us | us | 5.000000 | 4.800000 | 0.99000000 | pass | 0.95959184 | pass | n/a | n/a |
| full | queries-late | all_aggregates/p95_us | us | 5.600000 | 5.350000 | 1.04545455 | pass | 0.97252747 | pass | n/a | n/a |
| full | queries-late | broad_window/median_us | us | 5.300000 | 5.000000 | 1.00000000 | pass | 0.96189419 | pass | n/a | n/a |
| full | queries-late | broad_window/p95_us | us | 5.450000 | 5.200000 | 1.00000000 | pass | 0.98113208 | pass | n/a | n/a |
| full | queries-late | narrow_window/median_us | us | 4.400000 | 4.150000 | 0.98863636 | pass | 0.94341085 | pass | n/a | n/a |
| full | queries-late | narrow_window/p95_us | us | 4.600000 | 4.300000 | 0.98913043 | pass | 0.95505051 | pass | n/a | n/a |
| full | queries-late | unordered_filter/median_us | us | 2789.400000 | 2066.150000 | 1.02057890 | pass | 0.73580310 | pass | 0.9 | pass |
| full | queries-late | unordered_filter/p95_us | us | 3474.350000 | 2450.200000 | 1.01897054 | pass | 0.77084694 | pass | 0.9 | pass |
| full | queries-late | grouped/median_us | us | 6163.100000 | 4758.500000 | 0.99583906 | pass | 0.76695212 | pass | 0.9 | pass |
| full | queries-late | grouped/p95_us | us | 7530.700000 | 5383.950000 | 0.97434570 | pass | 0.76197592 | pass | 0.9 | pass |
| full | queries-late | min_max/median_us | us | 7.400000 | 7.100000 | 1.00000000 | pass | 0.95945946 | pass | n/a | n/a |
| full | queries-late | min_max/p95_us | us | 7.650000 | 7.300000 | 1.00000000 | pass | 0.95368421 | pass | n/a | n/a |
| full | identified-replay | p50 | us | 1.300000 | 1.100000 | 1.00000000 | pass | 0.77747253 | pass | n/a | n/a |
| full | identified-replay | p95 | us | 1.700000 | 1.600000 | 1.02941176 | pass | 0.88854489 | pass | 0.9 | pass |
| full | identified-replay | p99 | us | 2.100000 | 1.900000 | 1.00000000 | pass | 0.85478261 | pass | 0.9 | pass |
| half_1 | sparse-anonymous | p50 | ms | 1.917600 | 1.923850 | 1.03032072 | pass | 1.01118360 | pass | n/a | n/a |
| half_1 | sparse-anonymous | p95 | ms | 5.121900 | 5.463000 | 1.02037752 | pass | 1.04588614 | pass | n/a | n/a |
| half_1 | sparse-anonymous | p99 | ms | 14.500750 | 14.566150 | 0.99854802 | pass | 0.99944746 | pass | n/a | n/a |
| half_1 | sparse-anonymous | wall | ms | 1269.488100 | 1254.737950 | 1.00836727 | pass | 1.01502935 | pass | n/a | n/a |
| half_1 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| half_1 | sparse-named | p50 | ms | 1.891950 | 1.972750 | 1.01934665 | pass | 1.00063814 | pass | n/a | n/a |
| half_1 | sparse-named | p95 | ms | 5.524000 | 5.417350 | 0.98971158 | pass | 0.95675605 | pass | n/a | n/a |
| half_1 | sparse-named | p99 | ms | 14.131650 | 14.519850 | 1.03216931 | pass | 0.99733923 | pass | n/a | n/a |
| half_1 | sparse-named | wall | ms | 1263.934200 | 1301.108750 | 0.99560346 | pass | 1.00696084 | pass | n/a | n/a |
| half_1 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| half_1 | small-anonymous | p50 | ms | 4.059350 | 2.282350 | 1.02377197 | pass | 0.55782124 | pass | n/a | n/a |
| half_1 | small-anonymous | p95 | ms | 14.163550 | 9.493100 | 1.03846305 | pass | 0.67214745 | pass | n/a | n/a |
| half_1 | small-anonymous | p99 | ms | 18.076000 | 16.924400 | 1.02404682 | pass | 0.96174888 | pass | 0.95 | FAIL |
| half_1 | small-anonymous | wall | ms | 2549.750650 | 1801.070600 | 1.00844721 | pass | 0.70681697 | pass | 0.9 | pass |
| half_1 | small-anonymous | disk | bytes | 5320695.500000 | 4970406.000000 | 1.08270438 | n/a | 0.98912855 | pass | n/a | n/a |
| half_1 | small-named | p50 | ms | 4.063300 | 2.342750 | 1.02791721 | pass | 0.57632578 | pass | n/a | n/a |
| half_1 | small-named | p95 | ms | 14.218700 | 9.204050 | 1.02543112 | pass | 0.62677488 | pass | n/a | n/a |
| half_1 | small-named | p99 | ms | 18.835950 | 16.534050 | 1.05532911 | FAIL | 0.92003112 | pass | 0.95 | pass |
| half_1 | small-named | wall | ms | 2543.802850 | 1766.721050 | 1.04419993 | pass | 0.69870202 | pass | 0.9 | pass |
| half_1 | small-named | disk | bytes | 6426406.000000 | 5712440.500000 | 0.91358892 | n/a | 0.93248019 | pass | n/a | n/a |
| half_1 | pressure-anonymous | p50 | ms | 2.474200 | 2.450450 | 0.97977265 | pass | 1.00908026 | pass | n/a | n/a |
| half_1 | pressure-anonymous | p95 | ms | 7.347450 | 6.659400 | 0.90685383 | FAIL | 0.90642730 | pass | n/a | n/a |
| half_1 | pressure-anonymous | p99 | ms | 14.577950 | 17.023000 | 1.01115786 | pass | 1.14987791 | FAIL | n/a | n/a |
| half_1 | pressure-anonymous | wall | ms | 437.195750 | 433.672200 | 1.00219620 | pass | 1.00752569 | pass | n/a | n/a |
| half_1 | pressure-anonymous | disk | bytes | 11418457.000000 | 11430674.000000 | 1.00046386 | n/a | 1.00090473 | pass | n/a | n/a |
| half_1 | pressure-named | p50 | ms | 2.897250 | 3.023450 | 1.00485175 | pass | 1.05589598 | FAIL | n/a | n/a |
| half_1 | pressure-named | p95 | ms | 7.960700 | 12.367600 | 1.11195674 | FAIL | 1.18975397 | FAIL | n/a | n/a |
| half_1 | pressure-named | p99 | ms | 21.082650 | 23.126400 | 1.23339567 | FAIL | 0.98303717 | pass | n/a | n/a |
| half_1 | pressure-named | wall | ms | 516.924900 | 542.906700 | 1.04741929 | pass | 1.04221230 | pass | n/a | n/a |
| half_1 | pressure-named | disk | bytes | 12177833.500000 | 12147509.000000 | 0.94209215 | n/a | 0.99514226 | pass | n/a | n/a |
| half_1 | queries-ordered | all_aggregates/median_us | us | 5.000000 | 4.800000 | 1.02020408 | pass | 0.94938776 | pass | n/a | n/a |
| half_1 | queries-ordered | all_aggregates/p95_us | us | 5.450000 | 5.350000 | 1.02777778 | pass | 0.97222222 | pass | n/a | n/a |
| half_1 | queries-ordered | broad_window/median_us | us | 5.200000 | 4.900000 | 1.00961538 | pass | 0.94230769 | pass | n/a | n/a |
| half_1 | queries-ordered | broad_window/p95_us | us | 5.400000 | 5.100000 | 1.01851852 | pass | 0.94392034 | pass | n/a | n/a |
| half_1 | queries-ordered | narrow_window/median_us | us | 4.300000 | 4.000000 | 0.98837209 | pass | 0.91860465 | pass | n/a | n/a |
| half_1 | queries-ordered | narrow_window/p95_us | us | 4.500000 | 4.200000 | 1.00000000 | pass | 0.93257576 | pass | n/a | n/a |
| half_1 | queries-ordered | unordered_filter/median_us | us | 2975.700000 | 2089.800000 | 1.02864248 | pass | 0.71996877 | pass | 0.9 | pass |
| half_1 | queries-ordered | unordered_filter/p95_us | us | 4078.150000 | 2515.800000 | 1.06065135 | FAIL | 0.67870726 | pass | 0.9 | pass |
| half_1 | queries-ordered | grouped/median_us | us | 6347.100000 | 5036.850000 | 0.99827648 | pass | 0.79058714 | pass | 0.9 | pass |
| half_1 | queries-ordered | grouped/p95_us | us | 9006.000000 | 6861.600000 | 0.88248513 | FAIL | 0.77160987 | pass | 0.9 | pass |
| half_1 | queries-ordered | min_max/median_us | us | 7.850000 | 7.600000 | 0.97452126 | pass | 0.95576299 | pass | n/a | n/a |
| half_1 | queries-ordered | min_max/p95_us | us | 8.200000 | 8.000000 | 0.99405488 | pass | 0.94451220 | pass | n/a | n/a |
| half_1 | queries-late | all_aggregates/median_us | us | 5.050000 | 4.850000 | 0.99744898 | pass | 0.96959184 | pass | n/a | n/a |
| half_1 | queries-late | all_aggregates/p95_us | us | 5.600000 | 5.450000 | 1.00925325 | pass | 0.98198052 | pass | n/a | n/a |
| half_1 | queries-late | broad_window/median_us | us | 5.300000 | 5.050000 | 1.00943396 | pass | 0.93396226 | pass | n/a | n/a |
| half_1 | queries-late | broad_window/p95_us | us | 5.600000 | 6.750000 | 0.98245614 | pass | 1.06558442 | FAIL | n/a | n/a |
| half_1 | queries-late | narrow_window/median_us | us | 4.400000 | 4.200000 | 1.01136364 | pass | 0.93257576 | pass | n/a | n/a |
| half_1 | queries-late | narrow_window/p95_us | us | 4.800000 | 4.350000 | 1.00000000 | pass | 0.94466403 | pass | n/a | n/a |
| half_1 | queries-late | unordered_filter/median_us | us | 3058.550000 | 2189.200000 | 1.02216952 | pass | 0.74027379 | pass | 0.9 | pass |
| half_1 | queries-late | unordered_filter/p95_us | us | 4015.900000 | 3178.850000 | 1.03219251 | pass | 0.77929319 | pass | 0.9 | pass |
| half_1 | queries-late | grouped/median_us | us | 6564.200000 | 5060.800000 | 1.01676122 | pass | 0.75303534 | pass | 0.9 | pass |
| half_1 | queries-late | grouped/p95_us | us | 8071.550000 | 6602.200000 | 1.02274173 | pass | 0.81714020 | pass | 0.9 | pass |
| half_1 | queries-late | min_max/median_us | us | 7.600000 | 7.150000 | 0.99949324 | pass | 0.94126819 | pass | n/a | n/a |
| half_1 | queries-late | min_max/p95_us | us | 8.400000 | 7.400000 | 1.01298701 | pass | 0.88173568 | pass | n/a | n/a |
| half_1 | identified-replay | p50 | us | 1.400000 | 1.100000 | 1.00000000 | pass | 0.79285714 | pass | n/a | n/a |
| half_1 | identified-replay | p95 | us | 1.900000 | 1.650000 | 1.00000000 | pass | 0.91795666 | pass | 0.9 | FAIL |
| half_1 | identified-replay | p99 | us | 2.350000 | 2.050000 | 0.97826087 | pass | 0.88716356 | pass | 0.9 | pass |
| half_2 | sparse-anonymous | p50 | ms | 1.853750 | 1.892450 | 1.01783983 | pass | 1.01559798 | pass | n/a | n/a |
| half_2 | sparse-anonymous | p95 | ms | 5.148150 | 5.544700 | 1.03073489 | pass | 1.05985983 | FAIL | n/a | n/a |
| half_2 | sparse-anonymous | p99 | ms | 13.282400 | 13.678900 | 1.04641785 | pass | 1.00645704 | pass | n/a | n/a |
| half_2 | sparse-anonymous | wall | ms | 1206.078550 | 1268.196300 | 1.03222960 | pass | 1.01513761 | pass | n/a | n/a |
| half_2 | sparse-anonymous | disk | bytes | 1251167.000000 | 1251167.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| half_2 | sparse-named | p50 | ms | 1.863050 | 1.869750 | 1.00675780 | pass | 1.00454019 | pass | n/a | n/a |
| half_2 | sparse-named | p95 | ms | 5.339750 | 5.245800 | 1.00042041 | pass | 0.94057176 | pass | n/a | n/a |
| half_2 | sparse-named | p99 | ms | 13.343550 | 13.451250 | 1.02378665 | pass | 1.00573072 | pass | n/a | n/a |
| half_2 | sparse-named | wall | ms | 1235.201350 | 1245.087400 | 0.99427485 | pass | 1.00045282 | pass | n/a | n/a |
| half_2 | sparse-named | disk | bytes | 1359111.000000 | 1359111.000000 | 1.00000000 | n/a | 1.00000000 | pass | n/a | n/a |
| half_2 | small-anonymous | p50 | ms | 3.772850 | 2.235100 | 0.98551463 | pass | 0.59414319 | pass | n/a | n/a |
| half_2 | small-anonymous | p95 | ms | 13.201450 | 8.932400 | 1.02382548 | pass | 0.67844665 | pass | n/a | n/a |
| half_2 | small-anonymous | p99 | ms | 16.013550 | 15.539600 | 1.18265320 | FAIL | 0.97709610 | pass | 0.95 | FAIL |
| half_2 | small-anonymous | wall | ms | 2354.637850 | 1777.380750 | 1.03309024 | pass | 0.75498265 | pass | 0.9 | pass |
| half_2 | small-anonymous | disk | bytes | 5815857.000000 | 4974862.000000 | 1.00100980 | n/a | 0.91749002 | pass | n/a | n/a |
| half_2 | small-named | p50 | ms | 4.033450 | 2.159500 | 0.98209863 | pass | 0.54120095 | pass | n/a | n/a |
| half_2 | small-named | p95 | ms | 13.861350 | 9.067600 | 1.00168020 | pass | 0.65313559 | pass | n/a | n/a |
| half_2 | small-named | p99 | ms | 18.465150 | 15.550050 | 0.97273927 | pass | 0.85490955 | pass | 0.95 | pass |
| half_2 | small-named | wall | ms | 2513.030200 | 1684.817950 | 0.96592429 | pass | 0.66355736 | pass | 0.9 | pass |
| half_2 | small-named | disk | bytes | 6129253.000000 | 5713000.500000 | 0.99922369 | n/a | 0.97625002 | pass | n/a | n/a |
| half_2 | pressure-anonymous | p50 | ms | 2.294050 | 2.290050 | 1.01608025 | pass | 0.99573060 | pass | n/a | n/a |
| half_2 | pressure-anonymous | p95 | ms | 8.803950 | 6.322150 | 1.08948753 | FAIL | 0.71364481 | pass | n/a | n/a |
| half_2 | pressure-anonymous | p99 | ms | 16.857050 | 15.478000 | 0.99800765 | pass | 0.95210244 | pass | n/a | n/a |
| half_2 | pressure-anonymous | wall | ms | 430.075650 | 411.437450 | 0.98328861 | pass | 0.95492893 | pass | n/a | n/a |
| half_2 | pressure-anonymous | disk | bytes | 11483333.500000 | 11466607.500000 | 1.00134171 | n/a | 0.99854362 | pass | n/a | n/a |
| half_2 | pressure-named | p50 | ms | 2.800850 | 2.862300 | 1.02352971 | pass | 1.02350056 | pass | n/a | n/a |
| half_2 | pressure-named | p95 | ms | 12.185750 | 10.898200 | 0.79370443 | FAIL | 0.89979820 | pass | n/a | n/a |
| half_2 | pressure-named | p99 | ms | 20.494250 | 18.180150 | 0.78492652 | FAIL | 0.81288578 | pass | n/a | n/a |
| half_2 | pressure-named | wall | ms | 542.006200 | 513.758250 | 0.95061788 | pass | 0.93403253 | pass | n/a | n/a |
| half_2 | pressure-named | disk | bytes | 12158138.500000 | 12177017.500000 | 1.00080529 | n/a | 1.00155279 | pass | n/a | n/a |
| half_2 | queries-ordered | all_aggregates/median_us | us | 5.000000 | 4.700000 | 0.98979592 | pass | 0.93938776 | pass | n/a | n/a |
| half_2 | queries-ordered | all_aggregates/p95_us | us | 5.650000 | 5.200000 | 0.97641634 | pass | 0.92100313 | pass | n/a | n/a |
| half_2 | queries-ordered | broad_window/median_us | us | 5.200000 | 5.000000 | 0.99056604 | pass | 0.95209027 | pass | n/a | n/a |
| half_2 | queries-ordered | broad_window/p95_us | us | 5.450000 | 5.250000 | 0.97204752 | pass | 0.95420875 | pass | n/a | n/a |
| half_2 | queries-ordered | narrow_window/median_us | us | 4.300000 | 4.100000 | 1.00000000 | pass | 0.95346320 | pass | n/a | n/a |
| half_2 | queries-ordered | narrow_window/p95_us | us | 4.450000 | 4.250000 | 1.00000000 | pass | 0.95505051 | pass | n/a | n/a |
| half_2 | queries-ordered | unordered_filter/median_us | us | 2716.300000 | 2022.900000 | 1.00565151 | pass | 0.74781314 | pass | 0.9 | pass |
| half_2 | queries-ordered | unordered_filter/p95_us | us | 3215.050000 | 2247.150000 | 1.00606734 | pass | 0.73244420 | pass | 0.9 | pass |
| half_2 | queries-ordered | grouped/median_us | us | 6054.700000 | 4645.600000 | 1.00337315 | pass | 0.77124772 | pass | 0.9 | pass |
| half_2 | queries-ordered | grouped/p95_us | us | 7228.600000 | 5573.450000 | 0.96682581 | pass | 0.79685910 | pass | 0.9 | pass |
| half_2 | queries-ordered | min_max/median_us | us | 7.700000 | 7.600000 | 0.97665256 | pass | 0.98051948 | pass | n/a | n/a |
| half_2 | queries-ordered | min_max/p95_us | us | 8.050000 | 7.800000 | 0.96851266 | pass | 0.96897953 | pass | n/a | n/a |
| half_2 | queries-late | all_aggregates/median_us | us | 4.950000 | 4.750000 | 0.99000000 | pass | 0.95959184 | pass | n/a | n/a |
| half_2 | queries-late | all_aggregates/p95_us | us | 5.550000 | 5.250000 | 1.09271978 | FAIL | 0.96396104 | pass | n/a | n/a |
| half_2 | queries-late | broad_window/median_us | us | 5.150000 | 5.000000 | 1.00000000 | pass | 0.98039216 | pass | n/a | n/a |
| half_2 | queries-late | broad_window/p95_us | us | 5.350000 | 5.200000 | 1.00000000 | pass | 0.98113208 | pass | n/a | n/a |
| half_2 | queries-late | narrow_window/median_us | us | 4.300000 | 4.100000 | 0.97674419 | pass | 0.95348837 | pass | n/a | n/a |
| half_2 | queries-late | narrow_window/p95_us | us | 4.500000 | 4.300000 | 0.98888889 | pass | 0.95555556 | pass | n/a | n/a |
| half_2 | queries-late | unordered_filter/median_us | us | 2692.500000 | 1995.750000 | 1.00210416 | pass | 0.73505922 | pass | 0.9 | pass |
| half_2 | queries-late | unordered_filter/p95_us | us | 2986.950000 | 2342.950000 | 1.01364832 | pass | 0.77084694 | pass | 0.9 | pass |
| half_2 | queries-late | grouped/median_us | us | 6037.300000 | 4631.950000 | 0.99583906 | pass | 0.76900693 | pass | 0.9 | pass |
| half_2 | queries-late | grouped/p95_us | us | 7097.000000 | 5199.300000 | 0.93681632 | FAIL | 0.73897907 | pass | 0.9 | pass |
| half_2 | queries-late | min_max/median_us | us | 7.250000 | 7.050000 | 1.00000000 | pass | 0.96584084 | pass | n/a | n/a |
| half_2 | queries-late | min_max/p95_us | us | 7.550000 | 7.300000 | 1.00000000 | pass | 0.97324324 | pass | n/a | n/a |
| half_2 | identified-replay | p50 | us | 1.300000 | 1.000000 | 1.00000000 | pass | 0.76923077 | pass | n/a | n/a |
| half_2 | identified-replay | p95 | us | 1.650000 | 1.450000 | 1.06066176 | FAIL | 0.87867647 | pass | 0.9 | pass |
| half_2 | identified-replay | p99 | us | 2.050000 | 1.700000 | 1.02380952 | pass | 0.80952381 | pass | 0.9 | pass |

## Exact preservation

38,336 files, 5,222 directories,
53 bounded ZIP parts and 4,075,316,365
logical bytes pass every member CRC/order/offset/size, exact original/restored
file hashes and complete file/directory sets before and after the full pure
audit. Every fresh prerequisite, all raw correctness/quantiles/profile and
full/half controls/guards/42 goals/252 unstarted service specifications replay
exactly without Native, timers or existing-file writes. Original files remain;
only inventoried regenerable target/Python caches are excluded. Closed raw
logs are byte-exact gzip supplements. The failed test-compilation attempt,
its test-only corrected copy and failed Root-origin pure audit invocation are
retained with actual exits. The successful fresh820 executions are separate
from the324 executions before the first compile failure. The original
preserver metadata-index failure and successful independent completion are
retained separately; all raw archives and original inputs remain exact.

No new supported upgrade, reliable release ETA, fresh competitor ranking,
universal win, Native CPU/RSS or physical power-loss guarantee is claimed.
Recent raw GitHub backup remains unverified; no recent raw deletion is eligible.
See [reproduction](benchmarks/adaptive-speed-117/REPRODUCE.md) and the
[complete audit](benchmarks/adaptive-speed-117/complete-audit-proof.json).


- October10 continuation: [private backup and exact unused-restore cleanup](STORAGE_CLEANUP_20261010.md). All32 pending commits uploaded; complete trial117 raw tree freshly downloaded/hash-verified. Only its unused restored duplicate was removed after full current hashes; original raw data and failures remain. Other recent raw download verification is still pending. Supported016 and trial117 performance outcome are unchanged.
