"""Matched closed-loop embedded API probe, after open-loop loads have stopped.

Compiles identical probe text on verified copies of both source trees, serially.
No JSON/network/Python client loop is inside these timed requests. This is not
an arrival-rate qualification or a comparison with another database engine.
"""
import datetime
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from stress_compare import percentile

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent.parent/'work'


def main():
    output=ROOT/'benchmarks/retry-035-direct.json'
    assert not output.exists(),'Preserve existing direct evidence'
    assert json.loads((ROOT/'benchmarks/timed-035-final-run-order.json').read_text())[-1]['returncode']==0
    build=json.loads((ROOT/'benchmarks/rust-checks-035-final.json').read_text())
    base=json.loads((ROOT/'benchmarks/baseline-0.3.4-provenance.json').read_text())
    work=WORK/f'direct-retry-{time.time_ns()}'
    work.mkdir()
    probe=ROOT/'benchmarks/live_retry_inprocess.rs'
    report={'methodology':'closed-loop embedded LiveArchive append; one known 100-row payload; 1/16/64 caller threads; five seconds; three alternating rounds; every receipt asserted; systematic latency sample every 64 calls per worker; all attempts counted; no JSON/network/Python client inside timing; seed, publication, full scrub and compression outside timer; not an open-loop capacity/SLO result',
        'probe_source_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),'builds':{},'cases':[],'failed_cases':[],'run_order':[]}
    samples=ROOT/'benchmarks/retry-035-direct-samples'
    samples.mkdir(exist_ok=True)
    binaries={}
    for variant,version,source_root,proof in [('baseline','0.3.4',ROOT/'benchmarks/baseline-0.3.4-source',base['core_source_sha256']),
        ('candidate','0.3.5',ROOT,build['source_sha256'])]:
        checkout=work/(variant+'-source')
        checkout.mkdir()
        for relative,digest in proof.items():
            source=source_root/relative
            assert hashlib.sha256(source.read_bytes()).hexdigest()==digest,relative
            destination=checkout/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,destination)
        shutil.copy2(probe,checkout/'examples/live_retry_inprocess.rs')
        environment={**os.environ,'CARGO_TARGET_DIR':str(work/(variant+'-target')),'TMP':str(WORK/'rust-temp-032'),'TEMP':str(WORK/'rust-temp-032')}
        started=datetime.datetime.now(datetime.timezone.utc).isoformat()
        for job,command in [('build',['cargo','build','--release','--example','live_retry_inprocess','--offline','--locked']),
            ('clippy',['cargo','clippy','--example','live_retry_inprocess','--offline','--locked','--','-D','warnings'])]:
            print(variant+' '+job,flush=True)
            result=subprocess.run(command,cwd=checkout,env=environment,text=True,capture_output=True)
            (ROOT/'benchmarks/build-035-final-logs'/f'direct-{variant}-{job}.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
            assert result.returncode==0,result.stderr
        binary=work/(variant+'-target')/'release/examples/live_retry_inprocess.exe'
        binaries[variant]=binary
        report['builds'][variant]={'version':version,'core_source_sha256':proof,'probe_source_sha256':report['probe_source_sha256'],
            'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'binary_path':str(binary),'started_at_utc':started,
            'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    seed=WORK/'perf-035/final/receipt-seed.exe'
    for turn in range(3):
        order=['baseline','candidate'] if turn%2==0 else ['candidate','baseline']
        for clients in [1,16,64]:
            for variant in order:
                directory=work/f'{turn}-{clients}-{variant}'
                subprocess.check_output([str(seed),str(directory), '50000','1000000'],text=True,timeout=120)
                started=datetime.datetime.now(datetime.timezone.utc).isoformat()
                print(f'round {turn+1}, {clients} callers, {variant}',flush=True)
                try:
                    result=json.loads(subprocess.check_output([str(binaries[variant]),str(directory),str(clients),'5'],text=True,timeout=30))
                    finished=datetime.datetime.now(datetime.timezone.utc).isoformat()
                    assert result['version']==report['builds'][variant]['version']
                    assert result['all_receipts_valid'] and result['no_publications_during_load'] and result['full_scrub_passed']
                    if variant=='candidate':
                        assert result['ingest_after']['fast_retry_hits']-result['ingest_before']['fast_retry_hits']==result['successful_calls']
                    raw=result.pop('latency_ns_samples')
                    file=samples/f'{variant}-{clients}-{turn}.json.gz'
                    with gzip.open(file,'wt',encoding='utf-8') as stream:
                        json.dump(raw,stream,separators=(',',':'))
                    result.update(variant=variant,round=turn,sampled_calls=len(raw),sampled_latency_us={name:percentile(raw,p)/1000 for name,p in [('p50',.5),('p95',.95),('p99',.99)]},raw_latency_samples=str(file.relative_to(ROOT/'benchmarks')))
                    report['cases'].append(result)
                    report['run_order'].append({'variant':variant,'round':turn,'clients':clients,'started_at_utc':started,'completed_at_utc':finished})
                    print(json.dumps({k:result[k] for k in ['variant','clients','successful_rps_in_window','sampled_latency_us']}),flush=True)
                except Exception as error:
                    report['failed_cases'].append({'variant':variant,'round':turn,'clients':clients,'error':repr(error)})
                    raise
                finally:
                    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
                resolved=directory.resolve()
                assert resolved.is_relative_to(work.resolve()) and resolved!=work.resolve()
                shutil.rmtree(resolved)
    assert len(report['cases'])==18 and not report['failed_cases']


if __name__=='__main__':
    main()
