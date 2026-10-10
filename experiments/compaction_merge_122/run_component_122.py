"""Sole bounded balanced D: component cohort, after actual build completion."""
from pathlib import Path
from datetime import datetime,timezone
import ctypes, hashlib, json, os, subprocess, time, traceback
from ctypes import wintypes
R=Path('D:/Codex/Kestrel');W=R/'work/perf-122'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def utc():return datetime.now(timezone.utc).isoformat()
def identity(child):
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4
    kernel.GetProcessTimes.restype=wintypes.BOOL
    times=[wintypes.FILETIME() for _ in range(4)]
    assert kernel.GetProcessTimes(int(child._handle),*(ctypes.byref(t) for t in times))
    return {'pid':child.pid,'creation_filetime':times[0].dwLowDateTime+(times[0].dwHighDateTime<<32),'owned_Popen_handle':True}
policy=load(W/'policy.json');build=load(W/'build-proof.json');assert build['complete']
assert sha(W/'policy.json')==load(W/'declaration-proof.json')['policy_sha256']
guard=sorted((R/'work').glob('guard-cleanup-pretime-*.json'))[-1]
assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
prep=load(W/'preparation-proof.json')
files={'policy.json':sha(W/'policy.json'),'build-proof.json':sha(W/'build-proof.json')}
for n in ['baseline','candidate']:
    assert {p.relative_to(W/n).as_posix():sha(p) for p in (W/n).rglob('*') if p.is_file()}==prep[n]
    files.update({n+'/'+name:value for name,value in prep[n].items()})
files.update({'binaries/'+name:value for name,value in build['binary_SHA256'].items()})
assert all(sha(W/n)==value for n,value in files.items())
assert not (W/'component-cases.jsonl').exists() and not (W/'fixtures').exists()
current=sum(p.stat().st_size for p in W.rglob('*') if p.is_file());assert current+len(policy['cases'])*2_000_000<8_000_000_000
(W/'freeze.json').write_text(json.dumps({'utc':utc(),'files':files,'A_and_B_identical_binary':True,'initial_work_bytes':current},indent=2)+'\n')
(W/'fixtures').mkdir();(W/'raw').mkdir()
env=os.environ|{'TMP':str(W/'tmp'),'TEMP':str(W/'tmp')}
assert not any(k.startswith(('KESTREL_FAULT','KESTREL_LIVE_PAUSE','KESTREL_ASYNC','KESTREL_COUPLE')) for k in env)
completed=[]
try:
    # The fixed cooldown was declared before this candidate was prepared. All
    # source/binary hashing and excluded smokes finish before this idle window.
    assert policy['timing_cooldown_seconds'] == 120
    cooldown={'started_utc':utc(),'required_seconds':120,
              'after_all_preparation_hashes':True,
              'controller_sha256':sha(Path(__file__))}
    print('COOLDOWN_START 120 seconds',flush=True)
    idle_start=time.monotonic()
    time.sleep(120)
    cooldown.update(completed_utc=utc(),actual_elapsed_seconds=time.monotonic()-idle_start)
    assert cooldown['actual_elapsed_seconds'] >= 120
    with (W/'cooldown-proof.json').open('x',encoding='utf-8') as f:
        f.write(json.dumps(cooldown,indent=2)+'\n')
    print('COOLDOWN_COMPLETE',flush=True)
    for spec in policy['cases']:
        label=f"{spec['index']:03d}-r{spec['round']:02d}-{spec['name']}-{spec['variant']}"
        binary=W/'binaries'/('candidate' if spec['variant']=='candidate' else 'baseline')/'compaction_stage_121.exe'
        directory=W/'fixtures'/label
        argv=[str(binary),str(directory),spec['name'],str(spec['round'])]
        record=spec|{'argv':argv,'fixture':directory.relative_to(W).as_posix(),'started_utc':utc()}
        print('START '+label,flush=True)
        child=subprocess.Popen(argv,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
        record['identity']=identity(child)
        try:out,err=child.communicate(timeout=90)
        except subprocess.TimeoutExpired:
            child.kill();out,err=child.communicate(timeout=10);record['timeout']=True
        for suffix,content in [('stdout',out),('stderr',err)]:
            path=W/'raw'/(label+'.'+suffix);path.write_bytes(content);record[suffix]=path.relative_to(W).as_posix()
        record.update(actual_exit=child.returncode,actual_wait_completed=True,completed_utc=utc())
        with (W/'component-cases.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record,separators=(',',':'))+'\n')
        assert child.returncode==0 and not record.get('timeout'),(record,out[-1000:],err[-2000:])
        result=json.loads(out);assert result['all_checks_passed'] and result['cold_rows']==32768 and result['workload']==spec['name'] and result['seed']==spec['round']
        completed.append(record)
        print(json.dumps({'completed':len(completed),'total':216,'label':label,'compact_ms':result['compaction_ns']/1e6}),flush=True)
    assert all(sha(W/n)==value for n,value in files.items())
    (W/'cohort-completion.json').write_text(json.dumps({'complete':True,'cases':len(completed),'utc':utc(),'all_actual_child_exits_zero':True,'all_frozen_inputs_unchanged':True},indent=2)+'\n')
except BaseException:
    (W/'cohort-failure.json').write_text(json.dumps({'completed':len(completed),'utc':utc(),'error':traceback.format_exc(),'unstarted_indices':[s['index'] for s in policy['cases'][len(completed):]],'failed_case_not_retimed':True},indent=2)+'\n');raise
