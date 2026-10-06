"""Package the verified 0.3.1 evidence after all timed loads and servers stop.

Run from any directory with Python 3.11+. Historical packages are preserved.
"""
import ast
import hashlib
import json
import re
import shutil
import socket
import subprocess
import sys
import time
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent.parent
VERSION = '0.3.1'
PACKAGE = ROOT.parent / f'kestrel-sql-{VERSION}.zip'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def main():
    for port in [55439, 53329, 53319, 33060]:
        with socket.socket() as probe:
            probe.settimeout(.5)
            assert probe.connect_ex(('127.0.0.1', port)) != 0, ('reference server remains running', port)
    assert tomllib.loads((ROOT / 'Cargo.toml').read_text(encoding='utf-8'))['package']['version'] == VERSION
    build = read('benchmarks/rust-checks-031.json')
    assert build['version'] == VERSION
    assert build['rust_tests'] == {'debug': 31, 'release': 31, 'passed': True}
    assert build['format_check'] == build['clippy_warnings_as_errors'] == 'passed'
    for name, digest in build['source_sha256'].items():
        assert sha((ROOT / name).read_bytes()) == digest, ('source changed after checks', name)
    for name, field in [('kestrel', 'cli_sha256'), ('kestrel-stress', 'bridge_sha256'), ('performance-probe', 'probe_sha256')]:
        source = WORKSPACE / 'work' / 'perf-031' / 'candidate' / f'{name}.exe'
        assert sha(source.read_bytes()) == build[field], name
        shutil.copy2(source, ROOT / 'bin' / source.name)
    prior = ROOT / 'verification-v03.json'
    if not prior.exists():
        old = read('verification.json')
        assert old['version'] == '0.3.0'
        prior.write_text(json.dumps(old, indent=2) + '\n', encoding='utf-8')
    assert read('verification-v03.json')['version'] == '0.3.0'
    audit = read('benchmarks/perf-031-audit.json')
    stress_keys = ['baseline', 'buffered_trial', 'final', 'interleaved', 'analytics']
    cases = sum(audit[k]['completed_cases'] for k in stress_keys)
    offered = sum(audit[k]['offered_operations'] for k in stress_keys)
    assert cases == 84 and offered == 1400400
    assert audit['invalid_build_comparison']['excluded']
    recovery = read('benchmarks/perf-031-recovery.json')
    assert len(recovery['cycles']) == 24
    assert all(c['sum_and_full_scrub_passed'] and c['retry_deduplication_passed'] for c in recovery['cycles'])
    assert recovery['binary_sha256'] == build['bridge_sha256'] and recovery['sql_binary_sha256'] == build['cli_sha256']
    demo = read('portfolio/live-pipeline-031-results.json')
    assert demo['exact_sql_cases_against_duckdb'] == 42
    assert demo['replayed_sources_not_duplicated'] and demo['changed_content_rejected']
    assert demo['engine_version'] == VERSION and demo['binary_sha256'] == build['bridge_sha256']
    compatibility = read('benchmarks/format-031.json')
    assert compatibility['legacy_catalog_read'] and compatibility['older_binary_rejects_new_catalog']
    assert compatibility['binary_sha256'] == build['bridge_sha256']
    capabilities = read('benchmarks/capability-031.json')
    assert len(capabilities['engines']) == 6 and capabilities['engines'][0]['version'] == VERSION
    assert capabilities['binary_sha256'] == build['bridge_sha256'] and capabilities['sql_binary_sha256'] == build['cli_sha256']
    recheck = read('benchmarks/release-recheck-031.json')
    assert recheck['all_retained_results_match'] and recheck['binary_sha256'] == build['cli_sha256']
    baseline = read('benchmarks/baseline-0.3-provenance.json')
    for name, digest in baseline['core_source_sha256'].items():
        assert sha((ROOT / 'benchmarks' / 'baseline-0.3-source' / name).read_bytes()) == digest, name
    for name, digest in baseline['baseline_binary_sha256'].items():
        assert sha((ROOT / 'bin' / 'baseline-0.3' / name).read_bytes()) == digest, name
    assert baseline['core_source_sha256']['examples/performance_probe.rs'] == build['source_sha256']['examples/performance_probe.rs']
    historical = read('verification-v02.json')
    proof = {
        **build, 'version': VERSION, 'local_qualification_date': '2026-10-06',
        'status': 'experimental prototype; production qualification remains incomplete',
        'historical_0_3_proof': 'verification-v03.json', 'historical_0_2_proof': 'verification-v02.json',
        'historical_scale_and_pipeline': {k: historical[k] for k in ['archive_differential', 'scale', 'real_data', 'analytical_sql']},
        'retained_data_recheck': recheck, 'current_stress': audit,
        'archive_identified_process_kills': {
            'cycles_passed': 24, 'acknowledged_batches': sum(c['acknowledged_batches'] for c in recovery['cycles']),
            'unacknowledged_committed_batches': sum(c['unacknowledged_committed_batches'] for c in recovery['cycles']),
            'all_acknowledged_batches_present': True, 'published_batches_atomic': True,
            'retry_deduplication_passed': True, 'full_scrubs_passed': True,
            'fault_model': recovery['fault_model'], 'report': 'benchmarks/perf-031-recovery.json'},
        'hard_boundaries': recovery['boundaries'], 'live_pipeline': demo,
        'format_compatibility': compatibility, 'baseline_provenance': baseline,
        'executed_capabilities': {'engines': 6, 'report': 'benchmarks/capability-031.json', 'archive_transactional_parity': False},
        'stress_bridge': {'test_only': True, 'binary_sha256': build['bridge_sha256'],
                         'concurrency': 'immutable LiveArchive snapshots; one bounded durable group writer'},
        'reference_servers_stopped': True,
        'qualification_limits': [
            'shared desktop and unequal client interfaces; short repeated runs are descriptive',
            'latency percentiles include successes only; all failed/unexecuted offers reported separately',
            'unordered-filter regression and overload/single-client tail failures remain visible',
            'BIGINT aggregate subset; no raw projection, joins, updates/deletes or SQL transactions in Archive',
            'no native Arrow/Parquet SDK; Parquet demo reads sources through DuckDB',
            'receipt capacity correctness tested at 100000 IDs; full-ledger unique-write endurance unqualified',
            'queue/cache budgets exclude caller allocations, active pinned pages and OS caches',
            'backup/retention/orphan cleanup, upgrades and disk exhaustion remain unqualified',
            'physical power loss, Windows directory-entry durability and Linux execution unqualified',
            'no distributed scale, replication or TAOBench/Facebook-scale qualification']}
    (ROOT / 'verification.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    for path in ROOT.rglob('*.py'):
        if not {'target', '__pycache__', '.git'}.intersection(path.relative_to(ROOT).parts):
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    for path in ROOT.rglob('*.json'):
        json.loads(path.read_text(encoding='utf-8'))
    for path in ROOT.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith('#'):
                assert (path.parent / target.split('#')[0]).exists(), (path.name, target)
    for package in tomllib.loads((ROOT / 'Cargo.lock').read_text(encoding='utf-8'))['package']:
        if package['name'] != 'kestrel-sql':
            license_dir = ROOT / 'licenses' / f"{package['name']}-{package['version']}"
            assert license_dir.is_dir() and any(license_dir.iterdir()), ('missing licenses', str(license_dir))
    reply = subprocess.check_output([str(ROOT / 'bin' / 'kestrel.exe'), '--file', str(ROOT / 'examples' / 'live_metrics.sql')], text=True)
    responses = [json.loads(line) for line in reply.splitlines()]
    assert len(responses) == 8 and all(item['ok'] for item in responses)
    assert responses[2]['result']['rows'] == [[2, 30, 15.0]]
    files = sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name != 'MANIFEST.sha256'
                   and not {'target', '__pycache__', '.git'}.intersection(p.relative_to(ROOT).parts))
    manifest = [(sha(path.read_bytes()), path.relative_to(ROOT).as_posix()) for path in files]
    (ROOT / 'MANIFEST.sha256').write_text(''.join(f'{digest}  {name}\n' for digest, name in manifest), encoding='utf-8')
    files.append(ROOT / 'MANIFEST.sha256')
    with zipfile.ZipFile(PACKAGE, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=False) as archive:
        for path in files:
            archive.write(path, (Path(ROOT.name) / path.relative_to(ROOT)).as_posix())
    with zipfile.ZipFile(PACKAGE) as archive:
        assert archive.testzip() is None and len(archive.namelist()) == len(files)
        for digest, name in manifest:
            assert sha(archive.read(ROOT.name + '/' + name)) == digest, name
        extracted = WORKSPACE / 'work' / f'package-smoke-031-{time.time_ns()}'
        extracted.mkdir()
        for name in ['kestrel', 'kestrel-stress']:
            archive.extract(ROOT.name + '/bin/' + name + '.exe', extracted)
        binary = extracted / ROOT.name / 'bin' / 'kestrel.exe'
        assert '--archive' in subprocess.check_output([str(binary), '--help'], text=True)
        sys.path.insert(0, str(ROOT / 'benchmarks'))
        from stress_compare import Engine
        engine = Engine('kestrel', extracted / 'fresh-store', 1000, extracted / ROOT.name / 'bin' / 'kestrel-stress.exe', {})
        try:
            connection = engine.connect()
            assert connection.query('SELECT COUNT(*), SUM(value) FROM events') == [[1000, -500]]
            request = {'op': 'append', 'id': 'package:one', 'data': [[1000, 17, 2], [1001, -3, 2]]}
            assert not connection.call(request)['duplicate']
            assert connection.call(request)['duplicate']
            connection.close()
            engine.reopen()
            connection = engine.connect()
            assert connection.call(request)['duplicate']
            assert connection.query('SELECT COUNT(*), SUM(value) FROM events') == [[1002, -486]]
            assert connection.call({'op': 'verify'})['verified_bytes'] == 1002 * 24
            connection.close()
        finally:
            engine.finish()
    digest = sha(PACKAGE.read_bytes())
    PACKAGE.with_suffix('.zip.sha256').write_text(f'{digest}  {PACKAGE.name}\n', encoding='utf-8')
    result = {'package': str(PACKAGE), 'bytes': PACKAGE.stat().st_size, 'sha256': digest,
              'payload_files': len(manifest), 'zip_integrity': 'passed', 'all_file_hashes': 'passed',
              'internal_document_links': 'passed', 'python_syntax': 'passed',
              'packaged_executable_replay_reopen_scrub_smokes': 'passed', 'reference_servers_stopped': True,
              'current_stress_cases': cases, 'current_offered_requests': offered,
              'historical_0_3_proof_preserved': True, 'historical_0_2_proof_preserved': True,
              'invalid_build_probe_excluded': True}
    (ROOT.parent / f'kestrel-sql-{VERSION}-package-check.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
