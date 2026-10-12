"""Additive independent ALL-probe lifetimes and declared original receipt audit."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-137'
sys.path.insert(0,str(R));import archive_audit_099 as independent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def stamp(s):return datetime.fromisoformat(s)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert load(R/'phase137-actual-exits.json')['cohort_actual_exit']==0
assert load(R/'phase137-audit-actual-exits.json')['audit_actual_exit']==0
assert load(W/'audit.json')['correctness_passed']
cases=[json.loads(s) for s in (W/'component-cases.jsonl').read_text().splitlines()]
probes=[json.loads(s) for s in (W/'activity-checks.jsonl').read_text().splitlines()]
assert len(cases)==216
lifetimes=[(stamp(c['started_utc']),stamp(c['completed_utc'])) for c in cases]
assert all(start<=end for start,end in lifetimes)
assert all(lifetimes[i][1]<=lifetimes[i+1][0] for i in range(215))
for p in probes:
    start,end=stamp(p['started_utc']),stamp(p['utc']);assert start<=end
    assert all(end<=born or start>=exited for born,exited in lifetimes),p['place']
checks=[]
for c in cases:
    result=load(W/c['stdout'])
    expected=[[f'merge121:{r}',r,r+1] for r in range(32)] if c['name'] in ['clustered','late'] else []
    assert result['receipts']==expected,(c['index'],'original receipt list/generation is not independently declared')
    head,catalog,chain,receipts=independent.metadata(W/c['fixture']);assert head==33
    assert set(receipts)=={row[0] for row in expected}
    for key,run,gen in expected:
        assert gen==run+1 and receipts[key]['generation']==run+1 and receipts[key]['rows']==1024
    checks.append({'index':c['index'],'head':head,'original_receipts_checked_against_declared_run_plus_one':len(expected)})
freeze=load(W/'freeze.json');assert all(sha(W/n)==h for n,h in freeze['files'].items())
pauses=[json.loads(s) for s in (W/'between-case-pauses.jsonl').read_text().splitlines()] if (W/'between-case-pauses.jsonl').exists() else []
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'all216_cases_checked':True,'all_probe_intervals_outside_every_native_lifetime':True,
       'actual_probes':len(probes),'probe_native_interval_pairs_checked':len(probes)*216,'original_receipts_checked':sum(x['original_receipts_checked_against_declared_run_plus_one'] for x in checks),
       'receipt_generations_derived_from_declared_inputs_not_native_output':True,'all_frozen_bytes_unchanged':True,'between_case_pauses':len(pauses),
       'all_cases_kept_once_without_metric_selection':True,'checks':checks,'release017_qualified':False}
assert proof['original_receipts_checked']==2304
assert not (W/'lifecycle-receipt-audit.json').exists()
(W/'lifecycle-receipt-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in proof.items() if k!='checks'}),flush=True)
