"""Run all four comparison scopes serially after compilation is complete."""
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
output = ROOT / 'benchmarks/group-039-run-order.json'
logs = ROOT / 'benchmarks/group-039-run-logs'
assert not output.exists() and not logs.exists()
logs.mkdir()
build = json.loads((ROOT/'benchmarks/rust-checks-039.json').read_text())
adapter = json.loads((ROOT/'benchmarks/source-039-typed-adapter-build.json').read_text())
assert build['rust_tests'] == {'debug': 69, 'release': 69, 'passed': True}
assert max(job['completed_at_utc'] for job in build['build_run_order']) < adapter['started_at_utc']
records = []
for scope, label in [('small','typed'), ('nyc','nyc'), ('large','large'), ('extended','extended')]:
    command = [sys.executable, 'benchmarks/group_compare_039.py', '--scope', scope, '--output', f'benchmarks/group-039-{label}-comparison.json']
    if scope == 'small': command += ['--reuse-small-fixtures']
    if scope == 'extended': command += ['--reuse-extended-fixtures']
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert adapter['completed_at_utc'] < started
    print('Comparing ' + scope, flush=True)
    with (logs/(scope+'.txt')).open('w') as stream:
        result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    records.append({'scope': scope, 'started_at_utc': started,
        'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'command': command, 'returncode': result.returncode,
        'harness_sha256': hashlib.sha256((ROOT/'benchmarks/group_compare_039.py').read_bytes()).hexdigest()})
    output.write_text(json.dumps(records, indent=2)+'\n')
    assert result.returncode == 0, scope
    report = json.loads((ROOT/f'benchmarks/group-039-{label}-comparison.json').read_text())
    assert report['complete'] and report['binary_sha256']['candidate'] == build['group_probe_sha256']
    print(json.dumps({'scope': scope, 'completed_engine_round_cases': len(report['cases'])}), flush=True)
