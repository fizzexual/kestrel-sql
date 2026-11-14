from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
c=load(R/'phase145-storage-cleanup-proof.json');p=load(R/'phase145-publication-proof.json');v=load(R/'phase145-remote-save-proof.json')
assert c['completed145_prefix_stores_closed'] and not (R/'perf-145').exists()
old=N.read_bytes();expected=load(R/'phase145-running-next-proof.json')['new_sha256']
assert hashlib.sha256(old).hexdigest()==expected
assert not (R/'phase145-closed-next-proof.json').exists()
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###145 rejected full prefix / independent audit / private verified / closed — {stamp}

All118 attempted native cases actualexit0; controller89996 actualwait/exit1
at20:40:03Z aftercase117.98 indices118..215UNSTARTED. Both metadataworkers
actualexit0/noforcedkill. Post117 found Python78572 born20:39:59.559031Z,
before last native began20:40:00.351394Z/exited20:40:00.661959Z. Actionunknown,
possibleoverlap rejects ENTIRE performance prefix. Not an engine correctness
regression or speed result. No resuming/retiming145/fullcontrol selection.

Fresh128.75seconds observedquiet/zerobusyresets, both independentauditor actual
waits/exits0:3866624 exactrows/92798976CRCbytes/fullindexes/originalreceipt
digests and1344 independentlydeclared run+1 generations/head33/onesegment.
All343 probes vs124 native lifetimes42532pairs pass;4 earlier permittedwaits
outside lifetimes. One gateprobe before controller/native; manualmetadata
probe20:17:41 conservatively enveloped20:16:45..20:18:00 inside before17wait,
exactmanualstartunrecorded/disclosed. Frozenbytes/orderexact, allstallsonce.
Full/bothhalf144AA/144guards/6goals UNEVALUATED, overallspeedUNQUALIFIED.
Baseline154/candidate344/twolints/wire/recovery explicitlyREUSED, noRustjob.
Sixexcludedpreflights196608rows/4718592CRCbytes passed and notrerun.
Sandbox helpercreationdenial and dependentmissing-script launcherfailure
occurredBEFORE quietwait/auditors; preserved/retried exacthostpreparation.
No145 case orpassed144 prerequisite repeated.

Private main{p['private_main']} saves SHORT COMPACTION_PREFIX_145.md/actual
source/everyfailure/boundedproofs. Freshremote{len(v['files'])}files/
{sum(f['bytes'] for f in v['files'])}bytes exact; nativeexactperf145 cleanup
removed{c['logical_bytes_removed']}bytes/{c['files_removed']}files. Smalluseful
144/131/support/recoverykits andoldprivatehistory/tags/releases retained.
Supported016 corebyteexact,144notadopted,017UNRELEASED.

No146 job/cohort declared here. Nextunused146+ ONLY. Choose concrete measured
codework or complete fresh balanced supported016 comparison of exact144.
Never merely repeat145/closed trials or loosen complete full/bothhalf/median/
tail/setup gates. Strict reset/actualsupervisor/globalguards and120continuous
quiet, chargedinput/readCRC/phase/index/write/flush/sync; no heavy concurrent
work orselectedretiming. Possibleoverlap rejectsfullprefix. Independently
audit every payload/index/CRC/receipt/generation/frozenbyte/probe/native life
andactualexits. Original release324Native/252service/42goals/153AA/171guards
pluscorrectness/retry/recovery/sustainedservice unchanged. No componentonly
release/universalwins/inventedETA. Continue actualengineering, not reports.

FIRST actualreset/ALLnew supervisors includingrelativedeployment_soak. Any
timed/declaredcohort activeORwaiting blocksGit/hash/copy/build/package/cleanup/
independentaudits/otherbenchmarks. Fixedmetadataonly entries; noPythonfilename
inlineprocessstatuswrappers. Neverstop/message unrelatedproject/app,forcequit,
rearmexpiredreset/resumeabandonedchat/oldtasks/loop/checker. Alltests/buildsLOCAL
underActions$0Stopusage, evidence skipCI. SHORTprivateoutcomes/source, fresh
remotebytes thennativeabsolute scopedno-reparse cleanup; no rawmultiGBbundles
oroldremotehistory/ref/tag/release deletion. Usefulkits/unsavedwork retained.
SameACTIVE30minheartbeat/name/target/prefs; no duplicate.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
proof={'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,
    '145_closed':True,'completed_cases':118,'unstarted_cases':98,'no_speed_qualification':True}
(R/'phase145-closed-next-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(proof))
