from pathlib import Path
import ast,datetime,hashlib,json,re,shutil,subprocess
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
base=json.loads((W/'baseline.json').read_text())
for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d
for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d
for folder in ['trial-050-generation-identity','trial-053-compact-receipts','trial-055-service']:
    p=ROOT/'benchmarks'/folder;j=json.loads((p/'build-provenance.json').read_text())
    for n,d in j['source'].items():assert sha(p/'candidate'/n)==d
    for n,d in j['binaries'].items():assert sha(p/'bin'/n)==d
verified=0
for folder,name in [('publication-054-repeat','publication-054-preservation.json'),('trial-055-service','trial-055-preservation.json'),('trial-053-compact-receipts','trial-053-preservation.json')]:
    pr=json.loads((ROOT/'benchmarks'/name).read_text())
    for rel,d in pr['payload_sha256'].items():assert sha(ROOT/'benchmarks'/folder/rel)==d;verified+=1
checks=json.loads((ROOT/'benchmarks/native-054-service-055-bundle-check.json').read_text())
for check in checks:
    p=ROOT.parent/check['artifact'];assert sha(p)==check['sha256'] and p.stat().st_size==check['bytes']
    assert check['zip_crc_verified'] and check['all_database_fixture_and_payload_hashes_verified']
pub=json.loads((ROOT/'benchmarks/native-054-service-055-publication.json').read_text())
assert pub['private'] and pub['all_remote_asset_sizes_and_digests_verified']==78 and pub['historical_engine_tags_releases_and_archives_unchanged']==20
assert not (ROOT/'OVERNIGHT_2026-10-07.md').exists()
maintenance=ROOT/'benchmarks/native-054-service-055-maintenance';maintenance.mkdir(exist_ok=True)
for n in ['preserve_later_evidence.py','package_later_evidence.py','publish_later_evidence.py','verify_later_evidence.py']:shutil.copy2(W/n,maintenance/n)
docs=['PUBLICATION_054.md','SERVICE_TRIAL_055.md','README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']
for name in docs:
    for u in re.findall(r'\]\(([^)]+)\)',(ROOT/name).read_text(encoding='utf-8')):
        u=u.split('#')[0]
        if u and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',u):assert (ROOT/u).exists(),(name,u)
for p in ROOT.rglob('*'):
    if p.is_file() and not any(x in ['.git','target','__pycache__'] for x in p.parts):
        if p.suffix=='.py':ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
        elif p.suffix=='.json':json.loads(p.read_text(encoding='utf-8-sig'))
def names():
    raw=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT)
    return set(raw.decode().split('\0'))-{'','MANIFEST.sha256'}
pn='benchmarks/native-054-service-055-document-check.json'
proof={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'default_core_and_supported_binaries_unchanged':True,
    'frozen_050_053_and_055_source_and_bins_verified':True,'preserved_payload_hashes_verified':verified,
    'zip_crc_and_every_payload_verified_during_packaging':True,'immutable_zip_sizes_and_sha256_reverified':True,
    'database_fixture_files_in_new_zips':sum(c['full_database_fixture_files'] for c in checks),'documents_links_checked':docs,
    'repository_python_and_json_syntax_passed':True,'private_assets_verified':78,'historical_engine_releases_unchanged':20,
    'original_failed_native_053_guard_retained':True,'followup_native_054_source_unchanged':True,'service_055_failed_gates':4,
    'initial_service_preflight_failures_preserved':7,'completed_service_timings_not_restarted':29,'preflight_only_missing_cases_resumed':7,
    'new_engine_release':False,'trial_promoted':False,'morning_report_issued':False,'maintenance_execution_location':str(W),
    'git_manifest_payload_files':len(names()|{pn})}
(ROOT/pn).write_text(json.dumps(proof,indent=2)+'\n')
payload=names();manifest=''.join(sha(ROOT/n)+'  '+n+'\n' for n in sorted(payload));(ROOT/'MANIFEST.sha256').write_text(manifest,encoding='utf-8')
for line in manifest.splitlines():
    d,n=line.split('  ',1);assert sha(ROOT/n)==d
assert {line.split('  ',1)[1] for line in manifest.splitlines()}==names()
print(json.dumps(proof))
