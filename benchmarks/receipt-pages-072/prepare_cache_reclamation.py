"""Verify only task-owned, tagged compiler caches; retain every raw fixture/ZIP."""
from datetime import datetime, timezone
import hashlib,json,os,zipfile
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';OUT=ROOT.parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W/'cache-reclamation-plan.json').exists()
pub=load(ROOT/'repository-publication.json');assets={a['name']:a for r in pub['releases'] for a in r['assets']};assert len(assets)==114
archives={};targets=[]
for n in [69,70,71]:
    old=W.parent/f'perf-{n:03}';cache=old/'build-cache';assert cache.resolve().parent==old.resolve() and cache.name=='build-cache'
    assert (cache/'CACHEDIR.TAG').read_text().startswith('Signature: 8a477f597d28d172789f06886806bc55')
    assert not cache.is_symlink() and not any(p.is_symlink() or (p.stat().st_file_attributes & 1024) for p in cache.rglob('*'))
    build=load(old/'build-proof.json');binary=old/'bin/checkpoint-model.exe';assert sha(binary)==build['binary_sha256']
    for rel,d in build['source_sha256'].items():assert sha(old/'model'/rel)==d
    bundle=load(ROOT/f'benchmarks/compression-{n:03}-bundle-check.json');parts=bundle.get('artifacts',[bundle])
    for part in parts:
        path=OUT/part['artifact'];digest=sha(path);assert digest==part['sha256']==assets[path.name]['sha256'] and path.stat().st_size==assets[path.name]['bytes']
        archives[path.name]={'bytes':path.stat().st_size,'sha256':digest,'private_server_digest_record_matches':True}
    core=next((p for p in parts if 'core' in p['artifact']),parts[0]);archive=OUT/core['artifact']
    with zipfile.ZipFile(archive) as z:
        prefix=f'kestrel-sql/benchmarks/compression-{n:03}/'
        for rel,d in {'bin/checkpoint-model.exe':build['binary_sha256'],**{'model/'+rel:d for rel,d in build['source_sha256'].items()}}.items():
            with z.open(prefix+rel) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d,rel
    files={p.relative_to(cache).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in cache.rglob('*') if p.is_file()}
    targets.append({'path':str(cache.resolve()),'trial':n,'bytes':sum(f['bytes'] for f in files.values()),'files':files,'frozen_binary_sha256':sha(binary),
        'sources_binary_and_full_archives_verified':True,'only_tagged_compiler_cache':True})
    print('verified compiler cache',n,flush=True)
proof={'prepared_utc':datetime.now(timezone.utc).isoformat(),'targets':targets,'archives_verified':archives,'total_bytes':sum(t['bytes'] for t in targets),
    'no_raw_fixtures_reports_inputs_bins_source_or_archives_to_delete':True,'not_current_072_cache':True}
(W/'cache-reclamation-plan.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verified':True,'target_count':len(targets),'bytes':proof['total_bytes'],'full_archives_verified':len(archives)}))
