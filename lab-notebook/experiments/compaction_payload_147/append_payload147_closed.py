from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
c=load(R/'payload147-storage-cleanup-proof.json');p=load(R/'payload147-publication-proof.json');v=load(R/'payload147-remote-save-proof.json');kit=load(R/'compaction-kit-147/provenance.json')
assert c['completed147_stores_and_builds_closed'] and not (R/'perf-147').exists()
assert not (R/'payload147-closed-next-proof.json').exists()
old=N.read_bytes();expected=load(R/'payload147-started-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###147 implemented/correct/wire/recovery/private verified/closed — {stamp}

147 ACTUAL bounded CRCpayloadreuse code isCOMPLETE/UNTIMED. FOUR freshnormal/
faultdebug/release87each348tests/twostrictlints/originaldriver actual0; all52
declaredindependentstores644636rows15471264CRCbytes/originalreceipts/indexes/
generations pass. All12 supported016/candidate cases393216rows9437184CRCbytes/
sixremainingsegmentcatalog pairs byteexact. Artifact-only CLI/seed/fault builds
actual0, no passedtests repeated. All14 recoverycases56expectedexits28672rows/
688128CRCbytes/coldqueries/originalreceipts/head2before-head3after/IOpoison-old
snapshotreadable pass. Seven ownedexits86/sevenIOerrors87, noforcedunrelated
kill/physicalpowerlossproof. Originalcontroller1 afterfirstfault onPython52704
postguardhold; actualseed/import/fault0/0/86 preserved. Finisheractual0 reused
thoseTHREE commands, executedONLY53unstarted, metadatawaitoutsidecases; no
passedCargo/native replay. Allfailures/actualsource preserved.

Private main{p['private_main']} savesSHORT COMPACTION_PAYLOAD_147.md/actualcode/
everyfailure/proofs; freshremote{len(v['files'])}files{sum(x['bytes'] for x in v['files'])}
bytes exact. Nativeexactperf147 cleanup removed{c['logical_bytes_removed']}bytes/
{c['files_removed']}files. Usefulcompaction-kit-147 candidate+3recoveryartifacts
retained; candidateSHA{kit['useful_executable']['sha256']}.
Supported016 source/tests/deps/binaries unchanged;147speedUNMEASURED,017UNRELEASED.
Neverrerun147passedbuilds/audits/wire/recovery/publication/cleanup.

ActualCRCbytevectorsretained onlysmallcompaction, checkedlogicalbytes andsum
ACTUALbytevectorcapacities<=1MiB; overflow/overbudget dropsretention/fallsback
originalstream. Descriptors/existingCRCblocktemporary additional. Consumed/
dropped duringsegmentwrite beforeexplicitflush/sync. Original64KiBwriter,
BOTHsyncs/rename/receipts/ACK/faultsequence unchanged; ordinaryappend/larger
compactionstream original. Reader/inputCRC/sums/phase/merge/sortedness/index/
format outsidepublish exact144; no unsafe/dependency/API/globalsetting change,
rejected134/136/138/140 absent. Builds onexact131+144; no147isolatedspeedclaim.

No148cohort declaredhere. Nextunused148+ afteractualreset/ALLnewsupervisor/
globalbuild checks. Prepare NEW COMPLETE216 balancedsameD supported016A/B vs
JOINT131+144+147 C, not isolated147; reuse154baseline/348candidate/twolints/
52stores/wire/recovery explicitly. No Rustbuild for unchangedcode/harnessrepair.
12rounds/sixshapes/all6permutations pershapeperhalf/32x1024rows/3cols. Full/
bothhalf144AA/144guards (whole/prepare/write/segment-sync/catalog-sync/write+
syncmedians andwhole/setupp95=max),6clusteredwhole<=.95/prepare<=.90 goals,
AA[.90,1.10]/guard<=1.10 unchanged. ALLinput/readCRC/phase/index/write/flush/
synccharged. Everycase/stallonce, noselectedretiming/outlierdiscard/metricchoice/
gateloosening. Strict120continuousquiet afterprep/freezes/percasebefore-after/
ownedCPU8/persistentmetadataidle duringnative. Beforebusy startsNOtimer; after
only everybirth>=nativeexit+100ms AND>=postprobestart canwait. Missingbirth/
reset/possibleoverlap rejectsWHOLEprefix. EVERYprobevsEVERYlife/allpayload/
index/CRC/originaldigest+declaredgeneration/frozenbytes/order/full-halfmetrics/
actualexits independentlyaudited. DuringNative onlyfreshownedguardresponses/
actualsessionstatus, neverextrarootCIM. Waitsnotdatabase scheduling.

146 CLOSED numericalclusterwhole17.19%lower/prep48.98%lower/full-bothhalfgoals
pass but32AA/14guards/3calibratedlosses/manualrootquerygap makesoverallunqualified.
Do notcombinecohortratios/promote144 orretime146. Oldlimited133gains/125AAfail/
126kernelexclusions+orderedregression andallrejectedvariants remain. Original
release324Native/252service/42goals/153AA/171guards pluscorrectness/retry/recovery/
sustainedservice unchanged. No componentonlyadoption/release/universalwins/ETA.

FIRSTactualreset/allnewsupervisors inclrelativedeployment_soak/globalbuilds
includingdirectJavaMavenGradle. Anytimed/cohortactiveORwaiting blocksGit/hash/
copy/build/package/cleanup/independentaudit/otherbenchmark. Fixedmetadataentry
outsideNative; duringactiveusefreshownedguards/sessions/smalllogs. Neverstop/
messageunrelatedproject/app/forcequit/rearmexpiredreset/resumeabandonedchat/
oldmigration/loops/checker. SHORTprivateoutcomes/failures/source/freshbytes then
nativeabsolute literal scopedno-reparse cleanup; no rawmultiGBbundles/history/
ref/tag/release deletion. Keepkits/unsavedwork/uniqueunverifiedexports. Alltests/
buildsLOCAL/Actions$0Stopusage/evidence skipCI, sameACTIVE30minheartbeat/target/
name/prefs. Advanceactualengineering, neveronlyreplayclosedjobs orreports.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
proof={'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'147_closed':True,'performance_UNMEASURED':True,'release017_qualified':False}
(R/'payload147-closed-next-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof))
