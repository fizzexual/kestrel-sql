"""Fresh complete148 comparison from privately saved actual146 controllers."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json

R = Path('D:/Codex/Kestrel/work')
P = R.parent / 'outputs/kestrel-sql'
prior = P / 'experiments/compaction_extrema_compare_146'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, s):
    assert not p.exists(), p
    if p.suffix == '.py': ast.parse(s, filename=p.name)
    p.write_text(s.rstrip()+'\n', encoding='utf-8', newline='\n')

assert load(R/'payload147-storage-cleanup-proof.json')['completed147_stores_and_builds_closed']
assert load(R/'payload147-publication-v2-actual-exits.json')['publication_actual_exit'] == 0
assert not (R/'perf-147').exists() and not (R/'perf-148').exists()
assert not (P/'experiments/compaction_payload_compare_148').exists()
parents = {}
names = ['prepare_phase_compare_146.py', 'run_phase_compare_146.py',
    'audit_phase_compare_146.py', 'smoke_phase_compare_146.py',
    'activity_worker_146.ps1', 'launch_phase_compare_146.ps1',
    'audit_lifecycle_receipts_146.py', 'launch_preflight_phase146.ps1',
    'launch_audits_phase146.ps1']
for name in names:
    source = prior/name; parents[name] = sha(source)
    old = source.read_text(encoding='utf-8')
    new = old.replace('146', '148').replace('candidate144', 'candidate147')
    new = new.replace('compaction-kit-144', 'compaction-kit-147')
    new = new.replace('derive_extrema_compare_148.py', 'derive_payload_compare_148.py')
    new = new.replace('joint131_extrema144', 'joint131_extrema144_payload147')
    if name == 'prepare_phase_compare_146.py':
        new = new.replace('exact131 and the bounded-extrema144 binary', 'supported016 and the joint131+144+147 binary')
        new = new.replace("load(R/'extrema144-storage-cleanup-proof.json')['completed144_stores_and_regenerable_builds_closed'] and not (R/'perf-144').exists()", "load(R/'payload147-storage-cleanup-proof.json')['completed147_stores_and_builds_closed'] and not (R/'perf-147').exists()")
        new = new.replace("load(R/'phase145-publication-proof.json')['private_main']", "load(R/'payload147-publication-proof.json')['private_main']")
        new = new.replace("'candidate147_tests':344", "'candidate147_tests':348")
        new = new.replace("'candidate_independent_stores':28", "'candidate_independent_stores':52")
        start = new.index("policy['kind']=")
        end = new.index("policy['metrics']=", start)
        new = new[:start]+"policy['kind']='Complete Archive compaction: supported016 identical A/B versus JOINT131+144+147 C'\npolicy['hypothesis']='147 reuses CRC output bytes once during eligible compaction with checked total actual Vec byte capacity<=1MiB, dropping all retention on overflow/overbudget and using original stream.131 selects ordered concatenation or bounded merge from charged input disorder;144 reduces existing block extrema. Original64KiB writer, all input/readCRC/phase/index/write/flush/sync, both explicit syncs, format, receipts/ACK and cutpoints remain. This compares JOINT131+144+147 against supported016, not isolated147 versus144; it cannot qualify release/service by itself.'\n"+new[end:]
        assert 'payload147-publication-proof.json' in new and 'candidate147_tests' in new
    if name == 'audit_phase_compare_146.py':
        assert old[old.index('def rows('):old.index('def nearest(')] == new[new.index('def rows('):new.index('def nearest(')]
    write(R/name.replace('146', '148'), new)

ready = """from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-148';N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(R/'phase148-preparation-actual-exits.json')['preparation_actual_exit']==0
assert load(R/'phase148-preflight-actual-exits.json')['preflight_actual_exit']==0
smoke=load(W/'smoke-proof.json');assert smoke['complete'] and len(smoke['checks'])==6
assert not (W/'component-cases.jsonl').exists() and not (R/'phase148-preflight-ready-next-proof.json').exists()
old=N.read_bytes();expected=load(R/'payload147-closed-next-proof.json')['new_sha256']
assert hashlib.sha256(old).hexdigest()==expected
p=load(W/'policy.json');assert len(p['cases'])==216 and p['component_checks']=={'AA':144,'guards':144,'clustered_goals':6}
assert p['prerequisites_reused']['candidate147_tests']==348 and p['prerequisites_reused']['candidate_independent_stores']==52
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

### 148 complete comparison prepared and preflight passed — {stamp}

147 is CLOSED at private435f750fedbe105976803d699daaa9177789fe5e,65 files
368649 bytes fresh remote-exact verified. Exact999426952 bytes/7161 files removed,
useful147 candidate/recovery kit retained.348 fresh tests/two lints/52 independent
stores/six exact supported format pairs/14 recovery cases passed. Never rerun
passed147 prerequisites, publication or cleanup. Supported016 exact;017 unreleased.

CURRENT148 is NEW216 complete same-D cases: supported016 identical A/B SHA
2392cb6e53c0736a2d3bb67fd89369016848e6e12010989369b46a7a4ec2c1c7 versus
JOINT131+144+147 C SHAe2e20801121855cce9303151fcbe85cfb72864b240e15aa95e509289a38fa247.
Policy SHA{hashlib.sha256((W/'policy.json').read_bytes()).hexdigest()} declared before
binary copies/preflight. Reuse154 baseline/348 candidate tests/two lints/52 stores/
wire/recovery explicitly; NO Rust builds/tests. Six FRESH excluded preflights
196608 exact rows/4718592 CRC bytes/full indexes/original receipt digests and
declared generations pass; owned idle dummy busy-clear/five birth classifiers
pass; actual preparation/preflight/worker exits0. NO148 qualification case timed.

148 unchanged12 rounds/six shapes/all six permutations per shape per half,
32x1024 rows/three columns/RNG20261011. Full/both-half144AA/144guards across
whole/prepare/write/segment-sync/catalog-sync/write+sync medians and whole/setup
p95=max;6 clustered whole<=.95/prepare<=.90 goals,AA[.90,1.10]/guard<=1.10.
ALL input/readCRC/phase/index/write/flush/sync charged. JOINT comparison does
not isolate147 and cannot qualify release/service. Every sample/stall once;
no selected retiming/outlier removal/metric selection/gate loosening.

Launch148 appends running checkpoint ONCE from THIS ready proof before freezes
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
Next unused149+ ONLY after148 closure. Never replay146/145/older closed trials.

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
(R/'phase148-preflight-ready-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'148_prepared_preflight_passed':True,'no_timed_cases_yet':True},indent=2)+'\\n',encoding='utf-8',newline='\\n')
print('148 ready checkpoint appended; no qualification timing started')
"""
write(R/'append_phase148_ready.py', ready)
declared=(R/'append_phase146_declared.py').read_text(encoding='utf-8').replace('146','148').replace('147+','149+')
write(R/'append_phase148_declared.py',declared)
write(R/'payload148-controller-derivation.json',json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'parent_source_sha256':parents,'before_any148_timing':True,'new_complete216_cases':True,'same_input_generator_balanced_schedule_and_numerical_gates':True,'exact_supported016_vs_joint131_144_147':True,'candidate147_passed_prerequisites_reused':True},indent=2))
print('148 controllers derived; no native case or Rust build started')
