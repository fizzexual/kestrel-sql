"""Pure independent format/reference/journal oracle replay; no Native or writes."""
from pathlib import Path
import hashlib,itertools,json,struct,sys,zlib
import numpy as np
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import archive_audit_099 as archive
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(s) for s in p.read_bytes().splitlines() if s.strip()]
def inventory(p):return {f.name:sha(f) for f in sorted(p.iterdir()) if f.is_file()}
def brief(d):
 return {k:v for k,v in d.items() if k!='receipts'}|{'receipt_count':len(d['receipts']),'receipts_sha256':hashlib.sha256(json.dumps(d['receipts'],sort_keys=True,separators=(',',':')).encode()).hexdigest()}
def seed(count):
 rows=[[i,2*i,1] for i in range(count)]
 return rows,{f'seed:{i}':([rows[i]],i+1) for i in range(count)}
def pub_model(count,action,published,after=False):
 rows,receipts=seed(count);extra=action=='append' and (published or after)
 if extra:
  target=[[1000,7,1]]*10000;rows+=target;receipts['fault:target']=(target,count+1+int(not published))
 return rows,receipts
def source_model(published,after=False):
 key=hashlib.sha256(b'kestrelsql.source.v1\0orders:partition0').hexdigest()
 rows=[[1000,3,1]]*100;receipts={f'ksrc1:{key}:{5000:016x}:{5100:016x}':(rows.copy(),1)}
 if published or after:
  target=[[1000,7,1]]*100;rows+=target;receipts[f'ksrc1:{key}:{5100:016x}:{5200:016x}']=(target,2+int(not published))
 return rows,receipts
def byte_model(large):
 if large:
  rows=[[i,2*i] for i in range(70001)]
  receipts={f'{i:06}:'+('x'*121):([rows[i]],1) for i in range(70000)}
  receipts['after-large']=([rows[70000]],2)
 else:
  rows=[];receipts={}
  for i in range(73):
   row=[i,2*i];rows.append(row)
   if i==40:
    rows.append(row.copy());receipts['B:group/40']=([row],41);receipts['A:group/40']=([row],41)
   else:receipts[f'id:{i:03}']=([row],i+1+int(i>64))
 return rows,receipts
def legacy_check(d,magic):
 cats=list(d.glob('catalog-*.ks2'));assert len(cats)==1 and cats[0].name=='catalog-00000000000000000003.ks2'
 body,tail=archive.envelope(cats[0],magic);assert not tail and body['table']=='events' and body['columns']==['ts','value','device']
 rows,receipts=seed(3);existing=body.get('batches',{})
 assert set(body)==({'table','columns','segments','batches'} if magic==b'KSQLCAT3' else {'table','columns','segments'})
 assert set(existing)==(set(receipts) if magic==b'KSQLCAT3' else set())
 for key,(raw,generation) in receipts.items():
  if magic==b'KSQLCAT3':assert existing[key]=={'digest':archive.digest(raw),'rows':1,'generation':generation}
 payloads=[];checked=0
 assert len(body['segments'])==3 and len(set(body['segments']))==3
 for name in body['segments']:
  meta,payload=archive.envelope(d/name,b'KSQLSEG2');n=meta['rows'];assert n>0 and len(payload)==n*24 and len(meta['indexes'])==3
  cols=np.frombuffer(payload,dtype='<i8').reshape((3,n));payloads.append(cols)
  for col,index in zip(cols,meta['indexes']):
   assert index['monotonic']==bool(np.all(col[1:]>=col[:-1])) and type(index['monotonic']) is bool
   assert index['min']==int(col.min()) and index['max']==int(col.max())
   blocks=(n+4095)//4096;assert len(index['prefix'])==blocks+1 and index['prefix'][0]==0
   assert all(len(index[k])==blocks for k in ['crc','last','block_min','block_max'])
   total=0
   for bi,start in enumerate(range(0,n,4096)):
    part=col[start:start+4096];checked+=len(part)*8;total+=sum(map(int,part))
    assert zlib.crc32(part.tobytes())==index['crc'][bi] and total==index['prefix'][bi+1]
    assert [int(part[-1]),int(part.min()),int(part.max())]==[index['last'][bi],index['block_min'][bi],index['block_max'][bi]]
 actual=np.concatenate(payloads,axis=1);reference=np.array(rows,dtype='<i8').T
 assert np.array_equal(actual,reference) and checked==72
 return {'magic':magic.decode(),'rows':3,'receipt_count':len(existing),'full_block_crc_bytes':checked}
def audit(w,failed=False):
 policy=load(w/'oracle-policy-101.json');proof=load(w/('oracle-failure-101.json' if failed else 'oracle-proof-101.json'));freeze=load(w/'oracle-freeze-101.json')
 assert all(sha(w/n)==h for n,h in freeze['files'].items())
 if failed:
  assert proof['completed_publication']==72 and proof['completed_source']==18 and proof['completed_corruption']==22 and proof['completed_legacy']==0 and proof['completed_bytes']==0 and proof['native_commands']==633
  assert proof['current']=={'legacy':'KSQLCAT2'} and 'seed-candidate-3/archive.lock' in proof['error'] and 'FileNotFoundError' in proof['error']
 else:assert proof['complete']
 points=load(w/'policy.json')['publication_cuts']
 expected_pub=[{'count':n,'action':action,'point':p,'mode':m} for n,action,p,m in itertools.product([3,32],['append','compact'],points,['exit','io_error'])]
 expected_source=[{'point':p,'mode':m} for p,m in itertools.product(points,['exit','io_error'])]
 assert policy['publication']==expected_pub and len(expected_pub)==72 and policy['source']==expected_source and len(expected_source)==18
 records=load(w/'oracle-native-order.json');updates={}
 for r in lines(w/'native-oracles/native-events.jsonl'):updates[r['index']]=r
 assert [updates[i] for i in range(len(records))]==records
 used=[]
 for i,r in enumerate(records):
  assert r['index']==i and 'completed_utc' in r and not r.get('timeout')
  for kind in ['stdout','stderr']:assert sha(w/r[kind])==r[kind+'_sha256']
 def command(i,code=0):
  used.append(i);r=records[i];assert r['returncode']==code
  return r
 def queries(indices,rows,width=3,rejected=False):
  assert len(indices)==4
  for i,label in zip(indices,['normal','incremental','candidate','released016']):
   r=command(i,1 if rejected else 0);assert str(Path(r['argv'][0])).replace('\\','/').endswith('/'+label+'/kestrel.exe')
   assert r['argv'][-1]==('SELECT COUNT(*) FROM events' if rejected else 'SELECT COUNT(*), SUM(value) FROM events')
   if not rejected:assert load(w/r['stdout'])['result']['rows']==[[len(rows),sum(x[1] for x in rows)]]
 seeds=load(w/'oracle-seed-results.json');assert len(seeds)==4
 seed_results=[]
 for s in seeds:
  n=s['count'];d=w/s['directory'];rows,receipts=seed(n);r=command(s['command'])
  ack=[e for e in lines(w/r['stdout']) if e['event']=='ack'];assert [e['id'] for e in ack]==[f'seed:{i}' for i in range(n)]
  assert all(e['receipt']['generation']==i+1 and not e['receipt']['duplicate'] and e['receipt']['rows']==1 for i,e in enumerate(ack))
  decoded=brief(archive.check(d,rows,receipts));assert decoded==s['decode'] and inventory(d)==s['inventory'];seed_results.append(decoded)
 for n in [3,32]:assert next(s['inventory'] for s in seeds if s['count']==n and s['variant']=='normal')==next(s['inventory'] for s in seeds if s['count']==n and s['variant']=='candidate')
 results=[]
 pubs=load(w/'oracle-publication-results.json');assert len(pubs)==72
 for spec,c in zip(expected_pub,pubs):
  assert c['spec']==spec;published=spec['point']=='catalog_published';n=spec['count'];action=spec['action'];d=w/c['directory']
  r=command(c['failure_command'],86 if spec['mode']=='exit' else 87);assert r['fault_environment']=={'KESTREL_FAULT_POINT':spec['point'],'KESTREL_FAULT_MODE':spec['mode']}
  if spec['mode']=='io_error':assert b'poisoned writer; old snapshot readable' in (w/r['stderr']).read_bytes()
  before=w/c['before_directory'];decoded_before=brief(archive.check(before,*pub_model(n,action,published)))
  assert decoded_before==c['before'] and decoded_before['head']==n+int(published) and inventory(before)==c['before_inventory']
  r=command(c['recover_command']);stream=lines(w/r['stdout']);final=stream[-1];assert final['event']=='verified'
  if action=='append':
   replay=next(e for e in stream if e['event']=='target_recovered');expected_gen=n+1+int(not published)
   assert replay['receipt']['duplicate']==published and replay['receipt']['generation']==expected_gen and replay['retry']['duplicate'] and replay['retry']['generation']==expected_gen
  rows,receipts=pub_model(n,action,published,True);decoded=brief(archive.check(d,rows,receipts));assert decoded==c['after'] and inventory(d)==c['closed_inventory']
  assert final['crc_bytes']==len(rows)*24 and final['stats']['rows']==len(rows) and final['stats']['generation']==decoded['head']
  queries(c['cold_commands'],rows);results.append({'spec':spec,'before':decoded_before,'after':decoded})
 source_seed=load(w/'oracle-source-seed.json');r=command(source_seed['command']);assert lines(w/r['stdout'])[-1]['passed']
 assert brief(archive.check(w/source_seed['directory'],*source_model(False)))==source_seed['decode'] and inventory(w/source_seed['directory'])==source_seed['inventory']
 sources=load(w/'oracle-source-results.json');assert len(sources)==18;source_results=[]
 for spec,c in zip(expected_source,sources):
  assert c['spec']==spec;published=spec['point']=='catalog_published';d=w/c['directory'];before=w/c['before_directory']
  r=command(c['failure_command'],86 if spec['mode']=='exit' else 0);assert r['fault_environment']=={'KESTREL_FAULT_POINT':spec['point'],'KESTREL_FAULT_MODE':spec['mode']}
  if spec['mode']=='io_error':assert lines(w/r['stdout'])[-1]=={'poisoned_position_and_retries_rejected':True,'pinned_readable':True,'passed':True}
  pre=brief(archive.check(before,*source_model(published)));assert pre==c['before'] and inventory(before)==c['before_inventory'] and pre['head']==1+int(published)
  r=command(c['recover_command']);event=lines(w/r['stdout'])[-1];assert event['passed'] and event['position_before_recovery']['next_offset']==(5200 if published else 5100)
  assert event['target_replay']['duplicate']==published and event['target_replay']['generation']==2+int(not published)
  rows,receipts=source_model(published,True);post=brief(archive.check(d,rows,receipts));assert post==c['after'] and inventory(d)==c['closed_inventory'];queries(c['cold_commands'],rows)
  source_results.append({'spec':spec,'before':pre,'after':post})
 corrupt=load(w/'oracle-corruption-results.json');assert len(corrupt)==22 and len(policy['corruption'])==22
 for spec,c in zip(policy['corruption'],corrupt):
  assert c['spec']==spec;d=w/c['directory'];assert inventory(d)==c['closed_inventory']
  original=w/'oracle-fixtures'/('seed-candidate-32' if spec['damage']=='excess_chain' else 'seed-candidate-3');unchanged=inventory(original)
  if spec['damage']=='root_truncation':
   name='catalog-00000000000000000001.ks2';raw=(original/name).read_bytes();length=len(raw)//2 if spec['length']=='half' else len(raw)-1 if spec['length']=='last' else spec['length']
   assert (d/name).read_bytes()==raw[:length];unchanged.pop(name);assert {n:h for n,h in inventory(d).items() if n!=name}==unchanged
  elif spec['damage']=='excess_chain':
   name='catalog-00000000000000000033.ks2';body,tail=archive.envelope(d/name,b'KSQLCAT4');expected=json.loads((original/'catalog-00000000000000000032.ks2').read_bytes()[16:]);expected.update(generation=33,receipt_base=32,batches={'excess':{'digest':[0]*32,'rows':1,'generation':33}})
   assert body==expected and not tail and {n:h for n,h in inventory(d).items() if n!=name}==unchanged
  else:
   name='catalog-00000000000000000003.ks2';body=json.loads((original/name).read_bytes()[16:]);key,record=next(iter(body['batches'].items()));pair=json.dumps(key)+':'+json.dumps(record);raw=json.dumps(body).replace(json.dumps(body['batches']),'{'+pair+','+pair+'}',1).encode()
   assert (d/name).read_bytes()==b'KSQLCAT4'+struct.pack('<II',len(raw),zlib.crc32(raw))+raw;unchanged.pop(name);assert {n:h for n,h in inventory(d).items() if n!=name}==unchanged
  try:archive.metadata(d)
  except (AssertionError,ValueError,struct.error):pass
  else:raise AssertionError('damaged archive accepted by independent decoder')
  queries(c['cold_commands'],[],rejected=True)
 legacies=load(w/'oracle-legacy-results.json');assert [c['magic'] for c in legacies]==([] if failed else ['KSQLCAT2','KSQLCAT3'])
 for c in legacies:
  d=w/c['directory'];decoded=legacy_check(d,c['magic'].encode());assert decoded==c['decode'] and inventory(d)==c['closed_inventory']
  queries(c['cold_commands'],seed(3)[0]);r=command(c['oracle_command']);event=lines(w/r['stdout'])[-1]
  assert event['event']=='verified' and event['crc_bytes']==72 and event['stats']['recorded_batch_ids']==(3 if c['magic']=='KSQLCAT3' else 0)
 byte_cases=load(w/'oracle-byte-results.json');assert [(c['variant'],c['large']) for c in byte_cases]==([] if failed else list(itertools.product(['normal','candidate'],[False,True])));byte_results=[]
 for c in byte_cases:
  d=w/c['directory'];rows,receipts=byte_model(c['large']);decoded=brief(archive.check(d,rows,receipts));assert decoded==c['decode'] and inventory(d)==c['closed_inventory']
  for i in [c['create_command'],c['cross_reopen_command']]:
   r=command(i);event=lines(w/r['stdout'])[-1];assert event['rows']==len(rows) and event['receipts']==len(receipts) and event['original_generations_and_group_order_preserved'] and event['retry_collision_rejected'] and event['crc_scrubbed_bytes']==len(rows)*32
  queries(c['cold_commands'],rows,2);byte_results.append(decoded)
 if not failed:
  for large in [False,True]:assert next(c['closed_inventory'] for c in byte_cases if c['large']==large and c['variant']=='normal')==next(c['closed_inventory'] for c in byte_cases if c['large']==large and c['variant']=='candidate')
 assert sorted(used)==list(range(len(records))) and len(records)==proof['native_commands']==(633 if failed else 667)
 crc=sum(x['full_block_crc_bytes'] for x in seed_results)+sum(x['before']['full_block_crc_bytes']+x['after']['full_block_crc_bytes'] for x in results+source_results)+source_seed['decode']['full_block_crc_bytes']+sum(x['decode']['full_block_crc_bytes'] for x in legacies)+sum(x['full_block_crc_bytes'] for x in byte_results)
 return {'passed':True,'publication_fault_cases':72,'source_fault_cases':18,'corruption_cases':22,'legacy_formats':len(legacies),'normal_candidate_byte_fixtures':len(byte_cases),'exact_bytes_across_features':not failed,'aborted_fixture_setup_retained':failed,'complete_qualification':not failed,'native_commands':len(records),'full_reference_crc_bytes':crc,'native_launches':0,'performance_timer_launches':0,'publication':results,'source':source_results,'byte':byte_results}
if __name__=='__main__':
 w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-101');v=audit(w);p=w/'oracle-audit-proof-101.json';assert not p.exists();p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({k:x for k,x in v.items() if k not in ['publication','source','byte']}))
