"""No Native launches/timers: recompute all new worker faults and unit-store data."""
from pathlib import Path
import hashlib,itertools,json,re,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent));import archive_audit_096 as archive
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(x) for x in p.read_bytes().splitlines() if x.strip()]
def inventory(p):return {q.name:sha(q) for q in p.iterdir() if q.is_file()}
def audit(w):
 assert sha(w/'policy.json')=='ddd8c163a2c13cfd6cfab34a3b583cfd6ad240a5b3cd207d4ded66868af969ce'
 proof=load(w/'worker-recovery-proof-v2.json');assert proof['complete'] and proof['fixed_faults']==40 and proof['fixed_concurrent_cases']==8 and len(proof['cases'])==48
 declaration=load(w/'worker-run-declaration-v2.json');assert len(declaration['cases'])==48
 freeze=load(w/'worker-recovery-freeze-v2.json');assert all(sha(w/n)==h for n,h in freeze['files'].items())
 build=load(w/'build-proof.json');assert build['complete'] and build['strict_lint_modes']==4 and build['normal_artifacts_exclude_fault_keys']
 assert all(r['returncode']==0 for r in build['records']);assert sum(r.get('tests_passed',0) for r in build['records'])==build['native_test_executions']
 for f,dirname in [('first-build-failure-preservation.json','failed-build-v1'),('second-build-failure-preservation.json','failed-build-v2'),('third-build-failure-preservation.json','failed-build-v3')]:
  fp=load(w/f);root=w/dirname
  assert all(sha(root/n)==h for n,h in fp['files'].items())
 records=load(w/'native-run-order-v2.json');assert len(records)==proof['native_commands']
 for i,r in enumerate(records):
  assert r['index']==i and 'completed_utc' in r and not r.get('timeout') and not r.get('owned_timeout_termination') and not r.get('owned_hard_error_termination')
  for kind in ['stdout','stderr']:assert sha(w/r[kind])==r[kind+'_sha256']
 results=[];acks_total=0;checked=0;rejections=0
 for spec,c in zip(declaration['cases'],proof['cases']):
  assert c['spec']==spec and spec['index']==len(results)
  r=records[c['native_command']];stream=lines(w/r['stdout']);acks=[x for x in stream if x['event']=='ack']
  groups=96 if spec.get('action')=='publish' else 64;assert len(acks)==groups and [x['group'] for x in acks]==list(range(groups)) and all(x['rows']==100 and x['named']==(spec['history']=='named') for x in acks)
  assert [x['generation'] for x in acks[:64]]==list(range(1,65));assert acks==c['acks']
  env=r['fault_environment'];assert env['KESTREL_ASYNC_POINT']==spec['point'] and env['KESTREL_ASYNC_MODE']==spec['mode'] and int(env['KESTREL_ASYNC_ORDINAL'])==spec['ordinal']
  hook=lines(w/c['hook_log']);assert sha(w/c['hook_log'])==c['hook_sha256']
  reached=[x for x in hook if x['phase']==spec['point'] and x['ordinal']==spec['ordinal'] and x['kind']==(spec['target'] if 'delete' in spec['point'] else 'batch')];assert reached and reached[0]==c['actual_cut_reached']
  if spec['mode']=='exit':assert r['returncode']==86
  else:
   assert r['returncode']==0
   if spec['mode']=='error':
    end=next(x for x in stream if x['event']=='completed');assert end['stats']['failures']==1 and end['stats']['inflight']==0 and end['stats']['max_inflight']<=2
   elif spec['action']=='publish':
    e=next(x for x in stream if x['event']=='published_while_worker_paused');assert e['stats']['inflight']==2 and e['stats']['max_inflight']==2 and e['stats']['rejected']>0
    end=next(x for x in stream if x['event']=='finished');assert end['stats']['failures']==0 and end['stats']['inflight']==0
   else:assert [x['event'] for x in stream if x['event']!='ack']==['scheduled','archive_dropped','worker_joined_pin_retained','all_dropped']
  # Audit the actually reached selected file ordinal, not an unrelated publication counter.
  if 'delete' in spec['point']:
   cut=hook.index(reached[0]);prefix=hook[:cut+1];before=[x for x in prefix if x['phase']=='before-delete'];after=[x for x in prefix if x['phase']=='after-delete']
   assert len(before)==spec['ordinal'] and len(after)==spec['ordinal']-(1 if spec['point']=='before-delete' else 0)
   assert all(x['kind']==spec['target'] for x in before)
   assert all(x['name']==before[i]['name'] and x['ordinal']==before[i]['ordinal'] for i,x in enumerate(after))
  directory=w/c['directory'];assert inventory(directory)==c['closed_inventory']
  rows=[[i,2*i,i%97] for i in range(groups*100)]
  receipts={f"seed:{x['group']}":(rows[x['group']*100:(x['group']+1)*100],x['generation']) for x in acks} if spec['history']=='named' else {}
  decoded=archive.check(directory,rows,receipts);assert decoded==c['decode']
  assert (directory/'segment-00000000000000000999.ks2').read_bytes()==b'096 untouched crash orphan'
  assert (directory/'catalog-00000000000000000998.pending').read_bytes()==b'096 untouched pending'
  for idx in c['owner_rejection_commands']:
   rr=records[idx];assert rr['returncode']==1 and b'lock' in (w/rr['stderr']).read_bytes().lower();rejections+=1
  assert len(c['owner_rejection_commands'])==(4 if spec.get('action')=='publish' else 12 if spec.get('action')=='drop' else 0)
  assert len(c['cold_reader_commands'])==5 and all(records[idx]['returncode']==0 for idx in c['cold_reader_commands'])
  for idx in c['cold_reader_commands'][1:]:assert load(w/records[idx]['stdout'])['result']['rows']==[[groups*100,groups*100*(groups*100-1)]]
  acks_total+=groups;checked+=decoded['full_block_crc_bytes'];results.append({'index':spec['index'],'groups':groups,'decode':decoded})
 assert acks_total==proof['ack_batches']==3200 and checked==proof['full_crc_bytes']==7680000 and rejections==64
 # 72 stores from four original eight-test suites plus 19 from final nine-test run.
 units=[];equivalence={};roots=[p for p in (w/'cargo-tests').iterdir() if p.is_dir() and p.name.startswith('async-096-')]
 for p in sorted(roots):
  match=re.fullmatch(r'async-096-(.+)-(\d+)-(\d+)',p.name);assert match,p.name;label,pid,_=match.groups()
  stores=[p/'full',p/'worker'] if label=='equivalence' else [p]
  for directory in stores:
   n=65 if label in ['bound','progress'] else 2 if label=='filesystem' else 66 if label=='source' else 64
   rows=[[i,2*i] for i in range(64)] + [[100,9],[-1,11]] if label=='source' else [[i,2*i] for i in range(n)]
   _,_,_,existing=archive.metadata(directory);receipts={}
   if label in ['equivalence','source']:
    if label=='source' or existing:
     receipts={f'id:{i}':([[i,2*i]],i+1) for i in range(64)}
     if label=='source':
      key=hashlib.sha256(b'kestrelsql.source.v1\0orders').hexdigest();receipts[f'ksrc1:{key}:{100:016x}:{200:016x}']=([[100,9],[-1,11]],66)
    if label=='equivalence':equivalence.setdefault(pid,{}).setdefault(p.name,[]).append(len(existing))
   decoded=archive.check(directory,rows,receipts);units.append({'directory':directory.relative_to(w).as_posix(),'label':label,'decode':decoded})
 assert len(units)==91 and len(equivalence)==5
 for group in equivalence.values():assert len(group)==2 and sorted(group.values())==[[0,0],[64,64]]
 return {'passed':True,'worker_cases':48,'new_fault_cases':40,'concurrent_cases':8,'ack_batches':acks_total,'worker_crc_bytes':checked,'owner_rejections':rejections,'new_unit_current_stores':len(units),'unit_crc_bytes':sum(x['decode']['full_block_crc_bytes'] for x in units),'native_test_executions':build['native_test_executions'],'strict_lint_modes':4,'cases':results,'unit_stores':units,'native_launches':0,'performance_timer_launches':0,'all_frozen_inputs_and_failed_versions_exact':True}
if __name__=='__main__':
 w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-096')
 result=audit(w);p=w/'offline-audit-proof-v2.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in result.items() if k not in ['cases','unit_stores']}))
