"""Predeclared 21 native released/core-061 pairs; immutable 060 input."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import subprocess

W = Path(__file__).resolve().parent
ROOT = W / 'lab/outputs/kestrel-sql'
WORK = W / 'lab/work'
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def save(v):
    (W / 'primary.json').write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8')
policy = json.loads((W / 'policy.json').read_text())
config = policy['primary_range_goal']
assert json.loads((W / 'qualification.json').read_text())['complete']
assert not (W / 'primary.json').exists()
bins = {'baseline': ROOT / 'bin/baseline-0.3.16/group-probe.exe',
        'candidate': WORK / 'perf-061/candidate/group-probe.exe'}
assert sha(bins['candidate']) == json.loads((ROOT / 'benchmarks/rust-checks-061.json').read_text())['group_probe_sha256']
raw_dir = W / 'primary-raw'
raw_dir.mkdir()
report = {'trial': 61, 'started_utc': datetime.now(timezone.utc).isoformat(),
          'policy_sha256': sha(W / 'policy.json'), 'harness_sha256': sha(Path(__file__)),
          'binary_sha256': {v: sha(p) for v, p in bins.items()}, 'cases': [],
          'summaries': [], 'failed_cases': [], 'complete': False}
save(report)
for turn in range(config['pairs']):
    order = ['baseline', 'candidate'] if turn % 2 == 0 else ['candidate', 'baseline']
    queries = config['queries'][turn % 4:] + config['queries'][:turn % 4]
    for variant in order:
        label = f'{turn:02d}-{variant}'
        raw = raw_dir / (label + '.jsonl')
        stderr = raw_dir / (label + '.stderr')
        p = None
        try:
            with raw.open('w', encoding='utf-8') as out, stderr.open('w', encoding='utf-8') as err:
                p = subprocess.Popen([str(bins[variant]), config['fixture']], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=err, text=True, encoding='utf-8')
                def receive():
                    line = p.stdout.readline()
                    assert line, (label, 'probe stopped', p.poll())
                    out.write(line)
                    out.flush()
                    return json.loads(line)
                def request(obj):
                    p.stdin.write(json.dumps(obj) + '\n')
                    p.stdin.flush()
                    return receive()
                try:
                    header = receive()
                    assert header['version'] == policy[variant]
                    assert header['stats']['rows'] == config['rows']
                    case = {'round': turn, 'variant': variant, 'header': header, 'queries': []}
                    for q in queries:
                        response = request({'op': 'query', 'sql': q['sql'], 'repeats': config['repeats']})
                        assert response['result']['rows'] == q['expected_rows'], (label, q['name'])
                        samples = response['samples_ms']
                        assert len(samples) == config['repeats']
                        case['queries'].append({'name': q['name'], 'median_ms': statistics.median(samples),
                                                'samples_ms': samples, 'rows': response['result']['rows']})
                    case['verify'] = request({'op': 'verify'})
                    assert case['verify']['verified_bytes'] == config['rows'] * 24
                finally:
                    p.stdin.close()
                    try:
                        p.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.wait(timeout=10)
                    p.stdout.close()
                assert p.returncode == 0 and stderr.stat().st_size == 0, label
            case['raw_file'] = raw.relative_to(W).as_posix()
            case['raw_sha256'] = sha(raw)
            report['cases'].append(case)
        except Exception as error:
            report['failed_cases'].append({'label': label, 'error': repr(error)})
            raise
        finally:
            if p is not None and p.poll() is None:
                p.kill()
                p.wait(timeout=10)
            save(report)
    print(json.dumps({'pair': turn, 'complete': True, 'children_stopped': True}), flush=True)
for q in config['queries']:
    medians = {v: [] for v in bins}
    ratios = []
    for turn in range(config['pairs']):
        pair = {c['variant']: next(x for x in c['queries'] if x['name'] == q['name'])
                for c in report['cases'] if c['round'] == turn}
        for v in bins:
            medians[v].append(pair[v]['median_ms'])
        ratios.append(pair['candidate']['median_ms'] / pair['baseline']['median_ms'])
    ratio = statistics.median(ratios)
    report['summaries'].append({'query': q['name'], 'baseline_median_ms': statistics.median(medians['baseline']),
                                'candidate_median_ms': statistics.median(medians['candidate']),
                                'paired_ratios': ratios, 'median_paired_ratio': ratio,
                                'candidate_slower_pairs': sum(r > 1 for r in ratios),
                                'goal_passed': ratio <= config['paired_ratio_max']})
report['complete'] = True
report['completed_utc'] = datetime.now(timezone.utc).isoformat()
save(report)
print(json.dumps({'complete': True, 'summaries': report['summaries']}), flush=True)
