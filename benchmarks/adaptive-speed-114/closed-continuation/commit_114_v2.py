"""Commit fully restored rejected114 evidence; keep supported016 byte-exact."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,subprocess
R=Path('D:/Codex/Kestrel');WORK=R/'work';W=WORK/'perf-114';REPO=R/'outputs/kestrel-sql';OUT=REPO/'benchmarks/adaptive-speed-114'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(*args):
 p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(REPO),*args],capture_output=True,text=True)
 assert p.returncode==0,(args,p.stdout,p.stderr);return p.stdout
guard=sorted(WORK.glob('guard-final-114-*.json'))[-1];assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
parent=load(WORK/'commit-113-proof.json')['head'];assert git('rev-parse','HEAD').strip()==parent
assert not git('diff','--name-only') and not git('diff','--cached','--name-only')
preserved=load(OUT/'preservation-proof.json');restored=load(OUT/'restored-audit-proof.json');complete=load(OUT/'complete-audit-proof.json');n=complete['native']
assert preserved['complete'] and restored['replay_equals_original_complete_audit'] and complete==load(W/'complete-audit-proof.json')
assert complete['correctness_passed'] and not complete['release017_qualified'] and not complete['performance_qualified']
assert (n['cases'],n['identity_failed'],n['candidate_guards_failed'],n['goals_failed'])==(324,12,5,9)
assert complete['service']['status']=='UNSTARTED_UNTESTED' and complete['service']['cases']==252
assert json.loads((WORK/'preserve-114.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
protected={name:sha(REPO/name) for name in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
assert all(sha(REPO/name)==h for name,h in load(WORK/'perf-105/policy.json')['baseline_source_sha256'].items())
closed=OUT/'closed-continuation';assert closed.is_dir();logs={}
names=['declare-114.log','prepare-114.log','build-114-v2.log','prepare-harness-114.log','prepare-additional-audits-114.log','preflight-114-v2.log','preperformance-114-v2.log','prefix-audit-114.log','native-114-v2.log','native-audit-114-v2.log','prepare-closure-114.log','profile-native-114.log','complete-audit-114.log','prepare-preserver-114.log','preserve-114.log','update-next-building114.log','update-next-ready114.log']
for name in names:
 raw=(WORK/name).read_bytes();p=closed/(name+'.gz');assert p.exists() and gzip.decompress(p.read_bytes())==raw
 logs[name]={'raw_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':sha(p),'byte_exact':True}
(closed/'raw-log-proof.json').write_text(json.dumps(logs,indent=2)+'\n',encoding='utf-8',newline='\n');shutil.copy2(Path(__file__),closed/Path(__file__).name);shutil.copy2(guard,closed/guard.name)
for name in ['README.md','BENCHMARK_HISTORY.md']:assert (REPO/name).read_bytes()==(closed/(name+'.before-114')).read_bytes()
report='''# Adaptive publication trial 114

**Release qualification failed.** Supported main remains 0.3.16; isolated
0.3.17 is unreleased. All 324 native cases are correct, but 12 of 153 A/A
controls, five of 171 regression guards and nine of 42 goals fail. Every
252 service case is UNSTARTED/UNTESTED. No selected scope, extra round,
numerical retry or gate change occurred. Every raw stall and failure remains.

The measured publication stages in diagnostic 113 justified testing concurrent
durable flushes. Trial 114 retains exact 112 collector/filter/replay/scan and
the identical common native driver. Only the private publication feature,
archive dispatch, scoped flush helper and two integration tests change.
Both BufWriters flush before the pair; both existing sync_all successes and
the actual worker join precede catalog rename, read-view update and ACK.
Spawn errors, either flush error or either panic prevent success. At most
one borrowed worker exists per pair; no detached worker, unsafe code,
durability weakening, persistent thread or file-format change is introduced.
Archive/Cargo exact inverses and every other source hash independently pass.

796 fresh test executions across eight configurations, five strict lints,
all normal/fault binaries and 359 fresh recovery commands pass. Faults,
corruptions, CAT2/CAT3, byte fixtures, concurrent ACKs, original receipt
generations and cold SQLite answers pass. Four Native/two service excluded
smokes, 48 order checks, two invalid order fixtures and **six** invalid
conserved-outcome cases pass. Earlier prose saying 29 negative cases was
incorrect; the original raw dictionaries contained six. Historical reports
and all failed/unexecuted drafts remain preserved. Actual build argv confirms
benchmark-shutdown plus adaptive-engine for the candidate, and fault-injection
for the fault build; the policy's inherited features field is contextual.

The build, recovery, smoke and Native controllers and independent audits
actually exited zero. This does not reclassify the old 112 preflight API
return that was unobserved. Independent raw auditing passes all 479,232
acknowledgements and 2,921,356,800 CRC bytes, full row multisets, indexes,
named receipt digests/original generations, current metadata, cold SQL,
quantiles, direct Archive byte equivalence and balanced full/half orders.

## Controlled goals and remaining failures

Nine goal metrics pass targets and A/A in full and both halves. Displayed
medians use the indicated units; percentages use full within-round paired
ratios, which need not equal quotients of displayed medians. These compare
the complete experimental candidate with supported 0.3.16 and **do not
isolate a 114-versus-112 flush gain**. Earlier optimizations are included.

| Workload | Metric | Unit | Baseline median | Candidate median | Paired reduction |
| --- | --- | --- | ---: | ---: | ---: |
'''
for goal in complete['all_scope_controlled_goal_results']:
 row=next(v for v in goal['scopes'] if v['scope']=='full');query=row['metric'].endswith('_us');unit,scale=('us',1) if query else ('ms',1e-6)
 report+=f"| {row['workload']} | {row['metric']} | {unit} | {row['before_median']*scale:.6f} | {row['after_median']*scale:.6f} | {(1-row['CA'])*100:.2f}% |\n"
report+='''
Three failed guards have passing A/A in half 2: pressure-anonymous p95 is
10.96% slower and p99 11.53% slower; pressure-named p99 is 8.61% slower.
The other two guard failures have failing A/A. Ordered/late grouped p95
still miss the 10% target with passing full controls; late grouped median
and original-ID replay goals also miss required halves. Unstable replay
baseline controls prevent an all-scope replay-speed claim. Causes and any
benefit of selectively choosing a publication strategy are not established.

## Every before/after and mandatory gate

Latency/completion units are milliseconds; queries use microseconds; disk
uses bytes. A/A requires 0.95–1.05. Candidate guards require at most 1.05.
Every goal's own frozen limit is shown. All full and both-half results follow.

| Scope | Workload | Metric | Unit | Baseline median | Candidate median | A/A | Control | C/A | Guard | Goal limit/result |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- |
'''
for row in n['summaries']:
 keys=['scope','workload','metric'];same=lambda v:all(v[k]==row[k] for k in keys)
 control=next((v for v in n['controls'] if same(v)),None);g=next(v for v in n['guards'] if same(v));goal=next((v for v in n['goals'] if same(v)),None)
 unit,scale=('bytes',1) if row['metric']=='disk' else (('us',1) if row['metric'].endswith('_us') else ('ms',1e-6))
 outcome='n/a' if goal is None else f"{goal['limit']:g} / {'pass' if goal['passed'] else 'FAIL'}"
 report+=f"| {row['scope']} | {row['workload']} | {row['metric']} | {unit} | {row['before_median']*scale:.6f} | {row['after_median']*scale:.6f} | {row['AA']:.8f} | {'n/a' if control is None else ('pass' if control['passed'] else 'FAIL')} | {row['CA']:.8f} | {'pass' if g['passed'] else 'FAIL'} | {outcome} |\n"
report+=f'''
## Exact preservation and limits

{preserved['files']:,} files, {preserved['directories']:,} directories,
{len(preserved['parts'])} bounded ZIP parts and {preserved['logical_bytes']:,}
logical bytes pass member CRC/order/offset/size and exact original/restored
file hashes and directory sets before and after complete pure replay. Every
source/build/recovery/smoke and native gate replays identically, with no
Native, timer or existing-file write. All originals remain. Only inventoried
regenerable build/Python caches are excluded. Closed logs are byte-exact
gzip supplements. No recent complete private remote backup or deletion is claimed.

Automatic approval review rejected an attempted handoff update while the
build was live. The command did not execute. After the actual build exit and
a fresh idle guard, a corrected checkpoint executed successfully. Its
unexecuted rejected draft and resolution record are retained. No approval
barrier was bypassed, and the reset and all old task settings remain untouched.

There is no supported upgrade, new competitor ranking, universal benchmark
win, reliable release ETA, native CPU/RSS, physical I/O or power-loss claim.
The next justified measurement must isolate 112 serial versus 114 concurrent
publication with new predeclared balanced controls, before choosing a workload
dependent publication path. Neither old failure is reclassified.
See [reproduction](benchmarks/adaptive-speed-114/REPRODUCE.md) and
[complete audit](benchmarks/adaptive-speed-114/complete-audit-proof.json).
'''
path=REPO/'ADAPTIVE_ENGINE_114.md';assert path.read_bytes()==report.encode('utf-8')
for name in ['README.md','BENCHMARK_HISTORY.md']:
 p=REPO/name;text=p.read_text(encoding='utf-8');assert 'ADAPTIVE_ENGINE_114.md' not in text
 p.write_text(text.rstrip()+'\n\n- [Adaptive publication trial 114](ADAPTIVE_ENGINE_114.md): 796 fresh tests, 359 recovery commands and 324 correct native cases; nine controlled goal metrics, but 12 controls/five guards/nine goals fail. All 252 service cases unstarted; supported 0.3.16 unchanged. Exact restored raw evidence retained.\n',encoding='utf-8',newline='\n')
assert all(sha(REPO/name)==h for name,h in protected.items())
git('add','--','README.md','BENCHMARK_HISTORY.md','ADAPTIVE_ENGINE_114.md','benchmarks/adaptive-speed-114')
staged=git('diff','--cached','--name-only').splitlines();assert all(x in ['README.md','BENCHMARK_HISTORY.md','ADAPTIVE_ENGINE_114.md'] or x.startswith('benchmarks/adaptive-speed-114/') for x in staged)
git('diff','--cached','--check');git('commit','-m','Preserve rejected adaptive publication114 and exact restored evidence')
head=git('rev-parse','HEAD').strip();assert git('rev-parse','HEAD^').strip()==parent and all(sha(REPO/name)==h for name,h in protected.items()) and not git('status','--porcelain=v1','--untracked-files=all')
proof={'utc':datetime.now(timezone.utc).isoformat(),'head':head,'parent':parent,'repository_clean':True,'supported_source_byte_exact016':True,'trial114_fully_preserved_restored_and_committed':True,'no_private_upload_or_deletion_claim':True}
(WORK/'commit-114-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof))
