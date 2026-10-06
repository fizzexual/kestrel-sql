"""Compile before timing; preserve all CPU probe evidence and build provenance."""
import datetime
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'


def main():
    output = ROOT / 'benchmarks/digest-036-profile.json'
    assert not output.exists()
    base = json.loads((ROOT / 'benchmarks/baseline-0.3.5-provenance.json').read_text())
    owned = WORK / f'digest-profile-{time.time_ns()}'
    owned.mkdir()
    checkout = owned / 'source'
    for relative, digest in base['core_source_sha256'].items():
        source = ROOT / 'benchmarks/baseline-0.3.5-source' / relative
        assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
        destination = checkout / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    probe = ROOT / 'benchmarks/digest_profile.rs'
    shutil.copy2(probe, checkout / 'examples/digest_profile.rs')
    environment = {**os.environ, 'CARGO_TARGET_DIR': str(owned / 'target'),
        'TMP': str(WORK / 'rust-temp-032'), 'TEMP': str(WORK / 'rust-temp-032')}
    command = ['cargo', 'build', '--release', '--example', 'digest_profile', '--offline', '--locked']
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = subprocess.run(command, cwd=checkout, env=environment, capture_output=True, text=True)
    (ROOT / 'benchmarks/digest-036-build.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
    assert result.returncode == 0, result.stderr
    binary = owned / 'target/release/examples/digest_profile.exe'
    built = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print('Build complete; starting isolated SHA-256 CPU probe', flush=True)
    raw = json.loads(subprocess.check_output([str(binary)], text=True, timeout=90))
    ended = datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert raw['all_domains_equal'] and len(raw['cases']) == 75
    for case in raw['cases']:
        assert case['calls'] > 0 and case['elapsed_ns'] >= 300_000_000
        assert case['ns_per_digest'] == case['elapsed_ns'] / case['calls']
    medians = []
    for width, rows in [(3, 1), (3, 100), (3, 10000), (64, 100), (1, 131073)]:
        times = {variant: statistics.median(c['ns_per_digest'] for c in raw['cases']
            if (c['width'], c['rows'], c['variant']) == (width, rows, variant))
            for variant in ['original', 'chunk512', 'chunk4096']}
        medians.append({'width': width, 'rows': rows, 'median_ns': times,
            'chunk512_speedup': times['original'] / times['chunk512'],
            'chunk4096_speedup': times['original'] / times['chunk4096']})
    proof = {**raw, 'medians': medians, 'methodology': 'CPU-only single-thread digest; five rotated rounds; 300ms per variant/shape; 16 calls per timer poll; original per-i64 updates versus 512/4096-byte portable LE staging; allocations outside timer; final digest black_box; not database capacity',
        'probe_sha256': hashlib.sha256(probe.read_bytes()).hexdigest(),
        'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'binary_path': str(binary),
        'baseline_core': base['core_source_sha256'], 'build_started_at_utc': started,
        'build_completed_at_utc': built, 'timing_started_at_utc': built, 'timing_completed_at_utc': ended}
    output.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(medians), flush=True)


if __name__ == '__main__':
    main()
