"""Serial owned fixed native cohort or four excluded complete smokes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel');W=R/'work/perf-102';sys.path.insert(0,str(W))
from native_resources_088 import read_process
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def utc():return datetime.now(timezone.utc).isoformat()
assert not any(n.startswith(('KESTREL_FAULT','KESTREL_ASYNC','KESTREL_COUPLE','KESTREL_RECLAIM')) for n in os.environ)
policy=load(W/'policy.json');assert sha(W/'policy.json')=='2cfc5325f1097b311ed7c2b3eb9892f5faad470313a21af04696f61b314b5ef3'
smoke=sys.argv[1:]==['--smoke'];assert smoke or not sys.argv[1:]
for mode in ['normal','candidate']:
 p=W/'binaries'/mode/'publication_probe_100.exe';assert sha(p)==load(W/'build-proof.json')['binaries'][p.relative_to(W).as_posix()]
if smoke:
 specs=[{'index':i,'history':h,'variant':'baseline_a' if v=='normal' else 'candidate','binary':v,'probe_variant':'baseline_a'} for i,(h,v) in enumerate((h,v) for h in ['anonymous','named'] for v in ['normal','candidate'])]
 folder=W/'native-smokes';output=W/'native-smokes.json'
else:
 assert load(W/'preperformance-proof.json')['passed'];freeze=load(W/'timing-freeze.json');assert all(sha(W/n)==h for n,h in freeze['sha256'].items())
 guard=sorted((R/'work').glob('guard-pretime-102-*.json'))[-1];assert not load(guard)['active_processes'] and load(guard)['reset_phase']=='waiting-for-full-codex-exit';shutil.copy2(guard,W/guard.name)
 specs=policy['native']['cases'];folder=W/'native-cases';output=W/'paired-native.json'
assert not output.exists() and not folder.exists();folder.mkdir()
report={'trial':102,'complete':False,'excluded_from_main_gates':smoke,'started_utc':utc(),'policy_sha256':sha(W/'policy.json'),'cases':[],'failed_cases':[],'unstarted_cases':specs}
if not smoke:report['freeze_sha256']=sha(W/'timing-freeze.json')
save(output,report)
for index,spec in enumerate(specs):
 d=folder/f'{index:03d}';d.mkdir();proc=None
 argv=[str(W/'binaries'/spec['binary']/'publication_probe_100.exe'),str(d/'archive'),spec['probe_variant'],spec['history']]
 record={'case_index':index,**spec,'argv':argv,'started_utc':utc(),'raw':(d/'stdout.json').relative_to(W).as_posix(),'stderr':(d/'stderr.log').relative_to(W).as_posix()}
 try:
  assert shutil.disk_usage(W).free>policy['disk_min_free_bytes']
  with (d/'stdout.json').open('xb') as stdout,(d/'stderr.log').open('xb') as stderr:
   proc=subprocess.Popen(argv,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
   identity=read_process(proc.pid);record['owned_process_identity']={k:identity[k] for k in ['pid','creation_filetime']};save(d/'status.json',record)
   try:code=proc.wait(timeout=policy['native']['owned_health_deadline_seconds'])
   except subprocess.TimeoutExpired:
    record.update(timeout=True,error='Owned health deadline; never a successful finish');save(d/'status.json',record)
    if proc.poll() is None:
     assert read_process(proc.pid)['creation_filetime']==identity['creation_filetime'];proc.kill();proc.wait(timeout=10);record['exact_owned_handle_killed_after_failure']=True
    raise
  record.update(exit_code=code,finished_utc=utc());save(d/'status.json',record);assert code==0,record
  x=load(d/'stdout.json');assert x['trial']==100 and x['variant']==spec['probe_variant'] and len(x['append_records'])==512
  assert x['rows']==83968 and x['pin_after_owner_drop_verified'] and x['cold_reopen_passed']
  report['cases'].append(record);report['unstarted_cases']=specs[index+1:];save(output,report)
  print(json.dumps({'completed':index+1,'total':len(specs),'history':spec['history'],'variant':spec['variant']}),flush=True)
 except BaseException:
  record.update(error=traceback.format_exc(),finished_utc=utc())
  if proc is not None and proc.poll() is None:proc.kill();proc.wait(timeout=10);record['exact_owned_handle_killed_after_failure']=True
  save(d/'status.json',record);report['failed_cases'].append(record);report['unstarted_cases']=specs[index+1:];save(output,report);raise
report.update(complete=True,finished_utc=utc());save(output,report)
print(json.dumps({'complete':True,'cases':len(specs),'excluded_smokes':smoke,'no_adoption':True}),flush=True)
