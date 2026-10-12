"""Untimed134 correctness/build prerequisites; never a performance cohort."""
from pathlib import Path
from datetime import datetime,timezone
from ctypes import wintypes
import ctypes,hashlib,json,os,re,shutil,subprocess,traceback
R=Path('D:/Codex/Kestrel/work');W=R/'perf-136';C=W/'candidate'
CARGO='C:/Users/Frizer/.cargo/bin/cargo.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def save(n,v):
    with (W/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,indent=2)+'\n')
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=wintypes.HANDLE
k.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4;k.GetProcessTimes.restype=wintypes.BOOL
times=[wintypes.FILETIME() for _ in range(4)];assert k.GetProcessTimes(k.GetCurrentProcess(),*(ctypes.byref(t) for t in times))
creation=times[0].dwLowDateTime+(times[0].dwHighDateTime<<32)
def guard(label):
    result=subprocess.run(['D:/Codex/Migration-20261007/helper-runtime/powershell/pwsh.exe','-NoProfile','-File',str(R/'check_buffer136_prerequisite_activity.ps1'),'-OwnerPid',str(os.getpid()),'-OwnerCreationFileTime',str(creation)],capture_output=True,timeout=20)
    row={'utc':utc(),'before_job':label,'actual_exit':result.returncode,'stdout':result.stdout.decode('utf-8-sig'),'stderr':result.stderr.decode('utf-8-sig')}
    with (W/'prerequisite-activity-v2.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(row)+'\n')
    assert result.returncode==0,('Other task/timed/reset work appeared; stop untimed prerequisites',row)
    value=json.loads(row['stdout']);assert value['no_other_task_work'] and value['verified_controller_pid']==os.getpid() and value['verified_controller_creation_filetime']==creation
policy=load(W/'policy.json');prep=load(W/'preparation-proof.json')
assert policy['timed_cases_declared']==0 and not (W/'build-proof.json').exists()
assert all(sha(C/n)==h for n,h in prep['candidate_source_sha256'].items())
assert not any(key in os.environ for key in ['RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','CARGO_BUILD_TARGET'])
assert not any(key.startswith(('CARGO_PROFILE_RELEASE_','KESTREL_FAULT','KESTREL_LIVE_PAUSE')) for key in os.environ)
assert sha(Path('D:/Codex/Migration-20261007/fresh-profile-20261008/fresh_reset.ps1'))=='005d2246f6948eb9d2cef36a9169d9bcd82c9289c9bb0c5f7565fdae79b27e3b'
env=os.environ|{'TMP':str(W/'tmp'),'TEMP':str(W/'tmp'),'CARGO_INCREMENTAL':'0','CARGO_BUILD_JOBS':'4','CARGO_TARGET_DIR':str(W/'target')}
jobs=[]
for mode,features in [('normal','adaptive-segment-buffer-136'),('fault','adaptive-segment-buffer-136,fault-injection')]:
    for release in [False,True]:jobs.append((mode+('-release' if release else '-debug'),['test',*(['--release'] if release else []),'--features',features]))
    jobs.append((mode+'-lint',['clippy','--all-targets','--features',features]))
jobs.append(('release-artifact',['build','--release','--example','compaction_stage_121','--features','adaptive-segment-buffer-136']))
save('build-declaration-v2.json',{'utc':utc(),'jobs':jobs,'serial':True,'timed_cases_declared':0,'baseline154_reused':True,'unrelated_nonbenchmark_build_may_be_active':True})
records=[]
try:
    for label,options in jobs:
        guard(label)
        store=W/'test-stores'/label;store.mkdir()
        command=[CARGO,*options,'--offline','--locked',*(['--','-D','warnings'] if options[0]=='clippy' else [])]
        print('START '+label,flush=True);started=utc()
        result=subprocess.run(command,cwd=C,env=env|{'KESTREL_TEST_ROOT':str(store)},capture_output=True,timeout=900,creationflags=0x08000000)
        log=W/'logs'/(label+'.log');log.write_bytes(result.stdout+result.stderr)
        record={'label':label,'actual_exit':result.returncode,'actual_wait_completed':True,'started_utc':started,'completed_utc':utc(),'argv':command,'log_sha256':sha(log)}
        if options[0]=='test':record['fresh_tests']=sum(map(int,re.findall(rb'test result: ok\. (\d+) passed;',result.stdout)))
        records.append(record);save('build-step-'+label+'.json',record)
        assert result.returncode==0,(label,result.stdout[-2000:],result.stderr[-5000:])
        if options[0]=='test':assert record['fresh_tests']==86,record
        if label=='release-artifact':shutil.copy2(W/'target/release/examples/compaction_stage_121.exe',W/'binary/candidate136.exe')
        print(json.dumps({'passed':label,'fresh_tests':record.get('fresh_tests')}),flush=True)
    assert all(sha(C/n)==h for n,h in prep['candidate_source_sha256'].items())
    size=sum(f.stat().st_size for f in W.rglob('*') if f.is_file());assert size<policy['local_regenerable_build_cap_bytes']
    proof={'complete':True,'utc':utc(),'records':records,'fresh_Archive_tests':sum(r.get('fresh_tests',0) for r in records),'strict_lints':2,'baseline154_tests_and_binary_reused':True,'candidate_sha256':sha(W/'binary/candidate136.exe'),'all_source_byte_exact':True,'actual_size_bytes':size,'timed_cases_declared':0,'release017_qualified':False}
    save('build-proof.json',proof);print(json.dumps({key:value for key,value in proof.items() if key!='records'}),flush=True)
except BaseException:
    save('build-failure-v2.json',{'utc':utc(),'records':records,'error':traceback.format_exc(),'timed_cases_declared':0,'all_failures_preserved':True});raise
