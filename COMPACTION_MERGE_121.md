# Bounded compaction merge 121 — October 10, 2026

**Promising component improvement; not release-qualified. Supported 0.3.16.**
Compaction merges contiguous slices from sorted immutable runs, keeping ordered
input and bounded fallback to the old sort for fragmented inputs. Selection,
limits, reads, CRCs, durable publication, receipts and ACK placement are unchanged.
Source starts directly from supported 0.3.16; rejected 119/120 changes are excluded.

Fresh local checks: 154 baseline and 324 candidate successful tests (478 total),
three strict lint modes, two excluded independently checked smokes. A new unit
test incorrectly expected bulk merge for one-row tie interleaving; original
17-pass/one-fail attempt is preserved as failed-test-v1.rs. Test-only v2 uses
64-row tie blocks; engine algorithm unchanged. All 216 balanced cases independently
passed complete row multiset, indexes, receipt digests/generations, cold recovery
and 169,869,312 CRC bytes (7,077,888 rows). Pinned snapshots and damaged-input
rejection pass. This is not physical power-loss qualification.

32 runs*1,024 rows*three BIGINT columns per case;12 rounds, all six A/B/C
orders in both halves, identical A/B binary, same physical D:, warm OS cache
possible. Entire compact_small call charges input reads/CRC, preparation,
output writes, syncs and catalog publication. Setup/checks/reclaim/reopen are
outside component timing. No service/SQL throughput or competitor claim.

| Input | Baseline median ms | Candidate median ms | Paired C/A | A/A |
| --- | ---: | ---: | ---: | ---: |
| ordered | 6.0553 | 6.1698 | 1.0573 | 1.0455 |
| clustered | 6.8019 | 6.0446 | 0.8800 | 0.9814 |
| interleaved | 7.2606 | 7.5377 | 1.0207 | 1.0296 |
| duplicates | 6.7032 | 6.4444 | 0.9864 | 0.9726 |
| late | 6.9097 | 7.4606 | 1.0697 | 0.9292 |
| extreme | 7.5547 | 6.3776 | 0.8546 | 0.9916 |

Clustered wall is 12.00% shorter; preparation 35.59% shorter (2.34365->1.35305 ms,
paired C/A .644053). Both goals/controls pass full and both halves:
first_half wall_ms: C/A 0.9014, A/A 0.9834; first_half prepare_ms: C/A 0.6441, A/A 1.0509; second_half wall_ms: C/A 0.8800, A/A 0.9814; second_half prepare_ms: C/A 0.6188, A/A 0.9118. Ratios use within-round pairs, not the quotient of displayed medians.

**Nine/72 controls and three/72 guards fail.** Guard failures: ordered first_half catalog_sync_ms +10.81% (A/A 1.002); clustered second_half catalog_sync_ms +10.34% (A/A 0.986); late first_half wall_ms +11.06% (A/A 0.941).
All three guard controls pass; causal attribution to the merge is unproven.
Other failed controls mostly involve sync stages, plus second-half ordered
preparation and extreme inputs. All whole-case p50/p95/p99/max and every failed
scope were evaluated; no selected rerun. Original 324 Native/252 service/full
release gates remain outstanding for this change.

Next: bound unsuccessful planning earlier using actual observed slice density;
then qualify whole-engine/service/recovery behavior. Do not adopt this trial
or relax the failed guards. Raw fixtures follow the user's short-Markdown
retention policy after private save. [Reusable source](experiments/compaction_merge_121/README.md).
Source commit: `31488d67f97b5f1f281cf39b4ea14d48821ff460`.
Policy SHA256: `c28ee1d6e35dd1708dfb5c095d3004f6fab8b19276085cf6435ffcd84d41629c`.
Raw case journal SHA256: `57c20c256c8c9de55688bd6cdabd21e674b9e2d9150b6fb169167de354e1c373`.

Primary design references: [Rust heap](https://doc.rust-lang.org/std/collections/struct.BinaryHeap.html),
[benchmark interleaving](https://github.com/google/benchmark/blob/main/docs/random_interleaving.md).
