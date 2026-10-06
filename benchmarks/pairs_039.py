"""Short alternating pairs, with copies/setup/scrubs outside query timers."""
import argparse
import datetime
import hashlib
import json
import shutil
import statistics
import time
from pathlib import Path
from group_compare_039 import ROOT, WORK, Probe
import compare

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial-cache', action='store_true')
    args = parser.parse_args()
    label = 'cache-pairs' if args.trial_cache else 'paired-controls'
    output = ROOT / f'benchmarks/group-039-{label}.json'
    assert not output.exists()
    for scope in ['typed', 'nyc', 'large', 'extended']:
        assert json.loads((ROOT/f'benchmarks/group-039-{scope}-comparison.json').read_text())['complete']
    fixtures = []
    for scope in (['typed', 'extended'] if args.trial_cache else ['typed', 'nyc']):
        fixtures += json.loads((ROOT/f'benchmarks/group-039-{scope}-comparison.json').read_text())['fixtures']
    selected = {'dense97': ['group_full', 'unordered_control'], 'sparse19': ['group_sum', 'group_full'],
        'collision19': ['group_sum', 'group_full'], 'wide5003': ['group_full']} if args.trial_cache else {
        'dense97': ['group_full', 'unordered_control', 'prefix_control'], 'sparse19': ['group_full'],
        'cardinality5003': ['group_full'], 'nyc': ['zone', 'all_zones', 'day']}
    turns = 11 if args.trial_cache else 21
    binaries = {'baseline': WORK/'perf-039/typed-trial/group-probe.exe' if args.trial_cache else ROOT/'bin/baseline-0.3.8/group-probe.exe',
        'candidate': WORK/'perf-039/candidate/group-probe.exe'}
    work = WORK / f'group-039-{label}-{time.time_ns()}'; work.mkdir()
    report = {'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'methodology': f'{turns} alternating engine pairs; three warmups and eleven timed samples per query; exact-byte independent fixture copies; setup/copy/scrub outside timers; no overlapping heavy work',
        'baseline_kind': '0.3.9 typed trial without cache' if args.trial_cache else 'released 0.3.8',
        'binary_sha256': {v: hashlib.sha256(p.read_bytes()).hexdigest() for v,p in binaries.items()},
        'cases': [], 'complete': False}
    for fixture in fixtures:
        if fixture['label'] not in selected: continue
        probes = {}
        try:
            for variant, binary in binaries.items():
                archive = work/(fixture['label']+'-'+variant)
                shutil.copytree(fixture['archive'], archive, ignore=shutil.ignore_patterns('*.lock*'))
                for original in Path(fixture['archive']).glob('*.ks2'):
                    assert original.read_bytes() == (archive/original.name).read_bytes()
                probes[variant] = Probe(binary, archive, work/(fixture['label']+'-'+variant+'.stderr.log'))
                assert probes[variant].header['version'] == ('0.3.9' if args.trial_cache or variant == 'candidate' else '0.3.8')
            sqls = dict(fixture['queries'])
            for name in selected[fixture['label']]:
                pairs = []; expected = None
                for turn in range(turns):
                    pair = {}
                    for variant in (['baseline','candidate'] if turn%2 == 0 else ['candidate','baseline']):
                        response = probes[variant].call(op='query', sql=sqls[name], repeats=11)
                        if expected is None: expected = response['result']['rows']
                        assert compare.same(expected, response['result']['rows'])
                        pair[variant] = {'samples_ms': response['samples_ms'], 'median_ms': statistics.median(response['samples_ms']),
                            'plan': response['result']['plan']}
                    pairs.append(pair)
                record = {'fixture': fixture['label'], 'name': name, 'sql': sqls[name], 'pairs': pairs,
                    'baseline_median_ms': statistics.median(p['baseline']['median_ms'] for p in pairs),
                    'candidate_median_ms': statistics.median(p['candidate']['median_ms'] for p in pairs),
                    'paired_candidate_over_baseline_median': statistics.median(p['candidate']['median_ms']/p['baseline']['median_ms'] for p in pairs),
                    'all_results_equal': True}
                report['cases'].append(record); output.write_text(json.dumps(report, indent=2)+'\n')
                print(json.dumps({k:record[k] for k in ['fixture','name','baseline_median_ms','candidate_median_ms','paired_candidate_over_baseline_median']}), flush=True)
            for probe in probes.values(): assert probe.call(op='verify')['verified_bytes'] == fixture['rows']*24
        finally:
            for probe in probes.values(): probe.finish()
    report.update(complete=True, completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    output.write_text(json.dumps(report, indent=2)+'\n')

if __name__ == '__main__': main()
