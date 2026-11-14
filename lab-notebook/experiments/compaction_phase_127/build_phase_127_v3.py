"""Actual Archive prerequisites only; trial127 declares no timed cases."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, re, shutil, subprocess, traceback
ROOT = Path('D:/Codex/Kestrel')
WORK = ROOT / 'work/perf-127'
CARGO = 'C:/Users/Frizer/.cargo/bin/cargo.exe'
def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def save(name, value):
    with (WORK / name).open('x', encoding='utf-8') as stream: stream.write(json.dumps(value, indent=2) + '\n')
def utc(): return datetime.now(timezone.utc).isoformat()
policy = load(WORK / 'policy.json'); prep = load(WORK / 'preparation-proof-v3.json')
assert all(sha(WORK / 'candidate-v3' / name) == digest for name, digest in prep['candidate_source_sha256'].items())
assert policy['declared_timed_cases'] == 0 and not (WORK / 'build-proof-v3.json').exists()
assert not any(key in os.environ for key in ['RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_BUILD_TARGET'])
assert not any(key.startswith(('CARGO_PROFILE_RELEASE_', 'KESTREL_FAULT', 'KESTREL_LIVE_PAUSE')) for key in os.environ)
environment = os.environ | {'TMP': str(WORK / 'tmp'), 'TEMP': str(WORK / 'tmp'), 'CARGO_INCREMENTAL': '0',
                            'CARGO_BUILD_JOBS': '4', 'CARGO_TARGET_DIR': str(WORK / 'target')}
jobs = []
for mode, features in [('normal', 'adaptive-compaction-phase-127'), ('fault', 'adaptive-compaction-phase-127,fault-injection')]:
    for release in [False, True]:
        jobs.append((mode + ('-release' if release else '-debug'), ['test', *(['--release'] if release else []), '--features', features]))
    jobs.append((mode + '-lint', ['clippy', '--all-targets', '--features', features]))
jobs.append(('release-artifact', ['build', '--release', '--example', 'compaction_stage_121', '--features', 'adaptive-compaction-phase-127']))
save('build-declaration-v3.json', {'utc': utc(), 'jobs': jobs, 'serial': True, 'baseline154_tests_reused': True, 'all_timed_cases_unstarted': True})
records = []
try:
    for label, options in jobs:
        store = WORK / 'test-stores-v3' / label; store.mkdir()
        command = [CARGO, *options, '--offline', '--locked', *(['--', '-D', 'warnings'] if options[0] == 'clippy' else [])]
        print('START ' + label, flush=True)
        started = utc()
        result = subprocess.run(command, cwd=WORK / 'candidate-v3', env=environment | {'KESTREL_TEST_ROOT': str(store)},
                                capture_output=True, timeout=900, creationflags=0x08000000)
        log = WORK / 'logs-v3' / (label + '.log'); log.write_bytes(result.stdout + result.stderr)
        record = {'label': label, 'actual_exit': result.returncode, 'started_utc': started, 'completed_utc': utc(),
                  'argv': command, 'log_sha256': sha(log)}
        if options[0] == 'test': record['fresh_tests'] = sum(map(int, re.findall(rb'test result: ok\. (\d+) passed;', result.stdout)))
        records.append(record); save('build-v3-step-' + label + '.json', record)
        assert result.returncode == 0, (label, result.stdout[-5000:], result.stderr[-5000:])
        if options[0] == 'test': assert record['fresh_tests'] == 84, record
        if label == 'release-artifact': shutil.copy2(WORK / 'target/release/examples/compaction_stage_121.exe', WORK / 'binary-v3/candidate127.exe')
        print(json.dumps({'passed': label, 'fresh_tests': record.get('fresh_tests')}), flush=True)
    assert all(sha(WORK / 'candidate-v3' / name) == digest for name, digest in prep['candidate_source_sha256'].items())
    size = sum(path.stat().st_size for path in WORK.rglob('*') if path.is_file())
    assert size < policy['local_regenerable_build_cap_bytes'], size
    proof = {'complete': True, 'utc': utc(), 'records': records, 'fresh_Archive_tests': sum(row.get('fresh_tests', 0) for row in records),
             'strict_lints': 2, 'baseline154_tests_and_binary_reused': True,
             'candidate_sha256': sha(WORK / 'binary-v3/candidate127.exe'), 'all_source_byte_exact': True,
             'actual_size_bytes': size, 'timed_cases_declared': 0, 'release017_qualified': False}
    save('build-proof-v3.json', proof)
    print(json.dumps({key: value for key, value in proof.items() if key != 'records'}), flush=True)
except BaseException:
    save('build-failure-v3.json', {'utc': utc(), 'records': records, 'error': traceback.format_exc(), 'timed_cases_declared': 0, 'all_failures_preserved': True})
    raise
