"""Commit/private-push fully restored119 evidence; supported016 stays exact."""
from pathlib import Path
from datetime import datetime,timezone
import ast,gzip,hashlib,json,os,shutil,subprocess
R=Path('D:/Codex/Kestrel');WORK=R/'work';W=WORK/'perf-119';REPO=R/'outputs/kestrel-sql';OUT=REPO/'benchmarks/adaptive-speed-119'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
PARENT='8e856e17e0743a91ce60bf269cbdc63f36ab8216'
def utc():return datetime.now(timezone.utc).isoformat()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):
 assert not p.exists(),p
 p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
def command(argv):return subprocess.run(argv,capture_output=True,timeout=300,env=os.environ|{'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'})
def rawgit(*args):return command(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(REPO),*args])
def git(*args):
 p=rawgit(*args);assert p.returncode==0,(args,p.stdout,p.stderr);return p.stdout.decode('utf-8')
def privacy(label):
 p=command([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate,url']);assert p.returncode==0,(p.returncode,p.stderr)
 meta=json.loads(p.stdout);assert meta=={'isPrivate':True,'url':'https://github.com/fizzexual/kestrel-sql'}
 proof={'utc':utc(),'actual_gh_exit':p.returncode,'metadata':meta};save(WORK/(label+'-119.json'),proof);return proof
guard=sorted(WORK.glob('guard-final-119-*.json'))[-1];assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
assert git('rev-parse','HEAD').strip()==PARENT and not git('diff','--name-only') and not git('diff','--cached','--name-only')
complete=load(OUT/'complete-audit-proof.json');preserved=load(OUT/'preservation-proof.json');restored=load(OUT/'restored-audit-proof.json');n=complete['native']
assert preserved['complete'] and restored['replay_equals_original_complete_audit'] and complete==load(W/'complete-audit-proof.json')
assert complete['correctness_passed'] and not complete['performance_qualified'] and not complete['release017_qualified']
assert (n['cases'],n['identity_failed'],n['candidate_guards_failed'],n['goals_failed'])==(324,21,5,2)
assert complete['fresh_tests']==828 and complete['fresh_recovery_commands']==359 and len(complete['all_scope_controlled_goal_results'])==8 and len(complete['service']['all_specs'])==252
assert json.loads((WORK/'preserve-119.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
protected={p:sha(REPO/p) for p in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
assert all(sha(REPO/p)==h for p,h in load(WORK/'perf-105/policy.json')['baseline_source_sha256'].items())
private_before=privacy('privacy-before-commit');assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==PARENT
closed=OUT/'closed-continuation';assert not closed.exists();closed.mkdir();logs={}
for name in ['build-119-v1.log','preflight-119-v1.log','preperformance-119-v1.log','prefix-audit-119-v1.log','native-119-v1.log','native-audit-119-v1.log','prepare-closure-119.log','profile-native-119.log','complete-audit-119.log','prepare-preserver-119.log','preserve-119.log']:
 raw=(WORK/name).read_bytes();p=closed/(name+'.gz');p.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(p.read_bytes())==raw
 logs[name]={'raw_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':sha(p),'byte_exact':True}
save(closed/'raw-log-proof.json',logs);shutil.copy2(Path(__file__),closed/Path(__file__).name);shutil.copy2(guard,closed/guard.name)
for name in ['README.md','BENCHMARK_HISTORY.md']:
 raw=(REPO/name).read_bytes();(closed/(name+'.before-119.gz')).write_bytes(gzip.compress(raw,mtime=0))
report='''# Bounded compaction workspace trial 119

All 828 fresh test executions, five strict lints, 359 recovery commands and
324 Native cases pass correctness. Performance qualification fails **21/153
A/A checks, 5/171 guards and 2/42 goals**. All 252 service cases are unstarted.
Supported main remains byte-exact **0.3.16**; **0.3.17 is unqualified and unreleased**.

Compaction previously allocated a decoded vector for every input block.
The isolated candidate reuses one 4096-integer workspace across input runs
and columns through the unchanged CRC-first decoder. Its logical payload
capacity is 32 KiB. The original allocating feature-disabled path is exact.
Archive/Cargo byte inverses pass; all other corrected117 source, Reader,
collector, query, live writer, receipt, lock and common-driver bytes are exact.
Selection limits, reads/checksums, output order, maintenance/publication counts,
ACK timing and writer joins are unchanged. The stable
[Vec::clear API](https://doc.rust-lang.org/std/vec/struct.Vec.html#method.clear)
retains capacity. This uses existing APIs and the installed Rust1.97.1 toolchain.

The complete untimed118 diagnosis associated pressure tails with maintenance
gaps. It did not establish exclusive CPU/IO attribution or allocation causality.
This cohort compares the combined collector/filter/replay/scan/group-range/digest/
compaction candidate against fresh D: 016 A/A baselines. It does not isolate
the compaction change versus117 or establish a fresh competitor ranking.

Two new compaction integration tests check independent RAM SQL over full and
partial blocks, signed extrema and late data; repeat compaction, original receipt
identity/mismatch, pinned snapshots, reclaim and reopen; late-input CRC and
truncation rejection before publication with exact catalogs/generation, then
repair/retry. Damaged input bytes and error messages are preserved in test stores.
The complete eight-mode suite and all five strict lints passed on fresh targets.
Recovery includes28 publication injected-error/owned-exit cases,10 corruptions,
two legacy formats, two byte fixtures,256 concurrent ACKs, two named scenarios,
300 cold SQL checks and69,360 CRC bytes. This is not physical power-loss proof.

Four Native/two service excluded smokes,48 balanced-order checks,six invalid
outcome controls,two invalid-order rejections and frozen input provenance pass.
All324 cases ran once, twelve rounds/all six orders/full and both halves.
All479,232 ACKs and2,921,356,800 CRC bytes pass complete independent payload,
index, receipt, digest, generation, cold SQL and raw quantile checks. Every
controller actually exited0. No selected timing rerun or gate relaxation.

## Controlled goals

Eight metrics meet their targets and corresponding A/A controls in full and
both halves. Reductions use median within-round paired ratios; they need not
equal the quotient of displayed medians. These combined gains do not qualify
the release while other mandatory gates fail.

| Workload | Metric | Unit | 016 median | Candidate median | Full paired reduction | Full A/A | Full/both-half targets and controls |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
'''
def unit(row):
 if row['metric']=='disk':return 'bytes',1
 if '/' in row['metric'] or row['workload']=='identified-replay':return 'us',1 if '/' in row['metric'] else 1000
 return 'ms',1e-6
for row in complete['all_scope_controlled_goal_results']:
 full=next(s for s in row['scopes'] if s['scope']=='full');u,scale=unit(full)
 report+=f"| {row['workload']} | {row['metric']} | {u} | {full['before_median']*scale:.6f} | {full['after_median']*scale:.6f} | {(1-full['CA'])*100:.2f}% | {full['AA']:.8f} | pass |\n"
report+='\n## All failures\n\nPassing controls with failed guards are calibrated regressions. Failed controls make a comparison inconclusive. Service remains unstarted because Native qualification fails.\n'
for row in n['guards']:
 if row['passed']:continue
 c=next((c for c in n['controls'] if all(c[k]==row[k] for k in ['scope','workload','metric'])),None)
 state='calibrated regression' if c and c['passed'] else 'inconclusive: control fails'
 report+=f"\n- {row['scope']} {row['workload']} {row['metric']}: C/A {row['CA']:.8f} ({(row['CA']-1)*100:+.2f}%); A/A {row['AA']:.8f}; {state}.\n"
for row in n['goals']:
 if row['passed']:continue
 c=next(c for c in n['controls'] if all(c[k]==row[k] for k in ['scope','workload','metric']))
 report+=f"\n- Goal miss: {row['scope']} {row['workload']} {row['metric']}, C/A {row['CA']:.8f} versus {row['limit']}; A/A {row['AA']:.8f}; {'control passes' if c['passed'] else 'inconclusive: control fails'}.\n"
report+='''

## Every before/after comparison

All171 full/half comparisons follow. A/A requires0.95-1.05; candidate guards
require C/A at most1.05; goals retain their stricter metric-specific limits.
Disk has no A/A control. All failed guards remain even when controls fail.

| Scope | Workload | Metric | Unit | Baseline median | Candidate median | A/A | Control | C/A | Guard | Goal limit | Goal |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | ---: | --- |
'''
for row in n['summaries']:
 same=lambda v:all(v[k]==row[k] for k in ['scope','workload','metric'])
 c=next((v for v in n['controls'] if same(v)),None);g=next(v for v in n['guards'] if same(v));goal=next((v for v in n['goals'] if same(v)),None);u,scale=unit(row)
 report+=f"| {row['scope']} | {row['workload']} | {row['metric']} | {u} | {row['before_median']*scale:.6f} | {row['after_median']*scale:.6f} | {row['AA']:.8f} | {'n/a' if c is None else ('pass' if c['passed'] else 'FAIL')} | {row['CA']:.8f} | {'pass' if g['passed'] else 'FAIL'} | {'n/a' if goal is None else str(goal['limit'])} | {'n/a' if goal is None else ('pass' if goal['passed'] else 'FAIL')} |\n"
report+=f'''
## Exact preservation

{preserved['files']:,} files,{preserved['directories']:,} directories,
{len(preserved['parts'])} bounded ZIP parts and{preserved['logical_bytes']:,}
logical bytes pass every member CRC/order/offset/size and whole original/restored
SHA/size/file/directory sets before and after complete pure replay. Sources,
binaries, full raw streams/stores, damaged compaction inputs, all prerequisites,
controls/guards/goals/profile and252 unstarted service specs are preserved.
Only inventoried regenerable target/Python caches are excluded; originals remain.
Closed logs are byte-exact gzip supplements. Display-only copied text may have
one final newline; every changed original is additionally byte-exact gzip.
Internal ZIP raw bytes and frozen sources are unchanged. No119 raw cleanup is
eligible until fresh complete private remote content verification.

See [reproduction](benchmarks/adaptive-speed-119/REPRODUCE.md) and
[complete audit](benchmarks/adaptive-speed-119/complete-audit-proof.json).
No release ETA, universal win, new competitor ranking or adoption is established.
'''
p=REPO/'ADAPTIVE_ENGINE_119.md';assert not p.exists();p.write_text(report,encoding='utf-8',newline='\n')
assert len([s for s in report.splitlines() if s.startswith('| full |') or s.startswith('| half_')])==171
for name in ['README.md','BENCHMARK_HISTORY.md']:
 p=REPO/name;raw=p.read_bytes();assert b'ADAPTIVE_ENGINE_119.md' not in raw
 p.write_bytes(raw+b'\n- [Bounded compaction workspace trial119](ADAPTIVE_ENGINE_119.md):828 fresh tests,359 recovery commands and324 correct Native cases;21 controls,five guards,two goals fail. All252 service cases unstarted. Complete restored evidence retained; supported016 unchanged.\n')
views={}
for p in sorted(OUT.iterdir()):
 if not p.is_file() or p.suffix not in ['.py','.json','.md','.ps1']:continue
 raw=p.read_bytes();text=raw.decode('utf-8-sig');normalized=text.rstrip()+'\n'
 if normalized.encode()==raw:continue
 if p.suffix=='.py':assert ast.dump(ast.parse(text))==ast.dump(ast.parse(normalized))
 if p.suffix=='.json':assert json.loads(text)==json.loads(normalized)
 dest=closed/(p.name+'.original-bytes.gz');dest.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(dest.read_bytes())==raw
 p.write_text(normalized,encoding='utf-8',newline='\n');views[p.name]={'original_sha256':hashlib.sha256(raw).hexdigest(),'display_sha256':sha(p),'only_terminal_whitespace_or_BOM_normalized':True,'original_bytes_gzip':dest.name}
save(closed/'display-view-proof.json',views)
assert all(sha(REPO/p)==h for p,h in protected.items())
git('add','--','README.md','BENCHMARK_HISTORY.md','ADAPTIVE_ENGINE_119.md','benchmarks/adaptive-speed-119')
assert all(s in ['README.md','BENCHMARK_HISTORY.md','ADAPTIVE_ENGINE_119.md'] or s.startswith('benchmarks/adaptive-speed-119/') for s in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check');git('commit','-m','Preserve bounded compaction119 qualification and complete raw evidence')
head=git('rev-parse','HEAD').strip();assert git('rev-parse','HEAD^').strip()==PARENT and all(sha(REPO/p)==h for p,h in protected.items()) and not git('status','--porcelain=v1','--untracked-files=all')
save(WORK/'commit-119-proof.json',{'utc':utc(),'head':head,'parent':PARENT,'repository_clean':True,'supported_source_byte_exact016':True,'trial119_fully_preserved_restored_and_committed':True,'strict_whitespace_actual_exit':0,'all_original_raw_bytes_preserved':True,'private_before_commit':private_before})
privacy('privacy-before-push');p=rawgit('push','origin','main')
for name,data in [('push-119.stdout',p.stdout),('push-119.stderr',p.stderr)]:assert not (WORK/name).exists();(WORK/name).write_bytes(data)
save(WORK/'push-119-observation.json',{'utc':utc(),'actual_git_exit':p.returncode,'head':head,'stdout_sha256':sha(WORK/'push-119.stdout'),'stderr_sha256':sha(WORK/'push-119.stderr'),'ordinary_fast_forward_only':True})
assert p.returncode==0,(p.returncode,p.stdout,p.stderr)
remote=git('ls-remote','--exit-code','origin','refs/heads/main').split()[0];assert remote==head
private_after=privacy('privacy-after-push');status=git('status','--porcelain=v1','--untracked-files=all');assert not status
count=int(git('rev-list','--count',remote+'..'+head));assert count==0
proof={'complete':True,'utc':utc(),'head':head,'remote_main_actually_read':remote,'private_after_push':private_after,'local_unpushed_commits':count,'uncommitted_and_untracked_paths':[],'all119_results_full_restore_and_independent_audit_committed':True,'fresh_remote119_raw_download_verification_pending':True,'supported':'0.3.16','release017_qualified':False}
save(WORK/'trial119-final-proof.json',proof);print(json.dumps(proof))
