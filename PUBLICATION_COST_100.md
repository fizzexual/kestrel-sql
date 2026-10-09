# Append publication diagnostic 100 — October 9, 2026

**Trial 100 is unqualified: one of 24 identical-baseline checks fails; all 24 profiling guards pass.** All 144 cases and independent data/history/lifecycle checks pass. First-half named append p99 B/A is **1.1144882804632776**, exceeding the fixed 1.10 limit. The complete rule requires both histories, full cohort and both halves, so passing other scopes does not qualify attribution or a code adoption. Supported 0.3.16 remains byte-exact; .17 has no qualification or justified date. No competitor or all-benchmark win is claimed.

This is a new append-only fixture, distinct from rejected 099 retirement polling. Existing original segment/catalog sync clocks show approximately 61% of summed seven publication stages and 62–70% of outer time in case p99-tail groups. All six numerical material-cost criteria pass, but their complete calibration prerequisite fails. These are descriptive wall-clock signals, with no exclusive physical disk/OS wait/CPU explanation or service p99 decomposition. No new inner clock or engine algorithm is introduced.

| History | Scope | Median case sync / seven stages | Median case tail sync / outer append | Scope calibration |
| --- | --- | ---: | ---: | --- |
| anonymous | full | 0.613244636 | 0.663436443 | pass |
| anonymous | half_0 | 0.614872138 | 0.690577936 | pass |
| anonymous | half_1 | 0.611361838 | 0.623156708 | pass |
| named | full | 0.611405041 | 0.652922138 | pass |
| named | half_0 | 0.614212322 | 0.702041068 | fail |
| named | half_1 | 0.607105528 | 0.618977851 | pass |

The policy was declared before implementation/build/Native/timing, SHA256 `1d6bf0787eaf04ace6f9581a1407d3e9d64b7aebb79d1d973c403ec9a99d8347`. The 144 cases form 24 rounds and two independently balanced 12-round halves, seed 10010, all six permutations twice per half/history and alternating history order. A/B repeat the same normal release probe with async-reclaim enabled. C additionally enables only the preexisting publication-trace feature and reads its last record after each append. No fault or writer-trace feature enters timed artifacts. All Archive/Live/worker/publication bodies remain exact 099 bytes; only a new example and Cargo declaration are added.

The API is original append_group with one IngestBatch. ID/columns are prepared outside the outer clock; command-vector construction and returned receipt are included uniformly in every variant. Every fresh three-column store seeds 32,768 rows, publishes 512 durable 100-row groups and ends with 83,968 rows/generation 513. There is no compaction, reclamation or async worker submission. All 513 catalog and segment generations are retained. Metadata/trace getters, queries, inventories, CRC, retries/collisions, snapshot/lease/cold-open controls and journal serialization/flushing occur outside append clocks; flushing is fixed every 128 groups. OS cache may be warm. This is finite native publication, not a Live service, CPU/RSS/resource-tail, sustained throughput or maximum capacity comparison.

Controls reuse the native diagnostic band of 092/099: B/A 0.90–1.10 and C/A <=1.10 for summed append and p50/p95/p99 in each history/full/half. Ratios are medians of per-round ratios; C/B remains diagnostic. Nearest-rank p99 selects the sixth largest of 512 samples, including every stall. The material criteria require median case sync-stage fraction >=0.50 and median case sync/outer fraction >=0.50 over every group at or above that case's outer p99, including ties, in all six scopes. No gate, comparator, durability, sample selection, round count or budget changes after observation.

| Completed checks | Result |
| --- | --- |
| Fresh normal debug/release suites | 90 + 90 tests pass |
| Fresh profile debug/release suites | 93 + 93 tests pass |
| Strict default/normal/profile/combined lints | All four pass |
| Main durable append publications / C stage records | 73,728 / 24,576 |
| Independent current payload CRC/index/NumPy references | 290,193,408 bytes; every final store passes |
| Main historical catalog envelopes/CRCs/references | 73,872 exact generations pass |
| Named current receipt records | 36,864 original generations and full digests pass, with all historical checkpoint/delta receipts checked |
| Existing profile reconciliation | All C stage sums/counts/histograms and published catalog byte totals reconcile exactly |
| Real snapshot/owner/reopen controls | Seed pin remains readable and retains writer lease after owner drop; actual last-owner drop permits cold reopen |
| Named retry/collision | Exact original generation 18, no new publication/data files; stale trace stays unchanged |
| Complete excluded native smokes / CLI-vs-SQLite queries | Four / 16 pass; all original/profile final data bytes identical |
| Independent smoke histories/current payload | 2,052 catalog generations / 8,060,928 CRC bytes pass |
| Invalid stage/clock/receipt/lifecycle/order fixtures | All 21 rejected with zero Native/performance timers |

All four append events above 100 ms remain in the raw cohort and quantiles:

| Zero-based case | History | Variant | Group | Outer ms |
| --- | --- | --- | ---: | ---: |
| 18 | named | baseline_b | 402 | 131.2253 |
| 68 | named | profiled | 420 | 134.2308 |
| 99 | named | baseline_b | 440 | 100.8830 |
| 99 | named | baseline_b | 441 | 114.2894 |

The traced 134.2308 ms event includes segment write 45.6297 ms, segment sync 45.0279 ms and catalog sync 42.6157 ms. Those observed operation intervals do not establish a physical-device cause, and the untraced stalls cannot be decomposed. No additional rounds or selective reruns were used. There were no build, Native, original audit or preservation failures; harmless guessed report/output listing read errors are retained separately and did not affect any source/raw/timing operation. Prior 096/097/094 fault matrices are reused explicitly, not counted as fresh 100 recovery tests. A production pipeline change would need fresh controlled recovery.

All 13,723 frozen pre-timing inputs remain unchanged. **18 bounded ZIP parts preserve 162,267 files / 1,935 directories / 1,435,443,997 logical bytes**. All original source/artifacts/Native journals/stdio/identities/statuses/history/stores/locks/unit fixtures/validators/helpers and closed logs remain D:. Only inventoried regenerable target/Python caches are omitted, with originals retained. The verified 64 MiB chunk / 80 MiB logical part engine is reused byte-exact. Every member CRC/order/offset/size, full original/restored SHA and exact file/directory set passes before and after a complete restored pure audit. Replay exactly recomputes all raw metrics/controls/stage/profile reconciliations/criteria, every historical catalog/current reference and smoke/SQL check with zero Native/performance-timer launches or existing-file changes. Closed packager stdout and post-cohort source-basis/read records are copied and hashed only after actual closure in closed-continuation.

Evidence: [policy](benchmarks/publication-100/policy.json), [complete decision](benchmarks/publication-100/decision-summary.json), [preservation](benchmarks/publication-100/preservation-proof.json), [restored replay](benchmarks/publication-100/restored-audit-proof.json), [reproduction](benchmarks/publication-100/REPRODUCE.md). Originals: D:\Codex\Kestrel\work\perf-100. Restoration: D:\Codex\Kestrel\work\restored-publication-100.

The next code hypothesis has a separate verified basis in qualified 091. A post-cohort static comparison verifies both frozen source hashes and proves the whole current publication body byte-identical to that earlier source (body SHA256 `7a260c1a0269fbd0b0d9cedf6d163fdac0f2e5a153a04d9e0e58054927be01a0`). 091 passed all 39 A/A and 39 profiling controls, and its recorded pooled synchronization fraction is 0.671987659 of summed stages. This reuses qualified earlier diagnostic scope and never reclassifies 100. A separately numbered candidate could test scoped overlap of independent segment synchronization with catalog preparation/write/synchronization, joining both before catalog rename and ACK. Both original sync calls, atomic publication, snapshots/lease, poison/unknown-outcome handling, source/receipt/retry contracts and bounded ownership must remain. Thread creation overhead and same-device contention may erase gains. It is only a hypothesis, not declared/implemented/measured/adopted by 100.

Declare a new experiment >=101 before implementation. Preserve the exact feature-disabled path, verify actual error/panic/join/lease behavior and execute fresh coupled publication/worker recovery, old formats/corruption/source/retries plus fair normal same-D native and service A/A/performance/resource checks before considering adoption. Do not repeat 098/099/100, select passing histories/halves, change limits or drop synchronization. Full native analytical/scan, six service profiles, mixed/write/minute/overload/competitor/source/retry/recovery/ownership/pins/resource/restoration and justified isolated 061 integration still precede .17. Repository/history remain private/local on this computer; the prepared reset stays waiting, no app force-quit or old task/automation reactivation, and completed C cleanup is not repeated.

Pre-commit inspection caught an old packager-log filename in the first generated commit draft. That draft was never executed and changed no report, navigation, staged file, commit, Native/source/raw/policy or gate. Its exact helper/generator/derivation bytes are retained in closed-continuation/draft-commit-v1. The corrected v2 helper copies the actual closed preserve-100.log and all post-cohort basis/read records; numerical rejection and frozen evidence are unchanged.
