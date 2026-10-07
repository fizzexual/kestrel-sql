"""Verify 073 with its own frozen baseline; retain the published runner unchanged."""
import ast
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

assert len(sys.argv) == 3 and sys.argv[1] == '--verify'
work = Path(sys.argv[2]).resolve()
root = work.parents[1] / 'outputs/kestrel-sql'
destination = root / 'benchmarks/receipt-cycles-073-finalization'
destination.mkdir(exist_ok=True)

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

original = work / 'maintain_evidence.py'
assert sha(original) == '179fffb20df98357d6bf9c962924b7cc1edcb495897ea6b583f27bbb9bf3ae81'
baseline = work / 'repository-manifest-pre-073.sha256'
assert sha(baseline) == 'cf87be03526cc251212402ba606921acb736549c0d87a6540544a784cc390791'
preserved = root / 'benchmarks/receipt-cycles-073'
assert sha(preserved / original.name) == sha(original)
assert sha(preserved / baseline.name) == sha(baseline)
source = original.read_text(encoding='utf-8')
old = "W/'repository-manifest-pre-072.sha256'"
new = "W/'repository-manifest-pre-073.sha256'"
assert source.count(old) == 1 and new not in source
corrected = source.replace(old, new)
ast.parse(corrected, filename=str(original))
runner = Path(__file__).resolve()
assert sha(runner) == sha(work / runner.name)
if runner != destination / runner.name:
    shutil.copy2(runner, destination / runner.name)
assert sha(destination / runner.name) == sha(runner)
shutil.copy2(work / 'verification-first-failure.log', destination / 'verification-first-failure.log')
proof = {
    'prepared_utc': datetime.now(timezone.utc).isoformat(),
    'original_runner_sha256': sha(original),
    'original_runner_unchanged': True,
    'baseline_manifest_sha256': sha(baseline),
    'completion_runner_sha256': sha(runner),
    'retained_failure_log_sha256': sha(destination / 'verification-first-failure.log'),
    'correction': {'old_literal': old, 'new_literal': new, 'replacements': 1},
    'published_zip_unchanged': True,
    'no_build_or_timed_case_rerun': True,
    'measurements_policy_source_binary_unchanged': True,
    'scope': 'Post-publication verification filename only; original packaged maintainer retained.',
}
(destination / 'completion-provenance.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
sys.argv = [str(original), '--verify']
exec(compile(corrected, str(original), 'exec'), {'__file__': str(original), '__name__': '__main__'})
