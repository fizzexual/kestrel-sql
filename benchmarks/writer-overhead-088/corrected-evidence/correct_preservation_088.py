"""Preserve the failed archive attempt and repair its log-only bookkeeping error."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

ROOT = Path('D:/Codex/Kestrel')
W = ROOT / 'work/perf-088'
OUT = ROOT / 'outputs/kestrel-sql/benchmarks/writer-overhead-088'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


frozen = json.loads((W / 'timing-freeze.json').read_text(encoding='utf-8'))['sha256']
empty_hash = hashlib.sha256(b'').hexdigest()
assert frozen['freeze-088-run.log'] == empty_hash
assert (W / 'freeze-088-run.log').stat().st_size > 0
assert sha(W / 'freeze-088-run.log') == sha(ROOT / 'work/freeze-088-run.log')
for name in ['completed-freeze-088-run.log', 'initial-evidence-inventory.json',
             'preserve-088-first-attempt.log', 'WRITER_OVERHEAD_088.before-log-correction.md']:
    assert not (W / name).exists()
shutil.copy2(W / 'freeze-088-run.log', W / 'completed-freeze-088-run.log')
shutil.copy2(W / 'evidence-inventory.json', W / 'initial-evidence-inventory.json')
shutil.copy2(ROOT / 'work/preserve-088.log', W / 'preserve-088-first-attempt.log')
shutil.copy2(W / 'WRITER_OVERHEAD_088.md', W / 'WRITER_OVERHEAD_088.before-log-correction.md')
(W / 'freeze-088-run.log').write_bytes(b'')
assert all(sha(W / name) == digest for name, digest in frozen.items())
parts = sorted(OUT.glob('evidence-*.zip'))
assert len(parts) == 98
proof = {'utc': datetime.now(timezone.utc).isoformat(),
    'failed_step': 'Initial restored audit, timing-freeze hash of freeze-088-run.log',
    'cause': 'Post-timing packaging copied completed root stdout over the frozen empty preparation-log copy.',
    'initial_archives_retained': [{'name': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path)} for path in parts],
    'initial_restore_retained': 'D:/Codex/Kestrel/work/restored-writer-088',
    'initial_member_CRC_SHA_size_exact_sets_passed_before_audit_stop': True,
    'frozen_empty_log_recreated_from_known_zero_byte_content': True,
    'completed_stdout_retained_as': 'completed-freeze-088-run.log',
    'initial_inventory_and_failure_log_retained': True,
    'all_frozen_binary_source_harness_policy_auditor_hashes_exact': True,
    'timed_report_sha256': sha(W / 'paired-service.json'),
    'raw_audit_sha256': sha(W / 'audit.json'),
    'native_launches_and_timing_reruns': 0,
    'no_guard_or_comparator_change': True,
    'corrected_archive_location': 'benchmarks/writer-overhead-088/corrected-evidence',
    'corrected_restore_location': 'D:/Codex/Kestrel/work/restored-writer-088-v2'}
save(W / 'preservation-log-correction.json', proof)
save(OUT / 'initial-preservation-failure-proof.json', proof)
report = ROOT / 'outputs/kestrel-sql/WRITER_OVERHEAD_088.md'
text = report.read_text(encoding='utf-8')
assert text == (W / 'WRITER_OVERHEAD_088.md').read_text(encoding='utf-8')
text = text.replace('work\\\\restored-writer-088`', 'work\\\\restored-writer-088-v2`')
# Actual report has single backslashes after Python string evaluation.
text = text.replace('work\\restored-writer-088`', 'work\\restored-writer-088-v2`')
text += '''
The first packaging attempt overwrote the frozen empty preparation-log copy with the completed stdout log. All 98 initial archive parts passed CRC/member hash/size/set checks, but the restored frozen-file audit correctly stopped on that log hash. Every initial archive and the failed restoration remain retained. The empty log's exact known zero-byte content is restored; completed stdout, original inventory, helper and failure log are kept separately. Corrected full archives use `benchmarks/writer-overhead-088/corrected-evidence`, with a fresh `work/restored-writer-088-v2` restoration. Binaries, sources, policy, harness, auditor, raw timing and all qualification decisions are unchanged; no native workload is rerun.
'''
report.write_text(text, encoding='utf-8', newline='\n')
(W / 'WRITER_OVERHEAD_088.md').write_text(text, encoding='utf-8', newline='\n')
shutil.copy2(ROOT / 'work/correct_preservation_088.py', W / 'correct_preservation_088.py')
source = (ROOT / 'work/preserve_088.py').read_text(encoding='utf-8')
assert source.count("OUT = ROOT / 'outputs/kestrel-sql/benchmarks/writer-overhead-088'") == 1
source = source.replace("OUT = ROOT / 'outputs/kestrel-sql/benchmarks/writer-overhead-088'", "OUT = ROOT / 'outputs/kestrel-sql/benchmarks/writer-overhead-088/corrected-evidence'")
source = source.replace("RESTORE = ROOT / 'work/restored-writer-088'", "RESTORE = ROOT / 'work/restored-writer-088-v2'")
source = source.replace("'finish_088.py', 'preserve_088.py']:", "'finish_088.py', 'preserve_088.py', 'preserve_088_v2.py', 'correct_preservation_088.py']:", 1)
old = """for path in sorted((ROOT / 'work').glob('*088*.log')):
    if path.name != 'preserve-088.log':
        shutil.copy2(path, W / path.name)
"""
new = """frozen_hashes = load(W / 'timing-freeze.json')['sha256']
for path in sorted((ROOT / 'work').glob('*088*.log')):
    if path.name == 'preserve-088-v2.log':
        continue
    name = path.name
    if name in frozen_hashes and sha(path) != frozen_hashes[name]:
        name = 'completed-' + name
    target = W / name
    if target.exists():
        assert sha(target) == sha(path)
    else:
        shutil.copy2(path, target)
"""
assert source.count(old) == 1
source = source.replace(old, new)
source = source.replace("    relative = path.relative_to(W)\n", "    relative = path.relative_to(W)\n    if relative.as_posix() == 'evidence-inventory.json':\n        continue  # Its initial bytes are retained as initial-evidence-inventory.json.\n", 1)
source = source.replace('work\\\\restored-writer-088.', 'work\\\\restored-writer-088-v2.')
source = source.replace('All original evidence remains D:', 'Corrected full evidence ZIPs are in corrected-evidence. Initial root ZIPs and the failed first restoration remain preserved; do not combine their manifests. All original evidence remains D:')
source = source.replace("             'finish_088.py', 'preserve_088.py']:\n", "             'finish_088.py', 'preserve_088.py', 'preserve_088_v2.py', 'correct_preservation_088.py', 'preservation-log-correction.json']:\n")
target = ROOT / 'work/preserve_088_v2.py'
assert not target.exists()
compile(source, str(target), 'exec')
target.write_text(source, encoding='utf-8', newline='\n')
print(json.dumps({'frozen_hashes_restored': True, 'initial_98_parts_retained': True,
    'native_reruns': 0, 'new_pack_helper': str(target)}))
