"""One predeclared memory-kernel cohort; no filesystem/database fixture work."""
from pathlib import Path
from datetime import datetime, timezone
from ctypes import wintypes
import ctypes, hashlib, json, os, subprocess, time, traceback

ROOT = Path('D:/Codex/Kestrel/work')
WORK = ROOT / 'perf-126'
def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
def utc():
    return datetime.now(timezone.utc).isoformat()
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.GetCurrentProcess.restype = wintypes.HANDLE
kernel.GetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
kernel.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
def mask(handle):
    process = ctypes.c_size_t(); system = ctypes.c_size_t()
    assert kernel.GetProcessAffinityMask(handle, ctypes.byref(process), ctypes.byref(system))
    return process.value, system.value
def identity(child):
    times = [wintypes.FILETIME() for _ in range(4)]
    assert kernel.GetProcessTimes(int(child._handle), *(ctypes.byref(item) for item in times))
    return {'pid': child.pid, 'creation_filetime': times[0].dwLowDateTime + (times[0].dwHighDateTime << 32),
            'owned_Popen_handle': True, 'affinity_mask': mask(int(child._handle))[0]}

policy = load(WORK / 'policy.json')
assert sha(WORK / 'policy.json') == load(WORK / 'declaration-proof.json')['policy_sha256']
build = load(WORK / 'build-proof.json')
assert build['complete'] and build['fresh_kernel_tests'] == 10
task_guard = load(sorted(ROOT.glob('guard-cleanup-pretime-*.json'))[-1])
assert task_guard['verified_idle_terminal_reset'] and not task_guard['active_processes']
global_guard = load(sorted(ROOT.glob('global-build-preflight-*.json'))[-1])
assert global_guard['no_visible_build_jobs'] and not global_guard['visible_build_jobs']
assert (datetime.now(timezone.utc) - datetime.fromisoformat(global_guard['utc'])).total_seconds() < 60
assert not (WORK / 'component-cases.jsonl').exists() and not (WORK / 'freeze.json').exists()
assert sha(WORK / 'binary/kernel-layout-126.exe') == build['binary_sha256']
assert all(sha(WORK / 'source' / name) == digest for name, digest in load(WORK / 'source-proof.json').items())
assert sum(path.stat().st_size for path in WORK.rglob('*') if path.is_file()) < policy['local_resource_bound_bytes'] - 5_000_000
frozen = {name: sha(WORK / name) for name in ['policy.json', 'binary/kernel-layout-126.exe', 'source/kernel_layout_126.rs', 'source/merge_runs_122.rs']}
(WORK / 'freeze.json').write_text(json.dumps({'utc': utc(), 'files': frozen,
                                             'controller_sha256': sha(Path(__file__)),
                                             'auditor_sha256': sha(ROOT / 'audit_kernel_126.py')}, indent=2) + '\n', encoding='utf-8')
environment = os.environ | {'TMP': str(WORK / 'tmp'), 'TEMP': str(WORK / 'tmp')}
assert not any(name.startswith(('KESTREL_FAULT', 'KESTREL_LIVE_PAUSE', 'KESTREL_ASYNC', 'KESTREL_COUPLE')) for name in environment)
own = kernel.GetCurrentProcess()
original, system = mask(own)
assert original & 256 and system & 256
completed = []
try:
    assert kernel.SetProcessAffinityMask(own, 256) and mask(own)[0] == 256
    started = time.monotonic()
    cooldown = {'started_utc': utc(), 'required_seconds': 120, 'controller_original_affinity': original}
    print('COOLDOWN_START 120 seconds; kernel diagnostic only', flush=True)
    time.sleep(120)
    cooldown |= {'completed_utc': utc(), 'actual_seconds': time.monotonic() - started}
    assert cooldown['actual_seconds'] >= 120
    (WORK / 'cooldown-proof.json').write_text(json.dumps(cooldown, indent=2) + '\n', encoding='utf-8')
    for spec in policy['cases']:
        label = f"{spec['index']:03d}-r{spec['round']:02d}-{spec['name']}-{spec['variant']}"
        variant = 'candidate' if spec['variant'] == 'candidate_122' else 'baseline'
        argv = [str(WORK / 'binary/kernel-layout-126.exe'), spec['name'], str(spec['seed']), variant]
        record = spec | {'argv': argv, 'started_utc': utc()}
        child = subprocess.Popen(argv, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=0x08000000)
        record['identity'] = identity(child)
        try:
            output, errors = child.communicate(timeout=90)
        except subprocess.TimeoutExpired:
            child.kill(); output, errors = child.communicate(timeout=10)
            record['timeout'] = True
        for suffix, data in [('stdout', output), ('stderr', errors)]:
            path = WORK / 'raw' / (label + '.' + suffix)
            path.write_bytes(data)
            record[suffix] = path.relative_to(WORK).as_posix()
        record |= {'actual_exit': child.returncode, 'actual_wait_completed': True, 'completed_utc': utc()}
        with (WORK / 'component-cases.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(record, separators=(',', ':')) + '\n')
        assert child.returncode == 0 and record['identity']['affinity_mask'] == 256 and not record.get('timeout'), (record, errors[-2000:])
        result = json.loads(output)
        assert result['all_checks_passed'] and result['diagnostic_only'] and result['iterations'] == 32
        assert result['seed'] == spec['seed'] and result['workload'] == spec['name'] and result['candidate'] == (variant == 'candidate')
        completed.append(record)
        if len(completed) % 54 == 0:
            print(json.dumps({'completed': len(completed), 'total': 648}), flush=True)
    assert all(sha(WORK / name) == digest for name, digest in frozen.items())
    assert sum(path.stat().st_size for path in WORK.rglob('*') if path.is_file()) < policy['local_resource_bound_bytes']
    (WORK / 'cohort-completion.json').write_text(json.dumps({'complete': True, 'utc': utc(), 'cases': len(completed), 'all_actual_child_exits_zero': True,
                                                         'all_fixed_affinities_verified': True, 'all_frozen_files_unchanged': True, 'no_durable_DB_or_SQL_timer': True}, indent=2) + '\n', encoding='utf-8')
except BaseException:
    (WORK / 'cohort-failure.json').write_text(json.dumps({'utc': utc(), 'completed': len(completed), 'error': traceback.format_exc(),
                                                      'unstarted_indices': [case['index'] for case in policy['cases'][len(completed):]], 'no_selected_retiming': True}, indent=2) + '\n', encoding='utf-8')
    raise
finally:
    assert kernel.SetProcessAffinityMask(own, original) and mask(own)[0] == original
