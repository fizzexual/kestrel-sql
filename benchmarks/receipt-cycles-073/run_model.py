"""Frozen 54-case serial metadata cohort; no SQL/engine comparison."""
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
from process_memory import peak_memory
from order_plan import plan,validate
W=Path(__file__).resolve().parent;BIN=W/'bin/growth-model.exe'
FILES=['policy.json','build-proof.json','input-provenance.json','run_model.py','process_memory.py','audit_model.py','catalog_oracle.py','page_oracle.py','order_plan.py','native-control-oracle.json','order-balance-pre-timing.json']
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()
def initialize():
    assert not (W/'cohort-policy.json').exists() and not (W/'model-results.json').exists()
    build=load(W/'build-proof.json');assert build['complete'] and build['counts']=={'debug':22,'release':22}
    assert sha(BIN)==build['binary_sha256'] and not load(W/'pre-timing-process-check.json')['active_processes']
    for n,d in build['source_sha256'].items():assert sha(W/'model'/n)==d,n
    assert load(W/'native-control-oracle.json')['complete'];cases=plan();save(W/'order-balance-pre-timing.json',validate(cases))
    save(W/'cohort-policy.json',{'declared_utc':now(),'before_first_timer':True,'cases':cases,'binary_sha256':sha(BIN),'frozen_file_sha256':{n:sha(W/n) for n in FILES},'model_only':True,'no_engine_edit':True})
    print(json.dumps({'initialized':True,'cases':54,'publication_samples':3456,'fresh_recoveries':648}),flush=True)
def run():
    cohort=load(W/'cohort-policy.json');assert not (W/'model-results.json').exists()
    for n,d in cohort['frozen_file_sha256'].items():assert sha(W/n)==d,n
    assert sha(BIN)==cohort['binary_sha256'] and json.loads(json.dumps(validate(cohort['cases'])))==load(W/'order-balance-pre-timing.json')
    for item in load(W/'input-provenance.json')['inputs']:assert sha(Path(item['path']))==item['sha256']
    policy=load(W/'policy.json');(W/'fixtures').mkdir();(W/'raw').mkdir()
    result={'started_utc':now(),'complete':False,'cohort_policy_sha256':sha(W/'cohort-policy.json'),'cases':[],'failures':[]};save(W/'model-results.json',result)
    for index,spec in enumerate(cohort['cases']):
        label=f"{index:02d}-r{spec['round']}-{spec['seed_receipts']}-{spec['variant']}";store=W/'fixtures'/label;raw=W/'raw';free=shutil.disk_usage(W).free
        if free<policy['minimum_free_bytes']:
            result['failures'].append({'label':label,'case_not_started':True,'free_bytes':free});save(W/'model-results.json',result);raise RuntimeError('Disk guard, stop without restarting a case')
        argv=[str(BIN),'bench073',str(store),str(W/'inputs'/f"{spec['seed_receipts']}.ks2"),spec['mode'],'64']
        status={'spec':spec,'fixture':str(store),'label':label,'argv':argv,'started_utc':now(),'free_bytes_before':free};start=time.perf_counter()
        with (raw/f'{label}.stdout.json').open('w',encoding='utf-8') as stdout,(raw/f'{label}.stderr.txt').open('w',encoding='utf-8') as stderr:
            child=subprocess.Popen(argv,stdout=stdout,stderr=stderr);status['pid']=child.pid
            try:status['exit_code']=child.wait(timeout=policy['timeout_per_case_seconds'])
            except subprocess.TimeoutExpired:child.kill();child.wait();status.update(exit_code=child.returncode,timeout=True)
            status['memory']=peak_memory(child)
        status.update(ended_utc=now(),wall_seconds=time.perf_counter()-start);save(raw/f'{label}.status.json',status)
        if status['exit_code']!=0:
            result['failures'].append(status);save(W/'model-results.json',result);raise RuntimeError(f'Preserved failed case {label}')
        x=load(raw/f'{label}.stdout.json');assert x['probe']=='GROWTHMODEL073' and x['mode']==spec['mode'] and len(x['samples'])==64 and len(x['fresh_recovery'])==12
        result['cases'].append({'label':label,'spec':spec,**{key:sha(raw/f'{label}.{suffix}') for suffix,key in [('stdout.json','stdout_sha256'),('stderr.txt','stderr_sha256'),('status.json','status_sha256')]}});save(W/'model-results.json',result)
        print(json.dumps({'completed':index+1,'total':54,'label':label,'max_publication_ms':max(s['outer_ms'] for s in x['samples']),'migration_ms':x['migration_ms'],'wall_seconds':status['wall_seconds']}),flush=True)
    result.update(complete=True,completed_utc=now());save(W/'model-results.json',result)
if __name__=='__main__':
    if sys.argv[1:]==['--initialize']:initialize()
    else:assert not sys.argv[1:];run()
