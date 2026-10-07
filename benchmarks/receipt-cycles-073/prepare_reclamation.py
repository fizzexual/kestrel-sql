"""Verify the archived 071 duplicate model frames before scoped reclamation."""
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess,zipfile
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';OLD=W.parent/'perf-071';TARGET=OLD/'fixtures'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W/'fixture-reclamation-plan.json').exists();assert TARGET.resolve()==(W.parent/'perf-071/fixtures').resolve()
assert not TARGET.is_symlink() and not any(p.is_symlink() or p.stat().st_file_attributes & 1024 for p in TARGET.rglob('*'))
pub=load(ROOT/'repository-publication.json');expected={(r['tag'],a['name']):a for r in pub['releases'] for a in r['assets']};assert len(expected)==116
remote=json.loads(subprocess.check_output(['gh','api','repos/fizzexual/kestrel-sql/releases?per_page=100'],cwd=ROOT,text=True,encoding='utf-8'))
actual={(r['tag_name'],a['name']):a for r in remote for a in r['assets']};assert set(actual)==set(expected) and len(remote)==20
for key,a in expected.items():assert actual[key]['size']==a['bytes'] and actual[key]['digest']=='sha256:'+a['sha256']
inventory=load(OLD/'bundle-fixture-inventory.json');selected={k:v for k,v in inventory.items() if k.startswith('fixtures/')};assert len(selected)==648
assert {p.relative_to(OLD).as_posix() for p in TARGET.rglob('*') if p.is_file()}==set(selected)
archives=[];covered=set()
for part in load(ROOT/'benchmarks/compression-071-bundle-check.json')['artifacts']:
    p=ROOT.parent/part['artifact'];assert sha(p)==part['sha256']==expected['v0.3.16',p.name]['sha256']
    with zipfile.ZipFile(p) as z:
        manifests=[n for n in z.namelist() if n.endswith('_MANIFEST.sha256')];assert len(manifests)==1
        manifest=dict((n,d) for d,n in (line.split('  ',1) for line in z.read(manifests[0]).decode().splitlines()))
        for n,d in manifest.items():
            member='kestrel-sql/'+n
            rel=n.removeprefix('benchmarks/compression-071/')
            if rel not in selected:continue
            file=OLD/rel;assert sha(file)==d==selected[rel]['sha256'] and file.stat().st_size==selected[rel]['bytes']
            with z.open(member) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d
            assert rel not in covered;covered.add(rel);selected[rel].update(archive=p.name,member=member,member_crc=z.getinfo(member).CRC)
    archives.append({'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'private_server_digest_matched':True})
    print('verified retained archive',part['part'],flush=True)
assert covered==set(selected)
result={'target':str(TARGET.resolve()),'prepared_utc':datetime.now(timezone.utc).isoformat(),'files':selected,'file_count':len(selected),'bytes':sum(v['bytes'] for v in selected.values()),
    'model_directories':len(list(TARGET.iterdir())),'archives':archives,'all_original_member_bytes_verified':True,'remote_assets_verified':116,'only_duplicate_full_071_model_frames_to_remove':True,
    'raw_logs_inputs_reports_sources_binaries_archives_untouched':True,'free_before':shutil.disk_usage(W).free}
(W/'fixture-reclamation-plan.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:result[k] for k in ['file_count','bytes','model_directories','remote_assets_verified','free_before']}))
