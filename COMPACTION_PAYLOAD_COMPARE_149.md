# Payload comparison149 — October13,2026 UTC

**Overall REJECTED:216 independently correct stores;31/144 A/A and22/144 guards
fail. All six clustered goals and corresponding controls pass full/both halves.
Joint131+144+147 is not adopted;0.3.17 remains unreleased.**

Supported016 identical A/B versus joint131+144+147 C; this does not isolate147.
Paired medians can differ from quotients of the displayed medians.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Paired prepare change | Whole/tail A/A |
| --- | ---: | ---: | ---: | ---: | --- |
| ordered | 5.38990 | 5.68410 | +6.16% | +19.26% | pass / FAIL |
| clustered | 6.06690 | 5.53325 | -8.74% | -25.73% | pass / FAIL |
| interleaved | 6.82140 | 7.12315 | +2.75% | +9.51% | pass / FAIL |
| duplicates | 6.35575 | 6.27135 | -0.43% | +3.11% | pass / FAIL |
| late | 6.28090 | 6.42105 | +1.52% | +10.44% | pass / FAIL |
| extreme | 6.57325 | 6.06305 | -8.46% | -28.92% | pass / pass |

| Clustered scope | Metric | C/A | A/A | Goal |
| --- | --- | ---: | ---: | --- |
| full | wall_ms | 0.912639 | 0.989148 | pass |
| full | prepare_ms | 0.742699 | 1.025350 | pass |
| first_half | wall_ms | 0.939210 | 0.993268 | pass |
| first_half | prepare_ms | 0.786149 | 1.030990 | pass |
| second_half | wall_ms | 0.908198 | 0.984254 | pass |
| second_half | prepare_ms | 0.730297 | 1.017151 | pass |

Clustered whole6.06690->5.53325ms, paired8.74% lower; preparation
1.94355->1.45345ms, paired25.73% lower. Those goals/controls pass in both halves.
Clustered write+sync paired full+2.07% (halves+2.44%/+0.05%) with passing controls:
no measured write+sync improvement. Do not combine ratios with146 or infer147's
isolated effect. Large apparent full-tail gains with failed controls are inconclusive.

14 calibrated regressions remain. Ordered preparation full+19.26%,
first+16.46%,second+21.53% with passing controls; full ordered write+12.86%.
Extreme whole p95 9.8802->55.4811ms (5.615382x), A/A0.977845 passes. Ordered
second-half whole p95+10.36% also has passing controls. Interleaved first-half
prepare/write, duplicates full/second write, late full/first prepare and extreme
first write fail calibrated guards. [All53 failed checks](experiments/compaction_payload_compare_149/FAILED_CHECKS.md).
Measured intervals do not identify an exclusive allocator, disk or other cause.

All216 native/controller/two metadata workers/two auditors actual exit0; no
forced kills. Independent decode checked7,077,888 exact rows/169,869,312 CRC
bytes, every index/original receipt digest/head33 and2304 generations derived
from declared run+1. Every528 recorded worker probe was outside all216 native
lifetimes (114048 pairs); frozen bytes/order exact. Four predeclared pauses
were outside timers, with no repeated case/outlier discard/metric selection.
Waits are benchmark safety, not a database scheduling feature.

Declared12 balanced rounds/six shapes/32x1024 rows/three columns/RNG20261011,
all six permutations per shape per half, CPU8 only for owned jobs. ALL input/
readCRC/phase/index/write/flush/sync costs charged. Baseline154/candidate348
tests/two lints/52 stores/wire/recovery explicitly reused; zero new Rust builds.
Six fresh excluded preflights196608 rows/4718592 CRC bytes passed after120.968
continuous clear seconds. Final audits followed131.371 clear seconds/zero
busy resets. No failed149 preparation, preflight, native or audit attempt.

Original release324 Native/252 service/42 goals/153 A/A/171 guards plus
correctness/retry/recovery/sustained service remain unchanged. This component
cannot qualify a release or competitor/service win. Short private outcomes and
useful sources are freshly verified before native completed-fixture cleanup;
useful kits/old private history/tags/releases retained, no raw multiGB bundle.
