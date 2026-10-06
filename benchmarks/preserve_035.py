"""Verify the immutable 0.3.5 package, then preserve its exact baseline."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / 'benchmarks/baseline-0.3.5-provenance.json'
    assert not output.exists(), 'Preserve existing baseline proof'
    archive = ROOT.parent / 'kestrel-sql-0.3.5.zip'
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert archive_sha == 'c76c94236171ff8c961b942ffd020fbc10ba19975ab3c391a94ad4499dd9b81a'
    build = json.loads((ROOT / 'benchmarks/rust-checks-035-final.json').read_text())
    source_root = ROOT / 'benchmarks/baseline-0.3.5-source'
    binary_root = ROOT / 'bin/baseline-0.3.5'
    binary_root.mkdir()
    binary_hashes = {}
    with zipfile.ZipFile(archive) as bundle:
        for relative, digest in build['source_sha256'].items():
            data = bundle.read(ROOT.name + '/' + relative)
            assert hashlib.sha256(data).hexdigest() == digest
            assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
            destination = source_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        for name in ['kestrel.exe', 'kestrel-stress.exe', 'receipt-seed.exe']:
            data = bundle.read(ROOT.name + '/bin/' + name)
            assert data[:2] == b'MZ'
            (binary_root / name).write_bytes(data)
            binary_hashes[name] = hashlib.sha256(data).hexdigest()
        data = bundle.read(ROOT.name + '/bin/test-only/live-retry-inprocess-035.exe')
        (binary_root / 'live-retry-inprocess.exe').write_bytes(data)
        binary_hashes['live-retry-inprocess.exe'] = hashlib.sha256(data).hexdigest()
        assert binary_hashes['live-retry-inprocess.exe'] == json.loads(bundle.read(ROOT.name + '/benchmarks/retry-035-direct.json'))['builds']['candidate']['binary_sha256']
        assert binary_hashes['kestrel.exe'] == build['cli_sha256']
        assert binary_hashes['kestrel-stress.exe'] == build['bridge_sha256']
        assert binary_hashes['receipt-seed.exe'] == build['receipt_seed_sha256']
    shutil.copy2(ROOT / 'verification.json', ROOT / 'verification-v035.json')
    proof = {'version': '0.3.5', 'archive_sha256': archive_sha,
             'core_source_sha256': build['source_sha256'], 'baseline_binary_sha256': binary_hashes,
             'origin': 'Exact bytes from the verified immutable 0.3.5 release ZIP; current core matches before edits'}
    output.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'baseline': '0.3.5', 'files': len(build['source_sha256']), 'binaries': len(binary_hashes)}))


if __name__ == '__main__':
    main()
