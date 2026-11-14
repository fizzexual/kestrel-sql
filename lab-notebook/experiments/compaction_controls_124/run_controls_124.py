"""One bounded declared A/A/A cohort; fixed affinity belongs only to this job."""
from pathlib import Path
from datetime import datetime,timezone
from ctypes import wintypes
import ctypes,hashlib,json,os,subprocess,time,traceback
R=Path('D:/Codex/Kestrel/work');W=R/'perf-124'
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
policy=load(W/'policy.json');assert sha(W/'policy.json')==load(W/'declaration-proof.json')['policy_sha256']
guard=load(sorted(R.glob('guard-cleanup-pretime-*.json'))[-1]);assert not guard['active_processes'] and guard['verified_idle_terminal_reset']
assert not (W/'component-cases.jsonl').exists() and not (W/'fixtures').exists()
files={'policy.json':sha(W/'policy.json'),'binary/compaction_stage_121.exe':sha(W/'binary/compaction_stage_121.exe')}
assert files['binary/compaction_stage_121.exe']==policy['actual_binary_sha256']
current=sum(p.stat().st_size for p in W.rglob('*') if p.is_file());assert current+len(policy['cases'])*2_000_000<8_000_000_000
(W/'freeze.json').write_text(json.dumps({'utc':utc(),'files':files,'all_three_labels_same_supported016_binary':True,'initial_bytes':current,'controller_sha256':sha(Path(__file__))},indent=2)+'\n',encoding='utf-8')
(W/'fixtures').mkdir();(W/'raw').mkdir()
env=os.environ|{'TMP':str(W/'tmp'),'TEMP':str(W/'tmp')}
assert not any(name.startswith(('KESTREL_FAULT','KESTREL_LIVE_PAUSE','KESTREL_ASYNC','KESTREL_COUPLE')) for name in env)
completed=[];own=k.GetCurrentProcess();original,system=mask(own)
assert policy['affinity_mask']==256 and original&256 and system&256
try:
    assert k.SetProcessAffinityMask(own,256),ctypes.get_last_error()
    assert mask(own)[0]==256
    cooldown={'started_utc':utc(),'required_seconds':120,'controller_original_affinity':original,'controller_fixed_affinity':256,'no_global_machine_setting_changed':True}
    print('COOLDOWN_START 120 seconds; all children inherit logical CPU8',flush=True)
    start=time.monotonic();time.sleep(120)
    cooldown.update(completed_utc=utc(),actual_elapsed_seconds=time.monotonic()-start)
    assert cooldown['actual_elapsed_seconds']>=120
    (W/'cooldown-proof.json').write_text(json.dumps(cooldown,indent=2)+'\n',encoding='utf-8')
    for spec in policy['cases']:
        label=f"{spec['index']:03d}-r{spec['round']:02d}-{spec['name']}-{spec['variant']}"
        directory=W/'fixtures'/label
        argv=[str(W/'binary/compaction_stage_121.exe'),str(directory),spec['name'],str(spec['seed'])]
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
        if len(completed)%18==0:print(json.dumps({'completed':len(completed),'total':648,'last':label}),flush=True)
    assert all(sha(W/n)==v for n,v in files.items())
    (W/'cohort-completion.json').write_text(json.dumps({'complete':True,'cases':len(completed),'utc':utc(),'all_actual_child_exits_zero':True,'all_affinities_verified':True,'all_frozen_inputs_unchanged':True,'all_variants_supported016_no_candidate':True},indent=2)+'\n',encoding='utf-8')
except BaseException:
    (W/'cohort-failure.json').write_text(json.dumps({'completed':len(completed),'utc':utc(),'error':traceback.format_exc(),'unstarted_indices':[s['index'] for s in policy['cases'][len(completed):]],'failed_case_not_retimed':True},indent=2)+'\n',encoding='utf-8');raise
finally:
    assert k.SetProcessAffinityMask(own,original),ctypes.get_last_error()
    assert mask(own)[0]==original
