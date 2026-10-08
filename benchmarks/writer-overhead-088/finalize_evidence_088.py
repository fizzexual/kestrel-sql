"""Publish verified corrected proofs while retaining the original failed snapshot."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path('D:/Codex/Kestrel')
OUT = ROOT / 'outputs/kestrel-sql/benchmarks/writer-overhead-088'
CORRECTED = OUT / 'corrected-evidence'
RESTORE = ROOT / 'work/restored-writer-088-v2'
W = ROOT / 'work/perf-088'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


preservation = load(CORRECTED / 'preservation-proof.json')
restored = load(CORRECTED / 'restored-audit-proof.json')
assert preservation['complete'] and restored['passed']
assert restored['native_launches'] == restored['timing_reruns'] == 0
inventory = load(CORRECTED / 'evidence-inventory.json')
expected = set(inventory['entries']) | {'evidence-inventory.json'}
actual = {path.relative_to(RESTORE).as_posix() for path in RESTORE.rglob('*')
    if path.is_file() and '__pycache__' not in path.relative_to(RESTORE).parts and path.suffix != '.pyc'}
assert expected == actual and preservation['files'] == len(expected)
for name, value in inventory['entries'].items():
    assert sha(RESTORE / name) == value['sha256']
assert sha(RESTORE / 'evidence-inventory.json') == sha(W / 'evidence-inventory.json')
for path in sorted(CORRECTED.iterdir()):
    if path.is_file() and path.suffix in ['.json', '.py', '.ps1', '.md']:
        assert not (OUT / path.name).exists()
        shutil.copy2(path, OUT / path.name)
proof = load(OUT / 'preservation-proof.json')
for part in proof['parts']:
    part['name'] = 'corrected-evidence/' + part['name']
proof['initial_failed_98_part_snapshot_retained_at_root'] = True
proof['initial_failed_restore_retained'] = 'D:/Codex/Kestrel/work/restored-writer-088'
proof['correction_record'] = 'initial-preservation-failure-proof.json'
proof['post_audit_exact_file_set_excluding_only_generated_python_caches_passed'] = True
save(OUT / 'preservation-proof.json', proof)
reproduce = OUT / 'REPRODUCE.md'
text = reproduce.read_text(encoding='utf-8')
text = text.replace('ZIPs contain every', 'The corrected ZIPs under corrected-evidence contain every')
text = text.replace('Verify every ZIP SHA sidecar. Extract all parts', 'Use preservation-proof.json at this root: its part names explicitly select corrected-evidence. Verify those ZIP SHA sidecars. Extract all corrected parts')
text += '''
The 98 root-level evidence ZIPs are the initial preserved snapshot. Their member checks passed, but their restored audit failed on a preparation-log hash copied over after timing. They use their own archived evidence-inventory.json and the old restoration; initial-preservation-failure-proof.json records the retained failure. Do not combine their manifest with corrected archives or overwrite them. Completed stdout is retained separately and the exact frozen empty log is restored in the corrected set. Both helpers/failure logs are preserved. No timed binary/source/harness/policy/result or guard changed, and no native workload was rerun.
'''
reproduce.write_text(text, encoding='utf-8', newline='\n')
for name in ['preserve-088-v2.log', 'correct-preservation-088.log', 'finalize_evidence_088.py']:
    shutil.copy2(ROOT / 'work' / name, OUT / name)
print(json.dumps({'corrected_parts': len(proof['parts']), 'corrected_files': proof['files'],
    'initial_98_parts_retained': True, 'raw_audit_and_diagnosis_replayed_exactly': True,
    'post_audit_file_set_and_member_hashes_passed': True, 'native_reruns': 0}))
