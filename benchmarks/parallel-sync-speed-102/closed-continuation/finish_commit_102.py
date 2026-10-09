"""Complete102 recording with explicit inherited-only whitespace exception."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
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
guards=sorted(H.glob('guard-final-102v2-*.json'));assert guards;guard=load(guards[-1]);assert guard['active_processes']==[] and guard['verified_idle_terminal_reset']
assert git('rev-parse','HEAD').decode().strip()==PARENT and not git('diff','--name-only')
assert load(OUT/'preservation-proof.json')['complete'] and load(OUT/'restored-audit-proof.json')['passed'] and not load(W/'complete-audit-proof.json')['performance_qualified']
supported=load(OUT/'closed-continuation/supported-main-byte-proof.json')['files_sha256']
for n,h in supported.items():assert sha(REPO/n)==h==hashlib.sha256(git('show','HEAD:'+n)).hexdigest()
exceptions=load(OUT/'closed-continuation/inherited-whitespace-proof.json')['exemptions']
for e in exceptions:
 name=Path(e['path']).name;assert sha(OUT/name)==sha(W/name)==sha(H/'restored-parallel-sync-speed-102'/name)==sha(H/'perf-098'/name)==e['sha256']
failed=OUT/'failed-recording-v2';assert not failed.exists();failed.mkdir()
for n in ['resume_commit_102.py','resume-commit-102.log']:shutil.copy2(H/n,failed/n)
save(failed/'failure-preservation.json',{'utc':datetime.now(timezone.utc).isoformat(),'actual_exit_code':1,'commit_created':False,'reason':'Omitting blank-at-eof retained Git default whitespace behavior. All other staged files passed the full strict check. Only the two verified inherited files need explicit -blank-at-eof.','files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in failed.iterdir() if p.is_file()},'no_source_data_gate_reset_or_timer_change':True})
closed=OUT/'closed-continuation';shutil.copy2(Path(__file__),closed/Path(__file__).name);shutil.copy2(guards[-1],closed/guards[-1].name)
git('add','--','benchmarks/parallel-sync-speed-102')
names=[e['path'] for e in exceptions]
git('-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check','--','.',*[':(exclude)'+n for n in names])
git('-c','core.whitespace=blank-at-eol,space-before-tab,cr-at-eol,-blank-at-eof','diff','--cached','--check','--',*names)
staged=git('diff','--cached','--name-only').decode().splitlines();assert all(n in ['PARALLEL_SYNC_SPEED_102.md','README.md','BENCHMARK_HISTORY.md'] or n.startswith('benchmarks/parallel-sync-speed-102/') for n in staged)
for n,h in supported.items():assert sha(REPO/n)==h
git('commit','-m','Preserve complete native and service102 performance rejection and restored evidence')
head=git('rev-parse','HEAD').decode().strip();assert not git('status','--porcelain')
save(H/'commit-102-proof.json',{'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'parent':PARENT,'files_committed':len(staged),'supported_source_unchanged':True,'full_fixed_performance_rejected':True,'private_local_commit_no_remote_publication':True,'both_failed_recordings_and_exact_inherited_whitespace_preserved':True,'all_new_files_strict_whitespace_passed':True})
print(json.dumps(load(H/'commit-102-proof.json')),flush=True)
