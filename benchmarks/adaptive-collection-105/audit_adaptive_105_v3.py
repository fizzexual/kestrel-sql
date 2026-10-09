"""Pure replay of the new adaptive correctness cohort; no Native calls or writes."""
from pathlib import Path
import hashlib,itertools,json,sqlite3,struct,sys,zlib
import numpy as np
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import archive_audit_099 as archive

POINTS=['segment_partial','segment_written','segment_synced','catalog_partial','catalog_written','catalog_synced','catalog_published']
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(x) for x in p.read_bytes().splitlines() if x.strip()]
def inventory(p):return {f.relative_to(p).as_posix():sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def brief(d):return {k:v for k,v in d.items() if k!='receipts'}|{'receipt_count':len(d['receipts']),'receipts_sha256':hashlib.sha256(json.dumps(d['receipts'],sort_keys=True,separators=(',',':')).encode()).hexdigest()}
def data(key):return [[key,7,1],[key-1,-3,2]]
def fault_model(published,recovered=False):
 rows=data(-10);receipts={'adaptive:seed':(rows.copy(),1)}
 if published or recovered:
  rows+=data(1000);receipts['adaptive:target']=(data(1000),2 if published else 3)
 return rows,receipts
def sql_reference(rows):
 with sqlite3.connect(':memory:') as db:
  db.execute('CREATE TABLE events(ts INTEGER,value INTEGER,device INTEGER)');db.executemany('INSERT INTO events VALUES(?,?,?)',rows)
  queries=['SELECT COUNT(*), SUM(value) FROM events','SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device','SELECT COUNT(*), SUM(value) FROM events WHERE value >= 0','SELECT MIN(ts), MAX(ts), SUM(device) FROM events']
  return [{'sql':sql,'rows':[list(row) for row in db.execute(sql).fetchall()]} for sql in queries]
def legacy(d,magic):
 cats=list(d.glob('catalog-*.ks2'));assert len(cats)==1
 body,tail=archive.envelope(cats[0],magic);assert not tail
 assert set(body)==({'table','columns','segments','batches'} if magic==b'KSQLCAT3' else {'table','columns','segments'})
 assert body['table']=='events' and body['columns']==['ts','value','device'] and len(body['segments'])==1
 expected=data(-10)
 if magic==b'KSQLCAT3':assert body['batches']=={'adaptive:seed':{'rows':2,'generation':1,'digest':archive.digest(expected)}}
 meta,payload=archive.envelope(d/body['segments'][0],b'KSQLSEG2');assert meta['rows']==2 and len(payload)==48
 cols=np.frombuffer(payload,dtype='<i8').reshape((3,2));reference=np.array(expected,dtype='<i8').T
 ai=np.lexsort(tuple(cols[i] for i in range(2,-1,-1)));ri=np.lexsort(tuple(reference[i] for i in range(2,-1,-1)));assert np.array_equal(cols[:,ai],reference[:,ri])
 for col,index in zip(cols,meta['indexes']):
  assert index['crc']==[zlib.crc32(col.tobytes())] and index['prefix']==[0,sum(map(int,col))]
  assert index['last']==[int(col[-1])] and index['block_min']==[int(col.min())] and index['block_max']==[int(col.max())]
  assert index['min']==int(col.min()) and index['max']==int(col.max()) and index['monotonic']==bool(np.all(col[1:]>=col[:-1]))
 return {'format':magic.decode(),'rows':2,'full_block_crc_bytes':48}
def audit(w):
 policy=load(w/'external-v2-policy.json');proof=load(w/'external-v2-proof.json');freeze=load(w/'external-v2-freeze.json')
 assert proof['complete'] and policy['before_first_native'] and policy['faults']==[{'index':i,'point':p,'mode':m} for i,p,m in itertools.product([0,1],POINTS,['exit','io_error'])]
 assert all(sha(w/n)==h for n,h in freeze['files'].items())
 build=load(w/policy['build_proof']);assert build['complete'] and build['strict_lint_modes']==5
 records=load(w/'external-v2-command-order.json');updates={r['index']:r for r in lines(w/'external-v2-native/events.jsonl')}
 assert records==[updates[i] for i in range(len(records))]
 used=[]
 for i,r in enumerate(records):
  assert r['index']==i and r['owned_Popen_handle'] and r['pid']>0 and r['actual_wait_completed'] and not r.get('timeout')
  for kind in ['stdout','stderr']:assert sha(w/r[kind])==r[kind+'_sha256']
 def command(i,expected=0):
  used.append(i);r=records[i];assert r['returncode']==expected;return r
 def cold(case,rows,rejected=False):
  if not rejected:assert case['sql_reference']==sql_reference(rows)
  for c in case['cold_commands']:
   r=command(c['command'],1 if rejected else 0);assert r['argv'][-1]==c['sql']
   if not rejected:assert load(w/r['stdout'])['result']['rows']==next(x['rows'] for x in case['sql_reference'] if x['sql']==c['sql'])
  assert inventory(w/case.get('cold_directory',case['directory']))==case['closed_inventory']
 seed=load(w/'external-v2-seed.json');r=command(seed['command']);assert lines(w/r['stdout'])[0]['generation']==1
 assert brief(archive.check(w/seed['directory'],*fault_model(False)))==seed['decode']
 assert inventory(w/seed['directory'])==seed['inventory']
 scenarios=load(w/'external-v2-scenarios.json');assert [c['indexed'] for c in scenarios]==[0,1]
 crc=48
 for c in scenarios:
  r=command(c['command']);events=lines(w/r['stdout']);s=events[0];assert s['mode']=='scenario' and s['indexed']==bool(c['indexed'])
  entries=s['records'];assert len(entries)==529 and len({x['id'] for x in entries})==529
  expected_ids={f'sequential:{k}' for k in range(-16,0)}|{f'concurrent:{p}:{b}' for p,b in itertools.product(range(32),range(16))}|{'tail:single'}
  assert {x['id'] for x in entries}==expected_ids
  rows=[];receipts={}
  for e in entries:
   key=-20 if e['id']=='tail:single' else int(e['id'].split(':')[1]) if e['id'].startswith('sequential:') else int(e['id'].split(':')[1])*1000+int(e['id'].split(':')[2])*2+100
   assert e['key']==key and e['rows']==2;part=data(key);rows+=part;receipts[e['id']]=(part,e['generation'])
  phase=s['adaptive'];stats=s['ingest'];assert phase['last_phase']=='latency' and phase['last_selected_delay_ns']==0 and phase['max_selected_delay_ns']<=2_000_000
  assert phase['observed_publications']==stats['durable_group_commits'] and sum(phase[k] for k in ['latency_groups','coalescing_groups','pressure_groups'])==stats['collected_groups']
  assert s['before_burst']['latency_groups']==16 and s['before_burst']['max_selected_delay_ns']==0
  assert stats['queued_payload_bytes']==0 and stats['maintenance_errors']==0 and not stats['writer_poisoned'] and stats['duplicate_batches']==512 and stats['prepared_retry_hits']==(512 if c['indexed'] else 0)
  assert events[-1]['event']=='actual_writer_joined_pin_released' and events[-1]['cold_rows']==1058 and events[-1]['all_original_generation_retries_checked']==529
  decoded=brief(archive.check(w/c['directory'],rows,receipts));assert decoded==c['decode'];crc+=decoded['full_block_crc_bytes'];cold(c,rows)
 faults=load(w/'external-v2-faults.json');assert len(faults)==28
 for spec,c in zip(policy['faults'],faults):
  assert c['spec']==spec;published=spec['point']=='catalog_published';r=command(c['fault_command'],86 if spec['mode']=='exit' else 87)
  assert r['fault_environment']=={'KESTREL_FAULT_POINT':spec['point'],'KESTREL_FAULT_MODE':spec['mode']}
  if spec['mode']=='io_error':
   events=lines(w/r['stdout']);assert events[0]['ingest']['writer_poisoned'] and events[0]['pinned_rows']==2 and events[-1]['event']=='actual_writer_joined_pin_released'
   assert events[-1]['cold_rows']==(4 if published else 2)
  before=brief(archive.check(w/c['before_directory'],*fault_model(published)));assert before==c['before'] and inventory(w/c['before_directory'])==c['before_inventory'];crc+=before['full_block_crc_bytes']
  r=command(c['recover_command']);s=lines(w/r['stdout'])[0]
  assert s['before_rows']==(4 if published else 2) and s['seed_generation']==1 and s['target_generation']==(2 if published else 3) and s['target_was_duplicate']==published and s['verified_bytes']==96
  rows,receipts=fault_model(published,True);after=brief(archive.check(w/c['directory'],rows,receipts));assert after==c['after'];crc+=after['full_block_crc_bytes'];cold(c,rows)
 corrupt=load(w/'external-v2-corruptions.json');assert [c['spec'] for c in corrupt]==policy['corruptions']
 for c in corrupt:cold(c,[],True)
 legacies=load(w/'external-v2-legacies.json');assert [c['magic'] for c in legacies]==['KSQLCAT2','KSQLCAT3']
 for c in legacies:assert legacy(w/c['directory'],c['magic'].encode())==c['decode'];crc+=48;cold(c,data(-10))
 byte=load(w/'external-v2-byte.json');assert len(byte)==2 and [c['variant'] for c in byte]==['baseline','candidate']
 for c in byte:
  path=w/c['directory'];lifecycle=load(path/'bridge-lifecycle.json');assert len(lifecycle)==1
  life=lifecycle[0];assert life['returncode']==0 and life['graceful_background_joined'] and life['final']['ingest']['writer_stopped']
  assert (path/life['stdin']).read_bytes()==b'shutdown\n'
  messages=c['requests'];assert len(messages)==42+(1 if c['variant']=='candidate' else 0)
  rows=[];receipts={}
  for n in range(20):
   part=data(n);rows+=part;receipts[f'byte:{n}']=(part,n+1)
   first,retry=messages[2*n:2*n+2];assert first['response']=={'affected':2,'duplicate':False,'generation':n+1} and retry['response']=={'affected':2,'duplicate':True,'generation':n+1}
   assert first['request']=={'op':'append','data':part,'id':f'byte:{n}'} and retry['request']==first['request']
  assert 'error' in messages[40] and 'error' in messages[41]
  if c['variant']=='candidate':assert messages[-1]['response']['max_selected_delay_ns']==0 and messages[-1]['response']['latency_groups']==41
  d=path/'archive';decoded=brief(archive.check(d,rows,receipts));assert decoded==c['decode'] and inventory(d)==c['archive_inventory'];crc+=decoded['full_block_crc_bytes']
  cold(c,rows)
 assert byte[0]['archive_inventory']==byte[1]['archive_inventory']
 anonymous=load(w/'external-v2-anonymous.json');path=w/anonymous['directory'];lifecycle=load(path/'bridge-lifecycle.json');assert len(lifecycle)==1
 assert lifecycle[0]['returncode']==0 and lifecycle[0]['graceful_background_joined'] and lifecycle[0]['final']['ingest']['writer_stopped']
 entries=anonymous['acks'];assert len(entries)==256 and {(e['producer'],e['batch']) for e in entries}==set(itertools.product(range(16),range(16)))
 rows=[]
 for e in entries:
  key=e['producer']*1000+e['batch']*2+10;part=data(key);rows+=part
  assert e['request']=={'op':'append','data':part} and e['response']['affected']==2 and not e['response']['duplicate'] and e['response']['generation']>0
 phase=anonymous['phase'];assert phase['max_selected_delay_ns']<=2_000_000 and phase['observed_publications']==lifecycle[0]['final']['ingest']['durable_group_commits']
 decoded=brief(archive.check(path/'archive',rows,{}));assert decoded==anonymous['decode'];crc+=decoded['full_block_crc_bytes'];cold(anonymous,rows)
 assert sorted(used)==list(range(len(records))) and len(used)==len(set(used))
 return {'complete':True,'fresh_test_executions':build['fresh_native_test_executions'],'strict_lints':5,'scenarios':2,'anonymous_concurrent_acks':256,'fault_cases':28,'legacy_formats':2,'corruption_cases':len(corrupt),'byte_fixtures':2,'cold_sql_commands':sum(len(c['cold_commands']) for c in scenarios+faults+corrupt+legacies+byte+[anonymous]),'full_block_crc_bytes':crc,'every_native_actual_exit_checked':True,'every_raw_command_replayed':True,'complete_row_receipt_index_crc_and_sqlite_checks':True,'all_frozen_inputs_exact':True,'correctness_qualified':True,'performance_qualified':False,'release017_qualified':False}

if __name__=='__main__':print(json.dumps(audit(Path(sys.argv[1])),indent=2))
