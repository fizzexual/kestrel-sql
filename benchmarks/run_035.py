"""Serialize all confirmation workloads and subsequent untimed correctness jobs."""
import argparse
import datetime
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent.parent/'work'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=['timed','correctness'])
    parser.add_argument('--final',action='store_true')
    args=parser.parse_args()
    candidate=WORK/('perf-035/final' if args.final else 'perf-035/candidate')
    bridge=str(candidate/'kestrel-stress.exe')
    cli=str(candidate/'kestrel.exe')
    shared=['--baseline','bin/baseline-0.3.4/kestrel-stress.exe','--candidate',bridge,
        '--baseline-seed','bin/baseline-0.3.4/receipt-seed.exe','--candidate-seed',str(candidate/'receipt-seed.exe'),
        '--baseline-version','0.3.4','--candidate-version','0.3.5','--rounds','3']
    if args.phase=='timed':
        jobs=[('retry',['group_commit_compare.py',*shared,'--variants','baseline,baseline8,delay0,delay8',
                '--profiles','retry-only,retry-mixed','--seconds','15','--output','benchmarks/retry-035-confirmation.json']),
            ('retry-burst',['group_commit_compare.py',*shared,'--variants','baseline,delay0','--profiles','retry-burst',
                '--seconds','8','--output','benchmarks/retry-035-burst.json']),
            ('controls',['group_commit_compare.py',*shared,'--variants','baseline,delay0',
                '--profiles','anonymous-mixed,receipt-mixed,receipt-write','--seconds','15','--output','benchmarks/retry-035-controls.json']),
            ('reference',['group_commit_compare.py',*shared,'--variants','delay0,duckdb',
                '--profiles','anonymous-mixed','--seconds','15','--output','benchmarks/retry-035-reference.json'])]
        if args.final:
            jobs=[('final-retry',['group_commit_compare.py',*shared,'--variants','baseline,indexed0',
                '--profiles','retry-only,retry-mixed','--seconds','15','--output','benchmarks/retry-035-final-retry.json']),
                ('final-controls',['group_commit_compare.py',*shared,'--variants','baseline,delay0,indexed0',
                '--profiles','anonymous-mixed,receipt-mixed,receipt-write','--seconds','15','--output','benchmarks/retry-035-final-controls.json']),
                ('final-reference',['group_commit_compare.py',*shared,'--variants','delay0,indexed0,duckdb',
                '--profiles','anonymous-mixed','--seconds','15','--output','benchmarks/retry-035-final-reference.json'])]
    else:
        jobs=[('live-retry-faults',['live_retry_faults.py','--binary',bridge,'--driver',str(WORK/'kestrel-035-fault-build/release/examples/live_retry_probe.exe'),'--output','benchmarks/retry-035-faults.json']),
            ('publication-faults',['publication_faults.py','--binary',bridge,'--sql-binary',cli,'--fault-driver',str(WORK/'kestrel-035-fault-build/release/examples/publication_fault_probe.exe'),'--expected-version','0.3.5','--output','benchmarks/publication-035-faults.json']),
            ('group-kills',['group_commit_recovery.py','--binary',bridge,'--expected-version','0.3.5','--output','benchmarks/group-035-recovery.json']),
            ('pipeline',['live_pipeline_demo.py','--binary',bridge,'--group-delay-ms','8','--output','portfolio/live-pipeline-035-results.json']),
            ('differential',['archive_verify.py','--binary',cli,'--queries','500','--output','benchmarks/archive-035-verification.json']),
            ('retained',['recheck_release.py','--binary',cli,'--output','benchmarks/release-recheck-035.json'])]
        if args.final:
            for _,command in jobs:
                command[:]=[p.replace('kestrel-035-fault-build','kestrel-035-final-fault-build') for p in command]
                if command[0] in ['group_commit_recovery.py','live_pipeline_demo.py']:
                    command.append('--retry-index')
    log=ROOT/'benchmarks'/f"{args.phase}-035{'-final' if args.final else ''}-run-order.json"
    assert not log.exists(),'Keep historical attempts; choose a new log for a repair run'
    records=[]
    for name,arguments in jobs:
        record={'suite':name,'started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'started_monotonic_ns':time.perf_counter_ns(),
            'command':[sys.executable,'benchmarks/'+arguments[0],*arguments[1:]],
            'harness_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [ROOT/'benchmarks'/arguments[0],ROOT/'benchmarks/stress_compare.py',ROOT/'benchmarks/host_telemetry.py']}}
        print(name,flush=True)
        result=subprocess.run(record['command'],cwd=ROOT)
        record.update(returncode=result.returncode,completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_monotonic_ns=time.perf_counter_ns())
        records.append(record)
        log.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
        assert result.returncode==0,record


if __name__=='__main__':
    main()
