# Extrema comparison146 — October12,2026 UTC

**UNQUALIFIED:216 independently correct stores; 32/144 A/A,
14/144 guards and 0/6 goals fail. An extra
manual metadata-query boundary is unproven.144 is not adopted;017 unreleased.**

Exact supported016 A/B versus joint131+144 C; this does not isolate144 versus131.
The following complete-cohort observations are descriptive, not a qualified
speed claim. Paired medians can differ from quotients of displayed p50s.

| Shape | Before p50 ms | After p50 ms | Paired whole change | Paired prepare change | Before/after whole p95 ms | Whole/p95 A/A |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| ordered | 5.61835 | 5.52550 | +1.63% | +0.93% | 6.4592/6.3349 | pass / FAIL |
| clustered | 6.33270 | 5.19950 | -17.19% | -48.98% | 7.3414/5.8946 | pass / pass |
| interleaved | 7.21555 | 6.86675 | -5.35% | -10.04% | 8.0762/35.0418 | pass / pass |
| duplicates | 6.20210 | 6.27320 | -1.34% | +0.25% | 7.0367/8.5417 | pass / FAIL |
| late | 6.39150 | 6.44160 | +2.28% | -6.12% | 6.9158/45.0226 | pass / FAIL |
| extreme | 6.59610 | 5.62860 | -15.16% | -45.35% | 6.9874/6.1512 | pass / FAIL |

| Clustered scope | Metric | C/A | A/A | Numerical goal |
| --- | --- | ---: | ---: | --- |
| full | wall_ms | 0.828142 | 1.012368 | pass |
| full | prepare_ms | 0.510155 | 1.000440 | pass |
| first_half | wall_ms | 0.818578 | 1.012368 | pass |
| first_half | prepare_ms | 0.492876 | 1.034812 | pass |
| second_half | wall_ms | 0.832106 | 1.020316 | pass |
| second_half | prepare_ms | 0.533815 | 0.971305 | pass |

Clustered whole p50 is6.33270->5.19950ms, paired17.19% lower; preparation
2.15705->1.10910ms, paired48.98% lower. All six clustered numerical goals and
their controls pass full/both halves. The conservative manual-query envelope
intersects no clustered native case. These are limited joint131+144 observations;
the overall failures still prevent adoption. Do not combine ratios with133.

[Every numerical failed check](experiments/compaction_extrema_compare_146/FAILED_CHECKS.md)
is preserved; 3 failed guards have passing corresponding controls.
Failed controls make corresponding comparisons inconclusive. Every stall/sample
stays once, with no selected retiming, outlier removal or loosened threshold.
Measured prepare/write/sync intervals do not identify an exclusive disk cause.
Three calibrated failures remain: interleaved full whole p95
8.0762->35.0418ms (4.338897x); late first-half6.4848->29.4612ms (4.543116x);
late second-half segment-write median ratio1.107528. Passing corresponding
controls are0.907989/1.013277/0.980693. Other failed guards have failed controls.

All216 native/controller/two metadata workers/two main auditors actually exited0.
Full independent decode checked7,077,888 exact rows/169,869,312 CRCbytes, all
indexes/original receipt digests/head33 and2304 generations from declared run+1.
Every 517 recorded worker probe was checked against every216 native
lifetime (111,672 pairs); frozen bytes/order exact.
2 actual permitted waits stayed outside native lives.

I also made an initial required root live-status query with output21:17:05.309952Z;
its exact process start was not logged. Its conservative21:16:46.451..21:17:07
envelope intersects cases[14, 15, 16, 17].
This neither proves nor disproves actual overlap, and is not silently excluded.
No Git/hash/build/copy/cleanup/timed job came from that query. Additional audit
actually completed0 and saved the limitation. Future active-cohort checks use
the cohort's own fresh guard responses/owned-session status; no extra root
process query during native lives. Numerical controls cannot erase this gap.

Complete216 same-D cases/12 balanced rounds/six shapes/32x1024rows/3cols,
RNG20261011/all6permutations per shape per half, ownedCPU8.120 continuously
observed clear seconds before timers; reset/task/supervisor/global guards before/
after every case. All input/readCRC/phase/index/write/flush/sync charged inside
compact_small. Full/both-half144 controls/144 guards/6 clustered goals unchanged.
Whole/setup p95 nearest-rank with12/full or6/half=max. Baseline154/candidate344
tests/two lints/wire/recovery reused; no Rust build. Six fresh excluded preflights
196608rows/4718592CRCbytes passed. Waits are not a database scheduling feature.

Original324Native/252service/42goals/153AA/171guards plus correctness/retry/
recovery/sustained service remain before adoption. No component-only release,
universal-win/ETA or physical power-loss proof. [Actual source/proofs](experiments/compaction_extrema_compare_146/README.md).
Policy SHA256:`783b0319912fd7f453ddde9f5bd59c5f256af86238c79a32d3b094869a7501fa`; journal SHA256:`bc25843f6adf900ed6705ba337f34dd79cbb40ab038c939dcc92966eb8288e33`.
Short private outcomes/source/failures freshly byte-verified before native exact
completed-fixture cleanup. Useful kits/private history/tags/releases retained;
no raw multiGB bundle. Next unused147+, never replay146 or145.
