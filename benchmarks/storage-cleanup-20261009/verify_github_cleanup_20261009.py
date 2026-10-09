"""Verify redundant top-level packages against existing private GitHub assets.

No deletion, upload, native benchmark, or performance timer is performed here.
Every selected remote asset is downloaded into a streaming hash, never a file.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/Codex/Kestrel')
OUTPUTS = ROOT / 'outputs'
REPO = OUTPUTS / 'kestrel-sql'
EVIDENCE = ROOT / 'work/storage-cleanup-20261009-0841'
GH = r'C:\Users\Frizer\AppData\Local\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe'
REMOTE = 'repos/fizzexual/kestrel-sql'
FLAGS = subprocess.CREATE_NO_WINDOW


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(name, value):
    p = EVIDENCE / name
    assert not p.exists(), p
    p.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def api(endpoint):
    result = subprocess.run([GH, 'api', endpoint], capture_output=True,
                            creationflags=FLAGS, check=True)
    return json.loads(result.stdout)


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def real_directory(p):
    assert p.is_dir() and not p.is_symlink() and not p.is_junction(), p
    assert p.resolve() == p, p


for p in (ROOT, OUTPUTS, REPO, ROOT / 'work'):
    real_directory(p)
assert not EVIDENCE.exists()
EVIDENCE.mkdir()
save('authorization.json', {
    'utc': utc(),
    'user_instruction': 'Also any not usable things(benchmark too) delete them when we have them in github',
    'scope': 'Only redundant, non-current ZIP files immediately inside D:/Codex/Kestrel/outputs.',
    'verification': 'Private GitHub asset metadata, local complete SHA256/size/sidecar, and complete streaming remote download SHA256/size.',
    'keep': ['supported 0.3.16 package and service evidence', '061 archive for planned integration',
             'all original benchmark stores, source, failures and raw results',
             'tracked repository files and every Git commit', 'all unmatched or unverified files',
             'sidecars and package-check records', 'all newer experiments not yet on GitHub'],
    'no_reset_or_app_interference': True,
})
repository = api(REMOTE)
assert repository['private'] is True and repository['full_name'] == 'fizzexual/kestrel-sql'
save('github-repository.json', {
    'utc': utc(), 'full_name': repository['full_name'], 'private': repository['private'],
    'default_branch': repository['default_branch'], 'pushed_at': repository['pushed_at'],
})
branch = api(REMOTE + '/branches/main')
save('github-main.json', {'utc': utc(), 'sha': branch['commit']['sha']})
assets = {}
releases = []
page = 1
while True:
    current = api(REMOTE + f'/releases?per_page=100&page={page}')
    if not current:
        break
    for release in current:
        releases.append({k: release[k] for k in ('id', 'tag_name', 'draft', 'prerelease', 'html_url')})
        if release['draft']:
            continue
        for asset in release['assets']:
            item = {k: asset[k] for k in ('id', 'name', 'size', 'digest', 'state', 'browser_download_url', 'updated_at')}
            item['release_tag'] = release['tag_name']
            assets.setdefault(asset['name'], []).append(item)
    if len(current) < 100:
        break
    page += 1
save('github-releases-and-assets.json', {'utc': utc(), 'releases': releases, 'assets': assets})
selected = []
retained = []
for p in sorted(OUTPUTS.glob('*.zip')):
    reason = None
    if p.name.startswith('kestrel-sql-0.3.16'):
        reason = 'current supported release/service archive'
    elif p.name.startswith('kestrel-sql-development-061-'):
        reason = 'archive retained for planned analytical integration'
    elif p.is_symlink() or p.is_junction() or p.resolve().parent != OUTPUTS:
        reason = 'noncanonical or reparse file'
    elif len(assets.get(p.name, [])) != 1:
        reason = 'no unique existing published GitHub asset with exact name'
    if reason:
        retained.append({'path': str(p), 'bytes': p.stat().st_size, 'reason': reason})
        continue
    asset = assets[p.name][0]
    if asset['state'] != 'uploaded' or not re.fullmatch(r'sha256:[0-9a-f]{64}', asset['digest'] or ''):
        retained.append({'path': str(p), 'bytes': p.stat().st_size, 'reason': 'remote digest/state unavailable'})
        continue
    selected.append({'path': str(p), 'bytes': p.stat().st_size, 'asset': asset})
save('selection.json', {'utc': utc(), 'selected': selected, 'retained': retained})
verified = []
failed = []
for index, item in enumerate(selected):
    p = Path(item['path'])
    asset = item['asset']
    expected = asset['digest'][7:]
    print(f'[{index + 1}/{len(selected)}] verifying {p.name}', flush=True)
    before = p.stat()
    local = sha(p)
    sidecar = Path(str(p) + '.sha256')
    sidecar_text = sidecar.read_text(encoding='utf-8-sig').strip() if sidecar.is_file() else ''
    sidecar_ok = sidecar_text.split()[0].lower() == expected if sidecar_text else False
    record = {**item, 'local_sha256': local, 'sidecar': str(sidecar), 'sidecar_matches': sidecar_ok,
              'before_mtime_ns': before.st_mtime_ns}
    if before.st_size != asset['size'] or local != expected or not sidecar_ok:
        record.update({'verified': False, 'reason': 'local hash/size/sidecar mismatch'})
        failed.append(record)
        save(f'asset-{asset["id"]}-verification.json', record)
        continue
    stderr_path = EVIDENCE / f'asset-{asset["id"]}-download.stderr'
    digest = hashlib.sha256()
    received = 0
    prefix = b''
    with stderr_path.open('xb') as stderr:
        child = subprocess.Popen([GH, 'api', REMOTE + f'/releases/assets/{asset["id"]}',
                                  '-H', 'Accept: application/octet-stream'],
                                 stdout=subprocess.PIPE, stderr=stderr, creationflags=FLAGS)
        assert child.stdout is not None
        while True:
            block = child.stdout.read(1024 * 1024)
            if not block:
                break
            if received == 0:
                prefix = block[:4]
            received += len(block)
            digest.update(block)
        exit_code = child.wait()
    after = p.stat()
    record.update({'download_exit_code': exit_code, 'download_bytes': received,
                   'download_sha256': digest.hexdigest(), 'download_zip_prefix': prefix.hex(),
                   'stderr_sha256': sha(stderr_path), 'verified_utc': utc()})
    ok = (exit_code == 0 and received == before.st_size and digest.hexdigest() == expected
          and prefix == b'PK\x03\x04' and after.st_size == before.st_size
          and after.st_mtime_ns == before.st_mtime_ns)
    record['verified'] = ok
    save(f'asset-{asset["id"]}-verification.json', record)
    if ok:
        verified.append(record)
        print(f'verified {p.name}: {received} bytes', flush=True)
    else:
        record['reason'] = 'remote complete download or local stability failed'
        failed.append(record)
        print(f'RETAIN {p.name}: remote verification failed', flush=True)
save('verified-deletion-plan.json', {'complete': True, 'utc': utc(),
    'remote_private_verified': True, 'remote_main_sha': branch['commit']['sha'],
    'only_top_level_redundant_zip_files': True, 'recursive_deletion': False,
    'entries': verified, 'files': len(verified), 'bytes': sum(x['bytes'] for x in verified),
    'failed_retained': failed, 'selection_retained': retained,
    'no_file_deleted_by_verifier': True})
print(json.dumps({'verified_files': len(verified), 'verified_bytes': sum(x['bytes'] for x in verified),
                  'failed_retained': len(failed), 'otherwise_retained': len(retained)}), flush=True)
