"""Complete only seven cases skipped by the original pre-Engine disk guard."""
from pathlib import Path
import datetime,gzip,hashlib,json,shutil
from stress_compare import Engine,run_load,percentile
from host_telemetry import HostMonitor
w=Path(__file__).resolve().parent;root=w.parents[1]/'outputs/kestrel-sql'
out=w/'paired-service.json';report=json.loads(out.read_text())
failure=json.loads((w/'preflight-failure-preservation.json').read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert len(report['cases'])==29 and len(report['failed_cases'])==7 and not report['complete']
assert not report.get('resumption'), 'Do not restart a partial resumption'
for rel,d in failure['completed_raw_sha256'].items():assert sha(w/rel)==d
for name,d in failure['failed_attempt_snapshot_sha256'].items():assert sha(w/'disk-space-preflight-failure'/name)==d
assert sha(w/'paired_service.py')==report['harness_sha256']['paired_service.py']
policy=json.loads((w/'policy.json').read_text());assert sha(w/'policy.json')==report['policy_sha256']
bins={'baseline':root/'bin/baseline-0.3.16/kestrel-stress.exe','bundle_trial':w/'bin/kestrel-stress.exe'}
for v,p in bins.items():assert sha(p)==report['binary_sha256'][v]
configs=[*[(profile,64,seconds,rate) for profile,rate,seconds in policy['comparison']['profiles']],('read',64,8,2000),('scan',64,8,100)]
specs=[]
for turn in range(3):
    for index,(profile,clients,seconds,rate) in enumerate(configs):
        variants=list(bins)
        if (turn+index)%2:variants.reverse()
        for variant in variants:specs.append((turn,variant,profile,clients,seconds,rate))
def label(s):
    turn,variant,profile,clients,seconds,rate=s
    return f'{turn}-{variant}-{profile}-{rate}-{seconds}'
assert [f"{c['round']}-{c['variant']}-{c['profile']}-{c['offered_rps']}-{c['scheduled_seconds']}" for c in report['cases']]==[label(s) for s in specs[:29]]
assert [c['label'] for c in report['failed_cases']]==[label(s) for s in specs[29:]]
for s in specs[29:]:assert not (w/'service-fixtures'/label(s)).exists(), 'Never replace a timed fixture'
report['preserved_preflight_failures']=report['failed_cases']
report['failed_cases']=[]
report['resumption']={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'script_sha256':sha(Path(__file__)),'prior_report_sha256':sha(w/'disk-space-preflight-failure/paired-service.json'),
    'completed_cases_preserved':29,'preflight_skipped_cases':7,'reason':'Prior 1GB disk headroom guard before Engine construction; unchanged guard, no timed case rerun',
    'original_failure_report_retained':True,'only_missing_cases_executed':True}
def save():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
save()
for turn,variant,profile,clients,seconds,rate in specs[29:]:
    name=label((turn,variant,profile,clients,seconds,rate));directory=w/'service-fixtures'/name;engine=None
    print('RESUME '+name,flush=True)
    try:
        free=shutil.disk_usage(w).free;assert free>1000000000,free
        engine=Engine('kestrel',directory,1000000,bins[variant],{},bridge_args=(0,0))
        assert engine.version=='0.3.16' and engine.bridge_info['group_delay_ms']==0
        with HostMonitor() as monitor:case=run_load(engine,profile,clients,seconds,rate,100)
        raw=case.pop('samples');case['operation_latency_ms']={}
        for op in ['query','append']:
            selected=[v for v in raw if v['ok'] and v['operation']==op]
            case['operation_latency_ms'][op]={'successful':len(selected),'p50':percentile([v['latency_ms'] for v in selected],.5),'p95':percentile([v['latency_ms'] for v in selected],.95),'p99':percentile([v['latency_ms'] for v in selected],.99),'service_p99':percentile([v['service_ms'] for v in selected],.99)}
        sf=w/'paired-service-samples'/(name+'.jsonl.gz')
        assert not sf.exists()
        with gzip.open(sf,'wt',encoding='utf-8') as f:
            for v in raw:f.write(json.dumps(v,separators=(',',':'))+'\n')
        case.update(variant=variant,round=turn,host_telemetry=monitor.arrival_samples(case),raw_samples_file=sf.relative_to(w).as_posix(),raw_samples_sha256=sha(sf),disk_free_before_case_bytes=free,fixture=str(directory),resumed_after_preflight_only=True)
        report['cases'].append(case)
        print(json.dumps({k:case[k] for k in ['variant','profile','scheduled_seconds','offered_rps','latency_ms','operation_latency_ms','unsuccessful_or_unexecuted']}),flush=True)
    except Exception as error:
        report['failed_cases'].append({'label':name,'error':repr(error),'resume_attempt':True});print('FAILED '+repr(error),flush=True)
    finally:
        if engine is not None:engine.finish()
        save()
assert not report['failed_cases'] and len(report['cases'])==36
for rel,d in failure['completed_raw_sha256'].items():assert sha(w/rel)==d
report['complete']=True;report['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
report['resumption'].update(completed_utc=report['completed_utc'],all_29_original_raw_files_unchanged=True,seven_preflight_skipped_cases_completed=True)
save();print('36 cases complete; original 29 timings and seven preflight failures preserved',flush=True)
