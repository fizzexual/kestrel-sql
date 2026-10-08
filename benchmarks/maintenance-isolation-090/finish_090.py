"""Write a report from the complete independently restored trial090 decisions."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path('D:/Codex/Kestrel')
W = ROOT / 'work/perf-090'
REPO = ROOT / 'outputs/kestrel-sql'
OUT = REPO / 'benchmarks/maintenance-isolation-090'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


a, run = load(W / 'audit.json'), load(W / 'paired-service.json')
preserved, restored = load(OUT / 'preservation-proof.json'), load(OUT / 'restored-audit-proof.json')
assert preserved['complete'] and restored['passed']
assert restored['native_launches'] == restored['timing_reruns'] == 0
assert all(s['passed'] for s in a['scopes'] if s['family'] == 'restored-default')
assert (a['identity_failed_total'], a['candidate_failed_total']) == (2, 0)
assert all(sha(REPO / n) == v for n, v in load(W / 'unchanged-supported-source.json').items())
decisions, latency, memory = [], [], []
for s in a['scopes']:
    decisions.append(f"| {s['family']} | {s['scope']} | {s['identity_failed']}/13 | {s['candidate_failed']}/13 | {'Pass' if s['passed'] else 'Fail'} |")
    if s['scope'] != 'full':
        continue
    for r in s['summaries']:
        ca, ba = r['comparisons']['primary_candidate_over_a'], r['comparisons']['identity_b_over_a']
        for metric in ['overall'] + (['query', 'append'] if r['profile'] == 'write' else []):
            latency.append(f"| {s['family']} | {r['profile']}/{metric} | {r['variants']['baseline_a']['median_case_p99_ms'][metric]:.4f} | {r['variants']['candidate']['median_case_p99_ms'][metric]:.4f} | {ca['paired_ratios'][metric]['median']:.6f} | {ba['paired_ratios'][metric]['median']:.6f} |")
        memory.append(f"| {s['family']} | {r['profile']} | {ca['paired_ratios']['peak']['median']:.6f} | {ca['median_peak_difference_bytes']/1024:.1f} | Pass |")
report = f'''# Maintenance source isolation and writer qualification 090

October 8, 2026. **The isolated corrective default build passes every compatibility gate in the full cohort and both independent halves. Complete writer-tracing qualification still fails: write overall p99 A/A misses its 5% range in both halves.** All 144 cases pass correctness and no candidate numerical guard fails. Supported KestrelSQL remains **0.3.16**. This is a scoped default compatibility milestone, not an engine speed improvement, qualified low-overhead tracer, competitor sweep or 0.3.17 release.

## Implemented correction

[089](BUILD_COMPARE_089.md) identified two unconditional maintenance-result/control-flow rewrites in otherwise feature-disabled diagnostic source. Trial090 changes only an isolated copy of `src/live.rs`: mutually exclusive compile-time blocks select the original supported `match archive.compact_small()` and short-circuit reclaim condition when writer tracing is disabled, while retaining the exact corrected 087 traced maintenance statements when enabled. There is no new runtime switch. Synchronization, ACK/receipt ordering, queue budgets, maintenance frequency, pinned read views, error/poison handling and package/dependency versions are unchanged.

[Source isolation proof](benchmarks/maintenance-isolation-090/maintenance-source-isolation-proof.json) preserves the original/default/traced statement blocks and exact before/after source hashes; the complete diff is in the evidence archives. Original stock statements are compared after newline decoding; original CRLF files remain untouched and the corrected 087 LF source retains its line endings. Every other copied source/lock/manifest/example/test file is byte-exact. A new source path/compiler layout remains a causality limit: passing compatibility does not prove that these statements caused 088's regressions. All prior results, including [088](WRITER_OVERHEAD_088.md) and 089's failures, remain intact.

Both new artifacts still report version 0.3.16 for a controlled comparison. They are clearly labeled `restored-default` and `restored-writer` isolated trial artifacts; they do not replace the supported executable or constitute adoption. The baseline is the exact untouched stock-016 artifact built and preserved in 089.

## Correctness before timing

[Build proof](benchmarks/maintenance-isolation-090/build-proof.json) records **322 fresh native test executions**: default 78 and writer 83 tests each in debug/release. Five strict lint modes pass: default, publication-only, writer, fault-only and writer+fault. Two fresh D: feature targets use rustc/cargo 1.97.1, x86_64-pc-windows-msvc, offline locked existing dependencies, thin LTO/one codegen unit and incremental off, with extra ambient flags absent. No formatting, installation, dependency upgrade or network work occurred. Timed default/writer service artifacts contain no fault environment hooks; optional diagnostic fields/getters remain absent from the default artifact.

[Oracle proof](benchmarks/maintenance-isolation-090/oracle-proof.json) records **104 external native commands**. Eight sequence/oversized Archive stores across original 016, untouched stock 089 and both 090 variants are byte-equivalent; **32 full cross-reopens** and **48 independent SQLite comparisons** pass, including empty ranges and signed-i64 bounds. Ten native live modes exercise 96 named batches, exact retry/collision/empty-validation/pinned views, eight concurrent producers, a real catalog-pending-directory failure with unknown outcome and poisoning, and cold reopen/retry. Six original 016 CLI checks reopen both variants' sequential/concurrent/failure stores. Default and traced sequential stores are byte-equivalent. All three bridge variants preserve Stats fields; only the traced build accepts the empty diagnostic request and it rejects extra parameters.

All three complete setup smokes pass and are excluded from every performance gate. Four invalid orders, four resource mutations and four traced-record mutations (wrong generation/key, drop count and invalid epoch) are rejected before timing. Historical broad source/crash/process-kill qualification is reused, not newly rerun; controlled directory failures are not physical power-loss tests.

## Fixed balanced cohort

[Policy](benchmarks/maintenance-isolation-090/policy.json) was declared before source copying/edits/native work. [Timing freeze](benchmarks/maintenance-isolation-090/timing-freeze.json) records every dependency hash after correctness and before the first timed case. Twelve rounds form two independently complete six-permutation halves, balancing pair order and slot in every family/profile:

| Family | A and B | Candidate | Limits |
| --- | --- | --- | --- |
| restored-default | Exact untouched stock-016 artifact from089 | Corrected090 feature-disabled default | 088 compatibility 10% |
| restored-trace | Exact corrected 090 default artifact | Same corrected source with writer-trace enabled | 088 overhead 5% |

The **144 fresh serial stores** each begin with 1M rows and use 64 clients, 100-row anonymous batches, group delay 0, retry index 0, queue capacity 256 and 2-second expiry. Read offers 2,000/s for 8 seconds. Write offers 500/s for 20 seconds with 25% writes. Longer write windows were declared before any native work; this is a complete new cohort, not a direct 088/089 before/after comparison or selective repeat. Offered-rate caps are not measured maximum capacity.

Compatibility A/A p99/rate ranges are 0.90–1.10; candidate p99 <=1.10 and achieved-window rate >=0.90. Tracing A/A ranges are 0.95–1.05; candidate p99 <=1.05 and rate >=0.95. Zero losses are required. Native peak ratio and additional 2 MiB guards remain exactly088. Every family must pass full and both halves; C/B remains diagnostic only. Counts overlap full/half scopes and read overall/query populations and are not independent statistical observations.

The cohort ran **{run['started_utc']} through {run['completed_utc']}**. No builds, external copying/hashing/packaging/cleanup/Git or other benchmarks overlapped. Only light status-tail reads ran alongside timing. Resource callbacks/getters/reopen/reference/CRC checks run outside each arrival/drain window. Post-run process exclusion and waiting reset-worker identity/owner checks pass before the frozen raw audit.

## Complete accounting and decisions

All **{a['successful']:,}/{a['offered']:,} offered requests succeed**, with zero errors/loss/drop/expiry/unexecuted requests. All **{a['acknowledged_batches']:,} acknowledged 100-row batches** survive reopen with exact atomic counts/sums and no unacknowledged-but-committed batch. **{a['numpy_windows']:,} NumPy windows** and **{a['full_crc_bytes']:,} full-CRC row-data bytes** pass. All **{a['traced_requests_correlated']:,} traced ACKs** map exactly to retained fixture keys/publication generations with complete chronology, counters/stages and zero dropped events. Every **{a['events_over_100ms']:,} individual service sample above 100 ms** remains in the audit. A late untraced stock baseline has overall p99 = 390.4667 ms and append p99 = 474.7500 ms, with zero loss; it is preserved and included in every applicable decision.

| Family | Scope | Failed A/A | Failed candidate | Required decision |
| --- | --- | ---: | ---: | --- |
{chr(10).join(decisions)}

Default compatibility passes every required scope. Across the complete study, **2/78 A/A checks fail and 0/78 candidate guards fail**. Both failures are tracing-family write overall p99: paired B/A=0.902647 in the first half and1.059271 in the second. Its full control=1.007443 passes because the deviations have opposing directions; that cannot override the required half failures. Read, write-query/append, rate, loss and both memory criteria pass every full/half scope. Complete tracing overhead remains unqualified.

## Full-cohort observations

Times are medians of case p99 values; ratios are medians of within-round pairs and need not equal the quotient of displayed medians. Passing compatibility does not establish a speed gain.

| Family | Profile/metric | A median ms | C median ms | Paired C/A | Paired B/A |
| --- | --- | ---: | ---: | ---: | ---: |
{chr(10).join(latency)}

The corrected default's paired write overall p99 is 1.016062 (about 1.6% higher) and append p99 is 1.009796 (about 1.0% higher), with passing 10% controls and full/half guards. The tracer's apparently lower full write overall p99 is not a qualified gain or complete overhead bound because the independent half calibration fails. This study supplies no new competitor ranking and omits minute/mixed/overload/scans and the full integrated release matrix.

## Native resources and measurement limits

[GetProcessMemoryInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo) and [PROCESS_MEMORY_COUNTERS](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters) provide native peak working set. The sample includes startup/seed/workload through the post-load sample before trace serialization/reopen; it does not isolate allocations or measure full-lifetime peak RSS. Every full/half memory criterion passes. The traced full write paired peak ratio is 1.013953, within its fixed guard.

| Family | Profile | Paired C/A peak | Median paired difference KiB | Both full guards |
| --- | --- | ---: | ---: | --- |
{chr(10).join(memory)}

[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes) supplies native charged CPU with a 100 ns representation unit, not guaranteed resolution. CPU remains diagnostic; zero read increments do not prove zero cost. Failed complete write-overhead qualification prevents exclusive interpretation of traced stalls as uninstrumented p99, a physical disk/OS cause or an end-to-end decomposition.

## Preserved evidence and next work

**{len(preserved['parts'])} bounded archive parts preserve {preserved['files']:,} files/{preserved['logical_bytes']:,} logical bytes.** Complete ZIP/member CRC/SHA/size/exact-set checks, original-byte revalidation, exact frozen raw-audit replay and post-replay member checks pass. The independent restored tree is `D:\\Codex\\Kestrel\\work\\restored-maintenance-090`; raw quantiles/conservation/resources/trace relations/all full/half decisions replay exactly with **zero Native launches or timing reruns**. [Inventory](benchmarks/maintenance-isolation-090/evidence-inventory.json), [preservation proof](benchmarks/maintenance-isolation-090/preservation-proof.json), [restored audit](benchmarks/maintenance-isolation-090/restored-audit-proof.json) and [instructions](benchmarks/maintenance-isolation-090/REPRODUCE.md) make all evidence reviewable.

Every raw result/store/test/oracle/smoke/source/binary/lock/log/proof/helper remains at `D:\\Codex\\Kestrel\\work\\perf-090`. Only regenerable target/Python caches are omitted with explicit path/size inventory; originals remain intact. The first preparation assertion expected reclaim as a separate if rather than the original && short-circuit. It failed before source correction or native work; its exact partial sources/policy/helper/error are preserved under failed-preparation-v1. Correctedv2 resumes with byte-identical original policy and unchanged thresholds. An earlier apply_patch context mismatch rejected atomically without mutation. The frozen native raw audit passed first try; no timed input/result or gate was edited or selectively rerun. Mutable stdout is excluded from frozen dependencies and copied only after processes end.

The source correction is now qualified for default compatibility in these two profiles. Keep it isolated pending complete integrated checks. Before relying on correlated writer traces for optimization, use 091 or later with stronger predeclared complete observations (for example, 24 rounds/two complete 12-round halves under the same limits) and exact unchanged repeated controls; preserve every090 failure. A concrete writer improvement must follow an actual measured bottleneck and preserve all synchronization, ACK/retry/source/pinned-view contracts. Do not substitute diagnostic work for an engine improvement, relax thresholds, lower durability or call passing read subsets all-benchmark wins.

Actual adoption/release still requires full native/six-profile service/minute/overload/scans/memory/source/retry/crash/corrupt/historical-format/exclusive-writer/competitor/restored-audit qualification. The supported core and frozen overnight report are byte-exact; the repository remains private/local with all history preserved. The separate fresh-profile reset is still prepared and waiting for full Codex exit, not executed.

[089](BUILD_COMPARE_089.md), [088](WRITER_OVERHEAD_088.md), [087](WRITER_TRACE_087.md), [086](SERVICE_D_086.md), [release requirements](RELEASE_TARGET_0_3_17.md), [complete history](BENCHMARK_HISTORY.md).
'''
target = REPO / 'MAINTENANCE_ISOLATION_090.md'
assert not target.exists()
target.write_text(report, encoding='utf-8', newline='\n')
readme = REPO / 'README.md'
lines = readme.read_text(encoding='utf-8').splitlines()
assert lines[2].startswith('**Controlled default-build investigation:**')
lines[2] = '**Maintenance source correction:** [090 passes every default compatibility gate](MAINTENANCE_ISOLATION_090.md) in two profiles/full/both halves. All 1.872 million requests and 179,280 reopened ACK batches pass correctness. Tracing remains unqualified because two half-cohort A/A checks fail; no candidate guard fails. [089](BUILD_COMPARE_089.md), [088 regressions](WRITER_OVERHEAD_088.md) and all history remain preserved. Supported 0.3.16 is unchanged; this is compatibility, not a speed gain or 0.3.17 release.'
readme.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
with (REPO / 'BENCHMARK_HISTORY.md').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('\n## Maintenance source isolation 090 — October 8, 2026\n\n[Corrective source isolation](MAINTENANCE_ISOLATION_090.md) restores original feature-disabled maintenance statements while preserving traced behavior.322 Native test executions/five lint modes and 104 untimed commands pass byte/cross-reopen/SQLite/named/concurrent/controlled unknown-outcome/old-format/wire checks. All 144 service cases, 1.872 million requests and 179,280 reopened ACK batches pass correctness. Default compatibility passes full/both halves; complete tracing qualification fails two write-overall A/A half controls, with 0 candidate failures. All stalls, failed preparation and complete raw/restored evidence remain preserved. Supported 0.3.16 is unchanged; no engine gain/competitor win/release claim.\n')
with (REPO / 'RELEASE_TARGET_0_3_17.md').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('\n[090 maintenance-source correction](MAINTENANCE_ISOLATION_090.md) now passes every default compatibility criterion in full/two independent halves for read/write profiles. All 1.872 million requests succeed with zero loss and 179,280 ACK batches survive reopen. Complete writer-trace overhead still fails two half-cohort write-overall A/A checks despite passing all candidate guards. The source correction remains isolated; this does not qualify a speed gain, full service/recovery/competitor matrix or 0.3.17. Strengthen unchanged controls under a new numbered complete trial before tracing-based attribution; retain all prior failures and every integrated gate.\n')
for n in ['finish_090.py', 'preserve-090.log']:
    shutil.copy2(ROOT / 'work' / n, OUT / n)
print(json.dumps({'report': str(target), 'default_compatibility': True, 'trace_qualification': False,
    'files': preserved['files'], 'parts': len(preserved['parts']), 'supported': '0.3.16'}))
