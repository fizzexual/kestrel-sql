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
output = ROOT / 'benchmarks/correctness-044-run-order.json'
parser = argparse.ArgumentParser()
parser.add_argument('--resume', action='store_true')
args = parser.parse_args()
assert not output.exists() or args.resume
logs=ROOT/'benchmarks/correctness-044-run-logs'
assert args.resume or not logs.exists()
logs.mkdir(exist_ok=args.resume)
timed_order = json.loads((ROOT / 'benchmarks/sparse-044-run-order.json').read_text(encoding='utf-8'))
assert len({r['scope'] for r in timed_order if r['returncode']==0}) == 17

cli = WORK / 'perf-044/candidate/kestrel.exe'
bridge = WORK / 'perf-044/candidate/kestrel-stress.exe'
adapter = WORK / 'perf-044/candidate/source-pipeline-typed.exe'
faults = WORK / 'kestrel-044-fault-build/release/examples'
jobs = [
    ('sql-differential', ['benchmarks/archive_verify.py', '--binary', str(cli), '--output', 'benchmarks/archive-044-verification.json', '--queries', '500']),
    ('expanded-and-sparse-sql', ['benchmarks/group_verify_044.py']),
    ('cache-key-patterns', ['benchmarks/cache_verify_044.py']),
    ('medium-cache-sql', ['benchmarks/medium_verify_044.py']),
    ('fused-dense-sql',['benchmarks/dense_verify_044.py']),
    ('focused-sparse-shared-sum',['benchmarks/sparse_verify_044.py']),
    ('selectivity-and-filter-order', ['benchmarks/scan_verify_044.py']),
    ('publication-cuts-corruptions', ['benchmarks/publication_faults.py', '--binary', str(bridge), '--sql-binary', str(cli), '--fault-driver', str(faults / 'publication_fault_probe.exe'), '--expected-version', '0.3.14', '--output', 'benchmarks/publication-044-faults.json']),
    ('concurrent-forced-kills', ['benchmarks/group_commit_recovery.py', '--binary', str(bridge), '--expected-version', '0.3.14', '--retry-index', '--output', 'benchmarks/group-044-recovery.json']),
    ('source-cuts-and-kills', ['benchmarks/source_faults.py', '--adapter', str(adapter), '--driver', str(faults / 'source_fault_probe.exe'), '--output', 'benchmarks/source-044-faults.json']),
    ('parquet-source-pipeline', ['benchmarks/source_pipeline_demo.py', '--binary', str(adapter), '--expected-version', '0.3.14', '--output', 'portfolio/source-pipeline-044-results.json']),
    ('wide-json-and-sparse-reopen', ['benchmarks/wire_044.py']),
]
records = json.loads(output.read_text(encoding='utf-8')) if output.exists() else []
for name, arguments in jobs:
    if any(r['suite'] == name and r['returncode'] == 0 for r in records):
        continue
    record = {'suite': name, 'command': [sys.executable, *arguments],
        'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'harness_sha256': hashlib.sha256((ROOT / arguments[0]).read_bytes()).hexdigest()}
    assert timed_order[-1]['completed_at_utc'] <= record['started_at_utc']
    print(name, flush=True)
    attempts=sum(r['suite']==name for r in records)
    log=logs/(name+(f'-retry-{attempts}' if attempts else '')+'.txt')
    assert not log.exists()
    record['log']=str(log)
    with log.open('w',encoding='utf-8') as stream:
        result = subprocess.run(record['command'], cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode:print(log.read_text(encoding='utf-8'),flush=True)
    record.update(returncode=result.returncode, completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    records.append(record)
    output.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    assert result.returncode == 0, record
