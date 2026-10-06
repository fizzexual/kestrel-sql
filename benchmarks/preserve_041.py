"""Preserve verified release 0.3.10 before experimenting with group cache indexing."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
package = ROOT.parent / 'kestrel-sql-0.3.10.zip'
with package.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
assert digest == '0621cdd25739c25d485e5ef58ab98e9a39512a795cb48dbbad28067aa5dccdd4'
current = json.loads((ROOT / 'verification.json').read_text(encoding='utf-8'))
assert current['version'] == '0.3.10'
source = ROOT / 'benchmarks/baseline-0.3.10-source'
binary = ROOT / 'bin/baseline-0.3.10'
assert not source.exists() and not binary.exists()
source.mkdir()
binary.mkdir()
with zipfile.ZipFile(package) as archive:
    for relative, expected in current['source_sha256'].items():
        data = archive.read(ROOT.name + '/' + relative)
        assert hashlib.sha256(data).hexdigest() == expected
        assert (ROOT / relative).read_bytes() == data, relative
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    binaries = {}
    for item in archive.namelist():
        relative = item.removeprefix(ROOT.name + '/')
        if relative.startswith('bin/') and relative.count('/') == 1 and relative.endswith('.exe'):
            data = archive.read(item)
            path = binary / Path(relative).name
            assert (ROOT / relative).read_bytes() == data
            path.write_bytes(data)
            binaries[path.name] = hashlib.sha256(data).hexdigest()
proof = {'version': '0.3.10', 'archive': str(package), 'archive_sha256': digest,
    'core_source_sha256': current['source_sha256'], 'baseline_binary_sha256': binaries,
    'same_group_probe_source': current['source_sha256']['examples/group_probe.rs']}
(ROOT / 'benchmarks/baseline-0.3.10-provenance.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
assert not (ROOT / 'verification-v040.json').exists()
shutil.copy2(ROOT / 'verification.json', ROOT / 'verification-v040.json')
print(json.dumps({'baseline': '0.3.10', 'source_files': len(current['source_sha256']), 'binaries': len(binaries)}))
