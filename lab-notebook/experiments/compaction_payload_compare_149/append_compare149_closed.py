from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
cleanup=load(R/'phase149-storage-cleanup-proof.json');assert cleanup['completed149_stores_closed'] and not (R/'perf-149').exists()
assert load(R/'phase149-publication-actual-exits.json')['publication_actual_exit']==0
saved=load(R/'phase149-remote-save-proof.json');assert saved['complete'] and saved['private'] and saved['fresh_remote_text_and_source_byte_exact']
assert not (R/'phase149-closed-next-proof.json').exists()
old=N.read_bytes();expected=load(R/'phase149-running-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

### 149 complete comparison fully closed — {stamp}

ALL216 native/controller/two metadata workers/two auditors actual0; no forced
kills. Controller ended23:59:39Z; full independent audits ended00:02:54Z after
131.371 observed clear seconds/zero busy resets.7077888 exact rows/169869312 CRC
bytes/full indexes/original receipt digests/head33/2304 generations from declared
run+1 pass. ALL528 probes vs ALL216 native lifetimes114048 pairs pass; frozen
bytes exact. Four predeclared outside-timer pauses, every sample/stall once;
no selected retiming/outlier discard/metric selection/gate loosening. Six fresh
excluded preflights196608 rows/4718592 CRC pass after120.968 quiet/zero resets.
Reused154 baseline/348 candidate tests/two lints/52 stores/wire/recovery; NO Rust
build/test/prerequisite repeated and no failed149 native/audit/build attempt.

149 OVERALL REJECTED31/144 A/A and22/144 guards;0/6 goals fail. All6 clustered
goals/controls pass full/both halves: whole6.06690->5.53325ms paired8.74% lower,
preparation1.94355->1.45345ms paired25.73% lower. Clustered write+sync full+2.07%
with passing controls; no write+sync gain. This compares JOINT131+144+147 vs016,
not isolated147; do not combine ratios with146/133 or identify an exclusive cause.
{load(R/'phase149-publication-proof.json')['calibrated_guards_failed']} calibrated failed guards: ordered prepare full/first/second1.192616/1.164632/
1.215284, ordered write full/second1.128638/1.144353 and ordered second whole
p95 1.103552; interleaved first prepare/write1.149541/1.136762; duplicates full/
second write1.144384/1.145262; late full/first prepare1.104436/1.124586; extreme
full whole p95 5.615382 (9.8802->55.4811ms,AA.977845), extreme first write1.158307.
Other failed guards have failed
controls and remain inconclusive. Every53 failed check is saved. Candidate147
UNADOPTED/performance-rejected; supported016 exact,017 UNRELEASED.

Private main{saved['head']}, {len(saved['files'])} files/
{sum(f['bytes'] for f in saved['files'])} bytes freshly exact remote-verified.
SHORT COMPACTION_PAYLOAD_COMPARE_149.md/all failed checks/actual source/proofs,
no raw bundle. Native exact perf149 removed{cleanup['logical_bytes_removed']} bytes/
{cleanup['files_removed']} files; small useful kits/old private refs/tags/releases
retained. Source016/main clean after save. Never rerun149/148 or passed147
prerequisites/publication/cleanup. Latest append preserves all older bytes.

No150 job declared here. NEXT actual engineering must address measured ordered
preparation/write and tail regressions, not merely repeat calibration/reports or
loosen gates. Inspect actual publish allocation/CRC/writer costs before choosing
a justified workload-dependent change; a contiguous bounded CRC output buffer
is a hypothesis to reduce retained-vector allocation/fragmentation, not a proven
cause or speed gain. Research unfamiliar techniques in primary documentation.
New engine bytes need fresh normal/fault debug/release correctness/two strict
lints/full independent wire/payload/index/CRC/original receipt digests/generations
and recovery; unchanged prerequisites explicitly reused, no rebuild for harness
repairs. Future fresh150+ only AFTER149 closure, full balanced same-D baselines,
full/both-half A/A/median-tail-setup guards, all input/phase/index/writes/sync
charged. Original release324Native/252service/42goals/153AA/171guards plus
correctness/retry/recovery/sustained service unchanged before adoption/release.
No component-only release/universal wins/guessed ETA.

FIRST actual reset/ALL new supervisors including relative deployment_soak and
global builds/direct Java Maven/Gradle. ANY timed/cohort active OR waiting blocks
Git/hash/copy/build/package/cleanup/independent audits/other benchmarks. Active
native cohorts use OWNED fresh guards/session/small logs only, no extra root CIM.
Strict120 continuous quiet after prep/freezes/reset on activity/before-after
every case. Persistent worker idle on stdin during native lives. Before busy
starts NO timer; after waits only EVERY birth>=native exit+100ms AND>=post-probe
start. Missing birth/reset/possible overlap rejects WHOLE prefix. Finish full
cohorts/audits or all attempted/failed/unstarted prefix before new work. No
selected retiming/outlier discard/gate loosening; waits not DB scheduling.
SHORT private outcomes/every failure/useful source/fresh exact bytes then native
literal absolute scoped no-reparse completed fixtures/build cleanup. No multiGB
raw bundles/old refs/tags/releases deletion; keep useful kits/unsaved work/unique
unverified exports. All builds/tests LOCAL/Actions$0 Stop usage/evidence skipCI.
Reset wait-expired-no-source-mutated; old migration DISABLED/old loop/checker
PAUSED. Never stop/message unrelated projects/apps/forcequit/rearm expired reset/
resume abandoned chats. Same ACTIVE30min heartbeat/name/target/notification prefs.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'phase149-closed-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'149_closed':True,'candidate147_performance_rejected':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('149 closed checkpoint appended; old byte prefix exact')
