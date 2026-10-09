"""Preserve failed recording and exempt only proven inherited EOF whitespace."""
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
assert git('rev-parse','HEAD').decode().strip()==PARENT
assert load(OUT/'preservation-proof.json')['complete'] and load(OUT/'restored-audit-proof.json')['passed'] and not load(W/'complete-audit-proof.json')['performance_qualified']
allowed=lambda n:n in ['PARALLEL_SYNC_SPEED_102.md','README.md','BENCHMARK_HISTORY.md'] or n.startswith('benchmarks/parallel-sync-speed-102/')
assert all(allowed(n) for n in git('diff','--cached','--name-only').decode().splitlines())
assert not git('diff','--name-only')
supported=load(OUT/'closed-continuation/supported-main-byte-proof.json')['files_sha256']
for n,h in supported.items():assert sha(REPO/n)==h==hashlib.sha256(git('show','HEAD:'+n)).hexdigest()
failed=OUT/'failed-recording-v1';assert not failed.exists();failed.mkdir()
for src,name in [(H/'commit-102.log','commit-102.log'),(H/'commit_speed_102.py','commit_speed_102.py'),(REPO/'PARALLEL_SYNC_SPEED_102.md','PARALLEL_SYNC_SPEED_102.md'),(REPO/'README.md','README.md'),(REPO/'BENCHMARK_HISTORY.md','BENCHMARK_HISTORY.md'),(OUT/'scope-results.json','scope-results.json')]:shutil.copy2(src,failed/name)
exemptions=[]
for name in ['audit_service_095.py','outcomes_098.py']:
 path=OUT/name;rel='benchmarks/parallel-sync-speed-102/'+name
 assert path.read_bytes()==(W/name).read_bytes()==(H/'restored-parallel-sync-speed-102'/name).read_bytes()==(H/'perf-098'/name).read_bytes()
 assert sha(path)==load(W/'timing-freeze.json')['sha256'][name]
 exemptions.append({'path':rel,'sha256':sha(path),'byte_exact_original098_frozen102_and_restored102':True,'exception_only_preexisting_blank_line_at_EOF':True})
save(failed/'failure-preservation.json',{'utc':datetime.now(timezone.utc).isoformat(),'actual_exit_code':1,'commit_created':False,'reason':'Strict whitespace check rejected inherited EOF blank lines in exactly two frozen audit helpers. Source, performance data and restoration were unaffected.','exact_helper_log_and_generated_documents_retained':True,'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in failed.iterdir() if p.is_file()},'no_native_or_timer_rerun':True})
closed=OUT/'closed-continuation';shutil.copy2(Path(__file__),closed/Path(__file__).name)
save(closed/'inherited-whitespace-proof.json',{'passed':True,'exemptions':exemptions,'no_frozen_bytes_modified':True,'strict_whitespace_check_still_required_for_every_other_staged_file':True})
git('add','--','benchmarks/parallel-sync-speed-102')
names=[e['path'] for e in exemptions]
strict='core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'
git('-c',strict,'diff','--cached','--check','--','.',*[':(exclude)'+n for n in names])
git('-c','core.whitespace=blank-at-eol,space-before-tab,cr-at-eol','diff','--cached','--check','--',*names)
staged=git('diff','--cached','--name-only').decode().splitlines();assert all(allowed(n) for n in staged)
for n,h in supported.items():assert sha(REPO/n)==h
git('commit','-m','Preserve complete native and service102 performance rejection and restored evidence')
head=git('rev-parse','HEAD').decode().strip();assert not git('status','--porcelain')
save(H/'commit-102-proof.json',{'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'head':head,'parent':PARENT,'files_committed':len(staged),'supported_source_unchanged':True,'full_fixed_performance_rejected':True,'private_local_commit_no_remote_publication':True,'failed_first_recording_and_exact_inherited_whitespace_preserved':True})
print(json.dumps(load(H/'commit-102-proof.json')),flush=True)
