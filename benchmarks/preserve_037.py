"""Preserve exact 0.3.7 release core/binaries before a query-engine change."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / 'benchmarks/baseline-0.3.7-provenance.json'
    assert not output.exists()
    archive = ROOT.parent / 'kestrel-sql-0.3.7.zip'
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert archive_sha == 'ea3273d56d6dec58912179f322d70d1e2878f2df58030fba399d6a616a15cd4a'
    build = json.loads((ROOT / 'benchmarks/rust-checks-037.json').read_text())
    source_root = ROOT / 'benchmarks/baseline-0.3.7-source'
    binary_root = ROOT / 'bin/baseline-0.3.7'; binary_root.mkdir()
    binary_hashes = {}
    with zipfile.ZipFile(archive) as bundle:
        for relative, digest in build['source_sha256'].items():
            data = bundle.read(ROOT.name + '/' + relative)
            assert hashlib.sha256(data).hexdigest() == digest
            assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
            destination = source_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(data)
        fields = {'kestrel.exe':'cli_sha256', 'kestrel-stress.exe':'bridge_sha256', 'receipt-seed.exe':'receipt_seed_sha256',
            'scan-profile.exe':'scan_probe_sha256', 'performance-probe.exe':'probe_sha256'}
        for name, field in fields.items():
            data = bundle.read(ROOT.name + '/bin/' + name)
            assert data[:2] == b'MZ' and hashlib.sha256(data).hexdigest() == build[field]
            (binary_root / name).write_bytes(data)
            binary_hashes[name] = build[field]
    shutil.copy2(ROOT / 'verification.json', ROOT / 'verification-v037.json')
    assert json.loads((ROOT / 'verification-v037.json').read_text())['version'] == '0.3.7'
    proof = {'version':'0.3.7', 'archive_sha256':archive_sha, 'core_source_sha256':build['source_sha256'],
        'baseline_binary_sha256':binary_hashes,
        'origin':'Exact bytes from immutable 0.3.7 ZIP; current core checked before edits; later I/O diagnostics are separate evidence'}
    output.write_text(json.dumps(proof, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'baseline':'0.3.7', 'files':len(build['source_sha256']), 'binaries':len(binary_hashes)}))


if __name__ == '__main__': main()
