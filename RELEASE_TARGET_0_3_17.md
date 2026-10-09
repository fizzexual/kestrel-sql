# KestrelSQL 0.3.17 release target

**Latest matched tracer controls:** [095: stock-trace: unqualified; incremental-trace: unqualified](TRACE_CONTROLS_095.md), all 288 cases and every failure preserved. Diagnostic qualification is separate from an engine speed gain; 0.3.16 stays supported and .17 unqualified.


**Latest recovery milestone:** [094 passes 107 fixed fault cases and 22 corruption rejections](RECLAIM_RECOVERY_094.md), with exact independent restoration. This closes a recovery gap; 093 remains rejected on speed and supported 0.3.16 is unchanged. .17 remains unqualified.


**Latest engine candidate:** [093 incremental reclamation is rejected](INCREMENTAL_RECLAIM_093.md): 2,650 queue drops, five failed A/A checks and missed append goals. All 178,622 ACK batches pass full independent data/CRC audit and exact restoration; lower medians do not qualify a win. Supported 0.3.16 remains unchanged; .17 is unqualified.


**Reclamation measurement milestone:** [092 passes all native phase controls](RECLAIM_PHASES_092.md), 314 tests, both balanced halves and all 72 exact stores. File deletion accounts for about 83% of native reclaim time; this justifies a separate bounded Live cleanup candidate. Diagnostics are qualified in this scope; no engine gain or supported upgrade is claimed. All earlier failures remain preserved; supported 0.3.16 is unchanged.


**Writer diagnostic milestone:** [091 passes all full/half overhead controls](TRACE_CONTROLS_091.md) under unchanged 5% limits with exact 090 artifacts, 1.872 million successful requests, 179,280 reopened ACK batches and 59,760 correlated traced ACKs. Reclamation is the next measured writer target. This qualifies scoped diagnostics, not an engine gain or 0.3.17 release; [090](MAINTENANCE_ISOLATION_090.md) and all earlier failures remain preserved. Supported 0.3.16 is unchanged.

Updated October 8, 2026. Supported version: **0.3.16**. **0.3.17 is not qualified or released; there is no justified calendar ETA.** The next supported version requires a concrete engine change that passes the release checks below. Trial numbers are not released versions.

The objective is wins across the declared analytical and service suites, with exact answers, preserved durability and explicit accounting of every failed request. A faster successful-operation p99 with more losses does not win. Neither a warm native subset nor a metadata model establishes superiority across SQL workloads or feature parity.

| Area | Current evidence | Requirement before advancement |
| --- | --- | --- |
| Analytical queries | Supported 046 records 60/60 DuckDB median wins in its measured warm subset. Clean parser 061 records 60/60 and faster native ranges. | Preserve all supported shapes, exact results, paired native controls, tail and memory guards; record interface/layout limits. |
| Read service | Fresh D: 086 read p99 about 1.09 ms; guards pass in both blocks. | Pass complete end-to-end read/scan/mixed service guards under fresh controls. |
| Durable write tails | Fresh 086 fails calibrated write-heavy overall/append p99 guards: paired +15.75%/+24.32%. | Fix a measured publication/maintenance/queue bottleneck; preserve synchronization and ACK/replay contracts; pass full cohort and blocks. |
| Sustained load and overload | 086's three profiles execute all 900,000 offers with no loss. Prior full-service overload and minute failures remain. | Run the complete six-profile suite, including 2,000/s mixed, 10,000/s overload, write-heavy, minute mixed, read and scan; account all errors/drops/expiries and achieved throughput. |
| Recovery and compatibility | Previous candidate correctness suites and every rejected model are retained. 086 verifies fresh anonymous-write ACKs after reopen. | Fresh relevant source/retry/crash/error/corruption, historical-format, exclusive-writer, pinned-reader/reclaim and independent SQL/CRC qualification for the final engine change. |
| Competitor comparisons | Historical PostgreSQL mixed/append p99 losses coexist with read-p99 wins. | New matched-host comparisons with equivalent semantics, adapters and durability, complete losses and raw evidence. D: timings do not replace old C: competitors. |
| Reproducibility | Policies, sources, binaries, raw outcomes, stores and failures retained. | Fixed predeclared controls; full preserved inputs/results; verified restoration/audit; no selective reruns or changed gates. |

The current priority is the real service writer. Individual publication/compaction/wait diagnostics come before another write-path edit; aggregate sync totals alone cannot identify the cause of p99 stalls. Reader candidates 081/084 and metadata models remain isolated after failed qualification. The clean query fix remains a candidate until service checks pass.

When these checks pass for an actual integrated change, prepare 0.3.17 artifacts and reviewable release evidence. Keep every old release/failure and the private repository intact. This target is not a release announcement or a promise of universal superiority.

[Fresh D: service check 086](SERVICE_D_086.md), [clean query fix 061](CORE_READ_PATH_061.md), [complete benchmark history](BENCHMARK_HISTORY.md).

[087 bounded service-writer diagnostics](WRITER_TRACE_087.md) now pass scoped correctness, byte/retry/reopen and ACK correlation in both isolated cores. The diagnostic bridge extra-field bug is fixed and its failed evidence retained. Tracing overhead/default-build performance and individual service-tail calibration remain next; no speed gate, supported promotion or release date changes.

[088 default-build and tracer qualification](WRITER_OVERHEAD_088.md) now measures 288 fresh cases and verifies all 2.88 million operations, 147,024 ACK batches, reference windows and full CRC/reopen checks. Fixed full/half qualification fails 15 A/A checks and 12 candidate guards. Read/memory gates pass, but default-build write compatibility and tracer latency remain unqualified; full released-core default write overall p99 has a calibrated paired 23.4% regression. Inspect same-toolchain untouched/default-build provenance under new controls before interpreting traces or changing the writer. Supported 0.3.16 and all release gates remain unchanged.

[089 matched-toolchain default-build controls](BUILD_COMPARE_089.md) add 464 native test executions and byte/wire/SQLite/cross-reopen qualification before 216 fresh service cases. All 2.16 million requests succeed with zero loss, and no candidate guard fails. Eight A/A checks fail across required full/half scopes, so complete build/source compatibility remains unqualified. These new artifacts do not overturn 088 or qualify tracing overhead, an engine gain, a competitor sweep or 0.3.17. Next isolate unconditional maintenance control-flow changes with original feature-disabled execution shape under a new numbered trial and stronger complete controls; preserve all prior failures and every integrated release gate.

[090 maintenance-source correction](MAINTENANCE_ISOLATION_090.md) now passes every default compatibility criterion in full/two independent halves for read/write profiles. All 1.872 million requests succeed with zero loss and 179,280 ACK batches survive reopen. Complete writer-trace overhead still fails two half-cohort write-overall A/A checks despite passing all candidate guards. The source correction remains isolated; this does not qualify a speed gain, full service/recovery/competitor matrix or 0.3.17. Strengthen unchanged controls under a new numbered complete trial before tracing-based attribution; retain all prior failures and every integrated gate.


## Isolated asynchronous reclamation 096

[ASYNC_RECLAIM_096.md](ASYNC_RECLAIM_096.md): actual bounded owned deletion worker;693 native tests/four lints,40 fault and8 concurrent cases, exact ACK/CRC/ownership/format/retry/restoration pass. All first failures and partial stores retained. No performance timing, speed/adoption/competitor/release claim;0.3.16 supported,0.3.17 unqualified.


## Coupled worker/publication recovery 097

[COUPLED_RECOVERY_097.md](COUPLED_RECOVERY_097.md): 448 actual coupled worker error/exit and publication/compaction schedules pass; 370 fresh tests/four lints, complete ACK/ambiguous receipt/CRC/ownership checks and exact restoration. Every failed controller/preparation remains. Speed unmeasured; 0.3.16 supported and .17 unqualified.


## Normal owned async service 098

[ASYNC_SERVICE_098.md](ASYNC_SERVICE_098.md): all 1,872,000 offers and 179,280 ACKs pass independent data and graceful completion checks, but second-half append calibration and improvement miss the fixed gates. The entire 144-case result and all failures were restored exactly; unqualified, no adoption, supported 0.3.16 unchanged and .17 pending.


## Retirement diagnostic 099

[RETIREMENT_099.md](RETIREMENT_099.md): all 144 native cases, data and lifecycle checks pass, but four baseline repeatability gates fail. The approximately 1.1 ms retirement signal remains unqualified; no handle offload or speed adoption. All raw and failed attempts are restored exactly, supported 0.3.16 stays unchanged and .17 is pending.


## Append publication diagnostic 100

[PUBLICATION_COST_100.md](PUBLICATION_COST_100.md): all 144 cases, historical/current data and lifecycle checks pass, but one named p99 repeatability gate fails. All stages, stalls and unchanged decisions are restored exactly. Unqualified, no adoption; supported 0.3.16 stays unchanged and .17 is pending. A separate static proof retains qualified 091 as the basis for a future code hypothesis.
