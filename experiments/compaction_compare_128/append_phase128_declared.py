"""Append a checked continuation note before the first qualification timer."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-128';NEXT=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
policy=load(W/'policy.json');assert policy['trial']==128 and len(policy['cases'])==216
assert load(W/'smoke-proof.json')['complete'] and not (W/'component-cases.jsonl').exists()
old=NEXT.read_bytes();expected=load(R/'phase127-final-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

### Fresh phase comparison128 declared / live cohort controller — {stamp}

Earlier prefixes remain exact. Supported source and version remain0.3.16.
0.3.17 is unreleased and unqualified. New work/perf-128/policy.json declares
216 actual Archive component cases,12 rounds of ordered/clustered/interleaved/
duplicates/late/extreme,32x1024 rows/three columns. A/B use the byte-identical
supported016 artifact; C uses exact127 c39997c0dff47dd29683590f7501734fbb964235a712aec28d155ef3652085cd.
One fixed RNG20261011 balances every permutation once per shape in each half.
CPU8/120-second cooldown,72 A/A controls,72 guards,six clustered goals,
full/both-half checks and original release gates remain predeclared/unchanged.
All input CRC/read,phase selection,indexes and durable syncs are charged.
This compares combined127 against016,not isolated127-vs122 or126 kernel gains.

Six excluded seed5 full-row/CRC smokes actually passed. Baseline154 tests,
candidate336 tests and two strict lints are explicitly REUSED. No new Rust
build or tests. A different project has/had a30-minute Sprout deployment soak
and visible Java builds: preparation held without overlap. The old wait check
missed a relative supervisor between worker restarts; only verified own idle
waiter65552/creation2026-10-11T19:21:13.2043650Z was stopped before declaration.
V2 detects supervisors with D: workspace arguments plus workers. No other
process/app was stopped. Between-round guards verify actual controller PID /
creation and check reset/other task work/global builds, propagating busy exit3.

Live orchestration is work/wait_start_phase128_v2.ps1, tool session63944.
Its child work/run_phase_compare_128.py logs work/run-phase-compare-128.log;
finish the complete declared cohort and actual exit before any hashes/copies/
builds/cleanup/other timers. Then independent audit_phase_compare_128.py must
decode every store,receipt,digest,index,full CRC and complete tuple multiset.
Actual exits are stored in work/phase128-actual-exits.json. No timings are
claimed complete by this declaration. Preserve any failed/incomplete prefix
and every failed control; no selected retiming. Full release Native324/service252/
goals42/A/A153/guards171 and correctness/recovery/sustained qualification stay.

After actual completion/audits: save short COMPACTION_COMPARE_128.md and every
failure plus useful source privately, freshly byte-verify, then native scoped
cleanup of exact work/perf-128 only. Keep small useful122/127 artifact kits;
do not make new multiGB raw bundles. Old private history/tags/releases remain.
Reset stays terminal wait-expired-no-source-mutated; never rearm,old migration
Disabled/old automation paused. Shared C: app storage remains real. Respect
verified account Actions$0 Stop usage; local work only and skipCI commits.
Hourly continuation stays in this D: chat; no reliable release ETA.
'''
assert NEXT.read_bytes()==old
with NEXT.open('ab') as f:f.write(note.encode('utf-8'))
assert NEXT.read_bytes()==old+note.encode('utf-8')
proof={'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(NEXT.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'trial':128,'declared_cases':216,'no_cases_claimed_complete':True}
(R/'phase128-running-next-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
