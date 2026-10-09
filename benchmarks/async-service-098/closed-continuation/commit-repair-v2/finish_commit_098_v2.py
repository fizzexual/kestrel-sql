"""Resume only the failed evidence commit; preserve frozen EOF bytes and the failure."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess

ROOT = Path('D:/Codex/Kestrel')
WORK = ROOT / 'work'
R = ROOT / 'outputs/kestrel-sql'
W = WORK / 'perf-098'
RESTORE = WORK / 'restored-async-service-098'
O = R / 'benchmarks/async-service-098'
PARENT = 'b4e7cf9f8d2105c96ae07c57540d6a33f4d17018'
PATHS = ['ASYNC_SERVICE_098.md', 'README.md', 'BENCHMARK_HISTORY.md', 'RELEASE_TARGET_0_3_17.md', 'benchmarks/async-service-098']
EXCEPTIONS = ['benchmarks/async-service-098/audit_service_095.py', 'benchmarks/async-service-098/outcomes_098.py']
WHITESPACE = 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(p, data):
    assert not p.exists(), p
    p.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8', newline='\n')


def command(*args):
    return subprocess.run(['git', '--no-optional-locks', '-c', f'safe.directory={R.as_posix()}', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '-C', str(R), *args], capture_output=True)


def git(*args, binary=False):
    p = command(*args)
    assert p.returncode == 0, (args, p.stdout[-2000:], p.stderr[-2000:])
    return p.stdout if binary else p.stdout.decode().strip()


guard_path = sorted(WORK.glob('guard-precommit-098-*.json'))[-1]
guard = read(guard_path)
assert not guard['active_processes'] and guard['reset_phase'] == 'waiting-for-full-codex-exit'
assert git('rev-parse', 'HEAD') == PARENT
assert git('diff', '--quiet') == ''
staged = git('diff', '--cached', '--name-only').splitlines()
expected = set(PATHS[:4]) | {p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file()}
assert set(staged) == expected and len(staged) == len(expected)
previous = read(O / 'closed-continuation/proof.json')
core = previous['supported_core']
for name, digest in core.items():
    assert sha(R / name) == digest == hashlib.sha256(git('show', PARENT + ':' + name, binary=True)).hexdigest()
for name, digest in previous['navigation_prior_sha256'].items():
    old = git('show', PARENT + ':' + name, binary=True)
    assert hashlib.sha256(old).hexdigest() == digest and (R / name).read_bytes().startswith(old)

failure = command('-c', WHITESPACE, 'diff', '--cached', '--check', '--', *PATHS)
expected_errors = {f'{name}:{line}: new blank line at EOF.' for name, line in zip(EXCEPTIONS, [188, 41])}
assert failure.returncode == 2 and not failure.stderr
assert set(failure.stdout.decode().splitlines()) == expected_errors
backup = WORK / 'failed-commit-098-v1'
supplement = O / 'closed-continuation/commit-repair-v2'
assert not backup.exists() and not supplement.exists() and not (WORK / 'commit-098-proof.json').exists()
backup.mkdir()
for name in PATHS[:4]:
    shutil.copy2(R / name, backup / name)
for p in [WORK / 'commit_098.py', WORK / 'commit-098.log', O / 'closed-continuation/proof.json']:
    shutil.copy2(p, backup / p.name)
(backup / 'whitespace-check.stdout').write_bytes(failure.stdout)
(backup / 'initial-stage-objects.txt').write_bytes(git('ls-files', '--stage', '--', *PATHS, binary=True))
index = Path(git('rev-parse', '--git-path', 'index'))
if not index.is_absolute():
    index = R / index
shutil.copy2(index, backup / 'initial-index.bin')
save(backup / 'failure-preservation.json', {
    'utc': datetime.now(timezone.utc).isoformat(),
    'parent_head_unchanged': PARENT,
    'no_commit_created_by_failed_attempt': True,
    'failure': 'Only two frozen evidence scripts contain their existing terminal empty line',
    'staged_paths': staged,
    'files': {p.name: sha(p) for p in backup.iterdir() if p.is_file()},
    'supported_core': core,
    'no_original_raw_byte_modified': True,
})

exception_hashes = {}
for name in EXCEPTIONS:
    basename = Path(name).name
    digest = sha(R / name)
    assert digest == sha(W / basename) == sha(RESTORE / basename)
    assert (R / name).read_bytes().endswith(b'\n\n')
    exception_hashes[name] = digest
preserved = read(O / 'preservation-proof.json')
replayed = read(O / 'restored-audit-proof.json')
assert preserved['complete'] and replayed['passed']
assert replayed['native_launches'] == replayed['performance_timer_launches'] == 0
for part in preserved['parts']:
    assert sha(O / part['name']) == part['sha256']
audit = read(W / 'audit.json')
assert audit['lost'] == 0 and audit['identity_failed_total'] == audit['goals_failed'] == 1
assert audit['candidate_failed_total'] == 0 and not audit['scoped_candidate_qualified']

report = R / 'ASYNC_SERVICE_098.md'
report.write_bytes(report.read_bytes() + b'\nThe first local evidence-commit attempt stopped at the whitespace check: two frozen copied scripts retain an existing terminal empty line. That attempt created no commit. Its helper, closed log, report/navigation bytes and staged index/object identities are preserved in `closed-continuation/commit-repair-v2`. The final check covers every other staged path, with explicit SHA-verified exceptions only for `audit_service_095.py` and `outcomes_098.py`; neither frozen script was normalized or changed. This has no effect on the numerical rejection or release gates.\n')
shutil.copytree(backup, supplement)
shutil.copy2(Path(__file__), supplement / Path(__file__).name)
shutil.copy2(guard_path, supplement / guard_path.name)
save(supplement / 'repair-proof.json', {
    'utc': datetime.now(timezone.utc).isoformat(),
    'only_frozen_evidence_EOF_whitespace_exceptions': exception_hashes,
    'all_exceptions_equal_original_and_restored_bytes': True,
    'preserved_prior_failed_commit_attempt': str(backup),
    'files': {p.name: sha(p) for p in supplement.iterdir() if p.is_file()},
    'no_source_policy_timing_raw_or_threshold_change': True,
})
git('add', '--', *PATHS)
git('-c', WHITESPACE, 'diff', '--cached', '--check', '--', *PATHS, *[':(exclude)' + n for n in EXCEPTIONS])
assert all(sha(R / n) == h for n, h in exception_hashes.items())
git('commit', '-m', 'Preserve normal async service 098 rejection and complete graceful evidence')
head = git('rev-parse', 'HEAD')
assert git('merge-base', '--is-ancestor', PARENT, head) == '' and git('status', '--porcelain') == ''
assert all(sha(R / n) == h for n, h in core.items())
save(WORK / 'commit-098-proof.json', {
    'complete': True, 'clean': True, 'head': head, 'parent': PARENT,
    'supported_core': core, 'navigation_prior_sha256': previous['navigation_prior_sha256'],
    'private_only': True, 'remote_not_modified': True, 'trial_unqualified_not_adopted': True,
    'initial_commit_check_failure_preserved': True,
    'only_two_frozen_SHA_verified_EOF_exceptions': exception_hashes,
})
print(json.dumps({'private_commit': head, 'clean': True, 'supported_core_byte_exact': True,
                  'trial098_unqualified_no_adoption': True, 'failed_commit_attempt_preserved': True}))
