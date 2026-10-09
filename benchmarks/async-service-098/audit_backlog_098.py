"""Pure CRC/NumPy/receipt audit; zero Native executions or comparative timers."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-098')))
import archive_audit_096 as archive
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def lines(p):return [json.loads(x) for x in p.read_bytes().splitlines() if x.strip()]
def audit(w):
 assert sha(w/'policy.json')=='4fe1c7bc59de1363cdcbf4e70a22851286e4afe7cfd1035df166690214774bfe'
 report=load(w/'backlog-results.json');policy=load(w/'policy.json');assert report['complete'] and len(report['cases'])==4 and not report['failures']
 assert [c['spec'] for c in report['cases']]==policy['sustained_backlog']['fresh_cases']
 reference=[[i,2*i,i%97] for i in range(12000)];results=[]
 for index,c in enumerate(report['cases']):
  record=load(w/'backlog-raw'/(c['label']+'.command.json'));assert record['returncode']==0 and not record['timeout']
  assert all(sha(w/record[k])==record[k+'_sha256'] for k in ['stdout','stderr'])
  stream=lines(w/record['stdout']);acks=[e for e in stream if e['event']=='ack'];samples=[e for e in stream if e['event']=='sample']
  assert len(acks)==12000 and [e['group'] for e in acks]==list(range(12000)) and all(e['rows']==1 for e in acks)
  generations=[e['generation'] for e in acks];assert generations==sorted(set(generations)) and generations[0]==1
  assert [e['groups'] for e in samples]==list(range(64,12000,64))+[12000,12000]
  assert all(s['file_count']==len(s['files']) and s['bytes']==sum(s['files'].values()) for s in samples)
  max_files=max(s['file_count'] for s in samples);max_bytes=max(s['bytes'] for s in samples)
  assert max_files==c['maximum_physical_files'] and max_bytes==c['maximum_physical_bytes']
  assert c['backlog_gate_passed']==(max_files<=192 and max_bytes<=16777216)
  joined=[e for e in stream if e['event']=='shutdown'];requested=[e for e in stream if e['event']=='shutdown_requested'];cold=[e for e in stream if e['event']=='cold']
  assert len(joined)==len(requested)==len(cold)==1 and joined[0]==c['shutdown'] and cold[0]==c['cold']
  assert stream.index(joined[0])<stream.index(samples[-1])<stream.index(cold[0]) and 0<=joined[0]['shutdown_ms']<=5000
  stats=joined[0]['stats'];assert stats['writer_stopped'] and not stats['writer_poisoned'] and stats['queued_payload_bytes']==stats['maintenance_errors']==0 and stats['committed_batches']==12000
  receipts={f'backlog:{i}':([reference[i]],generations[i]) for i in range(12000)} if c['spec']['history']=='named' else {}
  decoded=archive.check(w/c['fixture'],reference,receipts);assert decoded['head']==cold[0]['stats']['generation'] and cold[0]['stats']['rows']==12000
  results.append({'index':index,'spec':c['spec'],'decode':decoded,'maximum_physical_files':max_files,'maximum_physical_bytes':max_bytes,'backlog_gate_passed':c['backlog_gate_passed'],'actual_join_exit_before_cold_read':True})
 units=[];worker_units=[]
 for p in sorted(p for root in ['cargo-tests','cargo-tests-v2'] for p in (w/root).glob('shutdown-098-*')):
  assert p.is_dir();m=re.fullmatch(r'shutdown-098-(ownership|drop-error)-(\d+)-(\d+)',p.name);assert m
  if m[1]=='ownership':rows=[[0,2,0],[1,4,1],[2,6,2]];receipts={'shutdown:seed':(rows[:2],1),'shutdown:tail':(rows[2:],2)}
  else:rows=[[i,2*i,i%97] for i in range(4)];receipts={}
  units.append({'directory':p.relative_to(w).as_posix(),'label':m[1],'decode':archive.check(p,rows,receipts)})
 assert len(units)==24 and sum(u['label']=='ownership' for u in units)==16 and sum(u['label']=='drop-error' for u in units)==8
 for p in sorted(p for root in ['cargo-tests','cargo-tests-v2'] for p in (w/root).glob('async-096-*')):
  assert p.is_dir();m=re.fullmatch(r'async-096-(.+)-(\d+)-(\d+)',p.name);assert m;label=m[1]
  for directory in ([p/'full',p/'worker'] if label=='equivalence' else [p]):
   n=65 if label in ['bound','progress'] else 2 if label=='filesystem' else 66 if label=='source' else 64
   rows=[[j,2*j] for j in range(64)]+[[100,9],[-1,11]] if label=='source' else [[j,2*j] for j in range(n)]
   _,_,_,existing=archive.metadata(directory);receipts={}
   if label in ['equivalence','source'] and (label=='source' or existing):
    receipts={f'id:{j}':([[j,2*j]],j+1) for j in range(64)}
    if label=='source':key=hashlib.sha256(b'kestrelsql.source.v1\0orders').hexdigest();receipts[f'ksrc1:{key}:{100:016x}:{200:016x}']=([[100,9],[-1,11]],66)
   worker_units.append({'directory':directory.relative_to(w).as_posix(),'label':label,'decode':archive.check(directory,rows,receipts)})
 assert len(worker_units)==152
 failure=load(w/'first-build-failure-preservation.json');f=w/'failed-build-v1';assert failure['complete'] and all(sha(f/n)==h for n,h in failure['files'].items())
 assert {p.relative_to(f).as_posix() for p in f.rglob('*') if p.is_file()}==set(failure['files'])
 assert sha(w/'policy.json')==sha(f/'policy.json') and load(f/'build-failure.json')['records'][-1]['step']=='default-lint'
 return {'passed':True,'backlog_cases':4,'acknowledged_groups':48000,'case_full_crc_reference_bytes':sum(c['decode']['full_block_crc_bytes'] for c in results),'all_original_named_generation_receipts_verified':True,'all_four_backlog_gates_passed':all(c['backlog_gate_passed'] for c in results),'shutdown_unit_stores':len(units),'shutdown_unit_full_crc_reference_bytes':sum(u['decode']['full_block_crc_bytes'] for u in units),'worker_unit_stores':len(worker_units),'worker_unit_full_crc_reference_bytes':sum(u['decode']['full_block_crc_bytes'] for u in worker_units),'first_build_failure_source_logs_executables_exact':True,'native_launches':0,'performance_timer_launches':0,'cases':results,'shutdown_units':units,'worker_units':worker_units}
if __name__=='__main__':
 w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-098');result=audit(w);p=w/'backlog-audit-proof.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in result.items() if k not in ['cases','shutdown_units','worker_units']}))
