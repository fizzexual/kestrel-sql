from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-146';N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(R/'phase146-preparation-actual-exits.json')['preparation_actual_exit']==0
assert load(R/'phase146-preflight-actual-exits.json')['preflight_actual_exit']==0
assert load(W/'smoke-proof.json')['complete'] and len(load(W/'smoke-proof.json')['checks'])==6
assert not (W/'component-cases.jsonl').exists() and not (R/'phase146-preflight-ready-next-proof.json').exists()
old=N.read_bytes();expected=load(R/'phase145-closed-next-proof.json')['new_sha256']
assert hashlib.sha256(old).hexdigest()==expected
p=load(W/'policy.json');assert len(p['cases'])==216 and p['component_checks']=={'AA':144,'guards':144,'clustered_goals':6}
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###146 fresh complete comparison prepared/preflight passed — {stamp}

145 CLOSED/private9b1deb1dad105936a72007a563fbf19e89f60ad8/60files240837bytes
fresh exactverified;100190556bytes653files removed.118correct/98UNSTARTED,
possibleoverlapperformance-rejected, everyfailure/source/prefix/lifecycle proof
saved. No145 replay/resume/selectedretiming. Supported016 exact,017unreleased.

CURRENT146 NEW216 completecases against same exact binaries: supported016 A/B
SH2392cb6e53c0736a2d3bb67fd89369016848e6e12010989369b46a7a4ec2c1c7 versus
JOINT131+144 C SH560e5868f61a3e5dc2d26aa2f30318206537af85af1eb82eeb6f861e550e711f.
PolicySH{hashlib.sha256((W/'policy.json').read_bytes()).hexdigest()}.
Same fixedRNG20261011/12balancedrounds/sixshapes/all6permutations perhalf,
32x1024rows/3cols,144AA/144guards/6clusteredwhole<=.95/preparation<=.90 goals.
AA[.90,1.10]/guard<=1.10/full-bothhalf/median-whole-prepare-write-sync/
write+sync andwhole/setupp95=max kept unchanged. ALLinput/readCRC/phase/index/
write/flush/synccharged; comparison doesnotisolate144vs131 orrelease/service.
Baseline154/candidate344 tests/twolints/28stores/wire/recovery REUSED, no Rustjob.
SixFRESHexcludedpreflights196608rows/4718592CRCbytes/declaredreceipt generations,
ownedidlebusy-clear/five birthclassifications/workeractual0 pass. Neverrerun
passed preparation/preflight or144prerequisites. No146timingyet.

Launchphase146appends runningproof fromTHISreadyproof beforefrozenbytes/120
continuous observedquiet/percasebefore-afterguards/ownedCPU8. Persistentowned
metadataworkeridleonstdin duringEVERYnative lifetime. Beforebusy startsNOtimer;
afterbusy waitONLYeverybirth>=nativeexit+100ms AND>=postprobestart. Missingbirth/
resetactivity/possibleoverlap rejectsENTIREprefix. Everycase/stallonce;no selected
retiming/outlierdiscard/metricselection/gateloosening. WaitsnotDBscheduling.
FinishTHIScohort/actualexits thenbothfullindependentaudits afterfreshquiet: all
payload/index/CRC/originaldigest+run+1generation/frozenbyte/order/full-halfmetrics,
everyprobevsEVERYnativelife. Onfailure preserveALLattempted/failed/unstarted.
Source/resultsUNSAVED untilSHORTprivatebyteverified publication; noearlycleanup.
Nextunused147+ ONLYafter146closure, neverrepeatclosed145/oldertrials.

Originalrelease324Native/252service/42goals/153AA/171guards pluscorrectness/
retry/recovery/sustainedservice unchanged. No componentonlyadoption/release/
universalwin/ETA. FIRSTactualreset/ALLnewsupervisors includingrelativedeployment
soak/globalbuilds inclJavaMavenGradle. Anytimed/cohortactiveORwaiting blocksGit/
hash/copy/build/package/cleanup/independentaudit/otherbenchmarks. Fixedmetadata
only, noinlineprocessstatuswithPythonfilenames. Neverstop/messageunrelatedjob,
forcequit/rearmexpiredreset/resumeabandonedchat/oldmigration/loops/checker.
SHORTprivateoutcomes/failures/source/freshbytes thennativeabsolute scoped
no-reparsecleanup; no multiGBbundles/history/ref/tag/release deletion. Useful
kits/unsavedsource/uniqueunverifiedexports retained. Localtests/builds only,
Actions$0Stopusage/evidence skipCI; sameACTIVE30minheartbeat/name/target/prefs.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'phase146-preflight-ready-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'146_prepared_preflight_passed':True,'no_timed_cases_yet':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print('146 preflight-ready checkpoint appended; no timing started')
