"""Verify preserved072/073 build inputs and exact native duplicates before reclaiming."""
import hashlib,json,shutil,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
releases=json.loads(subprocess.check_output(['gh','api','repos/fizzexual/kestrel-sql/releases?per_page=100'],text=True,encoding='utf-8'));actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']};assert len(releases)==20 and len(actual)==122
targets=[];archives=[]
for num,label in [('072','receipt-pages-072'),('073','receipt-cycles-073')]:
    old=W.parent/f'perf-{num}';bundle=load(ROOT/f'benchmarks/{label}-bundle-check.json');archive=ROOT.parent/bundle['artifact'];assert sha(archive)==bundle['sha256']
    asset=actual['v0.3.16',archive.name];assert asset['size']==archive.stat().st_size and asset['digest']=='sha256:'+bundle['sha256']
    preservation=load(ROOT/f'benchmarks/{label}-preservation.json');build=load(old/'build-proof.json');assert build['complete']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n,d in preservation['payload_sha256'].items():
            if n.startswith(('model/','bin/','locked-registry-crates/')):
                assert sha(old/n)==d
                with z.open('kestrel-sql/benchmarks/'+label+'/'+n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d
        for folder in ['build-cache','rust-temp']:
            target=(old/folder).resolve();assert target==W.parent/f'perf-{num}'/folder
            current={p.relative_to(old).as_posix():p for p in target.rglob('*') if p.is_file()};assert current
            inventory=load(old/'bundle-fixture-inventory.json') if folder=='rust-temp' else None
            if inventory:
                selected={n:v for n,v in inventory.items() if n.startswith('rust-temp/')};assert set(current)==set(selected),('unexpected unarchived native file',target)
            files=[]
            for n,p in current.items():
                digest=sha(p);size=p.stat().st_size
                if inventory:
                    assert digest==selected[n]['sha256'] and size==selected[n]['bytes']
                    with z.open('kestrel-sql/benchmarks/'+label+'/'+n) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
                files.append({'path':str(p.resolve()),'bytes':size,'sha256':digest})
            targets.append({'target':str(target),'files':files,'logical_bytes':sum(v['bytes'] for v in files),'kind':'regenerable completed compiler cache' if folder=='build-cache' else 'verified archived native fixture duplicate'})
    archives.append({'path':str(archive),'sha256':bundle['sha256'],'all_zip_crc_source_binary_crates_and_native_member_hashes_verified':True,'private_release_asset_digest_matched':True})
result={'verified_utc':datetime.now(timezone.utc).isoformat(),'targets':targets,'archives':archives,'only_completed_regenerable_caches_or_verified_archived_native_duplicates':True,'all_original_inputs_source_binaries_policies_raw_logs_reports_and_complete_archives_retained':True,'free_bytes_before':shutil.disk_usage(W).free}
(W/'reclamation-older-plan.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
s=(W/'reclaim_duplicates.ps1').read_text(encoding='utf-8').replace('reclamation-plan.json','reclamation-older-plan.json').replace('reclamation-result.json','reclamation-older-result.json')
s=s.replace("$taskExpected=@((Join-Path $taskWorkspace 'perf-076\\fixtures'),(Join-Path $taskWorkspace 'perf-076\\rust-temp'),(Join-Path $taskWorkspace 'perf-077\\fixtures'))","$taskExpected=@((Join-Path $taskWorkspace 'perf-072\\build-cache'),(Join-Path $taskWorkspace 'perf-072\\rust-temp'),(Join-Path $taskWorkspace 'perf-073\\build-cache'),(Join-Path $taskWorkspace 'perf-073\\rust-temp'))").replace('Count -ne 3','Count -ne 4').replace('Expected exactly three duplicate directories','Expected exactly four verified directories')
assert "perf-076\\" not in s and "perf-077\\" not in s
(W/'reclaim_older_duplicates.ps1').write_text(s,encoding='utf-8')
print(json.dumps({'verified':True,'targets':len(targets),'files':sum(len(t['files']) for t in targets),'logical_bytes':sum(t['logical_bytes'] for t in targets),'free_bytes_before':result['free_bytes_before']}))
