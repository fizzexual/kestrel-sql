"""Every probe/preflight/prefix lifetime and independently declared receipt148."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-148'
sys.path.insert(0,str(R));import archive_audit_099 as independent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines()] if p.exists() else []
def stamp(s):return datetime.fromisoformat(s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert load(R/'phase148-prefix-audit-actual-exits.json')['prefix_audit_actual_exit']==0
assert load(W/'prefix-audit.json')['independent_correctness_passed']
cases=lines(W/'component-cases.jsonl');preflights=lines(W/'preflight-native-exits.jsonl');probes=lines(W/'activity-checks.jsonl')
assert len(cases)==10 and len(preflights)==6
lifetimes=[(stamp(c['started_utc']),stamp(c['completed_utc'])) for c in preflights+cases]
assert all(a<=b for a,b in lifetimes) and all(lifetimes[i][1]<=lifetimes[i+1][0] for i in range(len(lifetimes)-1))
def outside(a,b):
    assert a<=b and all(b<=start or a>=end for start,end in lifetimes),('Metadata/native overlap',a,b)
for p in probes:outside(stamp(p['started_utc']),stamp(p['utc']))
quiet=load(R/'phase148-preflight-quiet-v2-proof.json');outside(stamp(quiet['started_utc']),stamp(quiet['completed_utc']))
assert quiet['continuous_quiet_seconds']>=120 and quiet['metadata_worker_actual_exit']==0
assert not lines(W/'between-case-pauses.jsonl')
blocker=None
for c in cases:
    before=next(p for p in probes if p['place']=='before_case' and p['index']==c['index'])
    after=next(p for p in probes if p['place']=='after_case' and p['index']==c['index'])
    assert before['exit']==0 and stamp(before['utc'])<=stamp(c['started_utc'])<=stamp(c['completed_utc'])<=stamp(after['started_utc'])
    assert before['worker_identity']==after['worker_identity']
    if c['index']!=9:assert after['exit']==0
    else:
        assert after['exit']==3
        messages=[json.loads(s) for s in after['stdout'].splitlines()]
        assert not messages[0]['reset_jobs']
        jobs=messages[0]['other_work']+([] if len(messages)<2 else messages[1]['visible_build_jobs'])
        cutoff=max(stamp(c['completed_utc'])+timedelta(seconds=.1),stamp(after['started_utc']))
        assert {j['pid'] for j in jobs}=={51924,87544,101672,103508}
        assert not all(stamp(j['creation_utc'])>=cutoff for j in jobs)
        blocker={'case_index':9,'native_started_utc':c['started_utc'],'native_completed_utc':c['completed_utc'],'post_probe_started_utc':after['started_utc'],'cutoff_utc':cutoff.isoformat(),'blockers':jobs,'blocker_birth_inside_native_lifetime':[j['pid'] for j in jobs if stamp(c['started_utc'])<=stamp(j['creation_utc'])<=stamp(c['completed_utc'])],'actual_compaction_timer_overlap_not_proven_or_disproved':True,'blocker_actions_unknown':True}
assert blocker is not None
receipts_checked=0
for c in cases:
    expected=[[f'merge121:{r}',r,r+1] for r in range(32)] if c['name'] in ['clustered','late'] else []
    assert load(W/c['stdout'])['receipts']==expected
    head,_,_,receipts=independent.metadata(W/c['fixture']);assert head==33 and set(receipts)=={key for key,r,g in expected}
    for key,r,g in expected:assert receipts[key]['generation']==r+1 and receipts[key]['rows']==1024
    receipts_checked+=len(expected)
frozen=load(W/'freeze.json');assert all(sha(W/n)==h for n,h in frozen['files'].items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'all_probes_outside_every_preflight_and_prefix_native_lifetime':True,'actual_probes':len(probes),'native_lifetimes':len(lifetimes),'probe_native_interval_pairs_checked':len(probes)*len(lifetimes),'all_original_receipt_generations_independently_declared':True,'original_receipts_checked':receipts_checked,'all_frozen_bytes_unchanged':True,'outside_lifetime_pauses':0,'failure':blocker,'failed_initial_quiet_worker_exit_not_separately_saved':True,'no_qualification_metrics_evaluated':True,'release017_qualified':False,'no_selected_retiming':True}
assert not (W/'prefix-lifecycle-audit.json').exists()
(W/'prefix-lifecycle-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(proof),flush=True)
