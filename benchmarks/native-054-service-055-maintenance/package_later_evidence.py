from pathlib import Path
import datetime,hashlib,json,zipfile
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
configs=[(W.parent/'perf-054','publication-054-repeat','PUBLICATION_054.md','publication-054-preservation.json','fixtures','local-native-fixtures','kestrel-sql-development-cat6-054-repeat-evidence.zip','PUBLICATION_054_MANIFEST.sha256'),
         (W,'trial-055-service','SERVICE_TRIAL_055.md','trial-055-preservation.json','service-fixtures','local-service-fixtures','kestrel-sql-development-cat6-055-service-evidence.zip','SERVICE_TRIAL_055_MANIFEST.sha256')]
checks=[]
for work,folder,report,preservation,fixture_dir,fixture_alias,filename,manifest in configs:
    files={p.relative_to(ROOT).as_posix():p for p in (ROOT/'benchmarks'/folder).rglob('*') if p.is_file()}
    for name in [report,'benchmarks/'+preservation]:files[name]=ROOT/name
    if work==W:files['benchmarks/trial-055-service-follow-up.json']=ROOT/'benchmarks/trial-055-service-follow-up.json'
    pr=json.loads((ROOT/'benchmarks'/preservation).read_text())
    for rel,d in pr['payload_sha256'].items():assert sha(ROOT/'benchmarks'/folder/rel)==d
    fixtures=json.loads((work/'fixture-inventory.json').read_text());fixture_count=0
    for c in fixtures:
        for rel,v in c['files'].items():
            p=work/fixture_dir/c['label']/rel
            assert sha(p)==v['sha256'] and p.stat().st_size==v['bytes']
            files[f"benchmarks/{folder}/{fixture_alias}/{c['label']}/{rel}"]=p;fixture_count+=1
    archive=ROOT.parent/filename;assert not archive.exists()
    inventory={name:sha(p) for name,p in files.items()}
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,p in files.items():z.write(p,'kestrel-sql/'+name)
        z.writestr('kestrel-sql/'+manifest,''.join(f'{d}  {n}\n' for n,d in sorted(inventory.items())))
        z.writestr('kestrel-sql/DEVELOPMENT_EVIDENCE.md','Unreleased CAT6 diagnostic/service evidence, not a supported engine upgrade. Read '+report+'. Original failed gates, every slower round and preflight/resumption limits remain visible. Native gains do not qualify sustained service. Historical engine releases unchanged.\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist())==len(inventory)+2
        for name,d in inventory.items():assert hashlib.sha256(z.read('kestrel-sql/'+name)).hexdigest()==d
    digest=sha(archive);archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n')
    check={'artifact':archive.name,'bytes':archive.stat().st_size,'sha256':digest,'payload_files':len(inventory),'zip_entries':len(inventory)+2,
        'full_database_fixture_files':fixture_count,'all_database_fixture_and_payload_hashes_verified':True,'zip_crc_verified':True,
        'new_engine_release':False,'default_engine_changed':False,'trial_promoted':False,'packaged_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    checks.append(check);print(json.dumps(check),flush=True)
(ROOT/'benchmarks/native-054-service-055-bundle-check.json').write_text(json.dumps(checks,indent=2)+'\n')
