from pathlib import Path
import json,struct,zlib,hashlib,subprocess,time
from stress_compare import Engine
w=Path(__file__).resolve().parents[1];root=w.parents[1]/'outputs/kestrel-sql'
old=root/'bin/baseline-0.3.16/kestrel-stress.exe';new=w/'bin/kestrel-stress.exe'
out=w/'compatibility.json';assert not out.exists();cases=[]
for version in [2,3,4]:
    directory=w/f'compatibility-cat{version}';engine=Engine('kestrel',directory,0,old,{})
    c=engine.connect();r=c.call({'op':'append','id':'old:receipt','data':[[0,3,1],[1,5,2]]});assert r['generation']==1;c.close();engine.finish()
    catalog=directory/'archive/catalog-00000000000000000001.ks2'; raw=catalog.read_bytes();body=json.loads(raw[16:])
    if version<4:
        body.pop('generation');body.pop('receipt_base')
        if version==2:body.pop('batches')
        data=json.dumps(body,separators=(',',':')).encode();catalog.write_bytes(f'KSQLCAT{version}'.encode()+struct.pack('<II',len(data),zlib.crc32(data))+data)
    # Confirm the generated legacy fixture is valid in the frozen old reader.
    engine=Engine('kestrel',directory,0,old,{},existing=True);c=engine.connect();assert c.query('SELECT COUNT(*), SUM(value) FROM events')==[[2,8]];c.close();engine.finish()
    segment=directory/'archive/segment-00000000000000000001.ks2';before=hashlib.sha256(segment.read_bytes()).hexdigest()
    engine=Engine('kestrel',directory,0,new,{},existing=True);c=engine.connect();assert c.query('SELECT COUNT(*), SUM(value) FROM events')==[[2,8]]
    if version>=3: assert c.call({'op':'append','id':'old:receipt','data':[[0,3,1],[1,5,2]]})['duplicate']
    assert not c.call({'op':'append','id':'new:receipt','data':[[2,7,3]]})['duplicate']
    assert c.query('SELECT COUNT(*), SUM(value) FROM events')==[[3,15]];assert c.call({'op':'verify'})['verified_bytes']==72;c.close();engine.finish()
    assert hashlib.sha256(segment.read_bytes()).hexdigest()==before
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (directory/'archive').iterdir() if p.is_file()}
    rejected=subprocess.run([str(root/'bin/baseline-0.3.16/kestrel.exe'),'--archive',str(directory/'archive'),'--sql','SELECT COUNT(*) FROM events'],text=True,capture_output=True,timeout=30)
    assert rejected.returncode!=0,rejected
    assert files=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (directory/'archive').iterdir() if p.is_file()}
    cases.append({'legacy_format':version,'frozen_old_reader_accepted_legacy':True,'trial_read_and_upgrade':True,'old_data_bytes_unchanged':True,'full_scrub_bytes':72,'old_writer_rejected_upgrade_without_file_changes':True,'rejection':rejected.stderr.strip()})
out.write_text(json.dumps({'trial':'CAT5 development trial','cases':cases,'passed':True},indent=2)+'\n',encoding='utf-8');print('CAT2/CAT3/CAT4 mixed upgrades and frozen old-version rejection passed')
