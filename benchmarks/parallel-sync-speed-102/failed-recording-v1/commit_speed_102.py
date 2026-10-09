"""Record the complete rejected102 controls without changing supported engine."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,statistics,subprocess
R=Path('D:/Codex/Kestrel');H=R/'work';W=H/'perf-102';REPO=R/'outputs/kestrel-sql';OUT=REPO/'benchmarks/parallel-sync-speed-102'
PARENT='04bf4d7724da3c47abbb38aae72524313a2bc372'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):
 assert not p.exists(),p;p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def git(*args):
 cmd=['git','--no-optional-locks','-c','safe.directory=D:/Codex/Kestrel/outputs/kestrel-sql','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(REPO),*args]
 r=subprocess.run(cmd,capture_output=True);assert r.returncode==0,(cmd,r.stdout,r.stderr);return r.stdout
guards=sorted(H.glob('guard-final-102v2-*.json'));assert guards;guard=load(guards[-1])
assert guard['active_processes']==[] and guard['verified_idle_terminal_reset'] and guard['reset_phase']=='wait-expired-no-source-mutated'
assert git('rev-parse','HEAD').decode().strip()==PARENT and not git('diff','--name-only') and not git('diff','--cached','--name-only')
assert all(line.startswith(b'?? benchmarks/parallel-sync-speed-102/') for line in git('status','--porcelain').splitlines())
complete=load(W/'complete-audit-proof.json');nt=load(W/'native-audit.json');st=load(W/'audit.json');pack=load(OUT/'preservation-proof.json');rest=load(OUT/'restored-audit-proof.json')
assert complete['complete_original_and_restored_semantic_audit_passed'] and not complete['performance_qualified'] and pack['complete'] and rest['passed']
assert sha(W/'complete-audit-proof.json')==sha(H/'restored-parallel-sync-speed-102/complete-audit-proof.json')
assert [nt['identity_failed'],nt['candidate_guards_failed'],nt['goals_failed']]==[7,2,1]
assert [st['identity_failed_total'],st['candidate_failed_total'],st['goals_failed']]==[1,0,1] and st['lost']==0
supported={}
for n in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').decode().splitlines():
 assert hashlib.sha256(git('show','HEAD:'+n)).hexdigest()==sha(REPO/n),n;supported[n]=sha(REPO/n)
closed=OUT/'closed-continuation';assert not closed.exists();closed.mkdir()
for n in ['preserve-102.log','preserve_102.py','prepare_preserver_102.py','preserver-engine-102-proof.json','commit_speed_102.py','record_next_102.py','reusable-sync-worker-design-20261009.json']:
 shutil.copy2(H/n,closed/n)
shutil.copy2(guards[-1],closed/guards[-1].name)
save(closed/'supported-main-byte-proof.json',{'complete':True,'parent':PARENT,'files_sha256':supported,'supported_version':'0.3.16','source_tests_examples_Cargo_verification_and_overnight_unchanged':True})
save(closed/'post-preservation-record.json',{'closed_packager_stdout_sha256':sha(H/'preserve-102.log'),'no_new_native_or_timer_after_cohort_exit':True,'remote_backup_verified':False,'no_recent_raw_deleted':True,'reset_terminal_expired_not_armed':True})
native_rows=[];native_lines=[]
for scope in nt['scopes']:
 for c in scope['checks']:
  row={'history':scope['history'],'scope':scope['scope'],**{k:v for k,v in c.items() if not isinstance(v,list)}};native_rows.append(row)
  native_lines.append(f"| {scope['history']} | {scope['scope']} | {c['metric']} | {c['before_median_ns']/1e6:.6f} | {c['after_median_ns']/1e6:.6f} | {c['CA_median']:.9f} | {c['AA_median']:.9f} | {'pass' if c['AA_passed'] else 'FAIL'} | {'pass' if c['candidate_guard_passed'] else 'FAIL'} |")
service_rows=[];service_lines=[];diag=[];cases=load(W/'paired-service.json')['cases']
for scope in st['scopes']:
 for row in scope['summaries']:
  aa=row['comparisons']['identity_b_over_a'];ca=row['comparisons']['primary_candidate_over_a'];service_rows.append({'scope':scope['scope'],'profile':row['profile'],'variants':{v:{k:x for k,x in r.items() if k!='all_rounds'} for v,r in row['variants'].items()},'AA_medians':{k:x['median'] for k,x in aa['paired_ratios'].items()},'CA_medians':{k:x['median'] for k,x in ca['paired_ratios'].items()},'identity_checks':aa['identity_checks'],'candidate_guards':ca['candidate_guards']})
  for op in ['overall','query','append']:
   a=row['variants']['baseline_a']['median_case_p99_ms'][op];c=row['variants']['candidate']['median_case_p99_ms'][op]
   if a is None:continue
   service_lines.append(f"| {scope['scope']} | {row['profile']} | {op} | {a:.6f} | {c:.6f} | {ca['paired_ratios'][op]['median']:.9f} | {aa['paired_ratios'][op]['median']:.9f} | {'pass' if aa['identity_checks'][op+'_p99'] else 'FAIL'} | {'pass' if ca['candidate_guards'][op+'_p99'] else 'FAIL'} |")
  rounds=range(1,25) if scope['scope']=='full' else (range(1,13) if scope['scope']=='half_1' else range(13,25))
  for op in ['overall','query','append']:
   for metric in ['p50','p95','p99','max']:
    pairs=[]
    for rnd in rounds:
     p={c['variant']:(c['latency_ms'] if op=='overall' else c['operation_latency_ms'][op])[metric] for c in cases if c['profile']==row['profile'] and c['round']==rnd}
     assert len(p)==3
     if p['baseline_a'] is not None:pairs.append(p)
    if pairs:
     diag.append({'scope':scope['scope'],'profile':row['profile'],'operation':op,'metric':metric,'median_before_ms':statistics.median(p['baseline_a'] for p in pairs),'median_after_ms':statistics.median(p['candidate'] for p in pairs),'median_paired_CA':statistics.median(p['candidate']/p['baseline_a'] for p in pairs),'median_paired_AA':statistics.median(p['baseline_b']/p['baseline_a'] for p in pairs),'descriptive_not_additional_acceptance_gate':True})
save(OUT/'scope-results.json',{'native_all_checks':native_rows,'native_all_goals':nt['goals'],'service_all_scopes':service_rows,'service_all_goals':st['goal_checks'],'service_p50_p95_p99_max_descriptive':diag,'every_round_preserved_in_bounded_archives':True,'original_native_audit_sha256':sha(W/'native-audit.json'),'original_service_audit_sha256':sha(W/'audit.json')})
report=REPO/'PARALLEL_SYNC_SPEED_102.md';assert not report.exists()
report.write_text(f'''# Scoped synchronization speed 102: rejected

The complete native and service cohorts pass independent correctness and raw-result audits but fail the predeclared performance qualification. Native fails 7/30 identical-baseline controls, 2/30 candidate regression guards and 1/12 goals. Service fails 1/45 baseline controls and 1/6 goals, with 0/51 candidate guard failures. Supported 0.3.16 stays unchanged; this does not qualify 0.3.17 or an all-benchmark win.

The full service write p99 signal is 4.779300 to 4.391250 ms, paired C/A 0.905177392; append p99 is 8.343950 to 7.587600 ms, paired 0.881088393. The second half's append baseline control B/A 0.942783217 is below 0.95, and candidate C/A 0.955857742 misses <=0.90. That failure invalidates adoption despite attractive full-cohort medians. Native named maximum has C/A 1.052658974 full and 1.225254771 second half, both guard failures with failed corresponding baseline controls; their physical cause is not established. All stalls and all numerical failures remain.

## Fixed scope and unchanged code

Policy SHA256 `{sha(W/'policy.json')}` was declared before source/build/timing. All 42 source files are exactly the qualified 101 source, with no 102 engine edit. Normal A and B use one exact binary with async-reclaim and benchmark-shutdown. Candidate C adds only parallel-sync-101. Both original sync_all calls, join before rename/ACK, formats, receipt/source digests, retry/collision outcomes, ownership, pins, reclamation budgets, queue limits and dispatch/client/arrival/drain contracts remain. The shared baseline is isolated async20/every8, not the supported 0.3.16 default. No analytical061 integration, fault or trace/profile feature enters timed artifacts.

Native: 144 cases, 24 rounds, two independently balanced 12-round halves; both anonymous/named histories and all six A/B/C permutations twice per history/half. The unchanged uninstrumented100 probe performs 512 durable 100-row appends per case from 32,768 to 83,968 rows. Raw trial100/probe-baseline tags identify the reused probe, while the declared logical variants identify actual normal/candidate artifacts. All 73,728 publications and 73,872 historical catalogs/receipt sets are independently checked, including full current data/index/CRC, retry/pin/lease/cold checks. Corresponding normal/candidate data and historical receipt bytes match exactly. Full case CRC bytes: {nt['full_case_crc_bytes']:,}. Native CPU/RSS is not measured or claimed.

Service: 144 cases, 24 rounds, two separately balanced 12-round halves, all permutations twice per profile/half; 1M initial rows, 64 clients and 100-row append operations. Read uses 2,000 offers/s for 8 seconds; 25%-write uses 500 offers/s for 20 seconds. All {st['offered']:,} offered operations succeed: zero drops, expiries or execution failures. All {st['acknowledged_batches']:,} ACK batches, original generation/late data/full CRC/NumPy references reconcile; {st['full_crc_bytes']:,} full-current-store CRC bytes and 2,880 reference windows pass. All 288 timed initial/cold Native processes join actual background work and exit zero with stopped writer, empty queue and no maintenance errors. Resource samples/getters occur after drain and before cold reopen; physical archive inventory is after actual join. The {st['events_over_100ms']} events over 100ms are preserved. Native CPU ticks are diagnostic only; read samples can be zero and 100ns representation is not clock resolution. No exclusive stage attribution or physical disk explanation follows.

## Every native before and after

These are medians of case metrics in milliseconds and medians of within-round ratios; the quotient of displayed medians can differ from paired C/A. Full and both halves stay in the decision. Native half_0 is rounds0-11; half_1 is12-23. Speed goals require p50<=0.95 and p99<=0.90 C/A in every history/scope; all metrics require calibrated A/A0.95-1.05 and C/A<=1.05.

| History | Scope | Metric | Before ms | After ms | Paired C/A | A/A | Control | Guard |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
{chr(10).join(native_lines)}

## Every service p99 before and after

Service half_1 is rounds1-12; half_2 is13-24. The complete original093 loss/latency/window-throughput/memory/disk gates apply unchanged. Both write goals must pass full and both halves. All p50/p95/p99/max descriptions, goal rows, resource guards and controls are in scope-results.json; complete per-round raw data and ratios remain in the bounded archives.

| Scope | Profile | Operation | Before ms | After ms | Paired C/A | A/A | Control | Guard |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
{chr(10).join(service_lines)}

## Correctness, prerequisites and failed attempts

Fresh exact-feature suites: 94+94 normal and101+101 candidate tests, 390 total, plus two strict all-target Clippy modes. Four finite 12,000-group backlog cases reconcile48,000 ACKs/full original named receipts/CRC/NumPy and graceful shutdown: anonymous maxima83 files/480,697 bytes, named113/4,586,387, within fixed192 files/16MiB. Four excluded native smokes and two excluded service smokes pass, plus24 fresh SQLite/cold-reader CLI queries and29 pretime synthetic invalid controls. Prior101 recovery682tests,576coupled faults,72publication faults,18source faults,22corruption cases, CAT2/CAT3 and byte fixtures are explicitly reused, not freshly rerun or recounted. Controlled live-filesystem process exits do not qualify physical powerloss or real disk exhaustion.

All original13,630 frozen inputs and8 operational inputs keep their hashes. The initial sandbox declaration stopped on WinError5 before creating the trial. The old reset worker expired after its24-hour wait before any source mutation; the original waiting-state guard/startup stopped before any Native/cohort result. V2 changes only guard filename and validation of the actual terminal state, preserving source/binary/order/arrival/clock/metric/gates. The posttime combined guard command also stopped before its future copy/audit because its parent command line named that work; the unchanged guard was then called separately and passed. All helpers, stops and diagnostic records remain, with incomplete raw transcript coverage explicitly labeled.

## Complete restoration and next work

Preservation: {len(pack['parts'])} bounded ZIP parts, {pack['files']:,} files, {pack['directories']:,} directories, {pack['logical_bytes']:,} logical bytes. The qualified64MiB-chunk/80MiB-logical-part engine is reused byte-exact. Every member CRC/order/size/offset, full original/restored SHA and exact file/directory set passes before and after complete pure restored replay. All dependencies load only from the restored tree, replay equals complete-audit-proof.json, and no Native/performance timer or existing-file write occurs. Original work/perf-102 and work/restored-parallel-sync-speed-102 remain on D:. Only inventoried regenerable target/Python caches are excluded; originals remain. tmp, unit stores, failed setups, stalls and empty directories are included. Closed packager stdout is separately hashed after actual exit.

Evidence: [benchmarks/parallel-sync-speed-102](benchmarks/parallel-sync-speed-102/REPRODUCE.md), with every fixed scope, full independent audit, source/build/declaration/reset proofs, raw outcomes, failed attempts and archive inventory/layout. No102 remote backup is verified and no recent raw result is deleted. The prepared reset is terminal expired, not armed/waiting; fresh taskReady/result2, old taskDisabled, realC Codex home unchanged.

The next code hypothesis should address per-publication thread creation and completion overhead while preserving both original syncs and join-before-rename/ACK.102's normal/candidate mechanism makes that cost a testable hypothesis, not proof that it caused the failed tails. Declare a new number and fixed correctness/recovery/ownership/shutdown controls before implementation; fresh balanced performance comes only after those pass. Do not add rounds, choose favorable scopes, retune existing gates or reinterpret098/099/100/102. Integrated analytical/scan/six-service/minute/overload/competitor/source/retry/recovery/old-format/resource and justified061 gates still precede0.3.17. There is no justified release ETA.
''',encoding='utf-8',newline='\n')
line=b'**Latest controlled performance:** [102 scoped synchronization speed rejected](PARALLEL_SYNC_SPEED_102.md): 144 native + 144 service cases, 1,872,000 successful offers/zero loss and full restored correctness; native 7 controls/2 guards/1 goal fail, service 1 control/1 goal fail. No adoption; 0.3.16 remains supported.\r\n\r\n'
for n in ['README.md','BENCHMARK_HISTORY.md']:
 p=REPO/n;before=p.read_bytes();assert b'PARALLEL_SYNC_SPEED_102.md' not in before;cut=before.index(b'\n')+1;p.write_bytes(before[:cut]+b'\r\n'+line+before[cut:])
git('add','--','PARALLEL_SYNC_SPEED_102.md','README.md','BENCHMARK_HISTORY.md','benchmarks/parallel-sync-speed-102')
git('-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check')
staged=git('diff','--cached','--name-only').decode().splitlines();assert all(n in ['PARALLEL_SYNC_SPEED_102.md','README.md','BENCHMARK_HISTORY.md'] or n.startswith('benchmarks/parallel-sync-speed-102/') for n in staged)
for n,h in supported.items():assert sha(REPO/n)==h
git('commit','-m','Preserve complete native and service102 performance rejection and restored evidence')
head=git('rev-parse','HEAD').decode().strip();assert not git('status','--porcelain')
save(H/'commit-102-proof.json',{'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'parent':PARENT,'files_committed':len(staged),'supported_source_unchanged':True,'full_fixed_performance_rejected':True,'private_local_commit_no_remote_publication':True})
print(json.dumps(load(H/'commit-102-proof.json')),flush=True)
