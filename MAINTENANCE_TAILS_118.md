# Maintenance-tail diagnostic 118 — October 10, 2026

In the preserved trial117 pressure-anonymous workload, first publications following a compaction account for a median **3.125% of ACKs** and **98.78% of candidate p99-tail samples**. Corresponding baselineA/B medians are89.02%/92.68%. This is a useful association for choosing the next engineering target; it does not prove exclusive compaction CPU/disk causality or qualify a speed improvement.

This is an **untimed post-hoc diagnostic** of the complete existing216 live cases and479232 ACKs: six workloads,12 balanced rounds, both016 baseline runs and combined117 candidate, full and both original six-round halves. There is no new engine, test, recovery or benchmark execution. Trial117's820 fresh tests/359 recovery results and its15 failed A/A controls/six failed guards/four failed goals are reused unchanged. All252 service cases remain unstarted. Supported016 and release017 status are unchanged.

The pressure workload has32 producers x128 batches; small has4x512, sparse1x512. Each batch contains100 rows and three signed-i64 columns; anonymous and named modes both remain. Every p50/p95/p99/max quantile exactly reproduces the original driver.

## How generation gaps identify maintenance

Actual baseline and candidate source agree: successful nonempty append_group publishes once and returns that generation to all group members. After sending those ACKs, the writer runs compact_small at64 small segments; it selects up to32 runs capped65536 rows/64MiB and publishes a separate generation while retaining original receipts. This driver starts empty and performs no intervening retries or other publications before cold statistics.

Sorted distinct ACK generations therefore expose interior maintenance publications. Every case independently reconciles unique ACK groups with ingest counters and missing generations with compactions/final cold generation. Two cases include a trailing compaction after the last ACK; both are retained. Ingest statistics are sampled before last-owner join, so cold generations resolve their timing race rather than discarding them.

The CSV classifies **every ACK**, including fast ones. `after_gap_0` means the first acknowledged publication after a gap; distances1/2 and3+ remain separate, as do requests before the first gap. Tails contain every sample at or above the nearest-rank cutoff, including ties; all denominators and per-case values remain. Different variants have different group sizes, so conditional classes are descriptive and do not replace the original full-population controls.

## Every full/half diagnostic summary

Each row is the median of all12 or six cases for that exact workload/variant/scope. The p99-tail shares are medians of per-case shares; they are not ratios of pooled counts. First-gap-group p99 is a conditional statistic, not a new benchmark win.

| Scope | Workload | Variant | First-gap ACK share % | p95 tail in first-gap group % | p99 tail in first-gap group % | p99 tail within first three groups % | First-gap p99 ms | Maintenance publications |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| full | pressure-anonymous | baseline_a | 3.1250 | 62.4390 | 89.0244 | 89.0244 | 24.658350 | 4.00 |
| full | pressure-anonymous | baseline_b | 3.1250 | 62.4390 | 92.6829 | 92.6829 | 24.226450 | 4.00 |
| full | pressure-anonymous | candidate | 3.1250 | 62.4390 | 98.7805 | 98.7805 | 24.276000 | 4.00 |
| full | pressure-named | baseline_a | 3.1250 | 57.8049 | 84.1463 | 84.1463 | 32.242700 | 4.00 |
| full | pressure-named | baseline_b | 3.1250 | 62.4390 | 86.5854 | 89.0244 | 31.146200 | 4.00 |
| full | pressure-named | candidate | 3.1250 | 62.4390 | 80.4878 | 80.4878 | 32.035050 | 4.00 |
| full | small-anonymous | baseline_a | 5.6641 | 7.2816 | 19.0476 | 23.8095 | 19.579400 | 29.00 |
| full | small-anonymous | baseline_b | 5.6641 | 7.7670 | 19.0476 | 19.0476 | 20.049850 | 29.00 |
| full | small-anonymous | candidate | 3.9062 | 19.9029 | 19.0476 | 19.0476 | 18.367200 | 20.00 |
| full | small-named | baseline_a | 5.4688 | 4.3689 | 19.0476 | 19.0476 | 23.312300 | 28.00 |
| full | small-named | baseline_b | 5.4932 | 6.3107 | 19.0476 | 21.4286 | 24.499500 | 28.50 |
| full | small-named | candidate | 3.5156 | 28.1553 | 19.0476 | 28.5714 | 23.405550 | 18.00 |
| full | sparse-anonymous | baseline_a | 2.9297 | 38.4615 | 16.6667 | 25.0000 | 16.006150 | 15.00 |
| full | sparse-anonymous | baseline_b | 2.9297 | 38.4615 | 16.6667 | 33.3333 | 15.974200 | 15.00 |
| full | sparse-anonymous | candidate | 2.9297 | 34.6154 | 16.6667 | 33.3333 | 16.213200 | 15.00 |
| full | sparse-named | baseline_a | 2.9297 | 42.3077 | 16.6667 | 33.3333 | 20.511950 | 15.00 |
| full | sparse-named | baseline_b | 2.9297 | 46.1538 | 16.6667 | 33.3333 | 20.775400 | 15.00 |
| full | sparse-named | candidate | 2.9297 | 46.1538 | 16.6667 | 33.3333 | 21.764850 | 15.00 |
| half_1 | pressure-anonymous | baseline_a | 3.1250 | 62.4390 | 89.0244 | 89.0244 | 25.201750 | 4.00 |
| half_1 | pressure-anonymous | baseline_b | 3.1250 | 62.4390 | 97.5610 | 97.5610 | 25.485150 | 4.00 |
| half_1 | pressure-anonymous | candidate | 3.1250 | 62.4390 | 100.0000 | 100.0000 | 26.063200 | 4.00 |
| half_1 | pressure-named | baseline_a | 3.1250 | 62.4390 | 92.6829 | 92.6829 | 35.160850 | 4.00 |
| half_1 | pressure-named | baseline_b | 3.1250 | 57.8049 | 78.0488 | 78.0488 | 31.007100 | 4.00 |
| half_1 | pressure-named | candidate | 3.1250 | 62.2875 | 85.3659 | 85.3659 | 33.464300 | 4.00 |
| half_1 | small-anonymous | baseline_a | 5.6641 | 3.8835 | 19.0476 | 19.0476 | 20.725700 | 29.00 |
| half_1 | small-anonymous | baseline_b | 5.6641 | 5.8252 | 19.0476 | 21.4286 | 19.318450 | 29.00 |
| half_1 | small-anonymous | candidate | 3.8574 | 24.2718 | 19.0476 | 26.1905 | 18.500150 | 20.00 |
| half_1 | small-named | baseline_a | 5.4688 | 7.2816 | 28.5714 | 28.5714 | 24.492500 | 28.00 |
| half_1 | small-named | baseline_b | 5.4688 | 7.7670 | 26.1905 | 26.1905 | 25.531550 | 28.00 |
| half_1 | small-named | candidate | 3.3936 | 29.1262 | 19.0476 | 28.5714 | 23.428450 | 18.00 |
| half_1 | sparse-anonymous | baseline_a | 2.9297 | 42.3077 | 16.6667 | 41.6667 | 18.027700 | 15.00 |
| half_1 | sparse-anonymous | baseline_b | 2.9297 | 40.3846 | 16.6667 | 33.3333 | 16.599800 | 15.00 |
| half_1 | sparse-anonymous | candidate | 2.9297 | 34.6154 | 16.6667 | 41.6667 | 17.231850 | 15.00 |
| half_1 | sparse-named | baseline_a | 2.9297 | 44.2308 | 16.6667 | 33.3333 | 20.380450 | 15.00 |
| half_1 | sparse-named | baseline_b | 2.9297 | 46.1538 | 16.6667 | 33.3333 | 21.064050 | 15.00 |
| half_1 | sparse-named | candidate | 2.9297 | 46.1538 | 25.0000 | 41.6667 | 22.062200 | 15.00 |
| half_2 | pressure-anonymous | baseline_a | 3.1250 | 62.4390 | 89.0244 | 89.0244 | 24.478350 | 4.00 |
| half_2 | pressure-anonymous | baseline_b | 3.1250 | 57.9185 | 80.4878 | 80.4878 | 23.525850 | 4.00 |
| half_2 | pressure-anonymous | candidate | 3.1250 | 62.4390 | 91.4634 | 91.4634 | 23.550300 | 4.00 |
| half_2 | pressure-named | baseline_a | 3.1250 | 53.1707 | 78.0488 | 78.0488 | 31.192600 | 4.00 |
| half_2 | pressure-named | baseline_b | 3.1250 | 62.4390 | 89.0244 | 90.2439 | 31.422050 | 4.00 |
| half_2 | pressure-named | candidate | 3.1250 | 62.4390 | 80.4878 | 80.4878 | 30.980500 | 4.00 |
| half_2 | small-anonymous | baseline_a | 5.6641 | 7.7670 | 33.3333 | 33.3333 | 19.099650 | 29.00 |
| half_2 | small-anonymous | baseline_b | 5.6641 | 7.7670 | 19.0476 | 19.0476 | 21.618350 | 29.00 |
| half_2 | small-anonymous | candidate | 3.9062 | 17.9612 | 19.0476 | 19.0476 | 18.367200 | 20.00 |
| half_2 | small-named | baseline_a | 5.5420 | 3.8835 | 19.0476 | 19.0476 | 22.984150 | 28.50 |
| half_2 | small-named | baseline_b | 5.6152 | 4.3689 | 19.0476 | 21.4286 | 23.959400 | 29.00 |
| half_2 | small-named | candidate | 3.5156 | 28.1553 | 21.4286 | 28.5714 | 23.399750 | 18.00 |
| half_2 | sparse-anonymous | baseline_a | 2.9297 | 38.4615 | 16.6667 | 16.6667 | 15.461850 | 15.00 |
| half_2 | sparse-anonymous | baseline_b | 2.9297 | 34.6154 | 16.6667 | 33.3333 | 15.588000 | 15.00 |
| half_2 | sparse-anonymous | candidate | 2.9297 | 36.5385 | 16.6667 | 16.6667 | 15.821750 | 15.00 |
| half_2 | sparse-named | baseline_a | 2.9297 | 40.3846 | 16.6667 | 25.0000 | 20.615600 | 15.00 |
| half_2 | sparse-named | baseline_b | 2.9297 | 44.2308 | 16.6667 | 33.3333 | 20.015000 | 15.00 |
| half_2 | sparse-named | candidate | 2.9297 | 44.2308 | 16.6667 | 33.3333 | 21.525600 | 15.00 |

## Implication and next hypothesis

Pressure tails are strongly concentrated immediately after maintenance in both baselines and candidate. Small and sparse p99 tails are much less concentrated: candidate full medians19.05% and16.67% in the first-gap group. Compaction alone cannot explain every remaining goal/guard miss. Absolute request arrival/scheduling alignment and stage-specific compaction costs were not measured here; generation association cannot attribute the117-vs016 pressure regression solely to one stage.

Source inspection identifies one concrete avoidable compaction cost: read_block allocates a fresh decoded Vec for every input block, then compact_small copies it into an already allocated output column. The existing CRC-first read_block_into can reuse a bounded single-block workspace across all selected runs/columns. A separate119 candidate can remove repeated temporary allocation while keeping exactly the same block reads, CRC checks, output values/order, selection ceilings, publication counts, receipt identity, ACK placement, maintenance work and writer join. Its benefit remains a hypothesis. Predeclare the complete unchanged324/252 qualification with fresh balanced D:016 A/A controls and additional actual compaction/retry/pin/corruption tests before implementing it; no119 source/build/timer is part of118.

## Preservation and limits

455 files/eight directories/53264913 logical bytes fit one bounded ZIP part. All current input hashes, member CRC/order and original/restored complete file/directory sets and full hashes pass before and after replaying the exact print-only auditor from a fresh restore. It independently reconstructs all479232 annotations,216 case quantiles/groups/counters and18 full/half summaries, retaining every original p95/p99 guard/control outcome. The first copied unexecuted auditor draft is retained alongside the actual print-only auditor; its sole difference is writing a proof into the audited tree, which the executed version avoids.

The original perf117 stores and its complete verified private archive remain unchanged. Every118 input/result/helper/draft is preserved locally. Source/reports/ZIP are committed privately; fresh remote118 raw-content download verification is still pending, so no118 duplicate or original is eligible for removal yet. No release/ETA, new competitor win, causal speed improvement or new correctness/recovery run is claimed.

See [all per-case data and original controls](benchmarks/maintenance-tails-118/analysis.json), [the preserved policy](benchmarks/maintenance-tails-118/policy.json), [independent audit](benchmarks/maintenance-tails-118/original-audit-proof.json), [full restored proof](benchmarks/maintenance-tails-118/preservation-proof.json) and [reproduction](benchmarks/maintenance-tails-118/REPRODUCE.md). Every original117 before/after remains in [trial117](ADAPTIVE_ENGINE_117.md).
