"""Verify archived074 native fixture duplicates for conservative disk headroom."""
import hashlib,json,shutil,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-074';ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
bundle=load(ROOT/'benchmarks/hybrid-receipts-074-bundle-check.json');archive=ROOT.parent/bundle['artifact'];assert sha(archive)==bundle['sha256']
releases=json.loads(subprocess.check_output(['gh','api','repos/fizzexual/kestrel-sql/releases?per_page=100'],text=True,encoding='utf-8'));assert len(releases)==20
asset=next(a for r in releases if r['tag_name']=='v0.3.16' for a in r['assets'] if a['name']==archive.name);assert asset['size']==archive.stat().st_size and asset['digest']=='sha256:'+bundle['sha256']
target=(OLD/'rust-temp').resolve();inventory=load(OLD/'bundle-fixture-inventory.json');selected={n:v for n,v in inventory.items() if n.startswith('rust-temp/')};current={p.relative_to(OLD).as_posix():p for p in target.rglob('*') if p.is_file()};assert set(selected)==set(current)
files=[]
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for n,d in selected.items():
        p=current[n];assert p.stat().st_size==d['bytes'] and sha(p)==d['sha256']
        with z.open('kestrel-sql/benchmarks/hybrid-receipts-074/'+n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d['sha256']
        files.append({'path':str(p.resolve()),**d})
result={'verified_utc':datetime.now(timezone.utc).isoformat(),'targets':[{'target':str(target),'files':files,'logical_bytes':sum(v['bytes'] for v in files)}],'archives':[{'path':str(archive),'sha256':bundle['sha256']}],'private_release_asset_digest_match':True,'only_complete_archived074_native_fixture_duplicates':True,'free_bytes_before':shutil.disk_usage(W).free}
(W/'reclamation-074-plan.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
s=(W/'reclaim_duplicates.ps1').read_text(encoding='utf-8').replace('reclamation-plan.json','reclamation-074-plan.json').replace('reclamation-result.json','reclamation-074-result.json').replace("$taskExpected=@((Join-Path $taskWorkspace 'perf-076\\fixtures'),(Join-Path $taskWorkspace 'perf-076\\rust-temp'),(Join-Path $taskWorkspace 'perf-077\\fixtures'))","$taskExpected=@((Join-Path $taskWorkspace 'perf-074\\rust-temp'))").replace('Count -ne 3','Count -ne 1').replace('Expected exactly three duplicate directories','Expected exactly one duplicate directory')
assert "perf-076\\" not in s and "perf-077\\" not in s
(W/'reclaim_074_duplicates.ps1').write_text(s,encoding='utf-8')
print(json.dumps({'verified':True,'files':len(files),'logical_bytes':sum(v['bytes'] for v in files)}))
