"""Measure bounded coalescing policies with fresh fixtures and complete loss evidence."""
import argparse
import concurrent.futures
import gzip
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

from host_telemetry import HostMonitor
from stress_compare import Engine, percentile, run_load

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {
    'anonymous-mixed': ('mixed', 64, 2000, False),
    'receipt-mixed': ('mixed', 64, 2000, True),
    'receipt-write': ('write', 64, 2000, True),
    'single-mixed': ('mixed', 1, 500, False),
    'burst': ('mixed', 64, 10000, False),
    'scan': ('scan', 64, 200, False),
    'retry-only': ('retry', 64, 2000, True),
    'retry-mixed': ('retry_mixed', 64, 2000, True),
    'retry-burst': ('retry', 64, 10000, True),
}


def prepare_replays(engine):
    """128 distinct committed batches; setup and original receipt capture untimed."""
    def commit(index):
        lo = engine.rows + index*100
        data = [[i,(i*37)%1000-500,(i*17)%97] for i in range(lo,lo+100)]
        connection = engine.connect()
        try:
            identifier = f'known:{index}'
            receipt = connection.call({'op':'append','id':identifier,'data':data})
            assert not receipt['duplicate'] and receipt['affected']==100
            return identifier,data,receipt['generation']
        finally:
            connection.close()
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        catalog = list(pool.map(commit,range(128)))
    engine.rows += 12800
    return catalog


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--baseline-seed', type=Path, required=True)
    parser.add_argument('--candidate-seed', type=Path, required=True)
    parser.add_argument('--baseline-version', default='0.3.3')
    parser.add_argument('--candidate-version', default='0.3.4')
    parser.add_argument('--variants', default='baseline,delay0,delay2,delay8')
    parser.add_argument('--profiles', default='anonymous-mixed,receipt-mixed,receipt-write')
    parser.add_argument('--rounds', type=int, default=3)
    parser.add_argument('--seconds', type=int, default=15)
    parser.add_argument('--ids', type=int, default=50_000)
    parser.add_argument('--rows', type=int, default=1_000_000)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    variants, scenarios = args.variants.split(','), args.profiles.split(',')
    policies = {'baseline': None, 'baseline8': 8, 'delay0': 0, 'delay2': 2, 'delay8': 8, 'delay20': 20, 'indexed0':0, 'indexed8':8, 'duckdb': None}
    assert len(set(variants)) == len(variants) and set(variants) <= policies.keys()
    assert len(set(scenarios)) == len(scenarios) and set(scenarios) <= SCENARIOS.keys()
    assert not ('duckdb' in variants and any(SCENARIOS[s][3] for s in scenarios))
    assert 1 <= args.rounds <= 5 and 1 <= args.seconds <= 120
    assert 1 <= args.ids <= 90_000 and 1000 <= args.rows <= 10_000_000
    binaries = {'baseline': args.baseline.resolve(), 'candidate': args.candidate.resolve()}
    seeds = {'baseline': args.baseline_seed.resolve(), 'candidate': args.candidate_seed.resolve()}
    versions = {'baseline': args.baseline_version, 'candidate': args.candidate_version}
    report = {
        'base_rows': args.rows, 'prefill_receipt_ids': args.ids,
        'methodology': 'paced open-loop common harness; scheduled-arrival latency; 256-slot client queue; 2s expiry; 8s socket timeout; independent fresh fixture per case; 100-row durable appends; order rotates each round; fixture seed/scrub, reconciliation and sample compression outside load; no compilation or heavy overlap; success percentiles and all offer losses retained; shared Windows desktop',
        'policy_ms': {v: policies[v] for v in variants},
        'binary_sha256': {n: hashlib.sha256(p.read_bytes()).hexdigest() for n,p in binaries.items()},
        'seed_binary_sha256': {n: hashlib.sha256(p.read_bytes()).hexdigest() for n,p in seeds.items()},
        'cases': [], 'failed_cases': [], 'orders': [],
    }
    work = ROOT.parent.parent/'work'/f'group-commit-{time.time_ns()}'
    work.mkdir()
    samples = args.output.parent/(args.output.stem+'-samples')
    samples.mkdir(exist_ok=True)
    for turn in range(args.rounds):
        offset = turn % len(variants)
        order = variants[offset:] + variants[:offset]
        report['orders'].append(order)
        for scenario in scenarios:
            profile, clients, rate, identified = SCENARIOS[scenario]
            for variant in order:
                family = 'baseline' if variant.startswith('baseline') else 'candidate'
                name = 'duckdb' if variant == 'duckdb' else 'kestrel'
                directory = work/f'{turn}-{scenario}-{variant}'
                engine = None
                print(f'Round {turn+1}: {scenario}, {variant}, {rate}/s', flush=True)
                try:
                    if identified:
                        seeded = json.loads(subprocess.check_output([str(seeds[family]), str(directory/'archive'), str(args.ids), str(args.rows)], text=True, timeout=120))
                        assert seeded['version'] == versions[family] and seeded['full_scrub_passed']
                    bridge_args = () if variant in ['baseline','duckdb'] else (policies[variant],)
                    if variant.startswith('indexed'):
                        bridge_args=(policies[variant],1)
                    engine = Engine(name, directory, args.rows, binaries[family], {}, existing=identified, bridge_args=bridge_args)
                    if name == 'kestrel':
                        assert engine.version == versions[family]
                        assert engine.bridge_info.get('group_delay_ms',0) == (policies[variant] or 0)
                    replays = prepare_replays(engine) if profile in ['retry','retry_mixed'] else None
                    with HostMonitor() as monitor:
                        case = run_load(engine, profile, clients, args.seconds, rate, 100, identified=identified, replay_catalog=replays)
                    if identified:
                        connection = engine.connect()
                        stats = connection.call({'op':'stats'})
                        assert stats['recorded_batch_ids'] == args.ids + (128 if replays else 0) + case['reconciliation']['published_batches']
                        size = args.rows//args.ids
                        receipt = connection.call({'op':'append','id':'seed:0','data':[[i,(i*37)%1000-500,(i*17)%97] for i in range(size)]})
                        assert receipt['duplicate'] and receipt['generation'] == 1
                        if replays:
                            for identifier,data,generation in replays:
                                receipt = connection.call({'op':'append','id':identifier,'data':data})
                                assert receipt['duplicate'] and receipt['generation']==generation and receipt['affected']==100
                            case['known_receipts_after_reopen'] = 128
                        connection.close()
                        case['seed_replay_passed'] = True
                        case['final_receipt_count'] = stats['recorded_batch_ids']
                    case.update(variant=variant, round=turn, scenario=scenario, configured_group_delay_ms=policies[variant], host_telemetry=monitor.arrival_samples(case))
                    for operation in ['query','append','replay']:
                        good = [s['latency_ms'] for s in case['samples'] if s['ok'] and s['operation'] == operation]
                        case[f'{operation}_latency_ms'] = {k: percentile(good,p) for k,p in [('p50',.5),('p95',.95),('p99',.99)]}
                    if name == 'kestrel':
                        before, after = case['ingest_state_before_load'], case['live_state_before_reopen']['ingest']
                        assert after['flush_delay_ms'] == (policies[variant] or 0)
                        case['load_group_commits'] = after['durable_group_commits'] - before['durable_group_commits']
                        case['batches_per_durable_group'] = case['write_successes']/case['load_group_commits'] if case['load_group_commits'] else 0
                        assert after.get('max_group_requests',1) <= 64
                    sample_file = samples/f'{variant}-{scenario}-{turn}.jsonl.gz'
                    with gzip.open(sample_file,'wt',encoding='utf-8') as stream:
                        for sample in case.pop('samples'):
                            stream.write(json.dumps(sample,separators=(',',':'))+'\n')
                    case['raw_samples_file'] = str(sample_file.relative_to(args.output.parent))
                    report['cases'].append(case)
                    print(json.dumps({k:case[k] for k in ['variant','round','scenario','successful_rps_in_arrival_window','latency_ms','append_latency_ms','unsuccessful_or_unexecuted']}),flush=True)
                except Exception as error:
                    report['failed_cases'].append({'variant':variant,'round':turn,'scenario':scenario,'error':repr(error)})
                    raise
                finally:
                    if engine is not None:
                        engine.finish()
                    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
                resolved = directory.resolve()
                assert resolved.is_relative_to(work.resolve()) and resolved != work.resolve()
                shutil.rmtree(resolved)
    assert len(report['cases']) == args.rounds*len(variants)*len(scenarios) and not report['failed_cases']
    print(json.dumps({'report':str(args.output),'completed_cases':len(report['cases'])}))


if __name__ == '__main__':
    main()
