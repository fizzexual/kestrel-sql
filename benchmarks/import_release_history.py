"""Import immutable release snapshots as exact-byte Git commits and tags.

Use once in a new local repository, before pushing. Existing working files are
never checked out, overwritten or removed. Large datasets remain outside Git.
"""
import argparse
import datetime
import hashlib
import json
import subprocess
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ['0.1.0', '0.2.0', 'stress-tested', '0.3.0', '0.3.1', '0.3.2', '0.3.3', '0.3.4', '0.3.5', '0.3.6', '0.3.7']
TITLES = {
    '0.1.0':'Initial RAM SQL prototype', '0.2.0':'Disk archive, 100M-row aggregates and real-data pipeline',
    'stress-tested':'Six-engine stress tests and exposed failures', '0.3.0':'Concurrent snapshots and replayable live ingestion',
    '0.3.1':'Receipt retry, compaction and publication profiling', '0.3.2':'Reusable streamed scan kernels',
    '0.3.3':'Bounded receipt catalog deltas and checkpoints', '0.3.4':'Measured optional coalescing policies',
    '0.3.5':'Opt-in confirmed retry index with retained unsuccessful trial', '0.3.6':'Immutable prepared batches and retry cost controls',
    '0.3.7':'Atomic archive-local source positions'}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--owner', required=True)
    parser.add_argument('--owner-id', required=True, type=int)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists() and args.owner.isascii() and args.owner.replace('-', '').isalnum()
    existing = subprocess.check_output(['git', 'for-each-ref', '--format=%(refname)'], cwd=ROOT, text=True)
    assert not existing.strip(), 'Only import into a new empty Git repository'
    identity = f'{args.owner} <{args.owner_id}+{args.owner}@users.noreply.github.com>'
    task = ROOT.parent.parent / 'work/github-publication'
    task.mkdir(parents=True, exist_ok=True)
    stream_path = task / f'history-{time.time_ns()}.fast-import'
    records = []
    with stream_path.open('wb') as stream:
        for mark, version in enumerate(VERSIONS, 1):
            archive = ROOT.parent / f'kestrel-sql-{version}.zip'
            digest = sha(archive)
            sidecar = archive.with_suffix('.zip.sha256')
            if sidecar.exists(): assert sidecar.read_text().split()[0] == digest
            timestamp = int(archive.stat().st_mtime)
            message = f'{version}: {TITLES[version]}\n\nImported byte-for-byte from {archive.name}.\nArchive SHA-256: {digest}\nExperimental local evidence; failures are preserved.\n'.encode()
            stream.write(f'commit refs/heads/main\nmark :{mark}\nauthor {identity} {timestamp} +0000\ncommitter {identity} {timestamp} +0000\ndata {len(message)}\n'.encode())
            stream.write(message + b'\n')
            if mark > 1: stream.write(f'from :{mark-1}\n'.encode())
            stream.write(b'deleteall\n')
            with zipfile.ZipFile(archive) as bundle:
                assert bundle.testzip() is None
                files = [name for name in bundle.namelist() if not name.endswith('/')]
                assert all(name.startswith(ROOT.name+'/') for name in files)
                manifest = ROOT.name + '/MANIFEST.sha256'
                if manifest in files:
                    for line in bundle.read(manifest).decode().splitlines():
                        file_digest, name = line.split('  ', 1)
                        assert hashlib.sha256(bundle.read(ROOT.name+'/'+name)).hexdigest() == file_digest
                for name in sorted(files):
                    relative = name[len(ROOT.name)+1:]
                    assert not {'..','.git','__pycache__','target'}.intersection(Path(relative).parts)
                    data = bundle.read(name)
                    stream.write(f'M 100644 inline {json.dumps(relative)}\ndata {len(data)}\n'.encode())
                    stream.write(data + b'\n')
                proof = json.loads(bundle.read(ROOT.name+'/verification.json')) if ROOT.name+'/verification.json' in files else {}
                tag = 'stress-tested-0.2.0' if version == 'stress-tested' else 'v'+version
                stream.write(f'\ntag {tag}\nfrom :{mark}\ntagger {identity} {timestamp} +0000\ndata {len(message)}\n'.encode())
                stream.write(message + b'\n')
                records.append({'tag':tag,'version':version,'title':TITLES[version],'archive':archive.name,'sha256':digest,
                    'bytes':archive.stat().st_size,'snapshot_files':len(files),'original_packaged_at_utc':datetime.datetime.fromtimestamp(timestamp,datetime.timezone.utc).isoformat(),
                    'rust_tests':proof.get('rust_tests'),'local_path':str(archive),
                    'release_url':f'https://github.com/{args.owner}/kestrel-sql/releases/tag/{tag}',
                    'download_url':f'https://github.com/{args.owner}/kestrel-sql/releases/download/{tag}/{archive.name}'})
            print(f'Prepared {tag}: {len(files)} exact files', flush=True)
    with stream_path.open('rb') as stream:
        subprocess.run(['git','fast-import','--quiet'],cwd=ROOT,stdin=stream,check=True)
    subprocess.run(['git','reset','--mixed','HEAD'],cwd=ROOT,check=True,capture_output=True,text=True)
    for record in records:
        record['commit'] = subprocess.check_output(['git','rev-parse',record['tag']+'^{commit}'],cwd=ROOT,text=True).strip()
    args.output.write_text(json.dumps({'repository':f'https://github.com/{args.owner}/kestrel-sql','snapshots':records,
        'history_import_sha256':sha(Path(__file__)),'all_release_envelopes_and_manifest_hashes_checked':True},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'snapshots':len(records),'working_files_preserved':True}))


if __name__ == '__main__': main()
