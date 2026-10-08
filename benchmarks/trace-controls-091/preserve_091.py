"""Preserve raw trial091 and independently replay the frozen auditor, never Native."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import shutil
import zipfile

ROOT = Path('D:/Codex/Kestrel')
W = ROOT / 'work/perf-091'
OUT = ROOT / 'outputs/kestrel-sql/benchmarks/trace-controls-091'
RESTORE = ROOT / 'work/restored-trace-controls-091'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


assert not OUT.exists() and not RESTORE.exists()
assert load(W / 'paired-service.json')['complete']
assert load(W / 'post-timing-process-check.json')['active_processes'] == []
expected_audit = load(W / 'audit.json')
assert not (W / 'conclude-091.log').exists()
shutil.copy2(ROOT / 'work/conclude-091.log', W / 'conclude-091.log')
frozen = load(W / 'timing-freeze.json')['sha256']
assert all(sha(W / name) == digest for name, digest in frozen.items())
files, excluded = [], []
for path in sorted(W.rglob('*')):
    assert not path.is_symlink() and not path.is_junction(), path
    assert path.resolve().is_relative_to(W.resolve()), path
    if not path.is_file():
        continue
    relative = path.relative_to(W)
    # Finished release binaries, all unit/oracle fixtures and logs are explicitly kept.
    # Only regenerable target build caches and Python caches are omitted; originals stay.
    if relative.parts[0].startswith('target-') or '__pycache__' in relative.parts or path.suffix == '.pyc':
        assert relative.as_posix() not in frozen
        excluded.append({'path': relative.as_posix(), 'bytes': path.stat().st_size})
    else:
        files.append(path)
assert not (W / 'evidence-inventory.json').exists()
entries = {}
for index, path in enumerate(files):
    entries[path.relative_to(W).as_posix()] = {'bytes': path.stat().st_size, 'sha256': sha(path)}
    if (index + 1) % 2000 == 0:
        print(json.dumps({'inventoried': index + 1, 'total_files': len(files)}), flush=True)
save(W / 'evidence-inventory.json', {'entries': entries, 'files': len(entries),
    'logical_bytes': sum(v['bytes'] for v in entries.values()),
    'excluded_regenerable_files': excluded, 'excluded_regenerable_bytes': sum(v['bytes'] for v in excluded),
    'only_exclusions': ['target-* build cache', '__pycache__', '*.pyc'],
    'all_unit_oracle_service_fixtures_logs_binaries_sources_retained': True,
    'all_originals_including_excluded_caches_retained_unchanged': True})
entries['evidence-inventory.json'] = {'bytes': (W / 'evidence-inventory.json').stat().st_size,
    'sha256': sha(W / 'evidence-inventory.json')}
OUT.mkdir()
RESTORE.mkdir()
groups, current, size = [], [], 0
for name, value in sorted(entries.items()):
    assert value['bytes'] <= 80 * 1024 * 1024, name
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
    assert not path.exists()
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
assert {p.relative_to(RESTORE).as_posix() for p in RESTORE.rglob('*') if p.is_file()} == set(entries)
for index, (name, value) in enumerate(entries.items()):
    assert sha(W / name) == value['sha256'] and (W / name).stat().st_size == value['bytes']
    if (index + 1) % 2000 == 0:
        print(json.dumps({'originals_reverified': index + 1, 'total_files': len(entries)}), flush=True)
spec = importlib.util.spec_from_file_location('restored_audit_091', RESTORE / 'audit_service_091.py')
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)
auditor.W = RESTORE
replayed = auditor.main()
assert replayed == expected_audit and sha(RESTORE / 'audit.json') == sha(W / 'audit.json')
diagnostic_spec = importlib.util.spec_from_file_location('restored_diagnostics_091', RESTORE / 'diagnose_trace_091.py')
diagnostic = importlib.util.module_from_spec(diagnostic_spec)
diagnostic_spec.loader.exec_module(diagnostic)
replayed_diagnostic = diagnostic.diagnose(RESTORE)
assert replayed_diagnostic == load(W / 'trace-group-diagnostics.json')
assert replayed_diagnostic == load(RESTORE / 'trace-group-diagnostics.json')

after = {p.relative_to(RESTORE).as_posix() for p in RESTORE.rglob('*')
    if p.is_file() and '__pycache__' not in p.relative_to(RESTORE).parts and p.suffix != '.pyc'}
assert after == set(entries)
assert all(sha(RESTORE / n) == v['sha256'] and (RESTORE / n).stat().st_size == v['bytes'] for n, v in entries.items())
assert all(sha(W / n) == digest for n, digest in frozen.items())
save(OUT / 'restored-audit-proof.json', {'passed': True, 'utc': datetime.now(timezone.utc).isoformat(),
    'every_raw_quantile_conservation_resource_full_and_half_decision_exact': True,
    'post_audit_every_member_hash_size_and_exact_set_passed': True,
    'native_launches': 0, 'timing_reruns': 0, 'descriptive_trace_replay_exact': True, 'restored_tree': str(RESTORE),
    'original_audit_sha256': sha(W / 'audit.json'), 'restored_audit_sha256': sha(RESTORE / 'audit.json'),
    'replayed_summary': {k: v for k, v in replayed.items() if k not in ['scopes', 'trace_results', 'all_events_over_100ms']}})
save(OUT / 'preservation-proof.json', {'complete': True, 'utc': datetime.now(timezone.utc).isoformat(),
    'parts': parts, 'files': len(entries), 'logical_bytes': sum(v['bytes'] for v in entries.values()),
    'all_CRC_SHA_size_and_exact_sets_passed': True, 'every_original_retained_unchanged': True,
    'only_regenerable_target_and_python_caches_excluded': True,
    'all_new_native_store_fixtures_included': True, 'old_090_native_tests_explicitly_reused': True, 'original_path': str(W), 'restored_path': str(RESTORE)})
for name in ['audit.json', 'policy.json', 'timing-freeze.json', 'decision-summary.json',
    'final-source-provenance.json', 'source-derivation.json', 'toolchain.json',
    'reused-qualification-proof.json', 'evidence-inventory.json', 'trace-group-diagnostics.json', 'bottleneck-summary.json',
    'harness-relocation-proof.json', 'order-and-resource-validator-proof.json', 'traced-validator-negative-proof.json',
    'audit_service_091.py', 'run_service_091.py', 'check_processes_091.ps1', 'diagnose_trace_091.py', 'inspect_diagnostics_091.py',
    'post-timing-process-check.json', 'conclude_091.py', 'preserve_091.py']:
    shutil.copy2(W / name, OUT / name)
(OUT / 'REPRODUCE.md').write_text('# Restore and audit stronger writer-trace controls 091\n\nRead TRACE_CONTROLS_091.md and policy.json first. Exact 090 released-core default is repeated A/A versus its writer-trace build; no code edits or rebuilds. Twenty-four rounds, two independently complete 12-round halves, fixed 5% limits and no added observations after results. All 39 A/A checks and 39 candidate guards pass in this two-profile scope. This qualifies scoped diagnostics, not an engine speed gain, competitor ranking or supported release. All 088–090 failures remain preserved.\n\nAll originals remain at D:/Codex/Kestrel/work/perf-091. Parts preserve every raw sample/ACK, all 144 native stores and both excluded smokes, exact copied source/lock/binaries, reused 090 qualification proofs, frozen policy/inputs/harness, every helper/closed log and complete event/tail diagnostics. Prior 090 native unit/lint/oracle/crash/source coverage is reused, not freshly rerun; complete original tests and failures remain in the 090 evidence/history. Only Python caches are omitted, with explicit path/size inventory; originals stay intact. No credentials or shared reset-control files are included. Mutable stdout is excluded from frozen dependencies and copied only after completion.\n\nVerify every ZIP SHA sidecar and preservation-proof.json. Extract into a fresh absolute directory without overwriting evidence; verify member CRC/SHA/size/exact set. evidence-inventory.json lists every member except itself; preservation proof includes it. The checked restored tree is D:/Codex/Kestrel/work/restored-trace-controls-091.\n\nImport audit_service_091.py, set W=Path(ABSOLUTE_RESTORED_DIRECTORY), call main(). Its dictionary and serialized audit.json must exactly match the original, including every sample, ACK/generation/key, quantile, resource, slow sample and full/half gate. Import diagnose_trace_091.py and call diagnose(RESTORED_DIRECTORY); its complete event/group result must match trace-group-diagnostics.json exactly. Both exact replays and every post-replay member hash/size/set are verified with zero native launches or timing reruns. Saved native reopen/NumPy/CRC proofs and preserved store hashes are checked bytes, not a new power-loss or full release test.\n\nDiagnostics are descriptive within this exact qualified artifact/workload scope. Different clock domains prevent exclusive end-to-end p99 decomposition or a physical disk cause. Reclamation intervals motivate a separate bounded-maintenance hypothesis, which must preserve pinned snapshots, orphan treatment, writer ownership, disk ceilings, public API behavior and durability/ACK/retry/source guarantees. Never rerun helpers over evidence, selectively repeat failures, relax limits/durability or compare older C: timings as D: before/after. Use a new experiment number and complete fresh balanced controls for any engine change.\n', encoding='utf-8', newline='\n')
print(json.dumps({'complete': True, 'parts': len(parts), 'files': len(entries),
    'logical_bytes': sum(v['bytes'] for v in entries.values()),
    'restored_raw_audit_exact': True, 'originals_retained': True}), flush=True)
