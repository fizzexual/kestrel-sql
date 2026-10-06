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
VERSION = tomllib.loads((ROOT / 'Cargo.toml').read_text(encoding='utf-8'))['package']['version']
assert VERSION in ['0.3.1', '0.3.2'], 'Add explicit qualification gates for this release'
TAG = VERSION.replace('.', '')
TESTS = {'0.3.1': 31, '0.3.2': 32}[VERSION]
BASELINE_VERSION = '0.3' if VERSION == '0.3.1' else '0.3.1'
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
    build = read(f'benchmarks/rust-checks-{TAG}.json')
    assert build['version'] == VERSION
    assert build['rust_tests'] == {'debug': TESTS, 'release': TESTS, 'passed': True}
    assert build['format_check'] == build['clippy_warnings_as_errors'] == 'passed'
    for name, digest in build['source_sha256'].items():
        assert sha((ROOT / name).read_bytes()) == digest, ('source changed after checks', name)
    binaries = [('kestrel', 'cli_sha256'), ('kestrel-stress', 'bridge_sha256'), ('performance-probe', 'probe_sha256')]
    if VERSION == '0.3.2':
        binaries.append(('scan-profile', 'scan_probe_sha256'))
    for name, field in binaries:
        source = WORKSPACE / 'work' / f'perf-{TAG}' / 'candidate' / f'{name}.exe'
        assert sha(source.read_bytes()) == build[field], name
        shutil.copy2(source, ROOT / 'bin' / source.name)
    prior = ROOT / ('verification-v03.json' if VERSION == '0.3.1' else 'verification-v031.json')
    prior_version = '0.3.0' if VERSION == '0.3.1' else '0.3.1'
    if not prior.exists():
        old = read('verification.json')
        assert old['version'] == prior_version
        prior.write_text(json.dumps(old, indent=2) + '\n', encoding='utf-8')
    assert json.loads(prior.read_text(encoding='utf-8'))['version'] == prior_version
    audit = read(f'benchmarks/perf-{TAG}-audit.json')
    stress_keys = ['baseline', 'buffered_trial', 'final', 'interleaved', 'analytics'] if VERSION == '0.3.1' else ['final', 'interleaved', 'analytics']
    cases = sum(audit[k]['completed_cases'] for k in stress_keys)
    offered = sum(audit[k]['offered_operations'] for k in stress_keys)
    assert (cases, offered) == ((84, 1400400) if VERSION == '0.3.1' else (35, 620000))
    if VERSION == '0.3.1':
        assert audit['invalid_build_comparison']['excluded']
    recovery = read(f'benchmarks/perf-{TAG}-recovery.json')
    assert len(recovery['cycles']) == 24
    assert all(c['sum_and_full_scrub_passed'] and c['retry_deduplication_passed'] for c in recovery['cycles'])
    assert recovery['binary_sha256'] == build['bridge_sha256'] and recovery['sql_binary_sha256'] == build['cli_sha256']
    demo = read(f'portfolio/live-pipeline-{TAG}-results.json')
    assert demo['exact_sql_cases_against_duckdb'] == 42
    assert demo['replayed_sources_not_duplicated'] and demo['changed_content_rejected']
    assert demo['engine_version'] == VERSION and demo['binary_sha256'] == build['bridge_sha256']
    compatibility = read(f'benchmarks/format-{TAG}.json')
    assert compatibility['legacy_catalog_read'] and compatibility['older_binary_rejects_new_catalog']
    assert compatibility['binary_sha256'] == build['bridge_sha256']
    capabilities = read(f'benchmarks/capability-{TAG}.json')
    assert len(capabilities['engines']) == (6 if VERSION == '0.3.1' else 2) and capabilities['engines'][0]['version'] == VERSION
    assert capabilities['binary_sha256'] == build['bridge_sha256'] and capabilities['sql_binary_sha256'] == build['cli_sha256']
    recheck = read(f'benchmarks/release-recheck-{TAG}.json')
    assert recheck['all_retained_results_match'] and recheck['binary_sha256'] == build['cli_sha256']
    baseline = read(f'benchmarks/baseline-{BASELINE_VERSION}-provenance.json')
    for name, digest in baseline['core_source_sha256'].items():
        assert sha((ROOT / 'benchmarks' / f'baseline-{BASELINE_VERSION}-source' / name).read_bytes()) == digest, name
    for name, digest in baseline['baseline_binary_sha256'].items():
        assert sha((ROOT / 'bin' / f'baseline-{BASELINE_VERSION}' / name).read_bytes()) == digest, name
    if VERSION == '0.3.2':
        profiled = baseline['profiled_baseline']
        assert sha((ROOT / 'bin' / 'baseline-0.3.1' / 'scan-profile.exe').read_bytes()) == profiled['binary_sha256']
        for name, digest in profiled['source_sha256'].items():
            assert sha((ROOT / 'benchmarks' / 'profile-baseline-031-source' / name).read_bytes()) == digest, name
    if VERSION == '0.3.1':
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
            'fault_model': recovery['fault_model'], 'report': f'benchmarks/perf-{TAG}-recovery.json'},
        'hard_boundaries': recovery['boundaries'], 'live_pipeline': demo,
        'format_compatibility': compatibility, 'baseline_provenance': baseline,
        'executed_capabilities': {'engines': len(capabilities['engines']), 'report': f'benchmarks/capability-{TAG}.json',
            'previous_six_engine_report': 'benchmarks/capability-031.json', 'archive_transactional_parity': False},
        'stress_bridge': {'test_only': True, 'binary_sha256': build['bridge_sha256'],
                         'concurrency': 'immutable LiveArchive snapshots; one bounded durable group writer'},
        'reference_servers_stopped': True,
        'qualification_limits': [
            'shared desktop and unequal client interfaces; short repeated runs are descriptive',
            'latency percentiles include successes only; all failed/unexecuted offers reported separately',
            'all overload loss and slow service cases disclosed; generic scan gains do not qualify durable tails',
            'BIGINT aggregate subset; no raw projection, joins, updates/deletes or SQL transactions in Archive',
            'no native Arrow/Parquet SDK; Parquet demo reads sources through DuckDB',
            'receipt capacity correctness tested at 100000 IDs; full-ledger unique-write endurance unqualified',
            'queue/cache budgets exclude caller allocations, active pinned pages and OS caches',
            'backup/retention/orphan cleanup, upgrades and disk exhaustion remain unqualified',
            'physical power loss, Windows directory-entry durability and Linux execution unqualified',
            'no distributed scale, replication or TAOBench/Facebook-scale qualification']}
    if VERSION == '0.3.2':
        proof['historical_0_3_1_proof'] = 'verification-v031.json'
        differential = read('benchmarks/archive-verification-032.json')
        assert differential['binary_sha256'] == build['cli_sha256']
        assert differential['queries_checked_against_each_reference'] == 500
        assert all(q['passed'] for q in differential['queries'])
        proof['current_archive_differential'] = {'queries_checked_against_each_reference': 500,
            'references': differential['references'], 'report': 'benchmarks/archive-verification-032.json'}
        proof['service_qualification'] = 'failed; retain all mixed/overload losses and publication stalls'
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
        extracted = WORKSPACE / 'work' / f'package-smoke-{TAG}-{time.time_ns()}'
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
        if VERSION == '0.3.2':
            # The scan change keeps CAT3/SEG2 and its receipt ledger readable by
            # the preceding release, rather than merely accepting legacy CAT2.
            previous = Engine('kestrel', extracted / 'fresh-store', 0,
                              ROOT / 'bin' / 'baseline-0.3.1' / 'kestrel-stress.exe', {}, existing=True)
            try:
                assert previous.version == '0.3.1'
                connection = previous.connect()
                assert connection.call(request)['duplicate']
                assert connection.query('SELECT COUNT(*), SUM(value) FROM events') == [[1002, -486]]
                assert connection.call({'op': 'verify'})['verified_bytes'] == 1002 * 24
                connection.close()
            finally:
                previous.finish()
    digest = sha(PACKAGE.read_bytes())
    PACKAGE.with_suffix('.zip.sha256').write_text(f'{digest}  {PACKAGE.name}\n', encoding='utf-8')
    result = {'package': str(PACKAGE), 'bytes': PACKAGE.stat().st_size, 'sha256': digest,
              'payload_files': len(manifest), 'zip_integrity': 'passed', 'all_file_hashes': 'passed',
              'internal_document_links': 'passed', 'python_syntax': 'passed',
              'packaged_executable_replay_reopen_scrub_smokes': 'passed', 'reference_servers_stopped': True,
              'current_stress_cases': cases, 'current_offered_requests': offered,
              'historical_0_3_proof_preserved': True, 'historical_0_2_proof_preserved': True,
              'historical_invalid_build_probe_excluded': True}
    if VERSION == '0.3.2':
        result['preceding_cat3_binary_read_retry_and_scrub'] = 'passed'
        result['service_qualification'] = 'failed; experimental scan candidate, publication stalls unresolved'
    (ROOT.parent / f'kestrel-sql-{VERSION}-package-check.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
