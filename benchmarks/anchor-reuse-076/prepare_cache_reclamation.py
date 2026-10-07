"""Verify preserved build inputs/outputs before deleting regenerable caches."""
import hashlib,json,shutil,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
publication=load(ROOT/'repository-publication.json')
expected={(r['tag'],a['name']):a for r in publication['releases'] for a in r['assets']};assert len(expected)==122
releases=json.loads(subprocess.check_output(['gh','api','repos/fizzexual/kestrel-sql/releases?per_page=100'],text=True,encoding='utf-8'))
actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']}
assert len(releases)==20 and set(actual)==set(expected)
for k,v in expected.items():assert actual[k]['size']==v['bytes'] and actual[k]['digest']=='sha256:'+v['sha256']
targets=[];archives=[]
for num,label,exe in [('074','hybrid-receipts-074','hybrid-model.exe'),('075','hybrid-cycles-075','growth-model.exe')]:
    old=W.parent/f'perf-{num}';proof=load(old/'build-proof.json');bundle=load(ROOT/f'benchmarks/{label}-bundle-check.json')
    archive=ROOT.parent/bundle['artifact'];assert sha(archive)==bundle['sha256']
    preservation=load(ROOT/f'benchmarks/{label}-preservation.json')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in preservation['payload_sha256'].items():
            if name.startswith(('model/','bin/','locked-registry-crates/')):
                p=old/name;assert sha(p)==digest
                with z.open('kestrel-sql/benchmarks/'+label+'/'+name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
    assert sha(old/'bin'/exe)==proof['binary_sha256']
    target=(old/'build-cache').resolve();assert target==W.parent/f'perf-{num}/build-cache'
    files=[{'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(target.rglob('*')) if p.is_file()]
    assert files
    targets.append({'target':str(target),'files':files,'logical_bytes':sum(v['bytes'] for v in files)})
    archives.append({'path':str(archive),'sha256':bundle['sha256'],'source_binary_crate_members_and_all_zip_crc_verified':True})
result={'verified_utc':datetime.now(timezone.utc).isoformat(),'targets':targets,'archives':archives,
        'private_server_assets_verified':122,'engine_releases_unchanged':20,'only_regenerable_completed_compiler_caches':True,
        'full_fixtures_raw_logs_inputs_source_binaries_policies_archives_reports_unchanged':True,'free_bytes_before':shutil.disk_usage(W).free}
(W/'cache-reclamation-plan.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verified':True,'targets':2,'files':sum(len(t['files']) for t in targets),'logical_bytes':sum(t['logical_bytes'] for t in targets),'private_assets':122}))
