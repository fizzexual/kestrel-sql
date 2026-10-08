# Bounded receipt-loader comparison, 082

**The speed hypothesis is rejected. Supported 0.3.16 remains unchanged.** Fresh isolated 081 passes correctness, but all 20 large-store reader goals fail in the full comparison. Lower memory does not compensate for migration/recovery regressions.

Measured October 8, 2026, 07:33:07.685225–07:36:57.306392 UTC on physical `D:\Codex\Kestrel\work\perf-082`. The exact qualified 078 binary was used twice as A/A controls against newly built/qualified 081. Twelve balanced rounds form two independently validated six-order blocks: 108 serial fresh stores, 6,912 durable publications (6,048 ordinary, 864 source), 216 checkpoint cycles and 1,296 fresh opens. Each case uses unchanged `bench075` with 64 publications, two source keys and three opens at four boundaries. OS caches may be warm; other desktop activity is uncontrolled. No compilation, cleanup, copy, hashing, Git or packaging ran alongside the timers.

Twenty goals were declared before timing: at most 0.90 paired candidate/control for migration, fresh-open p99, and p50/p99 of four recovery paths at each of 50K/99K. All 66 prior candidate guard thresholds and 72 identity checks were retained. Full cohort and each balanced half must independently pass all 158 checks. No case was rerun or trimmed.

| Original receipts | Metric | Control median ms | Candidate median ms | Median paired C/A | Matching A/A | Result |
| ---: | --- | ---: | ---: | ---: | ---: | --- |
| 50,126 | Migration | 80.557 | 102.128 | 1.225448 | 1.094211 | Goal fails; calibrated slowdown |
| 50,126 | Fresh-open p99 | 93.956 | 104.817 | 1.190600 | 0.930261 | Goal and guard fail; calibrated slowdown |
| 99,126 | Migration | 191.963 | 194.580 | 0.989361 | 0.940148 | Goal fails |
| 99,126 | Fresh-open p99 | 194.130 | 224.562 | 1.070610 | 0.946233 | Goal fails; calibrated slowdown |

Displayed medians and medians of within-round ratios differ. At 50K, calibrated failing guards also include ordinary publication p50 +10.5%, publication p50 +10.6%, checkpoint-plus-delta63 p50 +17.7% / p99 +28.9%, and anchor31 p50 +18.6% / p99 +15.8%. Ordinary maximum +15.2% fails numerically but its matching A/A calibration fails. At 99K, anchor31 p99 +11.7% is a calibrated failing guard. Full-cohort totals are descriptively 126.815→128.439 ms at 50K and 133.967→127.259 ms at 99K. The 99K total A/A passes at 0.904815, but the reader goals, regression guards and independent-block acceptance fail; this cannot establish an accepted speed upgrade.

**Full failures: 20/20 goals, 9/66 guards, 14/72 identity checks.** Block 1 fails 14 goals, 7 guards and 23 controls; block 2 fails 19 goals, 14 guards and 19 controls. Full acceptance and both-block robustness fail. The old 075/077/079/080 failures remain preserved.

The useful observed tradeoff is lower full-process peak memory:

| Original receipts | Working set control→candidate MiB | Paired ratio | Commit control→candidate MiB | Paired ratio |
| ---: | ---: | ---: | ---: | ---: |
| 50,126 | 27.84→24.60 | 0.883347 | 25.09→21.75 | 0.866983 |
| 99,126 | 51.33→45.10 | 0.878615 | 48.86→42.53 | 0.870194 |

Corresponding full-cohort memory A/A checks are approximately 1.00 and pass. These finite two-source-key process peaks do not establish maximum-fanout memory or universally lower allocation. No exclusive CPU or physical disk cause is inferred for either the memory tradeoff or slower recovery.

Correctness passes: the independent audit decodes all 201 canonical files and full-hashes all 7,236 timed file instances; exact publication bytes, complete ledgers, source positions, retry/collision outcomes, digests, generations, sync counts, recovery summaries, raw hashes, orders and frozen source/binary/input hashes match. Stored/reachable byte ratios are exactly 1.00. Six untimed integration smoke cases and three order rejection tests passed before timing. Fresh prerequisite 081 ran 60 debug + 60 release tests, strict Clippy, 242 native commands, 195 historical heads, 15 injected errors, 15 owned kills, 30 independent corruptions and 201 original-file comparisons. These are newly run tests, distinct from reused 078 control qualification.

All 480 publication/recovery events above 100 ms remain included: two are control publications and 478 are recovery opens. None exceeds 500 ms; worst is a 329.903 ms control anchor open. Pooled p50/p95/p99/max, stages where available, counts and chronology are diagnostic; per-case paired gates decide acceptance. Controlled process kills are not physical power-loss qualification.

Hardware: Intel i9-10900F, 10 cores/20 logical processors, approximately 32 GiB RAM, Windows 10 Pro build 19045; D: is NTFS on CT1000BX500SSD1 SATA SSD. C: is a separate KINGSTON SA400S37480G disk. Rust 1.97.1, Cargo 1.97.1, Python 3.12.10; release uses locked dependencies, ThinLTO and one codegen unit. No historical C: timer is used as a D: before/after baseline.

Keep 081 isolated. Next investigate charged receipt parsing/validation stages with a separate predeclared CPU profile and unchanged decoded result/rejection budgets before proposing another reader change. Real Archive/segment integration, exclusive writer ownership, service, crash and compatibility gates still precede any 0.3.17 adoption. No competitor ranking or engine upgrade follows from this model.

Complete raw evidence remains at `D:\Codex\Kestrel\work\perf-082`; [policy](benchmarks/d-development-080-082/perf-082/policy.json), [full audit](benchmarks/d-development-080-082/perf-082/model-audit.json), and [both balanced blocks and every stall](benchmarks/d-development-080-082/perf-082/robustness-audit.json) remain preserved. Forty bounded archives retain 38,189 files including complete stores, binaries, locked sources, inputs, prerequisite qualifications and failed attempts. All archive CRCs and full restoration hashes passed. Both restored audits reproduce every ratio, failure and inventory exactly without rerunning native commands or timers: [proof](benchmarks/d-development-080-082/restored-audit-proof.json), [reproduction instructions](benchmarks/d-development-080-082/REPRODUCE.md).
