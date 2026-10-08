# Stronger writer-trace controls 091

October 8, 2026. **The exact 090 writer-trace artifact passes every fixed overhead, calibration, loss and memory gate in the full cohort and both independent 12-round halves.** All 39 A/A checks and 39 candidate guards pass. All 1,872,000 requests succeed and all 179,280 acknowledged batches survive reopening. This is a **two-profile diagnostic qualification milestone**, not an engine speed gain, supported upgrade, maximum capacity measurement or competitor ranking. Supported KestrelSQL remains **0.3.16**; 0.3.17 has no qualified release date.

## Exact artifacts and predeclared controls

[090](MAINTENANCE_ISOLATION_090.md) restored the original feature-disabled maintenance statements in an isolated diagnostic source; its default compatibility passed, but both half write-overall tracing A/A checks failed. Those failures and all [088](WRITER_OVERHEAD_088.md)/[089](BUILD_COMPARE_089.md) results remain preserved. Trial 091 makes **no source edits or rebuilds**. The exact 090 `restored-default` executable is repeated as A and B; its exact `restored-writer` executable is C. Source/lock/binary hashes are verified before and after the cohort. Artifact version 0.3.16 identifies isolated controls; no supported binary is replaced.

[Policy](benchmarks/trace-controls-091/policy.json) was declared before copying/native/timing. Twenty-four rounds form two independently complete 12-round halves, each containing all six A/B/C permutations twice for each profile. A fixed seed of 9108 shuffles complete permutations and alternates profile order. The new 144-case cohort does not selectively repeat bad 090 cases, change limits, add rounds after results or establish a direct 090 before/after. [Timing freeze](benchmarks/trace-controls-091/timing-freeze.json) records explicit immutable inputs; mutable stdout and caches are excluded.

Each fresh D: store starts with 1M rows. Read offers 2,000/s for 8 seconds. Write offers 500/s for 20 seconds with 25% 100-row appends. Both use 64 clients, zero deliberate grouping delay, retry index 0, queue capacity 256 and expiry 2 seconds. Offered caps are not measured maximum sustainable throughput.

All original 090 overhead limits remain unchanged: A/A p99/rate and native peak ratio 0.95–1.05; candidate p99<=1.05, achieved-window rate>=0.95 and peak ratio<=1.05; A/A absolute peak difference and candidate additional peak<=2 MiB; zero loss. Full and both halves must pass, C/B is diagnostic only, and charged CPU is diagnostic. Read overall/query use the same population; full/half checks overlap and are not independent statistical observations. Acceptance concerns the declared paired medians, not a per-request or every-round 5% bound.

The cohort ran **2026-10-08T16:52:34.445983+00:00 through 2026-10-08T17:30:54.661199+00:00**. No builds, copying, external hashing, packaging, cleanup, Git mutations or other benchmarks overlapped. Only light progress-tail reads ran alongside timing. Getters/resource sampling/reference/CRC/reopening remain outside arrival/drain windows. All Native children exited before post-timing exclusion, audit and preservation. The separately armed fresh-profile reset stayed waiting, not executing.

## Correctness and every required decision

[Reused qualification](benchmarks/trace-controls-091/reused-qualification-proof.json) explicitly reuses 090's 322 native debug/release test executions, five strict lint modes and 104 external native oracle commands, including byte equality, SQLite, old-format/retry/collision/concurrency/controlled-directory-failure/poison/reopening. These are **not newly rerun** in 091. Complete original unit/oracle fixtures remain preserved in 090 history. Historical broad crash/source coverage is reused, not a new process-kill or physical power-loss qualification.

Both fresh complete setup smokes pass and are excluded from all gates. Four invalid orders, four resource mutations and four trace mutations are rejected before freeze. Exact 090 harness/receipt/resource callbacks are retained; the runner changes only D: root/trial/two-smoke bookkeeping, and the auditor changes only root/trial/policy round-count/permutation multiplicity. No numerical gate, quantile or conservation logic changes.

All **1,872,000/1,872,000 offers succeed**, with zero errors/drop/expiry/unexecuted requests or ambiguous committed outcomes. All **179,280 acknowledged 100-row batches** reconcile exactly after reopening. **2,880 NumPy reference windows** and **3,886,272,000 full-CRC row-data bytes** pass. All **59,760 traced append ACKs** map exact fixture keys, attempts and publication generations with complete event chronology, stages and zero dropped trace records. Every **686 individual service sample above 100 ms** remains included.

| Scope | Rounds | Failed A/A | Failed candidate | Decision |
| --- | ---: | ---: | ---: | --- |
| full | 24 | 0/13 | 0/13 | Pass |
| block_0 | 12 | 0/13 | 0/13 | Pass |
| block_1 | 12 | 0/13 | 0/13 | Pass |

The second-half write-overall A/A ratio 0.955069 passes narrowly under the original 0.95 floor; no rounding or tolerance relaxation is used. A late traced case has a large individual latency ratio, and the worst untraced baseline has overall p99 127.4619 ms/append 172.3671 ms/max 305.3857 ms. All remain in raw quantiles and decisions. Passing predeclared medians does not establish uniform latency or erase outliers.

## Paired latency and native resources

Times are medians of case p99 values; paired ratios are medians of within-round C/A and B/A and need not equal the quotient of displayed medians. Numerically lower traced medians qualify the declared overhead limit, not an engine optimization.

| Scope | Profile/metric | A median ms | C median ms | Paired C/A | Paired B/A |
| --- | --- | ---: | ---: | ---: | ---: |
| full | read/overall | 1.0163 | 1.0188 | 1.010413 | 1.002443 |
| full | write/overall | 8.0474 | 7.9109 | 0.969650 | 0.969713 |
| full | write/query | 1.2618 | 1.2588 | 0.997315 | 1.004819 |
| full | write/append | 14.3211 | 14.1780 | 0.986972 | 0.987337 |
| block_0 | read/overall | 1.0212 | 1.0162 | 1.003539 | 1.002443 |
| block_0 | write/overall | 7.9162 | 7.6341 | 0.968694 | 0.977359 |
| block_0 | write/query | 1.2606 | 1.2547 | 0.997315 | 1.010668 |
| block_0 | write/append | 14.2004 | 13.9685 | 0.965560 | 0.987337 |
| block_1 | read/overall | 1.0060 | 1.0188 | 1.028009 | 1.002174 |
| block_1 | write/overall | 8.4058 | 8.1552 | 0.991592 | 0.955069 |
| block_1 | write/query | 1.2618 | 1.2591 | 0.997132 | 1.002403 |
| block_1 | write/append | 14.5975 | 14.5809 | 0.992797 | 0.990583 |

Native GetProcessMemoryInfo peak working set includes startup/seed/workload through the post-load sample before getter/reopen. It is not isolated allocation or full-lifetime peak RSS. GetProcessTimes uses a 100 ns representation unit, not guaranteed resolution; zero read CPU increments do not prove zero cost. Every resource gate passes.

| Scope | Profile | Paired C/A peak | Median extra KiB | Paired window rate | Both memory guards |
| --- | --- | ---: | ---: | ---: | --- |
| full | read | 1.001572 | 64.0 | 1.000000 | Pass |
| full | write | 1.013060 | 572.0 | 1.000000 | Pass |
| block_0 | read | 1.002164 | 88.0 | 1.000000 | Pass |
| block_0 | write | 1.010507 | 462.0 | 1.000000 | Pass |
| block_1 | read | 1.001570 | 64.0 | 1.000000 | Pass |
| block_1 | write | 1.015065 | 662.0 | 1.000000 | Pass |

## Measured writer target

[Complete event/key correlation](benchmarks/trace-controls-091/trace-group-diagnostics.json) and [bottleneck summary](benchmarks/trace-controls-091/bottleneck-summary.json) preserve every traced append group and every maintenance interval. These are post-cohort descriptions within the qualified exact artifact/workload scope. Different clock domains prevent exclusive end-to-end p99 decomposition or physical disk/OS attribution.

| Native event | Count | p50 ms | p95 ms | p99 ms | Maximum ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| append | 56,989 | 2.0379 | 2.6509 | 8.0032 | 130.9467 |
| compact | 1,793 | 4.1317 | 6.1473 | 14.4885 | 133.0198 |
| reclaim | 1,767 | 11.1431 | 13.2025 | 18.0322 | 23.2830 |

Reclamation is a consistent long maintenance interval: median 11.1431 ms versus ordinary append 2.0379 ms; the median of per-write-case reclamation p99 values is 18.1537 ms. It currently scans the archive directory and synchronously removes eligible superseded catalogs/retired unpinned segments every 32 durable groups. This motivates separately identifying enumeration/deletion cost and testing bounded incremental writer reclamation, while retaining the existing public full-reclaim behavior, pinning/orphan/error rules and bounded disk use. It is a concrete source hypothesis, not proof that reclamation causes all service tails.

Pooled traced queue-to-collected-group p99 is 20.2765 ms. Of 27 append groups associated by exact receipt keys/generations with 155 service samples above 100 ms, 22 immediately follow an append, 3 compaction and 2 reclamation. Three native append intervals and one compaction exceed 100 ms; no reclaim interval does. Synchronization is 63.6–90.7% of summed recorded publication stages (median 64.7%), not a physical-storage fraction or p99 decomposition. All events and competing explanations remain preserved. No durability/synchronization/ACK reduction is authorized by this result.

## Complete preservation and continuation

**62 bounded archive parts preserve 6,820 files/4,045,857,272 logical bytes.** [Inventory](benchmarks/trace-controls-091/evidence-inventory.json), [preservation proof](benchmarks/trace-controls-091/preservation-proof.json), [restored proof](benchmarks/trace-controls-091/restored-audit-proof.json) and [reproduction](benchmarks/trace-controls-091/REPRODUCE.md) cover full ZIP/member CRC/SHA/size/exact-set checks, original-byte revalidation, exact frozen raw-audit replay, exact descriptive event/group replay and post-replay member checks. Restoration launches **zero Native processes and reruns zero timings**.

All originals remain at `D:/Codex/Kestrel/work/perf-091`; verified restoration is `D:/Codex/Kestrel/work/restored-trace-controls-091`. Only regenerable Python caches are excluded with explicit path/size inventory; originals remain. Finished logs are copied after closure. Three harmless read failures (wrong initial reset-status filename, unprivileged process-inventory access and guessed diagnostic-helper filename) are recorded with their resolution; no native run, frozen raw audit or preservation failed. All previous failed experiments remain intact.

Use 092 or later for a separate measured reclamation hypothesis, never another blind round-count extension or a reader tweak. Before changing scheduling/deletion work, quantify the actual operation cost, establish exclusive writer ownership and preserve pinned snapshots, historical catalogs, crash orphans, public API/error outcomes, disk ceilings and source/receipt/ACK/synchronization contracts. A justified candidate needs fresh predeclared complete balanced A/A/native/service/resource controls plus full correctness/recovery qualification before adoption. Full six-profile/minute/overload/scan/competitor/reproducibility release gates still precede 0.3.17; diagnostics alone supply no new all-benchmark win or ETA.

The supported core and issued overnight report are byte-exact; repository/history remain private/local. The separate prepared reset is waiting for full Codex exit. Never force-close apps, interfere with execution, resume abandoned chats or enable the old task/automation.

[090](MAINTENANCE_ISOLATION_090.md), [089](BUILD_COMPARE_089.md), [088](WRITER_OVERHEAD_088.md), [release requirements](RELEASE_TARGET_0_3_17.md), [history](BENCHMARK_HISTORY.md).
