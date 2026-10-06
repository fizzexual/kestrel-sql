"""Short alternating engine pairs to investigate unchanged-control regressions."""
import datetime
import hashlib
import json
import shutil
import statistics
import time
from pathlib import Path
from group_compare_038 import Probe, queries
import compare

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
output = ROOT / 'benchmarks/group-038-paired-controls.json'
assert not output.exists()
for scope in ['typed', 'nyc', 'large']:
    assert json.loads((ROOT / f'benchmarks/group-038-{scope}-comparison.json').read_text())['complete']
work = WORK / f'group-controls-038-{time.time_ns()}'; work.mkdir()
small = json.loads((ROOT / 'benchmarks/group-038-typed-comparison.json').read_text())
nyc = json.loads((ROOT / 'benchmarks/group-038-nyc-comparison.json').read_text())
fixtures = [*small['fixtures'], nyc['fixtures'][0]]
report = {'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'methodology': '21 short alternating baseline/candidate pairs per query; eleven timed samples plus three warmups each call; two exact-byte independent archive copies to avoid shared writer lock; copy/setup/scrubs outside timers; no other heavy job',
    'cases': [], 'complete': False}
for fixture in fixtures:
    probes = {}
    try:
        for variant in ['baseline', 'candidate']:
            archive = work / (fixture['label'] + '-' + variant)
            shutil.copytree(fixture['archive'], archive, ignore=shutil.ignore_patterns('*.lock*'))
            for original in Path(fixture['archive']).glob('*.ks2'):
                assert original.read_bytes() == (archive / original.name).read_bytes()
            binary = WORK / f'perf-038/{variant}/group-probe.exe'
            probes[variant] = Probe(binary, archive, work / f'{fixture["label"]}-{variant}.stderr.log')
        cases = dict(fixture['queries'])
        names = {'dense97': ['group_full', 'unordered_control', 'prefix_control'],
            'sparse19': ['group_full'], 'cardinality5003': ['group_full'],
            'nyc': ['zone', 'all_zones', 'day']}[fixture['label']]
        for name in names:
            sql = cases[name]; pairs = []; expected = None
            for turn in range(21):
                pair = {}
                for variant in (['baseline', 'candidate'] if turn % 2 == 0 else ['candidate', 'baseline']):
                    result = probes[variant].call(op='query', sql=sql, repeats=11)
                    if expected is None: expected = result['result']['rows']
                    assert compare.same(expected, result['result']['rows'])
                    pair[variant] = {'samples_ms': result['samples_ms'], 'median_ms': statistics.median(result['samples_ms']), 'plan': result['result']['plan']}
                pairs.append(pair)
            record = {'fixture': fixture['label'], 'name': name, 'sql': sql, 'pairs': pairs,
                'paired_candidate_over_baseline_median': statistics.median(p['candidate']['median_ms']/p['baseline']['median_ms'] for p in pairs),
                'baseline_median_ms': statistics.median(p['baseline']['median_ms'] for p in pairs),
                'candidate_median_ms': statistics.median(p['candidate']['median_ms'] for p in pairs), 'all_results_equal': True}
            report['cases'].append(record)
            output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
            print(json.dumps({key: record[key] for key in ['fixture', 'name', 'baseline_median_ms', 'candidate_median_ms', 'paired_candidate_over_baseline_median']}), flush=True)
        for probe in probes.values(): assert probe.call(op='verify')['verified_bytes'] == fixture['rows'] * 24
    finally:
        for probe in probes.values(): probe.finish()
report.update(complete=True, completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
