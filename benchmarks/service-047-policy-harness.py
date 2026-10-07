"""Current-release service qualification; fresh stores and explicit overload accounting.

Uses the unchanged historical arrival/expiry/reconciliation harness. No build,
fixture creation, scrub, restart, sample compression or report work overlaps load.
"""
import argparse
import ctypes
import datetime
import gzip
import hashlib
import json
import os
import shutil
import time
from ctypes import wintypes
from pathlib import Path

from host_telemetry import HostMonitor
from stress_compare import Engine, percentile, run_load

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'


def process_cpu(process):
    if process is None or os.name != 'nt':
        return None
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    values = [wintypes.FILETIME() for _ in range(4)]
    if not kernel.GetProcessTimes(wintypes.HANDLE(int(process._handle)), *(ctypes.byref(v) for v in values)):
        raise ctypes.WinError(ctypes.get_last_error())
    return sum(v.dwLowDateTime + (v.dwHighDateTime << 32) for v in values[2:]) / 10_000_000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['baseline', 'policy', 'soak', 'reference'], default='baseline')
    parser.add_argument('--rounds', type=int, default=1)
    parser.add_argument('--seconds', type=int, default=8)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--variants', default='kestrel,postgres,mysql,mariadb,sqlite,duckdb')
    args = parser.parse_args()
    assert 1 <= args.rounds <= 3 and 2 <= args.seconds <= 15
    assert not args.output.exists(), 'Preserve completed and unsuccessful reports'
    frozen_harness = args.output.with_name(args.output.stem + '-harness.py')
    assert not frozen_harness.exists()
    shutil.copyfile(__file__, frozen_harness)
    binary = ROOT / 'bin/baseline-0.3.16/kestrel-stress.exe'
    proof = json.loads((ROOT / 'benchmarks/baseline-0.3.16-provenance.json').read_text())
    binary_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
    assert binary_hash == proof['baseline_binary_sha256']['kestrel-stress.exe']
    work = WORK / f'service-047-{args.mode}-{time.time_ns()}'
    work.mkdir()
    samples_directory = args.output.parent / (args.output.stem + '-samples')
    samples_directory.mkdir()
    servers_path = WORK / 'stress-engines/running.json'
    servers = json.loads(servers_path.read_text()) if servers_path.exists() else {}
    if args.mode == 'baseline':
        variants = ['delay0']
        configs = [('read', 64, args.seconds, 500), ('mixed', 1, args.seconds, 500),
                   ('mixed', 64, args.seconds, 2000), ('mixed', 64, args.seconds, 10000),
                   ('write', 64, args.seconds, 500), ('scan', 64, args.seconds, 200),
                   ('mixed', 64, 60, 500)]
    elif args.mode == 'policy':
        variants = ['delay0', 'delay2', 'delay8']
        configs = [('mixed', 64, args.seconds, 2000), ('mixed', 64, args.seconds, 10000),
                   ('write', 64, args.seconds, 500)]
    elif args.mode == 'soak':
        variants = ['delay0', 'delay8']
        configs = [('mixed', 64, 60, 500)]
    else:
        variants = args.variants.split(',')
        assert len(set(variants)) == len(variants)
        assert set(variants) <= {'kestrel', 'postgres', 'mysql', 'mariadb', 'sqlite', 'duckdb'}
        configs = [('mixed', 64, args.seconds, 2000)]
    report = {'version': '0.3.16', 'mode': args.mode, 'rounds': args.rounds,
              'base_rows': 1_000_000, 'bridge_sha256': binary_hash,
              'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'disk_free_before_bytes': shutil.disk_usage(WORK).free,
              'frozen_harness': frozen_harness.relative_to(args.output.parent).as_posix(),
              'work_directory': str(work), 'methodology': {
                  'arrivals': 'Unchanged stress_compare.run_load; seed 20261006; paced open loop; scheduled-arrival latency; bounded queue 256; expiry 2s; connection timeout 8s',
                  'writes': '100 rows per synchronized append; mixed 5%, write 25%; 5% late timestamps; no identified receipt IDs in this service workload',
                  'ordering': 'Rotate variant order by one each round; fresh million-row store for every case',
                  'durability': 'No weakened synchronization or ACK policy. 0/2/8ms are existing explicit LiveOptions policies, not an engine change',
                  'limits': 'Shared Windows laptop, loopback JSON test bridge vs native reference interfaces, no affinity. Short sweeps and one 60s soak; not production qualification or universal ranking',
                  'serialization': 'No compilation or another heavy task overlaps a timed case. Scrubs, reopen, fixture creation, samples/report work outside load'},
              'harness_sha256': {name: hashlib.sha256((ROOT / 'benchmarks' / name).read_bytes()).hexdigest()
                                 for name in ['service_047.py', 'stress_compare.py', 'host_telemetry.py']},
              'orders': [], 'cases': [], 'failed_cases': [], 'complete': False}
    for turn in range(args.rounds):
        offset = turn % len(variants)
        order = variants[offset:] + variants[:offset]
        report['orders'].append(order)
        for profile, clients, seconds, rate in configs:
            for variant in order:
                label = f'{turn}-{variant}-{profile}-{clients}-{rate}-{seconds}'
                directory = work / label
                engine = None
                started = datetime.datetime.now(datetime.timezone.utc).isoformat()
                print('START ' + label, flush=True)
                try:
                    free_before_case = shutil.disk_usage(WORK).free
                    assert free_before_case > 1_000_000_000, 'Less than 1GB free: stop before creating another fixture'
                    is_kestrel = variant.startswith('delay') or variant == 'kestrel'
                    delay = int(variant[5:]) if variant.startswith('delay') else 0
                    engine = Engine('kestrel' if is_kestrel else variant, directory,
                                    1_000_000, binary, servers, bridge_args=(delay, 0))
                    if is_kestrel:
                        assert engine.version == '0.3.16' and engine.bridge_info['group_delay_ms'] == delay
                    measured_process = engine.process
                    cpu_start = process_cpu(measured_process)
                    client_start = time.process_time()
                    with HostMonitor() as monitor:
                        case = run_load(engine, profile, clients, seconds, rate, 100)
                    # Keep the original process handle: run_load restarts the
                    # bridge before reconciliation. Includes load/setup of worker
                    # connections and diagnostic reads, excludes the new process.
                    case['client_cpu_seconds_load_and_reconciliation'] = time.process_time() - client_start
                    case['server_cpu_before_load_seconds'] = cpu_start
                    case['server_cpu_seconds_load_connections_and_diagnostics'] = (
                        process_cpu(measured_process) - cpu_start if cpu_start is not None else None)
                    case['host_telemetry'] = monitor.arrival_samples(case)
                    raw = case.pop('samples')
                    assert len(raw) + case['queue_dropped'] + case['queue_expired'] == case['offered_operations']
                    assert case['successful_operations'] + case['unsuccessful_or_unexecuted'] == case['offered_operations']
                    case['operation_latency_ms'] = {}
                    for operation in ['query', 'append']:
                        selected = [s for s in raw if s['ok'] and s['operation'] == operation]
                        case['operation_latency_ms'][operation] = {
                            'successful': len(selected),
                            'p50': percentile([s['latency_ms'] for s in selected], .5),
                            'p95': percentile([s['latency_ms'] for s in selected], .95),
                            'p99': percentile([s['latency_ms'] for s in selected], .99),
                            'service_p99': percentile([s['service_ms'] for s in selected], .99)}
                    sample = samples_directory / (label + '.jsonl.gz')
                    with gzip.open(sample, 'wt', encoding='utf-8') as stream:
                        for value in raw:
                            stream.write(json.dumps(value, separators=(',', ':')) + '\n')
                    case.update(variant=variant, round=turn, started_at_utc=started,
                                disk_free_before_case_bytes=free_before_case,
                                completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                raw_samples_file=sample.relative_to(args.output.parent).as_posix(),
                                raw_samples_sha256=hashlib.sha256(sample.read_bytes()).hexdigest(),
                                fixture_directory=str(directory))
                    report['cases'].append(case)
                    print(json.dumps({key: case[key] for key in ['variant', 'profile', 'clients', 'offered_rps',
                                                                 'successful_rps_in_arrival_window', 'latency_ms',
                                                                 'operation_latency_ms', 'unsuccessful_or_unexecuted']}), flush=True)
                except Exception as error:
                    report['failed_cases'].append({'label': label, 'started_at_utc': started, 'error': repr(error)})
                    print('FAILED ' + repr(error), flush=True)
                finally:
                    if engine is not None:
                        engine.finish()
                    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    assert not report['failed_cases'], report['failed_cases']
    assert len(report['cases']) == len(variants) * len(configs) * args.rounds
    report['complete'] = True
    report['completed_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'complete': True, 'cases': len(report['cases']), 'output': str(args.output)}), flush=True)


if __name__ == '__main__':
    main()
