"""Serial current-binary differential, crash/retry and pipeline checks after timing."""
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
output = ROOT / 'benchmarks/correctness-038-run-order.json'
assert not output.exists()
for name in ['typed', 'nyc', 'large']:
    report = json.loads((ROOT / f'benchmarks/group-038-{name}-comparison.json').read_text())
    assert report['complete']
cli = WORK / 'perf-038/candidate/kestrel.exe'
bridge = WORK / 'perf-038/candidate/kestrel-stress.exe'
adapter = WORK / 'perf-038/candidate/source-pipeline-typed.exe'
faults = WORK / 'kestrel-038-fault-build/release/examples'
jobs = [
    ('group-profile', ['benchmarks/profile_group_038.py']),
    ('sql-differential', ['benchmarks/archive_verify.py', '--binary', str(cli), '--output', 'benchmarks/archive-038-verification.json', '--queries', '500']),
    ('publication-cuts-corruptions', ['benchmarks/publication_faults.py', '--binary', str(bridge), '--sql-binary', str(cli), '--fault-driver', str(faults / 'publication_fault_probe.exe'), '--expected-version', '0.3.8', '--output', 'benchmarks/publication-038-faults.json']),
    ('concurrent-forced-kills', ['benchmarks/group_commit_recovery.py', '--binary', str(bridge), '--expected-version', '0.3.8', '--retry-index', '--output', 'benchmarks/group-038-recovery.json']),
    ('source-cuts-and-kills', ['benchmarks/source_faults.py', '--adapter', str(adapter), '--driver', str(faults / 'source_fault_probe.exe'), '--output', 'benchmarks/source-038-faults.json']),
    ('parquet-source-pipeline', ['benchmarks/source_pipeline_demo.py', '--binary', str(adapter), '--expected-version', '0.3.8', '--output', 'portfolio/source-pipeline-038-results.json']),
]
records = []
for name, arguments in jobs:
    record = {'suite': name, 'command': [sys.executable, *arguments], 'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'harness_sha256': hashlib.sha256((ROOT / arguments[0]).read_bytes()).hexdigest()}
    print(name, flush=True)
    result = subprocess.run(record['command'], cwd=ROOT)
    record.update(returncode=result.returncode, completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    records.append(record); output.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    assert result.returncode == 0, record
