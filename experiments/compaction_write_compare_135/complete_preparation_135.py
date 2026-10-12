"""Complete an interrupted file-copy preparation without changing policy/inputs."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,shutil
R=Path('D:/Codex/Kestrel/work');W=R/'perf-135'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not (W/'component-cases.jsonl').exists() and not (W/'preparation-proof.json').exists()
policy=load(W/'policy.json');assert policy['trial']==135 and len(policy['cases'])==216 and sha(W/'policy.json')==load(W/'declaration-proof.json')['policy_sha256']
assert not (R/'derive_phase_compare_135.py').exists()
assert all(sha(W/'binary'/n)==h for n,h in policy['binary_sha256'].items())
names=['prepare_phase_compare_135.py','run_phase_compare_135.py','audit_phase_compare_135.py','smoke_phase_compare_135.py','activity_worker_135.ps1','launch_phase_compare_135.ps1','append_phase135_declared.py']
assert all(sha(R/n)==sha(W/n) for n in names)
failure={'utc':datetime.now(timezone.utc).isoformat(),'preparation_actual_exit':1,'reason':'Inherited copy list expected derive_phase_compare_135.py, while actual new derivation was named derive_write_compare_135.py; final source copy failed after policy/binaries/seven controllers were saved','all216_timed_cases_unstarted':True,'policy_and_binaries_unchanged':True}
(W/'preparation-failure.json').write_text(json.dumps(failure,indent=2)+'\n',encoding='utf-8',newline='\n')
shutil.copy2(R/'derive_write_compare_135.py',R/'derive_phase_compare_135.py')
shutil.copy2(R/'derive_phase_compare_135.py',W/'derive_phase_compare_135.py')
assert sha(R/'derive_phase_compare_135.py')==sha(R/'derive_write_compare_135.py')==sha(W/'derive_phase_compare_135.py')
for n in ['complete_preparation_135.py','derive_write_compare_135.py']:shutil.copy2(R/n,W/n)
for n in ['run_phase_compare_135.py','audit_phase_compare_135.py']:ast.parse((R/n).read_text(encoding='utf-8'))
(W/'preparation-proof.json').write_text(json.dumps({'complete':True,'policy_sha256':sha(W/'policy.json'),'binary_sha256':policy['binary_sha256'],'new_Rust_build_or_tests':0,'same_driver_both_artifacts':True,'no_timer_started':True,'failed_source_copy_attempt_preserved':True,'same_declared_policy_and_inputs_not_regenerated':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print('135 interrupted preparation completed; all216 timed cases unstarted, frozen policy/binaries unchanged')
