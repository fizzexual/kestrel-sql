"""Verify076 full local/private-Git archive and122 release digests before cache deletion."""
import hashlib,json,shutil,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-076';ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
completion=load(ROOT/'benchmarks/anchor-reuse-076-finalization/completion.json')
for a in completion['repository_artifacts']:
    p=ROOT/a['repository_path'];assert sha(p)==a['sha256'] and p.stat().st_size==a['bytes']
    assert subprocess.check_output(['git','hash-object','--no-filters',str(p)],text=True).strip()==a['git_blob_sha']
pub=load(ROOT/'repository-publication.json');expected={(r['tag'],a['name']):a for r in pub['releases'] for a in r['assets']};assert len(expected)==122
releases=json.loads(subprocess.check_output(['gh','api','repos/fizzexual/kestrel-sql/releases?per_page=100'],text=True,encoding='utf-8'))
actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']};assert len(releases)==20 and set(actual)==set(expected)
for k,v in expected.items():assert actual[k]['size']==v['bytes'] and actual[k]['digest']=='sha256:'+v['sha256']
bundle=load(ROOT/'benchmarks/anchor-reuse-076-bundle-check.json');archive=ROOT.parent/bundle['artifact'];assert sha(archive)==bundle['sha256']==completion['repository_artifacts'][0]['sha256']
preservation=load(ROOT/'benchmarks/anchor-reuse-076-preservation.json')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,digest in preservation['payload_sha256'].items():
        if name.startswith(('model/','bin/','locked-registry-crates/')):
            assert sha(OLD/name)==digest
            with z.open('kestrel-sql/benchmarks/anchor-reuse-076/'+name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
target=(OLD/'build-cache').resolve();assert target==W.parent/'perf-076/build-cache'
files=[{'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(target.rglob('*')) if p.is_file()];assert files
result={'verified_utc':datetime.now(timezone.utc).isoformat(),'target':str(target),'files':files,'logical_bytes':sum(v['bytes'] for v in files),'archive':{'path':str(archive),'sha256':bundle['sha256']},'private_git_archive_matches_recorded_blob':True,'source_binary_crates_and_all_zip_crc_verified':True,'private_server_assets_verified':122,'only_completed_regenerable_compiler_cache':True,'free_bytes_before':shutil.disk_usage(W).free}
(W/'cache-reclamation-plan.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verified':True,'files':len(files),'logical_bytes':result['logical_bytes'],'private_assets':122}))
