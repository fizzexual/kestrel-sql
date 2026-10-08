"""Record scoped default compatibility and failed full writer-trace qualification."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

ROOT = Path('D:/Codex/Kestrel')
W = ROOT / 'work/perf-090'
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
assert (a['cases'], a['offered'], a['successful'], a['lost']) == (144, 1872000, 1872000, 0)
assert (a['identity_failed_total'], a['candidate_failed_total']) == (2, 0)
assert a['correctness_passed'] and not a['all_required_scopes_passed']
assert len(a['scopes']) == 6 and sum(s['passed'] for s in a['scopes']) == 4
assert all(s['passed'] for s in a['scopes'] if s['family'] == 'restored-default')
assert load(W / 'post-timing-process-check.json')['active_processes'] == []
baseline = load(W / 'unchanged-supported-source.json')
assert all(sha(REPO / n) == v for n, v in baseline.items())
overnight = '1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
assert sha(REPO / 'OVERNIGHT_2026-10-07.md') == overnight
save(W / 'final-source-provenance.json', {'supported': '0.3.16', 'supported_core_unchanged': True,
    'core_source_sha256': baseline, 'overnight_sha256': overnight,
    'only_isolated_maintenance_source_corrected': True, 'no_remote_publication': True,
    'utc': datetime.now(timezone.utc).isoformat()})
save(W / 'decision-summary.json', {'trial': 90, 'correctness_passed': True,
    'default_compatibility_full_and_both_halves_passed': True,
    'trace_overhead_complete_qualification_passed': False,
    'complete_trial_qualification_passed': False,
    'candidate_failed_total': 0, 'identity_failed_total': 2,
    'identity_criteria': 78, 'candidate_criteria': 78, 'passed_scopes': 4, 'failed_scopes': 2,
    'failures': 'restored-trace write overall p99 A/A in both independent halves',
    'does_not_replace_or_invalidate_088_or_089': True,
    'no_engine_gain_exclusive_causality_or_supported_release_claim': True, 'supported': '0.3.16'})
for n in ['conclude_090.py', 'preserve_090.py', 'prepare_freezer_090.py', 'note_active_090.py']:
    assert not (W / n).exists()
    shutil.copy2(ROOT / 'work' / n, W / n)
frozen = load(W / 'timing-freeze.json')['sha256']
for p in sorted((ROOT / 'work').glob('*090*.log')):
    if p.name.startswith('preserve-090') or p.name == 'conclude-090.log':
        continue
    assert p.name not in frozen and not (W / p.name).exists()
    shutil.copy2(p, W / p.name)
print(json.dumps({'default_compatibility_passed': True, 'complete_tracing_qualification': False,
    'aa_failures': 2, 'candidate_failures': 0, 'supported_unchanged': True}))
