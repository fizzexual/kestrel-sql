# Combined overlap/reusable synchronization speed104 — October9,2026

**Rejected.** Native qualification fails10/30 identical-baseline controls,1/30 candidate guard and2/12 improvement goals. Service qualification fails3/45 controls,9/51 guards and4/6 goals, with **2,782 lost offers**. Supported0.3.16 stays byte-exact;0.3.17 remains unqualified. No scope is selected to overturn the complete decision.

All44 source files match final103. Fresh normal A/B use the same `async-reclaim,benchmark-shutdown` binary; C adds `reusable-sync-103`, including101 overlap. This measures the combined change versus isolated normal async, rather than pure worker reuse or a direct supported0.3.16 comparison. No061/tracing/fault/profile features enter timed artifacts. Both original synchronization calls, completed matching job, rename-before-ACK, actual worker join, receipts, pins and lease remain intact.

Both fixed cohorts completed144 cases:24 rounds, two independently balanced12-round halves, all six permutations twice per history/profile per half. Native seed10410 uses two histories and512 durable100-row appends per case. Service seed10411 uses1M starting rows,64 clients,100-row appends, read2000offers/s for8s and25%-write500/s for20s. Ratios are medians of within-round C/A and B/A; displayed medians are descriptive and their quotient need not equal the paired ratio. All stalls, numerical misses, raw losses and slower rounds remain. No added rounds, selective reruns, changed gates or durability reduction occurred.

| Native full-cohort metric | Before ms | After ms | Paired C/A | Identical B/A |
| --- | ---: | ---: | ---: | ---: |
| anonymous p50 | 2.175550 | 1.903400 | 0.883252084 | 0.993871981 |
| anonymous p99 | 3.643750 | 3.043000 | 0.858038804 | 0.957566716 |
| named p50 | 2.158250 | 1.943800 | 0.902054030 | 0.997434428 |
| named p99 | 3.591650 | 3.096850 | 0.828581427 | 0.996781165 |

Full native p50/p99 signals do not qualify the complete native change:10 repeatability failures, a half-cohort maximum guard of1.156145922 and two tail goals fail. All73,728 publications,73,872 historical catalogs/original receipt generations,290,193,408 independently checked CRC bytes and same-round current/historical file bytes pass. Two append events above100ms remain.

| Service full-cohort metric | Before ms | After ms | Paired C/A | Identical B/A |
| --- | ---: | ---: | ---: | ---: |
| read overall p99 | 1.077450 | 1.113200 | 1.062785102 | 1.024735193 |
| write overall p99 | 5.962200 | 5.814500 | 0.936587183 | 0.955899136 |
| write append p99 | 11.635750 | 11.978800 | 1.040837570 | 1.021561381 |

Service accounts for1,872,000 offers:1,869,218 successful,2,526 producer-queue drops,256 expiries and0 executed errors. Baseline B loses81 in case20/round4; candidate loses2,701 in case27/round5. Baseline A loses0. Candidate case27 append p99 is5,789.5685ms, maximum5,943.5444ms. These are failed/unexecuted offered requests, not acknowledged data loss. All178,581 acknowledged batches survive independent cold reopen, full3,884,594,400-byte CRC/index/NumPy row references and2,880 query windows. All288 initial/cold native processes actually join and exit0. Every4,309 request event above100ms stays in raw populations. No exclusive physical disk/OS cause is established.

Full write-overall C/A0.936587183 numerically meets5%, but append C/A1.040837570 regresses about4.1%. Half1 overall0.985255017 and append1.040837570 miss both goals; half2 overall0.876210546 meets5% and append1.060792339 misses10%. Read full paired p99 is1.062785102, exceeding its5% guard. CPU is diagnostic only. NativeCPU/RSS were not measured.

Fresh exact-feature debug/release suites execute406 tests and two strict lints. Four finite12,000-group backlog controls verify48,000 ACKs, physical ceilings, pins and original named receipts. Four native/two service smokes,24 cold CLI-versus-SQLite controls and29 synthetic invalid controls pass before the frozen cohort. Full103 correctness916 tests/832 coupled/104 publication/26 source/22 corruption/old-format/byte/restoration checks are **reused**, not recounted as fresh104 tests. Every13,744 pre-timing frozen input remains exact.

Preservation is complete: **78 bounded ZIP parts,168,976 files,2,287 directories,5,463,032,927 logical bytes**. Every memberCRC/order/offset/size, full original/restored fileSHA and exact file/directory set passes before and after complete independent restored replay. The replay recomputes original gates, outcomes, quantiles, historical/current references, resources, ownership/lifecycle, backlog, smokes, SQLite and frozen provenance with zero Native/timer launches or existing-file changes. Only inventoried regenerable targets/Python caches are excluded; originals, tmp/unit stores, failures and empty directories remain. Closed packager stdout is a separately hashed supplement after actual exit. No privateGitHub backup of104 is verified and no raw data is deleted.

Evidence: [policy](benchmarks/reusable-sync-speed-104/policy.json), [complete decision](benchmarks/reusable-sync-speed-104/complete-audit-proof.json), [preservation](benchmarks/reusable-sync-speed-104/preservation-proof.json), [restored replay](benchmarks/reusable-sync-speed-104/restored-audit-proof.json), [reproduction](benchmarks/reusable-sync-speed-104/REPRODUCE.md). OriginalD:/Codex/Kestrel/work/perf-104; restorationD:/Codex/Kestrel/work/restored-reusable-sync-speed-104.

The user's new direction is an optional adaptive execution policy, starting from the exact supported engine in a separately declared105 or later experiment. Sparse/concurrent/pressure collection may choose different bounded behavior; that is a new code hypothesis, not a104 gain. Actual integration and relevant analytical/service/sustained/overload/source/retry/recovery/compatibility/competitor/restoration checks still precede0.3.17 adoption. Work remains private on this computer. The reset is expired without mutation; no force-quit, abandoned-chat resume or old task/automation activation occurs.

Two whitespace-bearing raw helper supplements are stored as exact gzip copies; their uncompressed bytes remain in the verified archive, original and restored trees. The failed first evidence-commit check is retained. The complete staged whitespace check passes without path exclusions or raw normalization.
