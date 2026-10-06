"""Package optional coalescing evidence with explicit inheritance of unchanged storage."""
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
VERSION = '0.3.4'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(relative):
    return json.loads((ROOT/relative).read_text(encoding='utf-8'))


def smoke(extracted):
    cli = extracted/ROOT.name/'bin/kestrel.exe'
    bridge = extracted/ROOT.name/'bin/kestrel-stress.exe'
    assert '--archive' in subprocess.check_output([str(cli),'--help'],text=True)
    for delay in [0,2,8,20]:
        directory = extracted/f'store-{delay}'
        engine = Engine('kestrel',directory,1000,bridge,{},bridge_args=(delay,))
        first = {'op':'append','id':'package:first','data':[[1000,17,2],[1001,-3,2]]}
        second = {'op':'append','id':'package:old-writer','data':[[1002,5,3]]}
        try:
            assert engine.version == VERSION
            connection = engine.connect()
            assert connection.query('SELECT COUNT(*), SUM(value) FROM events')==[[1000,-500]]
            receipt = connection.call(first)
            assert not receipt['duplicate'] and connection.call(first)['duplicate']
            assert connection.call({'op':'stats'})['ingest']['group_delay_ns']==delay*1_000_000
            connection.close()
            engine.reopen()
            connection = engine.connect()
            replay = connection.call(first)
            assert replay['duplicate'] and replay['generation']==receipt['generation']
            assert connection.call({'op':'verify'})['verified_bytes']==1002*24
            connection.close()
        finally:
            engine.finish()
        previous = Engine('kestrel',directory,0,ROOT/'bin/baseline-0.3.3/kestrel-stress.exe',{},existing=True)
        try:
            assert previous.version=='0.3.3'
            connection = previous.connect()
            replay = connection.call(first)
            assert replay['duplicate'] and replay['generation']==receipt['generation']
            assert not connection.call(second)['duplicate']
            assert connection.query('SELECT COUNT(*), SUM(value) FROM events')==[[1003,-481]]
            assert connection.call({'op':'verify'})['verified_bytes']==1003*24
            connection.close()
        finally:
            previous.finish()
        current = Engine('kestrel',directory,0,bridge,{},existing=True,bridge_args=(delay,))
        try:
            connection = current.connect()
            assert connection.call(first)['duplicate'] and connection.call(second)['duplicate']
            assert connection.query('SELECT COUNT(*), SUM(value) FROM events')==[[1003,-481]]
            assert connection.call({'op':'verify'})['verified_bytes']==1003*24
            connection.close()
        finally:
            current.finish()


def main():
    assert tomllib.loads((ROOT/'Cargo.toml').read_text(encoding='utf-8'))['package']['version']==VERSION
    for port in [55439,53329,53319,33060]:
        with socket.socket() as connection:
            connection.settimeout(.5)
            assert connection.connect_ex(('127.0.0.1',port)) != 0
    build = read('benchmarks/rust-checks-034.json')
    assert build['rust_tests']=={'debug':38,'release':38,'passed':True}
    assert build['format_check']==build['clippy_warnings_as_errors']=='passed'
    for relative,digest in build['source_sha256'].items():
        assert sha(ROOT/relative)==digest,relative
    audit = read('benchmarks/perf-034-audit.json')
    assert (audit['completed_cases'],audit['offered_operations'])==(59,1_936_800)
    assert audit['concurrent_kill_cycles_passed']==32 and audit['delayed_parquet_pipeline_exact_sql_cases']==42
    order = read('benchmarks/perf-034-run-order.json')
    assert len(order)==4 and all(record['returncode']==0 for record in order)
    for record in order:
        assert record['started_at_utc']<record['completed_at_utc']
        for relative,digest in record['harness_sha256'].items():
            assert sha(ROOT/'benchmarks'/relative)==digest,relative
    assert all(left['completed_at_utc']<=right['started_at_utc'] for left,right in zip(order,order[1:]))
    base = read('benchmarks/baseline-0.3.3-provenance.json')
    assert sha(ROOT.parent/'kestrel-sql-0.3.3.zip')==base['archive_sha256']
    for relative,digest in base['core_source_sha256'].items():
        assert sha(ROOT/'benchmarks/baseline-0.3.3-source'/relative)==digest,relative
    for relative,digest in base['baseline_binary_sha256'].items():
        assert sha(ROOT/'bin/baseline-0.3.3'/relative)==digest,relative
    prior_path = ROOT/'verification-v033.json'
    if not prior_path.exists():
        prior = read('verification.json')
        assert prior['version']=='0.3.3'
        shutil.copy2(ROOT/'verification.json',prior_path)
    prior = read('verification-v033.json')
    assert prior['version']=='0.3.3'
    for relative,digest in audit['inherited_archive_checks'].items():
        assert digest==prior['source_sha256'][relative]==sha(ROOT/relative)
    mapping = {'kestrel':'cli_sha256','kestrel-stress':'bridge_sha256','performance-probe':'probe_sha256',
               'scan-profile':'scan_probe_sha256','publication-probe':'publication_probe_sha256','receipt-seed':'receipt_seed_sha256'}
    for name,field in mapping.items():
        binary_path = WORKSPACE/'work/perf-034/candidate'/(name+'.exe')
        assert sha(binary_path)==build[field],name
        shutil.copy2(binary_path,ROOT/'bin'/(name+'.exe'))
    proof = {**build,'status':'experimental optional coalescing policy; production qualification incomplete',
        'service_qualification':audit['service_qualification'],'default_group_delay_ms':0,
        'optional_group_delay_limit_ms':20,'current_policy_audit':audit,
        'prior_release_proof':'verification-v033.json','inherited_evidence':audit['archive_evidence'],
        'storage_format':{'catalog':'CAT4','segment':'SEG2','max_catalog_chain_files':32,'unchanged_from':'0.3.3'},
        'concurrent_crash_report':'benchmarks/group-034-recovery.json',
        'delayed_pipeline_report':'portfolio/live-pipeline-034-results.json',
        'baseline_provenance':base,'reference_servers_stopped':True,
        'historical_test_only_fault_driver':'bin/test-only/publication-fault-probe.exe is the preserved 0.3.3 feature-enabled driver, not a default executable',
        'qualification_limits':prior['qualification_limits']+[
            'optional window bounds intentional collection waiting, not OS scheduling, queueing or ACK/storage time',
            'coalescing can regress low concurrency, retries and tail latency; default remains zero',
            'one-minute screens and descriptive repeats do not establish long endurance',
            'unchanged storage/query checks inherited from prior proof are not counted as new tests']}
    (ROOT/'verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    for path in ROOT.rglob('*.py'):
        if not {'target','__pycache__','.git'}.intersection(path.relative_to(ROOT).parts):
            ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    for path in ROOT.rglob('*.json'):
        json.loads(path.read_text(encoding='utf-8'))
    for path in ROOT.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' not in target and not target.startswith('#'):
                assert (path.parent/target.split('#')[0]).exists(),(path,target)
    for package in tomllib.loads((ROOT/'Cargo.lock').read_text(encoding='utf-8'))['package']:
        if package['name']!='kestrel-sql':
            directory = ROOT/'licenses'/f"{package['name']}-{package['version']}"
            assert directory.is_dir() and any(directory.iterdir())
    replies = [json.loads(line) for line in subprocess.check_output([str(ROOT/'bin/kestrel.exe'),'--file',str(ROOT/'examples/live_metrics.sql')],text=True).splitlines()]
    assert len(replies)==8 and all(reply['ok'] for reply in replies)
    assert replies[2]['result']['rows']==[[2,30,15.0]]
    files = sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='MANIFEST.sha256'
        and not {'target','__pycache__','.git'}.intersection(p.relative_to(ROOT).parts))
    manifest = [(sha(path),path.relative_to(ROOT).as_posix()) for path in files]
    (ROOT/'MANIFEST.sha256').write_text(''.join(f'{digest}  {name}\n' for digest,name in manifest),encoding='utf-8')
    files.append(ROOT/'MANIFEST.sha256')
    package_path = ROOT.parent/f'kestrel-sql-{VERSION}.zip'
    assert not package_path.exists(),'Never replace an existing release artifact'
    with zipfile.ZipFile(package_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9,strict_timestamps=False) as archive:
        for path in files:
            archive.write(path,(Path(ROOT.name)/path.relative_to(ROOT)).as_posix())
    with zipfile.ZipFile(package_path) as archive:
        assert archive.testzip() is None and len(archive.namelist())==len(files)
        for digest,name in manifest:
            assert hashlib.sha256(archive.read(ROOT.name+'/'+name)).hexdigest()==digest,name
        extracted = WORKSPACE/'work'/f'package-smoke-034-{time.time_ns()}'
        extracted.mkdir()
        for name in ['kestrel','kestrel-stress']:
            archive.extract(ROOT.name+'/bin/'+name+'.exe',extracted)
        smoke(extracted)
    digest = sha(package_path)
    package_path.with_suffix('.zip.sha256').write_text(f'{digest}  {package_path.name}\n',encoding='utf-8')
    result = {'package':str(package_path),'bytes':package_path.stat().st_size,'sha256':digest,'payload_files':len(manifest),
        'zip_integrity':'passed','all_file_hashes':'passed','internal_document_links':'passed','python_syntax':'passed',
        'packaged_policies_0_2_8_20ms_replay_reopen_scrub':'passed','preceding_0_3_3_read_write_roundtrip':'passed',
        'current_stress_cases':59,'current_offered_requests':1_936_800,'concurrent_process_kill_cycles':32,
        'archive_evidence_inherited_by_verified_source_hashes':True,'historical_packages_preserved':True,
        'reference_servers_stopped':True,'service_qualification':audit['service_qualification']}
    (ROOT.parent/f'kestrel-sql-{VERSION}-package-check.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
