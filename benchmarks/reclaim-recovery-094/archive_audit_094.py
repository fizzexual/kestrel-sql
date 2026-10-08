"""Independent complete catalog-chain, receipt digest and block/row audit; no Native calls."""
import hashlib,json,struct,zlib
import numpy as np
def unique(pairs):
 d={}
 for k,v in pairs:
  assert k not in d,('duplicate JSON key',k)
  d[k]=v
 return d
def envelope(path,signature):
 b=path.read_bytes();assert b[:8]==signature and len(b)>=16
 size,crc=struct.unpack_from('<II',b,8);raw=b[16:16+size]
 assert len(raw)==size and zlib.crc32(raw)==crc
 return json.loads(raw,object_pairs_hook=unique),b[16+size:]
def digest(rows):
 x=np.array(rows,dtype='<i8').T.copy()
 return list(hashlib.sha256(struct.pack('<QQ',3,len(rows))+x.tobytes()).digest())
def check(directory,reference,expected_receipts):
 cats={int(p.name[8:28]):p for p in directory.glob('catalog-*.ks2')};assert cats
 generation=max(cats);head_generation=generation;head=None;chain=[];receipts={}
 while True:
  assert len(chain)<32 and generation not in chain
  body,tail=envelope(cats[generation],b'KSQLCAT4');assert not tail
  assert body['generation']==generation and body['table']=='events' and body['columns']==['ts','value','device']
  parent=body['receipt_base'];assert parent is None or 0<parent<generation
  assert len(set(body['segments']))==len(body['segments'])
  for key,rec in body['batches'].items():
   assert key not in receipts and 0<rec['generation']<=generation and rec['rows']>0
   assert parent is None or rec['generation']==generation
   receipts[key]=rec
  chain.append(generation)
  if head is None:head=body
  if parent is None:break
  generation=parent
 assert set(receipts)==set(expected_receipts)
 for key,(rows,gen) in expected_receipts.items():
  r=receipts[key];assert r['rows']==len(rows) and r['digest']==digest(rows)
  if gen is not None:assert r['generation']==gen
 parts=[];checked=0
 for name in head['segments']:
  assert name.startswith('segment-') and name.endswith('.ks2') and len(name)==32
  meta,payload=envelope(directory/name,b'KSQLSEG2');n=meta['rows']
  assert n>0 and len(payload)==n*24 and len(meta['indexes'])==3
  cols=np.frombuffer(payload,dtype='<i8').reshape((3,n))
  for column,index in zip(cols,meta['indexes']):
   blocks=(n+4095)//4096
   assert index['prefix'][0]==0 and len(index['prefix'])==blocks+1
   assert all(len(index[x])==blocks for x in ['crc','last','block_min','block_max'])
   assert index['min']==int(column.min()) and index['max']==int(column.max())
   prefix=0
   for bi,lo in enumerate(range(0,n,4096)):
    block=column[lo:lo+4096];checked+=len(block)*8
    assert zlib.crc32(block.tobytes())==index['crc'][bi]
    prefix+=sum(map(int,block));assert prefix==index['prefix'][bi+1]
    assert [int(block[-1]),int(block.min()),int(block.max())]==[index['last'][bi],index['block_min'][bi],index['block_max'][bi]]
  parts.append(cols)
 actual=np.concatenate(parts,axis=1);ref=np.array(reference,dtype=np.int64).T
 assert actual.shape==ref.shape and checked==len(reference)*24
 ai=np.lexsort((actual[2],actual[1],actual[0]));ri=np.lexsort((ref[2],ref[1],ref[0]))
 assert np.array_equal(actual[:,ai],ref[:,ri])
 return {'head':head_generation,'chain':chain,'segments':head['segments'],'receipts':receipts,'rows':len(reference),'full_block_crc_bytes':checked,'complete_numpy_row_multiset':True}
def maintenance_reference(history):
 rows=[[i,2*i,i%97] for i in range(6400)]
 receipts={f'seed:{g}':(rows[g*100:(g+1)*100],g+1) for g in range(64)} if history=='named' else {}
 return rows,receipts
def publication_reference(scenario):
 count=32 if 'checkpoint' in scenario else 3
 rows=[[i,i*2,1] for i in range(count)]
 receipts={f'seed:{i}':([rows[i]],i+1) for i in range(count)}
 if scenario.startswith('append'):
  target=[[1000,7,1]]*10000;rows+=target;receipts['fault:target']=(target,None)
 return rows,receipts
def live_reference():
 known=[[1000,3,1]]*100;target=[[1000,7,1]]*100
 return known+target,{'known':(known,1),'target':(target,None)}
