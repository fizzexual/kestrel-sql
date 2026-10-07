"""Independent bounded CAT4 model reader; no engine subprocess or file mutation."""
import hashlib,json,re
from pathlib import Path
import page_oracle as o
def ledger_sha(ledger):
    canonical={id:{'digest':r['digest'],'rows':r['rows'],'generation':r['generation']} for id,r in sorted(ledger.items())}
    return hashlib.sha256(json.dumps(canonical,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def read_catalog(path,generation=None):
    candidates=[int(p.name[8:28]) for p in path.iterdir() if re.fullmatch(r'catalog-[0-9]{20}\.model',p.name)];assert candidates
    latest=max(candidates) if generation is None else generation;assert latest in candidates and latest>0;g=latest;chain=[];ledger={};newest=None
    while True:
        assert len(chain)<32 and g>0
        v=o.document(o.envelope(path/f'catalog-{g:020}.model',b'KSQLCAT4',64*1024*1024));o.fields(v,'generation receipt_base table columns segments batches');o.schema(v)
        assert v['generation']==g;parent=v['receipt_base'];assert parent is None or (type(parent) is int and 0<parent<g)
        shape={k:v[k] for k in ['table','columns','segments']}
        if newest is None:newest=shape
        else:assert newest==shape
        for id,r in v['batches'].items():
            o.record(id,r,g);assert (parent is None or r['generation']==g) and id not in ledger and len(ledger)<100_000;ledger[id]=r
        chain.append(g)
        if parent is None:break
        g=parent
    return {'generation':latest,'receipts':len(ledger),'ledger_sha256':ledger_sha(ledger),'positions':o.positions(ledger),'history_files':len(chain)},ledger
def native_control_fixtures(w):
    checks=[]
    for p in sorted((w/'rust-temp').glob('cat073-*')):
        n=int(p.name.rsplit('-',1)[1]);store=p/'store';old=o.legacy(p/'input.ks2');expected=dict(old['batches'])
        if n in [14,15]:
            try:read_catalog(store)
            except (AssertionError,ValueError,KeyError):checks.append({'fixture':str(p),'invalid_native_fixture_rejected':True});continue
            raise AssertionError(('accepted invalid native control fixture',p))
        if n==12:
            for i in range(64):expected[f'new-{i:03}']=o.new_record(i,2,i+2)
        elif n==13:
            expected[o.source_id('feed',0,7)]=o.new_record(1,2,2)
            for i in range(32):expected[f'ordinary-{i}']=o.new_record(i,2,i+3)
        else:raise AssertionError(n)
        summary,ledger=read_catalog(store);assert ledger==expected,p
        checks.append({'fixture':str(p),'full_ledger_matches_independent_expected':True,**summary})
    return checks
