"""Append concrete closure while preserving the complete older checkpoint bytes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
remote=load(R/'extrema144-remote-save-proof.json')
assert remote['complete'] and remote['private'] and remote['fresh_remote_text_and_source_byte_exact']
assert load(R/'extrema144-publication-v3-actual-exits.json')['publication_actual_exit']==0
assert load(R/'extrema144-recovery-finish-actual-exits.json')['recovery_actual_exit']==0
prior=load(R/'extrema144-pending-publication-next-proof.json');before=N.read_bytes()
assert hashlib.sha256(before).hexdigest()==prior['new_sha256']
assert not (R/'extrema144-closed-next-proof.json').exists()
utc=datetime.now(timezone.utc).isoformat()
cleanup=load(R/'extrema144-storage-cleanup-proof.json') if (R/'extrema144-storage-cleanup-proof.json').exists() else None
storage=f"Native exactperf144 removed{cleanup['logical_bytes_removed']}bytes/{cleanup['files_removed']}files; useful compaction-kit-144 candidate+three recovery artifacts retained." if cleanup and cleanup['complete'] else 'Exact perf-144 cleanup remains UNSTARTED/guard-held; finish only after fresh remote byte verification and actual quiet. Do not rerun tests/audits/recovery.'
note=f'''
## Actual Archive extrema144 prerequisites closed ({utc})

144 code reuses existing block_min/max for global published column extrema on
exact131 phase/merge and original64KiBwriter. Reader/inputCRC/sums/otherindex/
sortedness/bothsyncs/catalogrename/receipt/ACK/format/cutpoints unchanged.
No rejected134/136/138/140 code. Ordinary append and compaction both covered.
Four fresh normal/fault debug/release suites86 each=344tests/two strict lints;
all28 independent stores245952rows/5902848CRCbytes; all12 excluded original016
compatibility cases393216rows/9437184CRCbytes/all6 segment+catalog pairs exact;
all14 publication fault cases/56 expected command exits/28672rows/688128CRCbytes
passed. Seven owned exits86/seven injectedIOerrors87, no unrelated forcedkill.
All original receipt digests+generations survive, head2 beforepub/head3 after;
IOerror poisonswriter while oldsnapshot readable; no physical powerloss proof.
All final controllers/auditors/builders actualwait/exit0.344fresh counts are
not repeated/recounted in future comparisons. CandidateSHA
560e5868f61a3e5dc2d26aa2f30318206537af85af1eb82eeb6f861e550e711f.

Failed/held harness prefixes preserved: initialbuild stopped beforelint on
unknownPython after172passedtests; continuation ran only remaining172+2lints/
artifact. Firstwire stopped beforedupcandidate after7nativecases; continuation
held before reauditing oldstore/zero newcases; finisher ran only5unstarted.
First recoveryartifact held beforeCargo/zerojobs;v2 compiledonlynormalCLI+seed/
fault artifacts, no tests. First recovery held beforecase4 onnewNodebuild with
4completecases/16commands; finisher reused4 and completed10unstarted, then
independently rechecked every settledstore without repeatednativechildren.
Initialpublication exited1 beforecommit on cp1252/UTF8 summary decode; separate
v3 corrected onlyencoding/save plumbing; secondattempt scopehold exposed the
partial ownedsummary, exact failedbytes preserved and ownedit restored, exact failedsource/exit preserved.
Sandbox denied finisher sourcewrite beforecreation; exact approvedretry0.
Before-child waits120clear; afterfault waits only births afterexit+100ms/probe
start. Every completed prefix/actual failed and correctedsource saved. No
metricselection or performance timing, no failed engine assertion from holds.

Private{remote['head']} saved{len(remote['files'])}files/{sum(f['bytes'] for f in remote['files'])}bytes;
exact remote bytes freshly verified. {storage}
Short COMPACTION_EXTREMA_144.md and experiments/compaction_extrema_144 preserve
all source/usefulfailed attempts, no multiGBrawbundle/privatehistorydeletion.
Supported016 core/main exact;017 UNRELEASED;144 durable speed UNMEASURED.

No145 cohort declared here. NEXTunused145-or-later only afterchecking LATEST/
actualliveidentities. Predeclare complete216 balanced12round/sixshape/all6perms
perhalf sameD supported016 A/B versusJOINT131+144 C (notisolated144effect).
Reuse baseline154/144344 tests/two lints/wire/recovery explicitly, no newRust
build.144AA/144guards all full/bothhalf medwhole/prepare/write/sync/catalog/
write+sync and whole/setup nearest-rankp95=max; allstalls kept once. Sixclustered
whole<=.95/prepare<=.90goals, AA[.90,1.10]/guard<=1.10 unchanged. Charge ALL
input/readCRC/phase/index/write/flush/sync inside actual compact_small clock.
Strict reset/ALLsupervisor/global checks includingJava before/afterEVERYcase;
120continuous observedquiet afterprep/freezes, reset onbusy. OwnedCPU8, persistent
metadataworkeridleonstdin duringnative. Beforebusy startsNOtimer; afterbusywait
onlyEVERYbirth>=nativeexit+100ms AND>=postprobestart. Missingbirth/reset/possible
overlap rejects wholeprefix. Everypayload/index/CRC/originaldigest+gen from
declaredinput, everyprobe vsEVERYnative/frozenbytes/order/full+halfmetrics and
actualcontroller/native/worker/auditorwaits/exits required; noselectedretime.
Waiting is not database scheduling. Finish anycohort/audits before newwork.

143 is fullyclosed diagnostic:216correct/715probes/7outside-lifetimewaits,
full indexkernel13.5-23.3%lower; orderedsecondhalfAA0.858189fails. AllArchiveI/O/
phase/sync/ACK/service excluded, no durablegain. Private6ac46ed/45files283351B,
exact215056382B/1196filesremoved. Closed142 outputfailure and rejected139/141/
135/137 remain; neverreplay.133 limited clusteredgain/controlfailures preserved.
Originalrelease324Native/252service/42goals/153AA/171guards pluscorrectness/
retry/recovery/sustainedservice unchanged. No componentrelease/universalwin/ETA.
FIRST actualreset/allnewsupervisors beforework; anytimed or declaredtimedcohort
activeORwaiting blocksGit/hash/copy/build/package/cleanup/independentaudits.
Neverstop/message anotherproject/app, forcequit, create unrelatedstopfiles,
rearmexpiredreset, resumeabandonedchat/oldmigration/oldloop/checker. Resetexpired
untouched; oldmigrationDisabled/oldloop+checkerPaused. Localtests/builds only,
Actions$0Stopusage/skipCIevidence; shortprivateoutcomes/everyfailure/usefulsource,
freshremotebytes thenliteralabsolute native no-reparse completedcleanup. Retain
usefulkits/unsavedwork/uniqueunverifiedexports/historicalrefs/tags/releases.
SameACTIVE30minheartbeat/name/target/prefs, no duplicate. Advanceactualnextstep.
'''
with N.open('ab') as f:f.write(note.encode())
after=N.read_bytes();assert after==before+note.encode()
proof={'utc':utc,'old_sha256':prior['new_sha256'],'new_sha256':hashlib.sha256(after).hexdigest(),'old_history_prefix_exact':True,'private_head':remote['head'],'144_prerequisites_complete':True,'storage_cleanup_complete':bool(cleanup and cleanup['complete']),'timed_performance_cases':0,'release017_qualified':False}
(R/'extrema144-closed-next-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(proof),flush=True)
