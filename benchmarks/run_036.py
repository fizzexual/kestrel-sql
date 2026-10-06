"""Serialize targeted controls and prepared-publication correctness after CPU work."""
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['timed', 'correctness'])
    args = parser.parse_args()
    candidate = WORK / 'perf-036/candidate'
    bridge = str(candidate / 'kestrel-stress.exe')
    shared = ['--baseline', 'bin/baseline-0.3.5/kestrel-stress.exe', '--candidate', bridge,
        '--baseline-seed', 'bin/baseline-0.3.5/receipt-seed.exe', '--candidate-seed', str(candidate / 'receipt-seed.exe'),
        '--baseline-version', '0.3.5', '--candidate-version', '0.3.6', '--rounds', '3']
    if args.phase == 'timed':
        direct = json.loads((ROOT / 'benchmarks/prepared-036-direct.json').read_text())
        assert len(direct['cases']) == 30 and not direct['failed_cases']
        jobs = [('retry-control', ['group_commit_compare.py', *shared, '--variants', 'baseline-indexed0,indexed0',
                '--profiles', 'retry-mixed', '--seconds', '15', '--output', 'benchmarks/prepared-036-retry-control.json']),
            ('write-controls', ['group_commit_compare.py', *shared, '--variants', 'baseline,delay0',
                '--profiles', 'anonymous-mixed,receipt-write', '--seconds', '15', '--output', 'benchmarks/prepared-036-write-controls.json'])]
    else:
        timed = json.loads((ROOT / 'benchmarks/timed-036-run-order.json').read_text())
        assert len(timed) == 2 and all(r['returncode'] == 0 for r in timed)
        jobs = [('prepared-faults', ['live_retry_faults.py', '--binary', bridge,
                '--driver', str(WORK / 'kestrel-036-fault-build/release/examples/live_retry_probe.exe'),
                '--expected-version', '0.3.6', '--process-exits', '--output', 'benchmarks/prepared-036-faults.json']),
            ('concurrent-kills', ['group_commit_recovery.py', '--binary', bridge, '--expected-version', '0.3.6',
                '--retry-index', '--output', 'benchmarks/group-036-recovery.json']),
            ('sql-differential', ['archive_verify.py', '--binary', str(candidate / 'kestrel.exe'),
                '--queries', '500', '--output', 'benchmarks/archive-036-verification.json'])]
    log = ROOT / f'benchmarks/{args.phase}-036-run-order.json'
    assert not log.exists(), 'Preserve attempts; choose a new log for repairs'
    records = []
    for name, arguments in jobs:
        output = Path(arguments[arguments.index('--output')+1])
        assert not (ROOT / output).exists(), 'Preserve existing report'
        record = {'suite': name, 'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'started_monotonic_ns': time.perf_counter_ns(), 'command': [sys.executable, 'benchmarks/' + arguments[0], *arguments[1:]],
            'harness_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [ROOT / 'benchmarks' / arguments[0], ROOT / 'benchmarks/stress_compare.py', ROOT / 'benchmarks/host_telemetry.py']}}
        print(name, flush=True)
        result = subprocess.run(record['command'], cwd=ROOT)
        record.update(returncode=result.returncode, completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            completed_monotonic_ns=time.perf_counter_ns())
        records.append(record)
        log.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
        assert result.returncode == 0, record


if __name__ == '__main__': main()
