# Fused publication index trial 120

**Rejected for release. Supported version remains 0.3.16; 0.3.17 is unreleased.**

The isolated candidate chooses a fused index builder for publications of at
least 4,096 rows, keeping the scalar path below that boundary. It combines
statistics passes and reuses a CRC buffer without changing archive bytes,
durability, receipts, ACKs or publication limits. Earlier experimental queue,
replay and query phases remain. Trial119's rejected decode change is excluded.

Correctness passed: **836 fresh tests, five strict lints, 359 recovery commands,
324 Native cases, 479,232 ACKs and 2,921,356,800 fully checked CRC bytes**.
Both initial build failures, all raw results and complete restored audit are
preserved in this private commit. Controlled exits are not physical power-loss
tests.

Performance failed **84/153 A/A controls, 22/171 regression guards and 7/42
goals**. All **252 service cases remain unstarted**. Passing controls also show
regressions, including +19.23% ordered aggregate p95. Failed controls make their
comparisons inconclusive.

Only two query metrics pass goals and controls in the full run and both halves:

| Late grouped query | 0.3.16 median | Candidate median | Paired reduction |
| --- | ---: | ---: | ---: |
| Median latency | 9,701.00 us | 6,713.25 us | 18.80% |
| p95 latency | 13,337.95 us | 9,885.95 us | 25.01% |

Reductions use within-round paired ratios, not the quotient of displayed
medians. This compares the combined candidate against 0.3.16; it does not
isolate the new builder or establish wins against other databases. No release
ETA or universal performance claim is supported.
