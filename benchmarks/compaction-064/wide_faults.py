"""Fourteen exact publication cuts over a 64-run archive, with independent SQL."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from stress_compare import Engine
W=Path(__file__).resolve().parent
WORK=W/'lab/work'
binary=WORK/'perf-064/candidate/kestrel-stress.exe'
seed=WORK/'perf-064/candidate/fanin-seed-probe.exe'
driver=WORK/'kestrel-064-fault-build/release/examples/publication_fault_probe.exe'
version='0.3.17-dev.64'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
output=W/'wide-faults.json';assert not output.exists()
fixtures=W/'wide-fault-fixtures';fixtures.mkdir()
source=fixtures/'source';(source/'archive').mkdir(parents=True)
initial=subprocess.run([str(seed),str(source/'archive'),'seed','64'],text=True,capture_output=True,timeout=60)
assert initial.returncode==0,(initial.stdout,initial.stderr)
assert json.loads(initial.stdout)['segments']==64
r={'trial':64,'started_utc':datetime.now(timezone.utc).isoformat(),
    'binary_sha256':sha(binary),'seed_sha256':sha(seed),'fault_driver_sha256':sha(driver),
    'method':'64 direct identified Archive publications; seven exact cut points with process exit and injected I/O failure; default recovery and independent Python SQL oracles; live filesystem, not physical power loss',
    'seed_output':json.loads(initial.stdout),'cases':[],'failed_cases':[],'complete':False}
def save():output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
save()
for point in ['segment_partial','segment_written','segment_synced','catalog_partial','catalog_written','catalog_synced','catalog_published']:
    for mode in ['exit','io_error']:
        directory=fixtures/(point+'-'+mode)
        shutil.copytree(source,directory)
        environment={**os.environ,'KESTREL_FAULT_POINT':point,'KESTREL_FAULT_MODE':mode}
        failure=subprocess.run([str(driver),str(directory/'archive'),'compact'],env=environment,text=True,capture_output=True,timeout=60)
        (directory/'fault.stdout.txt').write_text(failure.stdout,encoding='utf-8')
        (directory/'fault.stderr.txt').write_text(failure.stderr,encoding='utf-8')
        engine=None
        try:
            assert failure.returncode==(86 if mode=='exit' else 87),failure
            if mode=='io_error':assert 'poisoned writer; old snapshot readable' in failure.stderr
            generation=65 if point=='catalog_published' else 64
            cold=subprocess.run([str(seed),str(directory/'archive'),'check',str(generation)],text=True,capture_output=True,timeout=60)
            assert cold.returncode==0,(cold.stdout,cold.stderr)
            checks=json.loads(cold.stdout)
            assert checks['version']==version and checks['original_receipts_rows_sum_and_crc_passed']
            engine=Engine('kestrel',directory,0,binary,{},existing=True)
            assert engine.version==version
            connection=engine.connect()
            assert connection.query('SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device')==[[b,100,100*(b*200+99)] for b in range(64)]
            for lo,hi in [(0,37),(31,132),(3179,3292),(6350,6441)]:
                selected=list(range(max(0,lo),min(6400,hi)))
                assert connection.query(f'SELECT COUNT(*), SUM(value) FROM events WHERE ts >= {lo} AND ts < {hi}')==[[len(selected),sum(i*2 for i in selected)]]
            assert connection.call({'op':'verify'})['verified_bytes']==6400*24
            connection.close()
            r['cases'].append({'point':point,'mode':mode,'returncode':failure.returncode,'generation':generation,
                'segments':checks['segments'],'original64_receipts_preserved':True,'rows_sums_group_and_range_oracles_passed':True,
                'full_crc_passed':True,'writer_poison_and_pinned_read_passed':mode=='io_error','fixture':str(directory)})
            print(json.dumps(r['cases'][-1]),flush=True)
        except Exception as error:
            r['failed_cases'].append({'point':point,'mode':mode,'error':repr(error)})
            raise
        finally:
            if engine is not None:engine.finish()
            save()
assert len(r['cases'])==14 and not r['failed_cases']
r['complete']=True;r['completed_utc']=datetime.now(timezone.utc).isoformat();save()
