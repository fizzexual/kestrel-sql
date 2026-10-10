"""Finalize verified partial evidence staging; retain exact original raw EOF whitespace."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,subprocess
R=Path('D:/Codex/Kestrel');WORK=R/'work';W=WORK/'perf-114';REPO=R/'outputs/kestrel-sql';OUT=REPO/'benchmarks/adaptive-speed-114';C=OUT/'closed-continuation'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rawgit(*args):
 p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(REPO),*args],capture_output=True)
 return p
def git(*args):
 p=rawgit(*args);assert p.returncode==0,(args,p.stdout,p.stderr);return p.stdout.decode('utf-8')
def allowed(name):return name in ['README.md','BENCHMARK_HISTORY.md','ADAPTIVE_ENGINE_114.md'] or name.startswith('benchmarks/adaptive-speed-114/')
guard=sorted(WORK.glob('guard-final-114-*.json'))[-1];assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
parent=load(WORK/'commit-113-proof.json')['head'];assert git('rev-parse','HEAD').strip()==parent
assert not git('diff','--name-only') and all(allowed(n) for n in git('diff','HEAD','--name-only').splitlines())
assert all(allowed(n) for n in git('diff','--cached','--name-only').splitlines())
assert not git('diff','HEAD','--name-only','--','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md')
protected={n:sha(REPO/n) for n in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
assert all(sha(REPO/n)==h for n,h in load(WORK/'perf-105/policy.json')['baseline_source_sha256'].items())
complete=load(OUT/'complete-audit-proof.json');preserved=load(OUT/'preservation-proof.json');restored=load(OUT/'restored-audit-proof.json')
assert complete==load(W/'complete-audit-proof.json') and preserved['complete'] and restored['replay_equals_original_complete_audit']
assert complete['correctness_passed'] and not complete['release017_qualified'] and not complete['performance_qualified']
n=complete['native'];assert (n['cases'],n['identity_failed'],n['candidate_guards_failed'],n['goals_failed'])==(324,12,5,9)
assert complete['service']['status']=='UNSTARTED_UNTESTED' and len(complete['service']['all_specs'])==252
for name in ['README.md','BENCHMARK_HISTORY.md']:
 old=(C/(name+'.before-114')).read_bytes();blob=rawgit('show','HEAD:'+name);assert blob.returncode==0 and blob.stdout==old
 expected=old.decode('utf-8').rstrip()+'\n\n- [Adaptive publication trial 114](ADAPTIVE_ENGINE_114.md): 796 fresh tests, 359 recovery commands and 324 correct native cases; nine controlled goal metrics, but 12 controls/five guards/nine goals fail. All 252 service cases unstarted; supported 0.3.16 unchanged. Exact restored raw evidence retained.\n'
 assert (REPO/name).read_bytes()==expected.encode('utf-8')
report=REPO/'ADAPTIVE_ENGINE_114.md';text=report.read_text(encoding='utf-8');assert len([line for line in text.splitlines() if line.startswith('| full |') or line.startswith('| half_')])==171
for name,p in load(C/'raw-log-proof.json').items():
 raw=gzip.decompress((C/(name+'.gz')).read_bytes());assert hashlib.sha256(raw).hexdigest()==p['raw_sha256'] and raw==(WORK/name).read_bytes()
exception='benchmarks/adaptive-speed-114/outcomes_098.py';assert (REPO/exception).read_bytes()==(W/'outcomes_098.py').read_bytes()
check=rawgit('diff','--cached','--check');expected_error=(exception+':41: new blank line at EOF.\n').encode();assert check.returncode==2 and check.stdout==expected_error and not check.stderr
for name,code in [('commit-114.log',1),('commit-114-v2.log',1),('prepare-commit-114-v2.log',0)]:
 raw=(WORK/name).read_bytes();dest=C/(name+'.gz');assert not dest.exists();dest.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(dest.read_bytes())==raw
shutil.copy2(WORK/'prepare_commit_114_v2.py',C/'prepare_commit_114_v2.py');shutil.copy2(Path(__file__),C/Path(__file__).name);shutil.copy2(guard,C/guard.name)
proof={'first_commit_tool_actual_exit_code':1,'second_commit_tool_actual_exit_code':1,'no_commit_on_either_failed_attempt':True,'failure1':'Explicit UTF-8 required for existing README; repaired before staging','failure2':'Strict whitespace check finds one original raw audit helper trailing blank line','exception_path':exception,'raw_copy_sha256':sha(W/'outcomes_098.py'),'original_raw_bytes_and_frozen_inputs_unchanged':True,'all_other_staged_paths_strict_whitespace_checked':True,'all_original_failed_helpers_logs_and_partial_evidence_retained':True,'supported_engine_and_all_other_tracked_changes_absent':True,'generated_report_complete171_comparisons_retained':True}
p=C/'commit-finalization-proof.json';assert not p.exists();p.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
git('add','--','README.md','BENCHMARK_HISTORY.md','ADAPTIVE_ENGINE_114.md','benchmarks/adaptive-speed-114')
assert all(allowed(n) for n in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check','--','.',':(exclude)'+exception)
blob=rawgit('show',':'+exception);assert blob.returncode==0 and blob.stdout==(W/'outcomes_098.py').read_bytes()
git('commit','-m','Preserve rejected adaptive publication114 and exact restored evidence')
head=git('rev-parse','HEAD').strip();assert git('rev-parse','HEAD^').strip()==parent and all(sha(REPO/name)==h for name,h in protected.items()) and not git('status','--porcelain=v1','--untracked-files=all')
proof={'utc':datetime.now(timezone.utc).isoformat(),'head':head,'parent':parent,'repository_clean':True,'supported_source_byte_exact016':True,'trial114_fully_preserved_restored_and_committed':True,'two_commit_only_failures_preserved_and_resolved':True,'raw_original_EOF_whitespace_narrow_exception_verified':True,'no_private_upload_or_deletion_claim':True}
(WORK/'commit-114-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof))
