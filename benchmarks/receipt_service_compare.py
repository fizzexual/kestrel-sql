"""Repeated service comparisons with a large retained receipt ledger."""
import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
import struct
import time
from pathlib import Path

from host_telemetry import HostMonitor
from stress_compare import Engine, run_load

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--baseline-seed', type=Path, required=True)
    parser.add_argument('--candidate-seed', type=Path, required=True)
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--seconds', type=int, default=15)
    parser.add_argument('--ids', type=int, default=50_000)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert 1 <= args.rounds <= 5 and 1 <= args.seconds <= 30 and 1 <= args.ids <= 90_000
    binaries = {'baseline': args.baseline.resolve(), 'candidate': args.candidate.resolve()}
    seeds = {'baseline': args.baseline_seed.resolve(), 'candidate': args.candidate_seed.resolve()}
    for path in [*binaries.values(), *seeds.values()]:
        data = path.read_bytes()
        assert data[:2] == b'MZ', ('invalid executable header', str(path))
        offset = struct.unpack_from('<I',data,60)[0]
        assert data[offset:offset+4] == b'PE\0\0' and struct.unpack_from('<H',data,offset+4)[0] == 0x8664
    versions = {'baseline':'0.3.2', 'candidate':'0.3.3'}
    work = ROOT.parent.parent/'work'/f'receipt-service-{time.time_ns()}'
    work.mkdir()
    samples = args.output.parent/(args.output.stem+'-samples')
    samples.mkdir(exist_ok=True)
    report = {'base_rows':1_000_000, 'prefill_receipt_ids':args.ids,
        'methodology':'paced open-loop common harness; 64 clients; 2000 offers/s; mixed=5% and write=25% durable identified 100-row appends; 1M standard rows with retained receipts; three alternating rounds; fixture build/scrub outside load; no compilation or heavy overlap; raw samples and failures retained; shared desktop, no universal ranking',
        'binary_sha256': {name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in binaries.items()},
        'seed_binary_sha256': {name:hashlib.sha256(p.read_bytes()).hexdigest() for name,p in seeds.items()},
        'seed_source_sha256':hashlib.sha256((ROOT/'examples/receipt_seed.rs').read_bytes()).hexdigest(),
        'cases':[], 'failed_cases':[]}
    for turn in range(args.rounds):
        order = list(binaries) if turn % 2 == 0 else list(reversed(binaries))
        for profile in ['mixed','write']:
            for variant in order:
                directory = work/f'{turn}-{profile}-{variant}'
                seeded = json.loads(subprocess.check_output([str(seeds[variant]),str(directory/'archive'),str(args.ids),'1000000'], text=True, timeout=120))
                assert seeded['version'] == versions[variant] and seeded['full_scrub_passed']
                engine = None
                try:
                    engine = Engine('kestrel',directory,1_000_000,binaries[variant],{},existing=True)
                    assert engine.version == versions[variant]
                    with HostMonitor() as monitor:
                        case = run_load(engine,profile,64,args.seconds,2000,100,identified=True)
                    connection = engine.connect()
                    stats = connection.call({'op':'stats'})
                    assert stats['recorded_batch_ids'] == args.ids + case['reconciliation']['published_batches']
                    # Replay a setup ID with the exact standard 20-row payload.
                    size = 1_000_000//args.ids
                    lo,hi = 0,size
                    request = {'op':'append','id':'seed:0','data':[[i,(i*37)%1000-500,(i*17)%97] for i in range(lo,hi)]}
                    receipt = connection.call(request)
                    assert receipt['duplicate'] and receipt['generation'] == 1
                    connection.close()
                    case.update(variant=variant,round=turn,prefill_receipt_ids=args.ids,
                        final_receipt_count=stats['recorded_batch_ids'],seed_replay_passed=True,
                        final_catalog_chain_files=stats.get('catalog_chain_files'),
                        host_telemetry=monitor.arrival_samples(case))
                    file = samples/f'{variant}-{profile}-{turn}.jsonl.gz'
                    with gzip.open(file,'wt',encoding='utf-8') as stream:
                        for sample in case.pop('samples'):
                            stream.write(json.dumps(sample,separators=(',',':'))+'\n')
                    case['raw_samples_file'] = str(file.relative_to(args.output.parent))
                    report['cases'].append(case)
                    print(json.dumps({k:case[k] for k in ['variant','round','profile','successful_rps_in_arrival_window','latency_ms','unsuccessful_or_unexecuted','final_receipt_count']}),flush=True)
                except Exception as error:
                    report['failed_cases'].append({'variant':variant,'round':turn,'profile':profile,'error':repr(error)})
                    raise
                finally:
                    if engine is not None:
                        engine.finish()
                    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
                resolved = directory.resolve()
                assert resolved.is_relative_to(work.resolve()) and resolved != work.resolve()
                shutil.rmtree(resolved)
    assert len(report['cases']) == args.rounds*4 and not report['failed_cases']
    print(json.dumps({'report':str(args.output),'completed_cases':len(report['cases'])}))


if __name__ == '__main__':
    main()
