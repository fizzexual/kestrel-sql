from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-130';N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
p=load(W/'policy.json');assert p['trial']==130 and len(p['cases'])==216
assert load(W/'smoke-proof.json')['complete'] and not (W/'component-cases.jsonl').exists()
old=N.read_bytes();expected=load(R/'phase129-closed-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

### Fresh actual Archive comparison130 declared / owned controller — {stamp}

216 cases/12 rounds/six shapes,32x1024 rows/three columns. Exact supported016
A/B and exact127 C, same RNG20261011/permutations once per shape per half.
Reused154 baseline tests/336 candidate tests/two lints, zero fresh Rusttests.
Six fresh excluded full independent preflights pass196608rows/4718592CRCbytes.
120 continuously clear seconds after prep/freezes,10s observations/two-hour
deadline, ownedCPU8; activity probes before/afterEVERYnativecase. InputCRC/read,
phase selection, indexes and sync remain charged in actualcompact_small timer.
Numerical thresholds unchanged:72AA/72guards/sixgoals full/bothhalves, plus
originalrelease324Native/252service/42goals/153AA/171guards/correctness/recovery.

Launch work/launch_phase_compare_130.ps1 records actualwait/exit in
work/phase130-actual-exits.json; correctlog work/run-phase-compare-130.log.
Poll ONLY owned tool session or this.log tail whiletimed: no.git/hash/copy/build/
cleanup/audits or process query that includes.py paths (129 falsealarm).
Finish complete216 plus independent audit AFTER actualcontrollerexit. Any
failure preserves entireprefix/unstartedlist without selectedretiming.
No app/process stopped. Supported016unchanged/017unreleased. Shortprivate
outcome/source/freshremoteverify then exactnativecompletedfixturecleanup.
AutomationACTIVE30min/checkerPAUSED; no expiredresetrearm/oldchat/oldautomation.
'''
with N.open('ab') as f:f.write(note.encode())
assert N.read_bytes()==old+note.encode()
(R/'phase130-running-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'trial':130,'declared_cases':216,'no_case_completion_claimed':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Fresh130 declared checkpoint appended before timing')
