"""Freeze and run54 fresh serial all-hybrid cases; preserve failures, no observed reruns."""
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess,sys,time
from pathlib import Path
from process_memory import peak_memory
from order_plan import plan,validate
W=Path(__file__).resolve().parent
FILES=['policy.json','binary-provenance.json','input-provenance.json','run_model.py','process_memory.py','audit_model.py','catalog_oracle.py','page_oracle.py','hybrid_oracle.py','order_plan.py','native-control-oracle.json','order-balance-pre-timing.json','DESIGN.md','canonical_audit.py','qualify_integration.py','helper-derivation.json','source-finalization.json','baseline.json']
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()
def initialize():
    assert not (W/'cohort-policy.json').exists() and not (W/'model-results.json').exists()
    provenance=load(W/'binary-provenance.json');assert provenance['complete'] and provenance['reused_unchanged_binaries_no_rebuild']
    for label,b in provenance['builds'].items():
        assert sha(W/b['binary'])==b['binary_sha256']
        for n,d in b['source_sha256'].items():assert sha(W/b['source_directory']/n)==d,n
    assert not load(W/'pre-timing-process-check.json')['active_processes']
    assert load(W/'native-control-oracle.json')['complete'] and load(W/'source-finalization.json')['all_reused_sources_binaries_and_decoder_verified']
    cases=plan();save(W/'order-balance-pre-timing.json',validate(cases))
    files=FILES+[p.relative_to(W).as_posix() for folder in ['control-model','candidate-model','locked-registry-crates','prerequisites','inputs'] for p in sorted((W/folder).rglob('*')) if p.is_file()]
    save(W/'cohort-policy.json',{'declared_utc':now(),'before_first_timer':True,'cases':cases,'binary_sha256':{b['binary']:b['binary_sha256'] for b in provenance['builds'].values()},'frozen_file_sha256':{n:sha(W/n) for n in files},'model_only':True,'no_engine_edit':True,'all_cases_hybrid_protocol':True})
    print(json.dumps({'initialized':True,'cases':54,'publication_samples':3456,'fresh_recoveries':648}),flush=True)
def run():
    cohort=load(W/'cohort-policy.json');assert not (W/'model-results.json').exists()
    for n,d in cohort['frozen_file_sha256'].items():assert sha(W/n)==d,n
    for n,d in cohort['binary_sha256'].items():assert sha(W/n)==d,n
    assert json.loads(json.dumps(validate(cohort['cases'])))==load(W/'order-balance-pre-timing.json')
    assert not load(W/'pre-timing-process-check.json')['active_processes']
    provenance=load(W/'binary-provenance.json');policy=load(W/'policy.json');(W/'fixtures').mkdir();(W/'raw').mkdir()
    result={'started_utc':now(),'complete':False,'cohort_policy_sha256':sha(W/'cohort-policy.json'),'cases':[],'failures':[]};save(W/'model-results.json',result)
    for index,spec in enumerate(cohort['cases']):
        label=f"{index:02d}-r{spec['round']}-{spec['seed_receipts']}-{spec['variant']}";store=W/'fixtures'/label;raw=W/'raw';free=shutil.disk_usage(W).free
        if free<policy['minimum_free_bytes']:
            result['failures'].append({'label':label,'case_not_started':True,'free_bytes':free});save(W/'model-results.json',result);raise RuntimeError('Disk guard: preserve cases, stop without observed reruns')
        binary=provenance['builds'][provenance['variants'][spec['variant']]]['binary']
        argv=[str(W/binary),'bench075',str(store),str(W/'inputs'/f"{spec['seed_receipts']}.ks2"),'hybrid','64']
        status={'spec':spec,'fixture':str(store),'label':label,'argv':argv,'binary':binary,'started_utc':now(),'free_bytes_before':free};start=time.perf_counter()
        with (raw/f'{label}.stdout.json').open('w',encoding='utf-8') as stdout,(raw/f'{label}.stderr.txt').open('w',encoding='utf-8') as stderr:
            child=subprocess.Popen(argv,stdout=stdout,stderr=stderr);status['pid']=child.pid
            try:status['exit_code']=child.wait(timeout=policy['timeout_per_case_seconds'])
            except subprocess.TimeoutExpired:child.kill();child.wait();status.update(exit_code=child.returncode,timeout=True)
            status['memory']=peak_memory(child)
        status.update(owned_child_waited=True,ended_utc=now(),wall_seconds=time.perf_counter()-start);save(raw/f'{label}.status.json',status)
        if status['exit_code']!=0:
            result['failures'].append(status);save(W/'model-results.json',result);raise RuntimeError(f'Preserved failed case {label}')
        x=load(raw/f'{label}.stdout.json');assert x['probe']=='GROWTHMODEL075' and x['mode']=='hybrid' and len(x['samples'])==64 and len(x['fresh_recovery'])==12
        result['cases'].append({'label':label,'spec':spec,**{key:sha(raw/f'{label}.{suffix}') for suffix,key in [('stdout.json','stdout_sha256'),('stderr.txt','stderr_sha256'),('status.json','status_sha256')]}});save(W/'model-results.json',result)
        print(json.dumps({'completed':index+1,'total':54,'label':label,'max_publication_ms':max(s['outer_ms'] for s in x['samples']),'migration_ms':x['migration_ms'],'wall_seconds':status['wall_seconds']}),flush=True)
    result.update(complete=True,completed_utc=now());save(W/'model-results.json',result)
if __name__=='__main__':
    if sys.argv[1:]==['--initialize']:initialize()
    else:assert not sys.argv[1:];run()
