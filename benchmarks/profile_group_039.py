"""Profile the measured losing group paths separately from competitive timers."""
import argparse
import datetime
import hashlib
import json
import statistics
import time
from pathlib import Path
from group_compare_038 import ROOT, WORK, Probe, queries

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, default=ROOT / 'bin/baseline-0.3.8/group-probe.exe')
    parser.add_argument('--output', type=Path, default=ROOT / 'benchmarks/group-039-baseline-profiles.json')
    args = parser.parse_args()
    assert not args.output.exists()
    fixtures = json.loads((ROOT / 'benchmarks/group-038-typed-comparison.json').read_text())['fixtures']
    work = WORK / ('group-039-profile-' + args.output.stem + '-' + str(time.time_ns())); work.mkdir()
    report = {'binary_sha256': hashlib.sha256(args.binary.read_bytes()).hexdigest(),
        'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'methodology': 'instrumented stage times, three rounds, three warmups and eleven samples; excluded from competitive benchmarks',
        'cases': []}
    for turn in range(3):
        for fixture in fixtures:
            probe = Probe(args.binary, Path(fixture['archive']), work / f"{turn}-{fixture['label']}.stderr.log")
            try:
                for name, sql in queries(fixture['rows'])[:3]:
                    result = probe.call(op='query', sql=sql, repeats=11, profile=True)
                    profiles = result['profiles']
                    report['cases'].append({'round': turn, 'fixture': fixture['label'], 'query': name,
                        'plan': result['result']['plan'], 'samples_ms': result['samples_ms'], 'profiles': profiles})
                    print(json.dumps({'round': turn, 'fixture': fixture['label'], 'query': name,
                        'stage_medians_ms': {stage: statistics.median(p[stage] for p in profiles)
                            for stage in ['page_read_ms', 'selection_ms', 'aggregate_ms']}}), flush=True)
                assert probe.call(op='verify')['verified_bytes'] == fixture['rows'] * 24
            finally: probe.finish()
    report['completed_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    args.output.write_text(json.dumps(report, indent=2) + '\n')

if __name__ == '__main__': main()
