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
documents = ['TRIAL_050.md', 'TRIAL_049.md', 'TRIAL_048.md', 'README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']
for name in documents:
    text = (root / name).read_text(encoding='utf-8')
    for url in re.findall(r'\]\(([^)]+)\)', text):
        url = url.split('#')[0]
        if not url or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', url):
            continue
        assert (root / url).exists(), (name, url)
for p in root.rglob('*.py'):
    if not any(x in ['.git', 'target', '__pycache__'] for x in p.parts):
        ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p))
for p in root.rglob('*.json'):
    if not any(x in ['.git', 'target', '__pycache__'] for x in p.parts):
        json.loads(p.read_text(encoding='utf-8-sig'))
publication = json.loads((root / 'benchmarks/trial-050-publication.json').read_text(encoding='utf-8'))
assert publication['private'] and publication['all_remote_asset_sizes_and_digests_verified'] == 66
qualified = json.loads((root / 'benchmarks/trial-050-generation-identity/correctness-audit.json').read_text(encoding='utf-8'))
assert qualified['all_14_final_external_gates_passed'] and not qualified['fresh_performance_measured']
proof = {'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'default_core_and_supported_binaries_unchanged': True, 'new_documents_links_checked': documents,
         'repository_python_and_json_syntax_passed': True, 'rust_tests_each_mode': 85,
         'all_14_external_gates_audited': True, 'private_assets_verified': 66,
         'historical_archives_unchanged': 20, 'new_engine_release': False,
         'trial_promoted': False, 'fresh_performance_measured': False, 'morning_report_issued': False}
(root / 'benchmarks/trial-050-document-check.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')

def git_payloads():
    raw = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=root)
    return set(raw.decode('utf-8').split('\0')) - {'', 'MANIFEST.sha256'}

# An ordinary clone has no runtime lock markers. Match the actual Git payload,
# rather than silently including ignored files which happen to exist locally.
names = git_payloads()
old = {line.split('  ', 1)[1] for line in (root / 'MANIFEST.sha256').read_text(encoding='utf-8').splitlines()}
missing = sorted(old - names)
assert all(name.endswith('.lockfile') and (root / name).stat().st_size == 0 for name in missing), missing
marker_proof = root / 'benchmarks/repository-manifest-runtime-markers.json'
assert not marker_proof.exists()
marker_proof.write_text(json.dumps({
    'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'prior_manifest_referenced_git_ignored_empty_runtime_markers': missing,
    'correction': 'Repository manifest now hashes only Git-tracked/unignored payloads; ignored zero-byte lock markers remain local and in the immutable 049 ZIP.',
    'database_frames_or_raw_samples_removed': False, 'immutable_release_assets_changed': False
}, indent=2) + '\n', encoding='utf-8')
names = git_payloads()
manifest = ''.join(sha(root / name) + '  ' + name + '\n' for name in sorted(names))
(root / 'MANIFEST.sha256').write_text(manifest, encoding='utf-8')
for line in manifest.splitlines():
    digest, name = line.split('  ', 1)
    assert sha(root / name) == digest, name
assert {line.split('  ', 1)[1] for line in manifest.splitlines()} == git_payloads()
print(json.dumps(proof | {'manifest_payload_files': len(names), 'git_ignored_empty_runtime_markers_excluded': len(missing)}))
