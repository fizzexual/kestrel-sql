"""Alternate two identical core probes; setup/scrub are outside replay timings."""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--ids', type=int, default=50_000)
    parser.add_argument('--repetitions', type=int, default=1000)
    parser.add_argument('--output', type=Path, default=ROOT/'benchmarks'/'perf-031-replay.json')
    args = parser.parse_args()
    assert 1 <= args.rounds <= 5 and 1 <= args.ids <= 100_000 and 10 <= args.repetitions <= 10_000
    work = ROOT.parent.parent/'work'/f'replay-{time.time_ns()}'
    work.mkdir()
    binaries = {'baseline':args.baseline.resolve(), 'candidate':args.candidate.resolve()}
    report = {'methodology':'identical Rust probe source; release builds; alternating order; fresh receipt store each case; in-process replay timings include allocation and validation; setup and full scrub excluded',
        'probe_source_sha256':hashlib.sha256((ROOT/'examples'/'performance_probe.rs').read_bytes()).hexdigest(),
        'binary_sha256':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in binaries.items()},
        'cases':[]}
    for turn in range(args.rounds):
        order = list(binaries) if turn % 2 == 0 else list(reversed(binaries))
        for variant in order:
            output = subprocess.check_output([str(binaries[variant]),str(work/f'{turn}-{variant}'),str(args.ids),str(args.repetitions)], text=True)
            case = json.loads(output)
            assert case['version'] == {'baseline':'0.3.0','candidate':'0.3.1'}[variant], ('incorrect probe build',variant,case['version'])
            assert case['no_new_publication'] and case['rows_and_sum_match'] and case['full_scrub_passed']
            case.update(variant=variant, round=turn)
            report['cases'].append(case)
            args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            print(json.dumps({key:case[key] for key in ['variant','round','version','receipt_count','latency_ms']}),flush=True)
    print(json.dumps({'report':str(args.output),'cases':len(report['cases'])}))


if __name__ == '__main__':
    main()
