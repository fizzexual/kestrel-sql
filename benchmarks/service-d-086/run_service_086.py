"""Serial fresh service cases, complete failed attempts and exact prior binaries."""
from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, json, shutil, sys, traceback

W = Path('D:/Codex/Kestrel/work/perf-086')
sys.path.insert(0, str(W / 'harness'))
from stress_compare import Engine, run_load, percentile
from host_telemetry import HostMonitor

def now(): return datetime.now(timezone.utc).isoformat()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def save(p, v): p.write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8', newline='\n')

policy = load(W / 'policy.json')
bins = {'baseline_a': W / 'binaries/released-016.exe', 'baseline_b': W / 'binaries/released-016.exe',
        'candidate': W / 'binaries/clean-core-061.exe'}
assert all(sha(p) == policy['binary_sha256'][v] for v, p in bins.items())
smoke = sys.argv[1:] == ['--smoke']
assert smoke or not sys.argv[1:]
if smoke:
    assert not (W / 'smoke.json').exists()
    values = []
    for variant in ['baseline_a', 'candidate']:
        engine = Engine('kestrel', W / ('smoke-' + variant), 1000, bins[variant], {}, bridge_args=(0, 0))
        try:
            case = run_load(engine, 'mixed', 4, 1, 100, 100)
            save(W / ('smoke-' + variant + '.json'), case)
            assert case['reconciliation']['all_acknowledged_batches_present']
            values.append({'variant': variant, 'version': engine.version, 'offered': case['offered_operations']})
        finally: engine.finish()
    save(W / 'smoke.json', {'complete': True, 'excluded_from_every_gate': True, 'cases': values})
    print(json.dumps({'smoke_passed': True, 'excluded_from_cohort': True})); sys.exit(0)

assert load(W / 'smoke.json')['complete']
assert load(W / 'pre-timing-process-check.json')['active_processes'] == []
assert not (W / 'paired-service.json').exists()
freeze = load(W / 'timing-freeze.json')
for n, d in freeze['sha256'].items(): assert sha(W / n) == d, n
out = W / 'paired-service.json'
fixtures = W / 'service-fixtures'; fixtures.mkdir()
samples = W / 'paired-service-samples'; samples.mkdir()
report = {'trial': 86, 'policy_sha256': sha(W / 'policy.json'), 'freeze_sha256': sha(W / 'timing-freeze.json'),
    'base_rows': 1_000_000, 'rounds': 6, 'complete': False, 'started_utc': now(),
    'binary_sha256': {v: sha(p) for v, p in bins.items()}, 'cases': [], 'failed_cases': [],
    'method': 'Fresh serial D: stores, six frozen permutations, scheduled-arrival latency including queueing, durable ACK, 100-row batches, zero deliberate group delay, every sample/loss retained.'}
save(out, report)
for index, spec in enumerate(policy['cases']):
    variant = spec['variant']
    label = f"{index:02d}-r{spec['round']}-{variant}-{spec['profile']}-{spec['rate']}-{spec['seconds']}"
    directory = fixtures / label
    engine = None
    print('START ' + label, flush=True)
    try:
        free = shutil.disk_usage(W).free
        assert free > policy['comparison']['disk_preflight_min_free_bytes'], free
        started = now()
        engine = Engine('kestrel', directory, 1_000_000, bins[variant], {}, bridge_args=(0, 0))
        assert engine.version == policy['versions'][variant]
        assert engine.bridge_info['group_delay_ms'] == 0
        with HostMonitor() as monitor:
            case = run_load(engine, spec['profile'], 64, spec['seconds'], spec['rate'], 100)
        raw = case.pop('samples')
        case['operation_latency_ms'] = {}
        for op in ['query', 'append']:
            selected = [s for s in raw if s['ok'] and s['operation'] == op]
            case['operation_latency_ms'][op] = {'successful': len(selected),
                **{name: percentile([s['latency_ms'] for s in selected], q) for name, q in [('p50', .5), ('p95', .95), ('p99', .99)]},
                'max': max((s['latency_ms'] for s in selected), default=None),
                'service_p99': percentile([s['service_ms'] for s in selected], .99)}
        sf = samples / (label + '.jsonl.gz')
        with gzip.open(sf, 'wt', encoding='utf-8') as f:
            for value in raw: f.write(json.dumps(value, separators=(',', ':')) + '\n')
        case.update(variant=variant, round=spec['round'], block=spec['block'], case_index=index,
            host_telemetry=monitor.arrival_samples(case), raw_samples_file=sf.relative_to(W).as_posix(),
            raw_samples_sha256=sha(sf), disk_free_before_case_bytes=free, fixture=str(directory),
            case_started_utc=started, case_finished_utc=now(), native_process_pid=engine.process.pid)
        report['cases'].append(case)
        print(json.dumps({'completed': index+1, 'total': len(policy['cases']), 'label': label,
            'p99_ms': case['latency_ms']['p99'], 'append_p99_ms': case['operation_latency_ms']['append']['p99'],
            'lost': case['unsuccessful_or_unexecuted'], 'acks': case['write_successes']}), flush=True)
    except Exception as error:
        report['failed_cases'].append({'label': label, 'spec': spec, 'error': repr(error), 'traceback': traceback.format_exc(), 'utc': now()})
        save(out, report)
        raise
    finally:
        if engine is not None:
            engine.finish()
            assert engine.process.poll() is not None
        save(out, report)
assert len(report['cases']) == policy['expected_cases'] and not report['failed_cases']
report.update(complete=True, completed_utc=now())
save(out, report)
print(json.dumps({'complete': True, 'cases': len(report['cases']), 'supported_promotion': False}), flush=True)
