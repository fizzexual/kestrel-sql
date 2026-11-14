from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-145';N=Path('D:/Codex/KESTREL_NEXT.md')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'smoke-proof.json')['complete'] and load(R/'phase145-preflight-actual-exits.json')['preflight_actual_exit']==0
p=load(W/'policy.json');assert len(p['cases'])==216 and p['component_checks']=={'AA':144,'guards':144,'clustered_goals':6}
assert p['goals']=={'clustered_wall_ms_max_ratio':.95,'clustered_prepare_ms_max_ratio':.90}
before=N.read_bytes();prior=load(R/'phase145-launch-gate-next-proof.json');assert hashlib.sha256(before).hexdigest()==prior['new_sha256']
assert not (R/'phase145-running-next-proof.json').exists()
stamp=datetime.now(timezone.utc).isoformat()
note=f"""
## Comparison145 declared and launching ({stamp})

144 engineering/private save/native cleanup are CLOSED. Private
01a16b636a2b64ab3bb1cb0846f37a60561d89f2 saved94files438016bytes freshly exact
verified; exact988035645bytes/6815files removed, useful candidate+3 recovery
artifacts retained.344 fresh tests/two strict lints/all28 stores245952rows/
5902848CRCbytes/six supported016 wire pairs/14 recovery cases56commands passed.
No passed build/audit/native prerequisite is repeated;144 speed unmeasured.

CURRENT145 is NEW complete216-case balanced12round/sixshape sameD comparison:
supported016 identical A/B versus JOINT131+144 C, not isolated144 versus131.
Policy SHA {hashlib.sha256((W/'policy.json').read_bytes()).hexdigest()}.
RNG20261011, all6 permutations per shape per half,32x1024rows/3columns.
All6 fresh excluded preflights196608rows/4718592CRCbytes and owned dummy
busy/clear+five birth classifications pass, actual preflight/worker exits0.
Reused154 baseline/344 candidate tests+two lints/wire/recovery; no Rust builds.

Check work/run-phase-compare-145.log, actual controller/worker identities,
phase145-actual-exits.json and perf-145 FIRST. Finish THIS cohort and actual
exits/full independent audits before any new work. OwnedCPU8,120 continuous
observed clear seconds after all preparation/freezes, reset on activity;
strict reset/task/supervisor/global checks before/after EVERY actual case.
Persistent metadata worker idle on stdin during native lifetimes. Before
busy startsNOtimer; after only EVERYbirth>=nativeexit+100ms AND>=postprobe
start maywait. Missingbirth/reset/possibleoverlap rejects the wholeprefix.
No selected retiming/outlier removal/metric choice/gate loosening; allstalls
kept once. Waits are not database scheduling. Charge ALL input/readCRC/phase/
index/write/flush/sync inside compact_small; no excluded indexkernel claims.

Full/both-half144AA/144guards: whole/prepare/write/segment-sync/catalog-sync/
write+sync medians and whole/setup nearest-rankp95=max with12/full or6/half.
Six clustered whole<=.95/prepare<=.90 goals, AA[.90,1.10]/guard<=1.10 unchanged.
After actual controller exit and fresh quiet, audit_phase_compare_145.py must
decode ALL payload/index/CRC/originalreceipt digests+generations from declared
run+1, frozenbytes/order/all full+halfmetrics/pause boundaries. Then
audit_lifecycle_receipts_145.py checks EVERY probe against EVERY native
lifetime/originalgenerations independently. Both actual exits required.
If held/failed preserve ALL attempted/failed/unstarted indices, neverretime.
Short private outcome/everyfailure/usefulsource, freshremotebytes thennative
absolute scoped no-reparse completed cleanup. Nextunused146+ only afterclosure.

Original release324Native/252service/42goals/153AA/171guards pluscorrectness/
retry/recovery/sustained service unchanged.145 cannot qualify release alone.
Supported016 exact/017 UNRELEASED/145 speed UNEVALUATED.143 index-only limited
gains/control failure and all older failed/rejected/unstarted outcomes remain.
FIRST actualreset/ALLnew supervisors includingrelativedeployment_soak. Any
timed/declaredtimedcohort activeORwaiting blocksGit/hash/copy/build/package/
cleanup/independentaudits/otherbenchmarks. Poll owned sessions/small logs only;
no inline process commands containing Python filenames. Neverstop/message
unrelated project/app, forcequit/rearmreset/resumeabandonedchat/oldmigration/
oldloop/checker. Localtests/builds only/Actions$0Stopusage/evidence skipCI.
No rawmultiGBbundles/privatehistory/ref/tag/release deletion; preserve useful
kits/unsavedcode/unique unverified exports. SameACTIVE30minheartbeat/name/
target/prefs, no duplicate. Advance this declared cohort, not closed jobs.
"""
with N.open('ab') as f:f.write(note.encode())
after=N.read_bytes();assert after==before+note.encode()
(R/'phase145-running-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':prior['new_sha256'],'new_sha256':hashlib.sha256(after).hexdigest(),'old_history_prefix_exact':True,'declared145_cases':216,'no_case_timed_yet':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('145 complete cohort checkpoint appended before freezes/quiet/timers')
