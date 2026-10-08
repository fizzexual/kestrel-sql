"""Document rejected 093 and privately commit all verified evidence, preserving core/history."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
ROOT=Path('D:/Codex/Kestrel');R=ROOT/'outputs/kestrel-sql';W=ROOT/'work/perf-093';O=R/'benchmarks/incremental-reclaim-093'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):
    p=subprocess.run(['git','-c',f'safe.directory={R.as_posix()}','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(R),*args],capture_output=True,text=True)
    assert p.returncode==0,(args,p.stdout,p.stderr);return p.stdout.strip()
parent='519cda3e8edea07a0333e09aec394e2407fd688a'
assert git('rev-parse','HEAD')==parent and git('status','--porcelain')=='?? benchmarks/incremental-reclaim-093/'
assert load(O/'restored-audit-proof.json')['passed'] and load(O/'restored-audit-proof.json')['native_launches']==0
directory_proof=load(O/'directory-restoration-proof.json');assert directory_proof['passed']
a=load(W/'loss-aware-audit.json');p=load(O/'preservation-proof.json');timing=load(W/'paired-service.json')
assert a['failed_experiment_audit_passed'] and not a['all_required_scopes_passed'] and a['lost']==2650
diagnostics=load(ROOT/'work/load-stage-diagnostics-093.json')
assert diagnostics['source_audit_sha256']==sha(W/'loss-aware-audit.json') and len(diagnostics['all_144_cases'])==144
diagnostic_table='\n'.join(f"| {s['variant']} | {s['median_case_mean_append_publication_ms']:.3f} | {s['median_case_mean_ACKs_per_group']:.3f} | {s['sync_share_of_all_summed_stages']*100:.2f}% |" for s in diagnostics['write_summaries'])
core={q.relative_to(R).as_posix():sha(q) for q in R.rglob('*') if q.is_file() and (q.relative_to(R).parts[0] in ['src','tests','examples'] or q.name in ['Cargo.toml','Cargo.lock','OVERNIGHT_2026-10-07.md']) and '.git' not in q.relative_to(R).parts and 'target' not in q.relative_to(R).parts}
assert sha(R/'OVERNIGHT_2026-10-07.md')=='1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
table=[]
for s in a['scopes']:
    row=next(r for r in s['summaries'] if r['profile']=='write')
    aa=row['comparisons']['identity_b_over_a']['paired_ratios'];ca=row['comparisons']['primary_candidate_over_a']['paired_ratios']
    table.append(f"| {s['scope']} | {aa['overall']['median']:.6f} | {aa['append']['median']:.6f} | {ca['overall']['median']:.6f} | {ca['append']['median']:.6f} | {s['identity_failed']}/15 | {s['candidate_failed']}/17 | {s['goal_failed']}/2 |")
failures=[]
for s in a['scopes']:
    for group,key in [('A/A','identity_checks'),('candidate guard','candidate_guards'),('improvement goal','goals')]:
        for c in s[key]:
            if not c['passed']:failures.append(f"- {s['scope']}, {c['profile']}, {group}: {c['criterion']}.")
lossrows='\n'.join(f"| {c['case_index']} | {c['round']} | {c['variant']} / {c['binary']} | {c['queue_dropped']} | {c['latency_ms']['p99']:.4f} | {c['operation_latency_ms']['append']['p99']:.4f} | {c['publication']['dispatch_lag_ms']['max']:.4f} |" for c in a['loss_cases'])
report=f'''# Incremental Live reclamation experiment 093

October 8, 2026. **Rejected: no qualified speed gain or supported adoption.** The complete 144-case cohort records **2,650 queue drops**, including 765 in the default control and 1,885 in the candidate. Five of 45 A/A checks, two of 51 candidate guards and two of six improvement goals fail across the required full/half scopes. Lower successful-operation medians do not override loss, calibration or exact goal failures. Supported version remains **0.3.16**; **0.3.17 remains unqualified with no justified release date**. Historical competitor, minute and overload losses remain unresolved.

All 1,872,000 offered requests are accounted for: 1,869,350 execute successfully, 2,650 drop at the bounded producer queue, zero expire and zero return execution errors. Every one of **178,622 acknowledged 100-row batches** survives reopen with exact atomicity and sums. All 144 stores pass independent complete metadata/payload checksums and NumPy row-multiset comparison, covering **{a['full_crc_bytes']:,} row-data bytes** plus 2,880 query windows. Data correctness after ACK passes; this does not qualify performance, source replay, crash boundaries or a release.

## Isolated implementation and correctness

Source is copied from exact 091/090 restored source into D:/Codex/Kestrel/work/perf-093/source. Only Cargo.toml, src/archive.rs and src/live.rs change behind the explicit `incremental-reclaim` feature. An internal method removes at most 20 eligible files every eight inserted Live groups, replacing the candidate's original full reclaim every 32 groups. The default build and public full-reclaim body remain exact. Version/dependencies, publication/sync/ACK, writer ownership, receipt chains, pins, orphan treatment and partial-error behavior are preserved. A successful-deletion budget does not bound directory scanning or filesystem call latency. Nominal 80 deletions per 32 groups exceeds roughly 65 newly obsolete files; fixture ceilings are not arbitrary-history bounds.

New tests cover zero/one/twenty budgets, exact data/full-reclaim comparison, pinned snapshots, named receipts/retries/collisions, exclusive ownership, cold reopen, orphan preservation and deletion-error repair without poison. Anonymous and named 2,048-group tests check explicit 192-file/16-MiB fixture ceilings every eight groups. **490 native debug/release test executions and three strict lint modes pass**, including combined fault/trace features. **56 external oracle commands plus four owned bridge initial/reopen launches** check six exact baseline/candidate/old016 byte fixtures, 18 cross-opens, 24 SQLite comparisons, 320 named ACKs, repeats/collisions, original016 reads and six cross-process writer rejections. Historical crash/source/process-kill coverage is reused; it is not a newly executed cut-point or physical power-loss qualification for this change.

## Fixed complete benchmark design

The original [policy](benchmarks/incremental-reclaim-093/policy.json) precedes source copying, editing and builds. [Service policy](benchmarks/incremental-reclaim-093/service-policy.json) maps identical order/workload/limits into the existing relocated 091 harness. Fresh matched default A/A and candidate artifacts, 24 rounds, two independently balanced 12-round halves, all six permutations twice per profile/half, seed 9308 and alternating profiles yield 144 fresh serial D: stores. Each begins with 1M rows, 64 clients, 100-row batches, zero group delay/retry index and a 256-request producer queue with two-second expiry. Read load is 2,000/s for eight seconds; 25%-write load is 500/s for 20 seconds.

All 5% p99/rate/Native-peak controls, extra 2 MiB, zero loss, disk A/A 0.90–1.10, candidate disk <=1.10 and extra 2 MiB remain unchanged. Fixed write improvement goals are overall C/A <=0.95 and append C/A <=0.90 in full and both halves. C/A is the sole primary comparator; C/B is diagnostic. CPU and accumulated stage totals are diagnostic. Native peak includes startup/seed/load before getter/reopen, not isolated allocations or full-lifetime RSS. No selective reruns, excluded stalls, extra rounds, changed limits or durability reductions occur.

Timing ran {timing['started_utc']} through {timing['completed_utc']}; all children ended before audit/copy/hash/package/Git. No other task-owned heavy workload overlapped. The separately prepared reset remained waiting for full Codex exit; it has not executed.

| Scope | Write overall B/A | Write append B/A | Write overall C/A | Write append C/A | Failed A/A | Failed guards | Failed goals |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(table)}

These are medians of paired round ratios, not ratios of pooled p99s or every-request bounds. Full write overall C/A is about 19% lower; append is about 10% lower. The exact full append ratio 0.900174 exceeds 0.90 and stays failed; the second half also misses that goal. The first half append A/A and second-half overall/query A/A fail. All read/resource/disk numerical guards pass, but complete qualification fails. Overlapping full/half populations are not independent additional experiments.

Every failed criterion:

{chr(10).join(failures)}

## Retained backlog and failures

| Case | Round | Variant / binary | Queue drops | Overall p99 ms | Append p99 ms | Maximum dispatch lag ms |
| --- | --- | --- | ---: | ---: | ---: | ---: |
{lossrows}

All **{a['events_over_100ms']:,} executed samples above 100 ms** remain in raw successful latency populations and the complete audit. Dropped requests remain in offered denominators and zero-loss decisions. Missing dropped identities are reconstructed by exact offer-range set difference; intended operations are deterministically reconstructed from the unchanged generator, never described as recorded execution. Arrival scheduling remained within several milliseconds in both loss cases, while writer publication/backlog was high. Publication stage totals subtract the seed before description; recorded stage maxima include seed and cannot be called load maxima. These observations support investigation, not exclusive engine/disk/OS cause or p99 decomposition. No unrelated app is stopped or computer setting changed.

The [post-seed descriptive analysis](benchmarks/incremental-reclaim-093/load-stage-diagnostics-093.json) retains every case and subtracts seed stage totals before aggregation. Mean group publication cost is high in all variants; the median case's mean is not a per-group tail. Synchronization shares describe summed stages and do not identify the physical cause or explain p99 exclusively. These results are not a controlled direct before/after comparison with another numbered trial.

A post-cohort read-only Windows storage check reports D: on a CT1000BX500SSD1 SATA SSD, healthy/online, with Ultimate Performance already active. No settings change. This snapshot does not measure disk latency, thermal/cache state or explain publication stalls; [observation](benchmarks/incremental-reclaim-093/storage-observation-093.json).

| Variant | Median case mean append publication ms | Median case mean ACK requests per group | Two sync stages / all summed stages |
| --- | ---: | ---: | ---: |
{diagnostic_table}

The frozen zero-loss auditor stops at case112 raw cardinality. Its exact source/log/error remain under failed-zero-loss-audit-v1. A separate supplemental loss-aware auditor verifies all 144 raw outcomes, drop/expiry conservation, scheduler timestamps, ACKs, full current stores and the original unchanged gate functions. Six malformed outcome records are rejected. This validates a failed experiment; it does not relax qualification. A synthetic pre-timing validator first lacked a derived operation-latency field; exact failed fixture/helper/log is retained and correction changes only that synthetic fixture. The first postflight wrapper mistook its own parent command text for another Python job; it stopped before auditing. Exact failure/checker remains, and a separate unchanged guard invocation passes. No failed result is removed.

## Preservation and next work

All originals remain at D:/Codex/Kestrel/work/perf-093. **{len(p['parts'])} bounded ZIPs preserve {p['files']:,} files / {p['logical_bytes']:,} logical bytes**, including every raw store/stream, failed and successful source, binary, policy, native unit/oracle fixture, excluded smoke and helper. Only regenerable build/Python caches are excluded with an explicit inventory; originals remain. [Restored audit proof](benchmarks/incremental-reclaim-093/restored-audit-proof.json) checks every CRC/SHA/size/set, every raw/lost outcome, complete independent store reference and exact full/half decision, then every post-replay hash/set, with **zero Native launches or timer reruns**. The packager's initial stdout snapshot is additional setup evidence; its final closed complete stdout is separately preserved after packaging. No credentials/reset-control files are packaged. [Reproduce](benchmarks/incremental-reclaim-093/REPRODUCE.md).

An explicit [directory supplement](benchmarks/incremental-reclaim-093/directory-restoration-proof.json) preserves all {directory_proof['noncache_directory_count']:,} non-cache directories, including empty failure markers omitted by file-only ZIP entries. Exact original/restored directory sets and every original/restored preserved file SHA/size are verified again, without Native/timer reruns.

Use a new number for the next investigation. Inspect actual per-group durable publication/queue tails and controlled publication/reclamation cut-point recovery, including the candidate's changed maintenance cadence. First separate seed cost from load, ACKed operations from producer drops, and control instability from candidate behavior. Preserve synchronization, publication-before-ACK, pins/ownership/receipt/source/retry/error semantics. Do not blindly reduce the deletion budget, repeat only bad cases or extend rounds after seeing results. A concrete future change needs fresh predeclared balanced controls and complete six-profile/minute/overload/scan/memory/competitor/recovery/restoration gates before .17 adoption.

Supported source/tests/examples/Cargo/lock and the issued overnight report remain byte-exact; all prior Git history remains and everything stays private/local. [Measured deletion costs 092](RECLAIM_PHASES_092.md), [qualified scoped traces 091](TRACE_CONTROLS_091.md), [release requirements](RELEASE_TARGET_0_3_17.md).
'''
(R/'INCREMENTAL_RECLAIM_093.md').write_text(report,encoding='utf-8',newline='\n')
nav='**Latest engine candidate:** [093 incremental reclamation is rejected](INCREMENTAL_RECLAIM_093.md): 2,650 queue drops, five failed A/A checks and missed append goals. All 178,622 ACK batches pass full independent data/CRC audit and exact restoration; lower medians do not qualify a win. Supported 0.3.16 remains unchanged; .17 is unqualified.\n\n'
for n in ['README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md']:
    path=R/n;data=path.read_bytes();split=data.index(b'\n')+1;ending=b'\r\n' if b'\r\n' in data[:split] else b'\n'
    path.write_bytes(data[:split]+ending+nav.replace('\n',ending.decode()).encode()+data[split:])
closed=ROOT/'work/preserve-093.log';shutil.copy2(closed,O/'closed-preservation.log')
for name in ['load-stage-diagnostics-093.json','load-stage-diagnostics-093.log','load_stage_diagnostics_093.py','storage-observation-093.json','commit_093.py']:
    shutil.copy2(ROOT/'work'/name,O/name)
(O/'closed-preservation-log-proof.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),
    'sha256':sha(closed),'bytes':closed.stat().st_size,'copied_after_packager_exit':True,
    'initial_log_snapshot_in_archive_is_not_complete_packaging_stdout':True},indent=2)+'\n',encoding='utf-8')
names=['INCREMENTAL_RECLAIM_093.md','README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md','benchmarks/incremental-reclaim-093']
git('add','--',*names)
git('-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check')
assert all(sha(R/n)==h for n,h in core.items())
git('commit','-m','Preserve rejected incremental reclamation trial 093 and every loss')
head=git('rev-parse','HEAD');assert not git('status','--porcelain');git('merge-base','--is-ancestor',parent,head)
proof={'head':head,'clean':True,'all_prior_history_preserved':True,'supported_core_and_overnight_unchanged':all(sha(R/n)==h for n,h in core.items()),
    'no_remote_publication':True,'candidate_rejected':True,'lost':a['lost'],'no_qualified_engine_gain_or_release':True,
    'supported':'0.3.16','utc':datetime.now(timezone.utc).isoformat()}
(ROOT/'work/commit-093-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof),flush=True)
