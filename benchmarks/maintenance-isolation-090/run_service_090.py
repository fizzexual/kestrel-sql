"""Fresh serial original/default/trace service cases; all getters outside timers."""
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import json
import shutil
import sys
import time
import traceback

W = Path('D:/Codex/Kestrel/work/perf-090')
sys.path.insert(0, str(W / 'harness'))
from stress_compare import Engine, run_load, percentile
from host_telemetry import HostMonitor
from native_resources_088 import read_process

def now():
    return datetime.now(timezone.utc).isoformat()
def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

class OutsideWindow:
    def __init__(self, traced):
        self.traced = traced
        self.before = None
    def pre(self, engine):
        self.before = read_process(engine.process.pid)
    def post(self, engine, report):
        after = read_process(engine.process.pid)
        assert (after['pid'], after['creation_filetime']) == (self.before['pid'], self.before['creation_filetime'])
        ticks = after['kernel_100ns'] + after['user_100ns'] - self.before['kernel_100ns'] - self.before['user_100ns']
        assert ticks >= 0
        result = {'before': self.before, 'after_before_trace_getter': after,
            'charged_native_cpu_100ns': ticks, 'charged_native_cpu_seconds': ticks / 10_000_000,
            'peak_working_set_bytes': after['peak_working_set_bytes'],
            'peak_commit_bytes': after['peak_commit_bytes'], 'trace': None}
        if self.traced:
            connection = engine.connect()
            deadline = time.perf_counter() + 15
            calls = 0
            try:
                while True:
                    trace = connection.call({'op': 'writer_trace'})
                    calls += 1
                    if not trace['active_cycle']:
                        break
                    if time.perf_counter() >= deadline:
                        raise RuntimeError('Owned traced writer did not become idle after producers stopped')
                    time.sleep(.001)
                assert trace['dropped_events'] == 0
                result['trace'] = trace
                result['outside_window_getter_calls'] = calls
            finally:
                connection.close()
        return result

policy = load(W / 'policy.json')
smoke = sys.argv[1:] in [['--smoke'], ['--smoke-v2']]
smoke_prefix = 'smoke-v2' if sys.argv[1:] == ['--smoke-v2'] else 'smoke'
assert smoke or not sys.argv[1:]
for name, digest in policy['binary_sha256'].items():
    assert sha(W / 'binaries' / (name + '.exe')) == digest

if smoke:
    assert not (W / (smoke_prefix + '.json')).exists()
    result = {'complete': False, 'excluded_from_every_gate': True, 'cases': [], 'failed': []}
    for name in policy['binary_sha256']:
        engine = None
        try:
            engine = Engine('kestrel', W / (smoke_prefix + '-' + name), 1000, W / 'binaries' / (name + '.exe'), {}, bridge_args=(0, 0))
            assert engine.version == policy['versions'][name]
            hooks = OutsideWindow(name.endswith('-writer'))
            case = run_load(engine, 'write', 4, 1, 100, 100, before_arrivals=hooks.pre, after_load=hooks.post)
            assert case['reconciliation']['all_acknowledged_batches_present']
            case['binary'] = name
            save(W / (smoke_prefix + '-' + name + '.json'), case)
            result['cases'].append({'binary': name, 'offered': case['offered_operations'],
                'lost': case['unsuccessful_or_unexecuted'], 'resources_and_reopen_passed': True})
        except Exception as error:
            result['failed'].append({'binary': name, 'error': repr(error), 'traceback': traceback.format_exc()})
            save(W / (smoke_prefix + '-incomplete.json'), result)
            raise
        finally:
            if engine is not None:
                engine.finish()
    assert len(result['cases']) == 3 and not result['failed']
    result['complete'] = True
    save(W / (smoke_prefix + '.json'), result)
    print(json.dumps({'smokes_passed': 4, 'excluded_from_every_gate': True}), flush=True)
    sys.exit(0)

assert load(W / 'smoke-v2.json')['complete']
assert load(W / 'pre-timing-process-check.json')['active_processes'] == []
assert not (W / 'paired-service.json').exists()
freeze = load(W / 'timing-freeze.json')
for name, digest in freeze['sha256'].items():
    assert sha(W / name) == digest
fixtures = W / 'service-fixtures'
samples = W / 'raw-samples'
fixtures.mkdir()
samples.mkdir()
output = W / 'paired-service.json'
report = {'trial': 90, 'complete': False, 'started_utc': now(), 'policy_sha256': sha(W / 'policy.json'),
    'freeze_sha256': sha(W / 'timing-freeze.json'), 'cases': [], 'failed_cases': [],
    'method': 'All fixed cases; exact binaries; resource samples/getters after drain and before reopen; no simultaneous heavy work.'}
save(output, report)
for index, spec in enumerate(policy['cases']):
    label = f"{index:03d}-r{spec['round']:02d}-{spec['family']}-{spec['profile']}-{spec['variant']}"
    directory = fixtures / label
    engine = None
    print('START ' + label, flush=True)
    try:
        free = shutil.disk_usage(W).free
        assert free > policy['disk_min_free_bytes']
        started = now()
        binary = W / 'binaries' / (spec['binary'] + '.exe')
        engine = Engine('kestrel', directory, policy['base_rows'], binary, {}, bridge_args=(0, 0))
        assert engine.version == policy['versions'][spec['binary']]
        assert engine.bridge_info['group_delay_ms'] == 0 and not engine.bridge_info['retry_index_enabled']
        hooks = OutsideWindow(spec['binary'].endswith('-writer'))
        with HostMonitor() as monitor:
            case = run_load(engine, spec['profile'], 64, spec['seconds'], spec['rate'], 100,
                before_arrivals=hooks.pre, after_load=hooks.post)
        raw = case.pop('samples')
        case['operation_latency_ms'] = {}
        for operation in ['query', 'append']:
            selected = [s for s in raw if s['ok'] and s['operation'] == operation]
            values = [s['latency_ms'] for s in selected]
            case['operation_latency_ms'][operation] = {'successful': len(selected),
                **{name: percentile(values, q) for name, q in [('p50', .5), ('p95', .95), ('p99', .99)]},
                'max': max(values, default=None), 'service_p99': percentile([s['service_ms'] for s in selected], .99)}
        sf = samples / (label + '.jsonl.gz')
        with gzip.open(sf, 'wt', encoding='utf-8') as stream:
            for value in raw:
                stream.write(json.dumps(value, separators=(',', ':')) + '\n')
        case.update(**{name: spec[name] for name in ['family', 'stage', 'core', 'binary', 'variant', 'round', 'block']},
            case_index=index, fixture=str(directory), raw_samples_file=sf.relative_to(W).as_posix(), raw_samples_sha256=sha(sf),
            host_telemetry=monitor.arrival_samples(case), disk_free_before_case_bytes=free,
            case_started_utc=started, case_finished_utc=now())
        report['cases'].append(case)
        print(json.dumps({'completed': index + 1, 'total': len(policy['cases']), 'label': label,
            'p99_ms': case['latency_ms']['p99'], 'append_p99_ms': case['operation_latency_ms']['append']['p99'],
            'lost': case['unsuccessful_or_unexecuted'], 'peak_native_bytes': case['post_load_diagnostic']['peak_working_set_bytes']}), flush=True)
    except Exception as error:
        report['failed_cases'].append({'label': label, 'spec': spec, 'error': repr(error), 'traceback': traceback.format_exc(), 'utc': now()})
        report['unstarted_case_indices'] = list(range(index + 1, len(policy['cases'])))
        save(output, report)
        raise
    finally:
        if engine is not None:
            engine.finish()
            assert engine.process.poll() is not None
        save(output, report)
assert len(report['cases']) == 144 and not report['failed_cases']
report.update(complete=True, completed_utc=now())
save(output, report)
print(json.dumps({'complete': True, 'cases': 144, 'supported_promotion': False}), flush=True)
