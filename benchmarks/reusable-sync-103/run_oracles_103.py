"""Predeclared new untimed publication/source/corruption/legacy/byte controls."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,itertools,json,os,shutil,struct,subprocess,sys,traceback,zlib
R=Path('D:/Codex/Kestrel');W=R/'work/perf-103';RAW=W/'native-oracles';FIX=W/'oracle-fixtures'
sys.path.insert(0,str(Path(__file__).parent));import audit_oracles_103 as oracle
import archive_audit_099 as archive
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return oracle.sha(p)
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
def load(p):return oracle.load(p)
assert load(W/'recovery-proof-v2.json')['complete'] and load(W/'oracle-artifacts-proof.json')['complete']
assert not RAW.exists() and not FIX.exists()
guards=sorted((R/'work').glob('guard-preaudit-103-*.json'));assert guards;guard=guards[-1]
assert load(guard)['active_processes']==[] and load(guard)['verified_idle_terminal_reset']
points=load(W/'policy.json')['publication_cuts'];assert len(points)==13
pubspec=[{'count':n,'action':a,'point':p,'mode':m} for n,a,p,m in itertools.product([3,32],['append','compact'],points,['exit','io_error'])]
srcspec=[{'point':p,'mode':m} for p,m in itertools.product(points,['exit','io_error'])]
corruptspec=[{'damage':'root_truncation','length':n} for n in [*range(17),20,'half','last']]+[{'damage':'excess_chain','length':None},{'damage':'duplicate_key','length':None}]
assert len(pubspec)==104 and len(srcspec)==26 and len(corruptspec)==22
save(W/'oracle-policy-103.json',{'declared_utc':utc(),'before_first_oracle_native':True,'publication':pubspec,'source':srcspec,'corruption':corruptspec,'legacy':['KSQLCAT2','KSQLCAT3'],'byte_fixtures':list(itertools.product(['normal','candidate'],[False,True])),'native_commands':1065,'no_performance_cohort':True,'injected_IO_and_live_process_exit_not_physical_power_loss_or_actual_disk_full':True})
RAW.mkdir();FIX.mkdir();shutil.copy2(guard,W/guard.name)
for p in [Path(__file__),R/'work/audit_oracles_103.py']:shutil.copy2(p,W/p.name)
freeze={p.relative_to(W).as_posix():sha(p) for folder in [W/'source-v3',W/'binaries'] for p in folder.rglob('*') if p.is_file()}
for n in ['policy.json','declaration-proof.json','build-proof.json','oracle-artifacts-proof.json','source-derivation-v3.json','oracle-artifacts-declaration.json','oracle-policy-103.json','run_oracles_103.py','audit_oracles_103.py','archive_audit_099.py',guard.name]:freeze[n]=sha(W/n)
save(W/'oracle-freeze-103.json',{'files':freeze,'utc':utc(),'no_performance_timers':True})
envbase={**os.environ,'TMP':str(W/'tmp'),'TEMP':str(W/'tmp')}
assert not any(k.startswith(('KESTREL_FAULT_','KESTREL_RECLAIM_','KESTREL_ASYNC_','KESTREL_COUPLE_')) for k in envbase)
bins={n:W/'binaries'/n for n in ['normal','existing101','incremental','candidate','released016']}
records=[];seeds=[];pubs=[];sources=[];corrupt=[];legacies=[];byte_cases=[];current=None
def event(r):
 with (RAW/'native-events.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(r)+'\n')
def run(argv,expected=0,fault=None):
 i=len(records);stem=RAW/f'command-{i:04d}';argv=list(map(str,argv));env=envbase| (fault or {})
 r={'index':i,'argv':argv,'started_utc':utc(),'stdout':stem.with_suffix('.stdout').relative_to(W).as_posix(),'stderr':stem.with_suffix('.stderr').relative_to(W).as_posix(),'fault_environment':fault or {}};records.append(r);event(r)
 try:done=subprocess.run(argv,env=env,capture_output=True,timeout=120,creationflags=0x08000000)
 except subprocess.TimeoutExpired as e:
  stem.with_suffix('.stdout').write_bytes(e.stdout or b'');stem.with_suffix('.stderr').write_bytes(e.stderr or b'');r.update(timeout=True,completed_utc=utc());event(r);raise
 stem.with_suffix('.stdout').write_bytes(done.stdout);stem.with_suffix('.stderr').write_bytes(done.stderr)
 r.update(returncode=done.returncode,completed_utc=utc(),stdout_sha256=sha(stem.with_suffix('.stdout')),stderr_sha256=sha(stem.with_suffix('.stderr')));event(r)
 assert done.returncode==expected,(argv,done.returncode,done.stdout[-600:],done.stderr[-1000:]);return i,done
def cold(d,rows,width=3,rejected=False):
 before=oracle.inventory(d);indices=[]
 for label in bins:
  cmd=[bins[label]/'kestrel.exe','--archive',d,'--columns','ts,value' if width==2 else 'ts,value,device','--sql','SELECT COUNT(*) FROM events' if rejected else 'SELECT COUNT(*), SUM(value) FROM events']
  i,done=run(cmd,1 if rejected else 0);indices.append(i)
  if not rejected:assert json.loads(done.stdout)['result']['rows']==[[len(rows),sum(x[1] for x in rows)]]
 assert oracle.inventory(d)==before;return indices
def decode(d,model):return oracle.brief(archive.check(d,*model))
def write_catalog(p,body,magic=b'KSQLCAT4'):
 data=body.encode() if isinstance(body,str) else json.dumps(body,separators=(',',':')).encode();p.write_bytes(magic+struct.pack('<II',len(data),zlib.crc32(data))+data)
def checkpoint():
 save(W/'oracle-native-order.json',records);save(W/'oracle-seed-results.json',seeds);save(W/'oracle-publication-results.json',pubs);save(W/'oracle-source-results.json',sources);save(W/'oracle-corruption-results.json',corrupt);save(W/'oracle-legacy-results.json',legacies);save(W/'oracle-byte-results.json',byte_cases)
 save(W/'oracle-progress.json',{'publication_cases':len(pubs),'source_cases':len(sources),'corruptions':len(corrupt),'legacy_formats':len(legacies),'byte_cases':len(byte_cases),'native_commands':len(records),'current':current})
try:
 for variant,n in itertools.product(['normal','candidate'],[3,32]):
  current={'seed':variant,'count':n};d=FIX/f'seed-{variant}-{n}';i,_=run([W/'binaries'/variant/'publication_oracle_101.exe',d,'seed',n]);decoded=decode(d,oracle.seed(n))
  seeds.append({'variant':variant,'count':n,'directory':d.relative_to(W).as_posix(),'command':i,'decode':decoded,'inventory':oracle.inventory(d)});checkpoint()
 for n in [3,32]:assert next(s['inventory'] for s in seeds if s['variant']=='normal' and s['count']==n)==next(s['inventory'] for s in seeds if s['variant']=='candidate' and s['count']==n)
 for index,spec in enumerate(pubspec):
  current={'publication_index':index,'spec':spec};n=spec['count'];a=spec['action'];published=spec['point']=='catalog_published';case=FIX/f'publication-{index:03d}';case.mkdir();d=case/'archive';shutil.copytree(FIX/f'seed-candidate-{n}',d)
  fault={'KESTREL_FAULT_POINT':spec['point'],'KESTREL_FAULT_MODE':spec['mode']};i,done=run([W/'binaries/combined/publication_fault_probe.exe',d,a],86 if spec['mode']=='exit' else 87,fault)
  if spec['mode']=='io_error':assert b'poisoned writer; old snapshot readable' in done.stderr
  before=decode(d,oracle.pub_model(n,a,published));assert before['head']==n+int(published);pre=case/'before-recovery';shutil.copytree(d,pre)
  j,_=run([W/'binaries/candidate/publication_oracle_101.exe',d,'recover',n,'published' if published else 'unpublished',a]);rows,receipts=oracle.pub_model(n,a,published,True);after=decode(d,(rows,receipts));queries=cold(d,rows)
  pubs.append({'spec':spec,'directory':d.relative_to(W).as_posix(),'before_directory':pre.relative_to(W).as_posix(),'failure_command':i,'recover_command':j,'cold_commands':queries,'before':before,'before_inventory':oracle.inventory(pre),'after':after,'closed_inventory':oracle.inventory(d)});checkpoint()
  print(json.dumps({'publication_case':index,'passed':True}),flush=True)
 d=FIX/'source-seed';i,_=run([W/'binaries/combined/source_fault_probe.exe',d,'init']);source_seed={'directory':d.relative_to(W).as_posix(),'command':i,'decode':decode(d,oracle.source_model(False)),'inventory':oracle.inventory(d)};save(W/'oracle-source-seed.json',source_seed)
 for index,spec in enumerate(srcspec):
  current={'source_index':index,'spec':spec};published=spec['point']=='catalog_published';case=FIX/f'source-{index:02d}';case.mkdir();d=case/'archive';shutil.copytree(FIX/'source-seed',d)
  fault={'KESTREL_FAULT_POINT':spec['point'],'KESTREL_FAULT_MODE':spec['mode']};i,_=run([W/'binaries/combined/source_fault_probe.exe',d,'fail'],86 if spec['mode']=='exit' else 0,fault)
  before=decode(d,oracle.source_model(published));pre=case/'before-recovery';shutil.copytree(d,pre);j,_=run([W/'binaries/combined/source_fault_probe.exe',d,'recover']);rows,receipts=oracle.source_model(published,True);after=decode(d,(rows,receipts));queries=cold(d,rows)
  sources.append({'spec':spec,'directory':d.relative_to(W).as_posix(),'before_directory':pre.relative_to(W).as_posix(),'failure_command':i,'recover_command':j,'cold_commands':queries,'before':before,'before_inventory':oracle.inventory(pre),'after':after,'closed_inventory':oracle.inventory(d)});checkpoint()
  print(json.dumps({'source_case':index,'passed':True}),flush=True)
 original=FIX/'seed-candidate-3/catalog-00000000000000000001.ks2';data=original.read_bytes()
 for index,spec in enumerate(corruptspec):
  current={'corruption_index':index,'spec':spec};n=32 if spec['damage']=='excess_chain' else 3;d=FIX/f'corruption-{index:02d}';shutil.copytree(FIX/f'seed-candidate-{n}',d)
  if spec['damage']=='root_truncation':
   size=len(data)//2 if spec['length']=='half' else len(data)-1 if spec['length']=='last' else spec['length'];(d/original.name).write_bytes(data[:size])
  elif spec['damage']=='excess_chain':
   body=json.loads((d/'catalog-00000000000000000032.ks2').read_bytes()[16:]);body.update(generation=33,receipt_base=32,batches={'excess':{'digest':[0]*32,'rows':1,'generation':33}});write_catalog(d/'catalog-00000000000000000033.ks2',body)
  else:
   p=d/'catalog-00000000000000000003.ks2';body=json.loads(p.read_bytes()[16:]);key,record=next(iter(body['batches'].items()));pair=json.dumps(key)+':'+json.dumps(record);text=json.dumps(body).replace(json.dumps(body['batches']),'{'+pair+','+pair+'}',1);write_catalog(p,text)
  queries=cold(d,[],rejected=True);corrupt.append({'spec':spec,'directory':d.relative_to(W).as_posix(),'cold_commands':queries,'closed_inventory':oracle.inventory(d)});checkpoint()
 for magic in [b'KSQLCAT2',b'KSQLCAT3']:
  current={'legacy':magic.decode()};d=FIX/magic.decode();d.mkdir();_,head,_,receipts=archive.metadata(FIX/'seed-candidate-3')
  for name in head['segments']:shutil.copy2(FIX/'seed-candidate-3'/name,d/name)
  shutil.copy2(FIX/'seed-candidate-3/archive.lockfile',d/'archive.lockfile');body={k:head[k] for k in ['table','columns','segments']}
  if magic==b'KSQLCAT3':body['batches']=receipts
  write_catalog(d/'catalog-00000000000000000003.ks2',body,magic);decoded=oracle.legacy_check(d,magic);queries=cold(d,oracle.seed(3)[0]);before=oracle.inventory(d)
  i,_=run([W/'binaries/candidate/publication_oracle_101.exe',d,'legacy',3,'receipts' if magic==b'KSQLCAT3' else 'anonymous']);assert oracle.inventory(d)==before
  legacies.append({'magic':magic.decode(),'directory':d.relative_to(W).as_posix(),'decode':decoded,'cold_commands':queries,'oracle_command':i,'closed_inventory':before});checkpoint()
 for variant,large in itertools.product(['normal','candidate'],[False,True]):
  current={'byte':variant,'large':large};d=FIX/f'byte-{variant}-{large}';args=['oversized'] if large else [];i,_=run([W/'binaries'/variant/'byte_equivalence_probe.exe',d,*args]);rows,receipts=oracle.byte_model(large);decoded=decode(d,(rows,receipts));before=oracle.inventory(d)
  other='candidate' if variant=='normal' else 'normal';j,_=run([W/'binaries'/other/'byte_equivalence_probe.exe',d,'reopen',*args]);assert oracle.inventory(d)==before;queries=cold(d,rows,2)
  byte_cases.append({'variant':variant,'large':large,'directory':d.relative_to(W).as_posix(),'create_command':i,'cross_reopen_command':j,'cold_commands':queries,'decode':decoded,'closed_inventory':oracle.inventory(d)});checkpoint()
 for large in [False,True]:assert next(c['closed_inventory'] for c in byte_cases if c['large']==large and c['variant']=='normal')==next(c['closed_inventory'] for c in byte_cases if c['large']==large and c['variant']=='candidate')
 assert len(records)==1065 and all(sha(W/n)==h for n,h in freeze.items());current=None;checkpoint()
 save(W/'oracle-proof-103.json',{'complete':True,'publication_cases':104,'source_cases':26,'corruptions':22,'legacy_formats':2,'byte_fixtures':4,'native_commands':1065,'no_performance_timers':True,'all_frozen_inputs_exact':True})
 print(json.dumps(load(W/'oracle-proof-103.json')),flush=True)
except BaseException:
 checkpoint();save(W/'oracle-failure-103.json',{'error':traceback.format_exc(),'current':current,'completed_publication':len(pubs),'completed_source':len(sources),'completed_corruption':len(corrupt),'completed_legacy':len(legacies),'completed_bytes':len(byte_cases),'native_commands':len(records),'all_raw_partial_stores_and_unstarted_policy_retained':True});raise
