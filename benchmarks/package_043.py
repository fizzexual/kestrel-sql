"""Package fused dense sums only after comparisons, guards and recovery pass."""
import ast
import hashlib
import json
import re
import shutil
import subprocess
import time
import tomllib
import zipfile
from pathlib import Path
from stress_compare import Engine
from source_pipeline_demo import Adapter
from group_compare_043 import Probe

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
VERSION = '0.3.13'
def read(relative): return json.loads((ROOT / relative).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def smoke(extracted):
    binaries = extracted / ROOT.name / 'bin'
    bridge = binaries / 'kestrel-stress.exe'
    previous = binaries / 'baseline-0.3.12/kestrel-stress.exe'
    for delay in [0, 2, 8, 20]:
        directory = extracted / f'group-store-{delay}'
        request = {'op': 'append', 'id': 'smoke:known', 'data': [[3, 7, 2], [1, -3, 2], [2, 11, 3], [0, 2, 3]]}
        query = 'SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device'
        engine = Engine('kestrel', directory, 0, bridge, {}, bridge_args=(delay, 1))
        try:
            assert engine.version == VERSION
            connection = engine.connect(); receipt = connection.call(request)
            assert not receipt['duplicate'] and connection.call(request)['generation'] == receipt['generation']
            assert connection.query(query) == [[2, 2, 4], [3, 2, 13]]
            assert connection.query('SELECT COUNT(*), SUM(value) FROM events WHERE value >= 0 AND ts >= 1') == [[2, 18]]
            assert connection.query('SELECT device, COUNT(*), SUM(value) FROM events WHERE value >= 0 AND ts < 3 GROUP BY device ORDER BY device') == [[3, 2, 13]]
            assert connection.call({'op': 'verify'})['verified_bytes'] == 96
            connection.close(); engine.reopen(); connection = engine.connect()
            assert connection.call(request)['duplicate'] and connection.query(query) == [[2, 2, 4], [3, 2, 13]]
            assert connection.call({'op': 'stats'})['ingest']['group_delay_ns'] == delay * 1_000_000
            connection.close()
        finally: engine.finish()
        old = Engine('kestrel', directory, 0, previous, {}, existing=True)
        try:
            assert old.version == '0.3.12'
            connection = old.connect()
            assert connection.call(request)['duplicate']
            assert not connection.call({'op': 'append', 'id': 'smoke:old', 'data': [[5, 9, 2]]})['duplicate']
            assert connection.query(query) == [[2, 3, 13], [3, 2, 13]]
            connection.close()
        finally: old.finish()
        engine = Engine('kestrel', directory, 0, bridge, {}, existing=True)
        try:
            connection = engine.connect()
            assert connection.call(request)['generation'] == receipt['generation']
            assert connection.query(query) == [[2, 3, 13], [3, 2, 13]]
            assert connection.call({'op': 'verify'})['verified_bytes'] == 120
            stats = connection.call({'op': 'stats'})['ingest']
            assert not stats['retry_index_enabled'] and stats['group_delay_ns'] == 0
            connection.close()
        finally: engine.finish()
    source_dir = extracted / 'source-sdk'
    archive = source_dir / 'archive'
    demo = json.loads(subprocess.check_output([str(binaries / 'test-only/source-ingest-demo-043.exe'), str(archive)], text=True, timeout=30))
    assert demo['version'] == VERSION and demo['passed'] and demo['result']['rows'] == [[3, 37]]
    old = Engine('kestrel', source_dir, 0, previous, {}, existing=True)
    try:
        connection = old.connect()
        assert not connection.call({'op': 'append', 'id': 'ordinary:old', 'data': [[2, 1, 0]]})['duplicate']
        connection.close()
    finally: old.finish()
    adapter = Adapter(binaries / 'test-only/source-pipeline-043.exe', archive)
    try:
        assert adapter.call(op='stats')['version'] == VERSION
        assert adapter.call(op='position', source='orders:partition0')['next_offset'] == 210
        assert adapter.call(op='query', sql='SELECT COUNT(*), SUM(value) FROM events') == [[4, 38]]
        assert adapter.call(op='verify') == 96
    finally: adapter.finish()
    probe = Probe(binaries / 'group-probe.exe', archive, extracted / 'probe.stderr.log')
    try:
        result = probe.call(op='query', sql='SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device', repeats=1)
        assert probe.header['version'] == VERSION and result['result']['plan'] == 'streamed-dense-group'
        assert sum(row[1] for row in result['result']['rows']) == 4
        assert probe.call(op='verify')['verified_bytes'] == 96
    finally: probe.finish()
    # Verify signed sparse i128 groups through the actual packaged bridge and
    # preceding reader, including an exact durable retry after reopen.
    directory = extracted / 'sparse-wide'
    request = {'op': 'append', 'id': 'smoke:sparse:wide', 'data':
        [[i * 2 + turn, value, key] for i in range(3) for turn, (key, value) in
         enumerate([(-(2**63), 2**63-1), (2**63-1, -(2**63))])]}
    sql = 'SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device'
    expected = [[-(2**63), 3, (2**63-1)*3], [2**63-1, 3, -(2**63)*3]]
    owner = Engine('kestrel', directory, 0, bridge, {})
    try:
        connection = owner.connect(); receipt = connection.call(request)
        assert not receipt['duplicate'] and connection.query(sql) == expected
        connection.close()
    finally: owner.finish()
    for binary in [previous, bridge]:
        owner = Engine('kestrel', directory, 0, binary, {}, existing=True)
        try:
            connection = owner.connect(); replay = connection.call(request)
            assert replay['duplicate'] and replay['generation'] == receipt['generation']
            assert connection.query(sql) == expected and connection.call({'op':'verify'})['verified_bytes'] == 144
            connection.close()
        finally: owner.finish()


    # Exercise the promoted medium cache through extracted current and older bridges.
    directory = extracted / 'medium-wide'
    keys = [-(2**63),2**63-1,*[j*1000003-2501 for j in range(5001)]]
    request = {'op':'append','id':'smoke:medium:wide','data':
        [[i, (2**63-1) if (i%5003)%2==0 else -(2**63),keys[i%5003]] for i in range(15009)]}
    expected = sorted([[key,3,((2**63-1) if j%2==0 else -(2**63))*3] for j,key in enumerate(keys)])
    requests=[{'op':'append','id':f'smoke:medium:wide:{lo}','data':request['data'][lo:lo+5003]} for lo in range(0,len(request['data']),5003)]
    owner = Engine('kestrel',directory,0,bridge,{})
    try:
        connection=owner.connect(); known=[]
        for request in requests:
            receipt=connection.call(request);assert not receipt['duplicate']
            known.append((request,receipt['generation']))
        assert connection.query(sql)==expected
        assert connection.call({'op':'verify'})['verified_bytes']==360216
        connection.close()
    finally: owner.finish()
    for binary in [previous,bridge]:
        owner=Engine('kestrel',directory,0,binary,{},existing=True)
        try:
            connection=owner.connect()
            for request,generation in known:
                replay=connection.call(request)
                assert replay['duplicate'] and replay['generation']==generation
            actual=connection.query(sql)
            assert actual==expected and all(type(row[2]) is int for row in actual)
            assert connection.call({'op':'verify'})['verified_bytes']==360216
            connection.close()
        finally: owner.finish()


    # Verify the fused dense plan on both signed boundary domains in the ZIP,
    # preserving exact wide sums and receipt generations with the older reader.
    dense_sql='SELECT device, COUNT(*), SUM(value), AVG(value), SUM(value) FROM events GROUP BY device ORDER BY device'
    for label,base in [('min',-(2**63)),('max',2**63-1-136)]:
        directory=extracted/('dense-wide-'+label)
        data=[[i,(2**63-1) if (i*17%137)%2==0 else -(2**63),base+i*17%137] for i in range(411)]
        expected=[[base+k,3,((2**63-1) if k%2==0 else -(2**63))*3,
            float(((2**63-1) if k%2==0 else -(2**63))*3)/3,
            ((2**63-1) if k%2==0 else -(2**63))*3] for k in range(137)]
        owner=Engine('kestrel',directory,0,bridge,{})
        known=[]
        try:
            connection=owner.connect()
            for lo in range(0,len(data),137):
                request={'op':'append','id':f'smoke:dense:{label}:{lo}','data':data[lo:lo+137]}
                receipt=connection.call(request);assert not receipt['duplicate']
                known.append((request,receipt['generation']))
            result=connection.call({'op':'query','sql':dense_sql})
            assert result['plan']=='streamed-dense-group' and result['rows']==expected
            assert all(type(row[2]) is int and type(row[4]) is int for row in result['rows'])
            connection.close()
        finally:owner.finish()
        for binary in [previous,bridge]:
            owner=Engine('kestrel',directory,0,binary,{},existing=True)
            try:
                connection=owner.connect()
                for request,generation in known:
                    replay=connection.call(request)
                    assert replay['duplicate'] and replay['generation']==generation
                assert connection.query(dense_sql)==expected
                assert connection.call({'op':'verify'})['verified_bytes']==411*24
                connection.close()
            finally:owner.finish()


def main():
    package = ROOT.parent / f'kestrel-sql-{VERSION}.zip'
    assert not package.exists(), 'Never replace a completed release archive'
    assert tomllib.loads((ROOT / 'Cargo.toml').read_text())['package']['version'] == VERSION
    build = read('benchmarks/rust-checks-043.json'); audit = read('benchmarks/dense-043-audit.json')
    assert build['rust_tests'] == {'debug': 73, 'release': 73, 'passed': True}
    assert audit['source_sha256'] == build['source_sha256'] and audit['current_timed_query_samples'] == 5940
    assert audit['no_compilation_overlap_with_timed_database_work'] and audit['storage_publication_live_source_prefix_reader_and_sparse_helpers_unchanged']
    for relative, digest in build['source_sha256'].items(): assert sha(ROOT / relative) == digest
    base = read('benchmarks/baseline-0.3.12-provenance.json')
    assert sha(ROOT.parent / 'kestrel-sql-0.3.12.zip') == base['archive_sha256']
    for relative, digest in base['baseline_binary_sha256'].items(): assert sha(ROOT / 'bin/baseline-0.3.12' / relative) == digest
    prior = read('verification-v042.json'); assert prior['version'] == '0.3.12'
    fields = {'kestrel': 'cli_sha256', 'kestrel-stress': 'bridge_sha256', 'group-probe': 'group_probe_sha256',
        'scan-profile': 'scan_probe_sha256', 'performance-probe': 'probe_sha256', 'publication-probe': 'publication_probe_sha256', 'receipt-seed': 'receipt_seed_sha256'}
    for name, field in fields.items():
        source = WORK / 'perf-043/candidate' / (name + '.exe')
        assert sha(source) == build[field]
        assert b'KESTREL_FAULT_POINT' not in source.read_bytes() and b'KESTREL_LIVE_PAUSE' not in source.read_bytes()
        shutil.copy2(source, ROOT / 'bin' / source.name)
    test_only = ROOT / 'bin/test-only'; test_only.mkdir(exist_ok=True)
    for name, field in [('publication_fault_probe', 'fault_driver_sha256'), ('live_retry_probe', 'live_retry_driver_sha256'), ('source_fault_probe', 'source_fault_driver_sha256')]:
        source = WORK / 'kestrel-043-fault-build/release/examples' / (name + '.exe')
        assert sha(source) == build[field]
        shutil.copy2(source, test_only / (name.replace('_', '-') + '-043.exe'))
    adapter = read('benchmarks/source-043-typed-adapter-build.json')
    source = Path(adapter['binary_path']); assert sha(source) == adapter['binary_sha256']
    shutil.copy2(source, test_only / 'source-pipeline-043.exe')
    demo = WORK / 'kestrel-043-build/release/examples/source_ingest.exe'
    shutil.copy2(demo, test_only / 'source-ingest-demo-043.exe')
    proof = {**build, 'status': 'experimental fused dense shared SUM/AVG reduction; production qualification incomplete',
        'current_dense_reduction_audit': audit, 'prior_release_proof': 'verification-v042.json', 'baseline_provenance': base,
        'storage_format': prior['storage_format'], 'source_contract': prior['source_contract'],
        'default_group_delay_ms': 0, 'default_retry_index_enabled': False,
        'service_qualification': audit['service_qualification'], 'reference_servers_stopped': True,
        'qualification_limits': prior['qualification_limits'] + audit['limits'],
        'current_evidence': {'report': 'PERFORMANCE_043.md', 'dense_reduction': 'benchmarks/dense-043-audit.json',
            'correctness_order': 'benchmarks/correctness-043-run-order.json'},
        'historical_evidence': 'BENCHMARK_HISTORY.md', 'supported_binaries_contain_no_fault_hooks': True}
    (ROOT / 'verification.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    for path in ROOT.rglob('*'):
        if not path.is_file() or {'.git', 'target', '__pycache__'}.intersection(path.relative_to(ROOT).parts): continue
        if path.suffix == '.py': ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        elif path.suffix == '.json': json.loads(path.read_text(encoding='utf-8'))
        elif path.suffix == '.md':
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
                if '://' not in target and not target.startswith('#'): assert (path.parent / target.split('#')[0]).exists(), (path, target)
    for dependency in tomllib.loads((ROOT / 'Cargo.lock').read_text())['package']:
        if dependency['name'] != 'kestrel-sql': assert (ROOT / 'licenses' / f"{dependency['name']}-{dependency['version']}").is_dir()
    replies = [json.loads(line) for line in subprocess.check_output([str(ROOT / 'bin/kestrel.exe'), '--file', str(ROOT / 'examples/live_metrics.sql')], text=True).splitlines()]
    assert len(replies) == 8 and all(r['ok'] for r in replies)
    files = sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name != 'MANIFEST.sha256' and not {'.git', 'target', '__pycache__'}.intersection(p.relative_to(ROOT).parts))
    manifest = [(sha(path), path.relative_to(ROOT).as_posix()) for path in files]
    (ROOT / 'MANIFEST.sha256').write_text(''.join(f'{digest}  {name}\n' for digest, name in manifest), encoding='utf-8')
    files.append(ROOT / 'MANIFEST.sha256')
    with zipfile.ZipFile(package, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9, strict_timestamps=False) as bundle:
        for path in files: bundle.write(path, (Path(ROOT.name) / path.relative_to(ROOT)).as_posix())
    with zipfile.ZipFile(package) as bundle:
        assert bundle.testzip() is None
        for digest, name in manifest: assert hashlib.sha256(bundle.read(ROOT.name + '/' + name)).hexdigest() == digest
        extracted = WORK / f'package-smoke-043-{time.time_ns()}'; extracted.mkdir()
        for name in ['kestrel.exe', 'kestrel-stress.exe', 'group-probe.exe', 'baseline-0.3.12/kestrel-stress.exe',
            'test-only/source-pipeline-043.exe', 'test-only/source-ingest-demo-043.exe']:
            bundle.extract(ROOT.name + '/bin/' + name, extracted)
        smoke(extracted)
    digest = sha(package)
    package.with_suffix('.zip.sha256').write_text(f'{digest}  {package.name}\n', encoding='utf-8')
    result = {'version': VERSION, 'package': str(package), 'bytes': package.stat().st_size, 'sha256': digest,
        'payload_files': len(manifest), 'all_file_hashes_and_zip_crc': 'passed', 'document_links_and_syntax': 'passed',
        'packaged_grouping_and_0_2_8_20ms_retries_reopen_scrub': 'passed', 'preceding_0_3_12_read_write_roundtrip': 'passed',
        'packaged_source_sdk_and_older_ordinary_writer_roundtrip': 'passed', 'current_tests_each_mode': 73,
        'packaged_sparse_signed_wide_groups_and_preceding_reader': 'passed',
        'packaged_first_filter_and_sorted_bounds': 'passed',
        'packaged_medium_signed_wide_groups_retry_reopen_and_preceding_reader':'passed',
        'packaged_dense_signed_wide_shared_sum_avg_retry_reopen_and_preceding_reader':'passed',
        'current_core_comparison_cases': 108, 'current_core_timed_query_samples': 5940,
        'historical_packages_preserved': True, 'reference_servers_stopped': True, 'qualification': 'experimental, local only'}
    (ROOT.parent / f'kestrel-sql-{VERSION}-package-check.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__': main()
