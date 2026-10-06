"""Preserve verified release 0.3.15 before experimenting with a packed medium key-cache layout."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
package = ROOT.parent / 'kestrel-sql-0.3.15.zip'
with package.open('rb') as stream:
    digest = hashlib.file_digest(stream, 'sha256').hexdigest()
assert digest == 'afe7f3adc046efb1124be7c23e4058f631c158acec8f5f059a834d1265758b16'
current = json.loads((ROOT / 'verification.json').read_text(encoding='utf-8'))
assert current['version'] == '0.3.15'
source = ROOT / 'benchmarks/baseline-0.3.15-source'
binary = ROOT / 'bin/baseline-0.3.15'
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
proof = {'version': '0.3.15', 'archive': str(package), 'archive_sha256': digest,
    'core_source_sha256': current['source_sha256'], 'baseline_binary_sha256': binaries,
    'same_group_probe_source': current['source_sha256']['examples/group_probe.rs']}
(ROOT / 'benchmarks/baseline-0.3.15-provenance.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
assert not (ROOT / 'verification-v045.json').exists()
shutil.copy2(ROOT / 'verification.json', ROOT / 'verification-v045.json')
print(json.dumps({'baseline': '0.3.15', 'source_files': len(current['source_sha256']), 'binaries': len(binaries)}))
