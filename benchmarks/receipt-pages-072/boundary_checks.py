"""Additional independent malformed-file checks; preserve every rejected store."""
import hashlib,json,shutil,subprocess
from pathlib import Path
import oracle
W=Path(__file__).resolve().parent;EXE=W/'bin/receipt-page-model.exe'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not (W/'boundary-checks.json').exists()
assert json.loads((W/'qualification.json').read_text())['complete']
assert sha(EXE)==json.loads((W/'build-proof.json').read_text())['binary_sha256']
source=W/'fixtures/kill-root_published';records=[]
names=['root-count','root-page-size','root-slot','root-page-future','root-unknown-field','page-duplicate-ID','page-record-future','page-unknown-field','page-trailing','root-trailing','highest-root-corrupt','root-byte-budget']
for name in names:
    path=W/'fixtures'/('rejected-'+name);shutil.copytree(source,path)
    summary,ledger,root,refs=oracle.read_store(path);rp=path/f"root-{root['generation']:020}.model"
    if name.startswith('page-'):
        ref=root['pages'][0];pp=path/refs[0];page=oracle.document(oracle.envelope(pp,b'KPAG0721',256*1024))
        if name=='page-duplicate-ID':page['records'][1]=page['records'][0]
        elif name=='page-record-future':page['records'][0]['record']['generation']=ref['generation']+1
        elif name=='page-unknown-field':page['unexpected']=1
        if name=='page-trailing':pp.write_bytes(pp.read_bytes()+b'x')
        else:
            data=oracle.frame(b'KPAG0721',page);pp.write_bytes(data);ref['crc']=int.from_bytes(data[12:16],'little');rp.write_bytes(oracle.frame(b'KROT0721',root))
    elif name=='root-count':root['receipt_count']+=1;rp.write_bytes(oracle.frame(b'KROT0721',root))
    elif name=='root-page-size':root['page_size']=513;rp.write_bytes(oracle.frame(b'KROT0721',root))
    elif name=='root-slot':root['pages'][0]['slot']=195;rp.write_bytes(oracle.frame(b'KROT0721',root))
    elif name=='root-page-future':root['pages'][0]['generation']=root['generation']+1;rp.write_bytes(oracle.frame(b'KROT0721',root))
    elif name=='root-unknown-field':root['unexpected']=1;rp.write_bytes(oracle.frame(b'KROT0721',root))
    elif name=='root-trailing':rp.write_bytes(rp.read_bytes()+b'x')
    elif name=='highest-root-corrupt':(path/f"root-{root['generation']+1:020}.model").write_bytes(b'corrupt')
    elif name=='root-byte-budget':rp.write_bytes(b'x'*(512*1024+17))
    else:raise AssertionError(name)
    r=subprocess.run([str(EXE),'inspect',str(path)],capture_output=True,text=True,timeout=60)
    (W/'raw'/f'boundary-{name}-stdout.txt').write_text(r.stdout,encoding='utf-8');(W/'raw'/f'boundary-{name}-stderr.txt').write_text(r.stderr,encoding='utf-8')
    assert r.returncode!=0 and 'panicked' not in r.stderr,(name,r.stdout,r.stderr)
    try:oracle.read_store(path)
    except (AssertionError,ValueError,KeyError,FileNotFoundError) as err:reason=repr(err)
    else:raise AssertionError(('Python oracle accepted malformed file',name))
    records.append({'case':name,'native_rejected_without_panic':True,'independent_oracle_rejected':True,'native_exit':r.returncode,'python_reason':reason,'full_store_retained':str(path)})
(W/'boundary-checks.json').write_text(json.dumps({'complete':True,'model_only':True,'cases':records,'cases_passed':len(records)},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'independent_boundary_cases_passed':len(records)}))
