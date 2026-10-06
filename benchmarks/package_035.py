"""Explicit retry-release gates, immutable ZIP, hashes and packaged roundtrip smokes."""
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

ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent.parent
VERSION='0.3.5'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))


def smoke(extracted):
    cli=extracted/ROOT.name/'bin/kestrel.exe'
    bridge=extracted/ROOT.name/'bin/kestrel-stress.exe'
    assert '--archive' in subprocess.check_output([str(cli),'--help'],text=True)
    default=Engine('kestrel',extracted/'default-store',0,bridge,{})
    try:
        connection=default.connect()
        request={'op':'append','id':'default:known','data':[[1,2,3]]}
        assert not connection.call(request)['duplicate'] and connection.call(request)['duplicate']
        stats=connection.call({'op':'stats'})['ingest']
        assert not stats['retry_index_enabled'] and stats['retry_index_ids']==stats['retry_index_logical_bytes']==stats['fast_retry_hits']==0
        assert stats['collected_groups']==2
        assert connection.call({'op':'verify'})['verified_bytes']==24
        connection.close()
    finally:
        default.finish()
    for delay in [0,2,8,20]:
        directory=extracted/f'store-{delay}'
        first={'op':'append','id':'package:first','data':[[1000,17,2],[1001,-3,2]]}
        second={'op':'append','id':'package:old-writer','data':[[1002,5,3]]}
        engine=Engine('kestrel',directory,1000,bridge,{},bridge_args=(delay,1))
        try:
            assert engine.version==VERSION
            connection=engine.connect()
            receipt=connection.call(first)
            assert not receipt['duplicate']
            assert connection.call(first)['duplicate']
            stats=connection.call({'op':'stats'})['ingest']
            assert stats['fast_retry_hits']==1 and stats['retry_index_ids']==1
            assert not stats['writer_poisoned'] and not stats['writer_stopped']
            assert stats['group_delay_ns']==delay*1_000_000
            connection.close()
            engine.reopen()
            connection=engine.connect()
            replay=connection.call(first)
            assert replay['duplicate'] and replay['generation']==receipt['generation']
            assert connection.call({'op':'verify'})['verified_bytes']==1002*24
            connection.close()
        finally:
            engine.finish()
        previous=Engine('kestrel',directory,0,ROOT/'bin/baseline-0.3.4/kestrel-stress.exe',{},existing=True)
        try:
            assert previous.version=='0.3.4'
            connection=previous.connect()
            replay=connection.call(first)
            assert replay['duplicate'] and replay['generation']==receipt['generation']
            assert not connection.call(second)['duplicate']
            assert connection.query('SELECT COUNT(*), SUM(value) FROM events')==[[1003,-481]]
            assert connection.call({'op':'verify'})['verified_bytes']==1003*24
            connection.close()
        finally:
            previous.finish()
        current=Engine('kestrel',directory,0,bridge,{},existing=True,bridge_args=(delay,1))
        try:
            connection=current.connect()
            assert connection.call(first)['duplicate'] and connection.call(second)['duplicate']
            assert connection.call({'op':'stats'})['ingest']['fast_retry_hits']==2
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
            assert connection.connect_ex(('127.0.0.1',port))!=0
    build=read('benchmarks/rust-checks-035-final.json')
    assert build['rust_tests']=={'debug':41,'release':41,'passed':True}
    assert build['format_check']==build['clippy_warnings_as_errors']==build['feature_clippy_warnings_as_errors']=='passed'
    for relative,digest in build['source_sha256'].items():
        assert sha(ROOT/relative)==digest,relative
    audit=read('benchmarks/retry-035-audit.json')
    assert (audit['completed_cases'],audit['offered_operations'],audit['numpy_windows'])==(106,3_480_000,2120)
    assert audit['final_binary_cases']==48 and audit['final_binary_offers']==1_440_000 and audit['embedded_retry_cases']==18
    assert audit['live_retry_fault_cases']==8 and audit['concurrent_kill_cycles']==32
    assert audit['publication_cut_point_cases']==56 and audit['corruption_cases']==22
    assert audit['differential_cases_each_reference']==500 and audit['parquet_exact_sql_cases']==42
    assert audit['retained_result_checks']==153
    assert audit['timed_database_workloads_no_overlap'] and audit['build_and_correctness_outside_timed_suites']
    base=read('benchmarks/baseline-0.3.4-provenance.json')
    assert sha(ROOT.parent/'kestrel-sql-0.3.4.zip')==base['archive_sha256']
    for relative,digest in base['core_source_sha256'].items():
        assert sha(ROOT/'benchmarks/baseline-0.3.4-source'/relative)==digest,relative
    for relative,digest in base['baseline_binary_sha256'].items():
        assert sha(ROOT/'bin/baseline-0.3.4'/relative)==digest,relative
    trial=read('benchmarks/rust-checks-035.json')
    for relative,digest in trial['source_sha256'].items():
        assert sha(ROOT/'benchmarks/trial-0.3.5-source'/relative)==digest,relative
    assert sha(WORKSPACE/'work/perf-035/trial/kestrel-stress.exe')==trial['bridge_sha256']
    trial_dir=ROOT/'bin/trial-0.3.5'
    trial_dir.mkdir(exist_ok=True)
    for name,field in [('kestrel','cli_sha256'),('kestrel-stress','bridge_sha256'),('receipt-seed','receipt_seed_sha256')]:
        source=WORKSPACE/'work/perf-035/trial'/(name+'.exe')
        assert sha(source)==trial[field]
        shutil.copy2(source,trial_dir/source.name)
    prior_path=ROOT/'verification-v034.json'
    if not prior_path.exists():
        assert read('verification.json')['version']=='0.3.4'
        shutil.copy2(ROOT/'verification.json',prior_path)
    prior=read('verification-v034.json')
    assert prior['version']=='0.3.4'
    fields={'kestrel':'cli_sha256','kestrel-stress':'bridge_sha256','performance-probe':'probe_sha256','scan-profile':'scan_probe_sha256',
        'publication-probe':'publication_probe_sha256','receipt-seed':'receipt_seed_sha256'}
    for name,field in fields.items():
        source=WORKSPACE/'work/perf-035/final'/(name+'.exe')
        assert sha(source)==build[field],name
        data=source.read_bytes()
        assert b'KESTREL_LIVE_PAUSE' not in data and b'KESTREL_FAULT_POINT' not in data
        shutil.copy2(source,ROOT/'bin'/source.name)
    test_dir=ROOT/'bin/test-only'
    test_dir.mkdir(exist_ok=True)
    for name,field in [('publication_fault_probe','fault_driver_sha256'),('live_retry_probe','live_retry_driver_sha256')]:
        source=WORKSPACE/'work/kestrel-035-final-fault-build/release/examples'/(name+'.exe')
        assert sha(source)==build[field]
        shutil.copy2(source,test_dir/(name.replace('_','-')+'-035.exe'))
    direct=read('benchmarks/retry-035-direct.json')
    for variant,tag in [('baseline','034'),('candidate','035')]:
        source=Path(direct['builds'][variant]['binary_path'])
        assert sha(source)==direct['builds'][variant]['binary_sha256']
        shutil.copy2(source,test_dir/f'live-retry-inprocess-{tag}.exe')
    proof={**build,'status':'experimental confirmed retry optimization; production qualification incomplete',
        'service_qualification':audit['service_qualification'],'current_retry_audit':audit,'prior_release_proof':'verification-v034.json',
        'storage_format':{'catalog':'CAT4','segment':'SEG2','max_catalog_chain_files':32,'unchanged_from':'0.3.3'},
        'default_group_delay_ms':0,'default_retry_index_enabled':False,'optional_group_delay_limit_ms':20,'baseline_provenance':base,'reference_servers_stopped':True,
        'current_evidence':{'live_retry_faults':'benchmarks/retry-035-faults.json','publication_faults':'benchmarks/publication-035-faults.json',
            'group_crashes':'benchmarks/group-035-recovery.json','pipeline':'portfolio/live-pipeline-035-results.json',
            'differential':'benchmarks/archive-035-verification.json','retained_scale':'benchmarks/release-recheck-035.json'},
        'test_only_drivers':'publication/live-retry *-035.exe in bin/test-only have the fault-injection feature; live-retry-inprocess probes measure the embedded API without hooks; supported CLI/bridge contain no hooks',
        'qualification_limits':prior['qualification_limits']+[
            'confirmed retries use an extra bounded receipt map; logical counter excludes BTree nodes and allocator overhead',
            'fast retry successes acknowledge only original committed generations; pending IDs still use writer',
            'favorable combined retry percentiles can hide slow new writes; operation-specific tails and losses retained',
            'eight-second 10K retry screens and descriptive repeats do not establish sustained capacity']}
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
    for dependency in tomllib.loads((ROOT/'Cargo.lock').read_text(encoding='utf-8'))['package']:
        if dependency['name']!='kestrel-sql':
            directory=ROOT/'licenses'/f"{dependency['name']}-{dependency['version']}"
            assert directory.is_dir() and any(directory.iterdir())
    replies=[json.loads(line) for line in subprocess.check_output([str(ROOT/'bin/kestrel.exe'),'--file',str(ROOT/'examples/live_metrics.sql')],text=True).splitlines()]
    assert len(replies)==8 and all(reply['ok'] for reply in replies) and replies[2]['result']['rows']==[[2,30,15.0]]
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p.name!='MANIFEST.sha256'
        and not {'target','__pycache__','.git'}.intersection(p.relative_to(ROOT).parts))
    manifest=[(sha(path),path.relative_to(ROOT).as_posix()) for path in files]
    (ROOT/'MANIFEST.sha256').write_text(''.join(f'{digest}  {name}\n' for digest,name in manifest),encoding='utf-8')
    files.append(ROOT/'MANIFEST.sha256')
    package=ROOT.parent/f'kestrel-sql-{VERSION}.zip'
    assert not package.exists(),'Never replace a published release artifact'
    with zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9,strict_timestamps=False) as archive:
        for path in files:
            archive.write(path,(Path(ROOT.name)/path.relative_to(ROOT)).as_posix())
    with zipfile.ZipFile(package) as archive:
        assert archive.testzip() is None and len(archive.namelist())==len(files)
        for digest,name in manifest:
            assert hashlib.sha256(archive.read(ROOT.name+'/'+name)).hexdigest()==digest,name
        extracted=WORKSPACE/'work'/f'package-smoke-035-{time.time_ns()}'
        extracted.mkdir()
        for name in ['kestrel','kestrel-stress']:
            archive.extract(ROOT.name+'/bin/'+name+'.exe',extracted)
        smoke(extracted)
    digest=sha(package)
    package.with_suffix('.zip.sha256').write_text(f'{digest}  {package.name}\n',encoding='utf-8')
    result={'package':str(package),'bytes':package.stat().st_size,'sha256':digest,'payload_files':len(manifest),
        'zip_integrity':'passed','all_file_hashes':'passed','internal_document_links':'passed','python_syntax':'passed',
        'packaged_policies_0_2_8_20ms_fast_retry_reopen_scrub':'passed','preceding_0_3_4_read_write_roundtrip':'passed',
        'retained_stress_cases':106,'retained_offered_requests':3_480_000,'final_binary_stress_cases':48,'final_binary_offered_requests':1_440_000,'embedded_retry_cases':18,'live_retry_fault_cases':8,'concurrent_process_kill_cycles':32,
        'publication_cut_point_cases':56,'corruption_cases':22,'reference_servers_stopped':True,'historical_packages_preserved':True,
        'service_qualification':audit['service_qualification']}
    (ROOT.parent/f'kestrel-sql-{VERSION}-package-check.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
