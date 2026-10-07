"""Frozen serial stage diagnostics, six cases; no speedup or competing engine."""
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess, sys, time
from pathlib import Path
W=Path(__file__).resolve().parent;BIN=W/'trace-binaries/trace_probe.exe'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()
def initialize():
    assert not (W/'diagnostic-policy.json').exists() and not (W/'diagnostic-results.json').exists()
    assert load(W/'qualification-audit.json')['passed']
    assert load(W/'pre-timing-process-check.json')['active_processes']==[]
    trial=load(W/'policy.json');assert trial['diagnostics']['cases']==6
    build=load(W/'lab/outputs/kestrel-sql/benchmarks/rust-checks-068.json')
    assert sha(BIN)==build['frozen_binary_sha256']['trace-binaries\\trace_probe.exe']
    cases=[]
    for turn in range(2):
        sizes=[0,50000,99000];sizes=sizes[turn:]+sizes[:turn]
        cases.extend({'round':turn,'seed_receipts':size,'repetitions':128,'batch_rows':100} for size in sizes)
    save(W/'diagnostic-policy.json',{'declared_utc':now(),'before_first_diagnostic_case':True,
        'trial_policy_sha256':sha(W/'policy.json'),'qualification_audit_sha256':sha(W/'qualification-audit.json'),
        'binary_sha256':sha(BIN),'probe_source_sha256':sha(W/'lab/outputs/kestrel-sql/examples/trace_probe.rs'),
        'harness_sha256':sha(Path(__file__)),'independent_auditor_sha256':sha(W/'audit_diagnostics.py'),
        'cases':cases,'minimum_free_bytes':2000000000,'timeout_seconds':600,
        'slow_event_threshold_ms':500,'stage_sum_tolerance_ms':0.000001,
        'no_competitor_or_speedup_claim':True,'feature_overhead_unmeasured':True,'promotion_allowed':False,
        'maintenance_compact_and_reclaim_separate':True,
        'all_cases_and_events_retained_no_retry_or_threshold_change':True,
        'process_policy':'One task-owned local probe at a time; no compilation, oracle/audit, Git or packaging during timed cases'})
    print(json.dumps({'initialized':True,'diagnostic_cases':len(cases)}),flush=True)
def run():
    p=load(W/'diagnostic-policy.json');assert not (W/'diagnostic-results.json').exists()
    for path,key in [(BIN,'binary_sha256'),(W/'policy.json','trial_policy_sha256'),(W/'qualification-audit.json','qualification_audit_sha256'),(W/'lab/outputs/kestrel-sql/examples/trace_probe.rs','probe_source_sha256'),(Path(__file__),'harness_sha256'),(W/'audit_diagnostics.py','independent_auditor_sha256')]:assert sha(path)==p[key],path
    (W/'diagnostic-raw').mkdir();(W/'diagnostic-fixtures').mkdir()
    out={'started_utc':now(),'policy_sha256':sha(W/'diagnostic-policy.json'),'complete':False,'cases':[],'failures':[]}
    save(W/'diagnostic-results.json',out)
    for index,spec in enumerate(p['cases']):
        label=f"{index:02d}-r{spec['round']}-{spec['seed_receipts']}";store=W/'diagnostic-fixtures'/label;raw=W/'diagnostic-raw'
        free=shutil.disk_usage(W).free
        if free<p['minimum_free_bytes']:
            out['failures'].append({'label':label,'not_started':True,'free_bytes':free});save(W/'diagnostic-results.json',out);raise RuntimeError('Disk preflight failed; no case restarted')
        argv=[str(BIN),str(store),str(spec['seed_receipts']),str(spec['repetitions'])]
        status={'spec':spec,'label':label,'argv':argv,'fixture':str(store),'started_utc':now(),'free_bytes_before':free}
        started=time.perf_counter()
        with (raw/f'{label}.stdout.json').open('w',encoding='utf-8') as stdout,(raw/f'{label}.stderr.txt').open('w',encoding='utf-8') as stderr:
            process=subprocess.Popen(argv,stdout=stdout,stderr=stderr);status['pid']=process.pid
            try:status['exit_code']=process.wait(timeout=p['timeout_seconds'])
            except subprocess.TimeoutExpired:
                process.kill();process.wait();status.update(exit_code=process.returncode,timeout=True)
        status.update(ended_utc=now(),wall_seconds=time.perf_counter()-started)
        save(raw/f'{label}.status.json',status)
        if status['exit_code']!=0:
            out['failures'].append(status);save(W/'diagnostic-results.json',out);raise RuntimeError(f'Preserved failed diagnostic case {label}')
        result=load(raw/f'{label}.stdout.json')
        assert result['version']=='0.3.17-dev.68' and result['probe']=='KSQLTRACE068'
        assert len(result['events'])==131 and len(result['reclaim'])==3
        assert all(result[n] for n in ['rows_and_sum_match','reopen_original_generations_retry_and_full_scrub_passed','cold_trace_and_retry_remain_empty'])
        out['cases'].append({'spec':spec,'label':label,'stdout_sha256':sha(raw/f'{label}.stdout.json'),'status_sha256':sha(raw/f'{label}.status.json'),'stderr_sha256':sha(raw/f'{label}.stderr.txt')});save(W/'diagnostic-results.json',out)
        print(json.dumps({'completed':index+1,'total':6,'label':label,'events':131,'wall_seconds':status['wall_seconds'],'max_append_ms':max(e['outer_ms'] for e in result['events'] if e['operation']=='append')}),flush=True)
    out.update(complete=True,completed_utc=now());save(W/'diagnostic-results.json',out)
if __name__=='__main__':
    if sys.argv[1:]==['--initialize']:initialize()
    else:assert not sys.argv[1:];run()
