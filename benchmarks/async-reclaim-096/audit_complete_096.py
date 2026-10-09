"""Audit all finalized worker/unit/oracle stores and every partial failed store; no Native."""
from pathlib import Path
import hashlib,json,sqlite3,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import archive_audit_096 as archive
import audit_recovery_096_v2 as worker
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(x) for x in p.read_bytes().splitlines() if x.strip()]
def audit(w):
 complete=worker.audit(w)
 # Original stopped cohort and probe timeout remain material failed evidence.
 f=w/'failed-recovery-v1';failure=load(f/'worker-recovery-failure.json');assert len(failure['cases'])==41 and len(failure['unstarted'])==7
 freeze=load(f/'worker-recovery-freeze.json');assert all(sha(f/n)==h for n,h in freeze['files'].items())
 preserved=load(w/'first-recovery-failure-preservation.json');assert all(sha(f/n)==h for n,h in preserved['files'].items())
 original_records=load(f/'native-run-order.json');assert len(original_records)==263
 partial=[]
 for index in range(42):
  spec=load(f/'worker-run-declaration.json')['cases'][index];directory=f/'worker-fixtures'/f'case-{index:03d}'/'archive'
  if index<41:r=original_records[failure['cases'][index]['native_command']]
  else:
   r=original_records[250];assert r['owned_hard_error_termination'] and r['returncode']==1
   assert [x['event'] for x in lines(f/r['stdout']) if x['event']!='ack']==['scheduled','archive_dropped','worker_joined_pin_retained']
  stream=lines(f/r['stdout']);acks=[x for x in stream if x['event']=='ack'];groups=96 if index==40 else 64
  assert len(acks)==groups and [x['group'] for x in acks]==list(range(groups))
  rows=[[i,2*i,i%97] for i in range(groups*100)]
  receipts={f"seed:{x['group']}":(rows[x['group']*100:(x['group']+1)*100],x['generation']) for x in acks} if spec['history']=='named' else {}
  decoded=archive.check(directory,rows,receipts)
  if index<41:assert decoded==failure['cases'][index]['decode']
  assert (directory/'segment-00000000000000000999.ks2').read_bytes()==b'096 untouched crash orphan'
  assert (directory/'catalog-00000000000000000998.pending').read_bytes()==b'096 untouched pending'
  partial.append({'index':index,'groups':groups,'decode':decoded,'stdout_sha256':sha(f/r['stdout']),'stderr_sha256':sha(f/r['stderr']),'original_stdin_control_failure':index==41})
 # Six exact byte probes and two freshly executed Live protocol/retry stores.
 proof=load(w/'oracle-proof.json');journal=load(w/'oracle-journal-proof.json');assert proof['complete'] and journal['complete']
 assert journal['native_commands']==56 and journal['bridge_launches']==4 and journal['wire_requests']==338 and journal['fresh_named_acks']==320
 assert all(sha(w/n)==h for n,h in load(w/'oracle-freeze.json')['files'].items())
 records=load(w/'oracle-native-run-order.json');assert len(records)==56
 for i,r in enumerate(records):
  assert r['index']==i and 'completed_utc' in r and not r.get('timeout') and r['returncode'] in [0,1]
  for kind in ['stdout','stderr']:assert sha(w/r[kind])==r[kind+'_sha256']
 bridges=load(w/'oracle-bridge-run-order.json');assert len(bridges)==4 and all(x['controlled_owned_process_termination'] and 'completed_utc' in x for x in bridges)
 wire=lines(w/'oracle-native-raw/wire.jsonl');assert len(wire)==338 and all(x['index']==i for i,x in enumerate(wire))
 oracles=[]
 for variant in ['released016','baseline','candidate']:
  directory=w/'oracles'/(variant+'-sequence');rows=[[i,2*i] for i in range(73)]+[[40,80]]
  receipts={f'id:{i:03d}':([[i,2*i]],i+1+int(i>64)) for i in range(73) if i!=40}
  receipts.update({k:([[40,80]],41) for k in ['A:group/40','B:group/40']});decoded=archive.check(directory,rows,receipts)
  oracles.append({'directory':directory.relative_to(w).as_posix(),'decode':decoded})
  directory=w/'oracles'/(variant+'-oversized');rows=[[i,2*i] for i in range(70001)]
  receipts={f'{i:06d}:'+('x'*121):([[i,2*i]],1) for i in range(70000)};receipts['after-large']=([[70000,140000]],2)
  decoded=archive.check(directory,rows,receipts);oracles.append({'directory':directory.relative_to(w).as_posix(),'decode':decoded})
 for p in proof['wire_and_live_checks']:
  rows=[[i,(i*37)%1000-500,(i*17)%97] for i in range(16)]
  receipts={}
  assert len(p['acks'])==160
  for index,x in enumerate(p['acks']):
   assert x['request']=={'op':'append','id':f'id:{index}','data':[[16+index,(16+index)*2,1000+index]]}
   row=x['request']['data'];rows+=row;receipts[f'id:{index}']=(row,x['receipt']['generation'])
   matches=[z for z in wire if z['request']==x['request'] and z.get('result')==x['receipt']];assert matches
  directory=w/'oracles'/('live-'+p['variant'])/'archive';decoded=archive.check(directory,rows,receipts)
  assert not p['state']['ingest']['writer_poisoned'] and p['state']['ingest']['maintenance_errors']==0
  assert p['repeat']['duplicate'] and p['repeat']['generation']==p['acks'][17]['receipt']['generation'] and p['collision_error']
  oracles.append({'directory':directory.relative_to(w).as_posix(),'decode':decoded})
 assert len(oracles)==8
 ref=sqlite3.connect(':memory:');ref.execute('CREATE TABLE events(ts INTEGER,value INTEGER)');ref.executemany('INSERT INTO events VALUES (?,?)',[(i,i*2) for i in range(73)]+[(40,80)])
 assert len(proof['sqlite_checks'])==24
 for x in proof['sqlite_checks']:assert [list(ref.execute(x['sql']).fetchone())]==x['expected']
 ref.close()
 return {'passed':True,'worker':complete,'first_failed_cohort_stores':42,'first_failed_cohort_ack_batches':sum(x['groups'] for x in partial),'first_failed_crc_bytes':sum(x['decode']['full_block_crc_bytes'] for x in partial),'original_probe_timeout_preserved_not_engine_regression_proof':True,'partial_stores':partial,'oracle_stores':oracles,'oracle_current_stores':8,'oracle_crc_bytes':sum(x['decode']['full_block_crc_bytes'] for x in oracles),'oracle_native_commands':56,'oracle_bridges':4,'oracle_wire_requests':338,'fresh_live_named_one_row_acks':320,'sqlite_checks':24,'exact_byte_fixtures':6,'cold_cross_reads':18,'native_launches':0,'performance_timer_launches':0}
if __name__=='__main__':
 w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-096')
 result=audit(w);p=w/'complete-audit-proof.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['worker','partial_stores','oracle_stores']}))
