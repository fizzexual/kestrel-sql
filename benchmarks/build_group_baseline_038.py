"""Compile the same probe against the preserved 0.3.7 source, before workloads."""
import datetime
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
source = WORK / 'group-038-baseline-source'
target = WORK / 'kestrel-038-baseline-build'
parser = argparse.ArgumentParser()
parser.add_argument('--verify-existing', action='store_true')
args = parser.parse_args()
environment = {**os.environ, 'CARGO_TARGET_DIR': str(target), 'TMP': str(WORK / 'rust-temp-032'), 'TEMP': str(WORK / 'rust-temp-032')}
command = ['cargo', 'build', '--release', '--example', 'group_probe', '--offline', '--locked']
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
binary = target / 'release/examples/group_probe.exe'
destination = WORK / 'perf-038/baseline/group-probe.exe'
if not args.verify_existing:
    assert not source.exists()
    shutil.copytree(ROOT / 'benchmarks/baseline-0.3.7-source', source)
    shutil.copy2(ROOT / 'examples/group_probe.rs', source / 'examples/group_probe.rs')
    result = subprocess.run(command, cwd=source, env=environment, text=True, capture_output=True)
    (ROOT / 'benchmarks/build-038-logs/group-baseline.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
    assert result.returncode == 0, result.stderr
    destination.parent.mkdir(parents=True)
    shutil.copy2(binary, destination)
else:
    assert source.exists() and binary.read_bytes() == destination.read_bytes()
proof = {'version': '0.3.7', 'original_build_command': command,
    'validation_started_at_utc': started,
    'validation_completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'build_log': 'benchmarks/build-038-logs/group-baseline.txt',
    'existing_binary_modified_at_utc': datetime.datetime.fromtimestamp(binary.stat().st_mtime, datetime.timezone.utc).isoformat(),
    'probe_source_sha256': hashlib.sha256((source / 'examples/group_probe.rs').read_bytes()).hexdigest(),
    'binary_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
    'baseline_core_hashes_match_preservation': True, 'post_build_validation_repair': args.verify_existing}
baseline = json.loads((ROOT / 'benchmarks/baseline-0.3.7-provenance.json').read_text())
original = json.loads((ROOT / 'verification-v037.json').read_text())
for relative, digest in original['source_sha256'].items():
    assert hashlib.sha256((source / relative).read_bytes()).hexdigest() == digest
assert proof['probe_source_sha256'] == hashlib.sha256((ROOT / 'examples/group_probe.rs').read_bytes()).hexdigest()
(ROOT / 'benchmarks/group-038-baseline-build.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof), flush=True)
