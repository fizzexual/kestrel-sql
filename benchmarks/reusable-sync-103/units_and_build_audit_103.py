"""Independent build provenance, preserved paths and every owned unit-store reference."""
from pathlib import Path
import collections, hashlib, json, re, sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import archive_audit_099 as archive
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def check_build(w):
    policy=load(w/'policy.json');build=load(w/'build-proof.json');d=load(w/'source-derivation-v3.json')
    assert sha(w/'policy.json')==load(w/'declaration-proof.json')['policy_sha256']=='1cd0b07775b43ec6e114a1bac7b4f0ddb88088b2001e6e83bceb9e77c5050aa2'
    for directory,expected in [('source',policy['basis']['all_42_source_hashes']),('source-v2',d['previous']),('source-v3',d['final'])]:
        assert {p.relative_to(w/directory).as_posix():sha(p) for p in (w/directory).rglob('*') if p.is_file()}==expected
    original=(w/'source/src/archive.rs').read_bytes();current=(w/'source-v3/src/archive.rs').read_bytes()
    a=original.index(b'    fn publish(');b=original.index(b'    #[cfg(feature = "parallel-sync-101")]',a)
    c=original.index(b'    fn publish(',b);e=original.index(b'    /// Merge up to 32',c)
    assert original[a:b] in current and original[c:e] in current
    assert hashlib.sha256(original[a:b]).hexdigest()==d['normal_publication_body_sha256']=='7a260c1a0269fbd0b0d9cedf6d163fdac0f2e5a153a04d9e0e58054927be01a0'
    assert hashlib.sha256(original[c:e]).hexdigest()==d['existing101_publication_body_sha256']
    assert build['complete'] and build['normal_existing101_candidate_profile_exclude_fault_and_test_hooks'] and build['strict_lint_modes']==6
    assert all(r['returncode']==0 and sha(w/r['log'])==r['log_sha256'] for r in build['records'])
    assert sum(r.get('tests_passed',0) for r in build['records'])==build['fresh_native_test_executions']
    assert len([r for r in build['records'] if 'tests_passed' in r])==9
    assert all(sha(w/n)==h for n,h in build['binaries'].items())
    aux=load(w/'oracle-artifacts-proof.json');assert aux['complete'] and aux['source']==d['final']
    assert len(aux['records'])==3 and all(r['returncode']==0 and sha(w/r['log'])==r['log_sha256'] for r in aux['records'])
    assert all(sha(w/n)==h for n,h in aux['binaries'].items())
    assert load(w/'failed-preparation-v1/proof.json')['before_candidate_source_write_build_or_native']
    first=load(w/'build-failure.json')
    assert first['records'][-1]['step']=='candidate-lint' and first['records'][-1]['returncode']!=0
    assert sum(r.get('tests_passed',0) for r in first['records'])==916
    assert all(sha(w/r['log'])==r['log_sha256'] for r in first['records'])
    assert sha(w/'build-controller-v1.log')==d['closed_first_controller_log_sha256']
    return build
def audit_units(w):
    units=[];labels=collections.Counter();eq_receipts=[]
    roots=[w/'cargo-tests',w/'cargo-tests-v3']
    for p in sorted(p for root in roots for p in root.rglob('async-096-*')):
        if not p.is_dir():continue
        m=re.fullmatch(r'async-096-(.+)-(\d+)-(\d+)',p.name);assert m;label=m.group(1)
        for directory in ([p/'full',p/'worker'] if label=='equivalence' else [p]):
            n=65 if label in ['bound','progress'] else 2 if label=='filesystem' else 66 if label=='source' else 64
            rows=[[j,2*j] for j in range(64)]+[[100,9],[-1,11]] if label=='source' else [[j,2*j] for j in range(n)]
            _,_,_,existing=archive.metadata(directory);receipts={}
            if label in ['equivalence','source'] and (label=='source' or existing):
                receipts={f'id:{j}':([[j,2*j]],j+1) for j in range(64)}
                if label=='source':
                    key=hashlib.sha256(b'kestrelsql.source.v1\0orders').hexdigest()
                    receipts[f'ksrc1:{key}:{100:016x}:{200:016x}']=([[100,9],[-1,11]],66)
            if label=='equivalence':eq_receipts.append(len(existing))
            decoded=archive.check(directory,rows,receipts);labels[label]+=1
            units.append({'directory':directory.relative_to(w).as_posix(),'label':label,'decode':decoded})
    assert len(units)==342 and labels['equivalence']==72 and labels['progress']==144
    assert sorted(eq_receipts)==[0]*36+[64]*36
    overlap=[]
    for prefix,count in [('parallel-101-',28),('reusable-103-',120)]:
        current=[]
        for p in sorted(p for root in roots for p in root.rglob(prefix+'*')):
            if not p.is_dir():continue
            m=re.fullmatch(re.escape(prefix)+r'(.+)-(\d+)',p.name);assert m;label=m.group(1)
            if label=='archive-reuse':
                rows=[[j,2*j] for j in range(1,9)]
                receipts={f'group-{j}':([[j,2*j]],j) for j in range(1,9)}
            else:
                succeeds=label in ['catalog-first','segment-first'];rows=[[1,2],[3,6]]+([[0,0],[2,4]] if succeeds else [])
                receipts={'first':([[3,6],[1,2]],1)}
                if succeeds:receipts['second']=([[2,4],[0,0]],2)
            decoded=archive.check(p,rows,receipts)
            current.append({'directory':p.relative_to(w).as_posix(),'label':label,'decode':decoded})
        assert len(current)==count,(prefix,len(current));overlap+=current
    raw=[]
    for p in sorted(p for root in roots for p in root.rglob('worker-103-*')):
        if not p.is_dir():continue
        assert {x.name for x in p.iterdir()}=={'lease','segment'}
        assert (p/'lease').read_bytes()==b'' and (p/'segment').read_bytes()==b'original owned handle'
        raw.append({'directory':p.relative_to(w).as_posix(),'files':{x.name:sha(x) for x in p.iterdir()}})
    assert len(raw)==30
    return units,overlap,raw
