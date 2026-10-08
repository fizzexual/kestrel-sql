"""Write the verified trial089 report after successful evidence restoration."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path('D:/Codex/Kestrel')
W = ROOT / 'work/perf-089'
REPO = ROOT / 'outputs/kestrel-sql'
OUT = REPO / 'benchmarks/build-compare-089'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


audit, run = load(W / 'audit.json'), load(W / 'paired-service.json')
preservation, restored = load(OUT / 'preservation-proof.json'), load(OUT / 'restored-audit-proof.json')
assert preservation['complete'] and restored['passed']
assert restored['native_launches'] == restored['timing_reruns'] == 0
assert audit['correctness_passed'] and not audit['all_required_scopes_passed']
assert (audit['candidate_failed_total'], audit['identity_failed_total']) == (0, 8)
assert all(sha(REPO / n) == v for n, v in load(W / 'unchanged-supported-source.json').items())
decisions, performance, failures, memory = [], [], [], []
for scope in audit['scopes']:
    decisions.append(f"| {scope['family']} | {scope['scope']} | {scope['identity_failed']}/13 | {scope['candidate_failed']}/13 | {'Pass' if scope['passed'] else 'Fail'} |")
    rows = {r['profile']: r for r in scope['summaries']}
    for check in scope['identity_checks']:
        if not check['passed']:
            metric = check['criterion'].removesuffix('_p99')
            value = rows[check['profile']]['comparisons']['identity_b_over_a']['paired_ratios'][metric]['median']
            failures.append(f"| {scope['family']} | {scope['scope']} | {check['profile']}/{check['criterion']} | {value:.6f} |")
    if scope['scope'] != 'full':
        continue
    for row in scope['summaries']:
        primary, identity = row['comparisons']['primary_candidate_over_a'], row['comparisons']['identity_b_over_a']
        for metric in ['overall'] + (['query', 'append'] if row['profile'] == 'write' else []):
            a = row['variants']['baseline_a']['median_case_p99_ms'][metric]
            c = row['variants']['candidate']['median_case_p99_ms'][metric]
            ca, ba = primary['paired_ratios'][metric]['median'], identity['paired_ratios'][metric]['median']
            calibration = 'Pass' if identity['identity_checks'][metric + '_p99'] else 'Fail / unqualified'
            performance.append(f"| {scope['family']} | {row['profile']}/{metric} | {a:.4f} | {c:.4f} | {ca:.6f} | {ba:.6f} | {calibration} |")
        memory.append(f"| {scope['family']} | {row['profile']} | {primary['paired_ratios']['peak']['median']:.6f} | {primary['median_peak_difference_bytes'] / 1024:.1f} | Pass |")
report = f'''# Controlled default build comparison 089

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

Timing ran from **{run['started_utc']}** through **{run['completed_utc']}**. All builds, copying, hashing, packaging, cleanup and other benchmarks stopped before timing. Only light status-tail reads ran alongside it. Resource callbacks, reopen/verification and reference comparisons run outside each arrival/drain window. The post-run process guard verifies no owned native jobs remain and the separate offline reset is still waiting.

## Exact correctness and outcome accounting

All **{audit['successful']:,}/{audit['offered']:,} offered requests succeed**, with zero errors, drops, expiries, losses or unexecuted requests. All **{audit['acknowledged_batches']:,} acknowledged 100-row batches** survive cold reopen with exact atomic count/sum reconciliation and no unacknowledged-but-committed batch. Independent NumPy comparisons cover **{audit['numpy_windows']:,} windows**, and full CRC checks cover **{audit['full_crc_bytes']:,} row-data bytes**. All **{audit['events_over_100ms']:,} individual service samples above 100 ms** remain included. No tracing is enabled in any variant.

## Required full and half decisions

| Family | Scope | Failed A/A checks | Failed candidate guards | Required scope decision |
| --- | --- | ---: | ---: | --- |
{chr(10).join(decisions)}

Every candidate criterion passes. Rate, zero-loss, write-profile query and both native memory criteria also pass every control scope. Failed calibration covers write overall p99 in the rebuilt and diagnostic comparisons, diagnostic append p99 in the first half, and version-only read overall/query p99 in the second half. The passing full version-only scope and passing second diagnostic half cannot override the other required failures.

| Failed A/A family | Scope | Metric | Paired B/A |
| --- | --- | --- | ---: |
{chr(10).join(failures)}

## Full-cohort latency observations

Times below are medians of case p99 values. Ratios are medians of within-round pairs and need not equal the quotient of displayed medians. A failed corresponding control makes that difference unqualified; passing compatibility limits alone does not qualify a gain or the complete family.

| Family | Profile/metric | A median ms | C median ms | Paired C/A | Paired B/A | Corresponding full control |
| --- | --- | ---: | ---: | ---: | ---: | --- |
{chr(10).join(performance)}

For example, the rebuild's write overall paired C/A is 1.069345 while its A/A is 0.874794 and fails. The diagnostic source's write overall C/A is 0.969807 while its A/A is 1.254208 and fails. Neither result establishes an engine regression or improvement. The diagnostic full append control narrowly passes at 1.099998, but its first-half append control fails and the complete family remains unqualified. No native or timed cases were rerun to improve these decisions.

## Resource limits

[GetProcessMemoryInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo) and [PROCESS_MEMORY_COUNTERS](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters) provide native peak working set. Sampling includes startup, seed and workload through the post-load sample, before reopen; it does not isolate allocations or measure full-lifetime peak RSS. Every full/half ratio and additional-memory criterion passes.

| Family | Profile | Paired C/A peak | Median paired difference KiB | Both full memory guards |
| --- | --- | ---: | ---: | --- |
{chr(10).join(memory)}

[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes) reports native user/kernel CPU with a 100 ns representation unit, not guaranteed measurement resolution. CPU stays diagnostic; many read windows have zero charged increments and do not prove zero cost. No p99 decomposition, tracing-overhead bound or physical storage/OS cause is established here.

## Preserved evidence and next work

**{len(preservation['parts'])} bounded ZIP parts preserve {preservation['files']:,} files and {preservation['logical_bytes']:,} logical bytes.** Complete member CRC/SHA/size and exact-set checks pass. Every original is reverified unchanged. The independent restoration at `D:\\Codex\\Kestrel\\work\\restored-build-089` replays the frozen raw auditor exactly, including all quantiles, conservation, resource records and full/half failures, with **zero native launches or timing reruns**. Complete post-audit member hashes/sizes/sets also pass. [Inventory](benchmarks/build-compare-089/evidence-inventory.json), [preservation proof](benchmarks/build-compare-089/preservation-proof.json), [restored audit proof](benchmarks/build-compare-089/restored-audit-proof.json) and [restoration instructions](benchmarks/build-compare-089/REPRODUCE.md) make the evidence reviewable.

All raw results, every native service/smoke/oracle/cargo-test fixture, exact binaries/sources/locks, logs, policies and helpers remain at `D:\\Codex\\Kestrel\\work\\perf-089`. Only regenerable target-build/Python caches are omitted from ZIPs, with explicit path/size inventory; originals remain intact. Mutable stdout logs are excluded from frozen inputs and copied only after their processes end. A post-timing read requested a nonexistent bookkeeping filename; its error record is retained. The first reporting helper then failed on a flat-versus-nested source-hash schema lookup before writing conclusions; its exact helper and raw error are retained alongside the corrected helper. The frozen audit passed on its first run and no benchmark input or decision changed.

[Post-timing source comparison](benchmarks/build-compare-089/stock-to-diagnostic-source.json) retains every stock/diagnostic file SHA and the full diff inside the archives. It identifies two unconditional maintenance-result/control-flow rewrites in otherwise feature-disabled diagnostic source. They are a source hypothesis, not the measured cause of 088/089 outcomes. Use a new experiment number, 090 or later, to restore the original feature-disabled execution shape in an isolated diagnostic trial, verify native/byte/protocol/recovery behavior, and predeclare stronger complete balanced controls before any new timing. Preserve 086–089 and all failed blocks; never relax limits, reduce synchronization/ACK durability, switch to candidate/B or repeat only bad cases. Diagnostic work is not a substitute for a measured writer improvement.

A concrete integrated writer/query improvement still needs the complete native, six-profile/minute/overload/scan, memory, source/retry/crash/corruption, historical-format, exclusive-writer, competitor and restored-audit release checks. This study refreshes no competitor result. The private repository, supported engine and frozen overnight report remain unchanged. The fresh-profile reset is prepared and separately waiting for full Codex exit; no app was force-closed and no old task/chat/automation was resumed.

[088 controlled regressions](WRITER_OVERHEAD_088.md), [087 diagnostic correctness](WRITER_TRACE_087.md), [086 service failures](SERVICE_D_086.md), [0.3.17 release requirements](RELEASE_TARGET_0_3_17.md), [complete history](BENCHMARK_HISTORY.md).
'''
target = REPO / 'BUILD_COMPARE_089.md'
assert not target.exists()
target.write_text(report, encoding='utf-8', newline='\n')
readme = REPO / 'README.md'
text = readme.read_text(encoding='utf-8')
lines = text.splitlines()
assert lines[2].startswith('**Controlled writer qualification:**')
lines[2] = '**Controlled default-build investigation:** [089 completes 216 cases and 2.16 million requests](BUILD_COMPARE_089.md) with zero loss and no candidate guard failures. Eight A/A checks fail, so all comparison families remain unqualified. [088 calibrated write regressions](WRITER_OVERHEAD_088.md), [087 diagnostic correctness](WRITER_TRACE_087.md) and every prior result remain preserved. Supported 0.3.16 is unchanged; 0.3.17 is not qualified.'
readme.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
with (REPO / 'BENCHMARK_HISTORY.md').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('\n## Controlled default-build investigation 089 — October 8, 2026\n\n[Three matched-toolchain source/build controls](BUILD_COMPARE_089.md): 464 native test executions, eight byte-equivalent stores, 32 cross-reopens, 32 SQLite comparisons and four wire/setup variants pass. All 216 timed cases, 2.16 million offers and 110,268 reopened ACK batches pass correctness with zero loss. No candidate guard fails, but eight of 117 A/A checks fail across six of nine required scopes; every family remains unqualified overall. Original rebuild, version-only and feature-disabled diagnostic source comparisons do not establish exclusive causality, speed gains, tracer overhead, competitor wins or a release. Complete raw evidence/restored audit and post-run reporting failure are preserved; 088 remains unchanged.\n')
with (REPO / 'RELEASE_TARGET_0_3_17.md').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('\n[089 matched-toolchain default-build controls](BUILD_COMPARE_089.md) add 464 native test executions and byte/wire/SQLite/cross-reopen qualification before 216 fresh service cases. All 2.16 million requests succeed with zero loss, and no candidate guard fails. Eight A/A checks fail across required full/half scopes, so complete build/source compatibility remains unqualified. These new artifacts do not overturn 088 or qualify tracing overhead, an engine gain, a competitor sweep or 0.3.17. Next isolate unconditional maintenance control-flow changes with original feature-disabled execution shape under a new numbered trial and stronger complete controls; preserve all prior failures and every integrated release gate.\n')
shutil.copy2(ROOT / 'work/finish_089.py', OUT / 'finish_089.py')
shutil.copy2(ROOT / 'work/preserve-089.log', OUT / 'preserve-089.log')
print(json.dumps({'report': str(target), 'parts': len(preservation['parts']),
    'files': preservation['files'], 'supported': '0.3.16', 'qualified': False}))
