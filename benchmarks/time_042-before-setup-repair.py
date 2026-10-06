"""Serial final comparisons and controls; never overlap builds or qualification."""
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
output = ROOT / 'benchmarks/cache-042-run-order.json'
logs = ROOT / 'benchmarks/cache-042-run-logs'
assert not output.exists() and not logs.exists()
logs.mkdir()
build = json.loads((ROOT / 'benchmarks/rust-checks-042.json').read_text(encoding='utf-8'))
adapter = json.loads((ROOT / 'benchmarks/source-042-typed-adapter-build.json').read_text(encoding='utf-8'))
assert build['rust_tests'] == {'debug': 72, 'release': 72, 'passed': True}
assert max(job['completed_at_utc'] for job in build['build_run_order']) < adapter['started_at_utc']
jobs = []
for scope, label in [('small', 'typed'), ('nyc', 'nyc'), ('large', 'large'), ('extended', 'extended'), ('patterns','patterns'), ('irregular','irregular')]:
    arguments = ['benchmarks/group_compare_042.py', '--scope', scope, '--output', f'benchmarks/group-042-{label}-comparison.json']
    if scope == 'small':
        arguments += ['--reuse-small-fixtures']
    if scope == 'extended':
        arguments += ['--reuse-extended-fixtures']
    jobs.append((scope, arguments, f'benchmarks/group-042-{label}-comparison.json'))
candidate = str(WORK / 'perf-042/candidate/group-probe.exe')
baseline = str(ROOT / 'bin/baseline-0.3.11/group-probe.exe')
for name, helper, extra in [
    ('final-pairs', 'cache_controls_042.py', ['--fixture','wide5003','--turns','21','--names','group_sum','group_full','filtered_group']),
    ('highcard-guard-pairs', 'cache_controls_042.py', ['--fixture','cardinality70001','--turns','21','--names','group_sum','group_full']),
    ('sparse-guard-pairs', 'cache_controls_042.py', ['--fixture','sparse19','--turns','21','--names','group_sum','group_full','filtered_group']),
    ('scan-guard-pairs', 'scan_controls_040.py', ['--turns','21']),
    ('tiny-guard-pairs', 'tiny_controls_042.py', ['--turns','21','--repeats','101','--names','group_sum','group_full','filtered_group']),
    ('final-profiles', 'cache_controls_042.py', ['--fixture','wide5003','--profile','--turns','7','--names','group_sum','group_full','filtered_group']),
]:
    report = f'benchmarks/cache-042-{name}.json'
    jobs.append((name, ['benchmarks/'+helper, '--baseline', baseline,
        '--candidate', candidate, '--output', report, *extra], report))
records = []
for name, arguments, report in jobs:
    command = [sys.executable, *arguments]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert adapter['completed_at_utc'] < started
    print('Comparing ' + name, flush=True)
    with (logs / (name + '.txt')).open('w', encoding='utf-8') as stream:
        result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    records.append({'scope': name, 'started_at_utc': started,
        'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'command': command, 'returncode': result.returncode,
        'harness_sha256': hashlib.sha256((ROOT / arguments[0]).read_bytes()).hexdigest()})
    output.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    assert result.returncode == 0, name
    proof = json.loads((ROOT / report).read_text(encoding='utf-8'))
    assert proof['complete'] and proof['binary_sha256']['candidate'] == build['group_probe_sha256']
    print(json.dumps({'scope': name, 'completed_cases': len(proof['cases'])}), flush=True)
