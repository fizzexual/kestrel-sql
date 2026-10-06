"""Keep the uncached typed hash trial as reproducible experiment evidence."""
import hashlib
import json
import shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
source = ROOT / 'benchmarks/trial-039-typed-source'
frozen = WORK / 'perf-039/typed-trial/group-probe.exe'
assert not source.exists() and not frozen.exists()
source.mkdir(); frozen.parent.mkdir(parents=True)
paths = [ROOT/'Cargo.toml', ROOT/'Cargo.lock', *ROOT.glob('src/**/*.rs'), *ROOT.glob('tests/*.rs'), *ROOT.glob('examples/*.rs')]
proof = {'candidate_version': '0.3.9', 'description': 'expanded dense range and typed sparse arrays; no key cache', 'source_sha256': {}}
for path in paths:
    relative = path.relative_to(ROOT)
    destination = source / relative; destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)
    proof['source_sha256'][relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
shutil.copy2(WORK / 'kestrel-039-build/release/examples/group_probe.exe', frozen)
proof['binary_sha256'] = hashlib.sha256(frozen.read_bytes()).hexdigest()
proof['debug_tests_passed'] = sum(int(line.split('test result: ok. ')[1].split(' passed')[0]) for line in
    (ROOT/'benchmarks/build-039-typed-test.txt').read_text().splitlines() if 'test result: ok.' in line)
assert proof['debug_tests_passed'] == 67
(ROOT/'benchmarks/group-039-typed-trial-provenance.json').write_text(json.dumps(proof, indent=2)+'\n')
print(json.dumps({'frozen_probe': str(frozen), 'debug_tests': proof['debug_tests_passed']}))
