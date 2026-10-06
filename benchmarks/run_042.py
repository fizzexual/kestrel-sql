"""Correctness, retry and recovery qualification after all final comparisons stop."""
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
output = ROOT / 'benchmarks/correctness-042-run-order.json'
parser = argparse.ArgumentParser()
parser.add_argument('--resume', action='store_true')
args = parser.parse_args()
assert not output.exists() or args.resume
timed_order = json.loads((ROOT / 'benchmarks/cache-042-run-order.json').read_text(encoding='utf-8'))
assert len({r['scope'] for r in timed_order if r['returncode']==0}) == 12
followup_order=json.loads((ROOT/'benchmarks/cache-042-follow-up-run-order.json').read_text(encoding='utf-8'))
assert len(followup_order)==2 and all(r['returncode']==0 for r in followup_order)
cli = WORK / 'perf-042/candidate/kestrel.exe'
bridge = WORK / 'perf-042/candidate/kestrel-stress.exe'
adapter = WORK / 'perf-042/candidate/source-pipeline-typed.exe'
faults = WORK / 'kestrel-042-fault-build/release/examples'
jobs = [
    ('sql-differential', ['benchmarks/archive_verify.py', '--binary', str(cli), '--output', 'benchmarks/archive-042-verification.json', '--queries', '500']),
    ('expanded-and-sparse-sql', ['benchmarks/group_verify_042.py']),
    ('cache-key-patterns', ['benchmarks/cache_verify_042.py']),
    ('medium-cache-sql', ['benchmarks/medium_verify_042.py']),
    ('selectivity-and-filter-order', ['benchmarks/scan_verify_042.py']),
    ('publication-cuts-corruptions', ['benchmarks/publication_faults.py', '--binary', str(bridge), '--sql-binary', str(cli), '--fault-driver', str(faults / 'publication_fault_probe.exe'), '--expected-version', '0.3.12', '--output', 'benchmarks/publication-042-faults.json']),
    ('concurrent-forced-kills', ['benchmarks/group_commit_recovery.py', '--binary', str(bridge), '--expected-version', '0.3.12', '--retry-index', '--output', 'benchmarks/group-042-recovery.json']),
    ('source-cuts-and-kills', ['benchmarks/source_faults.py', '--adapter', str(adapter), '--driver', str(faults / 'source_fault_probe.exe'), '--output', 'benchmarks/source-042-faults.json']),
    ('parquet-source-pipeline', ['benchmarks/source_pipeline_demo.py', '--binary', str(adapter), '--expected-version', '0.3.12', '--output', 'portfolio/source-pipeline-042-results.json']),
    ('wide-json-and-sparse-reopen', ['benchmarks/wire_042.py']),
]
records = json.loads(output.read_text(encoding='utf-8')) if output.exists() else []
for name, arguments in jobs:
    if any(r['suite'] == name and r['returncode'] == 0 for r in records):
        continue
    record = {'suite': name, 'command': [sys.executable, *arguments],
        'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'harness_sha256': hashlib.sha256((ROOT / arguments[0]).read_bytes()).hexdigest()}
    assert followup_order[-1]['completed_at_utc'] <= record['started_at_utc']
    print(name, flush=True)
    result = subprocess.run(record['command'], cwd=ROOT)
    record.update(returncode=result.returncode, completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    records.append(record)
    output.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    assert result.returncode == 0, record
