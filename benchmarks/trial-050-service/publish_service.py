from pathlib import Path
import subprocess, hashlib, json, datetime, shutil

w = Path(__file__).parent
root = w.parents[1] / 'outputs/kestrel-sql'
repo = 'fizzexual/kestrel-sql'
def gh(*args):
    return json.loads(subprocess.check_output(['gh', *args], cwd=root, text=True, encoding='utf-8'))
def sha(p):
    return hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()
assert gh('repo', 'view', repo, '--json', 'isPrivate')['isPrivate']
assert not gh('api', f'repos/{repo}/actions/permissions')['enabled']
old = json.loads((root / 'repository-publication.json').read_text(encoding='utf-8'))
expected = {(v['tag'], a['name']): a for v in old['releases'] for a in v['assets']}
assert len(expected) == 66
releases = gh('api', f'repos/{repo}/releases?per_page=100')
actual = {(v['tag_name'], a['name']): a for v in releases for a in v['assets']}
assert len(releases) == 20 and set(actual) == set(expected)
for key, asset in expected.items():
    assert actual[key]['size'] == asset['bytes'] and actual[key]['digest'] == 'sha256:' + asset['sha256'], key
package = root.parent / 'kestrel-sql-development-cat5-050-service-evidence.zip'
paths = [package, package.with_suffix('.zip.sha256')]
check = json.loads((root / 'benchmarks/trial-050-service-bundle-check.json').read_text(encoding='utf-8'))
assert sha(package) == check['sha256'] and package.stat().st_size == check['bytes']
assert all(('v0.3.16', p.name) not in actual for p in paths)
backup = root / 'repository-publication-pre-trial-050-service.json'
assert not backup.exists()
shutil.copy2(root / 'repository-publication.json', backup)
subprocess.run(['gh', 'release', 'upload', 'v0.3.16', *map(str, paths), '--repo', repo], cwd=root, check=True)
releases = gh('api', f'repos/{repo}/releases?per_page=100')
actual = {(v['tag_name'], a['name']): a for v in releases for a in v['assets']}
assert len(releases) == 20 and len(actual) == 68
for key, asset in expected.items():
    assert actual[key]['size'] == asset['bytes'] and actual[key]['digest'] == 'sha256:' + asset['sha256'], key
added = []
for p in paths:
    asset = actual['v0.3.16', p.name]
    assert asset['size'] == p.stat().st_size and asset['digest'] == 'sha256:' + sha(p)
    added.append({'name': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p), 'server_digest_matched': True,
                  'download_url': asset['browser_download_url'], 'asset_id': asset['id'],
                  'role': 'Unreleased 050 service evidence; frozen correctness/source artifact is separate'})
refs = dict(line.split()[::-1] for line in subprocess.check_output(['git', 'ls-remote', 'origin', 'refs/tags/*'], cwd=root, text=True).splitlines())
for version in json.loads((root / 'release-history.json').read_text(encoding='utf-8'))['snapshots']:
    key = 'refs/tags/' + version['tag']
    assert refs.get(key + '^{}', refs.get(key)) == version['commit'], version['tag']
next(v for v in old['releases'] if v['tag'] == 'v0.3.16')['assets'].extend(added)
audit = json.loads((w / 'paired-service-audit.json').read_text(encoding='utf-8'))
old.update(uploaded_assets=68, all_68_server_digests_matched=True,
           completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
           development_trial_050_service={'report': 'SERVICE_TRIAL_050.md', 'promoted': False,
                                           'default_engine_changed': False, 'new_engine_release': False,
                                           'performance_gates_passed': audit['performance_gates_passed']})
(root / 'repository-publication.json').write_text(json.dumps(old, indent=2) + '\n', encoding='utf-8')
proof = {'repository': repo, 'private': True, 'actions_disabled': True, 'new_assets': added,
         'all_remote_asset_sizes_and_digests_verified': 68, 'original_assets_unchanged': 66,
         'historical_tags_and_releases_unchanged': 20, 'new_engine_release': False,
         'default_engine_changed': False, 'trial_promoted': False,
         'prior_publication_sha256': sha(backup), 'completed_utc': old['completed_at_utc']}
(root / 'benchmarks/trial-050-service-publication.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
nav = root / 'repository-navigation-audit.json'
shutil.copy2(nav, root / 'repository-navigation-pre-trial-050-service.json')
value = json.loads(nav.read_text(encoding='utf-8'))
value.update(verified_server_asset_digests=68, development_trial_report='SERVICE_TRIAL_050.md',
             development_trial_promoted=False, development_trial_tests_each_mode=85,
             updated_at_utc=old['completed_at_utc'])
nav.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
p = root / 'SERVICE_TRIAL_050.md'
s = p.read_text(encoding='utf-8')
s += '\nPrivate immutable [fresh service evidence download](' + added[0]['download_url'] + ') and [SHA-256](' + added[1]['download_url'] + '); frozen source/binaries and preceding gates are in the separate [correctness evidence](https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-cat5-050-correctness-evidence.zip). Original supported release archives remain unchanged. The bundle preserves this report before the final upload-link paragraph; publication proof lives in the repository.\n'
p.write_text(s, encoding='utf-8')
print(json.dumps(proof))
