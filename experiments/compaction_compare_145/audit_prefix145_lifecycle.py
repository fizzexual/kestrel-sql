"""Audit every probe, gate, pause and declared receipt in rejected145."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-145'
sys.path.insert(0,str(R));import archive_audit_099 as independent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines()]
def stamp(s):return datetime.fromisoformat(s)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert load(R/'phase145-prefix-audit-actual-exits.json')['prefix_audit_actual_exit']==0
assert load(W/'prefix-audit.json')['independent_correctness_passed']
cases=lines(W/'component-cases.jsonl');probes=lines(W/'activity-checks.jsonl');pauses=lines(W/'between-case-pauses.jsonl')
preflights=lines(W/'preflight-native-exits.jsonl')
assert len(cases)==118 and len(preflights)==6
lifetimes=[(stamp(c['started_utc']),stamp(c['completed_utc'])) for c in preflights+cases]
assert all(a<=b for a,b in lifetimes) and all(lifetimes[i][1]<=lifetimes[i+1][0] for i in range(len(lifetimes)-1))
def outside(a,b):
    assert a<=b
    assert all(b<=start or a>=end for start,end in lifetimes),('probe overlaps actual native lifetime',a,b)
for probe in probes:outside(stamp(probe['started_utc']),stamp(probe['utc']))
blocked=None
for case in cases:
    before=[p for p in probes if p['place'] in ['before_case','before_case_retry'] and p['index']==case['index']][-1]
    after=next(p for p in probes if p['place']=='after_case' and p['index']==case['index'])
    assert before['exit']==0 and stamp(before['utc'])<=stamp(case['started_utc'])<=stamp(case['completed_utc'])<=stamp(after['started_utc'])
    assert before['worker_identity']==after['worker_identity'] and after['worker_identity']['affinity_mask']==256
    if after['exit']==3:
        messages=[json.loads(s) for s in after['stdout'].splitlines()]
        assert not messages[0]['reset_jobs']
        jobs=messages[0]['other_work']+([] if len(messages)<2 else messages[1]['visible_build_jobs'])
        cutoff=max(stamp(case['completed_utc'])+timedelta(seconds=.1),stamp(after['started_utc']))
        safely_late=bool(jobs) and all(stamp(j['creation_utc'])>=cutoff for j in jobs)
        if case['index']==117:
            assert not safely_late and len(jobs)==1 and jobs[0]['pid']==78572 and jobs[0]['name']=='python.exe'
            assert stamp(jobs[0]['creation_utc'])==stamp('2026-10-12T20:39:59.5590310Z')
            blocked={'case_index':117,'native_started_utc':case['started_utc'],'native_completed_utc':case['completed_utc'],
                'blocker':jobs[0],'blocker_birth_minus_native_start_seconds':(stamp(jobs[0]['creation_utc'])-stamp(case['started_utc'])).total_seconds(),
                'possible_overlap_not_an_engine_regression_or_speed_result':True,'blocker_action_unknown':True}
        else:assert safely_late and any(p['mode']=='after' and p['index']==case['index'] and p['initial_probe']==after for p in pauses)
    else:assert after['exit']==0
assert blocked is not None and blocked['blocker_birth_minus_native_start_seconds']<0
for pause in pauses:
    assert pause['continuous_quiet_seconds']>=120 and pause['no_native_case_repeated'] and pause['no_metric_based_selection']
    a,b=stamp(pause['started_utc']),stamp(pause['completed_utc']);outside(a,b)
    case=cases[pause['index']]
    if pause['mode']=='before':assert b<=stamp(case['started_utc'])
    else:assert stamp(case['completed_utc'])<=a and b<=stamp(cases[pause['index']+1]['started_utc'])
gate=load(R/'phase145-cohort-launch-wait-actual-exits.json')
assert gate['gate_actual_exit']==1 and gate['actual_wait_completed'] and gate['controller_launch_attempts']==1 and gate['metadata_polls']==1
gate_probes=lines(R/'phase145-cohort-launch-wait-metadata.jsonl')
assert len(gate_probes)==1
for p in gate_probes:
    outside(stamp(p['started_utc']),stamp(p['utc']))
    assert p['metadata_only'] and p['no_native_case_started_by_poll'] and p['clear']
    assert stamp(p['utc'])<stamp('2026-10-12T20:10:21.494103Z')<lifetimes[6][0]
# Chat tool evidence recorded metadata output20:17:41.1949379Z during before17 wait.
# These are conservative bounds, not invented exact process start/end times.
manual={'conservative_interval_start_utc':'2026-10-12T20:16:45+00:00','conservative_interval_end_utc':'2026-10-12T20:18:00+00:00',
    'observed_metadata_output_utc':'2026-10-12T20:17:41.1949379Z','source':'same-chat read-only fixed metadata helper tool result',
    'exact_probe_start_not_recorded':True,'no_hash_git_copy_build_or_cleanup':True}
outside(stamp(manual['conservative_interval_start_utc']),stamp(manual['conservative_interval_end_utc']))
assert any(p['mode']=='before' and p['index']==17 and stamp(p['started_utc'])<=stamp(manual['conservative_interval_start_utc'])<stamp(manual['conservative_interval_end_utc'])<=stamp(p['completed_utc']) for p in pauses)
receipt_count=0
for c in cases:
    declared=[[f'merge121:{r}',r,r+1] for r in range(32)] if c['name'] in ['clustered','late'] else []
    assert load(W/c['stdout'])['receipts']==declared
    head,catalog,chain,receipts=independent.metadata(W/c['fixture']);assert head==33
    assert set(receipts)=={key for key,r,g in declared}
    for key,r,g in declared:assert receipts[key]['generation']==r+1 and receipts[key]['rows']==1024
    receipt_count+=len(declared)
frozen=load(W/'freeze.json');assert all(sha(W/n)==h for n,h in frozen['files'].items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'all_probes_outside_every_preflight_and_prefix_native_lifetime':True,
    'actual_probes':len(probes),'native_lifetimes':len(lifetimes),'probe_native_interval_pairs_checked':len(probes)*len(lifetimes),
    'gate_probes_before_actual_controller_and_native_work':True,'gate_probes':len(gate_probes),'manual_metadata_envelope':manual,
    'outside_lifetime_pauses':len(pauses),'all_receipt_generations_independently_declared':True,'original_receipts_checked':receipt_count,
    'all_frozen_bytes_unchanged':True,'failure':blocked,'no_performance_qualification':True,'no_selected_retiming':True}
assert not (W/'prefix-lifecycle-audit.json').exists()
(W/'prefix-lifecycle-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(proof),flush=True)
