"""Fixed 107-case recovery run with full owned Native, bridge and wire journals."""
from pathlib import Path
from datetime import datetime,timezone
import contextlib,hashlib,importlib,io,itertools,json,os,runpy,shutil,struct,subprocess,sys,time,traceback
ROOT=Path('D:/Codex/Kestrel');W=ROOT/'work/perf-094';S=W/'source';H=W/'harness';RAW=W/'native-raw'
sys.path.insert(0,str(Path(__file__).parent))
import archive_audit_094 as audit
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def inventory(p):return {q.name:sha(q) for q in p.iterdir() if q.is_file()}
def utc():return datetime.now(timezone.utc).isoformat()
assert load(W/'build-proof.json')['complete'] and not RAW.exists()
assert load(ROOT/'work/guard-prefault-094.json')['active_processes']==[]
RAW.mkdir();H.mkdir();(W/'maintenance-fixtures').mkdir();(W/'maintenance-seeds').mkdir()
for p in [Path(__file__),Path(__file__).with_name('archive_audit_094.py'),Path(__file__).with_name('audit_recovery_094.py'),ROOT/'work/check_processes_094.ps1',ROOT/'work/continue_recovery_094.ps1',ROOT/'work/serial-worker-094-identity.json',ROOT/'work/guard-prefault-094.json']:shutil.copy2(p,W/p.name)
derivations=[]
for name in ['stress_compare.py','publication_faults.py','live_retry_faults.py']:
 p=ROOT/'outputs/kestrel-sql/benchmarks'/name;b=p.read_bytes();(H/(name+'.original')).write_bytes(b);edited=b
 if name=='publication_faults.py':
  old=b"work = ROOT.parent.parent/'work'/f'catalog-faults-{time.time_ns()}'";new=b"work = ROOT/'publication-fixtures'";assert b.count(old)==1;edited=b.replace(old,new)
 elif name=='live_retry_faults.py':
  old=b"work = ROOT.parent.parent/'work'/f'live-retry-faults-{time.time_ns()}'";new=b"work = ROOT/'live-retry-fixtures'";assert b.count(old)==1;edited=b.replace(old,new)
 (H/name).write_bytes(edited);derivations.append({'file':name,'original_sha256':sha(p),'relocated_sha256':sha(H/name),'only_work_path_changed':edited!=b,'all_case_logic_unchanged':True})
p=ROOT/'work/perf-093/oracles_093.py';b=p.read_bytes();(H/'oracles_093.py.original').write_bytes(b)
assert b.count(b"W=ROOT/'work/perf-093'")==1
(H/'oracles_094.py').write_bytes(b.replace(b"W=ROOT/'work/perf-093'",b"W=ROOT/'work/perf-094'"))
derivations.append({'file':'oracles_094.py','original_sha256':sha(p),'relocated_sha256':sha(H/'oracles_094.py'),'only_work_path_changed':True})
save(W/'harness-derivation.json',derivations)
specs=[]
for history in ['anonymous','named']:
 for kind in ['catalog','retired']:
  for event,ordinal in [('before',1),('after',1),('after',20)]:
   for mode in ['exit','io_error']:
    for pin in (['held','released'] if kind=='catalog' else ['released']):
     specs.append({'index':len(specs),'history':history,'kind':kind,'event':event,'ordinal':ordinal,'mode':mode,'pin':pin})
assert len(specs)==36
save(W/'maintenance-run-declaration.json',specs)
freeze={p.relative_to(W).as_posix():sha(p) for folder in [S,W/'binaries',H] for p in folder.rglob('*') if p.is_file()}
for n in ['policy.json','declaration-proof.json','source-derivation.json','build-proof.json','maintenance-run-declaration.json','run_recovery_094.py','archive_audit_094.py','audit_recovery_094.py','check_processes_094.ps1','continue_recovery_094.ps1','serial-worker-094-identity.json','guard-prefault-094.json']:freeze[n]=sha(W/n)
save(W/'recovery-freeze.json',{'before_first_recovery_native':utc(),'files':freeze,'no_performance_timing':True})
records=[];bridge_records=[];wire_records=[];maintenance=[];owners=[];seed_records=[];unstarted=list(specs)
orig_run=subprocess.run;orig_popen=subprocess.Popen
def text_semantics(b,encoding='utf-8',errors='strict'):
 return io.TextIOWrapper(io.BytesIO(b),encoding=encoding,errors=errors,newline=None).read()
def logged_run(argv,*args,**kwargs):
 argv=list(map(str,argv));idx=len(records);stem=RAW/f'command-{idx:04d}';start=utc()
 kw=dict(kwargs);want_text=bool(kw.pop('text',False) or kw.pop('universal_newlines',False));encoding=kw.pop('encoding',None);errors=kw.pop('errors',None)
 assert not args and kw.get('capture_output') and not kw.get('input'),('unhandled Native logging call',argv)
 env=kw.get('env',os.environ);rec={'index':idx,'argv':argv,'started_utc':start,'fault_environment':{n:str(v) for n,v in env.items() if n.startswith('KESTREL_FAULT_') or n.startswith('KESTREL_RECLAIM_') or n=='KESTREL_LIVE_PAUSE'},'stdout':stem.with_suffix('.stdout').relative_to(W).as_posix(),'stderr':stem.with_suffix('.stderr').relative_to(W).as_posix()}
 records.append(rec);save(W/'native-run-order.json',records)
 try:r=orig_run(argv,**kw)
 except subprocess.TimeoutExpired as e:
  stem.with_suffix('.stdout').write_bytes(e.stdout or b'');stem.with_suffix('.stderr').write_bytes(e.stderr or b'');rec.update(timeout=True,completed_utc=utc());save(W/'native-run-order.json',records);raise
 stem.with_suffix('.stdout').write_bytes(r.stdout);stem.with_suffix('.stderr').write_bytes(r.stderr)
 rec.update(returncode=r.returncode,completed_utc=utc(),stdout_sha256=sha(stem.with_suffix('.stdout')),stderr_sha256=sha(stem.with_suffix('.stderr')));save(W/'native-run-order.json',records)
 if want_text or encoding:r.stdout=text_semantics(r.stdout,encoding or 'utf-8',errors or 'strict');r.stderr=text_semantics(r.stderr,encoding or 'utf-8',errors or 'strict')
 return r
subprocess.run=logged_run
sys.path.insert(0,str(H));import stress_compare as sc
original_call=sc.KestrelConnection.call
def wire_call(self,message):
 rec={'index':len(wire_records),'request':message}
 try:rec['result']=original_call(self,message);return rec['result']
 except BaseException as e:rec['error']=repr(e);raise
 finally:
  wire_records.append(rec)
  with (RAW/'wire.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(rec,separators=(',',':'))+'\n')
sc.KestrelConnection.call=wire_call
def bridge_start(self,rows):
 idx=len(bridge_records);stem=RAW/f'bridge-{idx:03d}';error=(self.directory/'bridge.log').open('ab');self._owned_error=error
 argv=[str(self.binary),str(self.directory/'archive'),str(rows),*self.bridge_args]
 self.process=orig_popen(argv,stdout=subprocess.PIPE,stderr=error,creationflags=0x08000000 if os.name=='nt' else 0)
 rec={'index':idx,'argv':argv,'pid':self.process.pid,'started_utc':utc(),'startup_stdout':stem.with_suffix('.stdout').relative_to(W).as_posix()};bridge_records.append(rec);save(W/'bridge-run-order.json',bridge_records)
 # A bounded owned startup read; preserve the actual bytes returned by the Native process.
 import concurrent.futures
 pool=concurrent.futures.ThreadPoolExecutor(max_workers=1)
 future=pool.submit(self.process.stdout.readline)
 try:line=future.result(timeout=15)
 except BaseException:
  self.process.kill();self.process.wait(timeout=10);pool.shutdown(wait=True);raise
 pool.shutdown(wait=True);stem.with_suffix('.stdout').write_bytes(line);info=json.loads(line)
 self.version=info['version'];self.bridge_info=info;host,port=info['address'].split(':');self.address=(host,int(port))
def bridge_finish(self):
 if self.process:
  self.process.terminate();self.process.wait(timeout=10)
  tail=self.process.stdout.read();self.process.stdout.close();self._owned_error.close()
  rec=next(r for r in reversed(bridge_records) if r['pid']==self.process.pid and 'completed_utc' not in r)
  with (W/rec['startup_stdout']).open('ab') as f:f.write(tail)
  rec.update(completed_utc=utc(),returncode=self.process.returncode);save(W/'bridge-run-order.json',bridge_records);self.process=None
def bridge_reopen(self):
 if self.process:bridge_finish(self);bridge_start(self,0)
sc.Engine.start_bridge=bridge_start;sc.Engine.finish=bridge_finish;sc.Engine.reopen=bridge_reopen
bins={n:W/'binaries'/n for n in ['baseline','candidate','fault']};bins['released016']=ROOT/'work/perf-090/binaries/released016'
def run(name,argv,success=True,env=None,code=None):
 r=logged_run(argv,capture_output=True,timeout=90,**({'env':env} if env else {}))
 assert (r.returncode==0)==success if code is None else r.returncode==code,(name,r.returncode,r.stdout[-500:],r.stderr[-500:])
 return r
def lines(r):return [json.loads(x) for x in r.stdout.splitlines() if x.strip()]
def invoke(module,argv,name):
 before=list(sys.argv);sys.argv=[module,*list(map(str,argv))]
 try:
  with (RAW/(name+'.stdout')).open('w',encoding='utf-8',newline='\n') as out,(RAW/(name+'.stderr')).open('w',encoding='utf-8',newline='\n') as err,contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):importlib.import_module(module).main()
 finally:sys.argv=before
def save_progress():save(W/'recovery-progress.json',{'maintenance':maintenance,'ownership':owners,'seeds':seed_records,'unstarted_maintenance':unstarted,'native_commands':len(records),'bridge_launches':len(bridge_records)})
try:
 # Fresh fixed byte/wire/SQLite/old-reader controls, unchanged oracle logic.
 with (RAW/'oracles.stdout').open('w',encoding='utf-8') as out,(RAW/'oracles.stderr').open('w',encoding='utf-8') as err,contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):runpy.run_path(str(H/'oracles_094.py'))
 print(json.dumps({'phase':'byte-wire-oracles','passed':True}),flush=True)
 for history in ['anonymous','named']:
  inv={}
  for variant in ['baseline','candidate']:
   p=W/'maintenance-seeds'/f'{history}-{variant}';r=run('seed',[bins[variant]/'reclaim_fault_probe_094.exe',p,'seed',history]);events=lines(r)
   acks=[e for e in events if e['event']=='ack'];assert len(acks)==64 and events[-1]['event']=='seed_complete'
   assert all(e['group']==i and e['generation']==i+1 and e['rows']==100 for i,e in enumerate(acks))
   rows,receipt=audit.maintenance_reference(history);a=audit.check(p,rows,receipt);inv[variant]=inventory(p)
   seed_records.append({'history':history,'variant':variant,'path':p.relative_to(W).as_posix(),'acks':acks,'audit':a,'inventory':inv[variant]});save_progress()
  assert inv['baseline']==inv['candidate']
 for spec in specs:
  case=W/'maintenance-fixtures'/f"case-{spec['index']:03d}";case.mkdir();directory=case/'archive';source=W/'maintenance-seeds'/f"{spec['history']}-candidate";shutil.copytree(source,directory)
  log=case/'deletions.jsonl';release=case/'fault-release';env={**os.environ,'KESTREL_RECLAIM_LOG':str(log),'KESTREL_RECLAIM_KIND':spec['kind'],'KESTREL_RECLAIM_EVENT':spec['event'],'KESTREL_RECLAIM_ORDINAL':str(spec['ordinal']),'KESTREL_RECLAIM_MODE':spec['mode'],'KESTREL_RECLAIM_RELEASE':str(release)}
  before=len(records);r=run('maintenance-fault',[bins['fault']/ 'reclaim_fault_probe_094.exe',directory,'fault',spec['history'],spec['pin']],success=spec['mode']=='io_error',env=env,code=86 if spec['mode']=='exit' else 0)
  events=lines(r);assert events[0]['event']=='before_cleanup' and events[0]['passed']
  deletes=[json.loads(x) for x in log.read_text().splitlines()];boundary=next(i for i,e in enumerate(deletes) if e['kind']==spec['kind'] and e['event']==spec['event'] and e['ordinal']==spec['ordinal'])
  if spec['mode']=='exit':assert boundary==len(deletes)-1
  else:assert release.read_bytes()==b'retry with test injection released' and events[-1]['event']=='maintenance_error_recovered' and events[-1]['healthy']
  selected=deletes[:boundary+1];successful=[e for e in selected if e['event']=='after' and e['kind']==spec['kind']]
  assert len(successful)==(0 if spec['event']=='before' else spec['ordinal'])
  if spec['pin']=='held':assert not any(e['kind']=='retired' for e in selected)
  rows,receipt=audit.maintenance_reference(spec['history']);decoded=audit.check(directory,rows,receipt)
  protected={f'catalog-{n:020d}.ks2' for n in decoded['chain']}|set(decoded['segments'])|{'segment-00000000000000000999.ks2','catalog-00000000000000000998.pending'}
  after=[e for e in deletes if e['event']=='after'];assert len({e['name'] for e in after})==len(after)
  assert all(e['name'] not in protected for e in deletes)
  assert all(e['kind']=='catalog' or (e['name'].startswith('segment-') and 1<=int(e['name'][8:28])<=32) for e in deletes)
  inv=inventory(directory);old=inventory(source);assert set(old)-set(inv)=={e['name'] for e in after}
  for name in ['segment-00000000000000000999.ks2','catalog-00000000000000000998.pending']:assert inv[name]==old[name]
  before_cold=inv.copy()
  for variant in ['baseline','candidate']:
   v=run('cold-retry',[bins[variant]/'reclaim_fault_probe_094.exe',directory,'verify',spec['history']]);assert lines(v)[-1]['passed']
  for variant in ['baseline','candidate','released016']:
   v=run('cross-reader',[bins[variant]/'kestrel.exe','--archive',directory,'--sql','SELECT COUNT(*), SUM(value) FROM events']);assert json.loads(v.stdout)['result']['rows']==[[6400,6400*6399]]
  assert inventory(directory)==before_cold,'cold open must preserve remembered-loss crash orphans'
  rec={**spec,'path':case.relative_to(W).as_posix(),'native_command_start':before,'fault_returncode':r.returncode,'reached_boundary':deletes[boundary],'boundary_index':boundary,'successful_selected_kind_before_interrupt':len(successful),'successful_deletions':len(after),'protected_names':sorted(protected),'inventory':inv,'audit':decoded,'cold_retries_cross_reads_orphans_exact':True,'fault_output_events':events}
  maintenance.append(rec);unstarted.pop(0);save_progress();print(json.dumps({'maintenance_case':spec['index'],'passed':True}),flush=True)
 # Snapshot must retain process-exclusive ownership after the Archive value drops.
 for history in ['anonymous','named']:
  case=W/'maintenance-fixtures'/f'ownership-{history}';case.mkdir();directory=case/'archive';shutil.copytree(W/'maintenance-seeds'/f'{history}-candidate',directory)
  out=(case/'hold.stdout').open('wb');err=(case/'hold.stderr').open('wb');argv=[str(bins['candidate']/ 'reclaim_fault_probe_094.exe'),str(directory),'hold',history]
  p=orig_popen(argv,stdout=out,stderr=err,creationflags=0x08000000 if os.name=='nt' else 0);start=utc()
  try:
   deadline=time.monotonic()+15
   while not (case/'owner-entered').exists():assert p.poll() is None and time.monotonic()<deadline;time.sleep(.005)
   for variant in ['baseline','candidate','released016']:
    x=run('second-owner',[bins[variant]/'kestrel.exe','--archive',directory,'--sql','SELECT COUNT(*) FROM events'],success=False);assert b'lock' in x.stderr.lower()
   (case/'owner-release').write_bytes(b'release owned pin');assert p.wait(timeout=15)==0
  finally:
   if p.poll() is None:p.kill();p.wait(timeout=10)
   out.close();err.close()
  assert json.loads((case/'hold.stdout').read_bytes())['passed'];owners.append({'history':history,'argv':argv,'pid':p.pid,'started_utc':start,'completed_utc':utc(),'passed':True});save_progress()
 invoke('publication_faults',['--binary',bins['candidate']/ 'kestrel-stress.exe','--sql-binary',bins['candidate']/ 'kestrel.exe','--fault-driver',bins['fault']/ 'publication_fault_probe.exe','--output',W/'publication-proof.json','--expected-version','0.3.16'],'publication')
 print(json.dumps({'phase':'publication','cases':56,'passed':True}),flush=True)
 invoke('live_retry_faults',['--binary',bins['candidate']/ 'kestrel-stress.exe','--driver',bins['fault']/ 'live_retry_probe.exe','--output',W/'live-retry-proof.json','--expected-version','0.3.16','--process-exits'],'live-retry')
 print(json.dumps({'phase':'live-retry','cases':15,'passed':True}),flush=True)
 independent=[]
 pub=load(W/'publication-proof.json');assert len(pub['cut_points'])==56
 for rec in pub['cut_points']:
  directory=W/'publication-fixtures'/f"{rec['scenario']}-{rec['point']}-{rec['mode']}"/'archive';rows,receipts=audit.publication_reference(rec['scenario']);independent.append({'kind':'publication','path':directory.relative_to(W).as_posix(),'audit':audit.check(directory,rows,receipts)})
 for index,rec in enumerate(pub['corruption_cases']):
  directory=W/'publication-fixtures'/f'corruption-{index}'/'archive'
  try:audit.check(directory,*audit.publication_reference('compact_checkpoint' if rec['damage']=='excess_chain' else 'compact_delta'))
  except (AssertionError,KeyError,ValueError,struct.error):pass
  else:raise AssertionError(('corruption not independently rejected',index))
 live=load(W/'live-retry-proof.json');assert len(live['cases'])==15 and not live['failed_cases']
 for rec in live['cases']:
  directory=W/'live-retry-fixtures'/f"{rec['mode']}-{rec['point']}"/'archive';independent.append({'kind':'live','path':directory.relative_to(W).as_posix(),'audit':audit.check(directory,*audit.live_reference())})
 assert all(sha(W/name)==digest for name,digest in freeze.items())
 assert all('completed_utc' in b for b in bridge_records)
 save(W/'recovery-proof.json',{'complete':True,'fixed_fault_cases':len(maintenance)+len(pub['cut_points'])+len(live['cases']),'maintenance':maintenance,'ownership':owners,'seeds':seed_records,'additional_corruption_rejections':len(pub['corruption_cases']),'independent_publication_live_audits':independent,'native_commands':len(records),'owned_bridge_launches':len(bridge_records),'wire_requests':len(wire_records),'normal_hook_absence_verified':True,'no_timing_or_adoption':True,'093_remains_rejected':True,'unstarted':[]})
 print(json.dumps({'complete':True,'fixed_fault_cases':107,'corruptions':len(pub['corruption_cases']),'native_commands':len(records),'bridge_launches':len(bridge_records)}),flush=True)
except BaseException:
 save(W/'recovery-failure.json',{'complete':False,'error':traceback.format_exc(),'unstarted_maintenance':unstarted,'publication_started':(W/'publication-proof.json').exists(),'live_retry_started':(W/'live-retry-proof.json').exists(),'native_commands':len(records),'completed_maintenance':len(maintenance)})
 raise
finally:subprocess.run=orig_run
