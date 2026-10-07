"""Verify every duplicate 062/063 store byte against its published full archive."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W/'prior-store-archive-plan.json').exists()
plans=[]
for number,prefix,directories in [(62,'service-calibration-062',[('service-fixtures',27)]),(63,'batching-063',[('service-fixtures',32),('recovery-fixtures',24)])]:
    previous=W.parent/f'perf-{number:03}'
    bundle=load(ROOT/f'benchmarks/{prefix}-bundle-check.json')
    publication=load(ROOT/f'benchmarks/{prefix}-publication.json')
    archive=ROOT.parent/bundle['artifact']
    assert sha(archive)==bundle['sha256']
    asset=next(a for a in publication['new_assets'] if a['name']==archive.name)
    assert asset['server_digest_matched'] and asset['sha256']==bundle['sha256']
    assert not load(previous/'post-qualification-process-check.json')['active_processes']
    inventory=load(previous/'fixture-inventory.json')
    with zipfile.ZipFile(archive) as z:
        for name,count in directories:
            target=(previous/name).resolve()
            assert target.is_relative_to(previous.resolve()) and target.name==name
            expected={n:d for n,d in inventory.items() if n.startswith(name+'/')}
            actual={p.relative_to(previous).as_posix() for p in target.rglob('*') if p.is_file()}
            assert actual==set(expected)
            assert len(list(target.iterdir()))==count
            assert not any(p.is_symlink() or p.is_junction() for p in target.rglob('*'))
            total=0
            for n,d in expected.items():
                p=previous/n
                assert p.resolve().is_relative_to(target) and p.stat().st_size==d['bytes'] and sha(p)==d['sha256']
                member='kestrel-sql/benchmarks/'+prefix+'/'+n
                assert z.getinfo(member).file_size==d['bytes']
                with z.open(member) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d['sha256']
                total+=d['bytes']
            plans.append({'directory':str(target),'task_directory':str(previous.resolve()),'store_count':count,'files':len(expected),
                'uncompressed_bytes':total,'archive':str(archive),'archive_sha256':bundle['sha256'],
                'private_release_url':asset['download_url'],'restore_member_prefix':'kestrel-sql/benchmarks/'+prefix+'/'+name+'/',
                'each_file_size_crc_sha256_matches_local_and_published_archive':True})
proof={'checked_utc':datetime.now(timezone.utc).isoformat(),'directories':plans,
    'all_raw_results_sources_binaries_failed_attempts_and_full_stores_retained':True,'removal_not_yet_performed':True}
(W/'prior-store-archive-plan.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verified_files':sum(p['files'] for p in plans),'duplicate_bytes':sum(p['uncompressed_bytes'] for p in plans)}))
