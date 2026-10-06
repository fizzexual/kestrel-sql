"""Preserve the immutable 0.3.8 release before the next query experiment."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    package = ROOT.parent / 'kestrel-sql-0.3.8.zip'
    digest = hashlib.sha256(package.read_bytes()).hexdigest()
    assert digest == '0240544963ac362d454b8abb623ef071515c571c058fb6369d30724a2dcd6d68'
    current = json.loads((ROOT / 'verification.json').read_text())
    assert current['version'] == '0.3.8'
    source = ROOT / 'benchmarks/baseline-0.3.8-source'
    binary = ROOT / 'bin/baseline-0.3.8'
    assert not source.exists() and not binary.exists()
    source.mkdir(); binary.mkdir()
    with zipfile.ZipFile(package) as archive:
        for relative, expected in current['source_sha256'].items():
            data = archive.read(ROOT.name + '/' + relative)
            assert hashlib.sha256(data).hexdigest() == expected
            assert (ROOT / relative).read_bytes() == data, relative
            path = source / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        binaries = {}
        for item in archive.namelist():
            relative = item.removeprefix(ROOT.name + '/')
            if relative.startswith('bin/') and relative.count('/') == 1 and relative.endswith('.exe'):
                data = archive.read(item)
                path = binary / Path(relative).name; path.write_bytes(data)
                binaries[path.name] = hashlib.sha256(data).hexdigest()
    proof = {'version': '0.3.8', 'archive': str(package), 'archive_sha256': digest,
             'core_source_sha256': current['source_sha256'], 'baseline_binary_sha256': binaries,
             'same_group_probe_source': current['source_sha256']['examples/group_probe.rs']}
    (ROOT / 'benchmarks/baseline-0.3.8-provenance.json').write_text(json.dumps(proof, indent=2)+'\n')
    assert not (ROOT / 'verification-v038.json').exists()
    shutil.copy2(ROOT / 'verification.json', ROOT / 'verification-v038.json')
    print(json.dumps({'baseline': '0.3.8', 'source_files': len(current['source_sha256']), 'binaries': len(binaries)}))

if __name__ == '__main__': main()
