"""Finish the interrupted evidence commit without changing any preserved bytes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess

ROOT = Path('D:/Codex/Kestrel')
WORK = ROOT / 'work'
REPO = ROOT / 'outputs/kestrel-sql'
OUT = REPO / 'benchmarks/reusable-sync-103'
PARENT = '917b941b635344d76c133ce9426f58cf75744817'
WHITESPACE = 'blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol'

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def run(*args, whitespace=False):
    command = ['git', '--no-optional-locks', '-c', 'safe.directory=' + REPO.as_posix(),
               '-c', 'gc.auto=0', '-c', 'maintenance.auto=false']
    if whitespace:
        command += ['-c', 'core.whitespace=' + WHITESPACE]
    command += ['-C', str(REPO), *args]
    return subprocess.run(command, capture_output=True)

def git(*args, whitespace=False):
    result = run(*args, whitespace=whitespace)
    if result.returncode:
        raise RuntimeError((args, result.returncode, result.stdout.decode(errors='replace'),
                            result.stderr.decode(errors='replace')))
    return result.stdout.decode('utf-8')

guard = sorted(WORK.glob('guard-final-103-*.json'))[-1]
state = load(guard)
assert not state['active_processes'] and state['verified_idle_terminal_reset']
assert git('rev-parse', 'HEAD').strip() == PARENT
assert not git('diff', '--name-only')
closed = OUT / 'closed-continuation'
closed_proof = load(closed / 'closed-log-proof.json')
for name, digest in closed_proof['files'].items():
    assert sha(closed / name) == digest, name
for name in ['README.md', 'BENCHMARK_HISTORY.md']:
    before = (closed / (name + '.before-103')).read_bytes()
    first = before.index(b'\n') + 1
    assert before[first:] in (REPO / name).read_bytes()
preserved = load(OUT / 'preservation-proof.json')
restored = load(OUT / 'restored-audit-proof.json')
assert preserved['complete'] and restored['passed']
assert restored['replay_equals_original_complete_audit']

failed = closed / 'failed-recording-v1'
assert not failed.exists()
failed.mkdir()
for name in ['commit_103.py', 'commit-103.log']:
    shutil.copy2(WORK / name, failed / name)
recheck = run('diff', '--cached', '--check')
assert recheck.returncode != 0
(failed / 'exact-default-whitespace-recheck.stdout').write_bytes(recheck.stdout)
(failed / 'exact-default-whitespace-recheck.stderr').write_bytes(recheck.stderr)
fixed = run('diff', '--cached', '--check', whitespace=True)
assert fixed.returncode == 0, (fixed.returncode, fixed.stdout, fixed.stderr)
(failed / 'windows-line-ending-check.stdout').write_bytes(fixed.stdout)
(failed / 'windows-line-ending-check.stderr').write_bytes(fixed.stderr)
proof = {
    'utc': datetime.now(timezone.utc).isoformat(),
    'original_recording_actual_exit_code': 1,
    'no_commit_created_by_first_attempt': True,
    'default_check_repeat_returncode': recheck.returncode,
    'fixed_check_returncode': fixed.returncode,
    'only_check_configuration_change': 'Recognize CR as the Windows CRLF line ending.',
    'core_whitespace': WHITESPACE,
    'all_default_blank_at_eol_blank_at_eof_space_before_tab_checks_still_enabled': True,
    'no_content_normalization_no_raw_or_source_edit_no_path_exclusion': True,
    'files': {p.name: sha(p) for p in failed.iterdir() if p.is_file()},
}
(failed / 'failure-and-recheck-proof.json').write_text(
    json.dumps(proof, indent=2) + '\n', encoding='utf-8', newline='\n')
shutil.copy2(guard, closed / guard.name)
shutil.copy2(Path(__file__), closed / Path(__file__).name)
git('add', '--', 'README.md', 'BENCHMARK_HISTORY.md', 'REUSABLE_SYNC_103.md',
    'benchmarks/reusable-sync-103')
names = git('diff', '--cached', '--name-only').splitlines()
assert all(name in ['README.md', 'BENCHMARK_HISTORY.md', 'REUSABLE_SYNC_103.md']
           or name.startswith('benchmarks/reusable-sync-103/') for name in names)
git('diff', '--cached', '--check', whitespace=True)
print(git('commit', '-m',
          'Qualify reusable sync103 correctness and preserve complete restored recovery evidence'),
      flush=True)
head = git('rev-parse', 'HEAD').strip()
assert not git('status', '--porcelain')
assert not git('diff', '--name-only', PARENT, head, '--', 'src', 'tests', 'examples',
               'Cargo.toml', 'Cargo.lock', 'verification.json', 'OVERNIGHT_2026-10-07.md')
result = {
    'utc': datetime.now(timezone.utc).isoformat(), 'complete': True,
    'parent': PARENT, 'head': head, 'staged_files': len(names), 'repository_clean': True,
    'supported_source_tests_examples_Cargo_verification_and_overnight_byte_exact': True,
    'performance_or_adoption_not_qualified': True,
    'no_remote_upload_or_raw_deletion': True,
    'first_recording_failure_fully_retained': True,
    'full_whitespace_check_with_Windows_CRLF_recognized_passed': True,
}
destination = WORK / 'commit-103-proof.json'
assert not destination.exists()
destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(result), flush=True)
