"""Alternating direct Archive CLI timings with exact before/after results checked."""
import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--rounds',type=int,default=3)
    parser.add_argument('--output',type=Path,default=ROOT/'benchmarks'/'perf-031-core.json')
    args = parser.parse_args()
    assert 1 <= args.rounds <= 5
    binaries = {'baseline':args.baseline.resolve(),'candidate':args.candidate.resolve()}
    work = ROOT.parent.parent/'work'/f'core-compare-{time.time_ns()}';work.mkdir()
    report = {'methodology':'identical 1M ordered fixture; one thread; three warmups then 31 repetitions; alternating order; fresh archive each case; setup and full scrub outside query timings; repeated fixed queries, not general SQL',
        'binary_sha256':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in binaries.items()},'cases':[]}
    expected = None
    for turn in range(args.rounds):
        order = list(binaries) if turn%2==0 else list(reversed(binaries))
        for variant in order:
            case = json.loads(subprocess.check_output([str(binaries[variant]),'--archive',str(work/f'{turn}-{variant}'),'--scale','1000000','31'],text=True))
            assert case['version']=={'baseline':'0.3.0','candidate':'0.3.1'}[variant], ('incorrect CLI build',variant,case['version'])
            assert case['verified_bytes']==24_000_000
            values = {q['sql']:q['result']['rows'] for q in case['queries']}
            if expected is None:expected=values
            assert values==expected
            case.update(variant=variant,round=turn,results_equal_across_builds=True)
            report['cases'].append(case)
            args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            print(json.dumps({'variant':variant,'round':turn,'median_us':{q['name']:q['median_us'] for q in case['queries']}}),flush=True)


if __name__ == '__main__':
    main()
