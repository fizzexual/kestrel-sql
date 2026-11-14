from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
p=load(R/'phase141-publication-proof.json');v=load(R/'phase141-remote-save-proof.json');c=load(R/'phase141-storage-cleanup-proof.json')
assert c['completed141_stores_closed'] and not (R/'perf-141').exists()
assert v['complete'] and v['private'] and v['fresh_remote_text_and_source_byte_exact']
old=N.read_bytes();expected=load(R/'phase141-running-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###141 closed: complete bounded-read comparison rejected — {stamp}

ALL216 native/controller actual0 (controller14:04:26Z), both metadataworkers0,
both independent auditors0 at14:07:50Z after126.76 continuous clearseconds/
zerobusyresets. ALL7,077,888exactrows/169,869,312CRCbytes/indexes/head/original
receipts checked; EVERY457probe vs EVERY216native lifetime (98,712pairs),2304
original generations independently declaredrun+1. Frozen actualsources/decoder/
binaries exact; zeroactualpauses/allcases+stalls once/no selectedretime. Reused
131340/140352tests/two lints/36stores/wire/recovery, noRustbuild or failed timing/audit attempt. Publication attempt1 failed
at precommit whitespace check on extra CRLF blank lines in3 newly generated
analysis helpers; exact failed bytes/source/exit saved. Separatev3 normalized
line endings/extra EOF lines, no engine/frozen input/order/metrics/gate change
or retiming. Attempt2 failed on read-only GraphQL privacy HTTP504 before normalization/
commit/push/cleanup; actualfailedv2source/exit saved. Separatev3 usesRESTprivacy
then same corrections; attempt3 failed at precommit whitespace check on copied CRLF publication-exit
JSON before commit/push/cleanup; exactJSON/failedv3source/exit saved. Separatev4
normalizes only JSON encoding (same fields/values), actualv4 publication wait/exit
required. No engine/frozen/cohort/metric change or rerun. Fresh6preflights196608rows4718592CRCbytes/idledummy/fivebirthtests pass.

141 REJECTED20/144A/A,15/144guards,4/6goals.107/108median controls pass; one
catalog-sync median/four wholep95/15 setupp95 controls fail. Clustered full
prepare12.475%lower,first3.939%lower,second14.408%lower; FULL/SECONDpreparegoals
pass, FIRST fails10%. Wholefull2.004%lower,first+2.914%,second2.125%lower;
allthreewhole5%goals fail. Corresponding mediancontrols pass. Orderedfull
whole4.978%lower/prep14.148%lower BUT wholep95+22.079% (5.7109->6.9718ms)
withpassingAA0.973402, so140 NOT ADOPTED. Otherfullpairedwhole interleaved+1.084%,
duplicates-0.946%,late-0.855%,extreme-0.161%. Eightcalibratedfailedguards remain,
including orderedfull/secondp95, clusteredfirstwhole/setupp95, interleavedfirst
p95, duplicatessecondwrite, latefirstcatalogsync/secondsetupp95. All39failed
checks saved. Lateapparentfullp95+6.133659x hasfailedAA0.894549 and is inconclusive.
No exclusivephysicaldisk/allocatorcause orphysicalpowerloss/universalwin/ETA
claim.140 joins rejected138allocation/134+136writer variants. Keep133limited
gain/125controls/126exclusions; never combine ratios across independenttrials.

Private main {p['private_main']} saves concise COMPACTION_READ_COMPARE_141.md,
everyfailure/actualsource. Fresh exact remote {len(v['files'])}files/
{sum(x['bytes'] for x in v['files'])}bytes verified. Native exact perf-141 removed
{c['logical_bytes_removed']}bytes/{c['files_removed']}files, useful131/140kits
retained.140source35files251788B saved at5e6d942,352tests/36independentstores/
14recoveries passed but141performance rejected. Supported016exact/mainclean/
zeroahead,017UNRELEASED. No historicalprivate refs/tags/releases deleted.

NO142 job declared yet at this checkpoint; checklatest/livejobs before starting.
Nextunused142+ ONLY. Preparation improved for several shapes but interleaved
full preparation changed only-0.328%. Isolate actual read/CRC/merge/index costs
or documented service bottlenecks before selecting a justified code change;
those medians alone do not identify an exclusive cause. Do not only repeat
calibration/reports, replay141 or loosen release goals. New enginebytes require
fresh normal/fault debug/release correctness/lints/full independent exact
wire/payload/index/CRC/original receipt+generation/recovery, then balanced sameD
full/bothhalf A/A/median/tail/setup whole-engine/service/sustained qualification.
Reuse alreadypassed identical prerequisites, no repeated builds for harnessonly
fixes. Allread/input/CRC/phase/index/write/flush/sync charged, componentcannotrelease.
Original324Native/252service/42goals/153AA/171guards +correctness/retry/recovery/
sustained unchanged beforeadoption; no universalwins/guessedETA/unsupportedgain.

FIRSTreset +ALL actual supervisors/workers/newerjobs includingrelative deployment
soakDargs. KnownSproutterminal, historicalPID/clock/gap notcompletionproof.
Neverstop/message anotherproject/app, forcequit, stopfiles or changeunrelateddata.
HoldGit/hash/copy/build/package/cleanup/independentaudits/otherbenchmarks while
ANYtimer/declaredtimedcohort activeORwaiting. Pollownedsessions/smalllogs only;
no inline statusPythonfilenames. Fresh reset/task/supervisor/globalchecks incl
directJavaMaven/Gradle and120continuouslyobservedclear seconds afterprep/freezes,
resetonbusy. Strictchecks BEFORE/AFTEReverycase, ownedmetadataworker idleonstdin
duringnative. Declared outside-lifetime waits ONLY: beforebusy startsNOtimer;
afterONLYEVERYblockerbirth>=nativeexit+100ms AND>=postprobestart. Missingtime/
reset/possibleoverlap rejectsWHOLEprefix. PreserveEVERYattempted/failed/unstarted
index; neverselectedretime/discardstall/metricchoice. Completeactual exits/full
independent payload/index/CRC/originalgeneration fromdeclaredinputs/everyprobe vs
everynativelifetime/frozenbytes/order/allscopedmetrics required. WaitsnotDBscheduling.

SHORTprivateoutcomes/everyfailure/usefulsource, freshremotebytes thennative
literalabsolute scoped no-reparse completedcleanup; no multiGBrawbundle/old
privatehistory/ref/tag/release deletion orloss of uniqueunverifiedexports/useful
kits/unsavedwork. Allbuilds/testsLOCAL/Actions$0Stopusage/evidence skipCI.
Resetwait-expired-no-source-mutated NEVERrearm/interfere; oldmigrationDISABLED/
oldloop+temporarycheckerPAUSED. Keep existingACTIVE30min heartbeat/name/samechat/
notificationprefs, no duplicate/abandonedchatresume. Advanceactualnew artifacts;
human objected to repetitive scheduling. Quietonunchangedbusy, notifyverified
gain/materialfailure/milestone/requiredrealdecision only.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'phase141-closed-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'141_closed':True,'candidate140_rejected':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('141 full outcome/private preservation/native cleanup checkpoint appended')
