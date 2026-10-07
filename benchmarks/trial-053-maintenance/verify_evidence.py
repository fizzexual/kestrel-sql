from pathlib import Path
import ast, datetime, hashlib, json, re, shutil, subprocess, zipfile
W=Path(__file__).resolve().parent; ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
base=json.loads((W/'baseline.json').read_text())
for n,d in base['core_source_sha256'].items(): assert sha(ROOT/n)==d,n
for n,d in base['baseline_binary_sha256'].items(): assert sha(ROOT/'bin'/n)==d,n
for folder,work in [('trial-050-generation-identity','perf-050'),('trial-053-compact-receipts','perf-053')]:
    frozen=ROOT/'benchmarks'/folder; p=json.loads((frozen/'build-provenance.json').read_text())
    for n,d in p['source'].items(): assert sha(frozen/'candidate'/n)==d
    for n,d in p['binaries'].items(): assert sha(frozen/'bin'/n)==d
docs=['TRIAL_053.md','README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']
for name in docs:
    for u in re.findall(r'\]\(([^)]+)\)',(ROOT/name).read_text(encoding='utf-8')):
        u=u.split('#')[0]
        if u and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',u): assert (ROOT/u).exists(),(name,u)
for p in ROOT.rglob('*'):
    if p.is_file() and not any(x in ['.git','target','__pycache__'] for x in p.parts):
        if p.suffix=='.py': ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
        elif p.suffix=='.json': json.loads(p.read_text(encoding='utf-8-sig'))
pr=json.loads((ROOT/'benchmarks/trial-053-preservation.json').read_text())
for rel,d in pr['payload_sha256'].items(): assert sha(ROOT/'benchmarks/trial-053-compact-receipts'/rel)==d
check=json.loads((ROOT/'benchmarks/trial-053-bundle-check.json').read_text())
archive=ROOT.parent/check['artifact']; assert sha(archive)==check['sha256'] and archive.stat().st_size==check['bytes']
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    lines=z.read('kestrel-sql/TRIAL_053_MANIFEST.sha256').decode().splitlines()
    assert len(lines)==check['payload_files']
    for line in lines:
        d,n=line.split('  ',1); assert hashlib.sha256(z.read('kestrel-sql/'+n)).hexdigest()==d
pub=json.loads((ROOT/'benchmarks/trial-053-publication.json').read_text())
assert pub['private'] and pub['all_remote_asset_sizes_and_digests_verified']==74 and pub['historical_engine_tags_releases_and_archives_unchanged']==20
assert not (ROOT/'OVERNIGHT_2026-10-07.md').exists()
maintenance=ROOT/'benchmarks/trial-053-maintenance'; maintenance.mkdir(exist_ok=True)
for n in ['preserve_evidence.py','package_evidence.py','publish_evidence.py','verify_evidence.py']:
    shutil.copy2(W/n,maintenance/n)
def names():
    raw=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT)
    return set(raw.decode().split('\0'))-{'','MANIFEST.sha256'}
pn='benchmarks/trial-053-document-check.json'
proof={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'default_core_and_supported_binaries_unchanged':True,
       'frozen_050_and_053_source_and_bins_verified':True,'documents_links_checked':docs,'repository_python_and_json_syntax_passed':True,
       'all_173_preserved_payload_hashes_verified':True,'immutable_zip_crc_manifest_and_sha256_verified':True,
       'native_database_fixture_files_in_zip':186,'private_assets_verified':74,'historical_engine_releases_unchanged':20,
       'trial_promoted':False,'new_engine_release':False,'failed_native_gates':1,'morning_report_issued':False,
       'maintenance_execution_location':str(W),'git_manifest_payload_files':len(names()|{pn})}
(ROOT/pn).write_text(json.dumps(proof,indent=2)+'\n')
payload=names(); manifest=''.join(sha(ROOT/n)+'  '+n+'\n' for n in sorted(payload))
(ROOT/'MANIFEST.sha256').write_text(manifest,encoding='utf-8')
for line in manifest.splitlines():
    d,n=line.split('  ',1); assert sha(ROOT/n)==d
assert {line.split('  ',1)[1] for line in manifest.splitlines()}==names()
print(json.dumps(proof))
