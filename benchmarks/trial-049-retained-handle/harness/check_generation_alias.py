"""Post-timing semantic probe; never run alongside a timed workload."""
from pathlib import Path
import json,struct,zlib,hashlib,shutil
from stress_compare import Engine
w=Path(__file__).resolve().parents[1];root=w.parents[1]/'outputs/kestrel-sql'
out=w/'generation-alias-probe.json';assert not out.exists()
trial=w/'bin/kestrel-stress.exe';old=root/'bin/baseline-0.3.16/kestrel-stress.exe'
a=w/'alias-bundle';b=w/'alias-legacy'
e=Engine('kestrel',a,0,trial,{});c=e.connect()
c.call({'op':'append','id':'a','data':[[i,1,1] for i in range(512)]})
c.call({'op':'append','id':'c','data':[[1000,3,1]]});c.close();e.finish()
e=Engine('kestrel',b,0,old,{});c=e.connect();c.call({'op':'append','id':'b','data':[[i,9,1] for i in range(512)]});c.close();e.finish()
shutil.copy2(b/'archive/segment-00000000000000000001.ks2',a/'archive/segment-00000000000000000001.ks2')
p=a/'archive/catalog-00000000000000000002.ks2';raw=p.read_bytes();end=16+struct.unpack('<I',raw[8:12])[0];body=json.loads(raw[16:end]);body['segments'].insert(1,'segment-00000000000000000001.ks2');data=json.dumps(body,separators=(',',':')).encode();p.write_bytes(b'KSQLCAT5'+struct.pack('<II',len(data),zlib.crc32(data))+data+raw[end:])
proof={'case':'checksummed restore mixes two physical file kinds with identical generation 1','expected_partial_sum':2000,'expected_full_sum':5120+3,'fixture':str(a),'trial_sha256':hashlib.sha256(trial.read_bytes()).hexdigest(),'started':True}
try:
    e=Engine('kestrel',a,0,trial,{},existing=True)
except Exception as error:
    proof.update(rejected_at_open=True,error=repr(error))
else:
    c=e.connect()
    try:
        proof['partial_sum']=c.query('SELECT SUM(value) FROM events WHERE ts >= 100 AND ts < 300')
        proof['full_sum']=c.query('SELECT SUM(value) FROM events')
        proof['verified_bytes']=c.call({'op':'verify'})['verified_bytes']
        proof['accepted_wrong_partial_sum']=proof['partial_sum']!=[[2000]]
        proof['rejected_at_open']=False
    finally:c.close();e.finish()
out.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
