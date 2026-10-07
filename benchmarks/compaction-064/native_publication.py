"""Frozen 27-case serial A/A/candidate trial; never replace completed cases."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess,time,sys
from process_memory import peak_memory
W=Path(__file__).resolve().parent
BIN={'baseline_a':W/'native-binaries/baseline-publication.exe','baseline_b':W/'native-binaries/baseline-publication.exe','candidate':W/'native-binaries/candidate-publication.exe'}
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()
def initialize():
    assert not (W/'native-policy.json').exists() and not (W/'native-results.json').exists()
    assert load(W/'qualification-audit.json')['passed'] and load(W/'native-smoke.json')['passed']
    policy=load(W/'policy.json');build=load(W/'native-driver-build.json');assert build['complete']
    assert sha(BIN['baseline_a'])==sha(BIN['baseline_b'])==build['baseline_sha256']
    assert sha(BIN['candidate'])==build['candidate_sha256']
    cases=[];labels=policy['native']['variants']
    for turn in range(3):
        for size_index,size in enumerate(policy['native']['starting_receipt_counts']):
            k=(turn+size_index)%3
            for label in labels[k:]+labels[:k]:
                cases.append({'round':turn,'seed_receipts':size,'variant':label,'repetitions':256,'batch_rows':100})
    save(W/'native-policy.json',{'declared_utc':now(),'before_first_performance_case':True,'trial_policy_sha256':sha(W/'policy.json'),
        'qualification_audit_sha256':sha(W/'qualification-audit.json'),'driver_build_sha256':sha(W/'native-driver-build.json'),
        'binary_sha256':{k:sha(v) for k,v in BIN.items()},'driver_sha256':sha(W/'native_publication_probe.rs'),
        'harness_sha256':sha(Path(__file__)),'memory_helper_sha256':sha(W/'process_memory.py'),'cases':cases,
        'aggregation':'For each size, median of three matched per-round ratios; all raw pairs retained; never ratio of pooled medians',
        'primary_total':'sum of 256 append latencies plus all compact_small+reclaim maintenance latencies',
        'identity_metrics':['append_plus_maintenance_ms','p99_ms','p50_ms','max_ms','reopen_ms','peak_working_set_bytes'],
        'memory_scope':'Full-process peak includes seed and verification; peak commit also reported; not isolated compaction allocation',
        'timeout_seconds_per_case':600,'minimum_free_bytes_before_case':500000000,'failed_case_policy':'Preserve and stop; never replace or silently restart',
        'smoke_excluded':True,'process_policy':'One task-owned native probe at a time; no build, tests, audit, packaging, Git or cache reclamation during workload'})
    print(json.dumps({'initialized':True,'cases':len(cases),'before_timing':True}),flush=True)
def run():
    p=load(W/'native-policy.json');assert not (W/'native-results.json').exists()
    for k,b in BIN.items():assert sha(b)==p['binary_sha256'][k]
    for name,key in [('policy.json','trial_policy_sha256'),('native_publication_probe.rs','driver_sha256'),('native_publication.py','harness_sha256'),('process_memory.py','memory_helper_sha256')]:assert sha(W/name)==p[key]
    (W/'native-raw').mkdir();(W/'native-fixtures').mkdir()
    report={'started_utc':now(),'native_policy_sha256':sha(W/'native-policy.json'),'cases':[],'failures':[],'complete':False};save(W/'native-results.json',report)
    for index,spec in enumerate(p['cases']):
        label=f"{index:02d}-r{spec['round']}-{spec['seed_receipts']}-{spec['variant']}"
        store=W/'native-fixtures'/label;raw=W/'native-raw';free=shutil.disk_usage(W).free
        if free<p['minimum_free_bytes_before_case']:
            report['failures'].append({'label':label,'case_not_started':True,'free_bytes':free});save(W/'native-results.json',report);raise RuntimeError('Disk preflight failed before case start')
        status={'spec':spec,'label':label,'started_utc':now(),'fixture':str(store),'free_bytes_before':free}
        argv=[str(BIN[spec['variant']]),str(store),str(spec['seed_receipts']),str(spec['repetitions'])];status['argv']=argv
        started=time.perf_counter()
        with (raw/f'{label}.stdout.json').open('w',encoding='utf-8') as out,(raw/f'{label}.stderr.txt').open('w',encoding='utf-8') as err:
            process=subprocess.Popen(argv,stdout=out,stderr=err);status['pid']=process.pid
            try:status['exit_code']=process.wait(timeout=p['timeout_seconds_per_case'])
            except subprocess.TimeoutExpired:
                process.kill();process.wait();status.update(exit_code=process.returncode,timeout=True)
            status['memory']=peak_memory(process)
        status.update(wall_seconds=time.perf_counter()-started,ended_utc=now())
        save(raw/f'{label}.status.json',status)
        if status['exit_code']!=0:
            report['failures'].append(status);save(W/'native-results.json',report);raise RuntimeError(f'Preserved failed case {label}')
        result=load(raw/f'{label}.stdout.json')
        assert result['version']==('0.3.17-dev.64' if spec['variant']=='candidate' else '0.3.16')
        assert result['rows_and_sum_match'] and result['reopen_retry_and_full_scrub_passed']
        assert result['prefill_receipt_count']==spec['seed_receipts'] and result['repetitions']==256
        assert len(result['raw_latency_ms'])==len(result['raw_catalog_bytes'])==256
        report['cases'].append({'spec':spec,'label':label,'stdout_sha256':sha(raw/f'{label}.stdout.json'),'status_sha256':sha(raw/f'{label}.status.json'),'stderr_sha256':sha(raw/f'{label}.stderr.txt')})
        save(W/'native-results.json',report)
        print(json.dumps({'completed':index+1,'total':27,'label':label,'wall_seconds':status['wall_seconds'],'maintenance_calls':len(result['maintenance_ms']),'max_append_ms':max(result['raw_latency_ms']),'memory_available':status['memory']['success']}),flush=True)
    report.update(completed_utc=now(),complete=True);save(W/'native-results.json',report)
if __name__=='__main__':
    if sys.argv[1:]==['--initialize']:initialize()
    else:assert not sys.argv[1:];run()
