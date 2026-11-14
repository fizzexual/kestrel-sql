from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
proof=load(R/'profile143-remote-save-proof.json');clean=load(R/'profile143-storage-cleanup-proof.json');prior=load(R/'profile143-running-next-proof.json')
assert proof['complete'] and proof['fresh_remote_text_and_source_byte_exact'] and clean['complete']
old=N.read_bytes();assert hashlib.sha256(old).hexdigest()==prior['new_sha256']
stamp=datetime.now(timezone.utc).isoformat()
note=f'''\n## Index diagnostic143 CLOSED / complete measured kernel result ({stamp})

All216native/controller/2workers/2auditors actualexit0. Controller16:56:00Z,
auditors17:00:31Z after131.695continuousquiet/zeroresets. Exact7077888represented
rows169869312CRCbytes;715probesvs216native=154440pairs,allchildbirths/7outside-
lifetimepauses/frozenbytes checked. All samples/stalls kept once; no selected retiming.
Sixfreshexampletests/one strictlint/6independentpreflights REUSED (noengine tests).
Librarysrc/tests/dependencies remainexact016.0.3.17UNRELEASED.

143 is INDEXONLY. Globalcolumnmin/max rescans removedbyusingexistingblockextrema,
everyotherkernel/timeroperationexact142; typedJSONoutputoutsideclockfixedi128.
Fullpairedkernel reductions ordered13.493%,clustered17.407%,interleaved23.275%,
duplicates18.331%,late19.666%,extreme20.886%. All6fullcontrols pass;5shapespass
full/bothhalves5%kernelgoals. OrderedsecondhalfAA0.858189 FAILS, apparent23.220%
gaininconclusive; correspondingguard/goalqualifiedfaildespitenumericpasses.
Overall1/18AA/guard/goal fails: no calibrated numericalregression, overallkernel
qualificationfails. Before/afterms aregrouped16buildmedian/16, notindividual
latencyquantiles. Pairedratiosdifferfromratiosofunpairedmedians. Separatelegacy
stageprofilesoutsideprimarytimerputglobalrescans26.0–28.5%instrumentedtotal,
blockextremapassesalsosubstantial; clocks/code-layout overhead excludedfrom
primary, noexclusiveArchivecost inference. ALLArchive input/readCRC/merge/sort/
metadata serde/write/flush/sync/receipt/ACK/serviceEXCLUDED; no durablegain/adoption.

Private main{proof['head']}, {len(proof['files'])}files{sum(f['bytes'] for f in proof['files'])}bytes
freshremote exactverified. Nativeperf143 removed{clean['logical_bytes_removed']}bytes/
{clean['files_removed']}files; smallcorrectedindex-kit143 retained. Actualsource/
all3inconclusivechecks/shortoutcome privatelysaved; no newrawbundle/historydelete.
143CLOSED, neverrerun/overwrite. 142closedfailureandold141rejectionsremain.

Nextunused144-or-laterONLY. Implement minimalACTUALArchivepublish global extrema
reusefromexistingblock_min/max usingmeasured143cost; keep exact131phase/merge,
original64KiBwriter,originalinputCRCreads,sum/metadataformat/receipts/ACK/sync/
cutpoints. DO NOTadoptrejectedwriter134/136,allocation138,coalesced140variants.
Freshnormal/faultdebug/releasetests/strictlints/fullindependentpayload/index/CRC/
wire/receipt+generation/recovery REQUIRED fornewenginebytes, thencompletebalanced
sameDsupported016 A/B vsjointcandidate C, charged allphase/input/index/write/sync,
full/bothhalfA/A/median/tail/setup andunchangedgoals. Declarecomparisonpurpose:
jointphase131+indexchangevs016, notisolate144effectfrom143kernel. Supported016
byteexact; original324Native/252service/42goals/153AA/171guards+correctness/retry/
recovery/sustainedservice unchangedbeforeadoption/release. No ETA/universalwins.

FIRSTreset/ALLactualsupervisors/newjobs inclrelative deploymentsoakDargs; no
clock/PID/restartgap exits. Neverstop/messageanotherapp/project, stopfiles,
forcequit/rearmreset. HoldGit/hash/copy/build/package/cleanup/independentaudits/
otherbenchmarks whileANYtimed/declaredcohort activeORwaiting. Pollownsession/
smalllogs; no inlinePythonfilename status. Freshstrictreset/task/global incl
directJavaMaven/Gradle beforetiming,120continuouslyobservedquietafterpreparation,
resetonactivity. Per-casebefore/after guards; ownedmetadataidleonstdinwhile
native. Outside-lifetimewaitsonlypredeclared: beforebusyNOtimer; afterEVERYbirth
>=nativeexit+100ms AND>=postprobe; missingtime/reset/possibleoverlaprejectFULL
prefix. Preserveallattempted/failed/unstarted; noselectedretiming/outlierdiscard.
SHORTprivate outcomes/failures/usefulsource,fresh exactremotebytes thennative
literalabsolute no-reparsecompletedcleanup. Retainusefulkits/unsaved/unique
unverifiedexports; no multiGBbundles/oldhistory/ref/tag/releasedeletion. Local
builds/tests/Actions$0Stopusage/evidence skipCI. Resetwait-expireduntouched,
oldmigrationdisabled/oldloop+checkerpaused; keepACTIVE30min samechat/name/prefs.
Advanceactualenginework, notmerecalibration/statusreplay. Quietunchangedbusy.
'''
after=old+note.encode();N.write_bytes(after);assert N.read_bytes()==after and after[:len(old)]==old
out={'utc':stamp,'old_sha256':prior['new_sha256'],'new_sha256':hashlib.sha256(after).hexdigest(),'old_history_prefix_exact':True,'143_closed':True,'release017_qualified':False}
(R/'profile143-closed-next-proof.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(out),flush=True)
