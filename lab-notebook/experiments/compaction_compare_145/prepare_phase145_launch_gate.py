"""One metadata-only launch gate; never repeat a controller or checkpoint append."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,shutil
R=Path('D:/Codex/Kestrel/work');W=R/'perf-145';N=Path('D:/Codex/KESTREL_NEXT.md');load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
assert load(R/'phase145-preflight-actual-exits.json')['preflight_actual_exit']==0
assert load(R/'phase145-preflight-wait-actual-exits.json')['waiter_actual_exit']==0
assert load(W/'smoke-proof.json')['complete'] and len(load(W/'smoke-proof.json')['checks'])==6
assert not (R/'phase145-actual-exits.json').exists() and not (R/'phase145-running-next-proof.json').exists()
assert not (W/'component-cases.jsonl').exists() and not (W/'fixtures').exists()
old=(R/'wait_preflight_phase145.ps1').read_text(encoding='utf-8')
prefix=old[:old.index('try {')]
prefix=prefix.replace('phase145-preflight-wait','phase145-cohort-launch-wait').replace("'phase145-preflight-actual-exits.json'", "'phase145-actual-exits.json'").replace('perf-145\\smoke-fixtures','perf-145\\fixtures').replace('Preflight already attempted; inspect its prefix','Controller already attempted; inspect its prefix').replace('Preflight fixture already exists','Controller fixture already exists').replace('metadata_only_until_excluded_preflight','metadata_only_until_controller_launch')
body=old[old.index('try {'):old.index('        if($taskClear){\n            $taskAttempts++')]
body=body.replace('phase145-preflight-wait-metadata','phase145-cohort-launch-wait-metadata')
suffix="""        if($taskClear){
            $taskAttempts++
            & 'D:\\Codex\\Migration-20261007\\helper-runtime\\powershell\\pwsh.exe' -NoProfile -File 'D:\\Codex\\Kestrel\\work\\launch_phase_compare_145.ps1'
            $taskChildExit=$LASTEXITCODE
            # No gate probes while the qualified controller/native children run.
            if(Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-actual-exits.json')){
                $taskActual=Get-Content -LiteralPath (Join-Path $taskRoot 'phase145-actual-exits.json') -Raw | ConvertFrom-Json
                if(-not $taskActual.actual_controller_wait_completed -or $taskActual.cohort_actual_exit -ne $taskChildExit){throw 'Actual controller wait/exit mismatch'}
                @{utc=(Get-Date).ToUniversalTime().ToString('o');gate_actual_exit=$taskChildExit;actual_wait_completed=$true;controller_launch_attempts=$taskAttempts;metadata_polls=$taskPolls;controller_attempted=$true;no_native_case_or_checkpoint_repeated=$true} | ConvertTo-Json | Set-Content -LiteralPath $taskProofPath -Encoding utf8
                exit $taskChildExit
            }
            throw 'Launcher held before controller creation; preserve existing append/guard and use a separate verified continuation, never retry here'
        }
        Start-Sleep -Seconds 10
    }
    throw 'Metadata launch wait deadline; no controller started'
} catch {
    @{utc=(Get-Date).ToUniversalTime().ToString('o');gate_actual_exit=1;actual_wait_completed=$true;controller_launch_attempts=$taskAttempts;metadata_polls=$taskPolls;bounded_error=$_.Exception.Message;controller_actual_exit_proof_present=(Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-actual-exits.json'));checkpoint_append_present=(Test-Path -LiteralPath (Join-Path $taskRoot 'phase145-running-next-proof.json'));no_case_or_checkpoint_repeated=$true} | ConvertTo-Json | Set-Content -LiteralPath $taskProofPath -Encoding utf8
    throw
}
"""
target=R/'wait_launch_phase145.ps1';assert not target.exists();target.write_text(prefix+body+suffix,encoding='utf-8',newline='\n')
prior=load(R/'phase145-preflight-ready-next-proof.json');before=N.read_bytes();assert hashlib.sha256(before).hexdigest()==prior['new_sha256']
append=R/'append_phase145_declared.py';text=append.read_text(encoding='utf-8');new=text.replace("load(R/'phase145-preflight-ready-next-proof.json')", "load(R/'phase145-launch-gate-next-proof.json')")
assert new!=text;ast.parse(new,filename=append.name);append.write_text(new,encoding='utf-8',newline='\n');shutil.copy2(append,W/append.name)
stamp=datetime.now(timezone.utc).isoformat()
note=f'''
## Comparison145 preflight passed; full cohort launch gated ({stamp})

All6 excluded ordered/clustered A/B/C stores independently pass196608rows/
4718592CRCbytes/fullindexes/originalreceipts+generations. Owned dummybusy-clear/
five birth classifications pass, actual preflight/controller/waiter/worker0,
no forcedkill or repeatednativecase. Actualpreflight nativeexit journal covers
all6. No qualified145 case/controller has started. Policy6b76deee2167fd15d1682697f52429ddf005e662f3ca2ed90b5da580e371a32b
and216order/inputs/binaries/gates remain exact; baseline154/candidate344+two
lints/all28 stores/wire/recovery REUSED, no Rustbuild/test. Source/resultUNSAVED.

Current one-off gate work/wait_launch_phase145.ps1 is READY/LAUNCHING. It uses
metadata only while actual reset/tasks/all supervisors/globalbuilds are busy,
then invokes existing launch_phase_compare_145.ps1 ONCE; it makes NO probes
while the actual controller/native children run. Inspect fresh gatepid/creation,
phase145-cohort-launch-wait started/metadata/actual-exit files and actual
controller/worker/run-phase-compare-145.log/phase145-actual-exits FIRST. Never
duplicate this gate/controller, old preflight waiter alreadyterminal0.
Deadline2h/10s polling/no new automation/app/process/settings changes. If a
launcher races a guard after append but beforecontroller, gate stops and saves
actual1: inspect exact append/prefix/absent cases, then separate verified
continuation only; never blindly repeat append/controller here. Gate does not
repeat cases or alter numerical gates/timers/inputs/binaries. Running checkpoint
appender dependency alone updated beforefreeze to chain from THIS gate proof.

Finish this COMPLETE216 balanced12round/sixshape sameD supported016 A/B vs
JOINT131+144C; full/both-half144AA/144guards/sixclusteredgoals unchanged. All
input/readCRC/phase/index/write/flush/sync charged, every stall once/no selected
retime/metric selection/outlier discard.120continuous clear afterprep/freezes,
reset onbusy; ownedCPU8/metadata idle onstdin duringNative/strictbefore+after
EVERYcase guards. Onlypredeclared provenoutside-lifetime waits, possibleoverlap/
missingbirth/resetrejectwholeprefix. Both complete independent payload/index/
CRC/originalreceipt digest+gen fromdeclaredrun+1/everyprobe vsEVERYnative/frozen/
order/full+halfmetrics auditors and actualwaits/exits required aftercontroller
exit and120freshquiet. Do not launch audits whilecohort activeORwaiting.

Supported016 exact/017 UNRELEASED/145 speed UNEVALUATED. Original324Native/
252service/42goals/153AA/171guards pluscorrectness/retry/recovery/sustained
unchanged; no componentrelease/universalwin/ETA. Anytimed ordeclaredcohort
activeORwaiting blocksGit/hash/copy/build/package/cleanup/independentaudits/
otherbenchmarks; metadata/owned smalllogs only. No inline status with Python
filenames. Neverstop/message unrelatedproject/app/forcequit/rearmreset/resume
abandonedchat/oldmigration/oldloop/checker. Localtests/builds/Actions$0Stopusage/
evidence skipCI; SHORTprivateoutcomes/failures/usefulsource,freshremotebytes
thenliteralabsolute native scoped no-reparse completedcleanup. No rawmultiGB
bundles/privatehistory/ref/tag/releasedeletion, keep usefulkits/unsavedwork/
uniqueunverifiedexports. SameACTIVE30minheartbeat/name/target/prefs, no duplicate.
'''
with N.open('ab') as f:f.write(note.encode())
after=N.read_bytes();assert after==before+note.encode()
proof={'utc':stamp,'old_sha256':prior['new_sha256'],'new_sha256':hashlib.sha256(after).hexdigest(),'old_history_prefix_exact':True,'all6_preflights_complete':True,'actual_preflight_waiter_worker_exit0':True,'cohort_launch_gate_ready':True,'no145_qualified_case_or_controller_started':True,'policy_order_inputs_binaries_numerical_gates_unchanged':True,'checkpoint_dependency_only_updated_before_freeze':True}
(R/'phase145-launch-gate-next-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof),flush=True)
