"""Link the unchanged recovery adapter to qualified 0.3.8 before timed queries."""
import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
deps = WORK / 'kestrel-038-build/release/deps'
destination = WORK / 'perf-038/candidate/source-pipeline-typed.exe'
assert not destination.exists()
libraries = {}
for name in ['kestrel_sql', 'serde_json']:
    found = list(deps.glob('lib' + name + '-*.rlib'))
    assert len(found) == 1, found
    libraries[name] = found[0]
command = ['rustc', '--edition=2024', '-O', '-C', 'lto=thin', '-C', 'codegen-units=1', '-D', 'warnings', str(ROOT / 'benchmarks/source_pipeline_probe.rs'),
    '-L', 'dependency=' + str(deps), '-o', str(destination)]
for name, library in libraries.items(): command += ['--extern', name + '=' + str(library)]
environment = {**os.environ, 'CARGO_PKG_VERSION': '0.3.8', 'TMP': str(WORK / 'rust-temp-032'), 'TEMP': str(WORK / 'rust-temp-032')}
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
result = subprocess.run(command, env=environment, cwd=ROOT, text=True, capture_output=True)
(ROOT / 'benchmarks/build-038-typed-logs/source-adapter.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
assert result.returncode == 0, result.stderr
assert b'KESTREL_FAULT_POINT' not in destination.read_bytes()
proof = {'version': '0.3.8', 'binary_path': str(destination), 'binary_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
    'source_sha256': hashlib.sha256((ROOT / 'benchmarks/source_pipeline_probe.rs').read_bytes()).hexdigest(),
    'command': command, 'started_at_utc': started, 'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
(ROOT / 'benchmarks/source-038-typed-adapter-build.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof), flush=True)
