from pathlib import Path
import datetime, hashlib, json, zipfile
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
FOLDER='trial-053-compact-receipts'
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
files={p.relative_to(ROOT).as_posix():p for p in (ROOT/'benchmarks'/FOLDER).rglob('*') if p.is_file()}
for name in ['TRIAL_053.md','benchmarks/trial-053-preservation.json']: files[name]=ROOT/name
pr=json.loads((ROOT/'benchmarks/trial-053-preservation.json').read_text())
for rel,d in pr['payload_sha256'].items(): assert sha(ROOT/'benchmarks'/FOLDER/rel)==d
fixtures=json.loads((W/'fixture-inventory.json').read_text())
frame_count=0
for c in fixtures:
    for rel,v in c['files'].items():
        p=W/'fixtures'/c['label']/rel
        assert sha(p)==v['sha256'] and p.stat().st_size==v['bytes']
        files[f"benchmarks/{FOLDER}/local-native-fixtures/{c['label']}/{rel}"]=p
        frame_count+=1
archive=ROOT.parent/'kestrel-sql-development-cat6-053-evidence.zip'
assert not archive.exists()
inventory={name:sha(p) for name,p in files.items()}
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,p in files.items(): z.write(p,'kestrel-sql/'+name)
    z.writestr('kestrel-sql/TRIAL_053_MANIFEST.sha256',''.join(f'{d}  {n}\n' for n,d in sorted(inventory.items())))
    z.writestr('kestrel-sql/DEVELOPMENT_EVIDENCE.md','Isolated CAT6 development evidence, not a supported engine release. Five of six native gates pass; the p50 guard fails. Read TRIAL_053.md. All slower rounds, raw failures and native database fixtures are preserved. All older engine releases remain unchanged.\n')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None and len(z.namelist())==len(inventory)+2
    for name,d in inventory.items(): assert hashlib.sha256(z.read('kestrel-sql/'+name)).hexdigest()==d
d=sha(archive)
archive.with_suffix('.zip.sha256').write_text(f'{d}  {archive.name}\n')
out={'artifact':archive.name,'bytes':archive.stat().st_size,'sha256':d,'payload_files':len(inventory),'zip_entries':len(inventory)+2,
     'native_fixture_files':frame_count,'all_native_fixture_bytes_and_payload_hashes_verified':True,'zip_crc_verified':True,
     'new_engine_release':False,'default_engine_changed':False,'trial_promoted':False,
     'packaged_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(ROOT/'benchmarks/trial-053-bundle-check.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
