from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-147';N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(R/'payload147-source-actual-exits.json')['preparation_actual_exit']==0
assert load(W/'preparation-proof.json')['source_outside_publish_byte_exact144']
assert not (R/'payload147-started-next-proof.json').exists()
old=N.read_bytes();expected=load(R/'phase146-closed-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###147 actual bounded CRC payload reuse implemented / prerequisites running — {stamp}

146 CLOSED/privatea50c79b001cf18c5a2320594fad6e4c8aef5b9d0/47files326427bytes
fresh exactverified;178303273bytes1142files removed.216 exactstores7077888rows/
169869312CRCbytes/allactualexits0,517workerprobes111672pairs/2304declaredreceipt
generations/twooutsidewaits/frozenbytes exact.32AA/14guards fail, all6clustered
goals+controls full/bothhalves pass. Clusterwhole6.3327->5.1995ms paired17.19%
lower/prepare2.15705->1.1091ms paired48.98%lower. Joint131+144, notisolated144.
Threecalibratedfailures: interleaved fullp958.0762->35.0418ms4.338897x,latefirst
p956.4848->29.4612ms4.543116x,late2ndwrite1.107528/AA0.980693. Extra initial
rootCIM exactstartunlogged; conservativeenvelope intersects14..17, noneclustered.
Actualoverlap notproven/disproved; monitoringqualificationfails, noadoption.
Everylimitation/failedcheck saved. No146 replay orratioadditionto133.

CURRENT147 actualfeature reuse-compaction-payload-147 onexact131+144. Compaction
only checkedlogicalpayload<=1MiB, andchecked sumACTUAL Vecbytecapacities<=1MiB;
oncapacityoverflow/overbudget dropretention/useoriginalstream. Vector descriptors
andoriginalsingleCRCblocktemporary additional. Same blockbytes alreadyformed
for CRC retainedthenconsumed duringsegmentwrite, avoidssecond scalarLE encoding.
Droppedbeforeexplicitflush/sync. Ordinaryappend/largercompactionoriginal64KiB
stream; same original64KiB BufWriter/syncs/catalogrename/receipt/ACK/cutsequence.
Reader/inputCRC/sums/phase/merge/sortedness/index/format unchanged; no unsafe/
dependency/publicAPI/globalsettingchange/rejected134/136/138/140code. Sourceoutside
publish byteexact144. Supported016 main/source/tests/deps stayexact.

Declaredpolicy BEFOREimplementation; performanceUNMEASURED/0timingcases.
Sourceatwork/perf-147/candidate andUNSAVED; neverremove beforeprivatepublication.
Freshnewtest totals2/4095/4096/4097/43690/43691 via2namedbatches, SQLreference/
extremes/emptyfilters/pins/reclaim/originalreceipt+mismatch/coldreopen. Newbyte
buffers needallfresh correctness/fault/debug/release/lints/independent store
payload/index/CRC/digest/generation/wire/recovery, noautomaticadoption.

work/build-payload-147.log/actualcontroller/step-proofs/build-proof/build-failure
FIRST. build_payload_147.py serial4suites expected87each348/twostrictlints/
original durable driver, guarded beforeeachjob. Ownedexec47871 ifavailable.
No passedjobrerun: onguardhold preserve allrecords andcontinueonlyunstarted.
Codechangebuilds areLOCAL/UNTIMED, expected<1.8GBregenerablecap. Nofuture148
qualificationcohort declared. Beforetimers strictreset/actualsupervisors/global
builds inclJavaMavenGradle/120continuousquiet afterprep/freezes/percaseguards.

Useactualstages asmeasuredbasis, notexclusiveCPU/physicaldisk attribution.
Rustprimary BufWriter/Write docsread: preserveexplicitflush/result checks;
current APIsstable andtoolchainunchanged. Future148+ complete216 balancedsameD
supported016A/B versusJOINT131+144+147 C(notisolated147), full/bothhalf144AA/
144guards/6clusteredwhole<=.95-prepare<=.90goals, AA[.90,1.10]/guard<=1.10,
median/tail/setupp95=max/allstalls. ALLinput/readCRC/phase/index/write/flush/
synccharged; originalrelease324Native/252service/42goals/153AA/171guards plus
correctness/retry/recovery/sustainedservice unchanged. No selectedretiming/
outlierdiscard/gateloosening/component-onlyrelease/universalwins/ETA.

FIRSTfreshactualreset/ALLnewsupervisors includingrelativedeployment_soak.
AnyTIMED/cohortactiveORwaiting blocksGit/hash/copy/build/package/cleanup/
independentaudits/otherbenchmarks. Duringactivecohort useitsfreshownedguard/
actualsessionrecords, noextra rootCIM duringnative. Outsidecohort usefixed
metadataentry, noinlineprocesscommandwithPythonfilenames. Neverstop/message
unrelatedproject/app,forcequit/rearmexpiredreset/resumeabandonedchat/oldtasks/
oldloops/checker. SHORTprivateoutcomes/failures/usefulsource/freshbytes then
nativeexactno-reparsecleanup; no rawmultiGBbundles/history/ref/tag/release
deletion. Keepkits/unsavedwork/uniqueunverifiedexports. Alltests/buildsLOCAL,
Actions$0Stopusage/evidence skipCI; sameACTIVE30minheartbeat/name/target/prefs.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
proof={'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'147_implemented_prerequisites_running':True,'timed_cases_declared':0,'release017_qualified':False}
(R/'payload147-started-next-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof))
