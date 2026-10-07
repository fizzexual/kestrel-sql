from pathlib import Path
import subprocess, os, json, hashlib, shutil, datetime

w = Path(__file__).parent
standard = w.parent / 'kestrel-048-build'
fault = w.parent / 'kestrel-048-fault-build'
env = {**os.environ, 'CARGO_TARGET_DIR': str(standard),
       'TMP': str(w.parent / 'rust-temp-032'), 'TEMP': str(w.parent / 'rust-temp-032'),
       'KESTREL_TEST_ROOT': str(w.parent / 'cargo-tests')}
assert json.loads((w / 'regression-before-fix-result.json').read_text(encoding='utf-8-sig'))['actual_exit'] == 101
old = w.parent / 'perf-049'
old_proof = json.loads((old / 'build-provenance.json').read_text(encoding='utf-8'))
for name, digest in old_proof['binaries'].items():
    assert hashlib.sha256((old / 'bin' / name).read_bytes()).hexdigest() == digest

def run(name, arguments, build_env=env):
    command = ['cargo', arguments[0], '--manifest-path', str(w / 'candidate/Cargo.toml'), *arguments[1:]]
    log = w / (name + '.txt')
    assert not log.exists(), log
    print('START ' + name, flush=True)
    with log.open('w', encoding='utf-8') as f:
        result = subprocess.run(command, env=build_env, stdout=f, stderr=subprocess.STDOUT)
    if result.returncode:
        print(log.read_text(encoding='utf-8')[-7000:], flush=True)
        raise SystemExit(result.returncode)
    print('PASS ' + name, flush=True)

run('fmt', ['fmt'])
run('fmt-check', ['fmt', '--check'])
run('regression-after-fix', ['test', '--offline', '--locked', '-j', '2', '--test', 'archive', 'bundle_rejects_generation_alias'])
run('clippy', ['clippy', '--offline', '--locked', '-j', '2', '--all-targets', '--', '-D', 'warnings'])
run('release-test', ['test', '--release', '--offline', '--locked', '-j', '2'])
run('release-build', ['build', '--release', '--offline', '--locked', '-j', '2', '--bins',
                      '--example', 'group_probe', '--example', 'performance_probe',
                      '--example', 'publication_probe', '--example', 'receipt_seed', '--example', 'scan_profile'])
run('debug-test', ['test', '--offline', '--locked', '-j', '2'])
fault_env = {**env, 'CARGO_TARGET_DIR': str(fault)}
run('fault-clippy', ['clippy', '--offline', '--locked', '-j', '2', '--all-targets', '--features', 'fault-injection', '--', '-D', 'warnings'], fault_env)
run('fault-build', ['build', '--release', '--offline', '--locked', '-j', '2', '--features', 'fault-injection',
                    '--example', 'publication_fault_probe', '--example', 'source_fault_probe'], fault_env)
(w / 'bin').mkdir()
for name in ['kestrel.exe', 'kestrel-stress.exe']:
    shutil.copy2(standard / 'release' / name, w / 'bin' / name)
for source, dest in [('group_probe', 'group-probe'), ('performance_probe', 'performance-probe'),
                     ('publication_probe', 'publication-probe'), ('receipt_seed', 'receipt-seed'), ('scan_profile', 'scan-profile')]:
    shutil.copy2(standard / 'release/examples' / (source + '.exe'), w / 'bin' / (dest + '.exe'))
for name in ['publication_fault_probe.exe', 'source_fault_probe.exe']:
    shutil.copy2(fault / 'release/examples' / name, w / 'bin' / name)
result = subprocess.run(['python', str(w / 'build_adapter.py')], env=env)
assert result.returncode == 0
for p in (w / 'bin').glob('*.exe'):
    if 'fault_probe' not in p.name:
        assert b'KESTREL_FAULT_POINT' not in p.read_bytes(), p
proof = {'trial': '050 unique physical generation hardening, NOT published 0.3.16',
         'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'build_target_reused_after_048_and_049_binaries_frozen': True,
         'source': {p.relative_to(w / 'candidate').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in (w / 'candidate').rglob('*') if p.is_file()},
         'binaries': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (w / 'bin').glob('*.exe')}}
(w / 'build-provenance.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print('All builds, tests and strict checks pass; isolated binary/source provenance frozen', flush=True)
