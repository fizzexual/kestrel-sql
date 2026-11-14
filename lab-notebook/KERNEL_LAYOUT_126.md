# In-memory layout diagnostic 126 — October 10, 2026

**Clustered layout work improves; ordered layout regresses. Overall diagnostic
fails. Supported 0.3.16 is unchanged; 0.3.17 is unreleased.** This investigates
[125's unstable durable controls](COMPACTION_CONTROLS_125.md), using the exact
experimental [122 merge](COMPACTION_MERGE_122.md) and supported sort/gather kernel.
It measures in-memory layout only, excluding input reads/CRCs, indexes, syncs,
SQL/service and recovery. It does not establish durable compaction improvement.

Clustered full paired elapsed work is **62.46% lower** and raw thread cycles
**65.16% lower**. Both batch goals and their controls pass in the full run and
both halves. Ordered full elapsed guard regresses **12.27%** with passing full
A/A; second-half elapsed/cycle guards regress 14.60%/15.04%. Timing and code
layout effects are not separated. The existing ordered fast path still incurs
planning checks, motivating a caller bypass derived during charged input
collection, rather than another scan after concatenation.

| Input | Baseline 32-call batch median ms | Candidate median ms | Paired wall C/A | Paired cycles C/A | All full/half controls |
| --- | ---: | ---: | ---: | ---: | --- |
| ordered | 1.9420 | 2.8149 | 1.1227 | 1.0256 | FAIL |
| clustered | 99.8547 | 37.6224 | 0.3754 | 0.3484 | pass |
| interleaved | 103.0615 | 98.2274 | 1.0535 | 0.9701 | FAIL |
| duplicates | 53.3118 | 47.4575 | 0.9029 | 0.9431 | FAIL |
| late | 88.3559 | 81.7738 | 0.9448 | 1.0025 | pass |
| extreme | 88.1823 | 24.7588 | 0.3316 | 0.3430 | FAIL |

**10/72 A/A, 5/72 guards and 3/12 goals fail.** Four metrics are
batch wall/cycles and within-case p95 wall/cycles, across full/both halves.
A/A requires [0.90,1.10], guard C/A<=1.10, clustered/extreme batch goals<=0.90
with passing controls. Every case, sample, p50/p95/p99/max and failed scope was
evaluated without selected retiming. All failed checks: A/A ordered first_half batch_wall_ns 0.8827; A/A interleaved second_half within_case_p95_wall_ns 1.2720; A/A duplicates second_half within_case_p95_wall_ns 0.8293; A/A extreme full batch_wall_ns 0.8681; A/A extreme full within_case_p95_wall_ns 0.8764; A/A extreme first_half within_case_p95_wall_ns 0.8829; A/A extreme second_half batch_wall_ns 0.8326; A/A extreme second_half batch_thread_cycles 0.8570; A/A extreme second_half within_case_p95_wall_ns 0.8764; A/A extreme second_half within_case_p95_thread_cycles 0.8388; guard ordered full batch_wall_ns 1.1227; guard ordered second_half batch_wall_ns 1.1460; guard ordered second_half batch_thread_cycles 1.1504; guard ordered second_half within_case_p95_wall_ns 1.1575; guard ordered second_half within_case_p95_thread_cycles 1.1282; goal/control extreme full batch_wall_ns 0.3316; goal/control extreme second_half batch_wall_ns 0.3274; goal/control extreme second_half batch_thread_cycles 0.3287.

One predeclared balanced RNG seed 20261010, 36 rounds, 12 valid seeds, 6 shapes,
CPU8, 120-second cooldown, 648 fresh cases x32 iterations. Every permutation
appears three times per half per input. Candidate merge accepted iterations
out of 1152 per input: ordered=0, clustered=1152, interleaved=0, duplicates=0, late=0, extreme=1152.
Each run is sorted before concatenation as supported append does. Clone/setup
and row validation are outside the kernel timer; all layout allocations and
the final independent monotonic check/sort/gather are inside it.

Both cohort and auditor actually exited 0. Native code checked exact canonical
row triples/sortedness for all 20,736 operations (679,477,248
rows checked). Python independently recomputed 648 reference fingerprints and
i128 sums; fingerprints can collide and are not complete independent output
decodes or Archive CRC proofs. 10 fresh kernel tests (5 debug + 5 release), 3 strict
compiler warning checks and 2 excluded smokes passed. 332 Archive candidate tests
from 122 are reused, not fresh 126. No recovery/physical-power-loss claim.
Timed cases: 2026-10-10T13:54:27.776937+00:00 through 2026-10-10T13:59:03.375953+00:00.

[Actual driver/controllers](experiments/kernel_layout_126/README.md).
[Microsoft's cycle-counter contract](https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-querythreadcycletime)
requires keeping cycles distinct from elapsed time; no cycle-to-time conversion
is used. Binary SHA256: `4442fc5c4455e7d972ac4e7f318d9df267b3725c36e3310d401bb36128c14fd5`.
Policy SHA256: `ecc23e63aa888d6b09d8ccff4ba1474e0b3792afbe0d3cdb18d449b45664955a`.
Journal SHA256: `33d87f8da167dc9c3a4e9daa5308eac7ecc710321765999e903766da5b58edb5`.
The original 324 Native/252 service/42 goals/153 controls/171 guards and relevant
correctness/recovery/sustained-service gates remain required. Concise outcome
and useful source follow private save verification, then scoped cleanup; no
multi-gigabyte raw bundle. No release ETA follows from this diagnostic.
