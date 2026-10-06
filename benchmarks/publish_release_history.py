"""Upload preserved archives to an explicitly requested private GitHub repository.

No benchmarking, deployment, force push, release replacement or public sharing.
Resume uploads only when existing assets have matching bytes and server digests.
"""
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = 'fizzexual/kestrel-sql'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def gh_json(*arguments):
    return json.loads(subprocess.check_output(['gh', *arguments], cwd=ROOT, text=True))


def main():
    inventory = json.loads((ROOT / 'release-history.json').read_text())
    assert inventory['repository'] == 'https://github.com/' + REPO
    assert gh_json('repo', 'view', REPO, '--json', 'isPrivate')['isPrivate'] is True
    assert gh_json('api', f'repos/{REPO}/actions/permissions')['enabled'] is False
    task = ROOT.parent.parent / 'work/github-publication'; task.mkdir(parents=True, exist_ok=True)
    state_path = task / 'publication-progress.json'
    state = {'repository': inventory['repository'], 'private': True, 'hosted_actions_disabled': True,
        'local_inventory_sha256': sha(ROOT / 'release-history.json'), 'releases': [], 'failures': []}
    # Put the latest download in reach first, then import all older assets.
    records = sorted(inventory['snapshots'], key=lambda r: (r['version'] != '0.3.7', r['original_packaged_at_utc']))
    for record in records:
        tag = record['tag']; archive = ROOT.parent / record['archive']
        assert sha(archive) == record['sha256'] and archive.stat().st_size == record['bytes']
        sidecar = archive.with_suffix('.zip.sha256')
        if not sidecar.exists(): sidecar.write_text(f"{record['sha256']}  {archive.name}\n", encoding='utf-8')
        assert sidecar.read_text().split()[0] == record['sha256']
        proof = ROOT.parent / (f"kestrel-sql-{record['version']}-package-check.json" if record['version'] != 'stress-tested' else 'kestrel-sql-stress-package-check.json')
        assets = [archive, sidecar] + ([proof] if proof.exists() else [])
        notes = task / (tag + '-notes.md')
        notes.write_text(f"{record['title']}.\n\nPreserved experimental snapshot, originally packaged {record['original_packaged_at_utc']}. This tag points to its exact historical source/report tree, not the current branch.\n\nDownload the ZIP for the original binaries, benchmarks, raw samples, previous baselines and reports. SHA-256: `{record['sha256']}`. Checksums and the original package-check proof are attached when available.\n\nWins, losses and unsuccessful experiments remain visible. These local Windows measurements do not establish production readiness, universal superiority or Facebook-scale qualification.\n\n[Browse the benchmark history](https://github.com/{REPO}/blob/main/BENCHMARK_HISTORY.md) | [All releases](https://github.com/{REPO}/releases)\n", encoding='utf-8')
        print(f'Publishing {tag} ({archive.stat().st_size/1e6:.2f} MB)', flush=True)
        try:
            lookup = subprocess.run(['gh','api',f'repos/{REPO}/releases/tags/{tag}'], cwd=ROOT, text=True, capture_output=True)
            if lookup.returncode != 0:
                assert 'HTTP 404' in lookup.stderr, lookup.stderr
                subprocess.run(['gh','release','create',tag,'--repo',REPO,'--verify-tag','--prerelease',
                    '--title',tag + ' - ' + record['title'],'--notes-file',str(notes)], cwd=ROOT, check=True)
            remote = gh_json('api', f'repos/{REPO}/releases/tags/{tag}')
            assert remote['tag_name'] == tag and remote['prerelease'] and not remote['draft']
            existing = {a['name']:a for a in remote['assets']}
            for asset in assets:
                if asset.name not in existing:
                    subprocess.run(['gh','release','upload',tag,str(asset),'--repo',REPO],cwd=ROOT,check=True)
            remote = gh_json('api', f'repos/{REPO}/releases/tags/{tag}')
            existing = {a['name']:a for a in remote['assets']}
            checked = []
            for asset in assets:
                value = existing[asset.name]
                assert value['size'] == asset.stat().st_size and value['state'] == 'uploaded'
                digest = value.get('digest')
                if digest is not None: assert digest == 'sha256:' + sha(asset), (tag, asset.name, digest)
                checked.append({'name':asset.name,'bytes':value['size'],'sha256':sha(asset),
                    'server_digest_matched':digest is not None,'download_url':value['browser_download_url']})
            state['releases'].append({'tag':tag,'url':remote['html_url'],'historical_commit':record['commit'],'assets':checked})
            print(f'{tag}: {len(checked)} assets uploaded and checked', flush=True)
        except Exception as error:
            state['failures'].append({'tag':tag,'error':repr(error)}); raise
        finally: state_path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    assert len(state['releases']) == 11 and not state['failures']
    assert gh_json('repo','view',REPO,'--json','isPrivate')['isPrivate'] is True
    state['completed_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state['all_uploaded_asset_sizes_checked'] = True
    state['all_server_digests_matched'] = all(a['server_digest_matched'] for r in state['releases'] for a in r['assets'])
    state_path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'private_repository':state['repository'],'preserved_releases':11,
        'all_server_digests_matched':state['all_server_digests_matched'],'hosted_actions_disabled':True}))


if __name__ == '__main__': main()
