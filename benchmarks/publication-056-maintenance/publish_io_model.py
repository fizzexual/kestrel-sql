from pathlib import Path
import datetime, hashlib, json, shutil, subprocess

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
REPO = 'fizzexual/kestrel-sql'

def gh(*args):
    return json.loads(subprocess.check_output(['gh', *args], cwd=ROOT, text=True, encoding='utf-8'))

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

assert gh('repo', 'view', REPO, '--json', 'isPrivate')['isPrivate']
assert not gh('api', f'repos/{REPO}/actions/permissions')['enabled']
backup = ROOT / 'repository-publication-pre-io-056.json'
if not backup.exists():
    shutil.copy2(ROOT / 'repository-publication.json', backup)
old = json.loads(backup.read_text())
expected = {(v['tag'], a['name']): a for v in old['releases'] for a in v['assets']}
assert len(expected) == 78
check = json.loads((ROOT / 'benchmarks/publication-056-bundle-check.json').read_text())
archive = ROOT.parent / check['artifact']
assert sha(archive) == check['sha256'] and archive.stat().st_size == check['bytes']
paths = [archive, archive.with_suffix('.zip.sha256')]
releases = gh('api', f'repos/{REPO}/releases?per_page=100')
actual = {(v['tag_name'], a['name']): a for v in releases for a in v['assets']}
assert len(releases) == 20 and set(expected) <= set(actual)
assert set(actual) <= set(expected) | {('v0.3.16', p.name) for p in paths}
for key, a in expected.items():
    assert actual[key]['size'] == a['bytes'] and actual[key]['digest'] == 'sha256:' + a['sha256'], key
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
actual = {(v['tag_name'], a['name']): a for v in releases for a in v['assets']}
assert len(releases) == 20 and len(actual) == 80
for key, a in expected.items():
    assert actual[key]['size'] == a['bytes'] and actual[key]['digest'] == 'sha256:' + a['sha256'], key
added = []
for p in paths:
    a = actual['v0.3.16', p.name]
    assert a['size'] == p.stat().st_size and a['digest'] == 'sha256:' + sha(p)
    added.append({'name': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p),
                  'server_digest_matched': True, 'download_url': a['browser_download_url'], 'asset_id': a['id'],
                  'role': 'Storage-only 056 model evidence, full primitive frames, two failed hypothesis checks; no SQL engine release'})
refs = dict(line.split()[::-1] for line in subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/tags/*'], cwd=ROOT, text=True).splitlines())
for v in json.loads((ROOT / 'release-history.json').read_text())['snapshots']:
    key = 'refs/tags/' + v['tag']
    assert refs.get(key + '^{}', refs.get(key)) == v['commit'], v['tag']
next(v for v in old['releases'] if v['tag'] == 'v0.3.16')['assets'].extend(added)
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
old.update(uploaded_assets=80, all_80_server_digests_matched=True, completed_at_utc=now,
           storage_primitive_056={'report': 'PUBLICATION_056.md', 'model_only': True, 'new_engine_code': False, 'all_checks_passed': False})
(ROOT / 'repository-publication.json').write_text(json.dumps(old, indent=2) + '\n')
proof = {'repository': REPO, 'private': True, 'actions_disabled': True, 'new_assets': added,
         'all_remote_asset_sizes_and_digests_verified': 80, 'original_assets_unchanged': 78,
         'historical_engine_tags_releases_and_archives_unchanged': 20, 'model_only': True,
         'new_engine_release': False, 'default_engine_changed': False, 'model_hypothesis_checks_failed': 2,
         'prior_publication_sha256': sha(backup), 'published_utc': now}
(ROOT / 'benchmarks/publication-056-publication.json').write_text(json.dumps(proof, indent=2) + '\n')
nav = ROOT / 'repository-navigation-audit.json'
nav_backup = ROOT / 'repository-navigation-pre-io-056.json'
if not nav_backup.exists():
    shutil.copy2(nav, nav_backup)
j = json.loads(nav.read_text())
j.update(verified_server_asset_digests=80, native_diagnostic_report='PUBLICATION_056.md',
         morning_report='OVERNIGHT_2026-10-07.md', morning_report_prepared=True, updated_at_utc=now)
nav.write_text(json.dumps(j, indent=2) + '\n')
p = ROOT / 'PUBLICATION_056.md'
s = p.read_text(encoding='utf-8')
sentence = ('\nPrivate immutable [full model evidence and primitive fixtures](' + added[0]['download_url'] + ') and [SHA-256](' + added[1]['download_url'] + '). '
            'This supplemental asset preserves the report before this final upload-link paragraph; it replaces no supported engine archive.\n')
if sentence not in s:
    p.write_text(s + sentence, encoding='utf-8')
print(json.dumps(proof))
