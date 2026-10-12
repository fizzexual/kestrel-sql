from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-143';N=Path('D:/Codex/KESTREL_NEXT.md')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'build-proof.json')['complete'] and load(W/'build-proof.json')['fresh_kernel_tests']==6
assert not (W/'component-cases.jsonl').exists()
prior=load(R/'profile142-closed-next-proof.json');old=N.read_bytes();assert hashlib.sha256(old).hexdigest()==prior['new_sha256']
now=datetime.now(timezone.utc).isoformat()
note=f'''\n## Index diagnostic143 implemented / build completed ({now})

142 isclosedfailed/0timings, private9462f4adc6600a01a8ceb5ad200e07b36b798e04,
51files324810bytesfreshverified, exact213570904bytes768filesremoved.
Fresh143 fixes ONLYdiagnostic output: typedJSONtext supports exactwidei128,
explicitpositive/negative4096/4097-prefix regressiontest. Actualkernel/index/
timeroperationsremainbyteexact142; allsupportedlibrarybytesexact016.
Sixfreshexampletests(3debug/3release),one strictlint/artifact actualexits0;
noenginechange/tests orspeedresult. BinarySHA{load(W/'build-proof.json')['binary_sha256']}.
FreshpolicydeclaredBEFOREcode/timer:216balancedcases12rounds6shapes,all6perms
perhalf, exactA/Blegacy vsCblockextremaforglobals;16fullbuildstimed,18AA/18guards/
18index-onlygoalsfull/bothhalves. ExcludesallArchive input/readCRC/merge/sort/
serde/writes/flush/sync/receipt/ACK/service; separatestageprofileoutsideprimary
timerwithclockoverhead. Need6freshindependentexcludedpreflights thenactual
completecohort/everyindex/inputSHA/CRC/i128/everyprobevsEVERYnativelifetime/
frozenbytes/order/metrics/exits. Neverrerunpassedbuilds. No143timingsyet.
CheckLATESTandliveidentities/actualwork first; nextuncompleted143step only.
Originalreleasegatesunchanged,016supportedexact/017unreleased.
'''
after=old+note.encode();N.write_bytes(after);assert N.read_bytes()==after and after[:len(old)]==old
out={'utc':now,'old_sha256':prior['new_sha256'],'new_sha256':hashlib.sha256(after).hexdigest(),'old_history_prefix_exact':True,'143_actual_build_complete':True,'timed_cases_started':0}
(R/'profile143-started-next-proof.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(out),flush=True)
