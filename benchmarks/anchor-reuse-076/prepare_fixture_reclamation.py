"""Verify only duplicate 075 case files against their preserved full archive."""
import hashlib,json,shutil,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-075';ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
publication=load(ROOT/'repository-publication.json')
expected={(r['tag'],a['name']):a for r in publication['releases'] for a in r['assets']};assert len(expected)==122
releases=json.loads(subprocess.check_output(['gh','api','repos/fizzexual/kestrel-sql/releases?per_page=100'],text=True,encoding='utf-8'))
actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']};assert len(releases)==20 and set(expected)==set(actual)
for k,v in expected.items():assert actual[k]['size']==v['bytes'] and actual[k]['digest']=='sha256:'+v['sha256']
bundle=load(ROOT/'benchmarks/hybrid-cycles-075-bundle-check.json');archive=ROOT.parent/bundle['artifact'];assert sha(archive)==bundle['sha256']
assert actual['v0.3.16',archive.name]['digest']=='sha256:'+bundle['sha256']
inventory=load(OLD/'fixture-inventory.json');target=(OLD/'fixtures').resolve();assert target==W.parent/'perf-075/fixtures'
files=[]
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for rel,v in inventory.items():
        p=OLD/rel;assert p.is_relative_to(target) and p.is_file() and p.stat().st_size==v['bytes'] and sha(p)==v['sha256']
        member='kestrel-sql/benchmarks/hybrid-cycles-075/'+rel
        with z.open(member) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==v['sha256']
        files.append({'path':str(p.resolve()),'bytes':v['bytes'],'sha256':v['sha256'],'zip_member':member})
assert len(files)==3546 and {str(p.resolve()) for p in target.rglob('*') if p.is_file()}=={v['path'] for v in files}
result={'verified_utc':datetime.now(timezone.utc).isoformat(),'target':str(target),'files':files,'total_bytes':sum(v['bytes'] for v in files),
    'archive':str(archive),'archive_sha256':bundle['sha256'],'every_zip_crc_and_duplicate_full_sha_verified':True,
    'private_server_assets_verified':122,'older_engine_releases':20,'only_duplicate_case_directory':True,
    'source_binary_inputs_policies_raw_logs_reports_and_full_archives_unchanged':True,'free_bytes_before':shutil.disk_usage(W).free}
(W/'fixture-reclamation-plan.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='files'}))
