"""Private evidence/report commit; retain the numerical rejection and supported core."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
ROOT=Path('D:/Codex/Kestrel');R=ROOT/'outputs/kestrel-sql';W=ROOT/'work/perf-098';O=R/'benchmarks/async-service-098';PARENT='b4e7cf9f8d2105c96ae07c57540d6a33f4d17018'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def git(*args,binary=False):
 p=subprocess.run(['git','--no-optional-locks','-c',f'safe.directory={R.as_posix()}','-c','gc.auto=0','-c','maintenance.auto=false','-C',str(R),*args],capture_output=True)
 assert p.returncode==0,(args,p.stdout[-2000:],p.stderr[-2000:]);return p.stdout if binary else p.stdout.decode().strip()
guard=sorted((ROOT/'work').glob('guard-precommit-098-*.json'))[-1];g=load(guard);assert not g['active_processes'] and g['reset_phase']=='waiting-for-full-codex-exit'
assert git('rev-parse','HEAD')==PARENT and git('status','--porcelain')=='?? benchmarks/async-service-098/'
p=load(O/'preservation-proof.json');restored=load(O/'restored-audit-proof.json');assert p['complete'] and restored['passed'] and restored['native_launches']==restored['performance_timer_launches']==0
a=load(W/'audit.json');assert a['lost']==0 and a['identity_failed_total']==a['goals_failed']==1 and a['candidate_failed_total']==0 and not a['scoped_candidate_qualified']
for part in p['parts']:assert sha(O/part['name'])==part['sha256']
core={q.relative_to(R).as_posix():sha(q) for folder in ['src','tests','examples'] for q in (R/folder).rglob('*') if q.is_file()}
for n in ['Cargo.toml','Cargo.lock','OVERNIGHT_2026-10-07.md']:core[n]=sha(R/n)
for n,h in core.items():assert hashlib.sha256(git('show',PARENT+':'+n,binary=True)).hexdigest()==h,n
assert set(core)==set(git('ls-tree','-r','--name-only',PARENT,'--','src','tests','examples','Cargo.toml','Cargo.lock','OVERNIGHT_2026-10-07.md').splitlines())
rows=[]
for scope in a['scopes']:
 r=next(r for r in scope['summaries'] if r['profile']=='write');c=r['comparisons']['primary_candidate_over_a']['paired_ratios'];b=r['comparisons']['identity_b_over_a']['paired_ratios']
 rows.append(f"| {scope['scope']} | {c['overall']['median']:.9f} | {c['append']['median']:.9f} | {b['append']['median']:.9f} |")
report=f'''# Normal owned async service 098 — October 9, 2026

**Trial 098 is unqualified. Supported 0.3.16 remains byte-exact; .17 is not ready and has no justified date.** The full cohort shows a numerical signal of 24.4% lower mixed p99 and 11.4% lower append p99, but the second half fails both append A/A calibration and the append improvement goal. There is no speed adoption, full release qualification or all-benchmark claim.

The comparison is normal same-D repeated identical **incremental budget20/every8 A/A versus exact owned async20/every8**, using the 097/096 worker base. It does not compare directly against historical 093 timings or supported full cleanup every32. Both modes use an identical optional consuming shutdown control after the original measurement windows. The original request dispatch/client and the entire original 093 stress harness, including arrivals/drain, remain byte-exact. No traces, fault hooks, dependency, version, ACK/durability, queue, budget, compaction, retry, source or snapshot change enters timed artifacts. The earlier isolated061 analytical fix is not integrated into this worker base.

All144cases were declared before source preparation:24rounds, two independently balanced12-round halves, six permutations twice per half, seed9810, alternating profiles. Each fresh fixture starts with1Mrows,64clients,100-row appends, delay0/retry0, queue256 and expiry2s. Read2000/s8s and25%-write500/s20s yield1,872,000offers. All fixed numerical cases finished, including every stall; there were no extra rounds, favorable-scope selection, comparator swaps, gate relaxation, budget retune or durability reduction. All comparisons use the median of per-round ratios, C/A primary and C/B diagnostic only.

| Scope | Mixed overall p99 C/A | Append p99 C/A | Append p99 identical B/A |
| --- | ---: | ---: | ---: |
{chr(10).join(rows)}

The unchanged goals require overall<=0.95 andappend<=0.90 in **all three scopes**, with calibrated identity/resource/loss/disk controls. The second-half append C/A is **0.9059120262593131**, only9.4088% lower, so it misses10%; it must not be rounded into a pass. Identical baseline B/A is **1.0589543791402463**, outside0.95–1.05. Full and first-half checks pass, but the complete decision remains rejection: **1/45 identity failures,0/51 candidate guard failures,1/6 goal failures**. CPU is diagnostic only; 100ns is representation rather than resolution, and many read samples charge zero ticks. No CPU win is claimed.

| Fresh checks | Result |
| --- | --- |
| Repaired source debug/release suites / strict lint modes | 716 tests /4 pass |
| Fixed normal service cases /offers /successes | 144 /1,872,000 /1,872,000 |
| Lost, dropped, expired, executed-error or ambiguous ACK outcomes | 0 |
| Acknowledged100-row batches /full current CRC references | 179,280 /3,886,272,000 bytes independently pass |
| Full NumPy ACK-row multisets /reference windows | Every timed current store /2,880 windows |
| Timed initial+cold native processes | 288 actual graceful joins and exit0 |
| Predeclared sustained backlog | Four12000-group schedules /48,000ACKs; all named digests/original generations pass |
| Sampled backlog peaks | Anonymous83files/480697bytes; named113files/4586387bytes, within192files/16MiB |
| Retained new shutdown /worker unit stores | 24 /152 across two actually executed source builds; independent CRC1920+149120bytes |
| Fresh compatibility controls | 56 Native commands /320namedACKs /four initial+cold graceful exits |
| Complete excluded service smokes /synthetic invalid fixtures | 2 /29 invalid records rejected with zero Native launches in the validators |

Resource sampling occurs after drain and before getters/reopen. The consuming control retains only counters/options/boolean, drops uniquely owned Live through its existing Inner writer/background joins, then reads final stopped/queue/maintenance counters. All client threads/snapshots are closed before shutdown. Native exit0, stoppedtrue, queue0, maintenance0 and cold lock acquisition are required. A5s health timeout fails the case; only an exact Popen-owned child may be killed after recording failure, and a kill never passes shutdown. Final physical disk inventory follows actual join+exit and precedes cold reading. Native shutdown milliseconds are separate descriptions and never alter arrival/drain metrics or constitute a calibrated speed result.

The first helper source passed716 fresh suites but failed strict default lint on a redundant field name. All its source, helpers, policy, logs, run order and132 original executable copies remain; its target cache is untouched. The repair only uses field shorthand/test-hook alias and completes untimed probe controls, including explicit shutdown deadlines and recorded files concurrently deleted during samples. A separate fresh target reran716 qualifying tests and four lints. Prior716 executions are retained as the failed-lint version, not counted as qualifying the repaired source. The consuming control's tests reject multiple Live ownership, retain snapshot leases until explicit drop, and observe a real worker error callback during existing Inner Drop/join using a finite custom unit writer. This is not a new physical-error or normal concurrency recovery matrix. Earlier096/097/094fault/corruption schedules are explicitly reused where stated, never recounted as freshly executed here.

{len(p['parts'])} bounded archives preserve **{p['files']:,} files /{p['directories']:,} directories /{p['logical_bytes']:,} logical bytes**. All source/binaries/raw samples/ACKs/generations/stdio/control/resource/lifecycle/stores/locks/failure bytes and empty directories remainD. Only inventoried regenerable target-build/target-build-v2/Python caches are omitted, with originals retained. The previously qualified64MiBchunk/80MiBlogicalpart algorithm is reused. Every memberCRC/order/offset/size and full original/restored SHA/file+directory set passes. Complete restored replay exactly recomputes all offer conservation, raw quantiles, fixed gates, resources, full current CRC/NumPy, lifecycle, backlog/unit/oracle/smoke stores and failed-version hashes with **zero Native/timer launches**, then every file/set is checked again. The original auditor's single attempted JSON output is captured in memory to preserve every existing file. Closed packager stdout is a separately hashed post-exit supplement.

Evidence: [policy](benchmarks/async-service-098/policy.json), [decision](benchmarks/async-service-098/decision-summary.json), [preservation](benchmarks/async-service-098/preservation-proof.json), [restored replay](benchmarks/async-service-098/restored-audit-proof.json), [reproduction](benchmarks/async-service-098/REPRODUCE.md). Full large raw/audit proofs remain in original/restored/chunk evidence. Work: D:\\Codex\\Kestrel\\work\\perf-098; restore: D:\\Codex\\Kestrel\\work\\restored-async-service-098.

The next step needs a new experiment number and hypothesis grounded in the remaining append path and control variability. Do not repeat098, select the passing first half, relax thresholds or assume file deletion explains append tails. Enumeration/publication sync and retirement/cache-handle drops remain distinct possible costs; the latter were outside092's deletion phase and are not attributed by098. Preserve every failure, measure the next bottleneck and qualify controls before considering adoption. Integration and broad six-profile/native analytical/scan/minute/overload/competitor/source/retry/crash/corruption/old-format/ownership/pins/resource/restoration gates still precede.17. This computer and private repository only; no C cleanup repetition, reset execution, app force-close, abandoned-chat resume or old task/automation reactivation occurred.
'''
for compact,spaced in [('budget20/every8','budget 20/every 8'),('incremental20/every8','incremental 20/every 8'),('async20/every8','async 20/every 8'),('every32','every 32'),('isolated061','isolated 061'),('All144cases','All 144 cases'),('24rounds','24 rounds'),('balanced12-round','balanced 12-round'),('seed9810','seed 9810'),('with1Mrows,64clients,100-row','with 1M rows, 64 clients, 100-row'),('queue256','queue 256'),('expiry2s','expiry 2 s'),('Read2000/s8s','Read 2000/s for 8 s'),('25%-write500/s20s','25%-write 500/s for 20 s'),('1,872,000offers','1,872,000 offers'),('overall<=0.95 andappend<=0.90','overall <=0.95 and append <=0.90'),('only9.4088%','only 9.4088%'),('misses10%','misses 10%'),('1/45 identity failures,0/51 candidate guard failures,1/6 goal failures','1/45 identity failures, 0/51 candidate guard failures, 1/6 goal failures'),('100ns','100 ns'),('tests /4','tests /4'),('100-row','100-row'),('Four12000-group','Four 12000-group'),('48,000ACKs','48,000 ACKs'),('named113files','named 113 files'),('Anonymous83files','Anonymous 83 files'),('within192files/16MiB','within 192 files/16 MiB'),('CRC1920+149120bytes','CRC 1920+149120 bytes'),('56 Native commands /320namedACKs /four','56 Native commands /320 named ACKs /four'),('A5s','A 5 s'),('stoppedtrue, queue0, maintenance0','stopped true, queue 0, maintenance 0'),('passed716','passed 716'),('and132','and 132'),('reran716','reran 716'),('Prior716','Prior 716'),('Earlier096/097/094fault','Earlier 096/097/094 fault'),('64MiBchunk/80MiBlogicalpart','64 MiB chunk/80 MiB logical part')]:report=report.replace(compact,spaced)
for compact,spaced in [('read2000','read 2000'),('2000/s8s','2000/s for 8 s'),('500/s20s','500/s for 20 s'),('500/s for 20 s yield1','500/s for 20 s yield 1'),('delay0/retry0','delay 0/retry 0'),('four12000','four 12000'),('all144','all 144'),('179,280 /3,886','179,280 / 3,886'),('Everytimedcurrentstore','Every timed current store'),('2,880 windows','2,880 windows'),('anonymous83','anonymous 83'),('113 files/4586387bytes','113 files / 4586387 bytes'),('83 files/480697bytes','83 files / 480697 bytes'),('83 files/480697bytes','83 files / 480697 bytes'),('320named','320 named'),('132original','132 original'),('originals retained. The previously','originals retained. The previously'),('CRC1920','CRC 1920'),('149120bytes','149120 bytes'),('remainD.','remain on D:.'),('before.17','before .17'),('repeat098','repeat 098'),('outside092','outside 092'),('attributed by098','attributed by 098')]:report=report.replace(compact,spaced)
q=R/'ASYNC_SERVICE_098.md';assert not q.exists();q.write_text(report,encoding='utf-8',newline='\n')
nav='\n\n## Normal owned async service 098\n\n[ASYNC_SERVICE_098.md](ASYNC_SERVICE_098.md): all 1,872,000 offers and 179,280 ACKs pass independent data and graceful completion checks, but second-half append calibration and improvement miss the fixed gates. The entire 144-case result and all failures were restored exactly; unqualified, no adoption, supported 0.3.16 unchanged and .17 pending.\n';before={}
for n in ['README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md']:
 q=R/n;b=q.read_bytes();before[n]=hashlib.sha256(b).hexdigest();q.write_bytes(b+nav.encode());assert q.read_bytes().startswith(b)
supplement=O/'closed-continuation';supplement.mkdir()
for path in [ROOT/'work/preserve-098.log',Path(__file__),guard]:shutil.copy2(path,supplement/path.name)
save(supplement/'proof.json',{'utc':datetime.now(timezone.utc).isoformat(),'files':{q.name:sha(q) for q in supplement.iterdir() if q.is_file()},'packager_stdout_copied_after_actual_exit':True,'supported_core':core,'parent':PARENT,'navigation_prior_sha256':before,'private_only':True})
paths=['ASYNC_SERVICE_098.md','README.md','BENCHMARK_HISTORY.md','RELEASE_TARGET_0_3_17.md','benchmarks/async-service-098'];git('add','--',*paths);git('-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check','--',*paths)
git('commit','-m','Preserve normal async service098 numerical rejection and full graceful evidence');head=git('rev-parse','HEAD');assert git('merge-base','--is-ancestor',PARENT,head)=='' and git('status','--porcelain')=='' and all(sha(R/n)==h for n,h in core.items())
save(ROOT/'work/commit-098-proof.json',{'complete':True,'clean':True,'head':head,'parent':PARENT,'supported_core':core,'navigation_prior_sha256':before,'private_only':True,'remote_not_modified':True,'trial_unqualified_not_adopted':True});print(json.dumps({'private_commit':head,'clean':True,'supported_core_byte_exact':True,'trial098_unqualified_no_adoption':True}))
