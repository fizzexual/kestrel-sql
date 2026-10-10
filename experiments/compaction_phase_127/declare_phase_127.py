"""Declare the measured ordered-path repair and correctness prerequisites."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess
ROOT = Path('D:/Codex/Kestrel')
WORK = ROOT / 'work/perf-127'
REPO = ROOT / 'outputs/kestrel-sql'
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
assert load(ROOT / 'work/kernel126-storage-cleanup-proof.json')['completed126_stores_closed']
assert not WORK.exists()
git = ['git', '--no-optional-locks', '-c', 'safe.directory=' + REPO.as_posix(), '-C', str(REPO)]
assert not subprocess.check_output(git + ['status', '--porcelain=v1', '--untracked-files=all']).strip()
head = subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip()
assert head == load(ROOT / 'work/kernel126-publication-proof.json')['private_main']
core = load(ROOT / 'work/compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(REPO / name) == digest for name, digest in core.items())
policy = {'trial': 127, 'declared_utc': datetime.now(timezone.utc).isoformat(), 'source_commit': head,
          'kind': 'Isolated actual Archive code repair and correctness prerequisites; no timed cohort declared',
          'hypothesis': '126 shows controlled clustered kernel gains but ordered full-wall +12.27% and second-half cycle +15.04% regressions. Candidate122 resamples run boundaries after concatenation. Track concatenation ordering from CRC-validated first-block values while actually reading/collecting the input; bypass merge planning when already ordered. All of this remains inside compact_small preparation. This may remove ordered planning work; no speedup is presumed.',
          'phases': 'Already ordered: bypass merge planning. Unordered chunked: unchanged122 bounded merge. Fragmented/small/zero-progress: unchanged original-sort fallback. Final publish sortedness check and every CRC/read/index/sync/receipt/ACK operation unchanged.',
          'supported_core_sha256': core, 'candidate_module_sha256': sha(REPO / 'experiments/compaction_merge_122/merge_runs_122.rs'),
          'no_new_public_API_format_dependencies_unsafe_or_deferred_work': True,
          'prerequisites': 'Four actual candidate library/test suites: debug/release with and without fault-injection; two strict clippy runs; common durable driver release build. Reuse baseline154 tests and binary explicitly. Existing122 module4 and actualArchive2 integration tests retained. Add one ordered signed-boundary/duplicate-boundary receipt/pin/CRC/cold-reopen integration test. Expected84 tests per suite,336 fresh total, pending actual exits.',
          'all_timed_cases_unstarted': True, 'declared_timed_cases': 0,
          'performance_acceptance': 'Before adoption require a fresh new-number balanced comparison with full/both-half identity controls, clustered gains reproduced, no ordered or other material regression, and all original whole-engine release gates. No kernel-boundary change or batch/cycle measurements replace whole-engine timing.',
          'original_release_gates_unchanged': {'Native': 324, 'service': 252, 'goals': 42, 'AA': 153, 'guards': 171},
          'local_regenerable_build_cap_bytes': 2_500_000_000,
          'retention': 'Concise outcomes/failures/useful source privately saved, freshly verified, then scoped regenerable output cleanup. No raw bundle.',
          'release017_qualified': False}
WORK.mkdir()
(WORK / 'policy.json').write_text(json.dumps(policy, indent=2) + '\n', encoding='utf-8')
(WORK / 'declaration-proof.json').write_text(json.dumps({'complete': True, 'policy_sha256': sha(WORK / 'policy.json'), 'before_candidate_source_implementation': True, 'timed_cases_declared': 0}, indent=2) + '\n', encoding='utf-8')
print('Declared isolated Archive ordered-phase repair127; no timed cases declared.')
