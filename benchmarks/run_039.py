"""Run correctness/recovery serially after every comparison and paired control."""
import datetime
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent/'work'
output = ROOT/'benchmarks/correctness-039-run-order.json'
parser = argparse.ArgumentParser(); parser.add_argument('--resume', action='store_true'); args=parser.parse_args()
assert not output.exists() or args.resume
for name in ['paired-controls', 'cache-pairs']:
    assert json.loads((ROOT/f'benchmarks/group-039-{name}.json').read_text())['complete']
cli = WORK/'perf-039/candidate/kestrel.exe'
bridge = WORK/'perf-039/candidate/kestrel-stress.exe'
adapter = WORK/'perf-039/candidate/source-pipeline-typed.exe'
faults = WORK/'kestrel-039-fault-build/release/examples'
jobs = [
    ('stage-profiles', ['benchmarks/profile_group_039.py', '--binary', str(WORK/'perf-039/candidate/group-probe.exe'), '--output', 'benchmarks/group-039-final-profiles.json']),
    ('sql-differential', ['benchmarks/archive_verify.py', '--binary', str(cli), '--output', 'benchmarks/archive-039-verification.json', '--queries', '500']),
    ('expanded-and-sparse-sql', ['benchmarks/group_verify_039.py']),
    ('publication-cuts-corruptions', ['benchmarks/publication_faults.py', '--binary', str(bridge), '--sql-binary', str(cli), '--fault-driver', str(faults/'publication_fault_probe.exe'), '--expected-version', '0.3.9', '--output', 'benchmarks/publication-039-faults.json']),
    ('concurrent-forced-kills', ['benchmarks/group_commit_recovery.py', '--binary', str(bridge), '--expected-version', '0.3.9', '--retry-index', '--output', 'benchmarks/group-039-recovery.json']),
    ('source-cuts-and-kills', ['benchmarks/source_faults.py', '--adapter', str(adapter), '--driver', str(faults/'source_fault_probe.exe'), '--output', 'benchmarks/source-039-faults.json']),
    ('parquet-source-pipeline', ['benchmarks/source_pipeline_demo.py', '--binary', str(adapter), '--expected-version', '0.3.9', '--output', 'portfolio/source-pipeline-039-results.json']),
    ('wide-json-and-sparse-reopen', ['benchmarks/wire_039.py']),
]
records = json.loads(output.read_text()) if output.exists() else []
for name, arguments in jobs:
    if any(r['suite']==name and r['returncode']==0 for r in records): continue
    record = {'suite': name, 'command': [sys.executable, *arguments],
        'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'harness_sha256': hashlib.sha256((ROOT/arguments[0]).read_bytes()).hexdigest()}
    print(name, flush=True)
    result = subprocess.run(record['command'], cwd=ROOT)
    record.update(returncode=result.returncode, completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    records.append(record); output.write_text(json.dumps(records, indent=2)+'\n')
    assert result.returncode == 0, record
