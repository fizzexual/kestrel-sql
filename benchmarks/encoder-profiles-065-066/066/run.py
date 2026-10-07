"""One frozen standalone encoder process per case; no engine changes or publications."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess,time,sys
from process_memory import peak_memory
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()
def initialize():
    assert not (W/'timing-provenance.json').exists() and not (W/'results.json').exists()
    assert load(W/'build.json')['complete'] and load(W/'smoke.json')['passed']
    assert not load(W/'pre-timing-process-check.json')['active_processes']
    policy=load(W/'policy.json');binary=W/'bin/encoder-probe.exe'
    assert sha(binary)==load(W/'build.json')['binary_sha256']
    for item in policy['inputs']:assert sha(W/item['body_relative'])==item['body_sha256']
    save(W/'timing-provenance.json',{'declared_utc':now(),'before_first_performance_case':True,'policy_sha256':sha(W/'policy.json'),
        'binary_sha256':sha(binary),'probe_source_sha256':sha(W/'encoder_probe.rs'),'models_sha256':sha(W/'released_encoder_models.rs'),
        'harness_sha256':sha(Path(__file__)),'memory_helper_sha256':sha(W/'process_memory.py'),'build_sha256':sha(W/'build.json'),'smoke_sha256':sha(W/'smoke.json'),
        'pre_timing_process_check_sha256':sha(W/'pre-timing-process-check.json')})
    print(json.dumps({'initialized':True,'cases':len(policy['cases'])}),flush=True)
def run():
    assert not (W/'results.json').exists()
    provenance=load(W/'timing-provenance.json');policy=load(W/'policy.json');binary=W/'bin/encoder-probe.exe'
    for name,key in [('policy.json','policy_sha256'),('bin/encoder-probe.exe','binary_sha256'),('encoder_probe.rs','probe_source_sha256'),('released_encoder_models.rs','models_sha256'),('run.py','harness_sha256'),('process_memory.py','memory_helper_sha256')]:assert sha(W/name)==provenance[key]
    raw=W/'raw';raw.mkdir();report={'started_utc':now(),'timing_provenance_sha256':sha(W/'timing-provenance.json'),'cases':[],'failures':[],'complete':False};save(W/'results.json',report)
    for index,spec in enumerate(policy['cases']):
        label=f"{index:02d}-r{spec['round']}-{spec['starting_receipts']}-{spec['variant']}"
        item=next(i for i in policy['inputs'] if i['starting_receipts']==spec['starting_receipts']);mode='baseline' if spec['variant'].startswith('baseline') else spec['variant']
        free=shutil.disk_usage(W).free
        assert free>=policy['minimum_free_bytes_before_case'],('disk preflight',free)
        argv=[str(binary),str(W/item['body_relative']),mode,str(spec['repetitions']),item['last_id']]
        status={'spec':spec,'label':label,'started_utc':now(),'argv':argv,'free_bytes_before':free};started=time.perf_counter()
        with (raw/f'{label}.stdout.json').open('w',encoding='utf-8') as out,(raw/f'{label}.stderr.txt').open('w',encoding='utf-8') as err:
            process=subprocess.Popen(argv,stdout=out,stderr=err);status['pid']=process.pid
            try:status['exit']=process.wait(timeout=policy['timeout_seconds_per_case'])
            except subprocess.TimeoutExpired:process.kill();process.wait();status.update(exit=process.returncode,timeout=True)
            status['memory']=peak_memory(process)
        status.update(ended_utc=now(),wall_seconds=time.perf_counter()-started);save(raw/f'{label}.status.json',status)
        try:
            assert status['exit']==0 and not status.get('timeout')
            x=load(raw/f'{label}.stdout.json');assert x['encoder_model_only'] and x['no_database_publication']
            assert x['mode']==mode and x['receipt_count']==item['receipts'] and x['input_bytes']==item['bytes']
            assert x['repetitions']==33 and len(x['raw_ms'])==len(x['capacities'])==33 and x['every_output_matches_original_catalog_bytes']
        except Exception as error:
            report['failures'].append({'label':label,'error':repr(error),'status':status});save(W/'results.json',report);raise
        report['cases'].append({'spec':spec,'label':label,'stdout_sha256':sha(raw/f'{label}.stdout.json'),'stderr_sha256':sha(raw/f'{label}.stderr.txt'),'status_sha256':sha(raw/f'{label}.status.json')});save(W/'results.json',report)
        print(json.dumps({'completed':index+1,'total':len(policy['cases']),'label':label,'wall_seconds':status['wall_seconds'],'first_encode_ms':x['raw_ms'][0],'memory_available':status['memory']['success'],'all33_byte_equal':True}),flush=True)
    report.update(complete=True,completed_utc=now());save(W/'results.json',report)
if __name__=='__main__':
    if sys.argv[1:]==['--initialize']:initialize()
    else:assert not sys.argv[1:];run()
