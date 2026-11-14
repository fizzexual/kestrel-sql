"""One bounded declared A/A/A cohort; fixed affinity belongs only to this job."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from ctypes import wintypes
import ctypes,hashlib,json,os,subprocess,time,traceback,queue,threading
R=Path('D:/Codex/Kestrel/work');W=R/'perf-139'
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.GetCurrentProcess.restype=wintypes.HANDLE
k.GetProcessAffinityMask.argtypes=[wintypes.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)];k.GetProcessAffinityMask.restype=wintypes.BOOL
k.SetProcessAffinityMask.argtypes=[wintypes.HANDLE,ctypes.c_size_t];k.SetProcessAffinityMask.restype=wintypes.BOOL
k.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4;k.GetProcessTimes.restype=wintypes.BOOL
def mask(handle):
    process=ctypes.c_size_t();system=ctypes.c_size_t()
    assert k.GetProcessAffinityMask(handle,ctypes.byref(process),ctypes.byref(system)),ctypes.get_last_error()
    return process.value,system.value
def identity(child):
    times=[wintypes.FILETIME() for _ in range(4)]
    assert k.GetProcessTimes(int(child._handle),*(ctypes.byref(t) for t in times))
    return {'pid':child.pid,'creation_filetime':times[0].dwLowDateTime+(times[0].dwHighDateTime<<32),'owned_Popen_handle':True,'affinity_mask':mask(int(child._handle))[0]}
class SafetyWorker:
    def __init__(self):
        times=[wintypes.FILETIME() for _ in range(4)]
        assert k.GetProcessTimes(k.GetCurrentProcess(),*(ctypes.byref(t) for t in times))
        self.owner_creation=times[0].dwLowDateTime+(times[0].dwHighDateTime<<32)
        self.child=subprocess.Popen(['D:/Codex/Migration-20261007/helper-runtime/powershell/pwsh.exe','-NoProfile','-File',str(R/'activity_worker_139.ps1'),'-OwnerPid',str(os.getpid()),'-OwnerCreationFileTime',str(self.owner_creation)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',bufsize=1,creationflags=0x08000000)
        self.identity=identity(self.child);self.messages=queue.Queue();self.errors=[];self.number=0
        assert self.identity['affinity_mask']==256
        def reader():
            for line in self.child.stdout:
                self.messages.put(line)
            self.messages.put(None)
        def errors():
            for line in self.child.stderr:
                assert sum(map(len,self.errors))<1000000,'Metadata stderr cap exceeded'
                self.errors.append(line)
        self.output_thread=threading.Thread(target=reader,daemon=True);self.error_thread=threading.Thread(target=errors,daemon=True)
        self.output_thread.start();self.error_thread.start()
        with (W/'worker-sessions.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps({'utc':utc(),'owner_pid':os.getpid(),'owner_creation_filetime':self.owner_creation,'worker_identity':self.identity,'owned_stdin_stdout_only':True})+'\n')
    def check(self,place,index=None):
        assert self.child.poll() is None,('Metadata worker exited',self.child.returncode,self.errors)
        started=utc();number=self.number;self.number+=1
        self.child.stdin.write(json.dumps({'operation':'check','request_id':number,'place':place,'index':index})+'\n');self.child.stdin.flush()
        line=self.messages.get(timeout=20)
        assert line is not None and len(line)<1000000,('Metadata worker EOF/response cap',self.errors)
        response=json.loads(line)
        assert response['request_id']==number and response['place']==place and response['index']==index and response['no_probe_during_native_case']
        row={'started_utc':started,'utc':utc(),'place':place,'index':index,'exit':response['exit'],'stdout':'\n'.join(json.dumps(m) for m in response['messages']),'stderr':'','worker_identity':self.identity,'request_id':number}
        with (W/'activity-checks.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(row,separators=(',',':'))+'\n')
        messages=response['messages'];assert messages and messages[0]['verified_controller_pid']==os.getpid() and messages[0]['verified_controller_creation_filetime']==self.owner_creation
        assert messages[0]['persistent_worker_pid']==self.identity['pid'] and messages[0]['worker_blocks_on_input_between_requests']
        if row['exit']==0:assert len(messages)==2 and messages[0]['no_other_task_work'] and messages[1]['no_visible_build_jobs']
        elif row['exit']==3:assert not messages[0]['no_other_task_work'] or (len(messages)==2 and not messages[1]['no_visible_build_jobs'])
        else:raise AssertionError(('Safety protocol error',row))
        return row
    def stop(self):
        forced=False
        if self.child.poll() is None:
            self.child.stdin.write(json.dumps({'operation':'stop'})+'\n');self.child.stdin.flush();self.child.stdin.close()
            try:self.child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.child.kill();self.child.wait(timeout=10);forced=True
        self.output_thread.join(timeout=2);self.error_thread.join(timeout=2)
        proof={'utc':utc(),'actual_exit':self.child.returncode,'actual_wait_completed':self.child.poll() is not None,'forced_owned_worker_kill':forced,'worker_identity':self.identity,'requests':self.number,'stderr':''.join(self.errors)}
        with (W/'worker-exits.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(proof)+'\n')
        return proof
def blockers_began_after_exit(probe,completed_utc):
    if probe['exit']!=3:return False
    messages=[json.loads(line) for line in probe['stdout'].splitlines()]
    if messages[0].get('reset_jobs'):return False
    jobs=messages[0]['other_work']+([] if len(messages)<2 else messages[1]['visible_build_jobs'])
    if not jobs:return False
    cutoff=max(datetime.fromisoformat(completed_utc)+timedelta(seconds=.1),datetime.fromisoformat(probe['started_utc']))
    try:return all(datetime.fromisoformat(job['creation_utc'])>=cutoff for job in jobs)
    except (KeyError,ValueError,TypeError):return False
def wait_between_cases(mode,index,initial,completed_utc=None):
    assert initial['exit']==3
    if mode=='after':assert blockers_began_after_exit(initial,completed_utc),('Possible in-case interference; preserve full prefix',initial)
    began=utc();start=time.monotonic();deadline=start+policy['cooldown_deadline_seconds'];quiet_since=None;resets=0
    while True:
        assert time.monotonic()<deadline,'Between-case quiet deadline expired; no next timer started'
        probe=activity_check('between_case_wait_'+mode,index);now=time.monotonic()
        if probe['exit']==0:
            if quiet_since is None:quiet_since=now
            if now-quiet_since>=120:break
        else:quiet_since=None;resets+=1
        time.sleep(policy['cooldown_poll_seconds'])
    proof={'mode':mode,'index':index,'started_utc':began,'completed_utc':utc(),'native_completed_utc':completed_utc,'initial_probe':initial,'continuous_quiet_seconds':now-quiet_since,'busy_reset_count':resets,'no_native_case_repeated':True,'no_metric_based_selection':True}
    with (W/'between-case-pauses.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(proof)+'\n')
    print(json.dumps({'between_case_pause_completed':mode,'index':index,'observed_clear_seconds':proof['continuous_quiet_seconds']}),flush=True)

worker=None
def activity_check(place,index=None):
    assert worker is not None
    return worker.check(place,index)

policy=load(W/'policy.json');assert sha(W/'policy.json')==load(W/'declaration-proof.json')['policy_sha256']
guard=load(sorted(R.glob('guard-cleanup-pretime-*.json'))[-1]);assert not guard['active_processes'] and guard['verified_idle_terminal_reset']
global_guard=load(sorted(R.glob('global-build-preflight-*.json'))[-1])
assert global_guard['no_visible_build_jobs'] and not global_guard['visible_build_jobs']
assert (datetime.now(timezone.utc)-datetime.fromisoformat(global_guard['utc'])).total_seconds()<60
assert not (W/'component-cases.jsonl').exists() and not (W/'fixtures').exists()
files={'policy.json':sha(W/'policy.json')}
files.update({'binary/'+n:sha(W/'binary'/n) for n in policy['binary_sha256']})
assert all(files['binary/'+n]==h for n,h in policy['binary_sha256'].items())
assert load(W/'smoke-proof.json')['complete']
helper=Path('D:/Codex/Migration-20261007/fresh-profile-20261008/fresh_reset.ps1')
assert sha(helper)=='005d2246f6948eb9d2cef36a9169d9bcd82c9289c9bb0c5f7565fdae79b27e3b'
for source in ['prepare_phase_compare_139.py', 'run_phase_compare_139.py', 'audit_phase_compare_139.py', 'smoke_phase_compare_139.py', 'activity_worker_139.ps1', 'launch_phase_compare_139.ps1', 'append_phase139_declared.py', 'derive_input_compare_139.py', 'audit_lifecycle_receipts_139.py', 'launch_preflight_phase139.ps1', 'launch_audits_phase139.ps1', 'archive_audit_099.py']:
    assert sha(R/source)==sha(W/source)
    files[source]=sha(W/source)
current=sum(p.stat().st_size for p in W.rglob('*') if p.is_file());assert current+len(policy['cases'])*2_000_000<policy['resource_bound_bytes']
(W/'freeze.json').write_text(json.dumps({'utc':utc(),'files':files,'A_and_B_same_exact131_binary':True,'candidate_exact_reuse138':True,'initial_bytes':current,'controller_sha256':sha(Path(__file__))},indent=2)+'\n',encoding='utf-8')
(W/'fixtures').mkdir();(W/'raw').mkdir()
env=os.environ|{'TMP':str(W/'tmp'),'TEMP':str(W/'tmp')}
assert not any(name.startswith(('KESTREL_FAULT','KESTREL_LIVE_PAUSE','KESTREL_ASYNC','KESTREL_COUPLE')) for name in env)
completed=[];own=k.GetCurrentProcess();original,system=mask(own)
assert policy['affinity_mask']==256 and original&256 and system&256
try:
    assert k.SetProcessAffinityMask(own,256),ctypes.get_last_error()
    assert mask(own)[0]==256
    worker=SafetyWorker()
    cooldown={'started_utc':utc(),'required_seconds':120,'controller_original_affinity':original,'controller_fixed_affinity':256,'no_global_machine_setting_changed':True}
    print('COOLDOWN_START 120 seconds; all children inherit logical CPU8',flush=True)
    start=time.monotonic();quiet_since=None;resets=0;deadline=start+policy['cooldown_deadline_seconds']
    while True:
        assert time.monotonic()<deadline,'Continuous quiet deadline expired before any timing'
        probe=activity_check('cooldown')
        now=time.monotonic()
        if probe['exit']==0:
            if quiet_since is None:quiet_since=now
            if now-quiet_since>=120:break
        else:
            quiet_since=None;resets+=1
        time.sleep(policy['cooldown_poll_seconds'])
    cooldown.update(completed_utc=utc(),actual_elapsed_seconds=now-start,continuous_quiet_seconds=now-quiet_since,busy_reset_count=resets)
    assert cooldown['continuous_quiet_seconds']>=120
    (W/'cooldown-proof.json').write_text(json.dumps(cooldown,indent=2)+'\n',encoding='utf-8')
    for spec in policy['cases']:
        probe=activity_check('before_case',spec['index'])
        if probe['exit']==3:
            wait_between_cases('before',spec['index'],probe)
            probe=activity_check('before_case_retry',spec['index'])
        assert probe['exit']==0,('Still busy before next timer',probe)
        label=f"{spec['index']:03d}-r{spec['round']:02d}-{spec['name']}-{spec['variant']}"
        directory=W/'fixtures'/label
        binary=W/'binary'/('candidate138.exe' if spec['variant']=='candidate' else 'baseline.exe')
        argv=[str(binary),str(directory),spec['name'],str(spec['seed'])]
        record=spec|{'argv':argv,'fixture':directory.relative_to(W).as_posix(),'started_utc':utc()}
        child=subprocess.Popen(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
        record['identity']=identity(child)
        try:out,err=child.communicate(timeout=90)
        except subprocess.TimeoutExpired:
            child.kill();out,err=child.communicate(timeout=10);record['timeout']=True
        for suffix,content in [('stdout',out),('stderr',err)]:
            path=W/'raw'/(label+'.'+suffix);path.write_bytes(content);record[suffix]=path.relative_to(W).as_posix()
        record.update(actual_exit=child.returncode,actual_wait_completed=True,completed_utc=utc())
        with (W/'component-cases.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record,separators=(',',':'))+'\n')
        assert record['identity']['affinity_mask']==256,record
        assert child.returncode==0 and not record.get('timeout'),(record,out[-1000:],err[-2000:])
        result=json.loads(out);assert result['all_checks_passed'] and result['cold_rows']==32768 and result['workload']==spec['name'] and result['seed']==spec['seed']
        completed.append(record)
        probe=activity_check('after_case',spec['index'])
        if probe['exit']==3:
            wait_between_cases('after',spec['index'],probe,record['completed_utc'])
        else:assert probe['exit']==0
        if len(completed)%18==0:print(json.dumps({'completed':len(completed),'total':216,'last':label}),flush=True)
    assert len(completed)==216
    worker_exit=worker.stop();worker=None
    assert worker_exit['actual_exit']==0 and worker_exit['actual_wait_completed'] and not worker_exit['forced_owned_worker_kill']
    assert all(sha(W/n)==v for n,v in files.items())
    assert all(sha(R/n)==files[n] for n in ['prepare_phase_compare_139.py', 'run_phase_compare_139.py', 'audit_phase_compare_139.py', 'smoke_phase_compare_139.py', 'activity_worker_139.ps1', 'launch_phase_compare_139.ps1', 'append_phase139_declared.py', 'derive_input_compare_139.py', 'audit_lifecycle_receipts_139.py', 'launch_preflight_phase139.ps1', 'launch_audits_phase139.ps1', 'archive_audit_099.py'])
    (W/'cohort-completion.json').write_text(json.dumps({'complete':True,'cases':len(completed),'utc':utc(),'all_actual_child_exits_zero':True,'all_affinities_verified':True,'all_frozen_inputs_unchanged':True,'A_B_identical131_and_C_exact_reuse138':True,'metadata_worker_actual_exit':worker_exit['actual_exit']},indent=2)+'\n',encoding='utf-8')
except BaseException:
    (W/'cohort-failure.json').write_text(json.dumps({'completed':len(completed),'utc':utc(),'error':traceback.format_exc(),'unstarted_indices':[s['index'] for s in policy['cases'][len(completed):]],'failed_case_not_retimed':True},indent=2)+'\n',encoding='utf-8');raise
finally:
    if worker is not None:
        worker.stop();worker=None
    assert k.SetProcessAffinityMask(own,original),ctypes.get_last_error()
    assert mask(own)[0]==original
