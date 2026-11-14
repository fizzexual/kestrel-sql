from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
cleanup=load(R/'contiguous150-storage-cleanup-proof.json');assert cleanup['completed150_stores_and_builds_closed'] and not (R/'perf-150').exists()
assert load(R/'contiguous150-publication-actual-exits.json')['publication_actual_exit']==0
saved=load(R/'contiguous150-remote-save-proof.json');assert saved['complete'] and saved['private'] and saved['fresh_remote_text_and_source_byte_exact']
kit=load(R/'compaction-kit-150/provenance.json');assert not (R/'contiguous150-closed-next-proof.json').exists()
old=N.read_bytes();expected=load(R/'contiguous150-started-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

### 150 actual contiguous-buffer engineering fully closed — {stamp}

150 code IMPLEMENTED/correctness complete, NO qualification timings declared.
Single preallocated CRC/output byte Vec on exact131+144, feature
contiguous-compaction-payload-150; rejected147 Vec-of-Vec implementation absent.
Compaction only/checked logical bytes<=1MiB/ACTUAL capacity<=1MiB or drop/old
stream fallback. Original little-endian iterator fills directly, CRC exact
new slice, original64KiB writer consumes same per-block spans/drop beforeflush.
One descriptor/other arrays additional, not RSS cap. Ordinary append/larger
compaction original CRC temporary/stream; no cache. Reader/inputCRC/sums/extrema/
monotonicity/phase/merge/sortedness/index outsidepublish exact144; BOTH syncs,
rename/receipt/ACK/format/cutpoint sequence unchanged. No unsafe/dependency/API/
global settings/rejected134/136/138/140/147. Allocation/locality hypothesis from
149 regressions, NOT an exclusive causal proof or speed gain. Prior147 output
vectors24 for32768 rows/3cols/BLOCK_ROWS4096; original rationale incorrectly96,
separate clarification preserved it, no engine/gate/acceptance change.

Actual four normal/fault debug/release87 each=348 fresh tests/two strict lints/
original driver0. ALL52 stores644636 rows15471264 CRC/full indexes/original
receipt digests/generations pass, retained/fallback2/4095/4096/4097/43690/43691/
SQL reference/pins/reclaim/mismatch/cold reopen. ALL12 excluded supported016/
candidate cases393216 rows9437184 CRC/all six segment/catalog byte pairs exact0.
Recovery normal CLI/seed and fault artifact-only builds0; no passed tests repeated.
ALL14 recovery cases/56 expected commands28672 rows688128 CRC/cold queries/
original receipts/gen0. Seven owned exits86/seven IOerrors87, head2 before
publication/head3 after; poisoned writer old snapshot readable. No forcekill/
physical power-loss claim. Every150 build/native/auditor/recovery actual0;
no failed engine/test/recovery attempt. Never rerun passed prerequisites.

Private main{saved['head']}, {len(saved['files'])} files/
{sum(f['bytes'] for f in saved['files'])} bytes fresh exact remote-verified.
SHORT COMPACTION_CONTIGUOUS_150.md/actual source/all outcomes/clarification, no
raw bundle. Native exact perf150 removed{cleanup['logical_bytes_removed']} bytes/
{cleanup['files_removed']} files; useful compaction-kit-150 candidate+three
recovery artifacts retained. CandidateSHA{kit['useful_executable']['sha256']}.
Source016/main clean, old private refs/tags/releases retained. Speed UNMEASURED,
017 UNRELEASED; never repeat150 publication/cleanup/build/audits/recovery.

NEXT no151 job declared. Fresh151+ complete216 same-D supported016 identical
A/B vs JOINT131+144+150 C, NOT isolated150. Reuse baseline154/candidate348 tests/
two lints/52 stores/wire/recovery explicitly, no new Rust builds. Baseline kit122
SHA2392cb6e53c0736a2d3bb67fd89369016848e6e12010989369b46a7a4ec2c1c7, new kit150
above. Declare policy BEFORE copies/preflight/timing; fresh six excluded full
payload/index/CRC/original receipt digest+generation preflights and idle dummy/
five birth classifiers/actual exits.149 embedded quiet under exact smoke owner
is preferred over a separate identity helper. Preserve completed/failed prefix,
continue ONLY unstarted steps; no native/prerequisite repeat. Update existing
prompt/checkpoint to ACTUAL ready state BEFORE main launch, append running ONCE.

Unchanged12 rounds/six shapes/all6 permutations per shape per half/32x1024 rows/
3cols/RNG20261011, full/both-half144 A/A/144 guards across whole/prepare/write/
segment-sync/catalog-sync/write+sync medians and whole/setup p95=max;6 clustered
whole<=.95/prepare<=.90 goals,AA[.90,1.10]/guard<=1.10. ALL input/readCRC/phase/
index/write/flush/sync charged. Every stall/case once, no selected retiming/outlier
discard/metric selection/gate loosening. Strict120 continuous quiet AFTER prep/
freezes/reset on activity/before-after EVERY case. OwnedCPU8 only, persistent
metadata worker idle on stdin during Native. Active cohorts use fresh OWNED
guards/session/small logs only, NO extra root CIM. Before busy starts NO timer;
after waits only EVERY birth>=Native exit+100ms AND>=post-probe start. Missing
birth/reset/possible overlap rejects WHOLE prefix. Independently audit EVERY
payload/index/CRC/original digest+declared generation/EVERY probe vs EVERY life/
frozen bytes/order/full-half metrics and actual waits/exits. Finish full cohorts
or whole attempted/failed/unstarted prefix before new work. Waits not DB scheduling.

149 FULLY CLOSED/rejected31AA/22guards/14 calibrated guards. Clustered goals and
controls full/both halves pass:whole8.74%lower/prep25.73%lower, but ordered prep
19.26%higher/extreme wholep95 5.615382x with passing controls. No147 adoption/
combined-cohort ratios/exclusive allocator-disk cause. All older failed/limited
trials preserved; never replay. Original release324Native/252service/42goals/
153AA/171guards plus correctness/retry/recovery/sustained service remain before
adoption/release. No component-only release/universal wins/guessed ETA. Pursue
actual measured engineering after outcomes, not only calibration/reports.

FIRST actual reset/ALL supervisors incl relative deployment_soak/global builds/
direct Java Maven/Gradle. ANY timed/cohort active OR waiting holds Git/hash/copy/
build/package/cleanup/independent audits/other benchmarks. Never stop/message
unrelated projects/apps/forcequit/rearm expired reset/resume abandoned chats/
old migration/loops/checker. SHORT private outcomes/every failure/useful source/
fresh exact bytes then native literal absolute scoped no-reparse completed
cleanup. No multiGB raw bundles/old private refs/tags/releases deletion; keep
useful kits/unsaved work/unique unverified exports. All tests/builds LOCAL,
Actions$0 Stop usage/evidence skipCI. Reset wait-expired-no-source-mutated; old
migration DISABLED/old loop/checker PAUSED. Same ACTIVE30min heartbeat/name/
target/notification preferences. Notify only verified gain/material failure/
milestone/required human decision; unchanged busy states quiet.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'contiguous150-closed-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'150_closed':True,'performance_UNMEASURED':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('150 closed checkpoint appended; old byte prefix exact')
