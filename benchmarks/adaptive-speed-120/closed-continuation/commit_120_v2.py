"""Commit/private-push fully restored120 evidence; supported016 stays exact."""
from pathlib import Path
from datetime import datetime,timezone
import ast,gzip,hashlib,json,os,shutil,subprocess
R=Path('D:/Codex/Kestrel');WORK=R/'work';W=WORK/'perf-120';REPO=R/'outputs/kestrel-sql';OUT=REPO/'benchmarks/adaptive-speed-120'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
PARENT='16084f7f6ee1995b1e72625d74fa0d19c24251d4'
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
 proof={'utc':utc(),'actual_gh_exit':p.returncode,'metadata':meta};save(WORK/(label+'-120.json'),proof);return proof
guard=sorted(WORK.glob('guard-final-120-*.json'))[-1];assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
assert git('rev-parse','HEAD').strip()==PARENT and not git('diff','--name-only') and not git('diff','--cached','--name-only')
complete=load(OUT/'complete-audit-proof.json');preserved=load(OUT/'preservation-proof.json');restored=load(OUT/'restored-audit-proof.json');n=complete['native']
assert preserved['complete'] and restored['replay_equals_original_complete_audit'] and complete==load(W/'complete-audit-proof.json')
assert complete['correctness_passed'] and not complete['performance_qualified'] and not complete['release017_qualified']
assert (n['cases'],n['identity_failed'],n['candidate_guards_failed'],n['goals_failed'])==(324,84,22,7)
assert complete['fresh_tests']==836 and complete['fresh_recovery_commands']==359 and len(complete['all_scope_controlled_goal_results'])==2 and len(complete['service']['all_specs'])==252
assert json.loads((WORK/'preserve-120.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
protected={p:sha(REPO/p) for p in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
assert all(sha(REPO/p)==h for p,h in load(WORK/'perf-105/policy.json')['baseline_source_sha256'].items())
private_before=privacy('privacy-before-commit');assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==PARENT
closed=OUT/'closed-continuation';assert not closed.exists();closed.mkdir();logs={}
for name in ['build-120-v1.log','build-120-v2.log','build-120-v3.log','repair-build-120-v2.log','repair-controller-120-v3.log','preflight-120-v3.log','preperformance-120-v3.log','prefix-audit-120-v3.log','native-120-v3.log','native-audit-120-v3.log','prepare-closure-120.log','profile-native-120.log','complete-audit-120.log','prepare-preserver-120.log','preserve-120.log']:
 raw=(WORK/name).read_bytes();p=closed/(name+'.gz');p.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(p.read_bytes())==raw
 logs[name]={'raw_sha256':hashlib.sha256(raw).hexdigest(),'gzip_sha256':sha(p),'byte_exact':True}
save(closed/'raw-log-proof.json',logs);shutil.copy2(Path(__file__),closed/Path(__file__).name);shutil.copy2(guard,closed/guard.name)
for name in ['README.md','BENCHMARK_HISTORY.md']:
 raw=(REPO/name).read_bytes();(closed/(name+'.before-120.gz')).write_bytes(gzip.compress(raw,mtime=0))
report='''# Fused publication index trial 120

**Rejected for release. Supported version remains 0.3.16; 0.3.17 is unreleased.**

The isolated candidate chooses a fused index builder for publications of at
least 4,096 rows, keeping the scalar path below that boundary. It combines
statistics passes and reuses a CRC buffer without changing archive bytes,
durability, receipts, ACKs or publication limits. Earlier experimental queue,
replay and query phases remain. Trial119's rejected decode change is excluded.

Correctness passed: **836 fresh tests, five strict lints, 359 recovery commands,
324 Native cases, 479,232 ACKs and 2,921,356,800 fully checked CRC bytes**.
Both initial build failures, all raw results and complete restored audit are
preserved in this private commit. Controlled exits are not physical power-loss
tests.

Performance failed **84/153 A/A controls, 22/171 regression guards and 7/42
goals**. All **252 service cases remain unstarted**. Passing controls also show
regressions, including +19.23% ordered aggregate p95. Failed controls make their
comparisons inconclusive.

Only two query metrics pass goals and controls in the full run and both halves:

| Late grouped query | 0.3.16 median | Candidate median | Paired reduction |
| --- | ---: | ---: | ---: |
| Median latency | 9,701.00 us | 6,713.25 us | 18.80% |
| p95 latency | 13,337.95 us | 9,885.95 us | 25.01% |

Reductions use within-round paired ratios, not the quotient of displayed
medians. This compares the combined candidate against 0.3.16; it does not
isolate the new builder or establish wins against other databases. No release
ETA or universal performance claim is supported.
'''
p=REPO/'ADAPTIVE_ENGINE_120.md';assert not p.exists();p.write_text(report,encoding='utf-8',newline='\n')
for name in ['README.md','BENCHMARK_HISTORY.md']:
 p=REPO/name;raw=p.read_bytes();assert b'ADAPTIVE_ENGINE_120.md' not in raw
 p.write_bytes(raw+b'\n- [Fused publication index trial120](ADAPTIVE_ENGINE_120.md):836 fresh tests,359 recovery commands and324 correct Native cases;84 controls,22 guards,seven goals fail. All252 service cases unstarted. Complete restored evidence retained; supported016 unchanged.\n')
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
git('add','--','README.md','BENCHMARK_HISTORY.md','ADAPTIVE_ENGINE_120.md','benchmarks/adaptive-speed-120')
assert all(s in ['README.md','BENCHMARK_HISTORY.md','ADAPTIVE_ENGINE_120.md'] or s.startswith('benchmarks/adaptive-speed-120/') for s in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check');git('commit','-m','Preserve fused publication120 qualification and complete raw evidence [skip ci]')
head=git('rev-parse','HEAD').strip();assert git('rev-parse','HEAD^').strip()==PARENT and all(sha(REPO/p)==h for p,h in protected.items()) and not git('status','--porcelain=v1','--untracked-files=all')
save(WORK/'commit-120-proof.json',{'utc':utc(),'head':head,'parent':PARENT,'repository_clean':True,'supported_source_byte_exact016':True,'trial120_fully_preserved_restored_and_committed':True,'strict_whitespace_actual_exit':0,'all_original_raw_bytes_preserved':True,'private_before_commit':private_before})
privacy('privacy-before-push');p=rawgit('push','origin','main')
for name,data in [('push-120.stdout',p.stdout),('push-120.stderr',p.stderr)]:assert not (WORK/name).exists();(WORK/name).write_bytes(data)
save(WORK/'push-120-observation.json',{'utc':utc(),'actual_git_exit':p.returncode,'head':head,'stdout_sha256':sha(WORK/'push-120.stdout'),'stderr_sha256':sha(WORK/'push-120.stderr'),'ordinary_fast_forward_only':True})
assert p.returncode==0,(p.returncode,p.stdout,p.stderr)
remote=git('ls-remote','--exit-code','origin','refs/heads/main').split()[0];assert remote==head
private_after=privacy('privacy-after-push');status=git('status','--porcelain=v1','--untracked-files=all');assert not status
count=int(git('rev-list','--count',remote+'..'+head));assert count==0
proof={'complete':True,'utc':utc(),'head':head,'remote_main_actually_read':remote,'private_after_push':private_after,'local_unpushed_commits':count,'uncommitted_and_untracked_paths':[],'all120_results_full_restore_and_independent_audit_committed':True,'fresh_remote120_raw_download_verification_pending':True,'supported':'0.3.16','release017_qualified':False}
save(WORK/'trial120-final-proof.json',proof);print(json.dumps(proof))
