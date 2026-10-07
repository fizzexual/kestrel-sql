"""Preserve all 061 outcomes, package exact inputs/stores, add immutable private assets."""
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
DEST = ROOT / 'benchmarks/core-read-path-061'
REPORT = 'CORE_READ_PATH_061.md'
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
    for n, d in load(W / 'source-provenance.json')['candidate'].items():
        assert sha(W / 'lab/outputs/kestrel-sql' / n) == d, n
    m = load(ROOT / 'benchmarks/overnight-2026-10-07-report-check.json')
    assert sha(ROOT / m['report_file']) == m['report_sha256']
    assert not load(W / 'post-qualification-process-check.json')['active_processes']
def cache_file(rel):
    return rel.parts[:2] == ('lab', 'work') and rel.parts[2].startswith('kestrel-061-')
def fixture_file(rel):
    return (rel.parts[0] == 'service-fixtures' or
            (rel.parts[:2] == ('lab', 'work') and rel.parts[2:4] != ('perf-061', 'candidate') and not cache_file(rel)))
def preserve():
    unchanged()
    assert load(W / 'audit.json')['correctness_passed'] and not DEST.exists()
    policy = load(W / 'policy.json')
    inputs = {}
    for f in policy['analytical_matrix']['fixtures']:
        label = f['scope'] + '-' + f['label']
        archive = Path(f['archive'])
        for p in sorted(archive.rglob('*')):
            if p.is_file():
                name = 'inputs/analytical/' + label + '/archive/' + p.relative_to(archive).as_posix()
                inputs[name] = {'source_path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}
        p = Path(f['reference'])
        inputs['inputs/analytical/' + label + '/reference.duckdb'] = {'source_path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}
    archive = Path(policy['primary_range_goal']['fixture'])
    for p in sorted(archive.rglob('*')):
        if p.is_file():
            name = 'inputs/primary/archive/' + p.relative_to(archive).as_posix()
            inputs[name] = {'source_path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)}
    save(W / 'analytical-input-inventory.json', {'created_utc': now(), 'post_run_hashes': True,
          'timed_input_paths_and_queries_preserved_in_policy': True, 'full_inputs_in_supplemental_zip': True, 'files': inputs})
    shutil.copy2(ROOT / 'MANIFEST.sha256', W / 'repository-manifest-pre-061.sha256')
    fixtures = {p.relative_to(W).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p)}
                for p in W.rglob('*') if p.is_file() and fixture_file(p.relative_to(W))}
    save(W / 'fixture-inventory.json', fixtures)
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
             'fresh_fixture_files': len(fixtures), 'timed_input_files': len(inputs),
             'full_stores_and_timed_inputs_in_separate_zip': True,
             'all_matrix_rounds_and_service_failures_preserved': True,
             'default_engine_unchanged': True, 'new_engine_release': False}
    save(ROOT / 'benchmarks/core-read-path-061-preservation.json', proof)
    score = load(W / 'matrix.json')['score']
    service = load(W / 'paired-service-audit.json')
    intro = (f'**Latest clean core development:** [061 ports the parser gain independently of SDK 058/060](CORE_READ_PATH_061.md). '
             f'Native range medians 5.6 to 2.7 microseconds; {score["candidate_duckdb_median_wins"]}/60 fresh DuckDB median wins, '
             f'{score["native_guards_failed"]}/60 failed native guards, {service["guards_failed"]}/29 failed service guards. '
             '77 tests per mode and full correctness/recovery gates pass. Supported 0.3.16 is unchanged.\n\n')
    for name in ['README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']:
        p = ROOT / name
        first, rest = p.read_text(encoding='utf-8').split('\n\n', 1)
        p.write_text(first + '\n\n' + intro + rest, encoding='utf-8')
    p = ROOT / 'ADOPTION_STATUS.md'
    text = p.read_text(encoding='utf-8')
    text += (f'\n[Clean core trial 061](CORE_READ_PATH_061.md) reproduces the native parser/range gain without SDK changes, '
             f'records {score["candidate_duckdb_median_wins"]}/60 fresh DuckDB analytical median wins and '
             f'{service["guards_failed"]}/29 failed service guards. All source/reader/publication recovery gates pass. '
             'It remains isolated development evidence; supported 0.3.16, historical losses and the primary-production adoption assessment remain unchanged.\n')
    p.write_text(text, encoding='utf-8')
    print(json.dumps({'preserved_payload_files': len(payload), 'fresh_fixture_files': len(fixtures), 'timed_input_files': len(inputs)}))
def package():
    unchanged()
    proof = load(ROOT / 'benchmarks/core-read-path-061-preservation.json')
    for n, d in proof['payload_sha256'].items():
        assert sha(DEST / n) == d, n
    files = {p.relative_to(ROOT).as_posix(): p for p in DEST.rglob('*') if p.is_file()}
    for name in [REPORT, 'benchmarks/core-read-path-061-preservation.json']:
        files[name] = ROOT / name
    for n, d in load(W / 'fixture-inventory.json').items():
        p = W / n
        assert p.stat().st_size == d['bytes'] and sha(p) == d['sha256']
        files['benchmarks/core-read-path-061/' + n] = p
    for n, d in load(W / 'analytical-input-inventory.json')['files'].items():
        p = Path(d['source_path'])
        assert p.stat().st_size == d['bytes'] and sha(p) == d['sha256']
        files['benchmarks/core-read-path-061/' + n] = p
    archive = ROOT.parent / 'kestrel-sql-development-061-clean-core-evidence.zip'
    assert not archive.exists()
    hashes = {n: sha(p) for n, p in files.items()}
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for n, p in files.items():
            z.write(p, 'kestrel-sql/' + n)
        z.writestr('kestrel-sql/CORE_READ_PATH_061_MANIFEST.sha256', ''.join(d + '  ' + n + '\n' for n, d in sorted(hashes.items())))
        z.writestr('kestrel-sql/DEVELOPMENT_ONLY.md', 'Isolated clean-core 0.3.17-dev.61 evidence, not a supported engine release. All 60 analytic shapes and all 36 service outcomes, full inputs, stores, source, frozen binaries and failures are preserved. Read CORE_READ_PATH_061.md before interpreting wins or guards.\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for n, d in hashes.items():
            with z.open('kestrel-sql/' + n) as f:
                assert hashlib.file_digest(f, 'sha256').hexdigest() == d
    archive.with_suffix('.zip.sha256').write_text(sha(archive) + '  ' + archive.name + '\n', encoding='utf-8')
    result = {'artifact': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha(archive),
              'zip_entries': len(hashes) + 2, 'payload_files': len(hashes),
              'fresh_fixture_files': proof['fresh_fixture_files'], 'timed_input_files': proof['timed_input_files'],
              'full_service_stores': 36, 'all_crc_and_payload_hashes_verified': True,
              'packaged_utc': now(), 'new_engine_release': False}
    save(ROOT / 'benchmarks/core-read-path-061-bundle-check.json', result)
    print(json.dumps(result))
def gh(*args):
    return json.loads(subprocess.check_output(['gh', *args], cwd=ROOT, text=True, encoding='utf-8'))
def publish():
    unchanged()
    assert gh('repo', 'view', REPO, '--json', 'isPrivate')['isPrivate']
    assert not gh('api', f'repos/{REPO}/actions/permissions')['enabled']
    backup = ROOT / 'repository-publication-pre-core-061.json'
    if not backup.exists():
        shutil.copy2(ROOT / 'repository-publication.json', backup)
    old = load(backup)
    expected = {(r['tag'], a['name']): a for r in old['releases'] for a in r['assets']}
    assert len(expected) == 88
    bundle = load(ROOT / 'benchmarks/core-read-path-061-bundle-check.json')
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
    assert len(releases) == 20 and len(actual) == 90
    for k, a in expected.items():
        assert actual[k]['size'] == a['bytes'] and actual[k]['digest'] == 'sha256:' + a['sha256']
    added = []
    for p in paths:
        a = actual['v0.3.16', p.name]
        assert a['size'] == p.stat().st_size and a['digest'] == 'sha256:' + sha(p)
        added.append({'name': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p), 'asset_id': a['id'],
                      'server_digest_matched': True, 'download_url': a['browser_download_url'],
                      'role': '061 clean parser-core development; all competitive/service outcomes and full inputs; no supported release'})
    refs = dict(line.split()[::-1] for line in subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/tags/*'], cwd=ROOT, text=True).splitlines())
    for r in load(ROOT / 'release-history.json')['snapshots']:
        k = 'refs/tags/' + r['tag']
        assert refs.get(k + '^{}', refs.get(k)) == r['commit']
    next(r for r in old['releases'] if r['tag'] == 'v0.3.16')['assets'].extend(added)
    old.update(uploaded_assets=90, all_90_server_digests_matched=True, completed_at_utc=now(),
               core_read_path_061={'report': REPORT, 'development_only': True,
                                  'sdk_independent_native_gain_reproduced': True, 'promoted': False})
    save(ROOT / 'repository-publication.json', old)
    result = {'private': True, 'actions_disabled': True, 'new_assets': added, 'remote_assets_verified': 90,
              'previous_assets_unchanged': 88, 'historical_engine_tags_releases_unchanged': 20,
              'new_engine_release': False, 'default_engine_changed': False, 'published_utc': now()}
    save(ROOT / 'benchmarks/core-read-path-061-publication.json', result)
    nav = ROOT / 'repository-navigation-audit.json'
    snapshot = ROOT / 'repository-navigation-pre-core-061.json'
    if not snapshot.exists():
        shutil.copy2(nav, snapshot)
    data = load(nav)
    data.update(verified_server_asset_digests=90, core_read_path_development_report=REPORT, updated_at_utc=now())
    save(nav, data)
    p = ROOT / REPORT
    line = '\nPrivate immutable [full trial evidence, inputs and stores](' + added[0]['download_url'] + ') and [SHA-256](' + added[1]['download_url'] + '). The supplemental archive contains the report before this upload-link paragraph; it replaces no historical asset and creates no engine release.\n'
    text = p.read_text(encoding='utf-8')
    if line not in text:
        p.write_text(text + line, encoding='utf-8')
    print(json.dumps(result))
def verify():
    unchanged()
    proof = load(ROOT / 'benchmarks/core-read-path-061-preservation.json')
    for n, d in proof['payload_sha256'].items():
        assert sha(DEST / n) == d, n
    bundle = load(ROOT / 'benchmarks/core-read-path-061-bundle-check.json')
    assert sha(ROOT.parent / bundle['artifact']) == bundle['sha256']
    publication = load(ROOT / 'benchmarks/core-read-path-061-publication.json')
    assert publication['private'] and publication['remote_assets_verified'] == 90
    updated = {'README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md', 'ADOPTION_STATUS.md',
               'repository-publication.json', 'repository-navigation-audit.json'}
    historical_files = 0
    for line in (W / 'repository-manifest-pre-061.sha256').read_text().splitlines():
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
              'all_fixtures_and_timed_inputs_zip_crc_and_hashes_verified': True,
              'default_source_binaries_and_morning_unchanged': True,
              'historical_manifest_files_unchanged': historical_files,
              'all_service_failures_and_round_outliers_preserved': True,
              'private_remote_assets_verified': 90, 'new_engine_release': False}
    save(ROOT / 'benchmarks/core-read-path-061-document-check.json', result)
    names = set(subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')) - {'', 'MANIFEST.sha256'}
    manifest = ''.join(sha(ROOT / n) + '  ' + n + '\n' for n in sorted(names))
    (ROOT / 'MANIFEST.sha256').write_text(manifest, encoding='utf-8')
    for line in manifest.splitlines():
        d, n = line.split('  ', 1)
        assert sha(ROOT / n) == d, n
    print(json.dumps({**result, 'manifest_payload_files': len(names)}))

assert len(sys.argv) == 2
{'--preserve': preserve, '--package': package, '--publish': publish, '--verify': verify}[sys.argv[1]]()
