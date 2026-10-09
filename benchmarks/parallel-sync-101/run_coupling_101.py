"""All576 fixed coupled cut cases; only untimed correctness, no speed cohort."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,queue,shutil,subprocess,sys,threading,time,traceback
R=Path('D:/Codex/Kestrel');W=R/'work/perf-101';RAW=W/'native-coupled';FIX=W/'coupled-fixtures'
sys.path.insert(0,str(Path(__file__).parent));import archive_audit_099 as audit
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def events(b):return [json.loads(x) for x in b.splitlines() if x.strip()]
assert load(W/'build-proof.json')['complete'] and not RAW.exists() and not FIX.exists()
guards=sorted((R/'work').glob('guard-preoracle-101-*.json'));assert guards;guard=guards[-1];assert load(guard)['active_processes']==[]
RAW.mkdir();FIX.mkdir();shutil.copy2(guard,W/guard.name)
for p in [Path(__file__),Path(__file__).with_name('archive_audit_099.py'),Path(__file__).with_name('audit_coupling_101.py'),R/'work/check_processes_101.ps1']:shutil.copy2(p,W/p.name)
old=R/'work/perf-097/binaries/released016';assert (W/'binaries/released016').is_dir()
oldhash={p.relative_to(old).as_posix():sha(p) for p in old.rglob('*') if p.is_file()};assert {p.relative_to(W/'binaries/released016').as_posix():sha(p) for p in (W/'binaries/released016').rglob('*') if p.is_file()}==oldhash
assert load(W/'old-reader-proof.json')['sha256']==oldhash
specs=load(W/'coupled-policy-101.json')['cases'];assert len(specs)==576
freeze={p.relative_to(W).as_posix():sha(p) for folder in [W/'source',W/'binaries'] for p in folder.rglob('*') if p.is_file()}
for n in ['policy.json','declaration-proof.json','source-derivation.json','source-derivation-aux.json','build-proof.json','auxiliary-build-proof.json','auxiliary-declaration.json','coupled-policy-101.json','toolchain.json','old-reader-proof.json','run_coupling_101.py','archive_audit_099.py','audit_coupling_101.py','check_processes_101.ps1',guard.name]:freeze[n]=sha(W/n)
save(W/'recovery-freeze-v2.json',{'files':freeze,'utc':utc(),'no_performance_timers':True})
bins={n:W/'binaries'/n for n in ['normal','incremental','candidate','released016']};driver=W/'binaries/combined/coupled_probe_097.exe'
envbase={**os.environ,'TMP':str(W/'tmp'),'TEMP':str(W/'tmp')};assert not any(k.startswith(('KESTREL_FAULT_','KESTREL_RECLAIM_','KESTREL_ASYNC_','KESTREL_COUPLE_')) for k in envbase)
records=[];cases=[];controls=[];unstarted=list(specs)
def native_event(rec):
 with (RAW/'native-events.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec)+'\n')
def journal_run(argv,expected=0):
 idx=len(records);stem=RAW/f'command-{idx:05d}';argv=list(map(str,argv))
 rec={'index':idx,'argv':argv,'started_utc':utc(),'stdout':stem.with_suffix('.stdout').relative_to(W).as_posix(),'stderr':stem.with_suffix('.stderr').relative_to(W).as_posix()};records.append(rec);native_event(rec)
 try:r=subprocess.run(argv,env=envbase,capture_output=True,timeout=120)
 except subprocess.TimeoutExpired as e:
  stem.with_suffix('.stdout').write_bytes(e.stdout or b'');stem.with_suffix('.stderr').write_bytes(e.stderr or b'');rec.update(timeout=True,completed_utc=utc());native_event(rec);raise
 stem.with_suffix('.stdout').write_bytes(r.stdout);stem.with_suffix('.stderr').write_bytes(r.stderr)
 rec.update(returncode=r.returncode,completed_utc=utc(),stdout_sha256=sha(stem.with_suffix('.stdout')),stderr_sha256=sha(stem.with_suffix('.stderr')));native_event(rec)
 assert r.returncode==expected,(argv,r.returncode,r.stdout[-500:],r.stderr[-500:]);return r,idx
def owner(directory):
 result=[]
 for n in bins:
  r,idx=journal_run([bins[n]/'kestrel.exe','--archive',directory,'--sql','SELECT COUNT(*) FROM events'],1);assert b'lock' in r.stderr.lower();result.append(idx)
 return result
def cold(directory,groups,history):
 r,idx=journal_run([driver,directory,'verify',history,groups]);assert events(r.stdout)[-1]['event']=='verified';indices=[idx]
 for n in bins:
  r,idx=journal_run([bins[n]/'kestrel.exe','--archive',directory,'--sql','SELECT COUNT(*), SUM(value) FROM events']);rows=groups*100
  assert json.loads(r.stdout)['result']['rows']==[[rows,rows*(rows-1)]];indices.append(idx)
 return indices
def control(case,event,**kw):
 rec={'index':len(controls),'case':case,'event':event,'utc':utc(),**kw};controls.append(rec)
 with (RAW/'control-events.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec)+'\n')
 return rec['index']
def write_gate(case,p,b):
 assert not p.exists();p.write_bytes(b);return control(case,'gate_write',path=p.relative_to(W).as_posix(),hex=b.hex(),sha256=sha(p))
def wait_file(p,process,accept):
 deadline=time.monotonic()+30;pending=[]
 while True:
  assert process.poll() is None and time.monotonic()<deadline,(p,process.poll(),pending)
  try:data=p.read_bytes()
  except (FileNotFoundError,PermissionError):data=None
  if data is not None:
   try:complete=accept(data)
   except (ValueError,UnicodeError):complete=False
   if complete:return data
   if data.hex() not in pending:
    pending.append(data.hex());control(spec['index'],'incomplete_gate_read',path=p.relative_to(W).as_posix(),hex=data.hex())
  time.sleep(.005)
def protected(directory):
 gen,head,chain,_=audit.metadata(directory)
 names=[f'catalog-{g:020}.ks2' for g in chain]+head['segments'];return gen,{n:sha(directory/n) for n in names}
class Owned:
 def __init__(self,argv,env,case):
  idx=len(records);stem=RAW/f'command-{idx:05d}';argv=list(map(str,argv));self.queue=queue.Queue();self.events=[];self.case=case
  self.err=stem.with_suffix('.stderr').open('wb');self.out=stem.with_suffix('.stdout');self.stdin_path=stem.with_suffix('.stdin');self.stdin=self.stdin_path.open('wb')
  self.p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,env=env,creationflags=0x08000000)
  self.rec={'index':idx,'argv':argv,'pid':self.p.pid,'owned_Popen_process_handle':True,'started_utc':utc(),'stdout':self.out.relative_to(W).as_posix(),'stderr':stem.with_suffix('.stderr').relative_to(W).as_posix(),'stdin':self.stdin_path.relative_to(W).as_posix(),'fault_environment':{k:v for k,v in env.items() if k.startswith(('KESTREL_ASYNC_','KESTREL_COUPLE_'))}}
  records.append(self.rec);native_event(self.rec)
  def read():
   with self.out.open('wb') as f:
    for line in iter(self.p.stdout.readline,b''):
     f.write(line);f.flush()
     try:e=json.loads(line);self.events.append(e);self.queue.put(e)
     except BaseException as e:self.queue.put(e)
   self.queue.put(EOFError('owned Native stdout closed'))
  self.reader=threading.Thread(target=read);self.reader.start()
 def wait(self,event):
  deadline=time.monotonic()+30
  while True:
   e=self.queue.get(timeout=max(.001,deadline-time.monotonic()))
   if isinstance(e,BaseException):raise e
   if e['event']==event:return e
 def send(self,text):
  b=(text+'\n').encode();self.stdin.write(b);self.stdin.flush();control(self.case,'stdin_write',native_command=self.rec['index'],hex=b.hex())
  self.p.stdin.write(b);self.p.stdin.flush()
 def finish(self,expected):
  try:code=self.p.wait(timeout=45)
  except subprocess.TimeoutExpired:self.p.kill();self.p.wait(timeout=10);self.rec['owned_timeout_termination']=True;raise
  finally:
   self.reader.join(timeout=5);assert not self.reader.is_alive();self.p.stdout.close();self.p.stdin.close();self.err.close();self.stdin.close()
   self.rec.update(returncode=self.p.returncode,completed_utc=utc(),stdout_sha256=sha(self.out),stderr_sha256=sha(W/self.rec['stderr']),stdin_sha256=sha(self.stdin_path));native_event(self.rec)
  assert code==expected,(self.rec,(W/self.rec['stderr']).read_bytes()[-500:])
 def abort(self):
  if self.p.poll() is None:self.p.kill();self.p.wait(timeout=10);self.rec['owned_hard_error_termination']=True
  self.reader.join(timeout=5);self.p.stdout.close();self.p.stdin.close();self.err.close();self.stdin.close();self.rec.update(returncode=self.p.returncode,completed_utc=utc());native_event(self.rec)
try:
 for spec in specs:
  i=spec['index'];d=FIX/f'case-{i:03d}';d.mkdir();store=d/'archive';worker=d/'worker';publisher=d/'publisher';arm=d/'arm';log=d/'worker.jsonl'
  env={**envbase,'KESTREL_ASYNC_POINT':spec['worker_point'],'KESTREL_ASYNC_KIND':spec['target'],'KESTREL_ASYNC_ORDINAL':str(spec['ordinal']),'KESTREL_ASYNC_MODE':'pause-'+spec['mode'],'KESTREL_ASYNC_LOG':str(log),'KESTREL_ASYNC_MARKER':str(worker),'KESTREL_COUPLE_POINT':spec['publication_point'],'KESTREL_COUPLE_MARKER':str(publisher),'KESTREL_COUPLE_ARM':str(arm)}
  p=Owned([driver,store,'couple',spec['history'],spec['target'],spec['operation']],env,i);native=p.rec['index'];owners=[]
  try:
   p.wait('scheduled');actual=wait_file(worker.with_suffix('.entered'),p.p,lambda b: len(b)==32 and (b.startswith(b'catalog-') or b.startswith(b'segment-')) and b.endswith(b'.ks2')).decode();control(i,'worker_entered',name=actual,native_command=native,existing_files=sorted(x.name for x in store.iterdir() if x.is_file()))
   hook=events(log.read_bytes());assert hook[-1]=={'phase':spec['worker_point'],'kind':spec['target'],'name':actual,'ordinal':spec['ordinal']}
   (d/'worker-cut.jsonl').write_bytes(log.read_bytes())
   assert (store/actual).exists()==(spec['worker_point']=='before-delete')
   owners+=owner(store);write_gate(i,arm,b'arm only after seed and scheduled worker');p.send('publish')
   pub=json.loads(wait_file(publisher.with_suffix('.entered'),p.p,lambda b: json.loads(b)=={'point':spec['publication_point'],'pid':p.p.pid}));assert pub=={'point':spec['publication_point'],'pid':p.p.pid};control(i,'publisher_entered',native_command=native,**pub)
   assert not publisher.with_suffix('.release').exists() and not worker.with_suffix('.release').exists()
   before_generation,before_protected=protected(store);expected_gen=66 if spec['publication_point']=='catalog_published' else 65;assert before_generation==expected_gen
   control(i,'protected_before_worker_release',generation=before_generation,files=before_protected)
   write_gate(i,worker.with_suffix('.release'),b'worker failure during paused real publication')
   if spec['mode']=='error':
    assert wait_file(worker.with_suffix('.observed'),p.p,lambda b: b==b'worker failure callback observed')==b'worker failure callback observed';control(i,'worker_error_observed',native_command=native)
    assert p.p.poll() is None and not publisher.with_suffix('.release').exists()
    after_generation,after_protected=protected(store);assert (after_generation,after_protected)==(before_generation,before_protected)
    owners+=owner(store);write_gate(i,publisher.with_suffix('.release'),b'publication continues after observed worker error');p.finish(0)
   else:
    p.finish(86);assert not publisher.with_suffix('.release').exists();control(i,'worker_exit_observed',native_command=native)
    after_generation,after_protected=protected(store);assert (after_generation,after_protected)==(before_generation,before_protected)
   control(i,'protected_after_worker_failure',generation=after_generation,files=after_protected)
   assert worker.with_suffix('.triggered').read_bytes()==spec['mode'].encode()
  except BaseException:p.abort();raise
  stream=p.events;acks=[e for e in stream if e['event']=='ack'];ack_groups=65 if spec['mode']=='error' and spec['operation']=='append' else 64
  assert [e['group'] for e in acks]==list(range(ack_groups));assert all(e['generation']==e['group']+1+int(e['group']>=64) and e['rows']==100 for e in acks)
  groups=65 if spec['operation']=='append' and (spec['mode']=='error' or spec['publication_point']=='catalog_published') else 64
  generation=66 if spec['mode']=='error' or spec['publication_point']=='catalog_published' else 65
  if spec['mode']=='error':
   drained=next(e['stats'] for e in stream if e['event']=='first_drained');assert drained['failures']==1 and drained['inflight']==0 and drained['deleted']==spec['ordinal']-int(spec['worker_point']=='before-delete')
   end=next(e['stats'] for e in stream if e['event']=='completed');assert end['failures']==1 and end['inflight']==0 and end['max_inflight']<=2
  else:assert not any(e['event'] in ['publication_completed','completed'] for e in stream)
  rows=[[j,2*j,j%97] for j in range(groups*100)]
  receipts={f'seed:{g}':(rows[g*100:(g+1)*100],g+1+int(g>=64)) for g in range(groups)} if spec['history']=='named' else {}
  decoded=audit.check(store,rows,receipts);assert decoded['head']==generation
  assert (store/'segment-00000000000000000999.ks2').read_bytes()==b'097 untouched crash orphan';assert (store/'catalog-00000000000000000998.pending').read_bytes()==b'097 untouched pending'
  inventory={x.name:sha(x) for x in store.iterdir() if x.is_file()};reads=cold(store,groups,spec['history']);assert {x.name:sha(x) for x in store.iterdir() if x.is_file()}==inventory
  cases.append({'spec':spec,'directory':store.relative_to(W).as_posix(),'native_command':native,'acks':acks,'unacknowledged_committed_groups':list(range(ack_groups,groups)),'expected_groups':groups,'expected_generation':generation,'worker_log':log.relative_to(W).as_posix(),'worker_log_sha256':sha(log),'actual_worker_name':actual,'publisher_marker':publisher.with_suffix('.entered').relative_to(W).as_posix(),'owner_rejection_commands':owners,'cold_reader_commands':reads,'decode':decoded,'closed_inventory':inventory,'protected_files_unchanged_during_fault':before_protected})
  unstarted.remove(spec);save(d/'case-result.json',cases[-1]);save(W/'progress-v2.json',{'completed_case_count':len(cases),'native_commands':len(records),'unstarted_count':len(unstarted)})
  print(json.dumps({'case':i,'passed':True,'groups':groups,'acks':len(acks),'mode':spec['mode'],'publication_point':spec['publication_point']}),flush=True)
 save(W/'native-run-order-v2.json',records);save(W/'control-run-order-v2.json',controls);save(W/'case-results-v2.json',cases)
 for n,h in freeze.items():assert sha(W/n)==h,n
 save(W/'recovery-proof-v2.json',{'complete':True,'fixed_cases':576,'new_ack_batches':sum(len(c['acks']) for c in cases),'unacknowledged_committed_groups':sum(len(c['unacknowledged_committed_groups']) for c in cases),'native_commands':len(records),'owner_rejections':sum(len(c['owner_rejection_commands']) for c in cases),'full_crc_reference_bytes':sum(c['decode']['full_block_crc_bytes'] for c in cases),'all_frozen_inputs_exact':True,'no_performance_timers':True,'physical_power_loss_not_qualified':True})
 print(json.dumps(load(W/'recovery-proof-v2.json')),flush=True)
except BaseException:
 save(W/'native-run-order-v2.json',records);save(W/'control-run-order-v2.json',controls);save(W/'case-results-v2.json',cases)
 save(W/'recovery-failure-v2.json',{'error':traceback.format_exc(),'completed_cases':cases,'unstarted':unstarted,'native_commands':len(records),'no_performance_timers':True});raise
