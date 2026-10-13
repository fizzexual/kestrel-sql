from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-150';N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(R/'contiguous150-source-actual-exits.json')['preparation_actual_exit']==0
assert load(W/'preparation-proof.json')['complete'] and not (R/'contiguous150-started-next-proof.json').exists()
old=N.read_bytes();expected=load(R/'phase149-closed-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

### 150 actual contiguous-buffer implementation and fresh prerequisites — {stamp}

149 CLOSED/private8257dd5d18602efe260645507a35a6491ef736d7/51 files357207 bytes
fresh remote-exact verified; exact178325102 bytes/1142 files removed.31AA/22guards/
14 calibrated guards/zero goal failures; limited clustered whole8.74%lower and
preparation25.73%lower, ordered preparation/write and extreme tail regressions.
All216 full audits/528probe intervals/2304 original generations pass; no149 replay.
Supported016 exact;017 UNRELEASED.147 performance-rejected, never adopt it.

CURRENT150 is ACTUALLY IMPLEMENTED under work/perf-150/candidate, feature
contiguous-compaction-payload-150 on exact131+144, rejected147 code absent.
Compaction only/checked logical rows*columns*8<=1MiB: allocate ONE byte Vec,
check ACTUAL capacity<=1MiB or drop/fallback original stream. Fill directly using
original little-endian iterator, CRC each exact newly filled slice, then write
the same contiguous per-block spans through original64KiB BufWriter. One Vec
descriptor/other arrays additional, not a whole RSS cap. No per-block retained
vectors or compaction CRC temporary on retained path, no cross-publication cache.
Ordinary append/larger compaction original CRC temporary/stream. BOTH explicit
syncs/rename/receipt/ACK/fault cutpoint sequence/format preserved; Reader/inputCRC/
sums/block extrema/monotonicity/phase/merge/sortedness/index outsidepublish exact144.
No unsafe/dependency/API/global-setting/rejected134/136/138/140/147 code. Primary
Vec docs reviewed: capacity can exceed request, so actual capacity checked;
stable APIs below MSRV1.89, no nightly APIs. Hypothesis about allocation/locality
and writer costs, NOT measured speed or an exclusive explanation of149 regressions.

Policy declared BEFORE copy/engine change, source preparation actual0. Required
four fresh normal/fault debug/release87 each=348 tests/two strict lints/original
driver, ALL52 independent stores644636rows15471264CRC/six supported wire pairs/
14 recovery cases56 commands. Existing meaningful SQL reference/2/4095/4096/
4097/43690/43691 boundaries/pins/reclaim/original receipts/mismatch/cold reopen
adapted to new feature; unchanged prior prerequisites not recounted. CURRENT
build_contiguous_150.py actual owned session41667 was running at this append;
normal debug/release174 tests already pass, fault/lints/artifact remaining.
Check work/build-contiguous-150.log, actual source/build exit proofs and each
build-step/build-proof FIRST. No duplicate controller, no passed suite rerun.
Finish active build and actual exits before independent fixture audits. Preserve
every guard-held/failed prefix and continue ONLY unstarted jobs if held.

150 source/binary UNSAVED until useful source/concise outcomes privately saved
and fresh exact remote bytes verified. Never remove early. ZERO150 qualification
timings declared; speed UNMEASURED. After actual build0 all independent payload/
index/CRC/declared original digest/generation/wire/recovery audits required before
fresh151+ performance qualification. Same full216 balanced same-D baseline016
A/B vsJOINT131+144+150 C does not isolate150; reuse passed identical prerequisites.
144AA/144guards/six clustered whole<=.95/prepare<=.90 goals/full-both halves/
median-tail-setup guards unchanged; all input/phase/index/write/flush/sync charged.
No selected retiming/outlier discard/gate loosening. Original release324Native/
252service/42goals/153AA/171guards plus correctness/retry/recovery/sustained service
unchanged. No component-only adoption/release/universal wins/guessed ETA.

FIRST actual reset/ALL live/new supervisors including relative deployment_soak/
global builds/direct Java Maven/Gradle. ANY timer/cohort active OR waiting holds
Git/hash/copy/build/package/cleanup/independent audits/other benchmarks. Active
native cohorts use OWNED fresh guards/session/small logs only, no extra root CIM.
Strict120 continuous quiet after preparation/freezes/reset on activity and
before-after EVERY case, persistent worker idle on stdin during native. Before
busy starts NO timer; after waits only EVERY birth>=native exit+100ms AND>=post
probe start. Missing birth/reset/possible overlap rejects WHOLE prefix. Finish
full cohorts/audits or whole attempted/failed/unstarted prefix before new work;
waits not database scheduling. SHORT private outcomes/everyfailure/useful source/
fresh bytes then native literal absolute scoped no-reparse completed cleanup.
No multiGB raw bundles/old private refs/tags/releases deletion; keep useful kits/
unsaved work/unique unverified exports. All builds/tests LOCAL/Actions$0 Stop usage/
evidence skipCI. Reset wait-expired-no-source-mutated; old migration DISABLED/old
loop and checker PAUSED; never forcequit/stop/message unrelated projects/apps/
rearm reset/resume abandoned chats. Same ACTIVE30min heartbeat/name/target/prefs.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'contiguous150-started-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'150_source_implemented':True,'fresh_prerequisites_in_progress':True,'timed_cases_declared':0,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('150 actual source/build checkpoint appended; old byte prefix exact')
