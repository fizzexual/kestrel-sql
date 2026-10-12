"""Record closed144 and the unstarted, guard-held145 preparation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
closed=load(R/'extrema144-closed-next-proof.json');assert closed['storage_cleanup_complete']
assert not (R/'perf-145').exists() and not (R/'prepare_phase_compare_145.py').exists()
assert not (R/'phase145-preparation-pending-next-proof.json').exists()
global_hold=load(R/'phase145-preparation-global.log');assert not global_hold['no_visible_build_jobs']
before=N.read_bytes();assert hashlib.sha256(before).hexdigest()==closed['new_sha256']
stamp=datetime.now(timezone.utc).isoformat()
note=f'''
## 144 closed;145 preparation guarded before creation ({stamp})

144 private source/outcome save actually completed0 at
01a16b636a2b64ab3bb1cb0846f37a60561d89f2.94files438016bytes freshly exact
verified. Native exactperf144 cleanup completed0,988035645bytes/6815files
removed; small kit144 candidate+three recovery artifacts retained.344tests/
two strict lints/all28 independent stores/six original016 exact wire pairs/
14 recovery cases56commands complete. No144 native case/build/audit repeats.
All144 publication encoding/partial-summary failures and failed bytes preserved
privately; finalv3 fixed only save plumbing. Source016/main core exact andclean.
144 speed UNMEASURED/017 UNRELEASED. Prior closed proofSHA
{closed['new_sha256']} remains exact older prefix.

NEXT145 helpers written, but no derivation/preparation/preflight/controller has
run. work/prepare_extrema_compare145.ps1 actually exited1 with waitcomplete
after global build guard, BEFORE running derive_extrema_compare_145.py. No
perf145 directory or prepare_phase_compare_145.py exists, zero native/Rust jobs,
zero declared policy/timings/preflights. Exact held launcher/global metadata
remain local. This is a safety hold, not an engine or performance failure.

When fresh actual reset/ALL supervisor/global guards are clear, run the existing
prepare_extrema_compare145.ps1 once; only its safety prelude previously ran.
derive_extrema_compare_145.py adapts validated139 controllers, preserves exact
input generator/order/numerical gates/protocol, replaces exact131 baseline with
supported016 kit122 baseline.exe and candidate138 with verified kit144. It must
predeclare complete216 balanced12round/sixshape/all6 permutations perhalf
before binary copy/smoke. Reuse baseline154/candidate344 tests/two lints/wire/
recovery, no Rust builds. Follow actual preparation exit, then
launch_preflight_phase145.ps1 on6 fresh excluded ordered/clustered A/B/C stores,
independent196608rows/4718592CRCbytes/owned dummy/five birth classifications.
Never repeat completed prefix on a hold/failure; preserve exact attempt/source.

Only AFTER actualpreflight0/proofs, launch_phase_compare_145.ps1 appends its
running checkpoint chained from THIS pending proof beforefreeze/120quiet.
Whole/setup p95 and six median families keep full/both-half144AA/144guards;
sixclusteredwhole<=.95/prepare<=.90goals, AA[.90,1.10]/guard<=1.10 unchanged.
Supported016 identical A/B versus JOINT131+144C, notisolated144effect. Charge
ALL input/readCRC/phase/index/write/flush/sync; allstalls once/no selectedretime.
Originalrelease324Native/252service/42goals/153AA/171guards pluscorrectness/
retry/recovery/sustainedservice unchanged. Component cannot qualify release.
Strict before/afterEVERYcase/reset/supervisor/global guards/120continuousquiet
afterprep/freezes; ownedCPU8/metadata idle onstdin duringNative. Onlypredeclared
proven outside-lifetime waits; possibleoverlap/missingbirth/resetrejectprefix.
Two complete payload/index/CRC/receipt/generation/lifecycle/frozen/order/metric
auditors and actual waits/exits required. Finish cohort/audits before newwork.

FIRST actualreset and ALLnew jobs, including relativedeployment_soak commands.
Any timed/declaredtimedcohort activeORwaiting blocksGit/hash/copy/build/package/
cleanup/independentaudits/otherbenchmarks; metadata/small ownedlogs only. Never
inline status with Python filenames. Neverstop/message anotherproject/app,
forcequit/rearmreset/resumeabandonedchat/oldmigration/oldloop/checker. SameACTIVE
30minheartbeat/name/target/prefs; oldloops/checker paused/migrationdisabled.
Localtests/builds underActions$0Stopusage/evidence skipCI. Short private
outcomes/everyfailure/usefulsource, freshremotebytes thennative literal absolute
scoped no-reparse completedcleanup. No newmultiGBbundles/history/ref/tag/release
deletion; retain usefulkits/unsavedwork/unique unverified exports. Advance only
actual145 preparation; no replay of closed144/143/other experiments.
'''
with N.open('ab') as f:f.write(note.encode())
after=N.read_bytes();assert after==before+note.encode()
proof={'utc':stamp,'old_sha256':closed['new_sha256'],'new_sha256':hashlib.sha256(after).hexdigest(),'old_history_prefix_exact':True,'145_preparation_actual_guard_exit':1,'actual_wait_completed':True,'no145_sources_derived_or_directory_created':True,'no145_native_or_Rust_jobs':True,'no145_policy_or_timed_cases':True,'bounded_global_hold':global_hold}
(R/'phase145-preparation-pending-next-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in proof.items() if k!='bounded_global_hold'}),flush=True)
