"""Close complete qualified tracing controls, preserving every original and stall."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil

ROOT = Path('D:/Codex/Kestrel')
W = ROOT / 'work/perf-091'
REPO = ROOT / 'outputs/kestrel-sql'
def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):
    assert not p.exists(),p
    p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')

a=load(W/'audit.json')
assert (a['cases'],a['offered'],a['successful'],a['lost'])==(144,1872000,1872000,0)
assert (a['identity_failed_total'],a['candidate_failed_total'])==(0,0)
assert a['correctness_passed'] and a['all_required_scopes_passed']
assert len(a['scopes'])==3 and all(s['passed'] for s in a['scopes'])
assert load(W/'post-timing-process-check.json')['active_processes']==[]
baseline=load(W/'unchanged-supported-source.json')
assert all(sha(REPO/n)==h for n,h in baseline.items())
overnight='1ea28cd931377a2040e0ae7a8447c8da1f938e1ef78a3ec37bacbacd563ed58c'
assert sha(REPO/'OVERNIGHT_2026-10-07.md')==overnight
save(W/'final-source-provenance.json',dict(supported='0.3.16',supported_core_unchanged=True,
    core_source_sha256=baseline,overnight_sha256=overnight,no_source_changes_or_builds=True,
    no_remote_publication=True,utc=datetime.now(timezone.utc).isoformat()))
save(W/'decision-summary.json',dict(trial=91,correctness_passed=True,
    trace_overhead_complete_qualification_passed=True,scope='two fixed read/write profiles, full and two independent 12-round halves, exact 090 released-core artifacts',
    identity_failed_total=0,candidate_failed_total=0,identity_criteria=39,candidate_criteria=39,
    no_engine_speed_gain_or_supported_promotion=True,no_direct_090_before_after=True,
    all_previous_failures_preserved=True,supported='0.3.16',
    next_hypothesis='Investigate the measured synchronous reclamation cost and a bounded incremental implementation. Establish enumeration/deletion cost and preserve public full-reclaim behavior, pinned snapshots, orphan treatment, ownership, error outcomes, disk ceilings and all durability/ACK/retry/source guarantees. Do not attribute all service p99 or physical disk cause from descriptive intervals.'))
for name in ['conclude_091.py','preserve_091.py','prepare_preserver_091.py',
             'prepare_diagnostics_091.py','diagnose_trace_091.py','inspect_diagnostics_091.py']:
    assert not (W/name).exists()
    shutil.copy2(ROOT/'work'/name,W/name)
frozen=load(W/'timing-freeze.json')['sha256']
for path in sorted((ROOT/'work').glob('*091*.log')):
    if path.name in ['conclude-091.log','preserve-091.log']:
        continue
    assert path.name not in frozen and not (W/path.name).exists()
    shutil.copy2(path,W/path.name)
save(W/'post-cohort-read-errors.json',dict(native_runs_affected=0,raw_results_changed=False,
    errors=[{'operation':'Read guessed diagnose_088.py','error':"Cannot find path 'D:\\Codex\\Kestrel\\work\\diagnose_088.py' because it does not exist.",
        'resolution':'rg found diagnose_trace_088.py; read exact source and created a new post-cohort 091 diagnostic copy.'}],
    no_failed_native_or_raw_audits=True))
print(json.dumps({'trace_overhead_qualified_in_declared_scope':True,'identity_failed':0,
    'candidate_failed':0,'all_144_cases_retained':True,'supported_unchanged':True}))
