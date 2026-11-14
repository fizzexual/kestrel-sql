"""Record completed engineering and the exact remaining save step; no job rerun."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-144';N=Path('D:/Codex/KESTREL_NEXT.md')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'build-proof.json')['fresh_Archive_tests']==344
assert load(W/'store-audit.json')['all28_stores_checked']
assert load(W/'legacy-wire-audit.json')['all_six_wire_pairs_exact']
assert load(W/'recovery-proof.json')['complete']
assert load(R/'extrema144-recovery-finish-actual-exits.json')['recovery_actual_exit']==0
assert not (R/'extrema144-publication-v3-actual-exits.json').exists()
prior=load(R/'extrema144-started-next-proof.json');before=N.read_bytes()
assert hashlib.sha256(before).hexdigest()==prior['new_sha256']
assert not (R/'extrema144-pending-publication-next-proof.json').exists()
utc=datetime.now(timezone.utc).isoformat()
note=f'''
## Extrema144 engineering complete; private save pending ({utc})

All prerequisites are COMPLETE; no144 build/audit/recovery/cohort is running.
Actual normal/fault debug/release86 each=344 fresh tests/two strict lints pass.
Independent all28 stores245952 rows/5902848CRC bytes pass; all12 excluded
supported016/candidate cases393216rows/9437184CRC bytes, all6 segment/catalog
pairs exact. All14 recovery cases/56 expected command exits28672rows/688128CRC
bytes pass; source frozen, seven owned exits86/seven IO errors87. Named original
receipt digests/generations survive, head2 beforepub/head3 after, cold queries
pass and IO errors poison writer while oldsnapshot readable. All final actual
controller/builder/auditor waits/exit0. No physical power-loss proof. Never rerun
any passed suite, native compatibility/recovery case or independent audit.
CandidateSHA560e5868f61a3e5dc2d26aa2f30318206537af85af1eb82eeb6f861e550e711f.

Source144 only reuses existing block extrema for global published column bounds
on exact131 phase/merge and64KiBwriter, ordinary append+compaction. Reader/CRC/
sums/otherindexes/sortedness/bothsyncs/rename/receipts/ACK/format/cutpoints exact.
Supported016 untouched;144 SPEED UNMEASURED/017 UNRELEASED; zero timings declared.

Build/wire/recovery guard holds preserved; continuations ran only unstarted work:
172+172tests,7+5wirecases,4+10recoverycases. Initial artifact hold beforeCargo
ran zero jobs; v2 built only CLI/seed/fault, no tests repeated. Finisher source
write sandbox PermissionError occurred beforecreation; exact escalated retry0.
All completed/failure prefixes remain under work/perf-144 and actual helpers.

CURRENT unfinished step is PRIVATE PUBLICATION, not engine engineering:
launch_publish_extrema144.ps1 actual1 beforecommit: implicitcp1252 decoded UTF8
summary; VERSION_SUMMARY was partially appended/misdecoded before BENCHMARK
HISTORY decode failed. Exact failed publisher/exit/log saved. V2 actual1 before
changing anything on scoped partial-state assertion. prepare_publication_v3
verified exact malformed bytes were only our own edit, preserved them asbase64,
restored ONLY VERSION_SUMMARY to HEAD bytes, then generated explicitUTF8 v3.
No engine/prerequisite rerun/change. Original source remains private HEAD
6ac46ed413596b694c3b47f57fe95a53acd5265f with only untracked144 report/source;
no144 commit/push yet. Useful144 source/binary remain UNSAVED; never delete early.

V3 launcher held BEFORE Python publisher creation on unrelated globalCargo
build; no extrema144-publication-v3-actual-exits.json exists. Latest observed
global build at18:35:55Z included newerCargo60156/96804 plusrustc; check FRESH
identities, never historicalPIDs. Do not rerun v3 preparation: it already fixed
the owned partial summary. When actual guards are clear, run ONLY existing
work/launch_publish_extrema144_v3.ps1; actual engine checks are reused. Publisher
complete_extrema144_publication_v3.py will save concise COMPACTION_EXTREMA_144.md,
every failure/actual source/failed summary bytes privately withskipCI and verify
exact remote bytes, then retain candidate+three recovery artifacts in kit144.
If its actualpublisher starts/fails, inspect exact partialstate and preserve it,
do not blindly relaunch aftercommit. Once private save+actualexit0 verified, run
close_extrema144_storage_v3.ps1 for literal absolute no-reparse perf144 cleanup.
If global guard holds, keepfixtures/usefulcode and refresh remote bytes before
later cleanup. Then append_extrema144_closed_v3.py will close this checkpoint
chain; do not use stale original/v2 publication-exit dependencies.

No145timing/cohort declared. AFTER144 save/cleanup, fresh unused145+ complete216
balanced sameD supported016 identicalA/B versus JOINT131+144C, notisolated144
effect. Reuse baseline154/144344+two lints/wire/recovery.144AA/144guards full/both
halves acrosswhole/prepare/write/sync/catalog/write+sync medians andwhole/setup
p95, allstalls once. Sixclusteredwhole<=.95/prepare<=.90goals; unchangedAA
[.90,1.10]/guard<=1.10. Chargeallinput/readCRC/phase/index/write/flush/sync.
120continuous quiet afterprep/freezes, strictbefore/aftereverycase; ownedCPU8/
idle-onstdin metadataworker. Onlypredeclared proven outside-lifetimewaits,
missingbirth/reset/possibleoverlap rejects fullprefix. Complete independent
payload/index/CRC/originalreceipts+generations/everyprobe vsEVERYnative/frozen
bytes/order/full+halfmetrics/actualexits required. No selectedretiming/gateloosen.
Originalrelease324Native/252service/42goals/153AA/171guards pluscorrectness,
retry/recovery/sustainedservice unchanged. No componentrelease/universalwin/ETA.

FIRSTreset/ALLlive/newsupervisors includingrelativedeployment_soak commands.
Any timed workload/declaredtimedcohort activeORwaiting blocksGit/hash/copy/build/
package/cleanup/independentaudits/otherbenchmarks. Never stop/message unrelated
projects/apps, forcequit/rearm expiredreset/resumeabandonedchat/oldmigration/
oldloop/checker. SameACTIVE30minheartbeat/name/target/prefs. Localbuilds/tests,
Actions$0Stopusage/evidence skipCI; shortprivateoutcomes/failures/usefulsource,
freshremotebytes thennative exactcompletedcleanup. No newmultiGBbundles, preserve
historical private refs/tags/releases/usefulkits/unsavedwork/uniqueunverified
exports. Advance actual v3 save step, never replay closed engineering jobs.
'''
with N.open('ab') as f:f.write(note.encode())
after=N.read_bytes();assert after==before+note.encode()
proof={'utc':utc,'old_sha256':prior['new_sha256'],'new_sha256':hashlib.sha256(after).hexdigest(),'old_history_prefix_exact':True,'144_prerequisites_complete':True,'144_private_save_pending':True,'timed_performance_cases':0,'release017_qualified':False}
(R/'extrema144-pending-publication-next-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(proof),flush=True)
