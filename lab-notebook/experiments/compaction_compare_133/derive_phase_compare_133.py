"""Fresh133: predeclared waits between timers, reject possible in-case overlap."""
from pathlib import Path
import ast
R=Path('D:/Codex/Kestrel/work')
assert not (R/'perf-133').exists() and not (R/'run_phase_compare_133.py').exists()
def renamed(s):return s.replace('perf-132','perf-133').replace('_132','_133').replace('phase132','phase133').replace('-132','-133')
run=renamed((R/'run_phase_compare_132.py').read_text(encoding='utf-8'))
run=run.replace('from datetime import datetime,timezone','from datetime import datetime,timezone,timedelta')
marker='worker=None\ndef activity_check(place,index=None):'
assert run.count(marker)==1
functions='''def blockers_began_after_exit(probe,completed_utc):
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
    with (W/'between-case-pauses.jsonl').open('a',encoding='utf-8',newline='\\n') as f:f.write(json.dumps(proof)+'\\n')
    print(json.dumps({'between_case_pause_completed':mode,'index':index,'observed_clear_seconds':proof['continuous_quiet_seconds']}),flush=True)
'''
run=run.replace(marker,functions+'\n'+marker,1)
old="        assert probe['exit']==0,('Other work appeared: preserve complete prefix without retiming',probe)"
new="""        if probe['exit']==3:
            wait_between_cases('before',spec['index'],probe)
            probe=activity_check('before_case_retry',spec['index'])
        assert probe['exit']==0,('Still busy before next timer',probe)"""
assert old in run;run=run.replace(old,new,1)
old="        assert probe['exit']==0,('Other work detected after native exit: preserve prefix',probe)"
new="""        if probe['exit']==3:
            wait_between_cases('after',spec['index'],probe,record['completed_utc'])
        else:assert probe['exit']==0"""
assert old in run;run=run.replace(old,new,1)
ast.parse(run);(R/'run_phase_compare_133.py').write_text(run,encoding='utf-8',newline='\n')
worker=renamed((R/'activity_worker_132.ps1').read_text(encoding='utf-8'));(R/'activity_worker_133.ps1').write_text(worker,encoding='utf-8',newline='\n')
prepare=renamed((R/'prepare_phase_compare_132.py').read_text(encoding='utf-8')).replace("'trial':132","'trial':133")
prepare=prepare.replace("assert head == load(R/'phase131-publication-proof.json')['private_main']","assert head == load(R/'phase132-publication-proof.json')['private_main']")
marker="assert not W.exists()"
prepare=prepare.replace(marker,marker+"\nassert load(R/'phase132-storage-cleanup-proof.json')['completed132_prefix_stores_closed'] and not (R/'perf-132').exists()",1)
prepare=prepare.replace('No engine/numerical gate/input reduction; removed repeated PowerShell startup is outside compaction clock.', 'Busy before a timer waits120 continuous clear seconds. Busy after a completed native child can wait ONLY if every observed blocker began after child exit+100ms and after the post-probe began; possible overlap rejects entire prefix. All samples/cases kept exactly once, no metric-dependent selection. No engine/numerical gate/input reduction; waits/startup outside compaction clock.')
ast.parse(prepare);(R/'prepare_phase_compare_133.py').write_text(prepare,encoding='utf-8',newline='\n')
smoke=renamed((R/'smoke_phase_compare_132.py').read_text(encoding='utf-8'))
marker="    clear=worker.check('protocol_clear');assert clear['exit']==0"
extra='''
    classify=namespace['blockers_began_after_exit']
    sample={'exit':3,'started_utc':'2026-10-12T00:00:01+00:00','stdout':json.dumps({'other_work':[{'creation_utc':'2026-10-12T00:00:02+00:00'}],'reset_jobs':[]})}
    assert classify(sample,'2026-10-12T00:00:00+00:00')
    assert not classify(sample,'2026-10-12T00:00:02+00:00')
    sample['stdout']=json.dumps({'other_work':[{'creation_utc':'2026-10-12T00:00:00.05+00:00'}],'reset_jobs':[]})
    assert not classify(sample,'2026-10-12T00:00:00+00:00')
    sample['stdout']=json.dumps({'other_work':[{'creation_utc':'2026-10-12T00:00:02+00:00'},{}],'reset_jobs':[]})
    assert not classify(sample,'2026-10-12T00:00:00+00:00')
    sample['stdout']=json.dumps({'other_work':[{'creation_utc':'2026-10-12T00:00:02+00:00'}],'reset_jobs':[{'pid':123}]})
    assert not classify(sample,'2026-10-12T00:00:00+00:00')
'''
assert marker in smoke;smoke=smoke.replace(marker,marker+extra,1)
smoke=smoke.replace("'all_proto_outside_native_cases':True", "'all_proto_outside_native_cases':True,'late_early_near_boundary_missing_time_reset_classification_tests':5")
ast.parse(smoke);(R/'smoke_phase_compare_133.py').write_text(smoke,encoding='utf-8',newline='\n')
audit=renamed((R/'audit_phase_compare_132.py').read_text(encoding='utf-8'))
old="case_probes=[row for row in activity if row['place'] in ['before_case','after_case']]\nassert len(case_probes)==432 and all(row['exit']==0 for row in case_probes)\nassert {(row['place'],row['index']) for row in case_probes}=={(place,i) for i in range(216) for place in ['before_case','after_case']}"
new="""case_probes=[row for row in activity if row['place'] in ['before_case','before_case_retry','after_case']]
pauses=[json.loads(line) for line in (W/'between-case-pauses.jsonl').read_text().splitlines()] if (W/'between-case-pauses.jsonl').exists() else []
assert all(row['continuous_quiet_seconds']>=120 and row['no_native_case_repeated'] and row['no_metric_based_selection'] for row in pauses)
assert sum(row['place']=='after_case' for row in case_probes)==216
assert {row['index'] for row in case_probes}==set(range(216))
for probe in case_probes:
    assert probe['exit'] in [0,3]
    if probe['exit']==3:
        mode='after' if probe['place']=='after_case' else 'before'
        assert any(p['mode']==mode and p['index']==probe['index'] and p['initial_probe']==probe for p in pauses)
"""
assert old in audit;audit=audit.replace(old,new,1)
audit=audit.replace("before_probe=next(p for p in case_probes if p['place']=='before_case' and p['index']==spec['index'])", "before_probe=[p for p in case_probes if p['place'] in ['before_case','before_case_retry'] and p['index']==spec['index']][-1]\n    assert before_probe['exit']==0")
marker="    assert before_probe['worker_identity']==after_probe['worker_identity'] and before_probe['worker_identity']['affinity_mask']==256"
extra='''
    if after_probe['exit']==3:
        from datetime import datetime,timedelta
        messages=[json.loads(line) for line in after_probe['stdout'].splitlines()]
        assert not messages[0]['reset_jobs']
        jobs=messages[0]['other_work']+([] if len(messages)<2 else messages[1]['visible_build_jobs'])
        cutoff=max(datetime.fromisoformat(case['completed_utc'])+timedelta(seconds=.1),datetime.fromisoformat(after_probe['started_utc']))
        assert jobs and all(datetime.fromisoformat(job['creation_utc'])>=cutoff for job in jobs)
    for pause in (p for p in pauses if p['index']==spec['index']):
        if pause['mode']=='before':assert pause['completed_utc']<=case['started_utc']
        else:assert case['completed_utc']<=pause['started_utc']<=pause['completed_utc']
        if pause['mode']=='after' and spec['index']<215:assert pause['completed_utc']<=cases[spec['index']+1]['started_utc']
'''
assert marker in audit;audit=audit.replace(marker,marker+extra,1)
audit=audit.replace("'all_original_release_gates_unchanged':True", "'all_original_release_gates_unchanged':True,'between_case_pauses':len(pauses),'all_cases_kept_once_without_metric_selection':True")
ast.parse(audit);(R/'audit_phase_compare_133.py').write_text(audit,encoding='utf-8',newline='\n')
print('Fresh133 protocol prepared: only proved post-exit activity can wait; possible overlap rejects whole prefix')
