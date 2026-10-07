from pathlib import Path
import ast, datetime, hashlib, json, re, subprocess

w = Path(__file__).parent
root = w.parents[1] / 'outputs/kestrel-sql'
def sha(p):
    return hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()
base = json.loads((w / 'baseline.json').read_text(encoding='utf-8'))
for name, digest in base['core_source_sha256'].items():
    assert sha(root / name) == digest
for name, digest in base['baseline_binary_sha256'].items():
    assert sha(root / 'bin' / name) == digest
documents = ['SERVICE_TRIAL_050.md', 'TRIAL_050.md', 'TRIAL_049.md', 'README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']
for name in documents:
    for url in re.findall(r'\]\(([^)]+)\)', (root / name).read_text(encoding='utf-8')):
        url = url.split('#')[0]
        if url and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', url):
            assert (root / url).exists(), (name, url)
for p in root.rglob('*.py'):
    if not any(x in ['.git', 'target', '__pycache__'] for x in p.parts):
        ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p))
for p in root.rglob('*.json'):
    if not any(x in ['.git', 'target', '__pycache__'] for x in p.parts):
        json.loads(p.read_text(encoding='utf-8-sig'))
publication = json.loads((root / 'benchmarks/trial-050-service-publication.json').read_text(encoding='utf-8'))
assert publication['private'] and publication['all_remote_asset_sizes_and_digests_verified'] == 68
audit = json.loads((root / 'benchmarks/trial-050-service/paired-service-audit.json').read_text(encoding='utf-8'))
assert audit['cases'] == 36 and audit['raw_quantiles_accounting_uniqueness_and_hashes_recomputed']
proof = {'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'default_core_and_supported_binaries_unchanged': True, 'new_documents_links_checked': documents,
         'repository_python_and_json_syntax_passed': True, 'audited_service_cases': 36,
         'all_offered_and_failed_evidence_retained': True, 'private_assets_verified': 68,
         'historical_archives_unchanged': 20, 'new_engine_release': False,
         'trial_promoted': False, 'morning_report_issued': False}
(root / 'benchmarks/trial-050-service-document-check.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
raw = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root)
names = set(raw.decode('utf-8').split('\0')) - {'', 'MANIFEST.sha256'}
manifest = ''.join(sha(root / name) + '  ' + name + '\n' for name in sorted(names))
(root / 'MANIFEST.sha256').write_text(manifest, encoding='utf-8')
for line in manifest.splitlines():
    digest, name = line.split('  ', 1)
    assert sha(root / name) == digest, name
print(json.dumps(proof | {'manifest_payload_files': len(names)}))
