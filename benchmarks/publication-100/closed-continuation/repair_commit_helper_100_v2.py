"""Preserve an unexecuted metadata draft and fix its old packager-log reference."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import json
import shutil

ROOT = Path('D:/Codex/Kestrel')
WORK = ROOT / 'work'
first = WORK / 'commit_100.py'
target = WORK / 'commit_100_v2.py'
backup = WORK / 'draft-commit-100-v1'
assert not backup.exists() and not target.exists() and not (WORK / 'commit-100-proof.json').exists()
assert not (ROOT / 'outputs/kestrel-sql/PUBLICATION_COST_100.md').exists()
old = first.read_text(encoding='utf-8')
needle = "for path in [WORK / 'preserve-099.log', Path(__file__), guard_path]:"
assert old.count(needle) == 1
backup.mkdir()
for name in ['commit_100.py', 'prepare_commit_100.py', 'commit-derivation-100.json']:
    shutil.copy2(WORK / name, backup / name)
proof = {'utc': datetime.now(timezone.utc).isoformat(),
    'unexecuted_generated_draft_preflight_caught_wrong_log_reference': 'preserve-099.log instead of preserve-100.log',
    'no_report_navigation_stage_commit_native_source_raw_policy_or_gate_mutated_by_first_draft': True,
    'files': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in backup.iterdir() if p.is_file()}}
(backup / 'draft-preservation.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8', newline='\n')
new = old.replace(needle,
    "for path in [WORK / 'preserve-100.log', Path(__file__), guard_path, WORK / 'prepare_commit_100.py', WORK / 'commit-derivation-100.json', WORK / 'repair_commit_helper_100_v2.py', WORK / 'commit-helper-repair-100-v2-proof.json', WORK / 'inspect_publication_basis_100.py', WORK / 'publication-basis-100-proof.json', WORK / 'publication-basis-100.log', WORK / 'qualified-basis-reuse-100-proof.json', WORK / 'initial-read-errors-100.json']:")
new = new.replace("save(supplement / 'proof.json', {",
    "shutil.copytree(WORK / 'draft-commit-100-v1', supplement / 'draft-commit-v1')\nsave(supplement / 'proof.json', {")
new = new.replace("'files': {p.name: sha(p) for p in supplement.iterdir() if p.is_file()},",
    "'files': {p.relative_to(supplement).as_posix(): sha(p) for p in supplement.rglob('*') if p.is_file()},")
new = new.replace("report_path = R / 'PUBLICATION_COST_100.md'",
    "report += '\\nPre-commit inspection caught an old packager-log filename in the first generated commit draft. That draft was never executed and changed no report, navigation, staged file, commit, Native/source/raw/policy or gate. Its exact helper/generator/derivation bytes are retained in closed-continuation/draft-commit-v1. The corrected v2 helper copies the actual closed preserve-100.log and all post-cohort basis/read records; numerical rejection and frozen evidence are unchanged.\\n'\nreport_path = R / 'PUBLICATION_COST_100.md'")
assert 'preserve-099.log' not in new
ast.parse(new)
target.write_text(new, encoding='utf-8', newline='\n')
final = {'utc': datetime.now(timezone.utc).isoformat(), 'unexecuted_first_draft_preserved': str(backup),
    'first_helper_sha256': hashlib.sha256(first.read_bytes()).hexdigest(),
    'v2_helper_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
    'only_closed_log_supplement_and_draft_preservation_bookkeeping_changed': True,
    'no_source_raw_policy_gate_or_native_change': True}
(WORK / 'commit-helper-repair-100-v2-proof.json').write_text(json.dumps(final, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(final))
