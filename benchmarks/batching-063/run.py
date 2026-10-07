"""Fresh serial batching controls on one immutable released executable."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import shutil
import traceback
from stress_compare import Engine, run_load, percentile
from host_telemetry import HostMonitor

W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
policy=load(W/'policy.json')
recovery=load(W/'recovery.json')
assert len(recovery['cycles'])==24 and not recovery['failed_cases']
assert not load(W/'pre-timing-process-check.json')['active_processes']
binary=W/'binaries/released-016.exe'
assert sha(binary)==policy['binary_sha256']==recovery['binary_sha256']
out=W/'paired-service.json'
assert not out.exists()
fixtures=W/'service-fixtures'; fixtures.mkdir()
samples=W/'paired-service-samples'; samples.mkdir()
report={'trial':63,'status':'optional current-release batching; supported default unchanged',
    'policy_sha256':sha(W/'policy.json'),'binary_sha256':sha(binary),'recovery_sha256':sha(W/'recovery.json'),
    'harness_sha256':{p.name:sha(p) for p in [Path(__file__),ROOT/'benchmarks/stress_compare.py',ROOT/'benchmarks/host_telemetry.py']},
    'method':'fresh 1M-row stores, 64 clients, 100-row batches, Latin-square rotation; one frozen binary; durable synchronized ACK; setup/checks/CRC outside arrival window; no competing task-heavy job',
    'cases':[],'failed_cases':[],'complete':False,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def save(): out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
save()
for turn in range(4):
    for index,(profile,rate,seconds) in enumerate(policy['comparison']['configs']):
        variants=list(policy['variants']); shift=(turn+index)%4
        variants=variants[shift:]+variants[:shift]
        for variant in variants:
            label=f'{turn}-{variant}-{profile}-{rate}-{seconds}'
            engine=None; failed=False
            print('START '+label,flush=True)
            try:
                free=shutil.disk_usage(W).free
                assert free>policy['comparison']['disk_preflight_min_free_bytes'],free
                started=datetime.datetime.now(datetime.timezone.utc).isoformat()
                delay=policy['variants'][variant]
                engine=Engine('kestrel',fixtures/label,1_000_000,binary,{},bridge_args=(delay,0))
                assert engine.version==policy['version'] and engine.bridge_info['group_delay_ms']==delay
                with HostMonitor() as monitor:
                    case=run_load(engine,profile,64,seconds,rate,100)
                raw=case.pop('samples'); case['operation_latency_ms']={}
                for op in ['query','append']:
                    chosen=[s for s in raw if s['ok'] and s['operation']==op]
                    case['operation_latency_ms'][op]={'successful':len(chosen),
                        **{name:percentile([s['latency_ms'] for s in chosen],q) for name,q in [('p50',.5),('p95',.95),('p99',.99)]},
                        'service_p99':percentile([s['service_ms'] for s in chosen],.99)}
                sf=samples/(label+'.jsonl.gz')
                with gzip.open(sf,'wt',encoding='utf-8') as f:
                    for s in raw: f.write(json.dumps(s,separators=(',',':'))+'\n')
                case.update(variant=variant,round=turn,group_delay_ms=delay,host_telemetry=monitor.arrival_samples(case),
                    raw_samples_file=sf.relative_to(W).as_posix(),raw_samples_sha256=sha(sf),fixture=str(engine.directory),
                    disk_free_before_case_bytes=free,case_started_utc=started,
                    case_finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
                report['cases'].append(case)
                print(json.dumps({k:case[k] for k in ['variant','round','profile','group_delay_ms','latency_ms','operation_latency_ms','unsuccessful_or_unexecuted']}),flush=True)
            except Exception as error:
                report['failed_cases'].append({'label':label,'error':repr(error),'traceback':traceback.format_exc()})
                print('FAILED '+repr(error),flush=True); failed=True
            finally:
                if engine is not None: engine.finish()
                save()
            if failed: raise RuntimeError('Preserved failed attempt; inspect before continuation')
assert len(report['cases'])==32 and not report['failed_cases']
report['complete']=True; report['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
save(); print('All 32 batching cases completed',flush=True)
