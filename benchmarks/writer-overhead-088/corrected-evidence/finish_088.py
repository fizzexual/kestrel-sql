"""Save a complete, gate-derived report without changing the supported engine."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

ROOT = Path('D:/Codex/Kestrel')
W = ROOT / 'work/perf-088'
REPO = ROOT / 'outputs/kestrel-sql'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


audit = load(W / 'audit.json')
diagnosis = load(W / 'trace-group-diagnostics.json')
report = load(W / 'paired-service.json')
assert audit['correctness_passed'] and not audit['all_required_scopes_passed']
assert (audit['cases'], audit['identity_failed_total'], audit['candidate_failed_total']) == (288, 15, 12)
baseline_path = ROOT / 'work/perf-086/previous-062-baseline.json'
baseline = load(baseline_path)
assert all(sha(REPO / name) == digest for name, digest in baseline['core_source_sha256'].items())
assert sha(REPO / 'OVERNIGHT_2026-10-07.md') == '1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
shutil.copy2(baseline_path, W / 'unchanged-supported-core-baseline.json')
save(W / 'final-source-provenance.json', {'supported': '0.3.16', 'supported_core_unchanged': True,
    'core_source_sha256': baseline['core_source_sha256'], 'overnight_unchanged': True,
    'overnight_sha256': sha(REPO / 'OVERNIGHT_2026-10-07.md'),
    'no_new_engine_build_or_edit': True, 'utc': datetime.now(timezone.utc).isoformat()})
save(W / 'controller-poll-syntax-failure.json', {'scope': 'read-only tool orchestration, outside the native runner',
    'error': 'SyntaxError: Invalid or unexpected token',
    'cause': 'An extra quote followed the yield_time_ms property name in a polling tool call.',
    'tool_js_not_executed': True, 'native_cohort_uninterrupted': True,
    'native_or_timing_reruns': 0, 'corrected_by': 'Repeating only the read-only polling call with valid JavaScript.'})

rows = []
failures = []
for scope in audit['scopes']:
    rows.append(f"| {scope['family']} | {scope['scope']} | {scope['identity_failed']}/13 | {scope['candidate_failed']}/13 | Fail |")
    identities = {(c['profile'], c['criterion']): c['passed'] for c in scope['identity_checks']}
    for check in scope['candidate_guards']:
        if not check['passed']:
            calibration = 'passes' if identities[check['profile'], check['criterion']] else 'fails; unqualified difference'
            failures.append(f"| {scope['family']} | {scope['scope']} | {check['profile']}/{check['criterion']} | {calibration} |")

performance = []
memory = []
for scope in audit['scopes']:
    if scope['scope'] != 'full':
        continue
    for row in scope['summaries']:
        primary = row['comparisons']['primary_candidate_over_a']
        identity = row['comparisons']['identity_b_over_a']
        for metric in ['overall'] + (['append'] if row['profile'] == 'write' else []):
            a = row['variants']['baseline_a']['median_case_p99_ms'][metric]
            c = row['variants']['candidate']['median_case_p99_ms'][metric]
            ca = primary['paired_ratios'][metric]['median']
            aa = identity['paired_ratios'][metric]['median']
            calibration = 'Pass' if identity['identity_checks'][metric + '_p99'] else 'Fail / unqualified'
            performance.append(f"| {scope['family']} | {row['profile']}/{metric} | {a:.4f} | {c:.4f} | {ca:.6f} | {aa:.6f} | {calibration} |")
        memory.append(f"| {scope['family']} | {row['profile']} | {primary['paired_ratios']['peak']['median']:.6f} | {primary['median_peak_difference_bytes'] / 1024:.1f} | Pass |")

text = f'''# Controlled service compatibility and writer overhead 088

October 8, 2026. **Qualification fails. Supported KestrelSQL remains 0.3.16; 0.3.17 is not qualified and has no justified calendar ETA.** All 288 fresh cases pass scoped correctness and recovery, but 15 of 156 identical-binary checks and 12 of 156 candidate guards fail. Six candidate failures have passing corresponding controls. No new engine change, low-overhead qualification or competitor win is established.

The full-cohort default released-core build has a calibrated write-heavy overall p99 regression: paired candidate/A 1.234137, about **23.4% higher**. Its matching A/A is 0.928233 and passes the fixed 10% range. The clean-core default build's overall regression is also calibrated at paired 1.202270, about 20.2% higher. Its append difference is unqualified because that control fails. These compare preserved original executables with fresh 087 default artifacts; they do not isolate an engine change, compiler/layout effect or physical cause.

## Frozen comparison

The six exact executables come from released 0.3.16, clean query fix 061 and the corrected 087 default/writer builds. No compilation ran for 088. [Policy](benchmarks/writer-overhead-088/policy.json) and [timing freeze](benchmarks/writer-overhead-088/timing-freeze.json) identify every binary/source/harness SHA and case. Each family uses the same baseline executable twice, as A and B:

| Family | A and B | Candidate |
| --- | --- | --- |
| compatibility-released | Exact original 0.3.16 | 087 released-core default build |
| compatibility-clean | Exact original 0.3.17-dev.61 | 087 clean-core default build |
| overhead-released | Exact 087 released-core default | Exact 087 released-core writer tracing |
| overhead-clean | Exact 087 clean-core default | Exact 087 clean-core writer tracing |

Twelve rounds contain all six A/B/C permutations twice. Each six-round half independently includes every permutation and balances both pair order and slot. Four families, two profiles and three variants yield 288 fresh serial stores: 1M seed rows, 64 clients, 100-row anonymous append batches, zero deliberate grouping delay; read 2,000 offers/s for 8 s and 25%-write 500 offers/s for 8 s. The first six-round draft was strengthened before any native run, with every numerical limit unchanged. Both six-binary setup-smoke cohorts are preserved and excluded from all gates.

Compatibility A/A p99/rate limits are 0.90–1.10, candidate p99 <=1.10 and achieved-window rate >=0.90. Tracer A/A limits are 0.95–1.05, candidate p99 <=1.05 and rate >=0.95. Both require zero losses; native peak-working-set ratio and additional 2 MiB guards also apply. Every family must pass the full cohort and both halves. Candidate/B is diagnostic only and cannot replace candidate/A. Counts include overlapping full/half checks and read overall/query metrics with the same population; they are not independent statistical observations.

The cohort ran from {report['started_utc']} through {report['completed_utc']}. Builds, copying, hashing, packaging, cleanup and other timed jobs were stopped throughout. Resource callbacks, trace getters, correctness/reopen checks and final audits run outside arrival/drain timing. Python records the append receipt already returned by the native bridge; all variants use the same wrapper.

## Correctness and complete outcome accounting

All **{audit['successful']:,}/{audit['offered']:,} offers** succeed, with zero errors, drops, expiries or unexecuted requests. All **{audit['acknowledged_batches']:,} acknowledged 100-row batches** are present after reopen, with exact count/sum atomicity and no unacknowledged-but-committed batch. Independent NumPy comparisons cover **{audit['numpy_windows']:,} windows**, and full CRC checks cover **{audit['full_crc_bytes']:,} row-data bytes**.

All {audit['traced_requests_correlated']:,} traced append ACKs map exactly to unique fixture keys and publication generations. The audit checks chronological complete event ranges, attempt/generation conservation, all seven aggregate stage totals, catalog bytes, append/compaction/reclaim counts, inactive cycles and zero dropped records. Native tests, byte/retry/controlled-failure and original-version reopen qualification from 087 are reused, not newly rerun. This scoped cohort omits minute mixed, overload, scans, competitor refresh and full crash/source/power-loss qualification.

## Fixed full and half decisions

| Family | Scope | Failed A/A checks | Failed candidate guards | Required decision |
| --- | --- | ---: | ---: | --- |
{chr(10).join(rows)}

All failures are write-heavy overall or append p99. Read latency, write-profile query p99, achieved-window rate, zero-loss and both memory criteria pass in every full/half scope. Passing individual criteria do not override the failed required scopes.

## Full-cohort latency

Times are medians of case p99 values. Ratios are medians of within-round pairs and therefore need not equal the quotient of displayed medians. A failed corresponding control makes the difference unqualified, including apparent improvements.

| Family | Profile/metric | A median ms | C median ms | Paired C/A | Paired B/A | Matching control |
| --- | --- | ---: | ---: | ---: | ---: | --- |
{chr(10).join(performance)}

The released tracing build numerically exceeds its 5% write limits, while the clean tracing build appears faster. Their write controls fail, so neither establishes latency overhead or a speed gain. All slow samples remain included: **{audit['events_over_100ms']:,} individual service samples exceed 100 ms**.

| Failed candidate criterion | Scope | Metric | Corresponding A/A |
| --- | --- | --- | --- |
{chr(10).join(failures)}

## Native resource observations

[Windows GetProcessMemoryInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo) supplies native process memory counters; [PROCESS_MEMORY_COUNTERS](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters) defines the peak working-set field. The sample before any trace getter includes native startup, seed and workload through the post-load resource sample, and excludes trace serialization and reopen. It does not isolate tracer allocation or measure full-lifetime peak RSS. Every paired ratio and additional-memory criterion passes in full and both halves.

| Family | Profile | Paired C/A peak | Median paired difference KiB | Both full memory guards |
| --- | --- | ---: | ---: | --- |
{chr(10).join(memory)}

[GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes) supplies charged native user/kernel CPU with a 100 ns representation unit; that unit is not measurement resolution. CPU stays diagnostic only. Many read windows report zero charged increments, so their CPU ratios cannot establish zero cost or an overhead bound. Host resource observations use the unchanged harness monitor.

## Descriptive writer observations and next experiment

Optional tracing records {diagnosis['trace_event_counts']['append']:,} append groups, {diagnosis['trace_event_counts']['compact']:,} compactions and {diagnosis['trace_event_counts']['reclaim']:,} reclamations. The post-cohort [trace analysis](benchmarks/writer-overhead-088/trace-diagnostic-summary.json) retains each group in the evidence ZIPs. It associates 205 service samples over 100 ms with 43 distinct append groups. Pooled traced enqueue-to-completed-collection p99 is 46.1861 ms. That wait excludes pre-enqueue validation and includes collection; clock domains are not aligned for an exclusive end-to-end decomposition. Recorded synchronization contributes 58.2–66.7% of summed stage time across released traced write cases and 64.1–96.7% across clean traced cases. These observations come from instruments whose write-latency overhead failed qualification: they motivate hypotheses, not attribution of uninstrumented p99 or a storage/OS cause.

Next use a new experiment number, 089 or later, to inspect default source/build differences and compare a fresh untouched 0.3.16 build with feature-disabled diagnostic sources under the same declared toolchain/flags. Preserve the original artifacts as controls. Establish default-build compatibility and calibrated write controls before revising tracer overhead or interpreting instrumented tails. Predeclare fresh complete balanced controls, retain every failed block and keep all synchronization, ACK/receipt and queue-budget contracts. No selective repeat of 088, no lower durability and no relaxed limits. A concrete writer improvement still needs all integrated native, six-profile service, memory, source/retry/crash/corruption, historical-format, competitor and restored-audit release checks.

## Preserved evidence

All raw offer/results, ACK generations, native stores, post-load snapshots, initial/final policies, smoke stores, six executables, four exact source/lock/test trees, harness changes, qualification proofs and logs remain at `D:\\Codex\\Kestrel\\work\\perf-088`. The frozen auditor is unchanged and passed on its first run. One read-only polling JavaScript syntax error stopped before any tool action; the native cohort continued uninterrupted and its record is retained. Every prior experiment, release and failure remains intact.

[Restoration instructions](benchmarks/writer-overhead-088/REPRODUCE.md), [complete inventory](benchmarks/writer-overhead-088/evidence-inventory.json), [preservation proof](benchmarks/writer-overhead-088/preservation-proof.json) and [restored audit proof](benchmarks/writer-overhead-088/restored-audit-proof.json) specify all ZIP/member CRC, SHA, size and exact-set checks. The restored tree is `D:\\Codex\\Kestrel\\work\\restored-writer-088`; raw quantiles, conservation, correlations, scopes and descriptive group analysis must replay exactly without launching native processes or rerunning timing. Only regenerable Python caches are excluded and remain in the original tree. The private repository, supported engine and frozen overnight report remain unchanged; the separate profile reset is still waiting for full Codex exit.

[087 diagnostic correctness](WRITER_TRACE_087.md), [086 service regressions](SERVICE_D_086.md), [0.3.17 release requirements](RELEASE_TARGET_0_3_17.md), [complete history](BENCHMARK_HISTORY.md).
'''
target = REPO / 'WRITER_OVERHEAD_088.md'
assert not target.exists()
target.write_text(text, encoding='utf-8', newline='\n')
(W / target.name).write_text(text, encoding='utf-8', newline='\n')
readme = REPO / 'README.md'
contents = readme.read_text(encoding='utf-8')
old = '**Service-writer diagnostics:** [087 qualifies bounded optional tracing](WRITER_TRACE_087.md) in isolated released/clean cores. Archive bytes, retry/failure/reopen, concurrent ACK correlation and corrected bridge protocol pass. Tracing overhead and service speed are unmeasured; supported0.3.16 remains unchanged. [086 write-tail regressions](SERVICE_D_086.md) still block0.3.17.'
assert contents.count(old) == 1
new = '**Controlled writer qualification:** [088 fails compatibility and write-latency overhead gates](WRITER_OVERHEAD_088.md): 288 cases and 2.88 million operations pass correctness/reopen, while 15 A/A checks and 12 candidate guards fail. The default released-core build has a calibrated paired 23.4% write-heavy overall p99 regression. Memory/read guards pass; supported 0.3.16 remains unchanged. [087 diagnostic correctness](WRITER_TRACE_087.md) and [086 write-tail failures](SERVICE_D_086.md) remain preserved.'
readme.write_text(contents.replace(old, new), encoding='utf-8', newline='\n')
with (REPO / 'BENCHMARK_HISTORY.md').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('\n## Controlled writer overhead 088 — October 8, 2026\n\n[Fresh four-family qualification](WRITER_OVERHEAD_088.md): 288 cases, 2.88 million successful offers and 147,024 reopened ACK batches. Fixed full/two-half checks fail 15 A/A and 12 candidate criteria; six candidate failures are calibrated. Default released-core write overall p99 regresses paired 23.4%. Read/memory/rate/loss checks pass. All slow cases and raw evidence retained; no low-overhead or supported release claim.\n')
with (REPO / 'RELEASE_TARGET_0_3_17.md').open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('\n[088 default-build and tracer qualification](WRITER_OVERHEAD_088.md) now measures 288 fresh cases and verifies all 2.88 million operations, 147,024 ACK batches, reference windows and full CRC/reopen checks. Fixed full/half qualification fails 15 A/A checks and 12 candidate guards. Read/memory gates pass, but default-build write compatibility and tracer latency remain unqualified; full released-core default write overall p99 has a calibrated paired 23.4% regression. Inspect same-toolchain untouched/default-build provenance under new controls before interpreting traces or changing the writer. Supported 0.3.16 and all release gates remain unchanged.\n')
summary = {k: v for k, v in diagnosis.items() if k not in ['cases', 'append_group_records']}
save(W / 'trace-diagnostic-summary.json', summary)
save(W / 'decision-summary.json', {'trial': 88, 'correctness_passed': True, 'qualification_passed': False,
    'identity_failures': 15, 'candidate_failures': 12, 'calibrated_candidate_failures': 6,
    'all_read_memory_rate_and_loss_criteria_passed': True,
    'no_low_overhead_or_supported_promotion': True, 'supported': '0.3.16'})
print(json.dumps({'report': str(target), 'supported_core_unchanged': True, 'qualified': False}))
