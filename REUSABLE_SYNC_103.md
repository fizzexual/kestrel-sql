# Reusable synchronization worker 103

The isolated worker passes the declared correctness and recovery gates, with exact restored replay. It reuses one owned thread across publications while preserving both durable flushes and completion before rename/ACK. Performance has not been measured. Supported **0.3.16** remains unchanged; **0.3.17 is unqualified** and has no release date.

The source observation motivating this trial is concrete:101 creates and joins a scoped thread on each publication. Trial102's complete native and service qualifications fail despite numerical full-cohort gains; those failures remain [fully preserved](PARALLEL_SYNC_SPEED_102.md). Its higher service CPU ratio is diagnostic, without a physical-cause claim.103 tests a separate reusable-worker hypothesis; it does not reclassify102 or establish a speed gain.

## Change and preserved contracts

Opt-in `reusable-sync-103` implies `parallel-sync-101` and selects a third publication function in isolated `work/perf-103/source-v3`. The complete original normal and101 publication function bodies remain byte-exact; dependency lock/version, source/receipt/digest/retry/format, reclaimer, queue and reader contracts stay unchanged. Supported repository source is not adopted from this trial.

One worker starts lazily for each Archive. Private zero-capacity request and capacity-one completion channels admit one owned, completely written/flushed original segment File. A checked monotonic ticket identifies the reply, which returns the same File after all job work. The catalog is encoded/written/synced concurrently. Both original `sync_all` calls must succeed and a matching completion must arrive before unchanged catalog rename and ACK. Stop/drop closes admission and actually joins the thread before the Archive lease field drops; snapshots keep their existing lease and pin behavior. Archive and ArchiveSnapshot retain Send/Sync. No unsafe code, OS-handle duplication, global pool, unbounded queue or silent fallback is added.

A completed job and an exited thread are distinct. Success permits an idle owned thread; it does not pretend a per-publication join occurred. The legacy external fault label `sync_joined` means received job completion in103. Thread exit and actual join are independently controlled on stop/drop and failure. Overlapping stage wall clocks are not an exclusive CPU/IO decomposition. Channel and join semantics follow the [Rust bounded-channel](https://doc.rust-lang.org/std/sync/mpsc/fn.sync_channel.html) and [actual join](https://doc.rust-lang.org/std/thread/struct.JoinHandle.html#method.join) contracts.

## Fresh validation

| Check | Result |
| --- | ---: |
| Current source tests:9 exact-feature suites |916 passed|
| Strict all-target lint modes |6 passed|
| Coupled retirement/publication cases |832 passed|
| Ordinary publication error/exit cases |104 passed|
| Source-position error/exit cases |26 passed|
| Corruption rejections |22 passed|
| Old-format controls |CAT2/CAT3 passed|
| Normal/candidate exact byte fixtures |74 and70,001 rows;4 fixtures passed|
| Qualifying external Native commands |13,129|
| Coupled ACK batches |53,456 reconciled|
| Unacknowledged committed batches |16 retained and reconciled|
| Competing writer ownership rejections |6,240|
| Retained archive unit stores |490 decoded|
| Owned-file protocol unit fixtures |30 verified|
| Full independent reference CRC bytes |144,640,896|

The matrix includes all original576 coupled cases plus256 new protocol boundaries:request admission, worker receipt, completed sync job and prepared reply. Both anonymous/named histories, catalog/retired kinds, ordinals1/20, before/after deletion, append/compaction and error/exit modes are complete. Five cold/ownership readers include normal, existing101, incremental, new103 and the exactly reused supported016 binary. Original receipt generations/digests, source positions, ACK and ambiguous rows, retry mismatch, readable pins, corruption and old formats are checked independently. Both small and70,001-row normal/candidate stores match byte-for-byte and cross-reopen/retry correctly.

Deterministic real-worker controls exercise both completion orders, eight publications on one thread while alternating order, at most one active job, original File cursor/bytes, idle and active drop/join, lease lifetime, errors/unwind on both sides, spawn failure, handoff/reply disconnection, wrong tickets, root panic and ticket exhaustion. No early rename or ACK is accepted.

The first preparation stopped on an initializer assumption before candidate write/build/Native; its pristine42-file source and extracted complete tool stderr remain. Source-v2 then passed916 tests and3 strict lints before candidate-lint rejected an unused test-only control. The repair changes only the new test module to alternate actual completion order across eight jobs; every production byte remains identical. Both full source/target/tmp/test/log snapshots remain. The1832 actual test executions include the916 passing tests from this rejected first build, reported separately from the916 current qualifying tests. An ordinary default-sandbox auditor-copy denial and approved identical retry are recorded; no automatic approval rejection occurred.

## Preservation and limits

All18 bounded ZIP parts restore **147,703 files**, **9,589 directories** and **1,445,080,037 logical bytes**. The previously qualified64MiB chunk/80MiB logical-part engine is reused byte-exact. Every member CRC/order/size/offset, every complete original/restored SHA and exact file/directory set pass before and after pure restored replay. All dependencies are imported from the restored tree; replay equals the complete original audit and launches zero Native processes or performance timers. Only inventoried regenerable target/Python caches are excluded, with originals retained. Both tmp trees and all successful/failed unit stores, raw stdout/stderr/stdin, markers, identities, receipts and helpers are included. Closed packager output is preserved separately after actual exit.

The original, restored and archived trees remain on D:. No103 remote backup has been verified and no recent raw material was deleted. The repository remains local/private in this work; no source was published. See [policy](benchmarks/reusable-sync-103/policy.json), [complete decision](benchmarks/reusable-sync-103/audit.json), [restored proof](benchmarks/reusable-sync-103/restored-audit-proof.json), [preservation proof](benchmarks/reusable-sync-103/preservation-proof.json) and [reproduction steps](benchmarks/reusable-sync-103/REPRODUCE.md).

This qualifies changed ordering and controlled error/process-exit recovery. It does not qualify physical power loss, actual resource exhaustion, sustained service, performance, competitor ranking or adoption. A new separately declared same-D balanced A/A comparison with full and independently balanced halves, all permutations and original latency/loss/rate/memory/disk guards and goals must test speed. Broad integrated analytical/scan/six-service/minute/overload/competitor/source/recovery and justified061 integration remain before .17. No universal benchmark win or release ETA follows.
