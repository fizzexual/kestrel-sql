from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
c=load(R/'phase146-storage-cleanup-proof.json');p=load(R/'phase146-publication-proof.json');v=load(R/'phase146-remote-save-proof.json')
assert c['completed146_stores_closed'] and not (R/'perf-146').exists()
assert not (R/'phase146-closed-next-proof.json').exists()
old=N.read_bytes();expected=load(R/'phase146-running-next-proof.json')['new_sha256'];assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###146 complete / unqualified / private verified / closed — {stamp}

All216 native/controller/two monitoringworkers/two mainauditor waits/exits0.
Actualcontroller ended21:48:07Z. Fullindependent7077888 exactrows169869312CRCbytes,
allindexes/head33/originalreceipt digests2304 independentlydeclaredgenerations.
All originalrecorded workerprobes vsALL216native lifetimes/frozenbytes/order
pass. Every sample/stallonce, noselectedretiming/gateloosening. Baseline154/
candidate344 tests/twolints/28stores/wire/recovery REUSED, noRustjob.

COMPONENTUNQUALIFIED {p['identity_failures']}/144AA,{p['guard_failures']}/144guards,
{p['goal_failures']}/6goals fail. Additionalrootmetadataquery output21:17:05.309952Z,
wall1.3879987s/exactstartunlogged, conservative21:16:46.451..21:17:07 envelope
intersects native lives; actualoverlap neitherproven nordisproved. Additional
auditoractual0 preservedthislimitation; doNOTclaimALLmetadataqueriesoutside.
Noheavy/timedaction camefromquery. FutureACTIVEcohort FIRST usesitsfreshowned
guard responses/actualowned-sessionstatus, noextra rootCIM duringNative lives.
Outsideactivecohort orprovablysafebetween-casewait only fixedmetadataentry.
Do notattributeexclusivephysicalcause orqualifygains fromthismonitoringgap.

Private main{p['private_main']} saves SHORT COMPACTION_EXTREMA_COMPARE_146.md/
every failed check/actualsources/independentproofs/manualquerylimitation.
Freshremote{len(v['files'])}files{sum(x['bytes'] for x in v['files'])}bytes exact.
Nativeexactperf146removed{c['logical_bytes_removed']}bytes{c['files_removed']}files.
Usefulsupport/131/144/recoverykits/oldprivatehistory/tags/releases retained.
Supported016corebyteexact/144notadopted/017UNRELEASED. No146 rerun/resume.

No147job declaredhere. Nextunused147+ afterFRESHactualreset/ALLnewsupervisors/
globalbuildchecks (includingrelativedeployment_soak/directJavaMavenGradle).
Pursue ACTUAL justifiedmeasured codeimprovement fromremaining prepare/CRC/
serialization/merge ordocumentedservice costs, not onlycalibration/reports.
Inspect complete146 distributions/stages inactual savedoutcome/proofs/source
before choosinghypothesis. Research primarydocsforunfamiliartechniques.
Newenginebytes requirefresh normal/faultdebug/release correctness/lints/full
independentpayload-index-CRC-wire-originalreceipt/generation/recovery; identical
passed prerequisites explicitlyREUSED, neverrebuildforharness-onlyrepair.

Futurecomplete balanced sameD supportedbaseline/full-bothhalfAA/median-tail-
setupguards chargedALLinput/readCRC/phase/index/write/flush/sync. Strict120quiet
afterprep/freezes/percasebefore-afterguards/ownedmetadataidle duringnative.
Missingbirth/reset/possibleoverlap rejectsWHOLEprefix. Allsamples/stalls once,
no selectedretiming/outlierdiscard/metricselection/gateloosening. Finishcomplete
cohorts/actualexits/allindependentaudits orpreserveevery failed/unstartedprefix.
Originalrelease324Native/252service/42goals/153AA/171guards pluscorrectness/
retry/recovery/sustainedservice remain. No componentonlyadoption/release,
universalwins/inventedETA orunsupportedupgrade. Previouslimitedgains/exclusions/
calibrationfailures/rejectedvariants retained, nevercombine separatecohort ratios.

AnyTIMED/cohort activeORwaiting blocksGit/hash/copy/build/package/cleanup/
independentaudits/otherbenchmarks. Actualowned session/smalllog/freshguardpolls
only; noextra rootCIM duringnative. Neverstop/messageunrelatedproject/app,
forcequit/rearmexpiredreset/resumeabandonedchat/oldmigration/loops/checker.
SHORTprivateoutcomes/failures/usefulsource/freshbytes thennativeabsolute scoped
no-reparsecleanup. No rawmultiGBbundles/history/ref/tag/release deletion; useful
kits/unsavedwork/uniqueunverifiedexports retained. Allbuilds/testsLOCAL,
Actions$0Stopusage/evidence skipCI; sameACTIVE30minheartbeat/name/target/prefs.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
proof={'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,
    '146_closed':True,'component_qualified':False,'manual_probe_boundary_unproven':p['manual_probe_boundary_unproven'],'release017_qualified':False}
(R/'phase146-closed-next-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof))
