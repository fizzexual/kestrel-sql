"""Commit completely restored rejected trial116 and keep supported016 byte-exact."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,subprocess
R=Path('D:/Codex/Kestrel');WORK=R/'work';W=WORK/'perf-116';REPO=R/'outputs/kestrel-sql';OUT=REPO/'benchmarks/adaptive-speed-116'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rawgit(*args):
 return subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(REPO),*args],capture_output=True)
def git(*args):
 p=rawgit(*args);assert p.returncode==0,(args,p.stdout,p.stderr);return p.stdout.decode('utf-8')
guard=sorted(WORK.glob('guard-final-116-*.json'))[-1];assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
parent=load(WORK/'commit-115-proof.json')['head'];assert git('rev-parse','HEAD').strip()==parent and not git('diff','--name-only') and not git('diff','--cached','--name-only')
complete=load(OUT/'complete-audit-proof.json');preserved=load(OUT/'preservation-proof.json');restored=load(OUT/'restored-audit-proof.json');n=complete['native']
assert preserved['complete'] and restored['replay_equals_original_complete_audit'] and complete==load(W/'complete-audit-proof.json')
assert complete['correctness_passed'] and not complete['performance_qualified'] and not complete['release017_qualified']
assert (n['cases'],n['identity_failed'],n['candidate_guards_failed'],n['goals_failed'])==(324,21,5,3)
assert complete['fresh_tests']==796 and complete['fresh_recovery_commands']==359 and len(complete['all_scope_controlled_goal_results'])==7 and len(complete['service']['all_specs'])==252
assert json.loads((WORK/'preserve-116.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
protected={p:sha(REPO/p) for p in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
assert all(sha(REPO/p)==h for p,h in load(WORK/'perf-105/policy.json')['baseline_source_sha256'].items())
closed=OUT/'closed-continuation';assert not closed.exists();closed.mkdir();logs={}
for name in ['build-116-v2.log','preflight-116-v2.log','preperformance-116-v2.log','prefix-audit-116.log','native-116-v2.log','native-audit-116-v2.log','prepare-closure-116.log','profile-native-116.log','complete-audit-116.log','prepare-preserver-116.log','preserve-116.log']:
 raw=(WORK/name).read_bytes();p=closed/(name+'.gz');p.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(p.read_bytes())==raw
 logs[name]={'raw_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':sha(p),'byte_exact':True}
(closed/'raw-log-proof.json').write_text(json.dumps(logs,indent=2)+'\n',encoding='utf-8',newline='\n')
shutil.copy2(Path(__file__),closed/Path(__file__).name);shutil.copy2(guard,closed/guard.name)
for name in ['README.md','BENCHMARK_HISTORY.md']:shutil.copy2(REPO/name,closed/(name+'.before-116'))
report='''# Adaptive grouped-range trial 116

The isolated candidate improves grouped-query medians against supported
0.3.16, but fails full release qualification. **0.3.17 remains unqualified
and unreleased; supported main remains byte-exact 0.3.16.** All 324 cases
are correct. Performance fails 21 of 153 A/A controls, five of 171 guards
and three of 42 goals. All 252 service cases are unstarted and untested.

The new query path consumes contiguous decoded ranges when dense groups and
one shared SUM/AVG accumulator exist and sorted bounds enforce every predicate,
or there are no predicates. Other shapes retain the existing kernel. It avoids
the selected-row vector and indirect row loads. Existing dense/sparse groups
and shared SUM/AVG are already implemented and are not claimed as new.
Same memory/domain caps, checked equal-length slices, CRC validation before
reduction, i128 totals, counts, output order, limits and errors are preserved.
The original Reader, collector, serial flushing, formats and receipts remain.
Exact Archive/Cargo byte inverses to serial112 and all other hashes pass.

This is the combined experimental candidate (collector107/filter109/replay110/
borrowed scan112/group-range116) versus fresh same-D: supported016 baselines.
It does not isolate the 116-versus112 effect. Always-concurrent flushing from
rejected114 is separate. No old C: result is used as a direct baseline.

All 796 fresh test executions across eight configurations, five strict lints,
normal/fault binaries and 359 fresh recovery commands pass. Four private units
and two integration tests cover signed limits, wide sums, shared projections,
partial/empty/repeated ranges, multiple segments, unsupported filters/shapes,
sparse domains and cold CRC errors. Recovery includes 28 fault boundaries,
ten corruptions, two historical formats, byte-equivalence, concurrent ACKs and
300 cold SQL checks. Actual current controller API exits are observed zero.
The historical112 unobserved recovery API return remains recorded honestly.

Four Native/two service excluded smokes, 48 order checks, six conserved-outcome
negatives and two invalid orders pass. All 324 fixed D: cases ran once with
twelve rounds and all six A/A/C orders balanced in full and both halves.
All 479,232 ACKs and 2,921,356,800 CRC bytes independently pass complete rows,
indexes, receipt generations/digests, current metadata, cold SQLite SQL and
raw quantiles. All stalls, maxima, failed scopes and raw streams remain.
No selected round, extra timing, numerical retry or changed gate occurred.

## Controlled gains and remaining failures

These seven goal metrics meet targets with passing corresponding A/A controls
in full and both halves. Percentages use full within-round paired ratios,
which need not equal the quotient of the displayed medians.

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
Grouped p95 is not a controlled win across all required scopes: ordered full
and half1 controls fail; late half1 and half2 controls fail. Numerical target
passes do not override those failures. Calibrated guard regressions include
sparse-anonymous half1 p99 +5.39%, sparse-named half1 p95 +6.37% and
pressure-anonymous half2 p99 +7.61%. Full pressure p99 and named pressure
half1 p95 also fail guards with failing controls and remain inconclusive.
The three calibrated target misses are small-named half1 p99 and identified
replay half1 p95/p99. All controls, guards and goals remain mandatory.

Safe checked range access follows the primary [Rust slice documentation](https://doc.rust-lang.org/std/primitive.slice.html#method.get).
The [zip documentation](https://doc.rust-lang.org/std/iter/trait.Iterator.html#method.zip)
motivates the explicit equal-length/range checks. Online docs are 1.99;
the actual build uses stable APIs on local Rust1.97.1.

## Every before/after comparison

All 171 full/half comparisons follow. A/A requires 0.95–1.05; guards require
C/A at most 1.05. Goals retain their original metric-specific stricter limits.
Disk has no A/A control. A failed guard remains recorded when its control fails.

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
logs are byte-exact gzip supplements. One declaration-only KeyError occurred
before engine copy; its original helper and key-only repair are retained,
as is an unexecuted helper-path draft correction. No engine-test retry occurred.

No new supported upgrade, reliable release ETA, fresh competitor ranking,
universal win, Native CPU/RSS or physical power-loss guarantee is claimed.
Recent raw GitHub backup remains unverified; no recent raw deletion is eligible.
See [reproduction](benchmarks/adaptive-speed-116/REPRODUCE.md) and the
[complete audit](benchmarks/adaptive-speed-116/complete-audit-proof.json).
'''
p=REPO/'ADAPTIVE_ENGINE_116.md';assert not p.exists();p.write_text(report,encoding='utf-8',newline='\n')
assert len([s for s in report.splitlines() if s.startswith('| full |') or s.startswith('| half_')])==171
for name in ['README.md','BENCHMARK_HISTORY.md']:
 p=REPO/name;text=p.read_text(encoding='utf-8');assert 'ADAPTIVE_ENGINE_116.md' not in text
 p.write_text(text.rstrip()+'\n\n- [Adaptive grouped-range trial 116](ADAPTIVE_ENGINE_116.md): 796 fresh tests, 359 recovery commands and 324 correct cases. Grouped medians improve 21.94% ordered and 20.91% late versus016 with full/half controls, but 21 controls/five guards/three goals fail. All252 service cases unstarted; supported016 unchanged. Complete restored evidence retained.\n',encoding='utf-8',newline='\n')
assert all(sha(REPO/p)==h for p,h in protected.items())
git('add','--','README.md','BENCHMARK_HISTORY.md','ADAPTIVE_ENGINE_116.md','benchmarks/adaptive-speed-116')
assert all(s in ['README.md','BENCHMARK_HISTORY.md','ADAPTIVE_ENGINE_116.md'] or s.startswith('benchmarks/adaptive-speed-116/') for s in git('diff','--cached','--name-only').splitlines())
check=rawgit('diff','--cached','--check');exception='benchmarks/adaptive-speed-116/outcomes_098.py'
assert check.returncode==2 and check.stdout==(exception+':41: new blank line at EOF.\n').encode() and not check.stderr
blob=rawgit('show',':'+exception);assert blob.returncode==0 and blob.stdout==(W/'outcomes_098.py').read_bytes()==(REPO/exception).read_bytes()
git('diff','--cached','--check','--','.',':(exclude)'+exception)
proof={'exact_original_raw_EOF_whitespace_narrow_exception':exception,'raw_sha256':sha(W/'outcomes_098.py'),'strict_original_check_actual_exit':2,'all_other_staged_paths_strict_whitespace_actual_exit':0,'original_raw_bytes_and_frozen_inputs_unchanged':True,'no_source_or_gate_change':True}
(closed/'raw-EOF-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');git('add','--',str(closed/'raw-EOF-proof.json'))
git('diff','--cached','--check','--','.',':(exclude)'+exception)
git('commit','-m','Preserve rejected grouped range116 and exact restored evidence')
head=git('rev-parse','HEAD').strip();assert git('rev-parse','HEAD^').strip()==parent and all(sha(REPO/p)==h for p,h in protected.items()) and not git('status','--porcelain=v1','--untracked-files=all')
proof={'utc':datetime.now(timezone.utc).isoformat(),'head':head,'parent':parent,'repository_clean':True,'supported_source_byte_exact016':True,'trial116_fully_preserved_restored_and_committed':True,'exact_raw_EOF_narrow_exception_only':True,'no_private_upload_or_deletion_claim':True}
(WORK/'commit-116-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof))
