"""Checkpoint prepared145 and its single metadata-only preflight waiter."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,shutil
R=Path('D:/Codex/Kestrel/work');W=R/'perf-145';N=Path('D:/Codex/KESTREL_NEXT.md')
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert load(R/'phase145-preparation-actual-exits.json')['preparation_actual_exit']==0
assert load(W/'preparation-proof.json')['complete'] and load(W/'preflight-exit-journal-preparation.json')['before_any_preflight_or_timed_case']
assert not (W/'smoke-fixtures').exists() and not (R/'phase145-preflight-actual-exits.json').exists()
prior=load(R/'phase145-preparation-pending-next-proof.json');before=N.read_bytes();assert hashlib.sha256(before).hexdigest()==prior['new_sha256']
assert not (R/'phase145-preflight-ready-next-proof.json').exists()
append=R/'append_phase145_declared.py';old=append.read_text(encoding='utf-8');new=old.replace("load(R/'phase145-preparation-pending-next-proof.json')", "load(R/'phase145-preflight-ready-next-proof.json')")
assert new!=old;ast.parse(new,filename=append.name);append.write_text(new,encoding='utf-8',newline='\n');shutil.copy2(append,W/append.name)
stamp=datetime.now(timezone.utc).isoformat()
note=f'''
## Comparison145 prepared; excluded preflight waiting ({stamp})

Actual derivation/preparation0 completed; policy is declared and complete216
balanced sameD supported016 identicalA/B versus JOINT131+144C. Cases/order/
inputs/binaries/controls/goals are fixed, baseline154/candidate344/two lints/
all28 stores/wire/recovery explicitly REUSED, zero newRustbuilds/tests.
Source/binaries/policy under work/perf-145 remain UNSAVED. Source144 closed
private01a16b6/94files438016B exactverified/988035645B6815files removed; never
replay closed144 engineering/save/cleanup.145 performance UNEVALUATED/017
UNRELEASED; no qualified case, preflight/native job or cohort has started.

Before first preflight, complete_phase145_preflight_logging.py preserved the
original smoke source asbase64 and added actual native identity/start/end/exit
journaling BEFORE validation/afterguard. No policy/order/input/binary/numerical
gate/safety protocol/timer changed. Source R/W copies match before freeze.
This avoids losing attempted-native proofs if a later build guard holds.

CURRENT single one-off waiter work/wait_preflight_phase145.ps1 is launching.
Inspect actual fresh owned pwsh identity and phase145-preflight-wait metadata/
actual-exit files and phase145-preflight-actual-exits.json FIRST; do not launch
duplicate waiters/preflights. It checks reset/tasks/all supervisors/relative
deployment_soak and visible global builds with metadata only while blocked,
then runs existing launch_preflight_phase145.ps1 once. It performs NO probes
while excluded native preflights run. Only a guard racing before Python/native
creation may recheck; any native prefix/actual preflight exit stops the waiter
and must be inspected, never repeated. Deadline2h/10s polling, no apps stopped/
messages/global settings changed, no new automation/checker created.

Require ALL6 excluded ordered/clustered A/B/C independent payload/index/CRC/
originalreceipt/generation preflights196608rows/4718592CRCbytes, owned dummy
busy-clear/five birth classifications and metadataworker actual0. If failure,
preserve all actual native exit journal/result/stores/failure/source, continue
only unstarted cases after fresh quiet; no engine/Rust rebuild or native retime.
After actualpreflight0, update existing heartbeat state BEFORE timedlaunch;
launch_phase_compare_145.ps1 appends phase145-running-next-proof.json chained
from THIS ready proof. Never duplicate append after guard hold/controller
notcreated; use a separate verified continuation retaining policy/source/order.

Then finish complete216 fixed balanced12round/sixshape/32x1024rows/3cols,
all6perms perhalf/RNG20261011;144AA/144guards full/bothhalf medwhole/prepare/
write/sync/catalog/write+sync andwhole/setup p95=max with12/full or6/half.
Sixclusteredwhole<=.95/prepare<=.90, AA[.90,1.10]/guard<=1.10 unchanged. ALL
input/readCRC/phase/index/write/flush/sync charged; every stall once, no metric
selection/outlier discard/selected retime/gate loosening.120 continuousclear
afterprep/freezes, strict before/afterEVERYcase/reset/ALLsupervisor/global
guards, ownedCPU8/metadata idle onstdin duringNative. Onlypredeclared proven
outside-lifetime waits; missingbirth/reset/possibleoverlap rejects fullprefix.
Both complete independent payload/index/CRC/originalreceipt digest+generation/
everyprobe vsEVERYnative/frozen/order/full+halfmetrics auditors and actual
controller/native/worker/auditor waits/exits required. No other heavywork while
timed or declaredtimedcohort activeORwaiting. Originalrelease324Native/252service/
42goals/153AA/171guards pluscorrectness/retry/recovery/sustained unchanged.
Components do not qualify release; no universalwin/ETA/unsupportedupgrade.

No inline status command mentioning Python filenames. Neverstop/message
unrelated project/app, forcequit/rearmexpiredreset/resumeabandonedchat orold
loop/migration/checker. Localbuilds/tests/Actions$0Stopusage/evidence skipCI.
Short private outcomes/everyfailure/usefulsource, fresh exactremotebytes then
native literalabsolute scoped no-reparse completedcleanup; no rawmultiGBbundle/
privatehistory/ref/tag/releasedeletion. Preserve usefulkits/unsavedwork/unique
unverified exports. SameACTIVE30minheartbeat/name/target/prefs, no duplicate.
'''
with N.open('ab') as f:f.write(note.encode())
after=N.read_bytes();assert after==before+note.encode()
proof={'utc':stamp,'old_sha256':prior['new_sha256'],'new_sha256':hashlib.sha256(after).hexdigest(),'old_history_prefix_exact':True,'145_preparation_complete':True,'145_preflight_waiter_ready':True,'no145_native_or_qualified_case_started':True,'policy_sha256':hashlib.sha256((W/'policy.json').read_bytes()).hexdigest(),'checkpoint_helper_dependency_only_updated_before_freeze':True}
(R/'phase145-preflight-ready-next-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(proof),flush=True)
