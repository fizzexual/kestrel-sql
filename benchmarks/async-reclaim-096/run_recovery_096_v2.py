"""Fixed 40 new worker fault boundaries plus 8 concurrent pause/lease cases.
No performance clocks. Every raw stream/store and failed/unstarted case retained.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,itertools,json,os,queue,shutil,subprocess,sys,threading,time,traceback
R=Path('D:/Codex/Kestrel');W=R/'work/perf-096';RAW=W/'native-raw-v2';FIX=W/'worker-fixtures-v2'
sys.path.insert(0,str(Path(__file__).parent));import archive_audit_094 as audit
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'build-proof.json')['complete']
assert load(R/'work/guard-precorrectness-096.json')['active_processes']==[]
assert not RAW.exists() and not FIX.exists();RAW.mkdir();FIX.mkdir()
for p in [Path(__file__),Path(__file__).with_name('archive_audit_094.py'),Path(__file__).with_name('archive_audit_096.py'),Path(__file__).with_name('audit_recovery_096_v2.py'),R/'work/check_processes_096.ps1',R/'work/guard-precorrectness-096.json']:shutil.copy2(p,W/p.name)
bins={n:W/'binaries'/n for n in ['default','incremental','async','combined']}
old=R/'work/perf-090/binaries/released016';bins['released016']=W/'binaries/released016';assert bins['released016'].is_dir()
oldhash={p.relative_to(old).as_posix():sha(p) for p in old.rglob('*') if p.is_file()};assert {p.relative_to(bins['released016']).as_posix():sha(p) for p in bins['released016'].rglob('*') if p.is_file()}==oldhash
save(W/'old-reader-copy-proof-v2.json',{'original':str(old),'files':oldhash,'old016_artifacts_reused_not_new_build_or_tests':True})
driver=W/'driver-control-v2/binary/async_reclaim_probe_096.exe'
assert load(W/'driver-control-v2/build-proof.json')['complete']
specs=[]
for history,target,point,ordinal,mode in itertools.product(['anonymous','named'],['catalog','retired'],['before-delete','after-delete'],[1,20],['error','exit']):
 specs.append({'index':len(specs),'type':'fault','history':history,'target':target,'point':point,'ordinal':ordinal,'mode':mode})
for history,point,mode in itertools.product(['anonymous','named'],['before-complete','after-complete'],['error','exit']):
 specs.append({'index':len(specs),'type':'fault','history':history,'target':'catalog','point':point,'ordinal':1,'mode':mode})
for history,target,action in itertools.product(['anonymous','named'],['catalog','retired'],['publish','drop']):
 specs.append({'index':len(specs),'type':'pause','history':history,'target':target,'point':'before-delete','ordinal':1,'mode':'pause','action':action})
assert len(specs)==48
save(W/'worker-run-declaration-v2.json',{'cases':specs,'fixed_faults':40,'fixed_concurrent_cases':8,'before_first_worker_native':utc()})
freeze={p.relative_to(W).as_posix():sha(p) for folder in [W/'source',W/'binaries',W/'driver-control-v2/source',W/'driver-control-v2/binary'] for p in folder.rglob('*') if p.is_file()}
for n in ['policy.json','declaration-proof.json','source-derivation.json','build-proof.json','worker-run-declaration-v2.json','run_recovery_096_v2.py','archive_audit_094.py','archive_audit_096.py','audit_recovery_096_v2.py','old-reader-copy-proof-v2.json','check_processes_096.ps1','guard-precorrectness-096.json']:freeze[n]=sha(W/n)
for n in ['driver-control-v2/build-proof.json','driver-control-v2/source-derivation.json']:freeze[n]=sha(W/n)
save(W/'worker-recovery-freeze-v2.json',{'files':freeze,'utc':utc(),'no_performance_timers':True})
records=[];cases=[];unstarted=list(specs)
envbase={**os.environ,'TMP':str(W/'tmp'),'TEMP':str(W/'tmp')}
assert not any(k.startswith(('KESTREL_FAULT_','KESTREL_RECLAIM_','KESTREL_ASYNC_')) for k in envbase)
def journal_run(argv,expected=0,env=None):
 idx=len(records);stem=RAW/f'command-{idx:04d}';argv=list(map(str,argv))
 rec={'index':idx,'argv':argv,'started_utc':utc(),'stdout':stem.with_suffix('.stdout').relative_to(W).as_posix(),'stderr':stem.with_suffix('.stderr').relative_to(W).as_posix(),'fault_environment':{k:v for k,v in (env or {}).items() if k.startswith('KESTREL_ASYNC_')}}
 records.append(rec);save(W/'native-run-order-v2.json',records)
 try:r=subprocess.run(argv,env=env or envbase,capture_output=True,timeout=120)
 except subprocess.TimeoutExpired as e:
  stem.with_suffix('.stdout').write_bytes(e.stdout or b'');stem.with_suffix('.stderr').write_bytes(e.stderr or b'');rec.update(timeout=True,completed_utc=utc());save(W/'native-run-order-v2.json',records);raise
 stem.with_suffix('.stdout').write_bytes(r.stdout);stem.with_suffix('.stderr').write_bytes(r.stderr)
 rec.update(returncode=r.returncode,completed_utc=utc(),stdout_sha256=sha(stem.with_suffix('.stdout')),stderr_sha256=sha(stem.with_suffix('.stderr')));save(W/'native-run-order-v2.json',records)
 assert r.returncode==expected,(argv,r.returncode,r.stdout[-700:],r.stderr[-700:])
 return r,rec
def events(raw):return [json.loads(x) for x in raw.splitlines() if x.strip()]
def second_owner(directory):
 result=[]
 for variant in ['default','incremental','async','released016']:
  r,rec=journal_run([bins[variant]/'kestrel.exe','--archive',directory,'--sql','SELECT COUNT(*) FROM events'],expected=1)
  assert b'lock' in r.stderr.lower(),(variant,r.stderr);result.append(rec['index'])
 return result
def cold(directory,groups,history):
 indices=[]
 r,rec=journal_run([driver,directory,'verify',history,groups]);assert events(r.stdout)[-1]['event']=='verified';indices.append(rec['index'])
 for variant in ['default','incremental','async','released016']:
  r,rec=journal_run([bins[variant]/'kestrel.exe','--archive',directory,'--sql','SELECT COUNT(*), SUM(value) FROM events'])
  rows=groups*100;assert json.loads(r.stdout)['result']['rows']==[[rows,rows*(rows-1)]];indices.append(rec['index'])
 return indices
def progress():save(W/'worker-recovery-progress-v2.json',{'completed_cases':cases,'native_commands':len(records),'unstarted':unstarted})
class Owned:
 def __init__(self,argv,env):
  idx=len(records);stem=RAW/f'command-{idx:04d}';argv=list(map(str,argv));self.queue=queue.Queue();self.events=[]
  self.err=stem.with_suffix('.stderr').open('wb');self.out=stem.with_suffix('.stdout')
  self.p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,env=env,creationflags=0x08000000)
  self.rec={'index':idx,'argv':argv,'pid':self.p.pid,'owned_Popen_process_handle':True,'started_utc':utc(),'stdout':self.out.relative_to(W).as_posix(),'stderr':stem.with_suffix('.stderr').relative_to(W).as_posix(),'fault_environment':{k:v for k,v in env.items() if k.startswith('KESTREL_ASYNC_')}}
  records.append(self.rec);save(W/'native-run-order-v2.json',records)
  def read():
   with self.out.open('wb') as f:
    for line in iter(self.p.stdout.readline,b''):
     f.write(line);f.flush()
     try:e=json.loads(line);self.events.append(e);self.queue.put(e)
     except BaseException as exc:self.queue.put(exc)
   self.queue.put(EOFError('owned Native stdout closed'))
  self.reader=threading.Thread(target=read);self.reader.start()
 def wait(self,event):
  deadline=time.monotonic()+30
  while True:
   e=self.queue.get(timeout=max(.001,deadline-time.monotonic()))
   if isinstance(e,BaseException):raise e
   if e['event']==event:return e
 def send(self,text):self.p.stdin.write((text+'\n').encode());self.p.stdin.flush()
 def finish(self):
  try:code=self.p.wait(timeout=45)
  except subprocess.TimeoutExpired:
   # Exact newly launched child's retained Windows process handle; no PID enumeration.
   self.p.kill();self.p.wait(timeout=10);self.rec['owned_timeout_termination']=True;raise
  finally:
   self.reader.join(timeout=5);assert not self.reader.is_alive();self.p.stdout.close();self.p.stdin.close();self.err.close()
   self.rec.update(returncode=self.p.returncode,completed_utc=utc(),stdout_sha256=sha(self.out),stderr_sha256=sha(W/self.rec['stderr']));save(W/'native-run-order-v2.json',records)
  assert code==0,(self.rec, (W/self.rec['stderr']).read_bytes()[-500:])
 def abort(self):
  if self.p.poll() is None:self.p.kill();self.p.wait(timeout=10);self.rec['owned_hard_error_termination']=True
  self.reader.join(timeout=5);self.p.stdout.close();self.p.stdin.close();self.err.close();self.rec.update(returncode=self.p.returncode,completed_utc=utc());save(W/'native-run-order-v2.json',records)
try:
 for spec in specs:
  d=FIX/f"case-{spec['index']:03d}";d.mkdir();store=d/'archive';log=d/'worker.jsonl';marker=d/'gate'
  env={**envbase,'KESTREL_ASYNC_POINT':spec['point'],'KESTREL_ASYNC_KIND':spec['target'] if 'delete' in spec['point'] else 'batch','KESTREL_ASYNC_ORDINAL':str(spec['ordinal']),'KESTREL_ASYNC_MODE':spec['mode'],'KESTREL_ASYNC_LOG':str(log),'KESTREL_ASYNC_MARKER':str(marker)}
  owner_checks=[];groups=64
  if spec['type']=='fault':
   r,rec=journal_run([driver,store,'fault',spec['history'],spec['target']],expected=86 if spec['mode']=='exit' else 0,env=env)
   stream=events(r.stdout);native_index=rec['index']
   if spec['mode']=='error':
    end=next(x for x in stream if x['event']=='completed');assert end['stats']['failures']==1 and end['stats']['inflight']==0 and end['stats']['max_inflight']<=2
  else:
   p=Owned([driver,store,'pause',spec['history'],spec['target']],env);native_index=p.rec['index']
   try:
    scheduled=p.wait('scheduled');assert scheduled['selected']==20
    deadline=time.monotonic()+15
    while not marker.with_suffix('.entered').exists():
     assert p.p.poll() is None and time.monotonic()<deadline;time.sleep(.005)
    owner_checks+=second_owner(store)
    if spec['action']=='publish':
     p.send('publish');e=p.wait('published_while_worker_paused');assert e['stats']['inflight']==2 and e['stats']['max_inflight']==2 and e['stats']['rejected']>0
     groups=96;marker.with_suffix('.release').write_bytes(b'owned continuation release');p.send('finish');end=p.wait('finished');assert end['stats']['failures']==0 and end['stats']['inflight']==0
    else:
     p.send('drop');p.wait('archive_dropped');owner_checks+=second_owner(store)
     marker.with_suffix('.release').write_bytes(b'owned join release');p.wait('worker_joined_pin_retained');owner_checks+=second_owner(store)
     p.send('release-pin');p.wait('all_dropped')
    p.finish();stream=p.events
   except BaseException:p.abort();raise
  hook=events(log.read_bytes());matches=[x for x in hook if x['phase']==spec['point'] and x['ordinal']==spec['ordinal'] and (x['kind']==spec['target'] if 'delete' in spec['point'] else x['kind']=='batch')];assert matches,('cut not reached',spec)
  acks=[x for x in stream if x['event']=='ack'];assert len(acks)==groups and [x['group'] for x in acks]==list(range(groups))
  rows=[[i,2*i,i%97] for i in range(groups*100)]
  receipts={f"seed:{x['group']}":(rows[x['group']*100:(x['group']+1)*100],x['generation']) for x in acks} if spec['history']=='named' else {}
  decoded=audit.check(store,rows,receipts)
  assert (store/'segment-00000000000000000999.ks2').read_bytes()==b'096 untouched crash orphan'
  assert (store/'catalog-00000000000000000998.pending').read_bytes()==b'096 untouched pending'
  before={x.name:sha(x) for x in store.iterdir() if x.is_file()}
  reads=cold(store,groups,spec['history']);assert {x.name:sha(x) for x in store.iterdir() if x.is_file()}==before
  cases.append({'spec':spec,'directory':store.relative_to(W).as_posix(),'native_command':native_index,'acks':acks,'hook_log':log.relative_to(W).as_posix(),'hook_sha256':sha(log),'actual_cut_reached':matches[0],'owner_rejection_commands':owner_checks,'cold_reader_commands':reads,'decode':decoded,'closed_inventory':before,'orphan_pending_exact':True})
  unstarted.remove(spec);progress();print(json.dumps({'case':spec['index'],'passed':True,'groups':groups,'mode':spec['mode']}),flush=True)
 for n,h in freeze.items():assert sha(W/n)==h,n
 save(W/'worker-recovery-proof-v2.json',{'complete':True,'cases':cases,'fixed_faults':40,'fixed_concurrent_cases':8,'new_worker_cutpoints_not_reused_094':True,'native_commands':len(records),'ack_batches':sum(len(c['acks']) for c in cases),'full_crc_bytes':sum(c['decode']['full_block_crc_bytes'] for c in cases),'all_frozen_inputs_exact':True,'no_performance_timers':True,'physical_power_loss_not_qualified':True})
 print(json.dumps({'complete':True,'fault_cases':40,'concurrent_cases':8,'native_commands':len(records)}),flush=True)
except BaseException:
 save(W/'worker-recovery-failure-v2.json',{'error':traceback.format_exc(),'cases':cases,'unstarted':unstarted,'native_commands':len(records),'no_performance_timers':True});raise
