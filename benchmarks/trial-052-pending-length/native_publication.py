"""Profile frozen binaries serially; retain fixtures and every probe output."""
from pathlib import Path
import datetime, hashlib, json, subprocess, time

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
VARIANTS = {
    'base_050': ROOT / 'benchmarks/trial-050-generation-identity/bin/publication-probe.exe',
    'presized_052': W / 'bin/publication-probe.exe',
}
SOURCES = {
    'base_050': ROOT / 'benchmarks/trial-050-generation-identity/candidate/examples/publication_probe.rs',
    'presized_052': W / 'candidate/examples/publication_probe.rs',
}

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(p, value):
    p.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def initialize():
    assert not (W / 'policy.json').exists()
    sources = {k: sha(v) for k, v in SOURCES.items()}
    assert len(set(sources.values())) == 1, 'Drivers must be byte-identical'
    cases = []
    sizes = [0, 50_000, 99_000]
    for turn in range(3):
        order = list(VARIANTS) if turn % 2 == 0 else list(reversed(VARIANTS))
        for size in sizes[turn:] + sizes[:turn]:
            for variant in order:
                cases.append({'round': turn, 'seed_receipts': size, 'variant': variant,
                              'repetitions': 256, 'batch_rows': 100})
    save(W / 'policy.json', {
        'declared_utc': now(), 'purpose': 'Evaluate exact pending file sizing with synchronized acknowledgment unchanged',
        'engine_change': True, 'default_engine_changed': False, 'promotion_test': False,
        'method': '18 serial fresh fixtures; three alternating pairs per receipt count; sizes rotate each round',
        'timed': 'Only append_once inside frozen native probe; 100 rows and synchronized acknowledgment',
        'excluded': 'Setup, stats, allocations before append call, compact/reclaim every 32 appends, full CRC and reopen',
        'stage_counters': 'After-minus-before totals and histogram deltas include eight maintenance publications; do not label these append-only',
        'max_stage_warning': 'Final max_ms is cumulative high-water, including prefill; cannot subtract maxima',
        'capacity_warning': 'Sequential closed-loop native diagnostic, not sustained open-loop requests/s or the 1M-row 64-client service',
        'freshness': 'Fresh 052 evidence against frozen development 050; predeclared experiment gates are in trial-policy.json',
        'retention': 'Retain every raw stdout, stderr, status and database fixture, including failures; no replacement or best-run selection',
        'process_policy': 'No compile, tests, audit, packaging or Git compression during timing; only one task-owned probe process at once',
        'timeout_seconds_per_case': 600, 'cases': cases,
        'binary_sha256': {k: sha(v) for k, v in VARIANTS.items()}, 'driver_source_sha256': sources,
    })

def run():
    policy = json.loads((W / 'policy.json').read_text(encoding='utf-8'))
    assert not (W / 'native-results.json').exists(), 'Do not restart completed/partial runs'
    for k, p in VARIANTS.items():
        assert sha(p) == policy['binary_sha256'][k]
        assert sha(SOURCES[k]) == policy['driver_source_sha256'][k]
    raw = W / 'raw'
    fixtures = W / 'fixtures'
    raw.mkdir()
    fixtures.mkdir()
    report = {'started_utc': now(), 'policy_sha256': sha(W / 'policy.json'), 'cases': [], 'failures': []}
    save(W / 'native-results.json', report)
    for index, spec in enumerate(policy['cases']):
        label = f"{index:02d}-r{spec['round']}-{spec['seed_receipts']}-{spec['variant']}"
        store = fixtures / label
        started = time.perf_counter()
        status = {'case': spec, 'label': label, 'started_utc': now(), 'fixture': str(store)}
        with (raw / (label + '.stdout.json')).open('w', encoding='utf-8') as out, (raw / (label + '.stderr.txt')).open('w', encoding='utf-8') as err:
            process = subprocess.Popen([str(VARIANTS[spec['variant']]), str(store),
                                        str(spec['seed_receipts']), str(spec['repetitions'])], stdout=out, stderr=err)
            status['pid'] = process.pid
            try:
                status['exit_code'] = process.wait(timeout=policy['timeout_seconds_per_case'])
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                status.update(exit_code=process.returncode, timeout=True)
        status.update(wall_seconds=time.perf_counter() - started, ended_utc=now())
        save(raw / (label + '.status.json'), status)
        if status['exit_code'] != 0:
            report['failures'].append(status)
            save(W / 'native-results.json', report)
            raise RuntimeError(f'Preserved failed case {label}: {status}')
        case = json.loads((raw / (label + '.stdout.json')).read_text(encoding='utf-8'))
        assert case['version'] == '0.3.16' and case['rows_and_sum_match'] and case['reopen_retry_and_full_scrub_passed']
        assert case['prefill_receipt_count'] == spec['seed_receipts'] and case['repetitions'] == 256
        assert len(case['raw_latency_ms']) == len(case['raw_catalog_bytes']) == 256
        report['cases'].append({'spec': spec, 'label': label, 'stdout_sha256': sha(raw / (label + '.stdout.json')),
                                'wall_seconds': status['wall_seconds']})
        save(W / 'native-results.json', report)
        print(json.dumps({'completed': index + 1, 'total': 18, 'label': label,
                          'wall_seconds': status['wall_seconds'], 'max_append_ms': max(case['raw_latency_ms']),
                          'cold_retry_and_scrub_passed': True}), flush=True)
    report.update(completed_utc=now(), completed=True)
    save(W / 'native-results.json', report)

if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--initialize']:
        initialize()
    else:
        assert not sys.argv[1:]
        run()
