from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-149';N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(R/'phase149-preparation-actual-exits.json')['preparation_actual_exit']==0
assert load(R/'phase149-preflight-actual-exits.json')['preflight_actual_exit']==0
smoke=load(W/'smoke-proof.json');assert smoke['complete'] and len(smoke['checks'])==6
assert not (W/'component-cases.jsonl').exists() and not (R/'phase149-preflight-ready-next-proof.json').exists()
old=N.read_bytes();expected=load(R/'phase148-closed-next-proof.json')['new_sha256']
assert hashlib.sha256(old).hexdigest()==expected
p=load(W/'policy.json');assert len(p['cases'])==216 and p['component_checks']=={'AA':144,'guards':144,'clustered_goals':6}
assert p['prerequisites_reused']['candidate147_tests']==348 and p['prerequisites_reused']['candidate_independent_stores']==52
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

### 149 complete comparison prepared and preflight passed — {stamp}

147 is CLOSED at private435f750fedbe105976803d699daaa9177789fe5e,65 files
368649 bytes fresh remote-exact verified. Exact999426952 bytes/7161 files removed,
useful147 candidate/recovery kit retained.348 fresh tests/two lints/52 independent
stores/six exact supported format pairs/14 recovery cases passed. Never rerun
passed147 prerequisites, publication or cleanup. Supported016 exact;017 unreleased.

CURRENT149 is NEW216 complete same-D cases: supported016 identical A/B SHA
2392cb6e53c0736a2d3bb67fd89369016848e6e12010989369b46a7a4ec2c1c7 versus
JOINT131+144+147 C SHAe2e20801121855cce9303151fcbe85cfb72864b240e15aa95e509289a38fa247.
Policy SHA{hashlib.sha256((W/'policy.json').read_bytes()).hexdigest()} declared before
binary copies/preflight. Reuse154 baseline/348 candidate tests/two lints/52 stores/
wire/recovery explicitly; NO Rust builds/tests. Six FRESH excluded preflights
196608 exact rows/4718592 CRC bytes/full indexes/original receipt digests and
declared generations pass; owned idle dummy busy-clear/five birth classifiers
pass; actual preparation/preflight/worker exits0. NO149 qualification case timed.

149 unchanged12 rounds/six shapes/all six permutations per shape per half,
32x1024 rows/three columns/RNG20261011. Full/both-half144AA/144guards across
whole/prepare/write/segment-sync/catalog-sync/write+sync medians and whole/setup
p95=max;6 clustered whole<=.95/prepare<=.90 goals,AA[.90,1.10]/guard<=1.10.
ALL input/readCRC/phase/index/write/flush/sync charged. JOINT comparison does
not isolate147 and cannot qualify release/service. Every sample/stall once;
no selected retiming/outlier removal/metric selection/gate loosening.

Launch149 appends running checkpoint ONCE from THIS ready proof before freezes
and120 continuous observed quiet/reset on activity/ownedCPU8. Strict actual
reset/tasks/all supervisors including relative deployment_soak/global builds
including direct Java Maven/Gradle before/after EVERY case. Persistent owned
metadata worker idle on stdin during every native lifetime. During active native
cohort only fresh OWNED guard responses/session status/small logs; no extra root
CIM. Before busy starts NO timer; after busy wait only if EVERY blocker birth
>=native exit+100ms AND>=post-probe start. Missing birth/reset/possible overlap
rejects WHOLE prefix. Waits are not database scheduling. Finish THIS cohort and
actual exits, then both independent full payload/index/CRC/original receipt
digest/declared run+1 generation/every probe vs EVERY lifetime/frozen bytes/order/
full-half metrics audits after fresh quiet. Preserve ALL attempted/failed/unstarted
on failure; never resume/retime rejected prefixes. Source/results UNSAVED until
SHORT private publication and fresh exact remote bytes; no early cleanup.
Next unused150+ ONLY after149 closure. Never replay146/145/older closed trials.

146 clustered numerical goals pass but32AA/14guards/calibrated tail losses and
manual root-query boundary gap leave overall performance unqualified. Do not
combine cohort ratios. Original release324Native/252service/42goals/153AA/
171guards plus correctness/retry/recovery/sustained service unchanged; no
component adoption/release/universal wins/ETA. Any timed workload/cohort active
OR waiting blocks Git/hash/copy/build/package/cleanup/independent fixture audit/
other benchmarks. Never stop/message unrelated projects/apps/forcequit/rearm
expired reset/resume abandoned chats/old migration/loops/checker. SHORT private
outcomes/every failure/useful source/fresh bytes then native literal absolute
scoped no-reparse cleanup. No multiGB raw bundles/old private refs/tags/releases
deletion; retain useful kits/unsaved work/unique unverified exports. All builds/
tests local under Actions$0 Stop usage/evidence skipCI. Same ACTIVE30min heartbeat
name/target/notification preferences; no duplicate automation.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'phase149-preflight-ready-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'149_prepared_preflight_passed':True,'no_timed_cases_yet':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print('149 ready checkpoint appended; no qualification timing started')
