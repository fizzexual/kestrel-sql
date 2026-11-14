"""Independent every-probe versus every native lifetime and pause-boundary check."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,traceback
R=Path('D:/Codex/Kestrel/work');W=R/'perf-142'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def stamp(s):return datetime.fromisoformat(s)
try:
    assert load(R/'profile142-actual-exits.json')['cohort_actual_exit']==0
    assert load(R/'profile142-audit-actual-exits.json')['audit_actual_exit']==0 and load(W/'audit.json')['correctness_passed']
    cases=[json.loads(s) for s in (W/'component-cases.jsonl').read_text().splitlines()]
    probes=[json.loads(s) for s in (W/'activity-checks.jsonl').read_text().splitlines()]
    assert len(cases)==216
    life=[(stamp(c['started_utc']),stamp(c['completed_utc'])) for c in cases]
    assert all(a<=b for a,b in life) and all(life[i][1]<=life[i+1][0] for i in range(215))
    for c,(a,b) in zip(cases,life):
        creation=datetime.fromtimestamp((c['identity']['creation_filetime']-116444736000000000)/1e7,timezone.utc)
        assert a<=creation<=b
    for p in probes:
        a,b=stamp(p['started_utc']),stamp(p['utc']);assert a<=b
        assert all(b<=born or a>=exited for born,exited in life),p['place']
    for c in cases:
        before=[p for p in probes if p['index']==c['index'] and p['place'] in ('before_case','before_case_retry')][-1]
        after=[p for p in probes if p['index']==c['index'] and p['place']=='after_case']
        assert before['exit']==0 and stamp(before['utc'])<=stamp(c['started_utc']) and len(after)==1 and stamp(after[0]['started_utc'])>=stamp(c['completed_utc'])
    pauses=[json.loads(s) for s in (W/'between-case-pauses.jsonl').read_text().splitlines()] if (W/'between-case-pauses.jsonl').exists() else []
    for pause in pauses:
        assert pause['continuous_quiet_seconds']>=120 and pause['no_native_case_repeated'] and pause['no_metric_based_selection']
        a,b=stamp(pause['started_utc']),stamp(pause['completed_utc']);assert all(b<=born or a>=exited for born,exited in life)
        probe=pause['initial_probe'];assert probe['exit']==3
        if pause['mode']=='after':
            messages=[json.loads(line) for line in probe['stdout'].splitlines()];assert not messages[0].get('reset_jobs')
            jobs=messages[0]['other_work']+([] if len(messages)<2 else messages[1]['visible_build_jobs']);assert jobs
            cutoff=max(stamp(pause['native_completed_utc'])+timedelta(seconds=.1),stamp(probe['started_utc']))
            assert all(stamp(j['creation_utc'])>=cutoff for j in jobs)
        quiet=[p for p in probes if p['place']=='between_case_wait_'+pause['mode'] and p['index']==pause['index'] and a<=stamp(p['started_utc'])<=b]
        lastbusy=max((i for i,p in enumerate(quiet) if p['exit']!=0),default=-1);clear=quiet[lastbusy+1:]
        assert clear and all(p['exit']==0 for p in clear) and (stamp(clear[-1]['utc'])-stamp(clear[0]['utc'])).total_seconds()>=120
    freeze=load(W/'freeze.json')
    for n,h in freeze['files'].items():
        with (W/n).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h
    proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'native_cases':216,'actual_probes':len(probes),'probe_native_pairs_checked':len(probes)*216,'every_probe_outside_every_native_lifetime':True,'all_actual_child_births_checked':True,'every_pause_checked':True,'pauses':len(pauses),'frozen_bytes_exact':True,'index_only_no_Archive_receipt_claim':True,'release017_qualified':False}
    assert not (W/'lifecycle-audit.json').exists();(W/'lifecycle-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof),flush=True)
except BaseException:
    (W/'lifecycle-audit-failure.json').write_text(json.dumps({'error':traceback.format_exc(),'no_case_retimed':True},indent=2)+'\n',encoding='utf-8',newline='\n');raise
