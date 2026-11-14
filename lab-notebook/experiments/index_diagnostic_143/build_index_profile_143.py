from pathlib import Path
from datetime import datetime,timezone
from ctypes import wintypes
import ctypes,hashlib,json,os,re,shutil,subprocess,traceback
R=Path('D:/Codex/Kestrel/work');W=R/'perf-143';C=W/'candidate'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=wintypes.HANDLE
k.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4
times=[wintypes.FILETIME() for _ in range(4)];assert k.GetProcessTimes(k.GetCurrentProcess(),*(ctypes.byref(t) for t in times))
creation=times[0].dwLowDateTime+(times[0].dwHighDateTime<<32)
def guard(label):
    r=subprocess.run(['D:/Codex/Migration-20261007/helper-runtime/powershell/pwsh.exe','-NoProfile','-File',str(R/'check_profile143_build_activity.ps1'),'-OwnerPid',str(os.getpid()),'-OwnerCreationFileTime',str(creation)],capture_output=True,timeout=30)
    row={'utc':now(),'before_job':label,'actual_exit':r.returncode,'stdout':r.stdout.decode('utf-8-sig'),'stderr':r.stderr.decode('utf-8-sig')}
    with (W/'build-activity.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(row)+'\n')
    assert r.returncode==0,row
policy=load(W/'policy.json');prep=load(W/'preparation-proof.json')
assert not (W/'build-proof.json').exists()
assert sha(C/'examples/index_profile_143.rs')==prep['kernel_source_sha256']
assert all(sha(C/n)==h for n,h in policy['supported_core_sha256'].items())
assert not any(n in os.environ for n in ['RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','CARGO_BUILD_TARGET'])
env=os.environ|{'CARGO_TARGET_DIR':str(W/'target'),'CARGO_INCREMENTAL':'0','CARGO_BUILD_JOBS':'4','TMP':str(W/'tmp'),'TEMP':str(W/'tmp')}
jobs=[('kernel-debug',['test','--example','index_profile_143']),('kernel-release',['test','--release','--example','index_profile_143']),
 ('kernel-lint',['clippy','--example','index_profile_143']),('artifact',['build','--release','--example','index_profile_143'])]
(W/'build-declaration.json').write_text(json.dumps({'jobs':jobs,'new_engine_tests':0,'kernel_only':True,'before_all_jobs':True},indent=2)+'\n',encoding='utf-8',newline='\n')
records=[]
try:
    for label,args in jobs:
        guard(label);argv=['C:/Users/Frizer/.cargo/bin/cargo.exe',*args,'--offline','--locked',*(['--','-D','warnings'] if label=='kernel-lint' else [])]
        print('START '+label,flush=True);started=now();r=subprocess.run(argv,cwd=C,env=env,capture_output=True,timeout=900,creationflags=0x08000000)
        (W/'logs'/(label+'.log')).write_bytes(r.stdout+r.stderr)
        row={'label':label,'started_utc':started,'completed_utc':now(),'actual_exit':r.returncode,'actual_wait_completed':True,'argv':argv}
        if label.startswith('kernel-') and label!='kernel-lint':row['fresh_kernel_tests']=sum(map(int,re.findall(rb'test result: ok\. (\d+) passed;',r.stdout)));assert row['fresh_kernel_tests']==3,row
        records.append(row);assert r.returncode==0,(label,r.stderr[-5000:],r.stdout[-2000:])
        print(json.dumps(row),flush=True)
    shutil.copy2(W/'target/release/examples/index_profile_143.exe',W/'binary/index_profile143.exe')
    assert all(sha(C/n)==h for n,h in policy['supported_core_sha256'].items())
    assert sha(C/'examples/index_profile_143.rs')==prep['kernel_source_sha256']
    proof={'complete':True,'utc':now(),'records':records,'fresh_kernel_tests':6,'strict_kernel_lints':1,'new_engine_tests':0,
      'library_core_byte_exact':True,'binary_sha256':sha(W/'binary/index_profile143.exe'),'kernel_only':True,'release017_qualified':False}
    (W/'build-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in proof.items() if k!='records'}),flush=True)
except BaseException:
    (W/'build-failure.json').write_text(json.dumps({'utc':now(),'records':records,'error':traceback.format_exc(),'no_timing_started':True},indent=2)+'\n',encoding='utf-8',newline='\n');raise
