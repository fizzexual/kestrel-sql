# Index diagnostic143: measured kernel improvement, one control failure

All216 cases/native/controller/two-worker/two-auditor exits0. Independent exact
input SHA, full indexes, wide i128 prefixes and represented CRC payloads pass:
7,077,888 rows /169,869,312 bytes across216 outputs. Every715 metadata probe
was checked against every216 native lifetimes (154,440 pairs); all7 outside-
lifetime pauses and actual child births checked. Frozen source/binaries exact.
All samples/stalls retained once; no metric selection, retiming or gate changes.

**Index construction only. No Archive/durable/service/release speed result.**
The original global column min/max rescans are replaced with reductions over
already verified block extrema. Every other index operation remains exact.
Six fresh example-only tests (3debug/3release), one strict lint and release
artifact pass, including positive/negative wide-i128 typed JSON output. All
supported library src/tests/dependencies remain byte-exact016;0 new engine tests.
Six excluded independent preflights cover196,608 rows/4,718,592 represented CRC
bytes and safety protocol checks. No passed prerequisite was rebuilt/repeated.

The predeclared216 cases use12 rounds/six shapes, every6 permutation once per
shape per half, identical legacy A/B versus extrema-reuse C on owned logicalCPU8.
Primary clocks cover16 full index builds/all allocations/prior-output drops.
The ms/build values below are median **grouped16-build durations divided by16**,
not measured per-operation latency quantiles. Paired changes use within-round
ratios and differ from ratios of unpaired medians. All six full controls pass;
five shapes pass full/both-half5% kernel goals. Ordered's second-half A/A fails:
0.858189, outside[.90,1.10]; its apparent23.220% gain is inconclusive. Overall
1/18 controls,1/18 qualified guards and1/18 qualified goals fail on that same
row; its candidate guard/goal numbers pass but the corresponding control fails.
There is no calibrated numerical regression. Overall kernel qualification fails.

| Shape | Legacy ms/build | Reuse ms/build | Paired change | Full/first/second controls | First/second paired change |
| --- | ---: | ---: | ---: | --- | --- |
| ordered | 0.279731 | 0.232969 | -13.493% | pass/pass/FAIL | -12.469% / -23.220% |
| clustered | 0.239088 | 0.194344 | -17.407% | pass/pass/pass | -19.116% / -13.308% |
| interleaved | 0.245081 | 0.193122 | -23.275% | pass/pass/pass | -21.009% / -28.742% |
| duplicates | 0.242097 | 0.195700 | -18.331% | pass/pass/pass | -18.331% / -19.258% |
| late | 0.240787 | 0.192416 | -19.666% | pass/pass/pass | -19.976% / -17.879% |
| extreme | 0.246672 | 0.198731 | -20.886% | pass/pass/pass | -18.742% / -25.288% |

The separate legacy stage clocks run OUTSIDE the primary timer. Their overhead
and different code layout mean these are diagnostic intervals, not exclusive
Archive costs. Medians need not add to the median total. Global rescans account
for26.0–28.5% of those instrumented totals, alongside block-extrema passes.

| Shape | Sum us | CRC-byte construction us | CRC us | Block extrema us | Global extrema us | Monotonic us | Instrumented total us |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ordered | 40.600 | 22.050 | 30.100 | 86.350 | 79.750 | 29.250 | 307.050 |
| clustered | 34.100 | 20.900 | 27.100 | 70.800 | 68.250 | 14.350 | 242.300 |
| interleaved | 34.800 | 21.150 | 27.150 | 70.700 | 69.250 | 14.400 | 244.150 |
| duplicates | 38.550 | 21.650 | 27.100 | 72.250 | 74.400 | 14.550 | 261.800 |
| late | 33.100 | 21.100 | 26.800 | 70.600 | 68.900 | 14.500 | 241.800 |
| extreme | 36.450 | 21.350 | 26.950 | 71.300 | 69.950 | 14.800 | 246.750 |

Input generation/stable timestamp sorting/SHA, Archive input read/CRC/merge/sort,
index metadata serde, segment/catalog writes/flush/sync, receipts/ACK and service
are EXCLUDED. Seven predeclared safety waits occurred outside actual native
lifetimes; they are not a database scheduling feature. Audit began after a fresh
131.695-second continuously observed clear interval/zero resets. Ten-second
metadata snapshots cannot exclude every brief unobserved process. These results
support a minimal real-engine experiment; they cannot predict durable gains.

Typed output fixes142's JSON Value range defect outside the kernel timer. That
failed/unstarted job and all failures stay in private history; it was not rerun.
Original release324Native/252service/42goals/153AA/171guards plus correctness,
retry/recovery/sustained service remain required.0.3.17 is unreleased. All work
local, evidence skips Actions; concise outcomes/source only, no raw bundle.
