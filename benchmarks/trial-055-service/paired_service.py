"""Predeclared local CAT6 compact-receipt service trial 055, paired with frozen 0.3.16."""
from pathlib import Path
import datetime,gzip,hashlib,json,shutil,time
from stress_compare import Engine,run_load,percentile
from host_telemetry import HostMonitor

w=Path(__file__).parent;root=w.parents[1]/'outputs/kestrel-sql'
out=w/'paired-service.json';assert not out.exists()
assert json.loads((w/'correctness-gates.json').read_text(encoding='utf-8'))['complete']
policy=json.loads((w/'policy.json').read_text(encoding='utf-8'))
bins={'baseline':root/'bin/baseline-0.3.16/kestrel-stress.exe','bundle_trial':w/'bin/kestrel-stress.exe'}
fixtures=w/'service-fixtures';fixtures.mkdir();samples=w/'paired-service-samples';samples.mkdir()
configs=[*[(profile,64,seconds,rate) for profile,rate,seconds in policy['comparison']['profiles']],('read',64,8,2000),('scan',64,8,100)]
report={'status':'055 service on unchanged frozen CAT6 053; inherited version string 0.3.16 is not a supported release; no promotion','policy_sha256':hashlib.sha256((w/'policy.json').read_bytes()).hexdigest(),'base_rows':1000000,'rounds':3,'method':'unchanged historical stress_compare.run_load, fresh matched stores, alternate variant order; scheduled-arrival latency includes queueing; synchronized durable ACK; 100-row batches; group delay zero; host sampling only during load; no builds/tests/packaging concurrent with timing','limits':'single shared Windows machine; no physical power loss, distributed activity or universal superiority qualification','binary_sha256':{v:hashlib.sha256(p.read_bytes()).hexdigest() for v,p in bins.items()},'harness_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),root/'benchmarks/stress_compare.py',root/'benchmarks/host_telemetry.py']},'cases':[],'failed_cases':[],'complete':False,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def save():out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
save()
for turn in range(3):
    for index,(profile,clients,seconds,rate) in enumerate(configs):
        variants=list(bins)
        if (turn+index)%2:variants.reverse()
        for variant in variants:
            label=f'{turn}-{variant}-{profile}-{rate}-{seconds}';directory=fixtures/label;engine=None
            print('START '+label,flush=True)
            try:
                free=shutil.disk_usage(w).free;assert free>1000000000,free
                engine=Engine('kestrel',directory,1000000,bins[variant],{},bridge_args=(0,0))
                assert engine.version=='0.3.16' and engine.bridge_info['group_delay_ms']==0
                with HostMonitor() as monitor:case=run_load(engine,profile,clients,seconds,rate,100)
                raw=case.pop('samples');case['operation_latency_ms']={}
                for op in ['query','append']:
                    selected=[v for v in raw if v['ok'] and v['operation']==op]
                    case['operation_latency_ms'][op]={'successful':len(selected),'p50':percentile([v['latency_ms'] for v in selected],.5),'p95':percentile([v['latency_ms'] for v in selected],.95),'p99':percentile([v['latency_ms'] for v in selected],.99),'service_p99':percentile([v['service_ms'] for v in selected],.99)}
                sf=samples/(label+'.jsonl.gz')
                with gzip.open(sf,'wt',encoding='utf-8') as f:
                    for v in raw:f.write(json.dumps(v,separators=(',',':'))+'\n')
                case.update(variant=variant,round=turn,host_telemetry=monitor.arrival_samples(case),raw_samples_file=sf.relative_to(w).as_posix(),raw_samples_sha256=hashlib.sha256(sf.read_bytes()).hexdigest(),disk_free_before_case_bytes=free,fixture=str(directory))
                report['cases'].append(case)
                print(json.dumps({k:case[k] for k in ['variant','profile','scheduled_seconds','offered_rps','latency_ms','operation_latency_ms','unsuccessful_or_unexecuted']}),flush=True)
            except Exception as error:
                report['failed_cases'].append({'label':label,'error':repr(error)});print('FAILED '+repr(error),flush=True)
            finally:
                if engine is not None:engine.finish()
                save()
assert not report['failed_cases'],report['failed_cases']
assert len(report['cases'])==36
report['complete']=True;report['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();print('36 paired cases completed',flush=True)
