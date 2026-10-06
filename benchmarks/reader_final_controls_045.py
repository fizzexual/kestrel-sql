"""Sequential same-archive controls; instrumentation is separate from query timings."""
import argparse
import datetime
import hashlib
import json
import statistics
import time
from pathlib import Path

import compare
from group_compare_040 import ROOT, WORK, Probe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, default=ROOT / 'bin/baseline-0.3.14/group-probe.exe')
    parser.add_argument('--candidate', type=Path, default=ROOT / 'bin/group-probe.exe')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--profile', action='store_true')
    parser.add_argument('--fixture', choices=['irregular5003'], default='irregular5003')
    parser.add_argument('--turns', type=int, default=7)
    parser.add_argument('--repeats', type=int, default=11)
    parser.add_argument('--names', nargs='+', choices=['group_sum', 'group_full', 'filtered_group', 'unordered_control', 'prefix_control'])
    args = parser.parse_args()
    assert 1 <= args.turns <= 31 and 1 <= args.repeats <= 101
    assert not args.output.exists()
    scope = 'typed' if args.fixture in ['dense97','sparse19','cardinality5003'] else 'extended'
    previous = json.loads((ROOT / 'benchmarks/group-045-irregular-comparison.json').read_text(encoding='utf-8'))
    fixture = next(f for f in previous['fixtures'] if f['label'] == args.fixture)
    rows = fixture['rows']
    archive = Path(fixture['archive'])
    queries = fixture['queries']
    if args.names:
        queries = [(name, sql) for name, sql in queries if name in args.names]
    work = WORK / f'reader-045-final-controls-{time.time_ns()}'
    work.mkdir()
    binaries = {'baseline': args.baseline.resolve(), 'candidate': args.candidate.resolve()}
    report = {
        'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'binary_sha256': {v: hashlib.sha256(p.read_bytes()).hexdigest() for v, p in binaries.items()},
        'probe_source_sha256': hashlib.sha256((ROOT / 'examples/group_probe.rs').read_bytes()).hexdigest(),
        'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'fixture': fixture,
        'methodology': {
            'turns': args.turns, 'repeats': args.repeats, 'warmups': 3, 'threads': 1,
            'same_archive': True, 'sequential_open_close': True, 'instrumented': args.profile,
            'timing': 'ArchiveSnapshot::query; setup/open/close/assertions/full scrubs excluded',
            'limits': 'warm shared Windows desktop; profiled stage samples excluded from competitive claims; no network or power-loss qualification',
        },
        'cases': [], 'complete': False,
    }
    for name, sql in queries:
        pairs = []
        expected = None
        for turn in range(args.turns):
            pair = {}
            for variant in (['baseline', 'candidate'] if turn % 2 == 0 else ['candidate', 'baseline']):
                probe = Probe(binaries[variant], archive, work / f'{name}-{turn}-{variant}.stderr.log')
                try:
                    assert probe.header['stats']['rows'] == rows
                    response = probe.call(op='query', sql=sql, repeats=args.repeats, profile=args.profile)
                    if expected is None:
                        expected = response['result']['rows']
                    assert compare.same(expected, response['result']['rows']), (name, variant, turn)
                    value = {
                        'version': probe.header['version'], 'samples_ms': response['samples_ms'],
                        'median_ms': statistics.median(response['samples_ms']),
                        'result': {**response['result'], 'rows': {'count':len(expected), 'sha256':hashlib.sha256(json.dumps(expected, separators=(',',':')).encode()).hexdigest(), 'first':expected[:3], 'last':expected[-3:]}},
                    }
                    if args.profile:
                        value['profiles'] = response['profiles']
                        value['stage_median_ms'] = {stage: statistics.median(p[stage] for p in response['profiles'])
                            for stage in ['page_read_ms', 'selection_ms', 'aggregate_ms']}
                    if turn == args.turns - 1:
                        assert probe.call(op='verify')['verified_bytes'] == rows * 24
                        value['full_scrub_bytes'] = rows * 24
                    pair[variant] = value
                finally:
                    probe.finish()
            pairs.append(pair)
        result = {
            'name': name, 'sql': sql, 'pairs': pairs, 'all_results_equal': True,
            'baseline_median_ms': statistics.median(p['baseline']['median_ms'] for p in pairs),
            'candidate_median_ms': statistics.median(p['candidate']['median_ms'] for p in pairs),
            'paired_candidate_over_baseline_median': statistics.median(p['candidate']['median_ms'] / p['baseline']['median_ms'] for p in pairs),
        }
        if args.profile:
            result['stage_median_ms'] = {variant: {stage: statistics.median(p[variant]['stage_median_ms'][stage] for p in pairs)
                for stage in ['page_read_ms', 'selection_ms', 'aggregate_ms']} for variant in binaries}
        report['cases'].append(result)
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({k: v for k, v in result.items() if k != 'pairs'}), flush=True)
    report.update(complete=True, completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
