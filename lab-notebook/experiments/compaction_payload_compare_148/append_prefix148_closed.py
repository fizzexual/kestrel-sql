from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(R/'phase148-storage-cleanup-proof.json')['completed148_prefix_stores_closed'] and not (R/'perf-148').exists()
assert load(R/'phase148-publication-actual-exits.json')['publication_actual_exit']==0
remote=load(R/'phase148-remote-save-proof.json');assert remote['complete'] and remote['private'] and remote['fresh_remote_text_and_source_byte_exact']
assert not (R/'phase148-closed-next-proof.json').exists()
old=N.read_bytes();expected=load(R/'phase148-running-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat();cleanup=load(R/'phase148-storage-cleanup-proof.json')
note=f'''

### 148 interrupted cohort fully closed — {stamp}

All10 native cases actual0;206 indices10..215 UNSTARTED. Controller actual1
23:06:48Z after case9. Native9 lived23:06:44.579360..23:06:45.004443Z;
pwsh103508/Python51924 births inside this lifetime, later Python87544/Sprout101672
also observed. Actions unknown/inner compaction overlap neither proved nor
disproved: WHOLE prefix performance-rejected. No speed result/engine regression
or selective retiming; ALL144AA/144guards/six goals UNEVALUATED. Never resume148.

Both complete-prefix auditors actual0 after122.434 observed clear seconds/two
busy resets.327680 exact rows/7864320 CRC bytes/all indexes/original receipt
digests and128 declared run+1 generations pass;78 recorded probes vs ALL16
preflight+prefix native lifetimes1248 pairs pass. Frozen bytes exact;zero pauses,
every sample once. Three successful metadata workers actual0/no forced kills.
Initial quiet-only helper owner-rejection/closed-stdin failure saved; its worker
exit not separately recorded. Separate v2 exact owner/guards/123.656 quiet then
six FRESH preflights pass196608 rows/4718592 CRC bytes. Prefix helper sandbox
denial/dependent missing launcher occurred BEFORE auditor; host retry0, no native
case/prerequisite repeated. Every failure/actual source saved privately.

Private main{remote['head']}, {len(remote['files'])} files/
{sum(f['bytes'] for f in remote['files'])} bytes fresh exact remote-verified.
SHORT COMPACTION_PREFIX_148.md/useful actual sources, no raw bundle. Native exact
perf148 removed{cleanup['logical_bytes_removed']} bytes/{cleanup['files_removed']} files;
useful kit147/131/144/support/recovery and old private refs/tags/releases retained.
Source016 exact/main clean after save;017 UNRELEASED.147 remains performance
UNQUALIFIED though348 tests/two lints/52 independent stores/wire/recovery passed;
never rerun passed147 or148 prerequisites/audits/publication/cleanup.

No149 declared here. Inspect latest actual reset/supervisors/global build state
first, including relative deployment_soak/direct Java Maven/Gradle. Before another
fair full216 comparison use fresh149+ and preserve policy before copies/preflight.
Reuse exact baseline154/candidate348/two lints/52 stores/wire/recovery, no Rust
rebuild for unchanged engine. Supported016 identical A/B vs JOINT131+144+147 C
does not isolate147; baselineSHA2392cb6e53c0736a2d3bb67fd89369016848e6e12010989369b46a7a4ec2c1c7,
candidateSHAe2e20801121855cce9303151fcbe85cfb72864b240e15aa95e509289a38fa247.
Complete12 rounds/six shapes/all6 permutations per shape per half/32x1024 rows/
3cols/RNG20261011,144AA/144guards/six clustered whole<=.95/prepare<=.90 goals
unchanged;AA[.90,1.10]/guard<=1.10,full-both halves/whole-prepare-write-sync/
write+sync medians and whole/setup p95=max. ALLinput/readCRC/phase/index/write/
flush/sync charged. Every case/stall once; no outlier discard/selected retiming/
metric selection/gate loosening. Research/pursue justified actual engine work
after measured complete outcomes, not only repeats/reports.

Strict120 continuous quiet after preparation/freezes/reset on activity and
before-after EVERY case. Persistent OWNED metadata worker idle on stdin during
native lifetimes; active cohorts use fresh OWNED guards/session/small logs only,
never extra root CIM. Before busy starts NO timer; after busy waits only every
birth>=native exit+100ms AND>=post-probe start. Missing birth/reset/possible
overlap rejects WHOLE prefix. Every probe vs EVERY life/all payload/index/CRC/
original digests/declared generations/frozen bytes/order/full-half controls and
actual waits/exits independently audited. Waiting cohorts block Git/hash/copy/
build/package/cleanup/independent audits/other benchmarks. Finish entire cohort
or full failed/unstarted prefix before new work. Waits are not DB scheduling.

Original release324Native/252service/42goals/153AA/171guards plus correctness/
retry/recovery/sustained service unchanged. No component adoption/release,
universal wins/guessed ETA. Preserve146/133 limitations and all previous rejected
trials; never replay them or combine cohort ratios. All tests/builds LOCAL,
Actions$0 Stop usage/evidence skipCI. SHORT private outcomes/every failure/useful
source/fresh exact remote bytes then native literal absolute scoped no-reparse
completed fixtures/build cleanup. No multiGB raw bundles/old refs/tags/releases
deletion;retain useful kits/unsaved work/unique unverified exports. Never stop/
message unrelated apps/projects/forcequit/rearm expired reset/resume abandoned
chats/old migration/loops/checker. Same ACTIVE30min heartbeat/name/target/prefs.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'phase148-closed-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'148_closed':True,'performance_UNQUALIFIED':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('148 closed checkpoint appended; original history byte prefix exact')
