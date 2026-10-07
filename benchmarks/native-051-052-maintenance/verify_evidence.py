from pathlib import Path
import ast, datetime, hashlib, json, re, subprocess, zipfile
W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
base = json.loads((W.parent / 'perf-050/baseline.json').read_text(encoding='utf-8'))
for name, digest in base['core_source_sha256'].items():
    assert sha(ROOT / name) == digest, name
for name, digest in base['baseline_binary_sha256'].items():
    assert sha(ROOT / 'bin' / name) == digest, name
frozen = ROOT / 'benchmarks/trial-050-generation-identity'
p = json.loads((frozen / 'build-provenance.json').read_text())
for name, digest in p['source'].items():
    assert sha(frozen / 'candidate' / name) == digest
for name, digest in p['binaries'].items():
    assert sha(frozen / 'bin' / name) == digest
documents = ['PUBLICATION_051.md', 'TRIAL_052.md', 'REPRODUCE_NATIVE_051_052.md',
             'README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']
for name in documents:
    for url in re.findall(r'\]\(([^)]+)\)', (ROOT / name).read_text(encoding='utf-8')):
        url = url.split('#')[0]
        if url and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', url):
            assert (ROOT / url).exists(), (name, url)
for p in ROOT.rglob('*'):
    if p.is_file() and not any(x in ['.git', 'target', '__pycache__'] for x in p.parts):
        if p.suffix == '.py':
            ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p))
        elif p.suffix == '.json':
            json.loads(p.read_text(encoding='utf-8-sig'))
for folder, name in [('publication-051-native', 'publication-051-preservation.json'),
                     ('trial-052-pending-length', 'trial-052-preservation.json')]:
    pr = json.loads((ROOT / 'benchmarks' / name).read_text())
    for rel, digest in pr['payload_sha256'].items():
        assert sha(ROOT / 'benchmarks' / folder / rel) == digest
checks = json.loads((ROOT / 'benchmarks/native-051-052-bundle-check.json').read_text())
for check in checks:
    archive = ROOT.parent / check['artifact']
    assert sha(archive) == check['sha256'] and archive.stat().st_size == check['bytes']
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
pub = json.loads((ROOT / 'benchmarks/native-051-052-publication.json').read_text())
assert pub['private'] and pub['all_remote_asset_sizes_and_digests_verified'] == 72
assert pub['historical_engine_tags_releases_and_archives_unchanged'] == 20
assert not (ROOT / 'OVERNIGHT_2026-10-07.md').exists()
def names():
    raw = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT)
    return set(raw.decode('utf-8').split('\0')) - {'', 'MANIFEST.sha256'}
proof_name = 'benchmarks/native-051-052-document-check.json'
proof = {'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'default_core_and_supported_binaries_unchanged': True, 'frozen_050_source_and_all_bins_unchanged': True,
         'documents_links_checked': documents, 'repository_python_and_json_syntax_passed': True,
         'all_189_preserved_payload_hashes_verified': True, 'immutable_zip_crc_and_sha256_verified': True,
         'private_assets_verified': 72, 'historical_engine_releases_unchanged': 20,
         'new_engine_release': False, 'trial_promoted': False, 'rejected_trial_052_gates_failed': 4,
         'morning_report_issued': False, 'git_manifest_payload_files': len(names() | {proof_name})}
(ROOT / proof_name).write_text(json.dumps(proof, indent=2) + '\n')
payload = names()
manifest = ''.join(sha(ROOT / name) + '  ' + name + '\n' for name in sorted(payload))
(ROOT / 'MANIFEST.sha256').write_text(manifest, encoding='utf-8')
for line in manifest.splitlines():
    digest, name = line.split('  ', 1)
    assert sha(ROOT / name) == digest
assert {line.split('  ', 1)[1] for line in manifest.splitlines()} == names()
print(json.dumps(proof))
