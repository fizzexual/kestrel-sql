"""Alternating scan profiles; setup and full CRC scrubs are outside timings."""
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'benchmarks'/'perf-032-profile.json')
    args=parser.parse_args()
    binaries={'baseline':args.baseline.resolve(),'candidate':args.candidate.resolve()}
    work=ROOT.parent.parent/'work'/f'scan-profile-{time.time_ns()}';work.mkdir()
    report={'binary_sha256':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in binaries.items()},
        'probe_source_sha256':hashlib.sha256((ROOT/'examples'/'scan_profile.rs').read_bytes()).hexdigest(),
        'methodology':'three alternating rounds, fresh 1M-row fixtures, identical probe source; stage instrumentation enabled; eleven samples after three warmups; independent results and full scrubs; not network throughput',
        'cases':[]}
    expected=None
    for turn in range(3):
        for variant in (['baseline','candidate'] if turn%2==0 else ['candidate','baseline']):
            directory=work/f'{turn}-{variant}'
            case=json.loads(subprocess.check_output([str(binaries[variant]),str(directory),'1000000'],text=True))
            assert case['version']=={'baseline':'0.3.1','candidate':'0.3.2'}[variant]
            assert case['verified_bytes']==24_000_000
            rows={q['sql']:q['result']['rows'] for q in case['cases']}
            if expected is None:expected=rows
            assert rows==expected
            case.update(variant=variant,round=turn,results_equal_across_builds=True)
            report['cases'].append(case)
            args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            print(json.dumps({'variant':variant,'round':turn,'full_scrub_passed':True}),flush=True)
            resolved=directory.resolve()
            assert resolved.is_relative_to(work.resolve()) and resolved!=work.resolve()
            shutil.rmtree(resolved)


if __name__=='__main__':main()
