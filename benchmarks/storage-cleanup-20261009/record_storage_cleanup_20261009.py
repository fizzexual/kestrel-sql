"""Record completed conditional GitHub-backed local cleanup; no deletions."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/Codex/Kestrel')
REPO = ROOT / 'outputs/kestrel-sql'
WORK = ROOT / 'work'
EVIDENCE = WORK / 'storage-cleanup-20261009-0841'
OUT = REPO / 'benchmarks/storage-cleanup-20261009'
NEXT = Path('D:/Codex/KESTREL_NEXT.md')
BEFORE_HEAD = '83c8e0743c122bdf4ec66b39234d806de410f516'


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def save(p, value):
    assert not p.exists(), p
    p.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def git(*args):
    p = subprocess.run(['git', '--no-optional-locks', '-c', 'safe.directory=' + REPO.as_posix(),
                        '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '-C', str(REPO), *args],
                       capture_output=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
    return p.stdout


def append(p, text):
    before = p.read_bytes()
    addition = text.replace('\n', '\r\n').encode('utf-8')
    p.write_bytes(before + addition)
    assert p.read_bytes()[:len(before)] == before


result = load(EVIDENCE / 'cleanup-result.json')
plan = load(EVIDENCE / 'verified-deletion-plan.json')
assert result['complete'] and plan['complete']
assert result['files'] == plan['files'] == len(result['deleted'])
assert result['logical_bytes_removed'] == plan['bytes']
assert not plan['failed_retained']
assert {x['path'].replace('\\', '/').lower() for x in result['deleted']} == {
    x['path'].replace('\\', '/').lower() for x in plan['entries']}
assert all(not Path(x['path']).exists() for x in plan['entries'])
assert all(Path(x['path']).is_file() for x in plan['selection_retained'])
assert (ROOT / 'outputs/kestrel-sql-0.3.16.zip').is_file()
assert (ROOT / 'outputs/kestrel-sql-0.3.16-service-047-evidence.zip').is_file()
assert (ROOT / 'outputs/kestrel-sql-development-061-clean-core-evidence.zip').is_file()
assert git('rev-parse', 'HEAD').decode().strip() == BEFORE_HEAD
assert git('status', '--porcelain') == b''
assert not OUT.exists()
OUT.mkdir()
for p in sorted(EVIDENCE.iterdir()):
    assert p.is_file() and not p.is_symlink() and not p.is_junction(), p
    shutil.copy2(p, OUT / p.name)
for name in ('verify_github_cleanup_20261009.py', 'cleanup_archives_20261009.ps1',
             'record_storage_cleanup_20261009.py', 'verify-github-cleanup-20261009.log',
             'cleanup-archives-20261009.log'):
    shutil.copy2(WORK / name, OUT / name)
save(OUT / 'initial-guard-denial.json', {
    'phase': 'read-only preprepare process check in default sandbox',
    'exit_code': 1, 'error': 'Get-CimInstance: Access denied',
    'no_deletion_or_mutation_in_failed_guard': True,
    'resolved_by_approved_same_scope_process_check': True,
    'automatic_approval_review_rejection': False,
})
size = result['logical_bytes_removed']
gib = size / 1024**3
delta = result['D_free_after_bytes'] - result['D_free_before_bytes']
report = f'''# Conditional GitHub-backed local storage cleanup — October 9, 2026

Removed {result['files']} redundant ZIP files immediately inside `D:\\Codex\\Kestrel\\outputs`, totaling **{size:,} logical bytes ({gib:.2f} GiB)**. D: free-space change measured during deletion was {delta:,} bytes; that filesystem reading can include unrelated activity. No directory or tracked repository file was deleted. This is storage cleanup, not a benchmark, release or speed improvement.

The user's new instruction allows removing unusable/redundant local things, including benchmark material, once they are on GitHub. This overrides earlier requirements to retain every redundant physical local copy. Benchmark failures remain evidence and retain a recoverable copy; a report or source commit alone never proves that raw stores, policies, binaries and failed attempts are backed up.

## What was verified before deletion

The existing repository `fizzexual/kestrel-sql` was authenticated and private. For every removed file, its exact name, size and full local SHA-256 matched the uploaded GitHub release asset and local checksum sidecar. Every remote asset was then downloaded completely into a streaming SHA-256 and byte count. Every complete remote hash/size matched the local file and GitHub digest. Downloads were not saved as another local duplicate. The native PowerShell cleanup rehashed every local file and refreshed every asset's GitHub metadata before any deletion, checked exact canonical real paths and task/reset exclusion, and used only `Remove-Item -LiteralPath` on individual top-level files, without recursion. Per-file deletion receipts are retained.

The verification had no failed asset checks. The first read-only CIM guard needed the already-authorized filesystem/process escalation; it was rerun successfully before work and is recorded. No automatic approval review rejected the action.

## Recovery and retained local work

The exact recovery URLs, asset IDs, SHA-256 values, byte counts, complete download results and deletion receipts are in [the deletion plan](benchmarks/storage-cleanup-20261009/verified-deletion-plan.json) and [the completed result](benchmarks/storage-cleanup-20261009/cleanup-result.json). Download an asset from its recorded private GitHub URL, verify its recorded SHA-256 and size, and restore it to the recorded path when historical tooling needs that package. This restores the original ZIP bytes. Assets span existing releases from [v0.1.0](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.1.0) through [v0.3.16](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.16); no release, tag or remote asset was edited or removed.

The supported 0.3.16 package and service evidence, trial 061 archive for planned integration, every original raw benchmark/failed-experiment store, local Git history, sources, policies, binaries and reports remain local. All unmatched ZIPs remain, including failed first packaging and later evidence parts whose exact backups are absent. See [the complete retained/selected list](benchmarks/storage-cleanup-20261009/selection.json).

At verification, GitHub main was `{plan['remote_main_sha']}` and local main was `{BEFORE_HEAD}`. The 17 newer local commits and experiments 080–100 were not yet present on GitHub main and were retained completely. This operation performs no upload, branch change, force-push, remote visibility change, reset, app shutdown or benchmark timing. The current release is still 0.3.16 and 0.3.17 remains unqualified.

## Standing cleanup rule

Continue removing obsolete copies/caches and inactive benchmark material when their complete required contents have a verified recoverable private GitHub backup and they are not needed by current work. Record exact paths, coverage, hashes, recovery URLs and actual deletion results. For raw experiment/store removal, first establish full archive coverage and restoration/reference audit for all raw results and failed attempts; never infer coverage from a report or archive filename. Retain active sources, current release artifacts and current experiment prerequisites locally. Verify task jobs and reset state before cleanup; serialize it against all timed workloads. Leave unbacked-up or ambiguous files intact.
'''
report_path = REPO / 'STORAGE_CLEANUP_20261009.md'
assert not report_path.exists()
report_path.write_text(report, encoding='utf-8', newline='\n')
append(REPO / 'BENCHMARK_HISTORY.md', '\n\n## October 9, 2026 — verified local storage cleanup\n\n'
       f'[Storage cleanup](STORAGE_CLEANUP_20261009.md) removes {result["files"]} redundant top-level ZIP copies ({gib:.2f} GiB) only after full private GitHub download/hash verification. Every original benchmark failure/raw store and all newer unbacked-up experiments remain. No performance result or release status changes.\n')
save(OUT / 'record-inventory.json', {
    'sha256': {p.relative_to(OUT).as_posix(): sha(p) for p in sorted(OUT.iterdir()) if p.is_file()},
    'report_sha256': sha(report_path), 'supported_source_untouched': True,
})
git('-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol', 'diff', '--check')
git('add', '--', 'STORAGE_CLEANUP_20261009.md', 'BENCHMARK_HISTORY.md', 'benchmarks/storage-cleanup-20261009')
git('-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol', 'diff', '--cached', '--check')
git('commit', '-m', 'Record verified GitHub-backed redundant archive cleanup')
head = git('rev-parse', 'HEAD').decode().strip()
assert git('status', '--porcelain') == b''
before = NEXT.read_bytes()
backup = WORK / 'KESTREL_NEXT-before-storage-cleanup-20261009.md'
assert not backup.exists()
backup.write_bytes(before)
note = f'''

## User-authorized conditional GitHub cleanup completed ({datetime.now(timezone.utc).isoformat()})

LATEST USER INSTRUCTION: "Also any not usable things(benchmark too) delete them when we have them in github". This supersedes older requirements to retain every redundant local physical copy. Preserve recoverable project/release/benchmark history and every failed result; only remove inactive/redundant local material after full required contents are verified on the existing private GitHub repository. A report/source commit is not proof that raw fixtures/policies/binaries/failures are remotely backed up. For future raw-store removal verify exact archive coverage and complete restored/reference audit, record hashes/URLs/path/deletion receipts, and keep current code/release/prerequisites local. Do not erase failures because they failed. Do not alter GitHub releases/history/visibility or force-push.

Cleanup completed: {result['files']} redundant individual top-level ZIP files from D:\\Codex\\Kestrel\\outputs, {size} logical bytes ({gib:.2f} GiB). For every file: private repository, unique existing published asset, exact local/sidecar/remote digest/size and COMPLETE streaming GitHub download SHA/size all verified. A second native PowerShell full local hash + refreshed metadata/real-path/live-job/reset validation preceded individual LiteralPath deletion, with zero recursive operations. All original raw/failed stores, local Git history and repository files retained. Supported 0.3.16 package/service archive and planned-integration 061 archive stay local, as do all unmatched/failed-first/newer ZIPs. GitHub main was {plan['remote_main_sha']}; 17 newer local commits/080–100 experiments were not there, so none was deleted. No upload/release/speed change/reset/app force-quit occurred.

Private local main is now {head}; repository clean. Report: D:\\Codex\\Kestrel\\outputs\\kestrel-sql\\STORAGE_CLEANUP_20261009.md. Exact recovery URLs/hashes/counts/deletion receipts/download/stdout/helper evidence: repository benchmarks/storage-cleanup-20261009 and original work/storage-cleanup-20261009-0841. C duplicate cleanup was already complete and not repeated. The independently armed reset remains waiting and no task-owned timed work overlapped cleanup.

Return to the previously stated new >=101 scoped synchronization-overlap code hypothesis and fresh correctness/recovery/fair performance gates; no 101 code was declared/implemented/timed by this cleanup. 0.3.16 stays supported, .17 unqualified without an ETA. Check live jobs/reset first, serialize benchmarks against cleanup/hash/copy/build/package/Git, keep work private/on this computer, and remain quiet on unchanged/non-actionable state.
'''
NEXT.write_bytes(before + note.replace('\n', '\r\n').encode('utf-8'))
assert NEXT.read_bytes()[:len(before)] == before
save(WORK / 'next-storage-cleanup-20261009-proof.json', {
    'previous_sha256': hashlib.sha256(before).hexdigest(), 'new_sha256': sha(NEXT),
    'all_prior_bytes_preserved': True, 'backup': str(backup), 'head': head,
    'removed_files': result['files'], 'removed_logical_bytes': size,
})
print(json.dumps({'head': head, 'repository_clean': True, 'removed_files': result['files'],
                  'removed_logical_bytes': size, 'GiB': gib, 'D_free_delta_bytes': delta,
                  'report': str(report_path), 'next_sha256': sha(NEXT)}), flush=True)
