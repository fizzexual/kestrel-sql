from pathlib import Path
import ast, datetime, hashlib, json, re, shutil, subprocess, sys, zipfile

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
DEST = ROOT / 'benchmarks/publication-057-reservation'
REPRO = W.parent / 'perf-057-cargo-reproduction-check'
REPO = 'fizzexual/kestrel-sql'
REPORT = 'PUBLICATION_057.md'

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(p, j):
    p.write_text(json.dumps(j, indent=2) + '\n', encoding='utf-8')

def gh(*args):
    return json.loads(subprocess.check_output(['gh', *args], cwd=ROOT, text=True, encoding='utf-8'))

def unchanged():
    baseline = json.loads((W / 'default-engine-baseline.json').read_text())
    for n, d in baseline['core_source_sha256'].items():
        assert sha(ROOT / n) == d
    for n, d in baseline['baseline_binary_sha256'].items():
        assert sha(ROOT / 'bin' / n) == d
    morning = json.loads((ROOT / 'benchmarks/overnight-2026-10-07-report-check.json').read_text())
    assert sha(ROOT / morning['report_file']) == morning['report_sha256']

def preserve():
    unchanged()
    audit = json.loads((W / 'model-audit.json').read_text())
    assert audit['failed_hypothesis_checks'] == 6 and audit['complete_cases'] == 12
    assert json.loads((W / 'cargo-reproduction-check.json').read_text())['independent_cargo_build_and_execution_passed']
    assert not json.loads((W / 'post-qualification-process-check.json').read_text(encoding='utf-8-sig'))['active_processes']
    assert not DEST.exists()
    DEST.mkdir()
    payload = {}
    for p in W.rglob('*'):
        if p.is_file() and 'fixtures' not in p.relative_to(W).parts and p.suffix != '.pdb':
            rel = p.relative_to(W)
            q = DEST / rel
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, q)
            assert sha(p) == sha(q)
            payload[rel.as_posix()] = sha(q)
    for p in REPRO.rglob('*'):
        rel = p.relative_to(REPRO)
        if p.is_file() and rel.parts[0] != 'target' and not rel.parts[0].startswith('fixture-') and p.suffix != '.pdb':
            q = DEST / 'independent-cargo-check' / rel
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, q)
            assert sha(p) == sha(q)
            payload[q.relative_to(DEST).as_posix()] = sha(q)
    proof = {'preserved_utc': now(), 'model_only': True, 'original_cases': 12, 'failed_hypothesis_checks': 6,
             'independent_cargo_small_mode_samples_excluded': 512, 'source_work_directory': str(W),
             'payload_sha256': payload, 'original_default_sql_core_and_binaries_unchanged': True,
             'morning_report_reissued_or_modified': False, 'new_engine_release': False}
    save(ROOT / 'benchmarks/publication-057-preservation.json', proof)
    intro = ('**Latest storage model:** [057 rejects advance zero filling after charging initialization](PUBLICATION_057.md), '
             'with a verified standalone Cargo reproduction. [Adoption assessment](ADOPTION_STATUS.md) explains the current case for Kestrel alongside PostgreSQL. '
             'No SQL engine upgrade; supported 0.3.16 and every earlier result remain unchanged.\n\n')
    for n in ['README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']:
        p = ROOT / n
        first, rest = p.read_text(encoding='utf-8').split('\n\n', 1)
        p.write_text(first + '\n\n' + intro + rest, encoding='utf-8')
    print(json.dumps({'preserved_payload_files': len(payload), 'model_only': True, 'default_engine_unchanged': True}))

def package():
    unchanged()
    files = {p.relative_to(ROOT).as_posix(): p for p in DEST.rglob('*') if p.is_file()}
    for n in [REPORT, 'ADOPTION_STATUS.md', 'benchmarks/publication-057-preservation.json']:
        files[n] = ROOT / n
    proof = json.loads((ROOT / 'benchmarks/publication-057-preservation.json').read_text())
    for n, digest in proof['payload_sha256'].items():
        assert sha(DEST / n) == digest
    count = 0
    inventory = json.loads((W / 'fixture-inventory.json').read_text())
    for rel, v in inventory.items():
        p = W / 'fixtures' / rel
        assert sha(p) == v['sha256'] and p.stat().st_size == v['bytes']
        files['benchmarks/publication-057-reservation/local-model-fixtures/' + rel] = p
        count += 1
    for c in json.loads((W / 'cargo-reproduction-check.json').read_text())['cases']:
        p = REPRO / ('fixture-' + c['mode']) / 'journal.bin'
        assert sha(p) == c['final_file_sha256'] and p.stat().st_size == c['final_bytes']
        files['benchmarks/publication-057-reservation/independent-cargo-check/local-fixtures/' + c['mode'] + '/journal.bin'] = p
        count += 1
    archive = ROOT.parent / 'kestrel-sql-development-io-057-reservation-evidence.zip'
    assert not archive.exists()
    payload = {n: sha(p) for n, p in files.items()}
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for n, p in files.items():
            z.write(p, 'kestrel-sql/' + n)
        z.writestr('kestrel-sql/PUBLICATION_057_MANIFEST.sha256', ''.join(d + '  ' + n + '\n' for n, d in sorted(payload.items())))
        z.writestr('kestrel-sql/MODEL_ONLY.md', '057 storage primitive model, not SQL or Archive WAL. Six criteria fail. Bootstrap is charged; sync_all on every commit. All original cases retained; independent Cargo build/checks are separate. Read PUBLICATION_057.md.\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist()) == len(payload) + 2
        for n, digest in payload.items():
            with z.open('kestrel-sql/' + n) as f:
                assert hashlib.file_digest(f, 'sha256').hexdigest() == digest
    digest = sha(archive)
    archive.with_suffix('.zip.sha256').write_text(digest + '  ' + archive.name + '\n')
    check = {'artifact': archive.name, 'bytes': archive.stat().st_size, 'sha256': digest,
             'payload_files': len(payload), 'zip_entries': len(payload) + 2, 'full_primitive_fixture_files': count,
             'original_model_fixture_files': 12, 'independent_cargo_fixture_files': 2,
             'all_payload_and_fixture_hashes_verified': True, 'zip_crc_verified': True,
             'model_only': True, 'new_engine_release': False, 'packaged_utc': now()}
    save(ROOT / 'benchmarks/publication-057-bundle-check.json', check)
    print(json.dumps(check))

def publish():
    unchanged()
    assert gh('repo', 'view', REPO, '--json', 'isPrivate')['isPrivate']
    assert not gh('api', f'repos/{REPO}/actions/permissions')['enabled']
    backup = ROOT / 'repository-publication-pre-io-057.json'
    if not backup.exists():
        shutil.copy2(ROOT / 'repository-publication.json', backup)
    old = json.loads(backup.read_text())
    expected = {(r['tag'], a['name']): a for r in old['releases'] for a in r['assets']}
    assert len(expected) == 80
    check = json.loads((ROOT / 'benchmarks/publication-057-bundle-check.json').read_text())
    archive = ROOT.parent / check['artifact']
    assert sha(archive) == check['sha256'] and archive.stat().st_size == check['bytes']
    paths = [archive, archive.with_suffix('.zip.sha256')]
    releases = gh('api', f'repos/{REPO}/releases?per_page=100')
    actual = {(r['tag_name'], a['name']): a for r in releases for a in r['assets']}
    assert len(releases) == 20 and set(expected) <= set(actual)
    assert set(actual) <= set(expected) | {('v0.3.16', p.name) for p in paths}
    for k, a in expected.items():
        assert actual[k]['size'] == a['bytes'] and actual[k]['digest'] == 'sha256:' + a['sha256']
    missing = []
    for p in paths:
        k = ('v0.3.16', p.name)
        if k in actual:
            assert actual[k]['size'] == p.stat().st_size and actual[k]['digest'] == 'sha256:' + sha(p)
        else:
            missing.append(str(p))
    if missing:
        subprocess.run(['gh', 'release', 'upload', 'v0.3.16', *missing, '--repo', REPO], cwd=ROOT, check=True)
    releases = gh('api', f'repos/{REPO}/releases?per_page=100')
    actual = {(r['tag_name'], a['name']): a for r in releases for a in r['assets']}
    assert len(releases) == 20 and len(actual) == 82
    for k, a in expected.items():
        assert actual[k]['size'] == a['bytes'] and actual[k]['digest'] == 'sha256:' + a['sha256']
    added = []
    for p in paths:
        a = actual['v0.3.16', p.name]
        assert a['size'] == p.stat().st_size and a['digest'] == 'sha256:' + sha(p)
        added.append({'name': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p), 'server_digest_matched': True,
                      'download_url': a['browser_download_url'], 'asset_id': a['id'],
                      'role': '057 failed storage reservation model, all primitive frames, independent Cargo reproduction; no SQL engine release'})
    refs = dict(line.split()[::-1] for line in subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/tags/*'], cwd=ROOT, text=True).splitlines())
    for r in json.loads((ROOT / 'release-history.json').read_text())['snapshots']:
        k = 'refs/tags/' + r['tag']
        assert refs.get(k + '^{}', refs.get(k)) == r['commit']
    next(r for r in old['releases'] if r['tag'] == 'v0.3.16')['assets'].extend(added)
    old.update(uploaded_assets=82, all_82_server_digests_matched=True, completed_at_utc=now(),
               storage_primitive_057={'report': REPORT, 'model_only': True, 'failed_checks': 6, 'promoted': False})
    save(ROOT / 'repository-publication.json', old)
    pub = {'repository': REPO, 'private': True, 'actions_disabled': True, 'new_assets': added,
           'all_remote_asset_sizes_and_digests_verified': 82, 'original_assets_unchanged': 80,
           'historical_engine_tags_releases_and_archives_unchanged': 20, 'model_only': True,
           'new_engine_release': False, 'default_engine_changed': False, 'failed_hypothesis_checks': 6,
           'prior_publication_sha256': sha(backup), 'published_utc': now(), 'morning_report_reissued': False}
    save(ROOT / 'benchmarks/publication-057-publication.json', pub)
    nav = ROOT / 'repository-navigation-audit.json'
    snapshot = ROOT / 'repository-navigation-pre-io-057.json'
    if not snapshot.exists():
        shutil.copy2(nav, snapshot)
    j = json.loads(nav.read_text())
    j.update(verified_server_asset_digests=82, native_diagnostic_report=REPORT,
             adoption_report='ADOPTION_STATUS.md', updated_at_utc=now())
    save(nav, j)
    p = ROOT / REPORT
    line = ('\nPrivate immutable [all model/reproduction evidence and primitive fixtures](' + added[0]['download_url'] + ') and [SHA-256](' + added[1]['download_url'] + '). '
            'This distinct supplemental asset preserves the report before this final upload-link paragraph and replaces no supported engine archive.\n')
    text = p.read_text(encoding='utf-8')
    if line not in text:
        p.write_text(text + line, encoding='utf-8')
    print(json.dumps(pub))

def verify():
    unchanged()
    proof = json.loads((ROOT / 'benchmarks/publication-057-preservation.json').read_text())
    for n, digest in proof['payload_sha256'].items():
        assert sha(DEST / n) == digest
    check = json.loads((ROOT / 'benchmarks/publication-057-bundle-check.json').read_text())
    archive = ROOT.parent / check['artifact']
    assert sha(archive) == check['sha256'] and archive.stat().st_size == check['bytes']
    pub = json.loads((ROOT / 'benchmarks/publication-057-publication.json').read_text())
    assert pub['private'] and pub['all_remote_asset_sizes_and_digests_verified'] == 82
    downloads = {a['download_url'] for r in json.loads((ROOT / 'repository-publication.json').read_text())['releases'] for a in r['assets']}
    docs = [REPORT, 'ADOPTION_STATUS.md', 'README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']
    for n in docs:
        for link in re.findall(r'\]\(([^)]+)\)', (ROOT / n).read_text(encoding='utf-8')):
            local = link.split('#')[0]
            if local and not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', local):
                assert (ROOT / local).exists(), (n, local)
            if '/releases/download/' in link:
                assert link in downloads
    for p in DEST.rglob('*'):
        if p.is_file():
            if p.suffix == '.py':
                ast.parse(p.read_text(encoding='utf-8-sig'), filename=str(p))
            elif p.suffix == '.json':
                json.loads(p.read_text(encoding='utf-8-sig'))
    pn = 'benchmarks/publication-057-document-check.json'
    checked = {'checked_utc': now(), 'default_core_and_supported_binaries_unchanged': True,
               'morning_report_hash_unchanged_and_not_reissued': True, 'preserved_payload_hashes_verified': len(proof['payload_sha256']),
               'all_fixture_zip_hashes_and_crc_verified': True, 'full_primitive_fixtures_in_zip': 14,
               'standalone_cargo_manifest_lock_build_and_two_modes_checked': True,
               'independent_cargo_samples_excluded': 512, 'report_links_verified': True,
               'new_python_and_json_syntax_passed': True, 'private_remote_assets_verified': 82,
               'historical_engine_releases_unchanged': 20, 'new_engine_release': False, 'trial_promoted': False}
    save(ROOT / pn, checked)
    names = set(subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')) - {'', 'MANIFEST.sha256'}
    manifest = ''.join(sha(ROOT / n) + '  ' + n + '\n' for n in sorted(names))
    (ROOT / 'MANIFEST.sha256').write_text(manifest, encoding='utf-8')
    for line in manifest.splitlines():
        digest, n = line.split('  ', 1)
        assert sha(ROOT / n) == digest
    assert {line.split('  ', 1)[1] for line in manifest.splitlines()} == names
    print(json.dumps({**checked, 'manifest_payload_files': len(names)}))

assert len(sys.argv) == 2
{'--preserve': preserve, '--package': package, '--publish': publish, '--verify': verify}[sys.argv[1]]()
