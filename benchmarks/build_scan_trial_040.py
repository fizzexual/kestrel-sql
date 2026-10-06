"""Serial test/build for preserved scan experiments, before any timed workload."""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    assert re.fullmatch('[a-z][a-z0-9-]{0,40}', args.name)
    trial = ROOT / f'benchmarks/trial-040-{args.name}'
    binary_dir = ROOT / f'bin/trials/scan-040-{args.name}'
    assert not trial.exists() and not binary_dir.exists()
    trial.mkdir()
    binary_dir.mkdir()
    paths = [ROOT / 'Cargo.toml', ROOT / 'Cargo.lock', *ROOT.glob('src/**/*.rs'), *ROOT.glob('tests/*.rs'), *ROOT.glob('examples/*.rs')]
    sources = {}
    for path in paths:
        relative = path.relative_to(ROOT)
        destination = trial / 'source' / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        sources[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    target = WORK / 'kestrel-039-build'
    environment = {**os.environ, 'TMP': str(WORK / 'rust-temp-032'), 'TEMP': str(WORK / 'rust-temp-032'),
        'KESTREL_TEST_ROOT': str(WORK / 'cargo-tests'), 'CARGO_TARGET_DIR': str(target)}
    commands = [('fmt', ['cargo', 'fmt', '--check']),
        ('debug', ['cargo', 'test', '--offline', '--locked']),
        ('build', ['cargo', 'build', '--release', '--example', 'group_probe', '--offline', '--locked'])]
    records = []
    tests = None
    for name, command in commands:
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(name, flush=True)
        result = subprocess.run(command, cwd=ROOT, env=environment, text=True, capture_output=True)
        (trial / (name + '.txt')).write_text(result.stdout + result.stderr, encoding='utf-8')
        records.append({'job': name, 'command': command, 'started_at_utc': started,
            'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'returncode': result.returncode})
        (trial / 'run-order.json').write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
        assert result.returncode == 0, (name, result.stdout, result.stderr)
        if name == 'debug':
            tests = sum(map(int, re.findall(r'test result: ok\. (\d+) passed;', result.stdout)))
            assert tests == 69, tests
    binary = binary_dir / 'group-probe.exe'
    shutil.copy2(target / 'release/examples/group_probe.exe', binary)
    for relative, digest in sources.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
    proof = {'trial': args.name, 'version': '0.3.9 development trial', 'source_sha256': sources,
        'debug_tests_passed': tests, 'group_probe_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
        'group_probe': str(binary), 'build_run_order': records,
        'qualification': 'trial only; full release/Clippy/fault/differential qualification not yet executed'}
    (trial / 'proof.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'trial': args.name, 'debug_tests': tests, 'binary': str(binary)}), flush=True)


if __name__ == '__main__':
    main()
