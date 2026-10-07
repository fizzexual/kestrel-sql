from pathlib import Path
import datetime, hashlib, json, shutil, subprocess, time

W = Path(__file__).resolve().parent

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(p, j):
    p.write_text(json.dumps(j, indent=2) + '\n', encoding='utf-8')

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def initialize():
    assert not (W / 'policy.json').exists()
    build = json.loads((W / 'build-provenance.json').read_text())
    assert sha(W / 'reservation-probe.exe') == build['binary_sha256']
    cases = []
    for turn in range(3):
        modes = ['growing', 'reserved'] if turn % 2 == 0 else ['reserved', 'growing']
        sizes = [2400, 153600] if turn % 2 == 0 else [153600, 2400]
        for size in sizes:
            for mode in modes:
                cases.append({'round': turn, 'mode': mode, 'payload_bytes': size, 'repetitions': 256})
    save(W / 'policy.json', {'declared_utc': now(), 'model_only': True, 'language': 'English',
         'binary_sha256': build['binary_sha256'], 'source_sha256': build['source_sha256'],
         'hypothesis': 'Filling a retained journal with zeros before commits might reduce ongoing file-growth cost; test before any Archive WAL design.',
         'motivation': '056 large-frame persistent-file totals fail; 055 service sync dominates. Earlier 052 per-generation set_len trial was rejected and is not reused.',
         'reading': 'PostgreSQL documents wal_init_zero can allocate space before WAL writes on some filesystems; this motivates a hypothesis, not a claimed Windows result.',
         'primary_source': 'https://www.postgresql.org/docs/current/runtime-config-wal.html#GUC-WAL-INIT-ZERO',
         'normal': 'Create retained file, write header, sync bootstrap, write/flush/sync_all every commit while extending file.',
         'candidate': 'Create retained file, write header and actual zero bytes for every planned frame, sync bootstrap, seek to first frame, write/flush/sync_all every commit within reserved extent.',
         'cost_accounting': 'Report bootstrap create/fill/sync/seek/total, commit quantiles and total, bootstrap+commit total, actual setup-and-commit wall including equal frame generation. No bootstrap cost hidden.',
         'timers': 'Native commit timers exclude equal payload generation/encoding/CRC. Whole setup-and-commit wall includes it. Both exclude final cold verification.',
         'frame_domain': 'Identical 056 headers/CRC/footer/payload; independent byte-equivalence within each 057 pair and against earlier frozen 056 files.',
         'scope': 'Not SQL, not Archive publication/recovery. No source offsets, receipt IDs, checkpoint, rotation, bounded WAL growth, readers, retention, concurrency or crash qualification.',
         'limits': 'Finite fixture reservation knows count in advance. No physical power-loss or filesystem allocation guarantee. Future WAL must budget and rotate capacity and implement crash recovery.',
         'method': '12 fresh serial cases; three alternating pairs per byte volume. All raw results and fixtures retained; original 056 results not overwritten or combined.',
         'predeclared_hypothesis_checks': {'commit_total_ratio_at_each_size_at_most': .85, 'bootstrap_plus_commit_total_ratio_at_each_size_at_most': .90,
              'setup_and_commit_wall_ratio_at_each_size_at_most': .90, 'commit_p99_ratio_at_each_size_at_most': .95,
              'commit_p50_guard_at_each_size_at_most': 1.05},
         'control': 'No compilation/tests/audits/packaging/Git compression or other CPU-heavy jobs while native timers run. One task-owned child at a time, stopped after case.',
         'free_space_guard_bytes': 500000000, 'case_timeout_seconds': 300, 'cases': cases,
         'decision': 'Even passing all five checks at both sizes only motivates archive-specific design; no engine upgrade or promotion.'})

def run():
    assert not (W / 'model-results.json').exists()
    policy = json.loads((W / 'policy.json').read_text())
    assert sha(W / 'reservation-probe.exe') == policy['binary_sha256']
    (W / 'raw').mkdir()
    (W / 'fixtures').mkdir()
    results = {'started_utc': now(), 'policy_sha256': sha(W / 'policy.json'), 'cases': [], 'failures': [], 'complete': False}
    save(W / 'model-results.json', results)
    for i, spec in enumerate(policy['cases']):
        label = f"{i:02d}-r{spec['round']}-{spec['payload_bytes']}-{spec['mode']}"
        fixture = W / 'fixtures' / label
        status = {'label': label, 'spec': spec, 'started_utc': now(), 'free_bytes_before_case': shutil.disk_usage(W).free}
        if status['free_bytes_before_case'] <= policy['free_space_guard_bytes']:
            status['preflight_failure'] = 'free_space_guard_before_process_creation'
            results['failures'].append(status)
            save(W / 'model-results.json', results)
            raise RuntimeError(status)
        started = time.perf_counter()
        with (W / 'raw' / (label + '.stdout.json')).open('w') as out, (W / 'raw' / (label + '.stderr.txt')).open('w') as err:
            child = subprocess.Popen([str(W / 'reservation-probe.exe'), str(fixture), spec['mode'], str(spec['payload_bytes']), str(spec['repetitions'])], stdout=out, stderr=err)
            status['pid'] = child.pid
            try:
                status['exit_code'] = child.wait(timeout=policy['case_timeout_seconds'])
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
                status.update(exit_code=child.returncode, timeout=True)
        status.update(wall_seconds=time.perf_counter() - started, completed_utc=now())
        save(W / 'raw' / (label + '.status.json'), status)
        if status['exit_code'] != 0:
            results['failures'].append(status)
            save(W / 'model-results.json', results)
            raise RuntimeError(status)
        raw = W / 'raw' / (label + '.stdout.json')
        data = json.loads(raw.read_text())
        assert data['sync_all_each_commit'] and data['bootstrap_sync_before_commits'] and data['bootstrap_cost_reported_and_charged']
        assert data['cold_exact_frame_bytes_verified'] and not data['sql_source_receipt_checkpoint_retention_and_crash_qualification']
        assert data['mode'] == spec['mode'] and data['payload_bytes'] == spec['payload_bytes'] and len(data['raw_samples']) == 256
        results['cases'].append({'label': label, 'spec': spec, 'stdout_sha256': sha(raw)})
        save(W / 'model-results.json', results)
        print(json.dumps({'completed': i + 1, 'total': 12, 'label': label, 'bootstrap_ms': data['bootstrap']['total_ms'],
                          'max_commit_ms': max(s['total_ms'] for s in data['raw_samples']), 'cold_exact_frames_passed': True, 'model_only': True}), flush=True)
    results.update(complete=True, completed_utc=now())
    save(W / 'model-results.json', results)

if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--initialize']:
        initialize()
    else:
        assert not sys.argv[1:]
        run()
