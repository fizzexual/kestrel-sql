"""Preserve all 088 stores/results and replay raw audits after exact restoration."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import shutil
import zipfile

ROOT = Path('D:/Codex/Kestrel')
W = ROOT / 'work/perf-088'
OUT = ROOT / 'outputs/kestrel-sql/benchmarks/writer-overhead-088'
RESTORE = ROOT / 'work/restored-writer-088'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


assert not OUT.exists() and not RESTORE.exists()
assert load(W / 'paired-service.json')['complete']
assert load(W / 'post-timing-process-check.json')['active_processes'] == []
expected_audit = load(W / 'audit.json')
expected_diagnosis = load(W / 'trace-group-diagnostics.json')
assert sha(W / 'audit.json') == expected_diagnosis['raw_audit_sha256']
for name in ['prepare_088.py', 'declare_balanced_088.py', 'capture_receipts_088.py',
             'freeze_088.py', 'check_processes_088.ps1', 'note_active_088.py',
             'run_service_088.py', 'audit_service_088.py', 'diagnose_trace_088.py',
             'finish_088.py', 'preserve_088.py']:
    target = W / name
    if target.exists():
        assert sha(target) == sha(ROOT / 'work' / name)
    else:
        shutil.copy2(ROOT / 'work' / name, target)
for path in sorted((ROOT / 'work').glob('*088*.log')):
    if path.name != 'preserve-088.log':
        shutil.copy2(path, W / path.name)
files, excluded = [], []
for path in sorted(W.rglob('*')):
    if not path.is_file():
        continue
    assert path.resolve().is_relative_to(W.resolve()) and not path.is_symlink()
    relative = path.relative_to(W)
    if '__pycache__' in relative.parts or path.suffix == '.pyc':
        excluded.append(path)
    else:
        files.append(path)
entries = {}
for index, path in enumerate(files):
    entries[path.relative_to(W).as_posix()] = {'bytes': path.stat().st_size, 'sha256': sha(path)}
    if (index + 1) % 2000 == 0:
        print(json.dumps({'inventoried': index + 1, 'total_files': len(files)}), flush=True)
save(W / 'evidence-inventory.json', {'files': len(entries),
    'logical_bytes': sum(value['bytes'] for value in entries.values()), 'entries': entries,
    'excluded_regenerable_python_cache_files': len(excluded),
    'excluded_regenerable_python_cache_bytes': sum(path.stat().st_size for path in excluded),
    'only_exclusions': ['__pycache__', '*.pyc'], 'every_original_retained': True})
entries['evidence-inventory.json'] = {'bytes': (W / 'evidence-inventory.json').stat().st_size,
    'sha256': sha(W / 'evidence-inventory.json')}
OUT.mkdir()
RESTORE.mkdir()
groups, current, size = [], [], 0
for name, value in sorted(entries.items()):
    if current and size + value['bytes'] > 80 * 1024 * 1024:
        groups.append(current)
        current, size = [], 0
    current.append(name)
    size += value['bytes']
if current:
    groups.append(current)
parts = []
for index, names in enumerate(groups):
    path = OUT / f'evidence-{index + 1:03d}.zip'
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3, allowZip64=True) as archive:
        for name in names:
            archive.write(W / name, name)
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None and archive.namelist() == names
        for name in names:
            target = (RESTORE / name).resolve()
            assert target.is_relative_to(RESTORE.resolve()) and not target.exists()
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as source, target.open('wb') as destination:
                shutil.copyfileobj(source, destination)
            assert sha(target) == entries[name]['sha256'] and target.stat().st_size == entries[name]['bytes']
    digest = sha(path)
    (OUT / (path.name + '.sha256')).write_text(digest + '  ' + path.name + '\n', encoding='utf-8', newline='\n')
    parts.append({'name': path.name, 'sha256': digest, 'bytes': path.stat().st_size, 'members': len(names)})
    print(json.dumps({'verified_part': index + 1, 'total_parts': len(groups), 'members': len(names)}), flush=True)
assert {path.relative_to(RESTORE).as_posix() for path in RESTORE.rglob('*') if path.is_file()} == set(entries)
for index, (name, value) in enumerate(entries.items()):
    assert sha(W / name) == value['sha256']
    if (index + 1) % 2000 == 0:
        print(json.dumps({'originals_reverified': index + 1, 'total_files': len(entries)}), flush=True)
auditor = module(RESTORE / 'audit_service_088.py', 'restored_audit_088')
auditor.W = RESTORE
restored_audit = auditor.main()
assert restored_audit == expected_audit and sha(RESTORE / 'audit.json') == sha(W / 'audit.json')
diagnostic = module(RESTORE / 'diagnose_trace_088.py', 'restored_diagnosis_088')
restored_diagnosis = diagnostic.diagnose(RESTORE)
assert restored_diagnosis == expected_diagnosis
save(OUT / 'restored-audit-proof.json', {'passed': True, 'utc': datetime.now(timezone.utc).isoformat(),
    'every_raw_quantile_conservation_trace_scope_and_diagnostic_decision_exact': True,
    'native_launches': 0, 'timing_reruns': 0, 'restored_tree': str(RESTORE),
    'original_audit_sha256': sha(W / 'audit.json'), 'restored_audit_sha256': sha(RESTORE / 'audit.json'),
    'descriptive_diagnosis_sha256': sha(W / 'trace-group-diagnostics.json'),
    'replayed_summary': {key: value for key, value in restored_audit.items()
        if key not in ['scopes', 'trace_results', 'all_events_over_100ms']}})
save(OUT / 'preservation-proof.json', {'complete': True, 'utc': datetime.now(timezone.utc).isoformat(),
    'parts': parts, 'files': len(entries), 'logical_bytes': sum(value['bytes'] for value in entries.values()),
    'all_CRC_SHA_size_and_exact_sets_passed': True, 'every_original_retained_unchanged': True,
    'excluded_only_regenerable_python_caches': True, 'original_path': str(W), 'restored_path': str(RESTORE)})
for name in ['audit.json', 'policy.json', 'timing-freeze.json', 'decision-summary.json',
             'trace-diagnostic-summary.json', 'final-source-provenance.json', 'evidence-inventory.json',
             'audit_service_088.py', 'diagnose_trace_088.py', 'run_service_088.py',
             'check_processes_088.ps1', 'post-timing-process-check.json',
             'reused087-bridge-v2-proof.json', 'reused087-build-proof.json',
             'order-and-trace-validator-check.json', 'controller-poll-syntax-failure.json',
             'finish_088.py', 'preserve_088.py']:
    shutil.copy2(W / name, OUT / name)
(OUT / 'REPRODUCE.md').write_text('''# Restore and audit service qualification 088

Read WRITER_OVERHEAD_088.md and the frozen policy before interpreting results. Every required full/half family fails qualification; supported 0.3.16 remains unchanged. The exact unmodified auditor verifies 288 cases, 2.88 million offers, all ACK/trace relationships, raw nearest-rank quantiles and fixed guards. CPU and post-cohort trace summaries are descriptive; they do not establish qualified write overhead or a physical cause.

All original evidence remains D:\\Codex\\Kestrel\\work\\perf-088. ZIPs contain every raw sample, all 288 native stores, both complete smoke cohorts, initial and strengthened pre-native policies, exact six binaries/four source trees/locks/tests, callback/receipt changes, raw traces, all logs/proofs and the read-only controller syntax failure. Only Python cache files are excluded; nothing is deleted. No profile configuration, credentials or reset-control data are included.

Verify every ZIP SHA sidecar. Extract all parts into a fresh absolute directory without overwriting originals. Check member CRC, member SHA/size and exact set against evidence-inventory.json and preservation-proof.json. The inventory lists the complete tree except its own entry; preservation-proof counts that entry too. Current verified restoration is D:\\Codex\\Kestrel\\work\\restored-writer-088.

To reparse without native/timer reruns, import audit_service_088.py using importlib, assign its module W to Path(ABSOLUTE_RESTORED_DIRECTORY), then call main(). The returned dictionary and serialized audit.json must exactly equal the preserved audit. Frozen source/hash/order/negative-validation evidence remains unchanged. Import diagnose_trace_088.py and call diagnose(ABSOLUTE_RESTORED_DIRECTORY); it must exactly equal trace-group-diagnostics.json, including every group association and calibration label. restored-audit-proof.json records the actual complete replay of both.

The auditor reads the saved Native/NumPy/CRC reconciliation proofs. Exact restored store hashes preserve the bytes on which those checks ran; this audit starts no process and does not claim fresh power-loss or new crash tests. Original 087 native/test/byte/retry/protocol qualifications are explicitly reused.

Never run prepare/smoke/runner over this evidence tree or rerun only bad cases. New same-toolchain build/control investigation, diagnostic revisions or writer candidates need a new experiment number, fresh directory, declared balanced unchanged controls and complete correctness/service/resource/recovery qualification. Builds/copies/hashing/packaging/cleanup must stop before timers. Preserve every failed/unqualified block and original 086/087/088 result.
''', encoding='utf-8', newline='\n')
print(json.dumps({'complete': True, 'parts': len(parts), 'files': len(entries),
    'logical_bytes': sum(value['bytes'] for value in entries.values()),
    'restored_raw_audit_and_diagnosis_exact': True, 'originals_retained': True}), flush=True)
