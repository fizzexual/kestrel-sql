from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-149';N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'smoke-proof.json')['complete'] and load(R/'phase149-preflight-actual-exits.json')['preflight_actual_exit']==0
assert not (R/'phase149-running-next-proof.json').exists() and not (W/'component-cases.jsonl').exists()
old=N.read_bytes();expected=load(R/'phase149-preflight-ready-next-proof.json')['new_sha256']
assert hashlib.sha256(old).hexdigest()==expected
stamp=datetime.now(timezone.utc).isoformat()
note=f'''

###149 existing216-case cohort launching — {stamp}

149prepared/preflightpassed/sourceUNSAVED. FinishTHIScomplete216 cohort/actual
native/controller/worker waits/exits/fullpayload-index-CRC-originalreceipt-
generation-frozenbytes-EVERYprobevsEVERYlifetime/full-half AA-guard-goal audits
beforeanynewwork. Allrules/gates/binaries/order inpreviousreadycheckpoint apply.
Check run-phase-compare-149.log/phase149-actual-exits.json/perf149/actualowned
controller-worker identities FIRST. No duplicate launch/checkpoint orpassed
preflight/build rerun. WhileactiveORwaiting ONLYownedpolls/smalllogs/metadata,
noGit/hash/copy/build/package/cleanup/independentaudit/otherbenchmark. Strict120
quiet/ownedCPU8/percasebefore-after/nooverlap; preserveentire failed/unstarted
prefix ifblocked. No selectedretiming/outlierremoval. Supported016exact/017
unreleased/speedunevaluated. SHORTprivateverifiedsave thennativeexactcleanup.
Nextunused150+ONLYafter149closure; nooldloop/checker/migrationreactivation.
'''
with N.open('ab') as f:f.write(note.encode('utf-8'))
assert N.read_bytes()==old+note.encode('utf-8')
(R/'phase149-running-next-proof.json').write_text(json.dumps({'utc':stamp,'old_sha256':expected,'new_sha256':hashlib.sha256(N.read_bytes()).hexdigest(),'old_history_prefix_exact':True,'declared149_cases':216,'no_case_timed_yet':True,'release017_qualified':False},indent=2)+'\n',encoding='utf-8',newline='\n')
print('149 running checkpoint appended before actual freeze/quiet/timers')
