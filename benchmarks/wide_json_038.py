"""Check that exact wide aggregate values survive the public CLI JSON boundary."""
import argparse
import hashlib
import json
import struct
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
assert not args.output.exists()
work = WORK / f'wide-json-038-{time.time_ns()}'; work.mkdir()
report = {'cases': [], 'complete': False}
for variant, binary in [('baseline', ROOT / 'bin/baseline-0.3.7/kestrel.exe'), ('candidate', WORK / 'perf-038/candidate/kestrel.exe')]:
    for value in [2**63-1, -(2**63)]:
        directory = work / f'{variant}-{value}'; directory.mkdir()
        raw = directory / 'rows.i64'
        raw.write_bytes(b''.join(struct.pack('<qqq', i, value, 7) for i in range(3)))
        imported = json.loads(subprocess.check_output([str(binary), '--archive', str(directory / 'archive'), '--import-i64', str(raw)], text=True))
        assert imported['ok'] and imported['verified_bytes'] == 72
        sql = 'SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device'
        result = subprocess.run([str(binary), '--archive', str(directory / 'archive'), '--sql', sql], text=True, capture_output=True)
        parsed = json.loads(result.stdout) if result.stdout.strip() else None
        passed = result.returncode == 0 and parsed['ok'] and parsed['result']['rows'] == [[7, 3, value*3]]
        report['cases'].append({'variant': variant, 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
            'input_value': value, 'expected_sum': str(value*3), 'returncode': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr, 'exact_wide_json_passed': passed})
report['complete'] = True
args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'cases': len(report['cases']), 'passed': sum(c['exact_wide_json_passed'] for c in report['cases'])}), flush=True)
