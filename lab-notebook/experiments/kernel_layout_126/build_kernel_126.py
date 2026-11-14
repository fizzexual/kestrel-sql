"""Serial diagnostic-only builds/tests/smokes; no cohort timer starts here."""
from pathlib import Path
from datetime import datetime, timezone
from ctypes import wintypes
import ctypes, hashlib, json, os, re, shutil, subprocess, traceback

ROOT = Path('D:/Codex/Kestrel')
WORK = ROOT / 'work/perf-126'
REPO = ROOT / 'outputs/kestrel-sql'
RUSTC = 'C:/Users/Frizer/.cargo/bin/rustc.exe'
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def save(name, data):
    with (WORK / name).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(data, indent=2) + '\n')
def utc():
    return datetime.now(timezone.utc).isoformat()
policy = load(WORK / 'policy.json')
assert sha(WORK / 'policy.json') == load(WORK / 'declaration-proof.json')['policy_sha256']
assert not (WORK / 'build-proof.json').exists()
assert all(sha(REPO / name) == digest for name, digest in policy['supported_source_sha256'].items())
module = REPO / 'experiments/compaction_merge_122/merge_runs_122.rs'
assert sha(module) == policy['candidate_module_sha256']
save('build-declaration.json', {'utc': utc(), 'serial': True, 'new_driver_only': True, 'candidate122_module_exact': True,
                              'jobs': ['debug-test-build', 'debug-tests', 'release-test-build', 'release-tests', 'optimized-driver', 'two-excluded-smokes'], 'no_cohort_timing': True})
for source in [ROOT / 'work/kernel_layout_126.rs', module]:
    shutil.copy2(source, WORK / 'source' / source.name)
save('source-proof.json', {path.name: sha(path) for path in (WORK / 'source').iterdir()})
environment = os.environ | {'TMP': str(WORK / 'tmp'), 'TEMP': str(WORK / 'tmp')}
assert not any(key.startswith(('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'KESTREL_FAULT')) for key in environment)
records = []
try:
    for label, options, output in [
        ('debug-test-build', ['--test', '-C', 'debuginfo=0'], 'kernel-tests-debug.exe'),
        ('release-test-build', ['--test', '-C', 'opt-level=3'], 'kernel-tests-release.exe'),
        ('optimized-driver', ['-C', 'opt-level=3', '-C', 'codegen-units=1'], 'kernel-layout-126.exe'),
    ]:
        command = [RUSTC, '--edition=2024', '-Dwarnings', str(WORK / 'source/kernel_layout_126.rs'), *options, '-o', str(WORK / 'binary' / output)]
        print('START ' + label, flush=True)
        result = subprocess.run(command, capture_output=True, env=environment, timeout=180, creationflags=0x08000000)
        (WORK / 'logs' / (label + '.log')).write_bytes(result.stdout + result.stderr)
        records.append({'label': label, 'actual_exit': result.returncode, 'argv': command})
        assert result.returncode == 0, (label, result.stderr[-4000:])
        if '--test' in options:
            result = subprocess.run([str(WORK / 'binary' / output), '--test-threads=1'], capture_output=True, env=environment, timeout=180, creationflags=0x08000000)
            (WORK / 'logs' / (label + '-execution.log')).write_bytes(result.stdout + result.stderr)
            count = sum(map(int, re.findall(rb'test result: ok\. (\d+) passed;', result.stdout)))
            records.append({'label': label + '-execution', 'actual_exit': result.returncode, 'fresh_kernel_tests': count})
            assert result.returncode == 0 and count == 5, (label, result.stdout[-3000:], result.stderr[-3000:])
            print(json.dumps({'passed': label, 'fresh_kernel_tests': count}), flush=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
    kernel.GetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
    own = kernel.GetCurrentProcess()
    previous = ctypes.c_size_t(); system = ctypes.c_size_t()
    assert kernel.GetProcessAffinityMask(own, ctypes.byref(previous), ctypes.byref(system)) and previous.value & 256
    smokes = []
    try:
        assert kernel.SetProcessAffinityMask(own, 256)
        for variant in ['baseline', 'candidate']:
            child = subprocess.Popen([str(WORK / 'binary/kernel-layout-126.exe'), 'clustered', '5', variant], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment, creationflags=0x08000000)
            mask = ctypes.c_size_t(); system_mask = ctypes.c_size_t()
            assert kernel.GetProcessAffinityMask(int(child._handle), ctypes.byref(mask), ctypes.byref(system_mask)) and mask.value == 256
            output, errors = child.communicate(timeout=90)
            (WORK / 'logs' / ('excluded-smoke-' + variant + '.stdout')).write_bytes(output)
            (WORK / 'logs' / ('excluded-smoke-' + variant + '.stderr')).write_bytes(errors)
            result = json.loads(output)
            assert child.returncode == 0 and result['all_checks_passed'] and result['full_native_multiset_checks'] == 32
            assert result['candidate'] == (variant == 'candidate') and result['rows_per_iteration'] == 32768
            assert result['arranged_iterations'] == (32 if variant == 'candidate' else 0)
            smokes.append({'variant': variant, 'actual_exit': child.returncode, 'affinity': mask.value, 'excluded_from648': True, 'fingerprint': result['canonical_fingerprint']})
        assert smokes[0]['fingerprint'] == smokes[1]['fingerprint']
    finally:
        assert kernel.SetProcessAffinityMask(own, previous.value)
    assert all(sha(WORK / 'source' / name) == digest for name, digest in load(WORK / 'source-proof.json').items())
    assert sum(path.stat().st_size for path in WORK.rglob('*') if path.is_file()) < policy['local_resource_bound_bytes']
    proof = {'complete': True, 'utc': utc(), 'records': records, 'fresh_kernel_tests': 10, 'fresh_Archive_tests': 0,
             'candidate122_332_library_tests_reused_not_fresh': True, 'strict_rustc_warning_checks': 3,
             'excluded_smokes': smokes, 'binary_sha256': sha(WORK / 'binary/kernel-layout-126.exe'),
             'all_sources_exact': True, 'no_cohort_timing_started': True, 'release017_qualified': False}
    save('build-proof.json', proof)
    print(json.dumps({key: value for key, value in proof.items() if key not in ['records', 'excluded_smokes']}), flush=True)
except BaseException:
    save('build-failure.json', {'utc': utc(), 'records': records, 'error': traceback.format_exc(), 'all648_cohort_cases_unstarted': True})
    raise
