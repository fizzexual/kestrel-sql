"""Separate Python bounded reader and exact receipt/source oracle, model only."""
import hashlib, json, re, struct, zlib
from pathlib import Path
PAGE=512;MAX_IDS=100_000;MAX_PAGES=196
def unique(pairs):
    out={}
    for k,v in pairs:
        assert k not in out,('duplicate JSON key',k);out[k]=v
    return out
def document(b):return json.loads(b,object_pairs_hook=unique)
def fields(v,names):assert isinstance(v,dict) and set(v)==set(names.split()),(set(v),names)
def integer(v,lo,hi):assert type(v) is int and lo<=v<=hi,v
def envelope(p,magic,budget):
    assert 16<=p.stat().st_size<=budget+16,p
    with p.open('rb') as f:b=f.read(budget+17);assert f.read(1)==b'',p
    assert b[:8]==magic,p;size,crc=struct.unpack('<II',b[8:16]);assert 0<size<=budget and len(b)==16+size,p
    assert zlib.crc32(b[16:])==crc,p;return b[16:]
def record(id,r,g):
    assert re.fullmatch(r'[A-Za-z0-9_./:\-]{1,128}',id),id
    fields(r,'digest rows generation');integer(r['rows'],1,1_000_000);integer(r['generation'],1,g)
    assert isinstance(r['digest'],list) and len(r['digest'])==32
    for b in r['digest']:integer(b,0,255)
def schema(v):
    assert re.fullmatch('[a-z_][a-z_0-9]{0,63}',v['table'])
    cols=v['columns'];assert 1<=len(cols)<=64 and len(set(cols))==len(cols)
    assert all(re.fullmatch('[a-z_][a-z_0-9]{0,63}',s) for s in cols)
    segs=v['segments'];assert len(segs)<=10_000 and len(set(segs))==len(segs)
    assert all(re.fullmatch(r'segment-[0-9]{20}\.ks2',s) and int(s[8:28])>0 for s in segs)
def source_key(s):return hashlib.sha256(b'kestrelsql.source.v1\0'+s.encode()).hexdigest()
def source_id(s,start,next):return f'ksrc1:{source_key(s)}:{start:016x}:{next:016x}'
def positions(ledger):
    out={}
    for id,r in sorted(ledger.items()):
        if not id.startswith('ksrc1:'):continue
        m=re.fullmatch(r'ksrc1:([0-9a-f]{64}):([0-9a-f]{16}):([0-9a-f]{16})',id);assert m,id
        key,start,next=m.groups();start=int(start,16);next=int(next,16);assert next>start
        if key in out:
            p=out[key];assert p['next_offset']==start and r['generation']>p['last_generation'],id
            p.update(next_offset=next,last_generation=r['generation'],committed_batches=p['committed_batches']+1)
        else:
            assert len(out)<4096;out[key]={'first_offset':start,'next_offset':next,'last_generation':r['generation'],'committed_batches':1}
    return out
def legacy(p):
    v=document(envelope(p,b'KSQLCAT4',64*1024*1024));fields(v,'generation receipt_base table columns segments batches');schema(v)
    integer(v['generation'],1,2**64-2);assert v['receipt_base'] is None and len(v['batches'])<=MAX_IDS
    for id,r in v['batches'].items():record(id,r,v['generation'])
    positions(v['batches']);return v
def read_store(path):
    roots=[];next=1
    for p in path.iterdir():
        m=re.fullmatch(r'root-([0-9]{20})\.model',p.name)
        if m:roots.append(int(m[1]))
        m=re.fullmatch(r'root-([0-9]{20})\.(model|pending)',p.name) or re.fullmatch(r'receipts-([0-9]{20})-([0-9]{3})\.model',p.name)
        if m:next=max(next,int(m[1])+1)
    assert roots and max(roots)>0;g=max(roots);integer(next,1,2**64-1)
    root=document(envelope(path/f'root-{g:020}.model',b'KROT0721',512*1024))
    fields(root,'generation table columns segments page_size receipt_count pages');schema(root)
    assert root['generation']==g and root['page_size']==PAGE;integer(root['receipt_count'],0,MAX_IDS)
    refs=root['pages'];assert len(refs)==(root['receipt_count']+PAGE-1)//PAGE<=MAX_PAGES
    ledger={};referenced=[]
    for slot,r in enumerate(refs):
        fields(r,'generation slot count crc');integer(r['generation'],1,g);integer(r['count'],1,PAGE);integer(r['crc'],0,2**32-1)
        assert r['slot']==slot and (slot==len(refs)-1 or r['count']==PAGE)
        p=path/f"receipts-{r['generation']:020}-{slot:03}.model";data=envelope(p,b'KPAG0721',256*1024);assert zlib.crc32(data)==r['crc']
        page=document(data);fields(page,'generation slot records');assert page['generation']==r['generation'] and page['slot']==slot and len(page['records'])==r['count']
        for e in page['records']:
            fields(e,'id record');record(e['id'],e['record'],r['generation']);assert e['id'] not in ledger;ledger[e['id']]=e['record']
        referenced.append(p.name)
    assert len(ledger)==root['receipt_count'];pos=positions(ledger)
    canonical={id:{'digest':r['digest'],'rows':r['rows'],'generation':r['generation']} for id,r in sorted(ledger.items())}
    digest=hashlib.sha256(json.dumps(canonical,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    return {'generation':g,'next_generation':next,'receipts':len(ledger),'pages':len(refs),'ledger_sha256':digest,'positions':pos},ledger,root,referenced
def fixture(sequence,width):return [[sequence*100+col*10+row for row in range(7)] for col in range(width)]
def digest(cols):
    data=struct.pack('<QQ',len(cols),len(cols[0]))+b''.join(struct.pack('<q',n) for col in cols for n in col)
    return list(hashlib.sha256(data).digest())
def new_record(sequence,width,g):return {'digest':digest(fixture(sequence,width)),'rows':7,'generation':g}
def frame(magic,v):
    b=json.dumps(v,separators=(',',':')).encode();return magic+struct.pack('<II',len(b),zlib.crc32(b))+b
