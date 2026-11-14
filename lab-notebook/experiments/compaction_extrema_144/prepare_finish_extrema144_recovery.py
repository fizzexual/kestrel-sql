"""Preserve the four completed fault cases and finish only the ten unstarted ones."""
from pathlib import Path
from datetime import datetime, timezone
import json

R = Path('D:/Codex/Kestrel/work')
W = R / 'perf-144'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
failure = load(W / 'recovery-failure.json')
assert len(failure['completed_checks']) == 4 and len(failure['actual_commands']) == 16
assert load(R / 'extrema144-recovery-actual-exits.json')['recovery_actual_exit'] == 1
assert all(r['actual_exit'] == r['expected_exit'] and r['actual_wait_completed'] for r in failure['actual_commands'])
source = (R / 'run_extrema144_recovery.py').read_text()
source = source.replace('from datetime import datetime,timezone', 'from datetime import datetime,timezone,timedelta')
source = source.replace('import ctypes,hashlib,json,os,struct,subprocess,sys,traceback', 'import ctypes,hashlib,json,os,struct,subprocess,sys,time,traceback')
start = source.index('def guard(label):')
end = source.index('\nchecks=[];commands=[]', start)
guards = '''def probe(label):
    started=now(); reports=[]
    arguments=[[PS,'-NoProfile','-File',str(R/'check_extrema144_recovery_finish_activity.ps1'),'-OwnerPid',str(os.getpid()),'-OwnerCreationFileTime',str(times[0].value)], [PS,'-NoProfile','-File',str(R/'check_global_build_activity.ps1')]]
    for args in arguments:
        result=subprocess.run(args,capture_output=True,timeout=30,creationflags=0x08000000)
        assert result.returncode in (0,3),(result.returncode,result.stderr.decode())
        reports.append(json.loads(result.stdout))
        if result.returncode==3: break
    clear=reports[0]['no_other_task_work'] and len(reports)==2 and reports[1]['no_visible_build_jobs']
    row={'place':label,'started_utc':started,'completed_utc':now(),'clear':clear,'reports':reports}
    with (W/'recovery-finish-activity.jsonl').open('a',encoding='utf-8',newline='\\n') as f:f.write(json.dumps(row)+'\\n')
    return row
def wait_clear(initial,label):
    began=now(); start=time.monotonic(); quiet=None; resets=0
    while True:
        assert time.monotonic()-start<7200,'Guard wait deadline; no next child started'
        p=probe('wait-'+label); tick=time.monotonic()
        if p['clear']:
            if quiet is None:quiet=tick
            if tick-quiet>=120:break
        else:quiet=None;resets+=1
        time.sleep(10)
    with (W/'recovery-finish-pauses.jsonl').open('a',encoding='utf-8',newline='\\n') as f:
        f.write(json.dumps({'initial':initial,'started_utc':began,'completed_utc':now(),'continuous_clear_seconds':tick-quiet,'busy_resets':resets,'no_case_repeated':True})+'\\n')
def guard(label,exited=None):
    p=probe(label)
    if p['clear']:return
    if exited is not None:
        reports=p['reports']; assert not reports[0]['reset_jobs']
        jobs=reports[0]['other_work']+([] if len(reports)==1 else reports[1]['visible_build_jobs'])
        cutoff=max(datetime.fromisoformat(exited)+timedelta(seconds=.1),datetime.fromisoformat(p['started_utc']))
        assert jobs and all(datetime.fromisoformat(j['creation_utc'])>=cutoff for j in jobs),'Possible in-case interference; preserve full prefix'
    wait_clear(p,label);assert probe(label+'-retry')['clear']
'''
source = source[:start] + guards + source[end:]
source = source.replace('checks=[];commands=[]', "prefix=load(W/'recovery-failure.json');checks=list(prefix['completed_checks']);commands=list(prefix['actual_commands'])")
source = source.replace("root=W/'recovery-fixtures';assert not root.exists();root.mkdir()", "root=W/'recovery-fixtures';assert root.is_dir();assert len(checks)==4 and len(commands)==16\n    journal=[json.loads(s) for s in (W/'recovery-command-exits.jsonl').read_text().splitlines()];assert journal==commands\n    assert all(r['actual_exit']==r['expected_exit'] and r['actual_wait_completed'] for r in commands)")
source = source.replace("incoming.write_bytes(b''.join(struct.pack('<qqq',*row) for row in second))", "assert incoming.read_bytes()==b''.join(struct.pack('<qqq',*row) for row in second)")
source = source.replace("label=point+'-'+mode;store=root/label\n            guard", "label=point+'-'+mode;store=root/label\n            if any(c['point']==point and c['mode']==mode for c in prefix['completed_checks']):continue\n            assert not store.exists()\n            guard")
source = source.replace("guard('after-fault-'+label)", "guard('after-fault-'+label,commands[-1]['completed_utc'])")
source = source.replace("guard('completed-recovery')", """guard('completed-recovery')
    # Recheck every settled store, including the original four, without repeating any child.
    for c in checks:
        checked=independent.check(root/(c['point']+'-'+c['mode']),expected,receipts)
        assert checked['head']==c['head'] and checked['rows']==2048 and checked['full_block_crc_bytes']==49152
    assert len({r['label'] for r in commands})==56
    assert all(r['actual_exit']==r['expected_exit'] and r['actual_wait_completed'] for r in commands)""")
source = source.replace("'speed_claim':False", "'speed_claim':False,'four_completed_native_cases_reused_ten_unstarted_finished':True,'no_native_case_repeated':True")
source = source.replace("(W/'recovery-failure.json').write_text", "(W/'recovery-finish-failure.json').write_text")
target=R/'finish_extrema144_recovery.py'
assert not target.exists()
compile(source,str(target),'exec')
target.write_text(source,encoding='utf-8',newline='\n')
guard=(R/'check_extrema144_recovery_activity.ps1').read_text().replace('run_extrema144_recovery', 'finish_extrema144_recovery')
(R/'check_extrema144_recovery_finish_activity.ps1').write_text(guard,encoding='utf-8',newline='\n')
launcher="""$ErrorActionPreference='Stop'
& 'C:\\Users\\Frizer\\AppData\\Local\\Programs\\Python\\Python312\\python.exe' 'D:\\Codex\\Kestrel\\work\\finish_extrema144_recovery.py' *> 'D:\\Codex\\Kestrel\\work\\recovery-extrema144-finish.log'
$taskExit=$LASTEXITCODE
if(Test-Path -LiteralPath 'D:\\Codex\\Kestrel\\work\\extrema144-recovery-finish-actual-exits.json'){throw 'Do not overwrite recovery finish exit'}
@{utc=(Get-Date).ToUniversalTime().ToString('o');recovery_actual_exit=$taskExit;actual_recovery_wait_completed=$true;timed_performance_cases=0;no_native_case_repeated=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:\\Codex\\Kestrel\\work\\extrema144-recovery-finish-actual-exits.json' -Encoding utf8
Get-Content -LiteralPath 'D:\\Codex\\Kestrel\\work\\recovery-extrema144-finish.log' -Tail 9
exit $taskExit
"""
(R/'launch_finish_extrema144_recovery.ps1').write_text(launcher,encoding='utf-8',newline='\n')
(W/'recovery-finish-declaration.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'reused_cases':4,'new_cases':10,'cases_inputs_binaries_cutpoints_unchanged':True,'no_native_case_repeated':True,'before_busy_wait120_no_child_started':True,'after_busy_wait_only_proven_birth_after_exit100ms_and_probe_start':True,'timed_performance_cases':0},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Preserved four complete cases; prepared only ten unstarted cases; no build or native job started')
