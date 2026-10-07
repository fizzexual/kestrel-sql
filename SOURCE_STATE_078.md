# Validated source-state projection 078

**The development metadata writer removes whole-ledger cloning from new source publication and passes 57 debug tests, 57 release tests, 15 injected write errors, 15 controlled process kills and 30 independent corruption cases. All 201 original-history files remain byte-identical. No new latency/throughput measurement or supported-engine adoption is claimed. KestrelSQL 0.3.16 is unchanged.**

## What changed and why

The fresh [077 profile](RECOVERY_COMPARE_077.md) identified substantial outer publication overhead: at99K receipts the candidate's residual was about53% of total publication time. That residual includes digest/batch preparation, source-ledger cloning and other work; it does not isolate source CPU or a physical filesystem cause. The old writer cloned the whole receipt ledger to validate each new reserved source ID. Source lookup separately rebuilt source positions using the reserved-ID range; it did not scan every ordinary receipt. 078 removes that avoidable work.

The Hybrid writer holds a private BTreeMap of at most4,096 validated source positions: first/next offset, last generation and committed interval count. Import/open capture an already strictly validated positions result. The ledger remains authoritative; all full recovery validation calls stay, and summaries still reconstruct the authoritative positions. The projection is neither persisted nor shared.

Before any IO or generation reservation, one pure preflight validates the new reserved ID against that bounded state. Grammar, lowercase hex widths, advancing intervals, next-offset continuity, increasing generation and4,096-source budget match the unchanged full validator. New publications have generations newer than the prior history, so appending at the validated next boundary is equivalent to full ledger validation. Direct reserved-ID commits and internal publications use the same helper. Already acknowledged IDs retain exact digest/row collision checks and return their original generation.

The prepared single Position is installed only after durable publication succeeds. Write errors poison the writer while leaving its old in-memory ledger/projection intact, including unknown outcomes after rename. Reopen reconstructs the complete durable history; retries preserve acknowledgement generations and cannot double-advance a source. Magic, caps, CRC, schemas, receipt/page/head fields, sync counts and076 anchor-body reuse remain unchanged.

## Before/after work, without a speed claim

| Work for a new source publication | Qualified076 | Candidate078 |
|---|---|---|
| Clone complete ordinary/source receipt ledger for preflight | One whole-ledger clone | Zero whole-ledger clones |
| Reconstruct current source position in source() | positions() over reserved receipts | One validated projection lookup |
| Validate the proposed reserved receipt | Full cloned-ledger source reconstruction | One bounded source preflight |
| Update source state after success | Reconstructed on subsequent use | Install one prepared Position |
| Strict import/recovery/source validation | Full authoritative validation | Same full authoritative validation |
| Persisted files and synchronization | Original protocol | Byte-identical protocol |
| Fresh latency, requests/s, extra process memory | Existing077 measurements only | Not measured in078 |

These are source-path and correctness assertions, not milliseconds saved. A source map has additional live memory and must be charged in the next comparison. Main has exactly two disclosed output-metadata substitutions so hybrid truthfully reports fully charged incremental validation; main's workloads, CAT4 models, digests, IO and all old tests are unchanged. [Source proof](benchmarks/source-state-078/source-finalization.json), [design](benchmarks/source-state-078/DESIGN.md), [original sources](benchmarks/source-state-078/original-076-model/src/hybrid.rs), [candidate](benchmarks/source-state-078/model/src/hybrid.rs).

## Fresh correctness and durable retry results

- ✅ All57 debug and57 release tests, four formatting checks, strict all-target Clippy and the release build pass. Every previous49 test remains. Eight added regressions cover more than1,200 distinct proposals from1,600 deterministic iterations against the unchanged full ledger validator, real two-cycle source interleaving/reopens, malformed/direct reserved IDs, gaps/overlaps/prepends, the4,096/4,097-source boundary, u64 offset limits, source error cuts and empty-publication cycles.
- ✅ The new native source-cut test exercises all11 delta/checkpoint error cuts with the old projection unchanged on error, a poisoned writer, complete old/new durable reconstruction and exact retry behavior. This is exercised in both native test modes. External qualification separately reruns15 errors and15 owned process kills: four anchor, four ordinary delta and seven reserved-source checkpoint cuts per mode. Every killed child observes its exact CUT line and is killed/waited through its own Popen handle.
- ✅ Original generation129 inputs have126/50,126/99,126 receipts. Each history adds64 real publications:56 ordinary receipts and eight contiguous source intervals, crossing two32-publication checkpoints. Native summaries and independent Python full ledgers agree. Python directly reconstructs all195 retained historical heads. A separate511-entry partial-page template crosses into a512+31 two-page source checkpoint. Native opens occur at the stated group boundaries and targeted tests; not every historical head is separately opened natively.
- ✅ Old ordinary/source retries return their original acknowledgement generations. Content collisions and source gaps perform no IO; abandoned generation numbers are skipped. All15 errors and15 process kills preserve complete old/new state and retry behavior. This is controlled process interruption qualification, not physical power-loss qualification.
- ✅ All30 altered stores fail both unchanged independent Python and the candidate:11 delta, ten checkpoint and nine valid-CRC malformed-anchor cases. Semantic validation remains mandatory despite valid CRC.
- ✅ Every one of201 files in the three original histories matches completed074 by full SHA-256, including full anchors, delta/checkpoint heads and pages. 242 external native commands,484 raw streams, no child timeout, and an empty post-qualification task-process check are preserved. Completed at `2026-10-07T16:40:43.422864+00:00`.

Frozen candidate binary SHA-256: `f22b8fd8bb4e798d3aa69cc54f49a0d6fc757659c729a0aefafc786ffda54f6a`. [Build proof](benchmarks/source-state-078/build-proof.json), [new tests](benchmarks/source-state-078/model/src/source_state_tests.rs), [frozen policy](benchmarks/source-state-078/qualification-policy.json), [full results](benchmarks/source-state-078/qualification-results.json), [raw audit](benchmarks/source-state-078/qualification-audit.json), [publication equality](benchmarks/source-state-078/publication-byte-equivalence.json), [external fixture hashes](benchmarks/source-state-078/fixture-inventory.json) and [process check](benchmarks/source-state-078/post-qualification-process-check.json).

## Latest measured timings remain077

The following are older077 measurements repeated for context, not078 results. Workload: same-process anchor-terminated opens after31 publications, six balanced rounds at each original receipt count; OS cache may be warm. Ratios are medians of matched per-round ratios, not division of displayed variant medians. Before is unchanged075 hybrid, after is qualified076 reader.

| Original receipts | Before anchor p50 ms | After anchor p50 ms | Paired after/before | Identical-control ratio | Outcome |
|---:|---:|---:|---:|---:|---|
| 126 | 4.66665 | 4.23635 | 0.944242 | 1.015856 | Guard passed; no declared speed goal |
| 50,126 | 120.183 | 57.8616 | 0.484639 | 1.011437 | ✅ Large anchor goal;6/6 wins |
| 99,126 | 238.60275 | 114.6381 | 0.481159 | 1.005975 | ✅ Large anchor goal;6/6 wins |

❌077 still fails four candidate guards and two identical-control checks. The99K publication p50/p99/max ratios1.062406/1.119724/1.185102 exceed their limits with passing controls; the small checkpoint-plus31-deltas p99 ratio1.102692 also fails. Candidate078 has not been measured against those guards. The [075 CAT4 adoption rejection](HYBRID_CYCLES_075.md), older stalls and every raw observation remain visible.

## DuckDB wins and losses: unchanged historical evidence

No competitor ran in078. These are prior completed workloads with their original interface/durability limits, not new source-state standings.

| Preserved comparison | Kestrel | DuckDB | Outcome |
|---|---:|---:|---|
| Supported016 warm analytical subset,60 shapes | 60 median wins | 0 median wins | ✅ [046 matrix](PERFORMANCE_046.md); selected aggregate subset, different API boundaries |
| Supported016 mixed service p99,64 clients/2,000 offered per second/three8-second rounds | 39.208 ms | 75.798 ms | ✅ [047 mixed service](SERVICE_047.md) |
| Same service read p99 | 1.205 ms | 75.698 ms | ✅047 read latency |
| Same service append p99 | 412.905 ms | 81.148 ms | ❌047 append latency |

The later isolated [061 candidate](CORE_READ_PATH_061.md) also recorded60/60 analytical median wins, but failed10/29 service guards and is unpromoted. Supported016's [047 minute soak](SERVICE_047.md) lost15,925/30,000 offered requests. These losses remain material. 078 metadata qualification establishes no general SQL ranking, PostgreSQL replacement, Facebook-scale qualification or production readiness.

## Failed attempts and disk evidence

The first native attempt passed57 debug and57 release tests, then strict Clippy rejected three new test expressions using modulo instead of is_multiple_of. Only those three test expressions changed; candidate hybrid implementation bytes stayed identical. The exact first source, logs, failure, run order and full native fixture trees remain. The complete second attempt passed every check. [First failure](benchmarks/source-state-078/build-logs/attempt-1/FAILURE.txt), [first Clippy log](benchmarks/source-state-078/build-logs/attempt-1/clippy.log), [repair proof](benchmarks/source-state-078/lint-repair.json), [second order](benchmarks/source-state-078/build-logs/attempt-2/run-order.json).

Between attempts the unchanged2.5GB build disk guard rejected one launch before a new attempt directory or child. The exact error is retained. A subsequent read met the same guard; it was not lowered. No observed external case was rerun and no correctness repair to the implementation was needed. Formatting tools emitted a canonicalization warning for C:/Users/Frizer with successful exit codes; all actual formatting checks passed. [Disk-guard failure](benchmarks/source-state-078/build-disk-guard-failure.txt), [format note](benchmarks/source-state-078/standalone-format-note.txt).

To retain headroom, 32,401 completed duplicate fixture/regenerable cache files totaling 1,508,330,087 logical bytes were removed only after exact path, inventory, member SHA, full archive CRC/SHA and private publication verification. This includes076 external/native duplicates,077 primary timed-store duplicates,074 native duplicates, and072/073 compiler/native directories. The original full archives, raw streams, sources/binaries, inputs, policies and reports stay. Restore the former working stores from complete private archives into a fresh directory.074 external byte-reference histories stay available. Disk free space fluctuated during the run; no physical cause or equal amount of free-space gain is claimed. [076/077 proof](benchmarks/source-state-078/reclamation-plan.json), [result](benchmarks/source-state-078/reclamation-result.json), [074 proof](benchmarks/source-state-078/reclamation-074-plan.json), [result](benchmarks/source-state-078/reclamation-074-result.json), [072/073 proof](benchmarks/source-state-078/reclamation-older-plan.json), [result](benchmarks/source-state-078/reclamation-older-result.json).

## Next work and preservation

The next step is a fresh balanced076/076/078 comparison, fully charging source validation and additional memory. Guard ordinary/publication tails, source tails, recovery paths, migration and small-store behavior; preserve every failed calibration and stall. [Pre-cohort requirements](benchmarks/source-state-078/NEXT_WORK.md), [reproduction](benchmarks/source-state-078/REPRODUCE.md). There is no compilation or heavy job during timed workloads. Only this computer is used.

All complete native fixtures from both attempts, external/input/error/kill/corruption fixtures, raw streams, model/control/released sources, binaries,22 locked crates and failures are bundled in disjoint bounded ZIP parts with per-member and whole-file hashes. Part1 contains tools/raw/source/binaries/inputs; every part is needed for full fixture restoration. [Complete fixture inventory](benchmarks/source-state-078/bundle-fixture-inventory.json), [preservation proof](benchmarks/source-state-078-preservation.json). Supported engine0.3.16, all20 engine releases/tags, previous results and the frozen morning report remain unchanged. English only; no deployment or messages to others.

Complete private Git evidence:

- [kestrel-sql-development-078-source-state-evidence-part-1-of-3.zip](benchmarks/kestrel-sql-development-078-source-state-evidence-part-1-of-3.zip).
- [kestrel-sql-development-078-source-state-evidence-part-2-of-3.zip](benchmarks/kestrel-sql-development-078-source-state-evidence-part-2-of-3.zip).
- [kestrel-sql-development-078-source-state-evidence-part-3-of-3.zip](benchmarks/kestrel-sql-development-078-source-state-evidence-part-3-of-3.zip).

[Whole-file hashes, full ZIP checks and extraction layout](benchmarks/source-state-078-bundle-check.json) and [private publication records](benchmarks/source-state-078-publication.json) identify every archive and sidecar. All parts are required to restore complete fixtures. The report inside part1 precedes these repository publication links. No release-asset upload was attempted in 078; all 122 older assets and 20 engine releases/tags remain unchanged, and the 076 upload remains pending.

[Post-package remote verifier](benchmarks/source-state-078-finalization/verify_git_remote.py) and [addition proof](benchmarks/source-state-078-finalization/finalization-proof.json) are repository-only additions after the three immutable ZIPs. They check matching local/remote main, archive and sidecar blob SHA/size, private repository status, unchanged older release digests/tags, supported core and the frozen morning report. They introduce no native or timed workload and do not change the original qualification payload.
