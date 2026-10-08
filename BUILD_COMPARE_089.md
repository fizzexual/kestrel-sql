# Controlled default build comparison 089

October 8, 2026. **All 216 cases pass correctness, and no candidate numerical guard fails. Qualification still fails: eight of 117 A/A checks fail across six of nine required scopes.** Every comparison family has at least one failed required scope. Supported KestrelSQL remains **0.3.16**; no engine speed improvement, low tracing overhead, competitor sweep or supported 0.3.17 release is established. There is no justified release date.

This fresh investigation follows [088's retained default-build write regressions](WRITER_OVERHEAD_088.md). It compares three newly built source variants under identical declared toolchain/settings, alongside the exact original 0.3.16 executable. The new cohort does not reproduce a candidate guard failure, but failed controls prevent complete compatibility qualification or exclusive attribution. It does not replace, invalidate or selectively repeat 088. Its same-version diagnostic artifact also differs from 088's versioned diagnostic artifact.

## Source, build and correctness before timing

Three isolated D: source copies preserve every original byte except predeclared self-version edits. `stock-016` uses supported 0.3.16 sources; `stock-version87` changes only this package's Cargo.toml/Cargo.lock version to 0.3.17-dev.87-released. `diagnostic-016` uses corrected 087 released-core sources with the self-version normalized to 0.3.16 and all diagnostic features disabled. An identical untimed byte-oracle example is added to stock sources solely as a correctness fixture. Source paths and crate metadata can affect compiled layout, so these comparisons do not establish exclusive version/source/compiler causality. Original-version labels identify isolated test controls, not supported promotion.

[Source derivation](benchmarks/build-compare-089/source-derivation.json), [toolchain](benchmarks/build-compare-089/toolchain.json) and [build proof](benchmarks/build-compare-089/build-proof.json) record rustc/cargo 1.97.1, x86_64-pc-windows-msvc, LLVM 22.1.6, offline locked dependencies, thin LTO, one codegen unit and CARGO_INCREMENTAL=0. Extra ambient Rust/release flags are absent. Each source uses a separate fresh D: target; no formatting, dependency upgrade, installation or network work occurred. Existing 087 diagnostic line endings are preserved exactly, including its lockfile difference from stock. Every debug/release suite and strict default lint passes: **464 native test executions**, three lint runs and three release binary builds. Default tracing getters/fields and fault controls are absent from tested service artifacts.

[Untimed oracle proof](benchmarks/build-compare-089/oracle-proof.json) records eight sequence/oversized stores with byte-equivalent Archive files, 32 complete cross-reopens with receipt/retry/collision checks, 32 independent SQLite comparisons including empty and signed-64-bit boundaries, and four default-wire checks. Seventy-two external native commands succeed. Both forms of the optional writer-trace request are rejected in all four default builds. All four fresh setup smokes pass and are excluded from every performance gate. Earlier broad crash/source qualification is reused, not newly rerun; this scoped study does not establish new crash or power-loss coverage.

## Frozen complete comparison

[Policy](benchmarks/build-compare-089/policy.json) and [timing freeze](benchmarks/build-compare-089/timing-freeze.json) identify every binary/source/harness SHA and all cases. The same exact baseline executable runs as A and B within each family:

| Family | A and B | Candidate |
| --- | --- | --- |
| rebuild-released | Exact original supported 0.3.16 artifact | Fresh untouched stock-016 build |
| package-version-only | Exact fresh stock-016 artifact | Fresh stock with only self-version edited |
| diagnostic-default-same-version | Exact fresh stock-016 artifact | Corrected 087 released source, version 0.3.16, diagnostics disabled |

Twelve rounds comprise two independently complete six-permutation halves, balancing pair order and slot for every family/profile. Three families, two profiles and three variants yield **216 fresh serial stores**. Each uses 1M seed rows, 64 clients, 100-row anonymous append batches and zero deliberate grouping delay. Read offers 2,000/s for 8 seconds; write offers 500/s for 8 seconds with 25% writes. Queue capacity is 256, expiry 2 seconds and retry index zero.

Fixed compatibility limits remain identical to 088: A/A p99 and achieved-window rate 0.90–1.10; candidate p99 <=1.10 and rate >=0.90; zero loss. A/A native peak ratio must be 0.90–1.10 with absolute difference <=2 MiB; candidate peak ratio <=1.05 and additional memory <=2 MiB. Every family must pass the full cohort and both halves. Candidate/B remains diagnostic and cannot replace the declared comparison. Full/half counts overlap, and read overall/query criteria share the same population; 117 checks are not 117 independent statistical observations.

Timing ran from **2026-10-08T14:40:51.277248+00:00** through **2026-10-08T15:12:42.740394+00:00**. All builds, copying, hashing, packaging, cleanup and other benchmarks stopped before timing. Only light status-tail reads ran alongside it. Resource callbacks, reopen/verification and reference comparisons run outside each arrival/drain window. The post-run process guard verifies no owned native jobs remain and the separate offline reset is still waiting.

## Exact correctness and outcome accounting

All **2,160,000/2,160,000 offered requests succeed**, with zero errors, drops, expiries, losses or unexecuted requests. All **110,268 acknowledged 100-row batches** survive cold reopen with exact atomic count/sum reconciliation and no unacknowledged-but-committed batch. Independent NumPy comparisons cover **4,320 windows**, and full CRC checks cover **5,448,643,200 row-data bytes**. All **307 individual service samples above 100 ms** remain included. No tracing is enabled in any variant.

## Required full and half decisions

| Family | Scope | Failed A/A checks | Failed candidate guards | Required scope decision |
| --- | --- | ---: | ---: | --- |
| rebuild-released | full | 1/13 | 0/13 | Fail |
| rebuild-released | block_0 | 1/13 | 0/13 | Fail |
| rebuild-released | block_1 | 1/13 | 0/13 | Fail |
| package-version-only | full | 0/13 | 0/13 | Pass |
| package-version-only | block_0 | 0/13 | 0/13 | Pass |
| package-version-only | block_1 | 2/13 | 0/13 | Fail |
| diagnostic-default-same-version | full | 1/13 | 0/13 | Fail |
| diagnostic-default-same-version | block_0 | 2/13 | 0/13 | Fail |
| diagnostic-default-same-version | block_1 | 0/13 | 0/13 | Pass |

Every candidate criterion passes. Rate, zero-loss, write-profile query and both native memory criteria also pass every control scope. Failed calibration covers write overall p99 in the rebuilt and diagnostic comparisons, diagnostic append p99 in the first half, and version-only read overall/query p99 in the second half. The passing full version-only scope and passing second diagnostic half cannot override the other required failures.

| Failed A/A family | Scope | Metric | Paired B/A |
| --- | --- | --- | ---: |
| rebuild-released | full | write/overall_p99 | 0.874794 |
| rebuild-released | block_0 | write/overall_p99 | 0.894896 |
| rebuild-released | block_1 | write/overall_p99 | 0.821858 |
| package-version-only | block_1 | read/overall_p99 | 1.131209 |
| package-version-only | block_1 | read/query_p99 | 1.131209 |
| diagnostic-default-same-version | full | write/overall_p99 | 1.254208 |
| diagnostic-default-same-version | block_0 | write/overall_p99 | 1.315715 |
| diagnostic-default-same-version | block_0 | write/append_p99 | 1.215776 |

## Full-cohort latency observations

Times below are medians of case p99 values. Ratios are medians of within-round pairs and need not equal the quotient of displayed medians. A failed corresponding control makes that difference unqualified; passing compatibility limits alone does not qualify a gain or the complete family.

| Family | Profile/metric | A median ms | C median ms | Paired C/A | Paired B/A | Corresponding full control |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| rebuild-released | read/overall | 1.0673 | 1.0597 | 0.976832 | 0.984306 | Pass |
| rebuild-released | write/overall | 9.1030 | 7.9522 | 1.069345 | 0.874794 | Fail / unqualified |
| rebuild-released | write/query | 1.2961 | 1.3131 | 1.033013 | 1.017970 | Pass |
| rebuild-released | write/append | 14.6586 | 14.3625 | 1.030679 | 0.970396 | Pass |
| package-version-only | read/overall | 1.0784 | 1.0960 | 1.044059 | 1.016963 | Pass |
| package-version-only | write/overall | 8.8058 | 8.2394 | 0.978172 | 1.046679 | Pass |
| package-version-only | write/query | 1.3057 | 1.2867 | 0.988692 | 0.989135 | Pass |
| package-version-only | write/append | 14.6048 | 14.6542 | 1.001833 | 1.016694 | Pass |
| diagnostic-default-same-version | read/overall | 1.0754 | 1.0781 | 0.982783 | 0.963209 | Pass |
| diagnostic-default-same-version | write/overall | 8.4188 | 9.6189 | 0.969807 | 1.254208 | Fail / unqualified |
| diagnostic-default-same-version | write/query | 1.3244 | 1.3015 | 0.984081 | 1.015751 | Pass |
| diagnostic-default-same-version | write/append | 14.2447 | 15.0128 | 0.983597 | 1.099998 | Pass |

For example, the rebuild's write overall paired C/A is 1.069345 while its A/A is 0.874794 and fails. The diagnostic source's write overall C/A is 0.969807 while its A/A is 1.254208 and fails. Neither result establishes an engine regression or improvement. The diagnostic full append control narrowly passes at 1.099998, but its first-half append control fails and the complete family remains unqualified. No native or timed cases were rerun to improve these decisions.

## Resource limits

[GetProcessMemoryInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo) and [PROCESS_MEMORY_COUNTERS](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters) provide native peak working set. Sampling includes startup, seed and workload through the post-load sample, before reopen; it does not isolate allocations or measure full-lifetime peak RSS. Every full/half ratio and additional-memory criterion passes.

| Family | Profile | Paired C/A peak | Median paired difference KiB | Both full memory guards |
| --- | --- | ---: | ---: | --- |
| rebuild-released | read | 0.999461 | -22.0 | Pass |
| rebuild-released | write | 1.000094 | 4.0 | Pass |
| package-version-only | read | 1.000049 | 2.0 | Pass |
| package-version-only | write | 1.001767 | 76.0 | Pass |
| diagnostic-default-same-version | read | 0.999706 | -12.0 | Pass |
| diagnostic-default-same-version | write | 1.001860 | 80.0 | Pass |

[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes) reports native user/kernel CPU with a 100 ns representation unit, not guaranteed measurement resolution. CPU stays diagnostic; many read windows have zero charged increments and do not prove zero cost. No p99 decomposition, tracing-overhead bound or physical storage/OS cause is established here.

## Preserved evidence and next work

**77 bounded ZIP parts preserve 19,665 files and 5,843,958,721 logical bytes.** Complete member CRC/SHA/size and exact-set checks pass. Every original is reverified unchanged. The independent restoration at `D:\Codex\Kestrel\work\restored-build-089` replays the frozen raw auditor exactly, including all quantiles, conservation, resource records and full/half failures, with **zero native launches or timing reruns**. Complete post-audit member hashes/sizes/sets also pass. [Inventory](benchmarks/build-compare-089/evidence-inventory.json), [preservation proof](benchmarks/build-compare-089/preservation-proof.json), [restored audit proof](benchmarks/build-compare-089/restored-audit-proof.json) and [restoration instructions](benchmarks/build-compare-089/REPRODUCE.md) make the evidence reviewable.

All raw results, every native service/smoke/oracle/cargo-test fixture, exact binaries/sources/locks, logs, policies and helpers remain at `D:\Codex\Kestrel\work\perf-089`. Only regenerable target-build/Python caches are omitted from ZIPs, with explicit path/size inventory; originals remain intact. Mutable stdout logs are excluded from frozen inputs and copied only after their processes end. A post-timing read requested a nonexistent bookkeeping filename; its error record is retained. The first reporting helper then failed on a flat-versus-nested source-hash schema lookup before writing conclusions; its exact helper and raw error are retained alongside the corrected helper. The frozen audit passed on its first run and no benchmark input or decision changed.

[Post-timing source comparison](benchmarks/build-compare-089/stock-to-diagnostic-source.json) retains every stock/diagnostic file SHA and the full diff inside the archives. It identifies two unconditional maintenance-result/control-flow rewrites in otherwise feature-disabled diagnostic source. They are a source hypothesis, not the measured cause of 088/089 outcomes. Use a new experiment number, 090 or later, to restore the original feature-disabled execution shape in an isolated diagnostic trial, verify native/byte/protocol/recovery behavior, and predeclare stronger complete balanced controls before any new timing. Preserve 086–089 and all failed blocks; never relax limits, reduce synchronization/ACK durability, switch to candidate/B or repeat only bad cases. Diagnostic work is not a substitute for a measured writer improvement.

A concrete integrated writer/query improvement still needs the complete native, six-profile/minute/overload/scan, memory, source/retry/crash/corruption, historical-format, exclusive-writer, competitor and restored-audit release checks. This study refreshes no competitor result. The private repository, supported engine and frozen overnight report remain unchanged. The fresh-profile reset is prepared and separately waiting for full Codex exit; no app was force-closed and no old task/chat/automation was resumed.

[088 controlled regressions](WRITER_OVERHEAD_088.md), [087 diagnostic correctness](WRITER_TRACE_087.md), [086 service failures](SERVICE_D_086.md), [0.3.17 release requirements](RELEASE_TARGET_0_3_17.md), [complete history](BENCHMARK_HISTORY.md).
