"""Current source-checkpoint gates, preserved 0.3.6 evidence, immutable package."""
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
from source_pipeline_demo import Adapter

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent.parent
VERSION = '0.3.7'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(relative): return json.loads((ROOT / relative).read_text(encoding='utf-8'))


def smoke(extracted):
    binaries = extracted / ROOT.name / 'bin'
    bridge = binaries / 'kestrel-stress.exe'
    old_bridge = binaries / 'baseline-0.3.6/kestrel-stress.exe'
    assert '--archive' in subprocess.check_output([str(binaries / 'kestrel.exe'), '--help'], text=True)
    default = Engine('kestrel', extracted / 'default-store', 0, bridge, {})
    try:
        connection = default.connect()
        request = {'op': 'append', 'id': 'default:known', 'data': [[1, 2, 3]]}
        assert not connection.call(request)['duplicate'] and connection.call(request)['duplicate']
        stats = connection.call({'op': 'stats'})['ingest']
        assert not stats['retry_index_enabled']
        assert stats['retry_index_ids'] == stats['retry_index_logical_bytes'] == stats['fast_retry_hits'] == stats['prepared_retry_hits'] == 0
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
            connection.close(); engine.reopen(); connection = engine.connect()
            replay = connection.call(first)
            assert replay['duplicate'] and replay['generation'] == receipt['generation']
            assert connection.call({'op': 'verify'})['verified_bytes'] == 1002 * 24
            connection.close()
        finally: engine.finish()
        previous = Engine('kestrel', directory, 0, old_bridge, {}, existing=True)
        try:
            assert previous.version == '0.3.6'
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
    directory = extracted / 'source-sdk-store'
    archive = directory / 'archive'
    demo = json.loads(subprocess.check_output([str(binaries / 'test-only/source-ingest-demo-037.exe'), str(archive)], text=True, timeout=20))
    assert demo['version'] == VERSION and demo['passed'] and demo['result']['rows'] == [[3, 37]]
    assert demo['position']['next_offset'] == 210 and demo['position']['committed_batches'] == 2
    # Older generic writers may add ordinary IDs, but must not write reserved source IDs.
    previous = Engine('kestrel', directory, 0, old_bridge, {}, existing=True)
    try:
        connection = previous.connect()
        assert previous.version == '0.3.6' and connection.query('SELECT COUNT(*), SUM(value) FROM events') == [[3, 37]]
        assert not connection.call({'op': 'append', 'id': 'ordinary:after-source', 'data': [[2, 1, 0]]})['duplicate']
        assert connection.call({'op': 'verify'})['verified_bytes'] == 96
        connection.close()
    finally: previous.finish()
    adapter = Adapter(binaries / 'test-only/source-pipeline-037.exe', archive)
    try:
        assert adapter.call(op='stats')['version'] == VERSION
        position = adapter.call(op='position', source='orders:partition0')
        assert position['next_offset'] == 210 and position['committed_batches'] == 2
        assert adapter.call(op='query', sql='SELECT COUNT(*), SUM(value) FROM events') == [[4, 38]]
        assert adapter.call(op='verify') == 96
    finally: adapter.finish()


def main():
    package = ROOT.parent / f'kestrel-sql-{VERSION}.zip'
    assert not package.exists(), 'Never replace a release artifact'
    assert tomllib.loads((ROOT / 'Cargo.toml').read_text())['package']['version'] == VERSION
    for port in [55439, 53329, 53319, 33060]:
        with socket.socket() as connection:
            connection.settimeout(.5)
            assert connection.connect_ex(('127.0.0.1', port)) != 0
    build = read('benchmarks/rust-checks-037.json')
    assert build['version'] == VERSION and build['rust_tests'] == {'debug': 55, 'release': 55, 'passed': True}
    assert build['format_check'] == build['clippy_warnings_as_errors'] == build['feature_clippy_warnings_as_errors'] == 'passed'
    for relative, digest in build['source_sha256'].items(): assert sha(ROOT / relative) == digest, relative
    audit = read('benchmarks/source-037-audit.json')
    assert audit['version'] == VERSION and audit['source_sha256'] == build['source_sha256']
    assert (audit['sequential_cases'], audit['timed_new_commits'], audit['timed_known_retries']) == (18, 1728, 18000)
    assert (audit['source_publication_fault_cases'], audit['source_process_kill_cycles'], audit['parquet_rows'], audit['parquet_batches'], audit['parquet_exact_sql_cases']) == (14, 8, 30000, 300, 42)
    assert audit['no_compilation_overlap_with_timed_database_work'] and audit['identical_catalog_bytes_for_matched_ids'] and audit['current_sdk_demo_passed']
    assert audit['archive_storage_query_publication_byte_identical_except_readonly_helpers']
    base = read('benchmarks/baseline-0.3.6-provenance.json')
    assert sha(ROOT.parent / 'kestrel-sql-0.3.6.zip') == base['archive_sha256']
    for relative, digest in base['core_source_sha256'].items(): assert sha(ROOT / 'benchmarks/baseline-0.3.6-source' / relative) == digest
    for relative, digest in base['baseline_binary_sha256'].items(): assert sha(ROOT / 'bin/baseline-0.3.6' / relative) == digest
    prior = read('verification-v036.json'); assert prior['version'] == '0.3.6'
    fields = {'kestrel': 'cli_sha256', 'kestrel-stress': 'bridge_sha256', 'performance-probe': 'probe_sha256',
        'scan-profile': 'scan_probe_sha256', 'publication-probe': 'publication_probe_sha256', 'receipt-seed': 'receipt_seed_sha256'}
    for name, field in fields.items():
        source = WORKSPACE / 'work/perf-037/candidate' / (name + '.exe')
        assert sha(source) == build[field]
        data = source.read_bytes()
        assert b'KESTREL_LIVE_PAUSE' not in data and b'KESTREL_FAULT_POINT' not in data
        shutil.copy2(source, ROOT / 'bin' / source.name)
    test_directory = ROOT / 'bin/test-only'; test_directory.mkdir(exist_ok=True)
    for name, field in [('publication_fault_probe', 'fault_driver_sha256'), ('live_retry_probe', 'live_retry_driver_sha256'), ('source_fault_probe', 'source_fault_driver_sha256')]:
        source = WORKSPACE / 'work/kestrel-037-fault-build/release/examples' / (name + '.exe')
        assert sha(source) == build[field]
        shutil.copy2(source, test_directory / (name.replace('_', '-') + '-037.exe'))
    comparison = read('benchmarks/source-037-comparison.json')
    assert sha(ROOT / 'benchmarks/source_publication.rs') == comparison['probe_source_sha256']
    assert sha(ROOT / 'benchmarks/source_pipeline_probe.rs') == comparison['adapter_source_sha256']
    for variant, tag in [('baseline', '036'), ('candidate', '037')]:
        record = comparison['builds'][variant]
        source = Path(record['binary_path'])
        assert sha(source) == record['binary_sha256']
        assert b'KESTREL_FAULT_POINT' not in source.read_bytes() and b'KESTREL_LIVE_PAUSE' not in source.read_bytes()
        shutil.copy2(source, test_directory / f'source-publication-{tag}.exe')
    demo = read('benchmarks/source-037-demo.json')
    for source, digest, name in [(Path(comparison['adapter_binary_path']), comparison['adapter_binary_sha256'], 'source-pipeline-037.exe'),
            (Path(demo['binary_path']), demo['binary_sha256'], 'source-ingest-demo-037.exe')]:
        assert sha(source) == digest
        assert b'KESTREL_FAULT_POINT' not in source.read_bytes() and b'KESTREL_LIVE_PAUSE' not in source.read_bytes()
        shutil.copy2(source, test_directory / name)
    proof = {**build, 'status': 'experimental atomic archive-local source checkpoints; production qualification incomplete',
        'service_qualification': audit['service_qualification'], 'current_source_audit': audit,
        'prior_release_proof': 'verification-v036.json', 'baseline_provenance': base,
        'storage_format': {'catalog': 'CAT4', 'segment': 'SEG2', 'unchanged_from': '0.3.3'},
        'default_group_delay_ms': 0, 'default_retry_index_enabled': False, 'reference_servers_stopped': True,
        'source_contract': {'reserved_receipt_prefix': 'ksrc1:', 'max_sources': 4096, 'global_receipt_limit': 100000,
            'nonempty_output_required': True, 'additional_checkpoint_publications': 0, 'lease_fencing': False,
            'source_reset': False, 'distributed_atomicity': False, 'automatic_retention': False},
        'current_evidence': {'publication_comparison': 'benchmarks/source-037-comparison.json',
            'source_publication_failures_and_kills': 'benchmarks/source-037-faults.json',
            'parquet_pipeline': 'portfolio/source-pipeline-037-results.json', 'sdk_demo': 'benchmarks/source-037-demo.json',
            'correctness_order': 'benchmarks/correctness-037-run-order.json',
            'initial_runner_failure': 'benchmarks/source-037-initial-runner-failure.json'},
        'historical_evidence': audit['historical_evidence'],
        'test_only_drivers': 'publication/live-retry/source-fault *-037.exe contain fault hooks; source-pipeline/source-ingest-demo contain no hooks; supported CLI/bridge contain no hooks',
        'qualification_limits': prior['qualification_limits'] + ['SourceArchive coordinates one archive output and source interval; external source/other sinks are not transactional',
            'source receipt history cannot advance empty output, reset sources, fence stale consumers or evict receipts',
            'source publication comparison uses sequential matched canonical IDs; no causal durable-write speed improvement or current req/s qualification',
            'older/generic writers must not publish reserved source IDs; format interoperability does not enforce typed source semantics']}
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
    with zipfile.ZipFile(package, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=False) as bundle:
        for path in files: bundle.write(path, (Path(ROOT.name) / path.relative_to(ROOT)).as_posix())
    with zipfile.ZipFile(package) as bundle:
        assert bundle.testzip() is None and len(bundle.namelist()) == len(files)
        for digest, name in manifest: assert hashlib.sha256(bundle.read(ROOT.name + '/' + name)).hexdigest() == digest, name
        extracted = WORKSPACE / 'work' / f'package-smoke-037-{time.time_ns()}'; extracted.mkdir()
        for name in ['kestrel.exe', 'kestrel-stress.exe', 'baseline-0.3.6/kestrel-stress.exe',
                'test-only/source-ingest-demo-037.exe', 'test-only/source-pipeline-037.exe']:
            bundle.extract(ROOT.name + '/bin/' + name, extracted)
        smoke(extracted)
    digest = sha(package)
    package.with_suffix('.zip.sha256').write_text(f'{digest}  {package.name}\n', encoding='utf-8')
    result = {'package': str(package), 'bytes': package.stat().st_size, 'sha256': digest, 'payload_files': len(manifest),
        'zip_integrity': 'passed', 'all_file_hashes': 'passed', 'internal_document_links': 'passed', 'python_syntax': 'passed',
        'packaged_default_and_0_2_8_20ms_replay_reopen_scrub': 'passed', 'preceding_0_3_6_read_write_roundtrip': 'passed',
        'packaged_source_sdk_and_older_ordinary_writer_roundtrip': 'passed', 'current_rust_tests_each_mode': 55,
        'current_sequential_cases': 18, 'current_timed_new_commits': 1728, 'current_timed_known_retries': 18000,
        'current_source_publication_fault_cases': 14, 'current_source_process_kill_cycles': 8,
        'current_parquet_rows': 30000, 'current_parquet_batches': 300, 'current_parquet_exact_sql_cases': 42,
        'historical_evidence': audit['historical_evidence'], 'reference_servers_stopped': True, 'historical_packages_preserved': True,
        'service_qualification': audit['service_qualification']}
    (ROOT.parent / f'kestrel-sql-{VERSION}-package-check.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
