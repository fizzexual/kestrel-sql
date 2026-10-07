"""Compare exact retained files and reopen dev67 stores with released code."""
from datetime import datetime, timezone
import hashlib, json, subprocess
from pathlib import Path
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert not (W/'byte-equivalence.json').exists()
D=W/'byte-fixtures';D.mkdir();records=[]
cases=[]
for size in ['sequence','oversized']:
    cases.extend((label,D/f'{store}-{size}',reopen,size) for label,store,reopen in [('baseline','baseline',False),('candidate','candidate',False),('baseline','candidate',True),('candidate','baseline',True)])
for label,store,reopen,size in cases:
    prefix=f'{label}-{store.name}-{reopen}'
    argv=[str(W/'native-binaries'/f'{label}-byte.exe'),str(store),*(['reopen'] if reopen else []),*(['oversized'] if size=='oversized' else [])]
    r=subprocess.run(argv,text=True,capture_output=True,timeout=180)
    (D/(prefix+'.stdout.json')).write_text(r.stdout,encoding='utf-8');(D/(prefix+'.stderr.txt')).write_text(r.stderr,encoding='utf-8')
    record={'argv':argv,'exit':r.returncode,'binary_sha256':sha(Path(argv[0])),'utc':datetime.now(timezone.utc).isoformat()}
    save(D/(prefix+'.status.json'),record);records.append(record)
    assert r.returncode==0,(prefix,r.stderr)
    x=json.loads(r.stdout);assert all(x[n] for n in ['sql_exact','original_generations_and_group_order_preserved','retry_collision_rejected'])
    assert x['rows']==x['receipts']==(74 if size=='sequence' else 70001) and x['generation']==(74 if size=='sequence' else 2)
    if not reopen and size=='sequence': assert x['checkpoints']>=3 and x['deltas']>=60
inventory=[]
for size in ['sequence','oversized']:
    a={p.name:p for p in (D/f'baseline-{size}').glob('*.ks2')};b={p.name:p for p in (D/f'candidate-{size}').glob('*.ks2')}
    assert a.keys()==b.keys()
    if size=='oversized': assert max(p.stat().st_size for n,p in a.items() if n.startswith('catalog-')) > 16*1024*1024
    for n in sorted(a):
        assert a[n].read_bytes()==b[n].read_bytes(),n
        inventory.append({'name':n,'case':size,'size':a[n].stat().st_size,'sha256':sha(a[n])})
out={'passed':True,'utc':datetime.now(timezone.utc).isoformat(),'archives_byte_identical':True,
    'released_reopen_candidate_passed':True,'candidate_reopen_released_passed':True,'records':records,'files':inventory,
    'catalogs_compared':sum(f['name'].startswith('catalog-') for f in inventory),'segments_compared':sum(f['name'].startswith('segment-') for f in inventory),
    'oversized_valid_catalogs_passed':True,'long_id_receipts':70001,
    'excluded_from_performance_timers':True,'full_files_retained':True}
save(W/'byte-equivalence.json',out)
print(json.dumps({k:v for k,v in out.items() if k not in ['records','files']}))
