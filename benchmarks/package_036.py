"""Explicit current gates, preserved 0.3.5 baseline, immutable package and smokes."""
import ast
import hashlib
import json
import re
import shutil
import socket
import subprocess
import time
import tomllib
import zipfile
from pathlib import Path
from stress_compare import Engine

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent.parent
VERSION = '0.3.6'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(relative): return json.loads((ROOT / relative).read_text(encoding='utf-8'))


def smoke(extracted):
    binaries = extracted / ROOT.name / 'bin'
    bridge = binaries / 'kestrel-stress.exe'
    assert '--archive' in subprocess.check_output([str(binaries / 'kestrel.exe'), '--help'], text=True)
    default = Engine('kestrel', extracted / 'default-store', 0, bridge, {})
    try:
        connection = default.connect()
        request = {'op': 'append', 'id': 'default:known', 'data': [[1, 2, 3]]}
        assert not connection.call(request)['duplicate'] and connection.call(request)['duplicate']
        stats = connection.call({'op': 'stats'})['ingest']
        assert not stats['retry_index_enabled'] and stats['retry_index_ids'] == stats['retry_index_logical_bytes'] == stats['fast_retry_hits'] == stats['prepared_retry_hits'] == 0
        assert stats['collected_groups'] == 2
        assert connection.call({'op': 'verify'})['verified_bytes'] == 24
        connection.close()
    finally: default.finish()
    for delay in [0, 2, 8, 20]:
        directory = extracted / f'store-{delay}'
        first = {'op': 'append', 'id': 'package:first', 'data': [[1000, 17, 2], [1001, -3, 2]]}
        second = {'op': 'append', 'id': 'package:old-writer', 'data': [[1002, 5, 3]]}
        engine = Engine('kestrel', directory, 1000, bridge, {}, bridge_args=(delay, 1))
        try:
            assert engine.version == VERSION
            connection = engine.connect()
            receipt = connection.call(first)
            assert not receipt['duplicate'] and connection.call(first)['duplicate']
            stats = connection.call({'op': 'stats'})['ingest']
            assert stats['fast_retry_hits'] == stats['retry_index_ids'] == 1
            assert not stats['writer_poisoned'] and not stats['writer_stopped']
            assert stats['group_delay_ns'] == delay * 1_000_000
            connection.close()
            engine.reopen()
            connection = engine.connect()
            replay = connection.call(first)
            assert replay['duplicate'] and replay['generation'] == receipt['generation']
            assert connection.call({'op': 'verify'})['verified_bytes'] == 1002 * 24
            connection.close()
        finally: engine.finish()
        previous = Engine('kestrel', directory, 0, ROOT / 'bin/baseline-0.3.5/kestrel-stress.exe', {}, existing=True)
        try:
            assert previous.version == '0.3.5'
            connection = previous.connect()
            replay = connection.call(first)
            assert replay['duplicate'] and replay['generation'] == receipt['generation']
            assert not connection.call(second)['duplicate']
            assert connection.query('SELECT COUNT(*), SUM(value) FROM events') == [[1003, -481]]
            assert connection.call({'op': 'verify'})['verified_bytes'] == 1003 * 24
            connection.close()
        finally: previous.finish()
        current = Engine('kestrel', directory, 0, bridge, {}, existing=True, bridge_args=(delay, 1))
        try:
            connection = current.connect()
            assert connection.call(first)['duplicate'] and connection.call(second)['duplicate']
            assert connection.call({'op': 'stats'})['ingest']['fast_retry_hits'] == 2
            assert connection.query('SELECT COUNT(*), SUM(value) FROM events') == [[1003, -481]]
            assert connection.call({'op': 'verify'})['verified_bytes'] == 1003 * 24
            connection.close()
        finally: current.finish()
    directory = extracted / 'prepared-api-store'
    subprocess.check_output([str(binaries / 'receipt-seed.exe'), str(directory), '50000', '1000000'], text=True, timeout=120)
    result = json.loads(subprocess.check_output([str(binaries / 'test-only/prepared-retry-inprocess-036.exe'), str(directory), '1', '1', 'prepared'], text=True, timeout=20))
    assert result['version'] == VERSION and result['mode'] == 'prepared'
    assert result['all_receipts_valid'] and result['no_publications_during_load'] and result['full_scrub_passed']
    assert result['ingest_after']['prepared_retry_hits'] == result['successful_calls'] > 0


def main():
    assert tomllib.loads((ROOT / 'Cargo.toml').read_text())['package']['version'] == VERSION
    for port in [55439, 53329, 53319, 33060]:
        with socket.socket() as connection:
            connection.settimeout(.5)
            assert connection.connect_ex(('127.0.0.1', port)) != 0
    build = read('benchmarks/rust-checks-036.json')
    assert build['rust_tests'] == {'debug': 45, 'release': 45, 'passed': True}
    assert build['format_check'] == build['clippy_warnings_as_errors'] == build['feature_clippy_warnings_as_errors'] == 'passed'
    for relative, digest in build['source_sha256'].items(): assert sha(ROOT / relative) == digest, relative
    audit = read('benchmarks/prepared-036-audit.json')
    assert (audit['cpu_digest_cases'], audit['embedded_retry_cases'], audit['completed_open_loop_cases'], audit['offered_operations'], audit['numpy_windows']) == (75, 30, 18, 540000, 360)
    assert (audit['prepared_fault_cases'], audit['concurrent_kill_cycles'], audit['differential_cases_each_reference']) == (15, 32, 500)
    assert audit['timed_database_workloads_no_overlap'] and audit['compilation_and_correctness_outside_timed_loads']
    assert audit['archive_storage_and_query_outside_receipt_helper_byte_identical_to_035']
    base = read('benchmarks/baseline-0.3.5-provenance.json')
    assert sha(ROOT.parent / 'kestrel-sql-0.3.5.zip') == base['archive_sha256']
    for relative, digest in base['core_source_sha256'].items(): assert sha(ROOT / 'benchmarks/baseline-0.3.5-source' / relative) == digest
    for relative, digest in base['baseline_binary_sha256'].items(): assert sha(ROOT / 'bin/baseline-0.3.5' / relative) == digest
    prior = read('verification-v035.json')
    assert prior['version'] == '0.3.5'
    fields = {'kestrel': 'cli_sha256', 'kestrel-stress': 'bridge_sha256', 'performance-probe': 'probe_sha256',
        'scan-profile': 'scan_probe_sha256', 'publication-probe': 'publication_probe_sha256', 'receipt-seed': 'receipt_seed_sha256'}
    for name, field in fields.items():
        source = WORKSPACE / 'work/perf-036/candidate' / (name + '.exe')
        assert sha(source) == build[field]
        data = source.read_bytes()
        assert b'KESTREL_LIVE_PAUSE' not in data and b'KESTREL_FAULT_POINT' not in data
        shutil.copy2(source, ROOT / 'bin' / source.name)
    test_directory = ROOT / 'bin/test-only'
    for name, field in [('publication_fault_probe', 'fault_driver_sha256'), ('live_retry_probe', 'live_retry_driver_sha256')]:
        source = WORKSPACE / 'work/kestrel-036-fault-build/release/examples' / (name + '.exe')
        assert sha(source) == build[field]
        shutil.copy2(source, test_directory / (name.replace('_', '-') + '-036.exe'))
    direct = read('benchmarks/prepared-036-direct.json')
    source = Path(direct['candidate_binary_path'])
    assert sha(source) == direct['candidate_binary_sha256']
    shutil.copy2(source, test_directory / 'prepared-retry-inprocess-036.exe')
    profile = read('benchmarks/digest-036-profile.json')
    source = Path(profile['binary_path'])
    assert sha(source) == profile['binary_sha256']
    shutil.copy2(source, test_directory / 'digest-profile-036.exe')
    proof = {**build, 'status': 'experimental immutable input reuse; production qualification incomplete',
        'service_qualification': audit['service_qualification'], 'current_prepared_audit': audit,
        'prior_release_proof': 'verification-v035.json', 'baseline_provenance': base,
        'storage_format': {'catalog': 'CAT4', 'segment': 'SEG2', 'unchanged_from': '0.3.3'},
        'default_group_delay_ms': 0, 'default_retry_index_enabled': False, 'reference_servers_stopped': True,
        'current_evidence': {'cpu_trial': 'benchmarks/digest-036-profile.json', 'embedded_retry': 'benchmarks/prepared-036-direct.json',
            'protocol_retry_control': 'benchmarks/prepared-036-retry-control.json', 'fresh_write_control': 'benchmarks/prepared-036-write-controls.json',
            'prepared_faults': 'benchmarks/prepared-036-faults.json', 'concurrent_crashes': 'benchmarks/group-036-recovery.json',
            'sql_differential': 'benchmarks/archive-036-verification.json'},
        'historical_evidence': 'Prior publication/corruption/Parquet/scale reports are preserved, not counted as fresh 0.3.6 runs',
        'test_only_drivers': 'publication/live-retry *-036.exe contain fault hooks; prepared-inprocess/digest probes contain no hooks; supported CLI/bridge contain no hooks',
        'qualification_limits': prior['qualification_limits'] + ['PreparedBatch amortizes library hashing only for immutable embedded reuse; unknown IDs copy/hash again at publication',
            'millions of confirmed retries per second ingest zero new rows; no SQL/network/write capacity claim',
            'prepared payload memory belongs to the caller; logical bytes exclude spare capacity and allocator overhead']}
    (ROOT / 'verification.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    for path in ROOT.rglob('*.py'):
        if not {'target', '__pycache__', '.git'}.intersection(path.relative_to(ROOT).parts): ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    for path in ROOT.rglob('*.json'): json.loads(path.read_text(encoding='utf-8'))
    for path in ROOT.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith('#'): assert (path.parent / target.split('#')[0]).exists(), (path, target)
    for dependency in tomllib.loads((ROOT / 'Cargo.lock').read_text())['package']:
        if dependency['name'] != 'kestrel-sql':
            directory = ROOT / 'licenses' / f"{dependency['name']}-{dependency['version']}"
            assert directory.is_dir() and any(directory.iterdir())
    replies = [json.loads(line) for line in subprocess.check_output([str(ROOT / 'bin/kestrel.exe'), '--file', str(ROOT / 'examples/live_metrics.sql')], text=True).splitlines()]
    assert len(replies) == 8 and all(r['ok'] for r in replies) and replies[2]['result']['rows'] == [[2, 30, 15.0]]
    files = sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name != 'MANIFEST.sha256' and not {'target', '__pycache__', '.git'}.intersection(p.relative_to(ROOT).parts))
    manifest = [(sha(path), path.relative_to(ROOT).as_posix()) for path in files]
    (ROOT / 'MANIFEST.sha256').write_text(''.join(f'{digest}  {name}\n' for digest, name in manifest), encoding='utf-8')
    files.append(ROOT / 'MANIFEST.sha256')
    package = ROOT.parent / f'kestrel-sql-{VERSION}.zip'
    assert not package.exists(), 'Never replace a release artifact'
    with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=False) as bundle:
        for path in files: bundle.write(path, (Path(ROOT.name) / path.relative_to(ROOT)).as_posix())
    with zipfile.ZipFile(package) as bundle:
        assert bundle.testzip() is None and len(bundle.namelist()) == len(files)
        for digest, name in manifest: assert hashlib.sha256(bundle.read(ROOT.name + '/' + name)).hexdigest() == digest, name
        extracted = WORKSPACE / 'work' / f'package-smoke-036-{time.time_ns()}'
        extracted.mkdir()
        for name in ['kestrel.exe', 'kestrel-stress.exe', 'receipt-seed.exe', 'test-only/prepared-retry-inprocess-036.exe']:
            bundle.extract(ROOT.name + '/bin/' + name, extracted)
        smoke(extracted)
    digest = sha(package)
    package.with_suffix('.zip.sha256').write_text(f'{digest}  {package.name}\n', encoding='utf-8')
    result = {'package': str(package), 'bytes': package.stat().st_size, 'sha256': digest, 'payload_files': len(manifest),
        'zip_integrity': 'passed', 'all_file_hashes': 'passed', 'internal_document_links': 'passed', 'python_syntax': 'passed',
        'packaged_default_and_0_2_8_20ms_replay_reopen_scrub': 'passed', 'preceding_0_3_5_read_write_roundtrip': 'passed',
        'packaged_prepared_api_scrub': 'passed', 'cpu_digest_cases': 75, 'embedded_retry_cases': 30,
        'current_open_loop_cases': 18, 'current_offers': 540000, 'prepared_fault_cases': 15, 'concurrent_kill_cycles': 32,
        'differential_cases_each_reference': 500, 'reference_servers_stopped': True, 'historical_packages_preserved': True,
        'service_qualification': audit['service_qualification']}
    (ROOT.parent / f'kestrel-sql-{VERSION}-package-check.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
