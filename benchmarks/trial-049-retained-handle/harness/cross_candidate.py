from pathlib import Path
import json,hashlib
from stress_compare import Engine
from source_pipeline_demo import Adapter
w=Path(__file__).resolve().parents[1];prev=w.parent/'perf-048/bin';curr=w/'bin'
out=w/'cross-candidate.json';assert not out.exists();cases=[]
for initial,next_bin in [(prev,curr),(curr,prev)]:
    label='048-to-049' if initial==prev else '049-to-048';directory=w/('cross-'+label)
    e=Engine('kestrel',directory,0,initial/'kestrel-stress.exe',{},bridge_args=(0,1));c=e.connect()
    first=c.call({'op':'append','id':'first','data':[[1,7,2],[0,-5,1]]});assert first['generation']==1;c.close();e.finish()
    e=Engine('kestrel',directory,0,next_bin/'kestrel-stress.exe',{},existing=True,bridge_args=(0,1));c=e.connect()
    assert c.call({'op':'append','id':'first','data':[[1,7,2],[0,-5,1]]})['duplicate']
    second=c.call({'op':'append','id':'second','data':[[2,11,3]]});assert not second['duplicate'];c.close();e.finish()
    e=Engine('kestrel',directory,0,initial/'kestrel-stress.exe',{},existing=True,bridge_args=(0,1));c=e.connect()
    replay=c.call({'op':'append','id':'second','data':[[2,11,3]]});assert replay['duplicate'] and replay['generation']==second['generation']
    assert c.query('SELECT COUNT(*), SUM(value) FROM events')==[[3,13]];assert c.call({'op':'verify'})['verified_bytes']==72;c.close();e.finish()
    source_dir=w/('cross-source-'+label);a=Adapter(initial/'source-pipeline.exe',source_dir)
    first=a.call(op='commit',source='cross:partition',start=500,next=600,columns=[[0]*100,[7]*100,[1]*100]);a.finish()
    a=Adapter(next_bin/'source-pipeline.exe',source_dir);assert a.call(op='position',source='cross:partition')['next_offset']==600
    second=a.call(op='commit',source='cross:partition',start=600,next=700,columns=[[1]*100,[11]*100,[1]*100]);a.finish()
    a=Adapter(initial/'source-pipeline.exe',source_dir)
    assert a.call(op='position',source='cross:partition')['next_offset']==700
    replay=a.call(op='commit',source='cross:partition',start=600,next=700,columns=[[1]*100,[11]*100,[1]*100]);assert replay['duplicate'] and replay['generation']==second['generation']
    assert a.call(op='query',sql='SELECT COUNT(*), SUM(value) FROM events')==[[200,1800]];assert a.call(op='verify')==4800;a.finish()
    cases.append({'direction':label,'identified_retries_and_cold_reopens':True,'source_output_and_position_match':True,'crc_bytes':72+4800})
out.write_text(json.dumps({'cases':cases,'binary_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [prev/'kestrel-stress.exe',curr/'kestrel-stress.exe',prev/'source-pipeline.exe',curr/'source-pipeline.exe']},'passed':True},indent=2)+'\n',encoding='utf-8');print('Both CAT5 cross-candidate directions preserve data, receipts and source positions')
