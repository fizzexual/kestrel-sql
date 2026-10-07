"""Serial, isolated Rust qualification and frozen binaries; run before timed loads."""
import datetime
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent.parent/'work'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--tag',default='067')
    args=parser.parse_args()
    (WORK/'rust-temp-032').mkdir(parents=True,exist_ok=True)
    (WORK/'cargo-tests').mkdir(parents=True,exist_ok=True)
    tag=args.tag
    target=WORK/f'kestrel-{tag}-build'
    fault_target=WORK/f'kestrel-{tag}-fault-build'
    logs=ROOT/f'benchmarks/build-{tag}-logs'
    logs.mkdir()
    environment={**os.environ,'TMP':str(WORK/'rust-temp-032'),'TEMP':str(WORK/'rust-temp-032'),
        'KESTREL_TEST_ROOT':str(WORK/'cargo-tests'),'CARGO_TARGET_DIR':str(target)}
    jobs=[('fmt',['cargo','fmt','--check']),('debug',['cargo','test','--offline','--locked']),
        ('release',['cargo','test','--release','--offline','--locked']),
        ('clippy',['cargo','clippy','--all-targets','--offline','--locked','--','-D','warnings']),
        ('build',['cargo','build','--release','--bins','--examples','--offline','--locked']),
        ('fault-clippy',['cargo','clippy','--all-targets','--features','fault-injection','--offline','--locked','--','-D','warnings']),
        ('fault-build',['cargo','build','--release','--example','publication_fault_probe','--example','live_retry_probe','--example','source_fault_probe','--features','fault-injection','--offline','--locked'])]
    records=[]
    test_counts={}
    for name,command in jobs:
        if name.startswith('fault-'):
            environment['CARGO_TARGET_DIR']=str(fault_target)
        started=datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(name,flush=True)
        result=subprocess.run(command,cwd=ROOT,env=environment,text=True,capture_output=True)
        (logs/(name+'.txt')).write_text(result.stdout+result.stderr,encoding='utf-8')
        records.append({'job':name,'command':command,'started_at_utc':started,'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':result.returncode})
        (logs/'run-order.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
        assert result.returncode==0,(name,result.stdout,result.stderr)
        if name in ['debug','release']:
            test_counts[name]=sum(map(int,re.findall(r'test result: ok\. (\d+) passed;',result.stdout)))
    expected=81
    assert test_counts=={'debug':expected,'release':expected},test_counts
    frozen=WORK/('perf-'+tag+'/candidate')
    frozen.mkdir(parents=True,exist_ok=True)
    fields={'kestrel':'cli_sha256','kestrel-stress':'bridge_sha256','performance-probe':'probe_sha256','scan-profile':'scan_probe_sha256',
        'group-probe':'group_probe_sha256','publication-probe':'publication_probe_sha256','receipt-seed':'receipt_seed_sha256'}
    proof={'version':'0.3.17-dev.67','rust_tests':{**test_counts,'passed':True},'format_check':'passed','clippy_warnings_as_errors':'passed','feature_clippy_warnings_as_errors':'passed','build_run_order':records}
    for name,field in fields.items():
        folder='examples' if name in ['performance-probe','scan-profile','group-probe','publication-probe','receipt-seed'] else ''
        source=target/'release'/folder/(name.replace('-','_')+'.exe' if folder else name+'.exe')
        destination=frozen/(name+'.exe')
        shutil.copy2(source,destination)
        data=destination.read_bytes()
        assert b'KESTREL_LIVE_PAUSE' not in data and b'KESTREL_FAULT_POINT' not in data
        proof[field]=hashlib.sha256(data).hexdigest()
    for name,field in [('publication_fault_probe','fault_driver_sha256'),('live_retry_probe','live_retry_driver_sha256'),('source_fault_probe','source_fault_driver_sha256')]:
        source=fault_target/'release/examples'/(name+'.exe')
        proof[field]=hashlib.sha256(source.read_bytes()).hexdigest()
    paths=[ROOT/'Cargo.toml',ROOT/'Cargo.lock',*ROOT.glob('src/**/*.rs'),*ROOT.glob('tests/*.rs'),*ROOT.glob('examples/*.rs')]
    proof['source_sha256']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    (ROOT/f'benchmarks/rust-checks-{tag}.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'tests':test_counts,'frozen':str(frozen)}),flush=True)


if __name__=='__main__':
    main()
