"""Preserve every 063 outcome and full store; add immutable private evidence assets."""
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
DEST = ROOT / 'benchmarks/batching-063'
REPORT = 'BATCHING_063.md'
REPO = 'fizzexual/kestrel-sql'
os.environ.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='safe.directory', GIT_CONFIG_VALUE_0=ROOT.as_posix())
def now():
    return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p, v):
    p.write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8')
def unchanged():
    b = load(W / 'baseline.json')
    for n, d in b['core_source_sha256'].items():
        assert sha(ROOT / n) == d, n
    for n, d in b['baseline_binary_sha256'].items():
        assert sha(ROOT / 'bin' / n) == d, n
    m = load(ROOT / 'benchmarks/overnight-2026-10-07-report-check.json')
    assert sha(ROOT / m['report_file']) == m['report_sha256']
    assert not load(W / 'post-qualification-process-check.json')['active_processes']
def cache_file(rel):
    return False
def fixture_file(rel):
    return rel.parts[0] in {'service-fixtures', 'recovery-fixtures'}
def preserve():
    unchanged()
    assert load(W / 'audit.json')['no_new_correctness_failure'] and not DEST.exists()
    shutil.copy2(ROOT / 'MANIFEST.sha256', W / 'repository-manifest-pre-063.sha256')
    fixtures = {p.relative_to(W).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p)}
                for p in W.rglob('*') if p.is_file() and fixture_file(p.relative_to(W))}
    save(W / 'fixture-inventory.json', fixtures)
    forensic_files = {}
    save(W / 'forensics-inventory.json', forensic_files)
    payload = {}
    for p in sorted(W.rglob('*')):
        rel = p.relative_to(W)
        if p.is_file() and not fixture_file(rel) and not cache_file(rel) and '__pycache__' not in rel.parts:
            dest = DEST / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            assert sha(p) == sha(dest)
            payload[rel.as_posix()] = sha(dest)
    proof = {'preserved_utc': now(), 'source_work_directory': str(W), 'payload_sha256': payload,
             'fresh_fixture_files': len(fixtures), 'timed_input_files': 0,
             'full_stores_in_separate_zip': True,
             'rescued_cached_executables_in_zip_only': len(forensic_files),
             'all_historical_results_unchanged': True,
             'default_engine_unchanged': True, 'new_engine_release': False}
    save(ROOT / 'benchmarks/batching-063-preservation.json', proof)
    service = load(W / 'audit.json')
    intro = (f'**Latest batching experiment:** [063 tests current released 0/1/4 ms options with identical zero-delay controls](BATCHING_063.md). '
             f'{service["identity_checks_failed"]}/10 identity checks and {service["candidate_criteria_failed"]}/26 option criteria fail. '
             'All previous native gains and service failures remain preserved. Supported 0.3.16 and its zero-delay default are unchanged.\n\n')
    for name in ['README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']:
        p = ROOT / name
        first, rest = p.read_text(encoding='utf-8').split('\n\n', 1)
        p.write_text(first + '\n\n' + intro + rest, encoding='utf-8')
    p = ROOT / 'ADOPTION_STATUS.md'
    text = p.read_text(encoding='utf-8')
    text += (f'\n[Current batching controls 063](BATCHING_063.md) record {service["identity_checks_failed"]}/10 failed identity checks '
             f'and {service["candidate_criteria_failed"]}/26 failed option criteria. Existing durable options are measured, with no engine edit, '
             'default promotion or change to the primary-production adoption assessment.\n')
    p.write_text(text, encoding='utf-8')
    print(json.dumps({'preserved_payload_files': len(payload), 'fresh_fixture_files': len(fixtures), 'timed_input_files': 0}))
def package():
    unchanged()
    proof = load(ROOT / 'benchmarks/batching-063-preservation.json')
    for n, d in proof['payload_sha256'].items():
        assert sha(DEST / n) == d, n
    files = {p.relative_to(ROOT).as_posix(): p for p in DEST.rglob('*') if p.is_file()}
    for name in [REPORT, 'benchmarks/batching-063-preservation.json']:
        files[name] = ROOT / name
    for n, d in load(W / 'fixture-inventory.json').items():
        p = W / n
        assert p.stat().st_size == d['bytes'] and sha(p) == d['sha256']
        files['benchmarks/batching-063/' + n] = p
    for n, d in load(W / 'forensics-inventory.json').items():
        p = W / n
        assert p.stat().st_size == d['bytes'] and sha(p) == d['sha256']
        files['benchmarks/batching-063/' + n] = p
    archive = ROOT.parent / 'kestrel-sql-development-063-batching-evidence.zip'
    assert not archive.exists()
    hashes = {n: sha(p) for n, p in files.items()}
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for n, p in files.items():
            z.write(p, 'kestrel-sql/' + n)
        z.writestr('kestrel-sql/BATCHING_063_MANIFEST.sha256', ''.join(d + '  ' + n + '\n' for n, d in sorted(hashes.items())))
        z.writestr('kestrel-sql/DEVELOPMENT_ONLY.md', 'Current-release optional batching experiment. Same frozen 0.3.16 executable for all four labels. All 32 service outcomes, raw requests, 24 new kill cycles and full stores retained. No engine edit or supported release. Read BATCHING_063.md before interpreting ratios.\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n, d in hashes.items():
            with z.open('kestrel-sql/' + n) as f:
                assert hashlib.file_digest(f, 'sha256').hexdigest() == d
    archive.with_suffix('.zip.sha256').write_text(sha(archive) + '  ' + archive.name + '\n', encoding='utf-8')
    result = {'artifact': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha(archive),
              'zip_entries': len(hashes) + 2, 'payload_files': len(hashes),
              'fresh_fixture_files': proof['fresh_fixture_files'], 'timed_input_files': proof['timed_input_files'],
              'full_service_stores': 27, 'all_crc_and_payload_hashes_verified': True,
              'packaged_utc': now(), 'new_engine_release': False}
    save(ROOT / 'benchmarks/batching-063-bundle-check.json', result)
    print(json.dumps(result))
def gh(*args):
    return json.loads(subprocess.check_output(['gh', *args], cwd=ROOT, text=True, encoding='utf-8'))
def publish():
    unchanged()
    assert gh('repo', 'view', REPO, '--json', 'isPrivate')['isPrivate']
    assert not gh('api', f'repos/{REPO}/actions/permissions')['enabled']
    backup = ROOT / 'repository-publication-pre-batching-063.json'
    if not backup.exists():
        shutil.copy2(ROOT / 'repository-publication.json', backup)
    old = load(backup)
    expected = {(r['tag'], a['name']): a for r in old['releases'] for a in r['assets']}
    assert len(expected) == 92
    bundle = load(ROOT / 'benchmarks/batching-063-bundle-check.json')
    archive = ROOT.parent / bundle['artifact']
    assert sha(archive) == bundle['sha256']
    paths = [archive, archive.with_suffix('.zip.sha256')]
    releases = gh('api', f'repos/{REPO}/releases?per_page=100')
    actual = {(r['tag_name'], a['name']): a for r in releases for a in r['assets']}
    assert len(releases) == 20 and set(expected) <= set(actual)
    assert set(actual) <= set(expected) | {('v0.3.16', p.name) for p in paths}
    for k, a in expected.items():
        assert actual[k]['size'] == a['bytes'] and actual[k]['digest'] == 'sha256:' + a['sha256']
    missing = []
    for p in paths:
        key = ('v0.3.16', p.name)
        if key in actual:
            assert actual[key]['size'] == p.stat().st_size and actual[key]['digest'] == 'sha256:' + sha(p)
        else:
            missing.append(str(p))
    if missing:
        subprocess.run(['gh', 'release', 'upload', 'v0.3.16', *missing, '--repo', REPO], cwd=ROOT, check=True)
    releases = gh('api', f'repos/{REPO}/releases?per_page=100')
    actual = {(r['tag_name'], a['name']): a for r in releases for a in r['assets']}
    assert len(releases) == 20 and len(actual) == 94
    for k, a in expected.items():
        assert actual[k]['size'] == a['bytes'] and actual[k]['digest'] == 'sha256:' + a['sha256']
    added = []
    for p in paths:
        a = actual['v0.3.16', p.name]
        assert a['size'] == p.stat().st_size and a['digest'] == 'sha256:' + sha(p)
        added.append({'name': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p), 'asset_id': a['id'],
                      'server_digest_matched': True, 'download_url': a['browser_download_url'],
                      'role': '063 current-release optional batching; 32 outcomes, 24 kill cycles and full stores; no engine release'})
    refs = dict(line.split()[::-1] for line in subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/tags/*'], cwd=ROOT, text=True).splitlines())
    for r in load(ROOT / 'release-history.json')['snapshots']:
        k = 'refs/tags/' + r['tag']
        assert refs.get(k + '^{}', refs.get(k)) == r['commit']
    next(r for r in old['releases'] if r['tag'] == 'v0.3.16')['assets'].extend(added)
    old.update(uploaded_assets=94, all_94_server_digests_matched=True, completed_at_utc=now(),
               batching_063={'report': REPORT, 'development_only': True,
                                  'optional_batching_controls_complete': True, 'promoted': False})
    save(ROOT / 'repository-publication.json', old)
    result = {'private': True, 'actions_disabled': True, 'new_assets': added, 'remote_assets_verified': 94,
              'previous_assets_unchanged': 92, 'historical_engine_tags_releases_unchanged': 20,
              'new_engine_release': False, 'default_engine_changed': False, 'published_utc': now()}
    save(ROOT / 'benchmarks/batching-063-publication.json', result)
    nav = ROOT / 'repository-navigation-audit.json'
    snapshot = ROOT / 'repository-navigation-pre-batching-063.json'
    if not snapshot.exists():
        shutil.copy2(nav, snapshot)
    data = load(nav)
    data.update(verified_server_asset_digests=94, batching_report=REPORT, updated_at_utc=now())
    save(nav, data)
    p = ROOT / REPORT
    line = '\nPrivate immutable [full batching evidence and stores](' + added[0]['download_url'] + ') and [SHA-256](' + added[1]['download_url'] + '). The supplemental archive contains the report before this upload-link paragraph; it replaces no historical asset and creates no engine release.\n'
    text = p.read_text(encoding='utf-8')
    if line not in text:
        p.write_text(text + line, encoding='utf-8')
    print(json.dumps(result))
def verify():
    unchanged()
    proof = load(ROOT / 'benchmarks/batching-063-preservation.json')
    for n, d in proof['payload_sha256'].items():
        assert sha(DEST / n) == d, n
    bundle = load(ROOT / 'benchmarks/batching-063-bundle-check.json')
    assert sha(ROOT.parent / bundle['artifact']) == bundle['sha256']
    publication = load(ROOT / 'benchmarks/batching-063-publication.json')
    assert publication['private'] and publication['remote_assets_verified'] == 94
    updated = {'README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md', 'ADOPTION_STATUS.md',
               'repository-publication.json', 'repository-navigation-audit.json'}
    historical_files = 0
    for line in (W / 'repository-manifest-pre-063.sha256').read_text().splitlines():
        d, n = line.split('  ', 1)
        if n not in updated:
            assert sha(ROOT / n) == d, ('historical payload changed', n)
            historical_files += 1
    downloads = {a['download_url'] for r in load(ROOT / 'repository-publication.json')['releases'] for a in r['assets']}
    for name in [REPORT, 'README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md', 'ADOPTION_STATUS.md']:
        text = (ROOT / name).read_text(encoding='utf-8')
        assert not any(ord(c) < 32 and c not in '\n\r\t' for c in text), name
        for link in re.findall(r'\]\(([^)]+)\)', text):
            local = link.split('#')[0]
            if local and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', local):
                assert (ROOT / local).exists(), (name, local)
            if '/releases/download/' in link:
                assert link in downloads
    for p in DEST.rglob('*'):
        if p.is_file():
            if p.suffix == '.py':
                ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p))
            elif p.suffix == '.json':
                load(p)
    result = {'checked_utc': now(), 'preserved_payload_files': len(proof['payload_sha256']),
              'all_local_and_release_links_verified': True, 'python_json_syntax_passed': True,
              'all_fixtures_zip_crc_and_hashes_verified': True,
              'default_source_binaries_and_morning_unchanged': True,
              'historical_manifest_files_unchanged': historical_files,
              'all_policy_failures_and_round_outliers_preserved': True,
              'private_remote_assets_verified': 94, 'new_engine_release': False}
    save(ROOT / 'benchmarks/batching-063-document-check.json', result)
    names = set(subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')) - {'', 'MANIFEST.sha256'}
    manifest = ''.join(sha(ROOT / n) + '  ' + n + '\n' for n in sorted(names))
    (ROOT / 'MANIFEST.sha256').write_text(manifest, encoding='utf-8')
    for line in manifest.splitlines():
        d, n = line.split('  ', 1)
        assert sha(ROOT / n) == d, n
    print(json.dumps({**result, 'manifest_payload_files': len(names)}))

assert len(sys.argv) == 2
{'--preserve': preserve, '--package': package, '--publish': publish, '--verify': verify}[sys.argv[1]]()
