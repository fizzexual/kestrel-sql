"""Serial final comparisons and controls; never overlap builds or qualification."""
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
output = ROOT / 'benchmarks/dense-043-run-order.json'
logs = ROOT / 'benchmarks/dense-043-run-logs'
parser=argparse.ArgumentParser()
parser.add_argument('--resume',action='store_true')
args=parser.parse_args()
assert args.resume or (not output.exists() and not logs.exists())
logs.mkdir(exist_ok=args.resume)
build = json.loads((ROOT / 'benchmarks/rust-checks-043.json').read_text(encoding='utf-8'))
adapter = json.loads((ROOT / 'benchmarks/source-043-typed-adapter-build.json').read_text(encoding='utf-8'))
assert build['rust_tests'] == {'debug': 73, 'release': 73, 'passed': True}
assert max(job['completed_at_utc'] for job in build['build_run_order']) < adapter['started_at_utc']
jobs = []
for scope, label in [('small', 'typed'), ('nyc', 'nyc'), ('large', 'large'), ('extended', 'extended'), ('patterns','patterns'), ('irregular','irregular')]:
    arguments = ['benchmarks/group_compare_043.py', '--scope', scope, '--output', f'benchmarks/group-043-{label}-comparison.json']
    if scope == 'small':
        arguments += ['--reuse-small-fixtures']
    if scope == 'extended':
        arguments += ['--reuse-extended-fixtures']
    jobs.append((scope, arguments, f'benchmarks/group-043-{label}-comparison.json'))
candidate = str(WORK / 'perf-043/candidate/group-probe.exe')
baseline = str(ROOT / 'bin/baseline-0.3.12/group-probe.exe')
for name, helper, extra in [
    ('final-pairs','dense_controls_043.py',['--fixture','10000000','--turns','21','--repeats','11','--names','group_sum','group_full','filtered_group']),
    ('dense5003-guard-pairs','dense_controls_043.py',['--fixture','cardinality5003','--turns','21','--names','group_sum','group_full','filtered_group']),
    ('sparse-guard-pairs','dense_controls_043.py',['--fixture','sparse19','--turns','21','--names','group_sum','group_full','filtered_group']),
    ('wide-guard-pairs','dense_controls_043.py',['--fixture','wide5003','--turns','21','--names','group_sum','group_full','filtered_group']),
    ('irregular-guard-pairs','irregular_controls_043.py',['--turns','21','--names','group_sum','group_full','filtered_group','unordered_control']),
    ('highcard-guard-pairs','cache_controls_042.py',['--fixture','cardinality70001','--turns','21','--names','group_sum','group_full']),
    ('scan-guard-pairs','scan_controls_040.py',['--turns','21']),
    ('tiny-guard-pairs','tiny_controls_043.py',['--turns','21','--repeats','101','--names','group_sum','group_full','filtered_group']),
    ('large-pairs','dense_controls_043.py',['--fixture','100000000','--turns','7','--repeats','5','--names','group_sum','group_full']),
    ('final-profiles','dense_controls_043.py',['--fixture','10000000','--profile','--turns','7','--repeats','11','--names','group_sum','group_full','filtered_group']),
    ('large-profiles','dense_controls_043.py',['--fixture','100000000','--profile','--turns','3','--repeats','3','--names','group_sum']),
]:
    report=f'benchmarks/dense-043-{name}.json'
    jobs.append((name,['benchmarks/'+helper,'--baseline',baseline,'--candidate',candidate,'--output',report,*extra],report))
assert len(jobs)==17

records = json.loads(output.read_text(encoding='utf-8')) if output.exists() else []
for name, arguments, report in jobs:
    if any(r['scope']==name and r['returncode']==0 for r in records):
        proof=json.loads((ROOT/report).read_text(encoding='utf-8'))
        assert proof['complete'] and proof['binary_sha256']['candidate']==build['group_probe_sha256']
        continue
    command = [sys.executable, *arguments]
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    assert adapter['completed_at_utc'] < started
    print('Comparing ' + name, flush=True)
    attempts=sum(r['scope']==name for r in records)
    log=logs/(name+(f'-retry-{attempts}' if attempts else '')+'.txt')
    assert not log.exists()
    with log.open('w', encoding='utf-8') as stream:
        result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    records.append({'scope': name, 'started_at_utc': started,
        'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'command': command, 'returncode': result.returncode, 'log':str(log),
        'harness_sha256': hashlib.sha256((ROOT / arguments[0]).read_bytes()).hexdigest()})
    output.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    assert result.returncode == 0, name
    proof = json.loads((ROOT / report).read_text(encoding='utf-8'))
    assert proof['complete'] and proof['binary_sha256']['candidate'] == build['group_probe_sha256']
    print(json.dumps({'scope': name, 'completed_cases': len(proof['cases'])}), flush=True)
