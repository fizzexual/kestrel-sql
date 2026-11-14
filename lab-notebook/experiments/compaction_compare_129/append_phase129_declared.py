from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-129';N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
p=load(W/'policy.json');assert p['trial']==129 and len(p['cases'])==216
assert load(W/'smoke-proof.json')['complete'] and not (W/'component-cases.jsonl').exists()
old=N.read_bytes();expected=load(R/'resumption-next-proof-20261012.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

### Fresh actual Archive comparison129 declared / live controller — {stamp}

work/perf-129/policy.json now declares 216 cases: 12 rounds/six shapes,
32x1024 rows/three columns, exact supported016 A/B and exact phase127 C.
Fixed RNG20261011, each permutation once per shape in each half; same
input/label multiset as unstarted128. Baseline154 tests/candidate336/two lints
are REUSED. Six fresh excluded complete independent row/CRC preflights pass.
No new Rust build/test, version change or benchmark result is claimed yet.

Updated predeclared protocol waits for 120 continuously clear seconds after
all prep/hash/smokes, resetting on busy observations. Ten-second observations,
two-hour pre-timing deadline, logicalCPU8 inherited only by owned children.
Safety probes before AND after every native case are outside compaction's
clock. Input CRC/read, phase selection, indexes and durable syncs remain
charged inside the unchanged actual Archive.compact_small timer. No numerical
gate changed: 72 controls/72 guards/six clustered goals, full/both halves.
All original release gates and correctness/recovery/service requirements stay.

Live work/run_phase_compare_129.py logs work/run-phase-compare-129.log;
launch wrapper records actual exit in work/phase129-actual-exits.json.
Finish all216 cases and independent audit_phase_compare_129.py AFTER actual
cohort exit. If any guard/native error occurs, preserve the complete prefix
and unstarted list; no selected retiming. No builds/hashes/Git/copies/cleanup
or other benchmark while timings run. Sprout is terminal and inactive at
preflight; do not stop/message unrelated processes if new work appears.

Supported0.3.16 remains unchanged;0.3.17 is unreleased. Candidate127 whole
performance is still unknown until the complete fresh audit;126's kernel
numbers do not qualify it. Save concise outcomes/every failure/useful source
privately, freshly byte-verify, then native exact owned cleanup. No raw bundles
or remote history/ref/release deletion. Recurring Kestrel is ACTIVE30-minute;
temporary completion checker PAUSED. Reset never rearmed, legacy tasks remain
disabled/paused, Actions$0 Stop usage respected; local work and skipCI commits.
'''
assert N.read_bytes()==old
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'phase129-running-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'trial':129,'declared_cases':216,'no_case_completion_claimed':True},indent=2)+'\n',encoding='utf-8')
print('New129 checkpoint appended before any timing')
