# Actual Archive comparison133 — October12,2026

**Controlled clustered whole compaction is10.80% lower and publication
preparation29.37% lower, passing both goals/controls in full and both halves.
Overall component qualification FAILS:7/72 identity checks and1/72 guard fail.
Supported0.3.16 is unchanged;0.3.17 remains unreleased.**

This is the combined [phase131 candidate](COMPACTION_PHASE_131.md) versus exact
supported016, not an isolated131-versus127 effect. All actual inputCRC/read,
phase selection, publication indexes and durable segment/catalog syncs are
charged. No SQL-query/service/competitor ranking or physical power-loss claim.

All216 native cases, controller, both owned safety workers and independent
auditor actually exited0. Independent exact payload/index/original receipt/
generation audits checked7,077,888 rows/169,869,312
CRCbytes; native retry/pins/reclaim/cold reopen checks pass. Baseline154 tests,
candidate340 tests/twolints are REUSED. Six excluded fresh correctness stores
also pass196608rows/4718592CRCbytes. No fresh Rust build/test was run in133.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Before/after p95 ms | Paired prepare change | Wall/prepare full+halves |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| ordered | 5.38095 | 5.55785 | +3.38% | 5.8252/62.6484 | +2.89% | pass |
| clustered | 6.10295 | 5.48780 | -10.80% | 6.3937/6.8120 | -29.37% | pass |
| interleaved | 6.70725 | 6.86050 | +3.20% | 7.0204/12.8643 | +5.46% | pass |
| duplicates | 6.16215 | 6.19325 | -0.89% | 6.4709/6.5179 | +2.62% | pass |
| late | 6.33435 | 6.23740 | +0.39% | 6.6658/34.3066 | +2.44% | pass |
| extreme | 6.34870 | 5.89415 | -5.83% | 7.0944/6.2370 | -27.35% | pass |

Changes use medians of within-round C/A ratios, not quotients of displayed
medians. All samples/stalls retained. With12 samples/variant, nearest-rank
p95/p99/max coincide; tails are descriptive and were not predefined component
median guards. Ordered candidate62.6484ms includes59.0192ms segment sync.
Late candidate34.3066ms includes18.4310ms segment sync and12.3182ms catalog sync.
Identical baselineB also stalled54.4245ms (50.3046ms segment sync) and54.2706ms
(49.1301ms segment sync). The largest intervals are measured inside sync calls;
this does not prove an exclusive physical-disk cause. These material tails
and failed sync controls remain outstanding; do not remove flushes or hide them.

| Clustered scope | Whole C/A | Whole A/A | Prepare C/A | Prepare A/A | Both goals/controls |
| --- | ---: | ---: | ---: | ---: | --- |
| full | 0.892009 | 0.987365 | 0.706346 | 0.985433 | pass |
| first_half | 0.882912 | 0.982348 | 0.701281 | 0.990747 | pass |
| second_half | 0.929385 | 1.033951 | 0.708309 | 0.975281 | pass |

Clustered goals are whole<=.95/prepare<=.90, controls[.90,1.10], guard<=1.10.
All72 complete full/both-half checks across whole/prepare/segment-sync/catalog-
sync were evaluated. Every failed control is a sync check; the only failed
guard is extreme first-half catalog-sync C/A1.143669 with failed A/A1.153175,
so that regression is inconclusive. [All8 failed checks](experiments/compaction_compare_133/FAILED_CHECKS.md).

One predeclared randomized balanced12-round/six-shape schedule,RNG20261011,
32x1024rows/three columns, same physicalD, ownedCPU8 and120 continuous observed
clear seconds after prep/freezes. Same byte-identical A/B. Before/after every
case the metadata worker checked actual reset/task/supervisor/global build
state, blocked on stdin during native lifetimes. Zero between-case pauses,
zero selected retiming/outlier rejection/timeouts. Frozen bytes and probe
boundaries all pass. Snapshot observations cannot exclude every brief hidden
task; no app/global setting changed. Original release324Native/252service/
42goals/153AA/171guards plus correctness/recovery/sustained qualification remain.

Candidate SHA256:`d0bbe3f1899b333c87494d70eeaae1e5e4a65cd1dde7cf21b38c78de9c6336b5`.
Policy SHA256:`937e67b8969a62273c289fa837f59419588df984362caabf29128191184f4641`.
Journal SHA256:`080f961f0b7c56fd0118903e87e00ff6a93e880cb42549f2cf8312d35aaf7324`.
[Actual immutable controllers/decoder reproduction](experiments/compaction_compare_133/README.md).
Next investigate bounded write-mode/buffer scheduling with every write/flush
charged and unchanged sync/ACK/format requirements. Microsoft describes the
[buffer/flush interaction](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers);
it does not promise a Kestrel speedup. No prior102 failure is erased. Concise
outcome/useful source freshly verified privately before scoped completed fixture
cleanup; no raw bundle or old remote history/ref/release deletion.
