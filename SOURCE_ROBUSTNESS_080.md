# Same-D source publication and recovery robustness, 080

Measured October 8, 2026 on the physical `D:\Codex\Kestrel\work\perf-080` tree. **Robustness qualification fails. Supported 0.3.16 remains unchanged.** This is a standalone receipt metadata model, not SQL, real segment I/O, a service benchmark, or an engine release.

The exact qualified 076 binary was used twice as A/A controls against unchanged 078. Twelve rounds form two separately balanced complete six-order blocks. The 108 serial fresh stores contain 6,912 durable publications (6,048 ordinary and 864 source intervals), 216 checkpoint cycles, and 1,296 fresh same-process recovery opens. Each case uses 64 publications, two source keys, and three opens at each of four boundaries. OS caches may be warm; other desktop activity is uncontrolled. Compilation, cleanup, hashing, copying, Git and packaging finished before timers began.

| Original receipts | Control total ms | Candidate total ms | Median paired C/A | Matching A/A | Total goal |
| ---: | ---: | ---: | ---: | ---: | --- |
| 126 | 125.551 | 115.780 | 0.937712 | 0.934123 | Not a large-store goal |
| 50,126 | 198.462 | 119.976 | 0.620488 | 1.045937 | Pass with calibrated control |
| 99,126 | 313.303 | 125.748 | 0.398436 | 0.955013 | Pass with calibrated control |

Displayed totals are medians of case sums; paired ratios are medians of within-round ratios and need not equal the quotient of displayed medians. No old C: timer is a before/after baseline for this D: cohort.

| Original receipts | Control source p99 ms | Candidate source p99 ms | Paired C/A | Matching A/A | Source goal |
| ---: | ---: | ---: | ---: | ---: | --- |
| 50,126 | 15.266 | 3.519 | 0.232968 | 1.062443 | Pass with calibrated control |
| 99,126 | 35.721 | 3.693 | 0.100134 | 0.866612 | Numeric pass; calibration fails |

All four numerical goals pass; three have passing matching controls. **3/66 candidate guards and 11/72 A/A checks fail** in the full cohort. The calibrated 50K recovery regressions are fresh-open p99 +11.3%, checkpoint64 p50 +17.0%, and checkpoint64 p99 +26.0%. Ordinary p99 at 50K is narrowly within the full-cohort limit, but it fails in the second block. The predeclared rule requires all 142 original 079 checks in the full cohort and separately in both six-round blocks. Blocks fail 18 and 37 checks respectively; a combined median does not erase those failures.

The independent audit fully decodes 201 canonical files and verifies all 7,236 timed file instances against them. All logical edits, complete ledgers, source positions, digests, generations, publication bytes, sync counts, recovery summaries, raw hashes and frozen sources pass. Six untimed common-workload smoke cases and three order rejection tests passed before the cohort. Historical 078 correctness qualification was reused, not rerun in 080.

All 467 publication/recovery events above 100 ms are recovery opens; no publication or recovery sample exceeds 500 ms. Every sample remains in the analysis. The pooled diagnostic p50/p95/p99/max and chronological events are separate from the unchanged per-case paired gates. No physical cause is inferred from the timings.

The source projection still reduces large-store publication work, but its recovery tails and calibration are insufficient for adoption. The next isolated hypothesis is bounded bulk construction of the authoritative receipt map during loading, with explicit duplicate rejection and the unchanged 100,000-entry/64 MiB limits. It must pass fresh correctness, interruption, wire and memory checks before a separate D: comparison against 078. Real Archive integration, exclusive writer ownership, service and durability gates remain necessary before any supported upgrade.

Complete working evidence: [policy](benchmarks/d-development-080-082/perf-080/policy.json), [frozen cohort](benchmarks/d-development-080-082/perf-080/cohort-policy.json), [full audit](benchmarks/d-development-080-082/perf-080/model-audit.json), [both block checks and exhaustive stalls](benchmarks/d-development-080-082/perf-080/robustness-audit.json), `D:/Codex/Kestrel/work/perf-080/raw`, and `D:/Codex/Kestrel/work/perf-080/fixtures`. Forty bounded preservation archives contain complete 080–082 evidence; all 38,189 restored files passed SHA-256 verification. Both restored audits reproduce every ratio, failure and inventory exactly: [proof](benchmarks/d-development-080-082/restored-audit-proof.json), [reproduction instructions](benchmarks/d-development-080-082/REPRODUCE.md). Historical 075/077/079 failures and the issued overnight report remain unchanged.
