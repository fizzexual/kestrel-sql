"""Pure CRC/NumPy/receipt audit; zero Native executions or comparative timers."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-102')))
import archive_audit_096 as archive
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def lines(p):return [json.loads(x) for x in p.read_bytes().splitlines() if x.strip()]
def audit(w):
 assert sha(w/'policy.json')=='2cfc5325f1097b311ed7c2b3eb9892f5faad470313a21af04696f61b314b5ef3'
 report=load(w/'backlog-results.json');policy=load(w/'policy.json');assert report['complete'] and len(report['cases'])==4 and not report['failures']
 assert [c['spec'] for c in report['cases']]==[{'history':h,'variant':v} for h in policy['sustained_backlog']['histories'] for v in policy['sustained_backlog']['binaries']]
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
 return {'passed':True,'backlog_cases':4,'acknowledged_groups':48000,'case_full_crc_reference_bytes':sum(c['decode']['full_block_crc_bytes'] for c in results),'all_original_named_generation_receipts_verified':True,'all_four_backlog_gates_passed':all(c['backlog_gate_passed'] for c in results),'native_launches':0,'performance_timer_launches':0,'cases':results}
if __name__=='__main__':
 w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-102');result=audit(w);p=w/'backlog-audit-proof.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in result.items() if k not in ['cases','shutdown_units','worker_units']}))
