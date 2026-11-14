"""Independent exact reference/current-chain/receipts/CRC audit for width 2 or 3."""
from pathlib import Path
import hashlib,json,struct,zlib
import numpy as np
def unique(pairs):
 d={}
 for k,v in pairs:assert k not in d,('duplicate JSON',k);d[k]=v
 return d
def envelope(p,magic):
 b=p.read_bytes();assert b[:8]==magic and len(b)>=16
 size,crc=struct.unpack_from('<II',b,8);assert size<=64*1024*1024
 raw=b[16:16+size];assert len(raw)==size and zlib.crc32(raw)==crc
 return json.loads(raw,object_pairs_hook=unique),b[16+size:]
def metadata(directory):
 cats={int(p.name[8:28]):p for p in directory.glob('catalog-*.ks2') if p.is_file()};assert cats
 generation=max(cats);head_generation=generation;head=None;chain=[];receipts={}
 while True:
  assert len(chain)<32 and generation not in chain
  body,tail=envelope(cats[generation],b'KSQLCAT4');assert not tail and body['generation']==generation
  assert body['table']=='events' and body['columns'] in [['ts','value'],['ts','value','device'],['ts','value','kind']]
  parent=body['receipt_base'];assert parent is None or 0<parent<generation
  assert len(set(body['segments']))==len(body['segments'])
  for key,r in body['batches'].items():
   assert key not in receipts and 0<r['generation']<=generation and r['rows']>0
   assert parent is None or r['generation']==generation;receipts[key]=r
  chain.append(generation)
  if head is None:head=body
  if parent is None:break
  generation=parent
 return head_generation,head,chain,receipts
def digest(rows):
 x=np.array(rows,dtype='<i8').T.copy();return list(hashlib.sha256(struct.pack('<QQ',x.shape[0],len(rows))+x.tobytes()).digest())
def check(directory,reference,expected_receipts):
 head_generation,head,chain,receipts=metadata(directory);width=len(head['columns'])
 assert set(receipts)==set(expected_receipts)
 for key,(rows,generation) in expected_receipts.items():
  r=receipts[key];assert r['rows']==len(rows) and r['digest']==digest(rows)
  assert r['generation']==generation
 parts=[];checked=0
 for name in head['segments']:
  assert name.startswith('segment-') and name.endswith('.ks2') and len(name)==32
  meta,payload=envelope(directory/name,b'KSQLSEG2');n=meta['rows'];assert n>0 and len(payload)==n*width*8 and len(meta['indexes'])==width
  cols=np.frombuffer(payload,dtype='<i8').reshape((width,n))
  for col,index in zip(cols,meta['indexes']):
   assert type(index['monotonic']) is bool and index['monotonic']==bool(np.all(col[1:]>=col[:-1]))
   blocks=(n+4095)//4096;assert index['prefix'][0]==0 and len(index['prefix'])==blocks+1
   assert all(len(index[k])==blocks for k in ['crc','last','block_min','block_max']);assert index['min']==int(col.min()) and index['max']==int(col.max())
   prefix=0
   for bi,lo in enumerate(range(0,n,4096)):
    block=col[lo:lo+4096];checked+=len(block)*8;assert zlib.crc32(block.tobytes())==index['crc'][bi]
    prefix+=sum(map(int,block));assert prefix==index['prefix'][bi+1]
    assert [int(block[-1]),int(block.min()),int(block.max())]==[index['last'][bi],index['block_min'][bi],index['block_max'][bi]]
  parts.append(cols)
 actual=np.concatenate(parts,axis=1);ref=np.array(reference,dtype=np.int64).T
 assert actual.shape==ref.shape and checked==len(reference)*width*8
 ai=np.lexsort(tuple(actual[i] for i in range(width-1,-1,-1)));ri=np.lexsort(tuple(ref[i] for i in range(width-1,-1,-1)))
 assert np.array_equal(actual[:,ai],ref[:,ri])
 return {'head':head_generation,'chain':chain,'segments':head['segments'],'receipts':receipts,'rows':len(reference),'full_block_crc_bytes':checked,'complete_numpy_row_multiset':True}
