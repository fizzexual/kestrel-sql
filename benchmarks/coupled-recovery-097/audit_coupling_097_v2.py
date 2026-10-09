"""Pure448-case journal/cut/publication/ACK/receipt/CRC audit; zero Native/timers."""
from pathlib import Path
import collections,hashlib,itertools,json,re,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent));import archive_audit_096 as archive
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(x) for x in p.read_bytes().splitlines() if x.strip()]
def inventory(p):return {q.name:sha(q) for q in p.iterdir() if q.is_file()}
def audit(w):
 policy=load(w/'policy.json');proof=load(w/'recovery-proof-v2.json');freeze=load(w/'recovery-freeze-v2.json');build=load(w/'build-proof.json')
 assert sha(w/'policy.json')==load(w/'declaration-proof.json')['policy_sha256']
 assert all(sha(w/n)==h for n,h in freeze['files'].items())
 assert {p.relative_to(w/'source').as_posix():sha(p) for p in (w/'source').rglob('*') if p.is_file()}==load(w/'source-derivation.json')['final']
 assert build['complete'] and build['normal_artifacts_exclude_fault_keys'] and build['strict_lint_modes']==4
 assert all(r['returncode']==0 and sha(w/r['log'])==r['log_sha256'] for r in build['records'])
 assert sum(r.get('tests_passed',0) for r in build['records'])==build['native_test_executions']==370
 for f,source in [('failed-preparation-v1',load(w/'source-before.json')),('failed-preparation-v2',load(w/'source-derivation.json')['final'])]:
  root=w/f;assert sha(root/'policy.json')==sha(w/'policy.json')
  assert {p.relative_to(root/'source').as_posix():sha(p) for p in (root/'source').rglob('*') if p.is_file()}==source
  assert (root/'error.log').is_file()
 assert proof['complete'] and proof['fixed_cases']==448 and policy['fixed_case_count']==448
 points=['segment_partial','segment_written','segment_synced','catalog_partial','catalog_written','catalog_synced','catalog_published']
 expected=[]
 for history,target,wp,ordinal,pp,operation,mode in itertools.product(['anonymous','named'],['catalog','retired'],['before-delete','after-delete'],[1,20],points,['append','compact'],['error','exit']):
  expected.append({'index':len(expected),'history':history,'target':target,'worker_point':wp,'ordinal':ordinal,'publication_point':pp,'operation':operation,'mode':mode})
 assert policy['cases']==expected
 records=load(w/'native-run-order-v2.json');controls=load(w/'control-run-order-v2.json');cases=load(w/'case-results-v2.json')
 assert len(cases)==448 and len(records)==proof['native_commands']==5376
 updates=lines(w/'native-raw-v2/native-events.jsonl');reconstructed={}
 for event in updates:reconstructed[event['index']]=event
 assert [reconstructed[i] for i in range(len(records))]==records
 assert lines(w/'native-raw-v2/control-events.jsonl')==controls
 for i,r in enumerate(records):
  assert r['index']==i and 'completed_utc' in r and not any(r.get(k) for k in ['timeout','owned_timeout_termination','owned_hard_error_termination'])
  for kind in ['stdout','stderr']+(['stdin'] if 'stdin' in r else []):assert sha(w/r[kind])==r[kind+'_sha256']
 totals=collections.Counter();results=[];used=[]
 for spec,c in zip(expected,cases):
  i=spec['index'];assert c['spec']==spec and load(w/f'coupled-fixtures-v2/case-{i:03d}/case-result.json')==c
  directory=w/c['directory'];d=directory.parent;r=records[c['native_command']];used.append(c['native_command']);stream=lines(w/r['stdout']);env=r['fault_environment']
  for key,value in [('KESTREL_ASYNC_POINT',spec['worker_point']),('KESTREL_ASYNC_KIND',spec['target']),('KESTREL_ASYNC_ORDINAL',str(spec['ordinal'])),('KESTREL_ASYNC_MODE','pause-'+spec['mode']),('KESTREL_COUPLE_POINT',spec['publication_point'])]:assert env[key]==value
  assert r['owned_Popen_process_handle'] and (w/r['stdin']).read_bytes()==b'publish\n' and r['returncode']==(0 if spec['mode']=='error' else 86)
  selected=next(e for e in stream if e['event']=='scheduled');assert selected['stats']['selected']==20 and selected['stats']['inflight']==1 and selected['archive']['generation']==65
  started=next(e for e in stream if e['event']=='publication_started');assert started['operation']==spec['operation'] and started['generation_before']==65
  ctrl=[x for x in controls if x['case']==i];by={e['event']:e for e in ctrl if e['event']!='gate_write'};writes=[e for e in ctrl if e['event']=='gate_write']
  assert len(writes)==(3 if spec['mode']=='error' else 2)
  for e in writes:assert (w/e['path']).read_bytes()==bytes.fromhex(e['hex']) and sha(w/e['path'])==e['sha256']
  pub=load(w/c['publisher_marker']);assert pub=={'point':spec['publication_point'],'pid':r['pid']} and by['publisher_entered']['pid']==r['pid']
  assert by['stdin_write']['hex']==b'publish\n'.hex() and by['stdin_write']['native_command']==r['index']
  indices=[by['worker_entered']['index'],writes[0]['index'],by['stdin_write']['index'],by['publisher_entered']['index'],by['protected_before_worker_release']['index'],writes[1]['index'],by['worker_error_observed' if spec['mode']=='error' else 'worker_exit_observed']['index']]
  if spec['mode']=='error':indices+=[writes[2]['index']]
  indices+=[by['protected_after_worker_failure']['index']];assert indices==sorted(indices) and len(indices)==len(set(indices))
  assert writes[0]['path'].endswith('/arm') and writes[1]['path'].endswith('/worker.release')
  assert (d/'worker.triggered').read_bytes()==spec['mode'].encode()
  if spec['mode']=='error':assert writes[2]['path'].endswith('/publisher.release') and (d/'worker.observed').read_bytes()==b'worker failure callback observed'
  else:assert not (d/'publisher.release').exists() and not (d/'worker.observed').exists()
  before=by['protected_before_worker_release'];after=by['protected_after_worker_failure'];assert (before['generation'],before['files'])==(after['generation'],after['files'])
  assert before['generation']==(66 if spec['publication_point']=='catalog_published' else 65) and before['files']==c['protected_files_unchanged_during_fault']
  cut=lines(d/'worker-cut.jsonl');hook=lines(w/c['worker_log']);assert sha(w/c['worker_log'])==c['worker_log_sha256'] and hook[:len(cut)]==cut
  target=cut[-1];assert target=={'phase':spec['worker_point'],'kind':spec['target'],'name':c['actual_worker_name'],'ordinal':spec['ordinal']}
  assert (d/'worker.entered').read_text()==target['name']==by['worker_entered']['name']
  b=[x for x in cut if x['phase']=='before-delete'];a=[x for x in cut if x['phase']=='after-delete'];deleted=spec['ordinal']-int(spec['worker_point']=='before-delete')
  assert len(b)==spec['ordinal'] and len(a)==deleted and len(set(x['name'] for x in b))==len(b)
  assert all(x['ordinal']==j+1 and x['kind']==spec['target'] for j,x in enumerate(b))
  assert all(x['name']==b[j]['name'] and x['ordinal']==j+1 and x['kind']==spec['target'] for j,x in enumerate(a))
  existing=by['worker_entered']['existing_files'];assert (target['name'] in existing)==(spec['worker_point']=='before-delete') and not any(x['name'] in existing for x in a)
  if spec['target']=='catalog':assert all(x['name'].startswith('catalog-') and int(x['name'][8:28])<65 and x['name'] not in before['files'] for x in b)
  else:assert all(x['name'].startswith('segment-') and int(x['name'][8:28])<=32 and x['name'] not in before['files'] for x in b)
  ack_groups=65 if spec['mode']=='error' and spec['operation']=='append' else 64
  groups=65 if spec['operation']=='append' and (spec['mode']=='error' or spec['publication_point']=='catalog_published') else 64
  gen=66 if spec['mode']=='error' or spec['publication_point']=='catalog_published' else 65
  acks=[e for e in stream if e['event']=='ack'];assert acks==c['acks'] and [e['group'] for e in acks]==list(range(ack_groups))
  assert all(e['rows']==100 and e['named']==(spec['history']=='named') and e['generation']==e['group']+1+int(e['group']>=64) for e in acks)
  assert c['expected_groups']==groups and c['expected_generation']==gen and c['unacknowledged_committed_groups']==list(range(ack_groups,groups))
  if spec['mode']=='error':
   dr=next(e['stats'] for e in stream if e['event']=='first_drained');assert dr['deleted']==deleted and dr['failures']==1 and dr['inflight']==0
   end=next(e['stats'] for e in stream if e['event']=='completed');assert end['failures']==1 and end['inflight']==0 and end['max_inflight']==1
   assert next(e for e in stream if e['event']=='publication_completed')['archive']['generation']==66
  else:assert not any(e['event'] in ['publication_completed','completed','first_drained','retry'] for e in stream)
  rows=[[j,2*j,j%97] for j in range(groups*100)];receipts={f'seed:{g}':(rows[g*100:(g+1)*100],g+1+int(g>=64)) for g in range(groups)} if spec['history']=='named' else {}
  decoded=archive.check(directory,rows,receipts);assert decoded==c['decode'] and decoded['head']==gen and inventory(directory)==c['closed_inventory']
  assert (directory/'segment-00000000000000000999.ks2').read_bytes()==b'097 untouched crash orphan' and (directory/'catalog-00000000000000000998.pending').read_bytes()==b'097 untouched pending'
  owners=c['owner_rejection_commands'];cold=c['cold_reader_commands'];assert len(owners)==(8 if spec['mode']=='error' else 4) and len(cold)==5
  for n in owners:assert records[n]['returncode']==1 and b'lock' in (w/records[n]['stderr']).read_bytes().lower()
  for n in cold:assert records[n]['returncode']==0
  verify=lines(w/records[cold[0]]['stdout']);assert verify[-1]['event']=='verified' and verify[-1]['groups']==groups and verify[-1]['stats']['generation']==gen
  retried=[e for e in verify if e['event']=='retry'];assert [e['group'] for e in retried]==(list(range(groups)) if spec['history']=='named' else [])
  assert all(e['generation']==e['group']+1+int(e['group']>=64) for e in retried)
  for n in cold[1:]:assert load(w/records[n]['stdout'])['result']['rows']==[[groups*100,groups*100*(groups*100-1)]]
  used+=owners+cold;totals.update(acks=ack_groups,unacknowledged=groups-ack_groups,crc=decoded['full_block_crc_bytes'],owner_rejections=len(owners));results.append({'index':i,'groups':groups,'generation':gen,'actual_deleted_before_error_exit':deleted,'decode':decoded})
 assert sorted(used)==list(range(len(records)))
 assert totals['acks']==proof['new_ack_batches']==28784 and totals['unacknowledged']==proof['unacknowledged_committed_groups']==16
 assert totals['crc']==proof['full_crc_reference_bytes']==69120000 and totals['owner_rejections']==proof['owner_rejections']==2688
 # Four full async/combined suites now include all nine worker tests:19 stores each.
 units=[];labels=collections.Counter();eq_receipts=[]
 for p in sorted((w/'cargo-tests').iterdir()):
  if not p.is_dir() or not p.name.startswith('async-096-'):continue
  m=re.fullmatch(r'async-096-(.+)-(\d+)-(\d+)',p.name);assert m;label=m.group(1)
  for directory in ([p/'full',p/'worker'] if label=='equivalence' else [p]):
   n=65 if label in ['bound','progress'] else 2 if label=='filesystem' else 66 if label=='source' else 64
   rows=[[j,2*j] for j in range(64)]+[[100,9],[-1,11]] if label=='source' else [[j,2*j] for j in range(n)]
   _,_,_,existing=archive.metadata(directory);receipts={}
   if label in ['equivalence','source'] and (label=='source' or existing):
    receipts={f'id:{j}':([[j,2*j]],j+1) for j in range(64)}
    if label=='source':key=hashlib.sha256(b'kestrelsql.source.v1\0orders').hexdigest();receipts[f'ksrc1:{key}:{100:016x}:{200:016x}']=([[100,9],[-1,11]],66)
   if label=='equivalence':eq_receipts.append(len(existing))
   decoded=archive.check(directory,rows,receipts);labels[label]+=1;units.append({'directory':directory.relative_to(w).as_posix(),'label':label,'decode':decoded})
 assert len(units)==76 and labels['equivalence']==16 and labels['progress']==32 and sorted(eq_receipts)==[0]*8+[64]*8
 return {'passed':True,'coupled_cases':448,'new_native_tests':370,'strict_lint_modes':4,'native_commands':len(records),'owner_rejections':totals['owner_rejections'],'ack_batches':totals['acks'],'unacknowledged_committed_batches':totals['unacknowledged'],'case_crc_reference_bytes':totals['crc'],'new_worker_unit_stores':76,'unit_crc_reference_bytes':sum(x['decode']['full_block_crc_bytes'] for x in units),'native_launches':0,'performance_timer_launches':0,'all_frozen_inputs_failed_versions_and_control_journals_exact':True,'cases':results,'unit_stores':units}
if __name__=='__main__':
 w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-097');result=audit(w);p=w/'offline-audit-proof-v2.json';assert not p.exists()
 p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in result.items() if k not in ['cases','unit_stores']}))
