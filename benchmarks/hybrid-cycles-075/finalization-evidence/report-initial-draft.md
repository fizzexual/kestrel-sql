# Hybrid receipt checkpoint benchmark 075

The qualified 074 hybrid metadata protocol now has a fresh balanced performance baseline. **All four large-history goals pass, but nine of 29 guards and ten of 33 identical-control checks fail. The trial is rejected; supported KestrelSQL 0.3.16 is unchanged.** Logical correctness passes. These are metadata-model measurements; SQL, data segments and network requests are outside this cohort.

## Current workload and comparison

A/B are identical CAT4 controls with the released borrowed serializer and bounded 32-catalog cycle. C uses the byte-identical [074 hybrid protocol](HYBRID_RECEIPTS_074.md): an immutable complete anchor, cheap bounded delta heads and post-anchor receipt pages only at checkpoint roots. Both use the same instrumented file helper, which is not the entire released Archive IO implementation.

Every case imports the unchanged original generation-129 checkpoint containing 126/50,126/99,126 receipts and adds 64 actual new receipts: 56 ordinary IDs and eight contiguous intervals over two feeds. Both execute two full 32-publication cycles; CAT4 resets to a complete catalog, while hybrid publishes a tail page and checkpoint head at publications 32 and 64. Segment references are identical and opaque. No data segment is written or queried.

Six fresh rounds use every A/B/C permutation once per size, every variant/size at each position twice and A/B relative ordering three times each way. All binary/source/input/order/policy/harness/oracle hashes were frozen before timers. Timed cohort: 2026-10-07T14:21:21.039485+00:00 to 2026-10-07T14:24:32.243458+00:00. All 54 cases completed, with 3,456 publications, 432 source intervals and 648 fresh recoveries. One owned child at a time; no compile, test, audit, package or Git ran during timed work. No case was rerun or excluded.

Publication time charges batch/digest/source validation, the same full-ledger source clone, metadata copies, serialization/checksums, all changed-file writes/flushes/syncs/closes/renames and ledger updates. Exact full-ledger summary hashes are checked outside timers. Migration and recovery are timed separately. Peak memory includes setup, migration, recovery and validation. Recovery means three same-process fresh opens after dropping the writer at publications 31/32/63/64; OS cache may be warm.

## Before/after publication totals

Display times are independent medians of six 64-publication sums, in milliseconds. Matched columns are medians of six per-round C/A and B/A ratios; **never divide the display medians**. A/A calibration applies to each declared metric, not just publication total. Large totals are lower within this cohort, while the full candidate still fails adoption and tails lack stable controls.

| Initial receipts | CAT4 A display ms | CAT4 B display ms | Hybrid C display ms | Matched C/A | Matched B/A |
|---:|---:|---:|---:|---:|---:|
| 126 | 172.1765 | 133.5172 | 174.6733 | 1.217985 | 1.000214 |
| 50,126 | 1461.0573 | 1737.9939 | 542.5345 | 0.558045 | 0.902623 |
| 99,126 | 780.6439 | 745.6653 | 393.7853 | 0.589895 | 0.934647 |

- ✅ Large total goals pass: matched C/A 0.558045 at 50,126 (44.2% lower) and 0.589895 at 99,126 (41.0% lower). Their total B/A checks pass at 0.902623 and 0.934647. Both have five rounds favoring C and one slower; this is scoped metadata evidence, not a released-engine improvement.
- ❌ At 126, total C/A 1.217985 fails the 1.10 guard; five rounds are slower and one faster. Median publication latency fails across all histories despite passing p50 A/A checks.

- 126 C/A publication totals by round: 1.236164, 1.199805, 1.321878, 0.755174, 1.144121, 2.314503.
- 50,126 C/A publication totals by round: 0.947024, 0.635953, 0.671450, 0.403203, 0.163731, 0.480137.
- 99,126 C/A publication totals by round: 0.658455, 0.607223, 0.437279, 0.390598, 1.054174, 0.572568.

## Latency and controls

All ratios below are matched medians; lower is better. P50/p99/max use all 64 publications. Source p99 uses the eight source publications, which include both checkpoints. Tail reductions at large sizes remain descriptive because corresponding A/A p99/max/source-p99 checks fail.

| Initial receipts | C/A p50 | C/A p99 | C/A maximum | C/A source p99 | B/A p50 | B/A p99 | B/A source p99 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 126 | 1.221238 | 1.136604 | 1.083823 | 1.323627 | 1.006794 | 1.065883 | 1.112679 |
| 50,126 | 1.232030 | 0.210309 | 0.209713 | 0.196925 | 1.012980 | 0.847544 | 0.822585 |
| 99,126 | 1.250814 | 0.206479 | 0.169522 | 0.155457 | 1.056317 | 0.848657 | 0.781320 |

❌ Publication p50 is 22.1%, 23.2% and 25.1% slower respectively. Small p99/source-p99 also fail. The attractive large checkpoint/tail numbers cannot establish a qualified tail improvement while identical-control tails drift. Adding source-p99 to A/A before this cohort exposed three more failed source calibrations; no previous gate was relaxed.

## Recovery and migration

Recovery display p99 values below are independent medians of six case p99s, each based on 12 opens. Matched recovery ratios are independently computed per round. Migration includes full input read/parse/validation and every initial publication sync. All migration guards pass, but 99K migration A/A fails; its apparent reduction is descriptive.

| Initial receipts | CAT4 A recovery p99 display ms | Hybrid recovery p99 display ms | Matched recovery C/A | Recovery B/A | Migration C/A | Migration B/A |
|---:|---:|---:|---:|---:|---:|---:|
| 126 | 8.4189 | 10.7484 | 1.185107 | 0.784255 | 1.067260 | 0.921177 |
| 50,126 | 79.9431 | 140.0843 | 1.700473 | 0.923361 | 0.732351 | 1.036962 |
| 99,126 | 174.5725 | 287.4180 | 1.653799 | 0.990096 | 0.814328 | 1.116579 |

❌ All recovery guards fail. At 50K/99K, recovery is 70.0%/65.4% slower with passing corresponding A/A checks. Small recovery A/A also fails, so the 18.5% increase there lacks stable calibration.

Additive correction to 074 prose: the unchanged native anchor-terminated path performs **three full anchor-body reads and two JSON parses**. The loop reads/checks it, the termination helper rereads/parses it, and final reconstruction rereads/parses it again. The independent Python reader parses it three times. Checkpoint-terminated native recovery reads/parses its anchor once. These costs remain charged; old 074 code, reports and archive are unchanged. A current hybrid chain may reference an additional immutable anchor outside its bounded delta/checkpoint heads; reachable counts at publications 31/32/63/64 are 32/3/34/3 versus CAT4 32/1/32/1.

## Storage and operation counts

✅ Retained-directory goals pass: about 66.7% fewer bytes at both large sizes. These deliberately retained benchmark histories include superseded files. They do **not** measure reclaimed disk space. Final current reachable hybrid metadata is nearly equal to CAT4 at large sizes and 3.7% larger at the small size; all predeclared <=1.05 current-byte guards pass.

| Initial receipts | Retained CAT4 A bytes | Retained hybrid bytes | Retained C/A | Final reachable CAT4 bytes | Final reachable hybrid bytes | Reachable C/A |
|---:|---:|---:|---:|---:|---:|---:|
| 126 | 173,413 | 61,051 | 0.352055 | 33,350 | 34,596 | 1.037361 |
| 50,126 | 24,845,811 | 8,262,178 | 0.332538 | 8,234,336 | 8,235,585 | 1.000152 |
| 99,126 | 48,991,269 | 16,310,654 | 0.332930 | 16,282,822 | 16,284,071 | 1.000077 |

Migration syncs one file in both models; hybrid anchor bodies match original complete CAT4 bodies exactly. CAT4 syncs 64 files across 64 publications; hybrid syncs 66 (62 non-checkpoint delta heads, two tail pages and two checkpoint heads). Final hybrid reachable metadata has three files versus one for CAT4; all 67 versus 65 historical files per case remain evidence. Neither model reclaims metadata.

Predeclared descriptive subsets do not replace any guard. Each case has 62 non-checkpoint publications (including six source intervals) and two checkpoints:

| Initial receipts | C/A non-checkpoint p50 | C/A non-checkpoint p99 | C/A checkpoint sum | C/A checkpoint maximum |
|---:|---:|---:|---:|---:|
| 126 | 1.222196 | 1.226519 | 1.109827 | 0.947520 |
| 50,126 | 1.229186 | 1.369518 | 0.121633 | 0.133557 |
| 99,126 | 1.247877 | 1.362398 | 0.152775 | 0.144202 |

## Every failed declared check

Four goals pass; 20 guards and 23 identity checks pass. All 19 failures below remain failures. Candidate guards compare C/A; identical-control checks compare B/A. Limits were declared before timers and calculated without rounded observations.

| Result/type | Initial receipts | Metric | Matched ratio | Required bound |
|---|---:|---|---:|---|
| ❌ guard | 126 | total_ms | 1.217985 | <= 1.1 |
| ❌ guard | 126 | p50_ms | 1.221238 | <= 1.05 |
| ❌ guard | 126 | p99_ms | 1.136604 | <= 1.1 |
| ❌ guard | 126 | fresh_recovery_p99_ms | 1.185107 | <= 1.1 |
| ❌ guard | 126 | source_p99_ms | 1.323627 | <= 1.1 |
| ❌ identity | 126 | max_ms | 1.108984 | 0.90–1.10 |
| ❌ identity | 126 | fresh_recovery_p99_ms | 0.784255 | 0.90–1.10 |
| ❌ identity | 126 | source_p99_ms | 1.112679 | 0.90–1.10 |
| ❌ guard | 50,126 | p50_ms | 1.232030 | <= 1.05 |
| ❌ guard | 50,126 | fresh_recovery_p99_ms | 1.700473 | <= 1.1 |
| ❌ identity | 50,126 | p99_ms | 0.847544 | 0.90–1.10 |
| ❌ identity | 50,126 | max_ms | 0.821705 | 0.90–1.10 |
| ❌ identity | 50,126 | source_p99_ms | 0.822585 | 0.90–1.10 |
| ❌ guard | 99,126 | p50_ms | 1.250814 | <= 1.05 |
| ❌ guard | 99,126 | fresh_recovery_p99_ms | 1.653799 | <= 1.1 |
| ❌ identity | 99,126 | p99_ms | 0.848657 | 0.90–1.10 |
| ❌ identity | 99,126 | max_ms | 0.775910 | 0.90–1.10 |
| ❌ identity | 99,126 | migration_ms | 1.116579 | 0.90–1.10 |
| ❌ identity | 99,126 | source_p99_ms | 0.781320 | 0.90–1.10 |

## Correctness, retries and crash provenance

- ✅ Three new integration tests in debug and release, both format checks and strict all-target Clippy pass. Only common dispatcher arms, a cloned bench075 entry point/CLI route and integration tests were added. CAT4/common IO source and the old bench073 entry point are byte-identical; the hybrid protocol and Cargo manifest/lock are byte-identical to 074.
- ✅ Six untimed pre-cohort workload smoke cases (toy 7/8/9 receipt inputs, both modes) pass full native history/retry/source/recovery and independent file checks. Their timings are excluded from performance controls by design.
- ✅ Every actual receipt ID/digest/row/generation/source position, old ordinary/source retry and collision rejection passes in all 54 cases; no retry/collision creates files. Original 126/50,126/99,126 receipt histories are retained intact.
- ✅ Independent Python directly decodes all 396 files in six canonical size/mode stores, reconstructing every anchor, delta, parent CRC, page/checkpoint and logical edit. All 3,546 primary fixture files match those independently validated equivalents by full SHA/length. All recovery hashes, stages, bytes, sync counts, memory queries, order and frozen hashes pass. This is direct canonical decoding plus exact duplicate hashing, not direct JSON decoding of every replica.
- ✅ The unchanged protocol's 40 debug + 40 release tests, 15 injected errors, 15 controlled process kills and 21 independent corruption fixtures are completed **074 prerequisites**, not new 075 crash tests. Their proof/source hashes are preserved. No 075 protocol cut, segment crash test or physical power-loss qualification is claimed.

All primary histories total 1,035,929,214 retained bytes. All owned native children exited and no task-owned DB/compiler process remains in the recorded post-cohort check. Frozen binary SHA: `4c3500672e23196fc64ab669ac78fc99ec121ddcaa8b12b4e998cefb46f8e0d1`.

## Stage profile and preservation

There are 21 publications over 500ms; none are removed. The largest is 38-r4-99000-hybrid, publication 33, 3796.4443ms, with 3747.0397ms inside measured sync_all (98.70%). It is a non-checkpoint publication. Stage timing identifies observed delay, not its physical-device/OS cause. Aggregate stage fractions are not individual causal proof. Residual includes hash/validation/source clone/ledger work and other outer overhead:

| Size/variant (six cases) | Publication total ms | Encode ms | Write ms | Sync ms | Rename ms | Residual ms | >500ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0-baseline_a | 1291.5000 | 3.9321 | 143.8684 | 923.3527 | 186.0565 | 34.2903 | 0 |
| 0-baseline_b | 2045.2752 | 3.7388 | 162.2328 | 1646.8056 | 201.9434 | 30.5546 | 0 |
| 0-hybrid | 1877.2484 | 2.3723 | 153.4873 | 1488.7624 | 190.0998 | 42.5266 | 0 |
| 50000-baseline_b | 10100.0968 | 250.9592 | 332.0364 | 8839.5509 | 175.5473 | 502.0030 | 6 |
| 50000-hybrid | 3933.2664 | 2.2858 | 164.8333 | 3071.7994 | 172.2547 | 522.0932 | 0 |
| 50000-baseline_a | 11266.8174 | 274.1458 | 419.8177 | 9708.5695 | 333.8041 | 530.4803 | 7 |
| 99000-hybrid | 7491.7626 | 2.2016 | 173.9983 | 6029.3809 | 231.3323 | 1054.8495 | 2 |
| 99000-baseline_a | 9905.1376 | 631.3216 | 305.1879 | 7644.3118 | 194.2698 | 1130.0465 | 3 |
| 99000-baseline_b | 10452.4136 | 655.7035 | 530.8605 | 7856.4504 | 203.9223 | 1205.4769 | 3 |

[Fixed policy](benchmarks/hybrid-cycles-075/policy.json), [frozen plan/hashes](benchmarks/hybrid-cycles-075/cohort-policy.json), [paired audit and all gates](benchmarks/hybrid-cycles-075/model-audit.json), [case index](benchmarks/hybrid-cycles-075/model-results.json), [full inventory](benchmarks/hybrid-cycles-075/fixture-inventory.json), [stage profile](benchmarks/hybrid-cycles-075/stage-profile.json), [build proof](benchmarks/hybrid-cycles-075/build-proof.json), [design](benchmarks/hybrid-cycles-075/DESIGN.md), [reproduction](benchmarks/hybrid-cycles-075/REPRODUCE.md) and [next work](benchmarks/hybrid-cycles-075/NEXT_WORK.md) retain the result and its limits. Raw commands/stdout/stderr are under the case index's sibling raw directory.

The generated benchmark-helper-derivation record predates three additional FILES entries in the final harness freeze list. Its initial SHA remains preserved; [harness finalization](benchmarks/hybrid-cycles-075/harness-finalization.json) proves that this list extension is the exact only difference. The authoritative final harness SHA is in cohort-policy.json. No workload, gate or observation changed.

To make space before 075, only 6,420 duplicate 073 working fixture files (1,120,068,012 logical bytes) were removed after full local SHA/ZIP member/CRC verification and fresh confirmation of all 120 private server asset digests. The original complete 073 ZIP (SHA `86d6a0dcf65d66df01134066d30a0281414557945262f5dcbb414ed2ef884d80`), raw logs/inputs/source/binaries/policy/report remain intact. Reproduce 073 by extracting its original complete ZIP into a fresh directory. [Scoped plan](benchmarks/hybrid-cycles-075/fixture-reclamation-plan.json) and [result](benchmarks/hybrid-cycles-075/fixture-reclamation-result.json) preserve the check. No 075 store is removed.

The next unimplemented hypothesis is a reader that validates/reuses each anchor body once while preserving exact parent/count/source/duplicate validation and fail-closed recovery. Qualify changed recovery with full histories, retries, error/kill/corruption cuts before fresh balanced recovery timers. Median publication overhead requires separate investigation; recovery optimization cannot claim to fix it. Any actual engine design still needs legacy-chain migration, exclusive ownership, segment publication/SQL, service concurrency, compaction/pinned readers/reclaim and a durability contract.

DuckDB/PostgreSQL/other-engine standings are unchanged. This trial does not measure SQL superiority, Facebook-scale activity, production readiness or PostgreSQL replacement. Supported 0.3.16 and the frozen morning report remain unchanged. English only; this computer only; no deployment or messages to others.
