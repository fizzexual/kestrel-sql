"""Serial Rust qualification of an opt-in diagnostic feature; no timed workload."""
from datetime import datetime, timezone
import hashlib, json, os, re, shutil, subprocess, sys
from pathlib import Path
W=Path(__file__).resolve().parent;LAB=W/'lab/outputs/kestrel-sql';WORK=W/'lab/work'

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()

assert not (LAB/'benchmarks/rust-checks-068.json').exists()
logs=LAB/'benchmarks/build-068-logs';logs.mkdir()
targets={m:WORK/f'kestrel-068-{m}-build' for m in ['trace','fault','fault-only']}
targets['default']=WORK/'kestrel-068-build'
env={**os.environ,'TMP':str(WORK/'rust-temp-032'),'TEMP':str(WORK/'rust-temp-032'),
     'KESTREL_TEST_ROOT':str(WORK/'cargo-tests')}
jobs=[
    ('fmt','default',['cargo','fmt','--check']),
    ('default-clippy','default',['cargo','clippy','--all-targets','--offline','--locked','--','-D','warnings']),
    ('default-build','default',['cargo','build','--release','--bins','--offline','--locked']),
    ('debug','trace',['cargo','test','--features','publication-trace','--offline','--locked']),
    ('release','trace',['cargo','test','--release','--features','publication-trace','--offline','--locked']),
    ('trace-clippy','trace',['cargo','clippy','--all-targets','--features','publication-trace','--offline','--locked','--','-D','warnings']),
    ('trace-build','trace',['cargo','build','--release','--bins','--examples','--features','publication-trace','--offline','--locked']),
    ('fault-only-clippy','fault-only',['cargo','clippy','--all-targets','--features','fault-injection','--offline','--locked','--','-D','warnings']),
    ('trace-fault-clippy','fault',['cargo','clippy','--all-targets','--features','publication-trace,fault-injection','--offline','--locked','--','-D','warnings']),
    ('trace-fault-build','fault',['cargo','build','--release','--example','publication_fault_probe','--example','live_retry_probe','--example','source_fault_probe','--features','publication-trace,fault-injection','--offline','--locked']),
    ('source-adapter','trace',[sys.executable,str(LAB/'benchmarks/build_source_adapter_068.py')]),
]
frozen=WORK/'perf-068/candidate';frozen.mkdir(parents=True)
records=[];counts={}
for name,mode,argv in jobs:
    print('starting',name,flush=True)
    started=now()
    result=subprocess.run(argv,cwd=LAB,env={**env,'CARGO_TARGET_DIR':str(targets[mode])},text=True,capture_output=True)
    (logs/(name+'.txt')).write_text(result.stdout+result.stderr,encoding='utf-8')
    records.append({'job':name,'mode':mode,'command':argv,'started_at_utc':started,'completed_at_utc':now(),'returncode':result.returncode})
    save(logs/'run-order.json',records)
    assert result.returncode==0,(name,result.stdout,result.stderr)
    if name in ['debug','release']:
        counts[name]=sum(map(int,re.findall(r'test result: ok\. (\d+) passed;',result.stdout)))
    print(name,'passed',flush=True)
assert counts=={'debug':80,'release':80},counts
proof={'version':'0.3.17-dev.68','rust_tests':{**counts,'passed':True},'format_check':'passed',
       'clippy_warnings_as_errors':'passed','feature_clippy_warnings_as_errors':'passed',
       'four_strict_clippy_modes_passed':True,'build_run_order':records,
       'default_tests_not_repeated':{'historical_released_tests':77,'new_trace_tests':3,'all_77_existing_tests_executed_with_trace_in_debug_and_release':True},
       'completed_utc':now(),'frozen_binary_sha256':{}}
for name in ['kestrel','kestrel-stress','performance-probe','scan-profile','group-probe','publication-probe','receipt-seed']:
    folder='examples' if name not in ['kestrel','kestrel-stress'] else ''
    source=targets['trace']/'release'/folder/(name.replace('-','_')+'.exe' if folder else name+'.exe')
    destination=frozen/(name+'.exe');shutil.copy2(source,destination)
    data=destination.read_bytes();assert b'KESTREL_FAULT_POINT' not in data and b'KESTREL_LIVE_PAUSE' not in data
    proof['frozen_binary_sha256'][str(destination.relative_to(W))]=sha(destination)
for folder in ['trace-binaries','default-binaries','fault-binaries']:(W/folder).mkdir()
p=W/'trace-binaries/trace_probe.exe';shutil.copy2(targets['trace']/'release/examples/trace_probe.exe',p)
assert b'KSQLTRACE068' in p.read_bytes() and b'KESTREL_FAULT_POINT' not in p.read_bytes()
proof['frozen_binary_sha256'][str(p.relative_to(W))]=sha(p)
for n in ['kestrel','kestrel-stress']:
    p=W/'default-binaries'/(n+'.exe');shutil.copy2(targets['default']/'release'/(n+'.exe'),p)
    data=p.read_bytes();assert all(s not in data for s in [b'KSQLTRACE068',b'last_publication_trace',b'KESTREL_FAULT_POINT',b'KESTREL_LIVE_PAUSE'])
    proof['frozen_binary_sha256'][str(p.relative_to(W))]=sha(p)
for n in ['publication_fault_probe','live_retry_probe','source_fault_probe']:
    p=W/'fault-binaries'/(n+'.exe');shutil.copy2(targets['fault']/'release/examples'/(n+'.exe'),p)
    proof['frozen_binary_sha256'][str(p.relative_to(W))]=sha(p)
proof['frozen_binary_sha256'][str((frozen/'source-pipeline-typed.exe').relative_to(W))]=sha(frozen/'source-pipeline-typed.exe')
paths=[LAB/'Cargo.toml',LAB/'Cargo.lock',*LAB.glob('src/**/*.rs'),*LAB.glob('tests/*.rs'),*LAB.glob('examples/*.rs')]
proof['source_sha256']={p.relative_to(LAB).as_posix():sha(p) for p in sorted(paths)}
save(LAB/'benchmarks/rust-checks-068.json',proof)
save(W/'source-provenance.json',{'baseline':json.loads((W/'baseline.json').read_text(encoding='utf-8'))['core_source_sha256'],'candidate':proof['source_sha256']})
print(json.dumps({'complete':True,'tests_each':80,'strict_clippy_modes':4,'frozen_binaries':len(proof['frozen_binary_sha256'])}),flush=True)
