"""Preserve raw trial090 and independently replay the frozen auditor, never Native."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import shutil
import zipfile

ROOT = Path('D:/Codex/Kestrel')
W = ROOT / 'work/perf-090'
OUT = ROOT / 'outputs/kestrel-sql/benchmarks/maintenance-isolation-090'
RESTORE = ROOT / 'work/restored-maintenance-090'


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
assert not (W / 'conclude-090.log').exists()
shutil.copy2(ROOT / 'work/conclude-090.log', W / 'conclude-090.log')
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
spec = importlib.util.spec_from_file_location('restored_audit_090', RESTORE / 'audit_service_090.py')
auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor)
auditor.W = RESTORE
replayed = auditor.main()
assert replayed == expected_audit and sha(RESTORE / 'audit.json') == sha(W / 'audit.json')
after = {p.relative_to(RESTORE).as_posix() for p in RESTORE.rglob('*')
    if p.is_file() and '__pycache__' not in p.relative_to(RESTORE).parts and p.suffix != '.pyc'}
assert after == set(entries)
assert all(sha(RESTORE / n) == v['sha256'] and (RESTORE / n).stat().st_size == v['bytes'] for n, v in entries.items())
assert all(sha(W / n) == digest for n, digest in frozen.items())
save(OUT / 'restored-audit-proof.json', {'passed': True, 'utc': datetime.now(timezone.utc).isoformat(),
    'every_raw_quantile_conservation_resource_full_and_half_decision_exact': True,
    'post_audit_every_member_hash_size_and_exact_set_passed': True,
    'native_launches': 0, 'timing_reruns': 0, 'restored_tree': str(RESTORE),
    'original_audit_sha256': sha(W / 'audit.json'), 'restored_audit_sha256': sha(RESTORE / 'audit.json'),
    'replayed_summary': {k: v for k, v in replayed.items() if k not in ['scopes', 'trace_results', 'all_events_over_100ms']}})
save(OUT / 'preservation-proof.json', {'complete': True, 'utc': datetime.now(timezone.utc).isoformat(),
    'parts': parts, 'files': len(entries), 'logical_bytes': sum(v['bytes'] for v in entries.values()),
    'all_CRC_SHA_size_and_exact_sets_passed': True, 'every_original_retained_unchanged': True,
    'only_regenerable_target_and_python_caches_excluded': True,
    'all_cargo_tests_included': True, 'original_path': str(W), 'restored_path': str(RESTORE)})
for name in ['audit.json', 'policy.json', 'timing-freeze.json', 'decision-summary.json',
    'final-source-provenance.json', 'source-derivation.json', 'maintenance-source-isolation-proof.json',
    'toolchain.json', 'build-proof.json', 'oracle-proof.json', 'evidence-inventory.json',
    'harness-relocation-proof.json', 'order-and-resource-validator-proof.json', 'traced-validator-negative-proof.json',
    'audit_service_090.py', 'run_service_090.py', 'check_processes_090.ps1',
    'post-timing-process-check.json', 'conclude_090.py', 'preserve_090.py']:
    shutil.copy2(W / name, OUT / name)
(OUT / 'REPRODUCE.md').write_text('''# Restore and audit controlled build comparison 090

Read MAINTENANCE_ISOLATION_090.md and the fixed policy first. All candidate numerical guards pass. Restored default compatibility passes full and both halves; writer-trace overall p99 A/A fails in both halves, so complete tracing qualification fails. Supported 0.3.16 and failed prior experiments remain unchanged. This is a scoped maintenance source correction with default compatibility qualified in two profiles, not an engine speed gain, complete tracer overhead bound, competitor win or release.

All original files remain at D:\\Codex\\Kestrel\\work\\perf-090. ZIPs preserve all raw 1.872 million samples, ACKs, 144 native stores, three setup smokes, every cargo-test/oracle fixture and raw native result/log, exact built/baseline binaries, one corrected source/lock/test tree plus the exact failed partial preparation/source tree, initial/final policies, helpers, build settings, source derivation and all failures. Only regenerable target build caches and Python caches are excluded; excluded path/size inventory is explicit and originals remain intact. No credentials or shared reset-control files are included. Completed stdout logs are not frozen dependencies and were copied only after their processes ended.

Verify every ZIP SHA sidecar against preservation-proof.json; extract all parts into a fresh absolute directory without overwriting any evidence. Verify ZIP member CRC, member SHA/size and exact set. evidence-inventory.json lists every member except itself; preservation-proof includes the inventory file too. Verified restoration is D:\\Codex\\Kestrel\\work\\restored-maintenance-090.

Import audit_service_090.py using importlib, assign module W = Path(ABSOLUTE_RESTORED_DIRECTORY), then call main(). The returned dictionary and serialized audit.json must exactly match the preserved audit, including all raw quantiles, conservation, memory/CPU records, failed A/A checks and full/half decisions. This starts no native process and reruns no timing. restored-audit-proof.json records the completed exact replay plus post-audit complete hash/size/set checks, excluding only newly generated Python caches. Frozen inputs and original bytes were reverified.

The auditor reads saved native reopen/NumPy/CRC proofs. Restored store hashes preserve the checked bytes; no fresh crash, power-loss or complete release suite is claimed. Actual 090 correctness includes 322 native test executions/five strict lint modes, eight byte-equivalent stores, 32 cross-reopens, 48 independent SQLite comparisons, ten named/concurrent/retry/controlled-directory-failure/reopen modes, six old016 CLI live reopens and three wire checks. Traced append ACK keys/generations/stages are exactly audited. The first pre-native preparation guard failed; its exact policy/source/helper/error stays in failed-preparation-v1 and corrected v2 keeps the policy byte-identical. No native/timing reruns were used. Earlier full crash/source qualifications are reused and clearly distinguished.

Never run prepare/build/oracles/smoke/runner over preserved evidence or selectively repeat failed cases. Further controls or justified engine candidates require a new experiment number, fresh predeclared complete balanced unchanged A/A controls, full and half gates, preserved failures and correctness/recovery/service/resource qualification. Do not relax thresholds or durability. Builds/copies/hashing/packaging/cleanup must stop before timers.
''', encoding='utf-8', newline='\n')
print(json.dumps({'complete': True, 'parts': len(parts), 'files': len(entries),
    'logical_bytes': sum(v['bytes'] for v in entries.values()),
    'restored_raw_audit_exact': True, 'originals_retained': True}), flush=True)
