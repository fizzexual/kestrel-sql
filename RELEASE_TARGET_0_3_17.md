# KestrelSQL 0.3.17 release target

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
