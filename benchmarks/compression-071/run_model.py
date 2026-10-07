"""Frozen54-case serial raw/A-A/zstd model; no SQL comparison."""
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess, sys, time
from pathlib import Path
from process_memory import peak_memory
from order_plan import plan, validate
W=Path(__file__).resolve().parent;BIN=W/'bin/checkpoint-model.exe'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()
def initialize():
    assert not (W/'cohort-policy.json').exists() and not (W/'model-results.json').exists()
    build=load(W/'build-proof.json');assert build['complete'] and build['tests']=={'debug':12,'release':12}
    assert not load(W/'pre-timing-process-check.json')['active_processes']
    for n,d in build['source_sha256'].items():assert sha(W/'model'/n)==d,n
    assert sha(BIN)==build['binary_sha256']
    p=load(W/'policy.json');assert p['method']['rounds']==6 and p['method']['cases']==54
    cases=plan();balance=validate(cases)
    save(W/'order-balance-pre-timing.json',balance)
    save(W/'cohort-policy.json',{'declared_utc':now(),'before_first_timer':True,'cases':cases,
        'policy_sha256':sha(W/'policy.json'),'build_proof_sha256':sha(W/'build-proof.json'),
        'input_provenance_sha256':sha(W/'input-provenance.json'),'binary_sha256':sha(BIN),
        'harness_sha256':sha(Path(__file__)),'memory_helper_sha256':sha(W/'process_memory.py'),
        'independent_auditor_sha256':sha(W/'audit_model.py'),'frame_oracle_sha256':sha(W/'zstd_frame_oracle.py'),
        'oracle_provenance_sha256':sha(W/'oracle-provenance.json'),'order_plan_sha256':sha(W/'order_plan.py'),'order_balance_sha256':sha(W/'order-balance-pre-timing.json'),'model_only':True,'no_engine_edit':True})
    print(json.dumps({'initialized':True,'cases':len(cases),'publication_samples':648}),flush=True)
def run():
    p=load(W/'cohort-policy.json');assert not (W/'model-results.json').exists()
    for name,key in [('policy.json','policy_sha256'),('build-proof.json','build_proof_sha256'),('input-provenance.json','input_provenance_sha256'),('run_model.py','harness_sha256'),('process_memory.py','memory_helper_sha256'),('audit_model.py','independent_auditor_sha256')]:assert sha(W/name)==p[key],name
    assert sha(BIN)==p['binary_sha256']
    assert sha(W/'zstd_frame_oracle.py')==p['frame_oracle_sha256'] and sha(W/'oracle-provenance.json')==p['oracle_provenance_sha256']
    for name,digest in load(W/'oracle-provenance.json')['files'].items():assert sha(Path(name))==digest,name
    assert sha(W/'order_plan.py')==p['order_plan_sha256'] and sha(W/'order-balance-pre-timing.json')==p['order_balance_sha256']
    assert json.loads(json.dumps(validate(p['cases'])))==load(W/'order-balance-pre-timing.json')
    for i in load(W/'input-provenance.json')['inputs']:assert sha(Path(i['path']))==i['sha256']
    policy=load(W/'policy.json');(W/'fixtures').mkdir();(W/'raw').mkdir()
    result={'started_utc':now(),'complete':False,'cohort_policy_sha256':sha(W/'cohort-policy.json'),'cases':[],'failures':[]};save(W/'model-results.json',result)
    for index,spec in enumerate(p['cases']):
        label=f"{index:02d}-r{spec['round']}-{spec['seed_receipts']}-{spec['variant']}";store=W/'fixtures'/label;raw=W/'raw'
        free=shutil.disk_usage(W).free
        if free<policy['minimum_free_bytes']:
            result['failures'].append({'label':label,'case_not_started':True,'free_bytes':free});save(W/'model-results.json',result);raise RuntimeError('Disk guard; stop without case restart')
        argv=[str(BIN),str(store),str(W/'inputs'/f"{spec['seed_receipts']}.ks2"),spec['mode'],'12']
        status={'spec':spec,'label':label,'fixture':str(store),'argv':argv,'started_utc':now(),'free_bytes_before':free}
        start=time.perf_counter()
        with (raw/f'{label}.stdout.json').open('w',encoding='utf-8') as stdout,(raw/f'{label}.stderr.txt').open('w',encoding='utf-8') as stderr:
            process=subprocess.Popen(argv,stdout=stdout,stderr=stderr);status['pid']=process.pid
            try:status['exit_code']=process.wait(timeout=policy['timeout_per_case_seconds'])
            except subprocess.TimeoutExpired:
                process.kill();process.wait();status.update(exit_code=process.returncode,timeout=True)
            status['memory']=peak_memory(process)
        status.update(ended_utc=now(),wall_seconds=time.perf_counter()-start);save(raw/f'{label}.status.json',status)
        if status['exit_code']!=0:
            result['failures'].append(status);save(W/'model-results.json',result);raise RuntimeError(f'Preserved failed case {label}')
        x=load(raw/f'{label}.stdout.json');assert x['probe']=='CHECKPOINTMODEL071' and x['mode']==spec['mode']
        assert len(x['samples'])==len(x['fresh_read_decode_ms'])==12 and x['all_bytes_match_original']
        result['cases'].append({'label':label,'spec':spec,'stdout_sha256':sha(raw/f'{label}.stdout.json'),'status_sha256':sha(raw/f'{label}.status.json'),'stderr_sha256':sha(raw/f'{label}.stderr.txt')});save(W/'model-results.json',result)
        print(json.dumps({'completed':index+1,'total':54,'label':label,'wall_seconds':status['wall_seconds'],'max_ms':max(s['outer_ms'] for s in x['samples'])}),flush=True)
    result.update(complete=True,completed_utc=now());save(W/'model-results.json',result)
if __name__=='__main__':
    if sys.argv[1:]==['--initialize']:initialize()
    else:assert not sys.argv[1:];run()
