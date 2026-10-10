"""Commit completely restored rejected trial117 and keep supported016 byte-exact."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,subprocess
R=Path('D:/Codex/Kestrel');WORK=R/'work';W=WORK/'perf-117';REPO=R/'outputs/kestrel-sql';OUT=REPO/'benchmarks/adaptive-speed-117'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rawgit(*args):
 return subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(REPO),*args],capture_output=True)
def git(*args):
 p=rawgit(*args);assert p.returncode==0,(args,p.stdout,p.stderr);return p.stdout.decode('utf-8')
guard=sorted(WORK.glob('guard-final-117-*.json'))[-1];assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
parent=load(WORK/'commit-116-proof.json')['head'];assert git('rev-parse','HEAD').strip()==parent and not git('diff','--name-only') and not git('diff','--cached','--name-only')
complete=load(OUT/'complete-audit-proof.json');preserved=load(OUT/'preservation-proof.json');restored=load(OUT/'restored-audit-proof.json');n=complete['native']
assert preserved['complete'] and restored['replay_equals_original_complete_audit'] and complete==load(W/'complete-audit-proof.json')
assert complete['correctness_passed'] and not complete['performance_qualified'] and not complete['release017_qualified']
assert (n['cases'],n['identity_failed'],n['candidate_guards_failed'],n['goals_failed'])==(324,15,6,4)
assert complete['fresh_tests']==820 and complete['fresh_recovery_commands']==359 and len(complete['all_scope_controlled_goal_results'])==8 and len(complete['service']['all_specs'])==252
assert json.loads((WORK/'preserve-117.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
protected={p:sha(REPO/p) for p in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
assert all(sha(REPO/p)==h for p,h in load(WORK/'perf-105/policy.json')['baseline_source_sha256'].items())
closed=OUT/'closed-continuation';assert not closed.exists();closed.mkdir();logs={}
for name in ['build-117-v2.log','build-117-v3.log','preflight-117-v3.log','preperformance-117-v3.log','prefix-audit-117-v4.log','native-117-v3.log','native-audit-117-v3.log','prepare-closure-117.log','profile-native-117.log','complete-audit-117.log','complete-audit-117-v2.log','prepare-preserver-117.log','preserve-117.log']:
 raw=(WORK/name).read_bytes();p=closed/(name+'.gz');p.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(p.read_bytes())==raw
 logs[name]={'raw_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':sha(p),'byte_exact':True}
(closed/'raw-log-proof.json').write_text(json.dumps(logs,indent=2)+'\n',encoding='utf-8',newline='\n')
shutil.copy2(Path(__file__),closed/Path(__file__).name);shutil.copy2(guard,closed/guard.name)
for name in ['README.md','BENCHMARK_HISTORY.md']:shutil.copy2(REPO/name,closed/(name+'.before-117'))
report='''# Byte-buffered receipt hashing trial 117

The combined experimental candidate improves identified-replay p99 against
supported 0.3.16, but fails full release qualification. **0.3.17 remains
unqualified and unreleased; supported main remains byte-exact 0.3.16.**
All 324 cases are correct. Performance fails 15 of 153 A/A controls,
six of 171 guards and four of 42 goals. All 252 service cases are unstarted.

Receipt hashing previously called SHA-256 update separately for the header
fields and every integer. A private fixed 64-byte buffer now feeds the same
width/row header and column-major submitted signed little-endian values in
larger chunks. Full and partial buffers, including cross-column boundaries,
preserve the exact message and digest. This changes neither validation nor
receipt identity. No unsafe, digest cache, new backend/dependency, wire/format,
budget, ACK, read-view, lock, flush, collection or public API change occurs.
The original scalar feature-disabled path remains byte-exact. Archive/Cargo
inverses and every other serial116 Reader/query/live/source/group/test hash pass.
The locked [sha2 0.10.9 API](https://docs.rs/sha2/0.10.9/sha2/) supports hashing
the canonical message with incremental or one-shot updates.

This measures collector107/filter109/replay110/scan112/group-range116/digest117
together against fresh same-D: supported016 A/A baselines. It does not isolate
the new digest change versus116. Rejected concurrent flushing114 stays separate.

All 820 fresh tests/eight configurations, five strict lints, normal/fault
binaries and 359 fresh recovery commands pass. Four new units compare flat
message oracles and independent Python hashlib goldens across signed limits,
empty/short/full/partial/cross-column buffers, shape/order, large/wide inputs
and repeated calls. Two integrations verify durable receipt bytes, mismatch
rejection, retry/reopen, Live prepared/indexed/unindexed and SourceArchive
recovery identity. Recovery covers 28 injected error/owned process exits,
ten corruptions, two old formats, exact byte fixtures, concurrent ACKs and
300 cold SQL checks. These do not establish physical power-loss guarantees.

The first build exited1 on a new test assertion comparing u64 to usize after
324 baseline/fixed executions. Its original sources/proofs/logs/targets remain.
A separate corrected input changes only that test conversion; all 820 required
tests were then run fresh. One pure closure invocation from the Root helper
directory exited1 on the required import-origin guard before auditing data.
The unchanged auditor launched from the experiment directory passes; both
logs and actual exits are retained. No timed or numerical rerun occurred.

Four Native/two service excluded smokes, 48 order checks, six outcome negatives
and two invalid orders pass. All324 fixed cases ran once, twelve rounds/all
six balanced orders/full and both halves. All479,232 ACKs and2,921,356,800 CRC
bytes pass independent rows/indexes/receipt generations/digests/current metadata,
cold SQLite SQL and raw quantiles. Every stall, maximum and failed scope remains.

## Controlled goals

These eight metrics meet targets and corresponding controls in full and both
halves. Percentages use median within-round paired ratios and need not equal
the quotient of the displayed medians.

| Workload | Metric | Unit | 016 baseline median | Candidate median | Full paired reduction | Full A/A | Full/both-half goal and controls |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
'''
def unit(row):
 if row['metric']=='disk':return 'bytes',1
 if '/' in row['metric'] or row['workload']=='identified-replay':return 'us',1 if '/' in row['metric'] else 1000
 return 'ms',1e-6
for row in complete['all_scope_controlled_goal_results']:
 full=next(s for s in row['scopes'] if s['scope']=='full');u,scale=unit(full)
 report+=f"| {row['workload']} | {row['metric']} | {u} | {full['before_median']*scale:.6f} | {full['after_median']*scale:.6f} | {(1-full['CA'])*100:.2f}% | {full['AA']:.8f} | pass |\n"
report+='''
## Remaining failures

Every failed guard and goal follows. A passing control with a failing guard
is a calibrated regression. A failed control makes that comparison inconclusive.
Goals require both their numerical target and corresponding controls in every
declared scope. No gate has changed; service is unstarted because Native fails.
'''
for row in n['guards']:
 if row['passed']:continue
 control=next((c for c in n['controls'] if all(c[k]==row[k] for k in ['scope','workload','metric'])),None)
 state='calibrated regression' if control and control['passed'] else 'inconclusive: control fails'
 report+=f"\n- {row['scope']} {row['workload']} {row['metric']}: C/A {row['CA']:.8f} ({(row['CA']-1)*100:+.2f}%); A/A {row['AA']:.8f}; {state}.\n"
for row in n['goals']:
 if row['passed']:continue
 control=next(c for c in n['controls'] if all(c[k]==row[k] for k in ['scope','workload','metric']))
 state='control passes' if control['passed'] else 'inconclusive: control fails'
 report+=f"\n- Goal miss: {row['scope']} {row['workload']} {row['metric']}, C/A {row['CA']:.8f} versus {row['limit']}; A/A {row['AA']:.8f}; {state}.\n"
report+='''

## Every before/after comparison

All171 full/half comparisons follow. A/A requires0.95-1.05; candidate guards
require C/A at most1.05. Goals keep metric-specific stricter limits. Disk has
no A/A control. Every failed guard remains recorded even when controls fail.

| Scope | Workload | Metric | Unit | Baseline median | Candidate median | A/A | Control | C/A | Guard | Goal limit | Goal |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | ---: | --- |
'''
for row in n['summaries']:
 same=lambda v:all(v[k]==row[k] for k in ['scope','workload','metric'])
 control=next((v for v in n['controls'] if same(v)),None);guard_row=next(v for v in n['guards'] if same(v));goal=next((v for v in n['goals'] if same(v)),None);u,scale=unit(row)
 report+=f"| {row['scope']} | {row['workload']} | {row['metric']} | {u} | {row['before_median']*scale:.6f} | {row['after_median']*scale:.6f} | {row['AA']:.8f} | {'n/a' if control is None else ('pass' if control['passed'] else 'FAIL')} | {row['CA']:.8f} | {'pass' if guard_row['passed'] else 'FAIL'} | {'n/a' if goal is None else str(goal['limit'])} | {'n/a' if goal is None else ('pass' if goal['passed'] else 'FAIL')} |\n"
report+=f'''
## Exact preservation

{preserved['files']:,} files, {preserved['directories']:,} directories,
{len(preserved['parts'])} bounded ZIP parts and {preserved['logical_bytes']:,}
logical bytes pass every member CRC/order/offset/size, exact original/restored
file hashes and complete file/directory sets before and after the full pure
audit. Every fresh prerequisite, all raw correctness/quantiles/profile and
full/half controls/guards/42 goals/252 unstarted service specifications replay
exactly without Native, timers or existing-file writes. Original files remain;
only inventoried regenerable target/Python caches are excluded. Closed raw
logs are byte-exact gzip supplements. The failed test-compilation attempt,
its test-only corrected copy and failed Root-origin pure audit invocation are
retained with actual exits. The successful fresh820 executions are separate
from the324 executions before the first compile failure. No numerical retry.

No new supported upgrade, reliable release ETA, fresh competitor ranking,
universal win, Native CPU/RSS or physical power-loss guarantee is claimed.
Recent raw GitHub backup remains unverified; no recent raw deletion is eligible.
See [reproduction](benchmarks/adaptive-speed-117/REPRODUCE.md) and the
[complete audit](benchmarks/adaptive-speed-117/complete-audit-proof.json).
'''
p=REPO/'ADAPTIVE_ENGINE_117.md';assert not p.exists();p.write_text(report,encoding='utf-8',newline='\n')
assert len([s for s in report.splitlines() if s.startswith('| full |') or s.startswith('| half_')])==171
for name in ['README.md','BENCHMARK_HISTORY.md']:
 p=REPO/name;text=p.read_text(encoding='utf-8');assert 'ADAPTIVE_ENGINE_117.md' not in text
 p.write_text(text.rstrip()+'\n\n- [Byte-buffered receipt hashing trial 117](ADAPTIVE_ENGINE_117.md): 820 fresh tests, 359 recovery commands and 324 correct cases. Replay p99 improves14.52% versus016 with full/half controls, but15 controls/six guards/four goals fail. All252 service cases unstarted; supported016 unchanged. Exact restored evidence and failed prerequisite attempts retained.\n',encoding='utf-8',newline='\n')
assert all(sha(REPO/p)==h for p,h in protected.items())
git('add','--','README.md','BENCHMARK_HISTORY.md','ADAPTIVE_ENGINE_117.md','benchmarks/adaptive-speed-117')
assert all(s in ['README.md','BENCHMARK_HISTORY.md','ADAPTIVE_ENGINE_117.md'] or s.startswith('benchmarks/adaptive-speed-117/') for s in git('diff','--cached','--name-only').splitlines())
check=rawgit('diff','--cached','--check');exception='benchmarks/adaptive-speed-117/outcomes_098.py'
assert check.returncode==2 and check.stdout==(exception+':41: new blank line at EOF.\n').encode() and not check.stderr
blob=rawgit('show',':'+exception);assert blob.returncode==0 and blob.stdout==(W/'outcomes_098.py').read_bytes()==(REPO/exception).read_bytes()
git('diff','--cached','--check','--','.',':(exclude)'+exception)
proof={'exact_original_raw_EOF_whitespace_narrow_exception':exception,'raw_sha256':sha(W/'outcomes_098.py'),'strict_original_check_actual_exit':2,'all_other_staged_paths_strict_whitespace_actual_exit':0,'original_raw_bytes_and_frozen_inputs_unchanged':True,'no_source_or_gate_change':True}
(closed/'raw-EOF-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');git('add','--',str(closed/'raw-EOF-proof.json'))
git('diff','--cached','--check','--','.',':(exclude)'+exception)
git('commit','-m','Preserve receipt hashing117 results and exact restored failures')
head=git('rev-parse','HEAD').strip();assert git('rev-parse','HEAD^').strip()==parent and all(sha(REPO/p)==h for p,h in protected.items()) and not git('status','--porcelain=v1','--untracked-files=all')
proof={'utc':datetime.now(timezone.utc).isoformat(),'head':head,'parent':parent,'repository_clean':True,'supported_source_byte_exact016':True,'trial117_fully_preserved_restored_and_committed':True,'exact_raw_EOF_narrow_exception_only':True,'no_private_upload_or_deletion_claim':True}
(WORK/'commit-117-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof))
