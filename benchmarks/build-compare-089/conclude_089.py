"""Record trial089 decisions without changing any timed or supported input."""
from pathlib import Path
from datetime import datetime, timezone
import difflib
import hashlib
import json
import shutil

ROOT = Path('D:/Codex/Kestrel')
W = ROOT / 'work/perf-089'
REPO = ROOT / 'outputs/kestrel-sql'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


a = load(W / 'audit.json')
assert (a['cases'], a['offered'], a['successful'], a['lost']) == (216, 2160000, 2160000, 0)
assert (a['identity_failed_total'], a['candidate_failed_total']) == (8, 0)
assert a['correctness_passed'] and not a['all_required_scopes_passed']
assert len(a['scopes']) == 9 and sum(s['passed'] for s in a['scopes']) == 3
assert load(W / 'post-timing-process-check.json')['active_processes'] == []
baseline = load(W / 'unchanged-supported-source.json')
assert all(sha(REPO / n) == v for n, v in baseline.items())
overnight = '1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
assert sha(REPO / 'OVERNIGHT_2026-10-07.md') == overnight
save(W / 'final-source-provenance.json', {'supported': '0.3.16',
    'supported_core_unchanged': True, 'core_source_sha256': baseline,
    'overnight_sha256': overnight, 'no_supported_source_or_package_edit': True,
    'no_remote_publication': True, 'utc': datetime.now(timezone.utc).isoformat()})
save(W / 'decision-summary.json', {'trial': 89, 'correctness_passed': True,
    'qualification_passed': False, 'candidate_failed_total': 0, 'identity_failed_total': 8,
    'identity_criteria': 117, 'candidate_criteria': 117,
    'passed_scopes': 3, 'failed_scopes': 6, 'all_families_unqualified': True,
    'overlapping_scopes_and_read_metrics_not_independent_observations': True,
    'does_not_replace_or_invalidate_088': True, 'supported': '0.3.16',
    'no_speed_gain_tracer_overhead_competitor_or_supported_release_claim': True})
save(W / 'controller-read-missing-path.json', {
    'scope': 'post-timing read-only inspection, not the runner or frozen auditor',
    'requested_path': str(W / 'baseline-to-current-source-comparison.json'),
    'error': 'Get-Content: Cannot find path because it does not exist.',
    'existing_relevant_record': 'source-derivation.json', 'data_changed': False,
    'native_launches': 0, 'timing_reruns': 0})
stock = W / 'sources/stock-016'
diagnostic = W / 'sources/diagnostic-016'
names = sorted({p.relative_to(root).as_posix() for root in (stock, diagnostic)
    for p in root.rglob('*') if p.is_file()})
changes, diffs = [], []
for name in names:
    left, right = stock / name, diagnostic / name
    before = left.read_bytes() if left.exists() else b''
    after = right.read_bytes() if right.exists() else b''
    if before == after:
        continue
    changes.append({'path': name, 'stock_sha256': sha(left) if left.exists() else None,
        'diagnostic_sha256': sha(right) if right.exists() else None})
    diffs.extend(difflib.unified_diff(before.decode('utf-8').splitlines(keepends=True),
        after.decode('utf-8').splitlines(keepends=True),
        fromfile='stock-016/' + name, tofile='diagnostic-016/' + name))
(W / 'stock-to-diagnostic-source.diff').write_text(''.join(diffs), encoding='utf-8', newline='')
save(W / 'stock-to-diagnostic-source.json', {'changed_files': changes,
    'diff_sha256': sha(W / 'stock-to-diagnostic-source.diff'),
    'analysis_only_after_timing': True, 'no_source_change': True,
    'exclusive_causality_not_established': True,
    'next_hypothesis': 'Check unconditional maintenance-result control-flow changes before revising diagnostics; retain original source for feature-disabled execution.'})
for name in ['conclude_089.py', 'preserve_089.py', 'note_active_089.py']:
    target = W / name
    assert not target.exists()
    shutil.copy2(ROOT / 'work' / name, target)
for path in sorted((ROOT / 'work').glob('*089*.log')):
    if path.name.startswith('preserve-089') or path.name == 'conclude-089.log':
        continue
    target = W / path.name
    assert not target.exists()
    assert path.name not in load(W / 'timing-freeze.json')['sha256']
    shutil.copy2(path, target)
print(json.dumps({'correctness': True, 'qualification': False,
    'aa_failures': 8, 'candidate_failures': 0, 'supported_core_unchanged': True}))
