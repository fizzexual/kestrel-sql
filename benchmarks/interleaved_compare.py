"""Repeated, rotated local comparisons with fresh fixtures and raw loss accounting."""
import argparse
import gzip
import hashlib
import json
import shutil
import time
from pathlib import Path

from host_telemetry import HostMonitor
from stress_compare import Engine, run_load

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--variants',default='baseline,candidate,postgres,mysql,mariadb,sqlite,duckdb')
    parser.add_argument('--rounds',type=int,default=3)
    parser.add_argument('--seconds',type=int,default=15)
    parser.add_argument('--scan-seconds',type=int,default=8)
    parser.add_argument('--rows',type=int,default=1_000_000)
    parser.add_argument('--analytics',action='store_true')
    parser.add_argument('--scans',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'benchmarks'/'perf-031-interleaved.json')
    parser.add_argument('--servers',type=Path,default=ROOT.parent.parent/'work'/'stress-engines'/'running.json')
    args = parser.parse_args()
    variants = args.variants.split(',')
    assert len(set(variants))==len(variants) and set(variants)<=set(['baseline','candidate','postgres','mysql','mariadb','sqlite','duckdb'])
    assert 1<=args.rounds<=5 and 1<=args.seconds<=30 and 1<=args.scan_seconds<=30 and 1000<=args.rows<=10_000_000
    binaries = {'baseline':args.baseline.resolve(),'candidate':args.candidate.resolve()}
    servers = json.loads(args.servers.read_text(encoding='utf-8')) if args.servers.exists() else {}
    report = {'base_rows':args.rows,'seed':20261006,'rounds':args.rounds,
        'methodology':'paced open-loop common harness; 64 clients; 100-row durable appends; order rotates by two positions per round; fresh fixture each case; no compilation/other timed workload overlaps; shared desktop, no affinity; no universal database ranking',
        'binary_sha256':{name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in binaries.items()},
        'orders':[],'cases':[],'failed_cases':[]}
    work = ROOT.parent.parent/'work'/f'interleaved-{time.time_ns()}';work.mkdir()
    samples = args.output.parent/(args.output.stem+'-samples');samples.mkdir(exist_ok=True)
    profiles = [('analytics' if args.analytics else 'mixed',args.seconds,2000)]
    if args.scans:profiles.append(('scan',args.scan_seconds,200))
    for turn in range(args.rounds):
        offset = turn*2%len(variants)
        order = variants[offset:]+variants[:offset]
        report['orders'].append(order)
        for profile,seconds,rate in profiles:
            for variant in order:
                directory = work/f'{turn}-{profile}-{variant}'
                name = 'kestrel' if variant in binaries else variant
                binary = binaries.get(variant,binaries['candidate'])
                engine = None
                print(f'Round {turn+1}: {variant}, {profile}, {rate}/s',flush=True)
                try:
                    engine = Engine(name,directory,args.rows,binary,servers)
                    if variant in binaries:
                        assert engine.version == {'baseline':'0.3.0','candidate':'0.3.1'}[variant], ('incorrect bridge build',variant,engine.version)
                    with HostMonitor() as monitor:
                        case = run_load(engine,profile,64,seconds,rate,100)
                    case.update(variant=variant,round=turn,host_telemetry=monitor.arrival_samples(case))
                    sample_file = samples/f'{variant}-{profile}-{turn}.jsonl.gz'
                    with gzip.open(sample_file,'wt',encoding='utf-8') as file:
                        for sample in case.pop('samples'):
                            file.write(json.dumps(sample,separators=(',',':'))+'\n')
                    case['raw_samples_file'] = str(sample_file.relative_to(args.output.parent))
                    report['cases'].append(case)
                    print(json.dumps({key:case[key] for key in ['variant','round','profile','successful_rps_in_arrival_window','latency_ms','unsuccessful_or_unexecuted']}),flush=True)
                except Exception as error:
                    report['failed_cases'].append({'variant':variant,'round':turn,'profile':profile,'error':repr(error)})
                    print(f'FAILED: {error!r}',flush=True)
                finally:
                    if engine is not None:engine.finish()
                args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
                resolved = directory.resolve()
                assert resolved.is_relative_to(work.resolve()) and resolved != work.resolve()
                if resolved.exists():shutil.rmtree(resolved)
    expected = len(variants)*args.rounds*len(profiles)
    assert len(report['cases'])==expected and not report['failed_cases'],report['failed_cases']
    print(json.dumps({'report':str(args.output),'completed_cases':expected}))


if __name__ == '__main__':
    main()
