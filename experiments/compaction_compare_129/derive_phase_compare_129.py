"""Prepare new protocol sources; never mutate trial128 sources or supported core."""
from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work')
def renamed(text):return text.replace('perf-128','perf-129').replace('_128','_129').replace('phase128','phase129')
guard=renamed((R/'check_round_activity_128.ps1').read_text(encoding='utf-8')).replace('between_rounds_only','outside_actual_case_timers_only')
(R/'check_round_activity_129.ps1').write_text(guard,encoding='utf-8',newline='\n')
run=renamed((R/'run_phase_compare_128.py').read_text(encoding='utf-8'))
start=run.index('policy=load(')
api='''def activity_check(place,index=None):
    times=[wintypes.FILETIME() for _ in range(4)]
    assert k.GetProcessTimes(k.GetCurrentProcess(),*(ctypes.byref(t) for t in times))
    creation=times[0].dwLowDateTime+(times[0].dwHighDateTime<<32)
    checked=subprocess.run(['D:/Codex/Migration-20261007/helper-runtime/powershell/pwsh.exe','-NoProfile','-File',str(R/'check_round_activity_129.ps1'),'-OwnerPid',str(os.getpid()),'-OwnerCreationFileTime',str(creation)],capture_output=True,timeout=20)
    row={'utc':utc(),'place':place,'index':index,'exit':checked.returncode,'stdout':checked.stdout.decode('utf-8-sig'),'stderr':checked.stderr.decode('utf-8-sig')}
    with (W/'activity-checks.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row,separators=(',',':'))+'\\n')
    messages=[json.loads(line) for line in row['stdout'].splitlines() if line.strip()]
    if checked.returncode==0:
        assert len(messages)==2 and messages[0]['no_other_task_work'] and messages[1]['no_visible_build_jobs']
        assert messages[0]['verified_controller_pid']==os.getpid() and messages[0]['verified_controller_creation_filetime']==creation
    elif checked.returncode==3:
        assert messages and (not messages[0]['no_other_task_work'] or (len(messages)==2 and not messages[1]['no_visible_build_jobs']))
    else:
        raise AssertionError(('Safety guard error, not a busy machine',row))
    return row
'''
run=run[:start]+api+'\n'+run[start:]
old="    start=time.monotonic();time.sleep(120)\n    cooldown.update(completed_utc=utc(),actual_elapsed_seconds=time.monotonic()-start)\n    assert cooldown['actual_elapsed_seconds']>=120"
new="""    start=time.monotonic();quiet_since=None;resets=0;deadline=start+policy['cooldown_deadline_seconds']
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
    assert cooldown['continuous_quiet_seconds']>=120"""
assert old in run;run=run.replace(old,new)
a=run.index("        if spec['index']%18==0:");b=run.index('        label=',a)
run=run[:a]+"        probe=activity_check('before_case',spec['index'])\n        assert probe['exit']==0,('Other work appeared: preserve complete prefix without retiming',probe)\n"+run[b:]
run=run.replace("        completed.append(record)\n", "        completed.append(record)\n        probe=activity_check('after_case',spec['index'])\n        assert probe['exit']==0,('Other work detected after native exit: preserve prefix',probe)\n")
ast.parse(run);(R/'run_phase_compare_129.py').write_text(run,encoding='utf-8',newline='\n')
audit=renamed((R/'audit_phase_compare_128.py').read_text(encoding='utf-8'))
marker="policy=load(W/'policy.json');freeze=load(W/'freeze.json');assert all(sha(W/n)==v for n,v in freeze['files'].items())"
assert marker in audit
extra="""
activity=[json.loads(line) for line in (W/'activity-checks.jsonl').read_text(encoding='utf-8').splitlines()]
case_probes=[row for row in activity if row['place']!='cooldown']
assert len(case_probes)==432 and all(row['exit']==0 for row in case_probes)
assert {(row['place'],row['index']) for row in case_probes}=={(place,i) for i in range(216) for place in ['before_case','after_case']}
assert load(W/'cooldown-proof.json')['continuous_quiet_seconds']>=120
"""
audit=audit.replace(marker,marker+extra)
ast.parse(audit);(R/'audit_phase_compare_129.py').write_text(audit,encoding='utf-8',newline='\n')
smoke=renamed((R/'smoke_phase_compare_128.py').read_text(encoding='utf-8'))
ast.parse(smoke);(R/'smoke_phase_compare_129.py').write_text(smoke,encoding='utf-8',newline='\n')
prepare=renamed((R/'prepare_phase_compare_128.py').read_text(encoding='utf-8'))
prepare=prepare.replace("assert head == '8e9e5fafcf79a68b43a01aa1acee92b0f039c010'", "assert head == 'f41a2c56524446233c5e54386a4ecf40ee3e03d4'\nassert load(R/'phase128-storage-cleanup-proof.json')['completed128_preflight_stores_closed'] and not (R/'perf-128').exists()")
prepare=prepare.replace("'trial':128", "'trial':129")
prepare=prepare.replace("'affinity_mask':256,'cooldown_seconds':120", "'affinity_mask':256,'cooldown_seconds':120,'cooldown_poll_seconds':10,'cooldown_deadline_seconds':7200")
prepare=prepare.replace('each complete round','before and after each actual native case')
prepare=prepare.replace("'timer':'Instant", "'new_protocol':'Same engine/input multiset/RNG seed as unstarted128. Continuous clear120-second interval after all preparation, reset on busy observations; per-case pre/post safety probes outside compaction timing. No workload or numerical gate changes.',\n 'timer':'Instant")
a=prepare.index("code=(R/'run_controls_125.py')");b=prepare.index("audit=(R/'audit_component_122.py')",a)
prepare=prepare[:a]+"ast.parse((R/'run_phase_compare_129.py').read_text(encoding='utf-8'))\n"+prepare[b:]
a=prepare.index("audit=(R/'audit_component_122.py')");b=prepare.index("for n in [",a)
prepare=prepare[:a]+"ast.parse((R/'audit_phase_compare_129.py').read_text(encoding='utf-8'))\n"+prepare[b:]
prepare=prepare.replace(",'wait_start_phase129.ps1','wait_start_phase129_v2.ps1'", "")
prepare=prepare.replace("'append_phase129_declared.py']", "'append_phase129_declared.py','derive_phase_compare_129.py']")
ast.parse(prepare);(R/'prepare_phase_compare_129.py').write_text(prepare,encoding='utf-8',newline='\n')
launch=renamed((R/'launch_phase_compare_128.ps1').read_text(encoding='utf-8'))
(R/'launch_phase_compare_129.ps1').write_text(launch,encoding='utf-8',newline='\n')
print('New129 source controllers derived; no declaration, fixture copy or timer started')
