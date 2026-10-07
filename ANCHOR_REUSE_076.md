# Validated anchor reuse qualification 076

**The changed metadata reader passes qualification: 49 debug/release tests, 15 injected errors, 15 controlled process kills and 30 independently corrupted fixtures. Anchor-terminated recovery now reads/parses its anchor body once. No fresh latency cohort has run; supported KestrelSQL 0.3.16 is unchanged.** This is a development metadata reader, not an adopted SQL/storage release.

## Why this change

[075](HYBRID_CYCLES_075.md) preserved a rejected performance baseline: large metadata publication totals fell within its cohort, but nine guards and ten identical-control calibrations failed. Publication p50 was 22–25% slower; large-history recovery was 65–70% slower with passing recovery controls. Its unchanged 074 reader read the complete anchor body three times and parsed it twice when traversal terminated at an anchor. This trial removes that duplicate work while keeping validation and publication behavior.

The reader separates body validation from loading. Backward traversal validates the original anchor body already read and CRC checked, retains the owned parsed Legacy plus body CRC within that one open, and moves it into final reconstruction. Checkpoint-terminated recovery keeps its single referenced-anchor load/parse. There is no cross-open cache. All caps, highest-head fail-closed behavior, next-generation reservation, parent CRC/depth/checkpoint binding, counts, schema/receipts/digests, duplicate rejection, pages and source continuity remain.

Source comparison proves the complete moved validation/positions block is byte-identical, as are main/Cargo/common CAT4/workloads, hybrid publication/import/source methods and all 43 existing tests. Six new regressions are added. On-disk magic remains KANC0741/KHED0741/KDEL0741/KPAG0741. No publication or format change; every file in the three original 074 histories is byte-identical by full SHA.

## Before/after work counts, not latency

Before counts are original 075 source-path accounting; after counts are asserted by successful native test-only probes at 0/1/31/32/63/64 publications with 126 original receipts. A separate probe asserts every reachable head body is loaded once. Receipt pages use the common reader and are not included in that head-body probe. All probes are thread-local, opt-in and compiled only under cfg(test); the release binary has no probe overhead.

| Recovery termination | 075 anchor body reads | 076 anchor body reads | 075 anchor parses | 076 anchor parses |
|---|---:|---:|---:|---:|
| Original anchor / anchor after 1 or 31 publications | 3 | 1 | 2 | 1 |
| Checkpoint after 32 / checkpoint plus deltas after 63 / checkpoint after 64 | 1 | 1 | 1 | 1 |

✅ Duplicate anchor work is removed on the anchor path. This is structural verification. **No milliseconds, recovery speedup, SQL throughput improvement or correction of the publication p50 regression is claimed.** The unchanged checkpoint path remains separately guarded in future measurements.

## Correctness and durable retry qualification

- ✅ All 49 debug and 49 release tests, three format checks, strict all-target Clippy and release build pass. Forty-three retained tests exercise previous bounded page/CAT4/hybrid/integration behavior; six new tests exercise body reads/parses, source retries on both termination paths, malformed anchor JSON/schema/receipt/source semantics, unchanged parent/checkpoint binding and pending generation reservation. This is the changed binary's qualification, not reused old pass counts.
- ✅ Original generation-129 histories with 126/50,126/99,126 receipts import exact complete anchor bodies and add 64 actual receipts each: 56 ordinary and eight contiguous source intervals. Native summaries and independent Python full ledgers agree. All 195 retained historical head versions are directly reconstructed in Python; native opens are checked at group boundaries and in the targeted regressions, not at every individual historical version.
- ✅ Old ordinary/source retries retain original acknowledgement generations; conflicting content and source gaps create no files. A partial 511-entry tail crosses into 512+31 entries under the checkpoint-cut template.
- ✅ All 15 error cuts and 15 owned process kills pass complete old/new-ledger/source checks, poisoned writer rejection, abandoned-generation reservation and exact acknowledged retries. Each kill observes its exact CUT line, kills only its Popen child and waits. These are fresh affected qualification cases on the changed reader; original 074 results remain separate.
- ✅ Thirty deliberately altered fixtures fail both the changed native reader and unchanged independent Python: 11 delta, ten checkpoint and nine new valid-CRC malformed-anchor cases. The new cases cover unknown/missing/duplicate fields/receipt keys, anchor generation, receipt_base, receipt generation, source gap and empty schema. Correct CRC cannot bypass semantics.
- ✅ All 201 original-history files match completed 074 by full SHA, including anchors, delta/checkpoint heads and pages. All changed-reader full fixtures and command/raw streams are retained. Publication/import/source/commit behavior and bytes remain unchanged.

External native commands: 242; every owned child exited or was killed/waited. The post-qualification process check is empty. Frozen candidate binary SHA: `e9ef281a10ce46370b169ae8a6a98632837820b0fcc081c969fabd60f88ab37b`. This qualification is untimed; it does not qualify physical power loss, real segments/SQL, legacy-chain migration, exclusive ownership, service concurrency, compaction/pinned readers/reclaim or supported-engine adoption.

## Disk guard and preservation

The first external qualification launch stopped at the unchanged 2.5GB disk guard with about 2.02GB free, before any child, policy, input/raw/fixture directory or observation. The exact failure and original process check remain. After verification, the same qualification was started once with sufficient space; no observed case was rerun, no gate was lowered and no source/binary fix was required.

Only regenerable completed 074/075 compiler caches were initially removed: 1,693 files / 467,297,468 logical bytes. Their full source/binary/crate archive members, whole archive SHA/CRC and all 122 private server asset digests were checked. Then 3,546 duplicate 075 primary working fixture copies / 1,035,929,214 logical bytes were removed after full local/member hashes, all ZIP CRC and another fresh verification of all 122 server digests. Native PowerShell checked exact resolved targets within this task, every inventory/hash and absence of reparse points. Old full archives, logs, source/binaries, inputs, policies and reports stay unchanged; restore 075 full primary stores from its original immutable ZIP into a fresh directory if needed. No 076 fixture is removed.

[Design](benchmarks/anchor-reuse-076/DESIGN.md), [source proof](benchmarks/anchor-reuse-076/source-finalization.json), [build](benchmarks/anchor-reuse-076/build-proof.json), [frozen qualification policy](benchmarks/anchor-reuse-076/qualification-policy.json), [full qualification results](benchmarks/anchor-reuse-076/qualification-results.json), [fixture inventory](benchmarks/anchor-reuse-076/fixture-inventory.json), [publication byte equality](benchmarks/anchor-reuse-076/publication-byte-equivalence.json), [operation counts](benchmarks/anchor-reuse-076/operation-count-check.json), [disk failure](benchmarks/anchor-reuse-076/qualification-disk-guard-failure.txt), [cache plan](benchmarks/anchor-reuse-076/cache-reclamation-plan.json), [cache cleanup](benchmarks/anchor-reuse-076/cache-reclamation-result.json), [duplicate plan](benchmarks/anchor-reuse-076/fixture-reclamation-plan.json), [duplicate cleanup](benchmarks/anchor-reuse-076/fixture-reclamation-result.json), [reproduction](benchmarks/anchor-reuse-076/REPRODUCE.md) and [next work](benchmarks/anchor-reuse-076/NEXT_WORK.md) preserve the result and limits. Raw commands/stdout/stderr are under the results' sibling raw directory.

Next freeze a fresh balanced matched recovery benchmark with two identical unchanged 075 hybrid controls and the candidate. Guard anchor- and checkpoint-terminated opens separately, keep source tails/memory/publication checks and every calibration/stall/failure. Narrow recovery qualification does not erase 075 adoption failures or fix publication p50.

DuckDB/PostgreSQL/other-engine standings are unchanged. No SQL superiority, Facebook-scale qualification, production-readiness or PostgreSQL-replacement claim. Supported 0.3.16 and the frozen morning report remain unchanged. English only, this computer only; no deployment or messages to others.

Complete private repository evidence:

- [kestrel-sql-development-076-anchor-reuse-evidence.zip](benchmarks/kestrel-sql-development-076-anchor-reuse-evidence.zip).
- [kestrel-sql-development-076-anchor-reuse-evidence.zip.sha256](benchmarks/kestrel-sql-development-076-anchor-reuse-evidence.zip.sha256).

Two gh release uploads and one direct binary API upload returned HTTP 500. Each authoritative remote query found no new asset and verified all 122 older assets. The complete unchanged ZIP and sidecar are therefore preserved directly through private Git storage; the separate release-asset upload remains pending. [Failure/recovery evidence](benchmarks/anchor-reuse-076-finalization/completion.json), raw upload logs and recovery helper sources are retained. The original archive/source/binary/policy/raw/fixture evidence is unchanged; no observed case was rerun. These finalization files and archive links are repository additions after the immutable ZIP. All 20 supported engine releases/tags stay unchanged.
