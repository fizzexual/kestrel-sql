"""Final independent audit includes every first reached/failed current store."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import archive_audit_096 as archive
import audit_coupling_097_v2 as final
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(x) for x in p.read_bytes().splitlines() if x.strip()]
def audit(w):
 current=final.audit(w);assert current==load(w/'offline-audit-proof-v2.json')
 failure=load(w/'first-coupling-failure-preservation.json');f=w/'failed-coupling-v1';assert failure['complete']
 assert {p.relative_to(f).as_posix() for p in f.rglob('*') if p.is_file()}==set(failure['snapshot_files'])
 assert all(sha(f/n)==h for n,h in failure['snapshot_files'].items())
 for folder in ['native-raw','coupled-fixtures']:
  for is_file in [True,False]:
   first_set={p.relative_to(f/folder).as_posix() for p in (f/folder).rglob('*') if p.is_file()==is_file}
   original_set={p.relative_to(w/folder).as_posix() for p in (w/folder).rglob('*') if p.is_file()==is_file};assert first_set==original_set
  assert all(sha(p)==sha(w/folder/p.relative_to(f/folder)) for p in (f/folder).rglob('*') if p.is_file())
 firstfreeze=load(f/'recovery-freeze.json')['files'];assert all(sha(f/n)==h for n,h in firstfreeze.items())
 assert all(sha(w/n)==h for n,h in firstfreeze.items())
 recs=load(f/'native-run-order.json');original_recs=load(w/'native-run-order.json');assert recs==original_recs
 ctrls=load(f/'control-run-order.json');assert ctrls==load(w/'control-run-order.json')==lines(f/'native-raw/control-events.jsonl')
 latest={}
 for r in lines(f/'native-raw/native-events.jsonl'):latest[r['index']]=r
 assert [latest[i] for i in range(len(recs))]==recs and len(recs)==485
 first=load(f/'case-results.json');assert first==load(w/'case-results.json') and len(first)==40
 stopped=load(f/'recovery-failure.json');assert len(stopped['unstarted'])==408 and stopped['unstarted'][0]['index']==40
 assert "AssertionError" in stopped['error'] and "worker failure callback observed" in stopped['error']
 units=[];total_acks=0;total_crc=0;unack=0
 for i in range(41):
  d=f/f'coupled-fixtures/case-{i:03d}';store=d/'archive';spec=load(w/'policy.json')['cases'][i]
  r=recs[first[i]['native_command']] if i<40 else recs[480]
  stream=lines(f/r['stdout']);acks=[e for e in stream if e['event']=='ack']
  ackgroups=65 if i<40 and spec['mode']=='error' and spec['operation']=='append' else 64
  groups=65 if i<40 and spec['operation']=='append' and (spec['mode']=='error' or spec['publication_point']=='catalog_published') else 64
  gen=66 if i<40 and (spec['mode']=='error' or spec['publication_point']=='catalog_published') else 65
  assert [e['group'] for e in acks]==list(range(ackgroups))
  assert all(e['generation']==e['group']+1+int(e['group']>=64) and e['rows']==100 for e in acks)
  rows=[[j,2*j,j%97] for j in range(groups*100)];receipts={f'seed:{g}':(rows[g*100:(g+1)*100],g+1+int(g>=64)) for g in range(groups)} if spec['history']=='named' else {}
  decoded=archive.check(store,rows,receipts);assert decoded['head']==gen
  assert (store/'segment-00000000000000000999.ks2').read_bytes()==b'097 untouched crash orphan' and (store/'catalog-00000000000000000998.pending').read_bytes()==b'097 untouched pending'
  assert {p.name:sha(p) for p in store.iterdir() if p.is_file()}=={p.name:sha(w/f'coupled-fixtures/case-{i:03d}/archive'/p.name) for p in store.iterdir() if p.is_file()}
  if i<40:
   assert decoded==first[i]['decode'] and acks==first[i]['acks'] and r['returncode']==(0 if spec['mode']=='error' else 86)
   assert len(first[i]['owner_rejection_commands'])==(8 if spec['mode']=='error' else 4) and len(first[i]['cold_reader_commands'])==5
   for n in first[i]['owner_rejection_commands']:assert recs[n]['returncode']==1 and b'lock' in (f/recs[n]['stderr']).read_bytes().lower()
   for n in first[i]['cold_reader_commands']:assert recs[n]['returncode']==0
   for n in first[i]['cold_reader_commands'][1:]:assert load(f/recs[n]['stdout'])['result']['rows']==[[groups*100,groups*100*(groups*100-1)]]
  else:
   assert r['owned_hard_error_termination'] and r['returncode']!=0 and (d/'worker.observed').read_bytes()==b''
   assert not (d/'publisher.release').exists() and load(d/'publisher.entered')=={'pid':r['pid'],'point':'catalog_partial'}
   assert (d/'worker.release').exists() and not any(e['event'] in ['publication_completed','completed'] for e in stream)
  total_acks+=len(acks);total_crc+=decoded['full_block_crc_bytes'];unack+=groups-len(acks);units.append({'index':i,'decode':decoded,'data_reference_passed':True,'original_controller_case_passed':i<40})
 for r in recs:
  for k in ['stdout','stderr']+(['stdin'] if 'stdin' in r else []):
   if k+'_sha256' in r:assert sha(f/r[k])==r[k+'_sha256']
   assert (f/r[k]).read_bytes()==(w/r[k]).read_bytes()
 assert total_acks==2634 and unack==1 and total_crc==6324000
 return {'passed':True,'final':current,'first_failed_run_stores':41,'first_ack_batches':total_acks,'first_unacknowledged_committed_batches':unack,'first_crc_reference_bytes':total_crc,'first_failed_store_data_passed_controller_failure_retained':True,'total_original_current_stores':448+76+41,'total_crc_reference_bytes':current['case_crc_reference_bytes']+current['unit_crc_reference_bytes']+total_crc,'native_launches':0,'performance_timer_launches':0,'failed_first_stores':units,'all_first_and_final_original_raw_bytes_frozen_policies_sources_binaries_exact':True}
if __name__=='__main__':
 w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-097');result=audit(w);p=w/'complete-audit-proof.json';assert not p.exists()
 p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in result.items() if k not in ['final','failed_first_stores']}))
