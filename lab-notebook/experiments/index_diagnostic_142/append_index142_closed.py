from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
proof=load(R/'profile142-remote-save-proof.json');clean=load(R/'profile142-storage-cleanup-proof.json');prior=load(R/'profile142-started-next-proof.json')
assert proof['complete'] and proof['fresh_remote_text_and_source_byte_exact'] and clean['complete']
old=N.read_bytes();assert hashlib.sha256(old).hexdigest()==prior['new_sha256']
stamp=datetime.now(timezone.utc).isoformat()
note=f'''\n## Index diagnostic142 CLOSED / output failure ({stamp})

142 has NO timing cohort: all216 qualification cases and18AA/18guards/18goals
UNSTARTED or UNEVALUATED. Four fresh kernel-only tests/one lint/artifact actual0,
all supported library src/tests/dependencies exact016; no engine change/gain.
Five excluded outputs independently exact163840rows/3932160CRCbytes. First
preflight actual1 at AFTER guard afternewnodebuild; fouridentities saved, late
exit0/checks observed butidentity unsaved/disclosed. Passedowned dummy/protocol
reused. v2 reusedallfive withoutretiming,120.64quiet thenONLYunstartedextreme
actual101: json! Value conversion numberoutofrange forwidei128 prefixes. Both
internalindexassertions passed, noJSON forindependentaudit. Controller1/worker0,
noforcedkills; neitherfailureisArchive regressionorengine speed evidence.
Sandbox derivation denialbeforeworkercreation exactapprovedretry0; NEXTappend
succeededthenunsupportedPSByRef-likeverificationfailed, exactoldprefix/existing
append recoveredcryptographicallywithoutrewrite. Allfailures/actualsources saved.
Private main{proof['head']}, {len(proof['files'])}files/{sum(f['bytes'] for f in proof['files'])}bytes
freshremote exactverified. Native exactperf142 removed{clean['logical_bytes_removed']}bytes/
{clean['files_removed']}files. No142jobrunning, no rerun/overwrite142.

Nextunused143-or-later: fix ONLYdiagnostic output via typed serde_json text
serialization supportingi128, add explicitwide-prefixoutput regressiontest.
Library/kernelindex/timeroperations remainexact; declarefreshbalanced216
index-onlycomparison and full/bothhalf18AA/18guards/18kernelgoals withscope
exclusions, everyinputSHA/fullindex/i128/CRC independentlychecked. Completeall
actualcases/exits/everyprobevseverylifetimes/frozenmetrics beforecodeadoption.
Then chooseactualenginechangefrommeasuredpreparationcost, notmerecalibration.
Originalrelease324Native/252service/42goals/153AA/171guards+correctness/retry/
recovery/sustainedunchanged. Supported016byteexact,017unreleased.

FIRSTactualreset/ALLsupervisors/newerjobs inclrelative deploymentsoakDargs,
nohistoricalPID/clock/gapcompletion. Neverstop/messageanotherproject/app,
forcequit/stopfiles/rearmreset. WhileANYtimed/declaredcohortactiveORwaiting,
holdGit/hash/copy/build/package/cleanup/independentaudit/otherbenchmarks.
Pollownsession/smalllogs; no inlinePythonfilename statuswrappers. Freshstrict
reset/task/global guards inclJavaMaven/Gradle,120continuouslyobservedquietafter
prep/freezes; resetonactivity. Per-casebefore/after strictguards; ownmetadata
idlewhileactualnative. Outside-lifetimewaitsONLYpredeclared: beforebusyNOtimer;
afteronlyEVERYbirth>=nativeexit+100ms AND>=postprobe. Missingtime/reset/possible
overlaprejectwholeprefix; preserveallattempted/failed/unstarted, noselectedretime.
SHORTprivatefailure/outcomes/usefulsource,freshremotebytes thenexactnative
absolute literalno-reparse completedcleanup. No multiGBbundles/oldprivate
history/ref/tag/releasedeletes; retainusefulkits/unsaved/uniquebackup-unverified
exports. Localbuilds/tests,Actions$0Stopusage,skipCIevidence. Resetwait-expired
untouched; oldmigrationdisabled/oldloop+checkerpaused; keepthisACTIVE30min
samechatheartbeat/name/prefs, noduplicate/abandonedresume. Advanceactualjobs.
'''
after=old+note.encode();N.write_bytes(after);assert N.read_bytes()==after and after[:len(old)]==old
out={'utc':stamp,'old_sha256':prior['new_sha256'],'new_sha256':hashlib.sha256(after).hexdigest(),'old_history_prefix_exact':True,'142_closed':True,'release017_qualified':False}
(R/'profile142-closed-next-proof.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(out),flush=True)
