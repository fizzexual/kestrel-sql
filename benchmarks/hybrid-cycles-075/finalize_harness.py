"""Explain the preserved generated harness snapshot versus its final freeze."""
import hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parent
def load(n):return json.loads((W/n).read_text(encoding='utf-8-sig'))
def digest(b):return hashlib.sha256(b).hexdigest()
run=(W/'run_model.py').read_bytes()
addition=b",'canonical_audit.py','qualify_integration.py','prerequisite-073-policy.json'"
assert run.count(addition)==1
initial=run.replace(addition,b'')
old=load('benchmark-helper-derivation.json')['new_075_run_sha256']
assert digest(initial)==old
frozen=load('cohort-policy.json')['frozen_file_sha256']['run_model.py']
assert digest(run)==frozen
result={'initial_generated_harness_sha256':old,'final_frozen_harness_sha256':frozen,
        'exact_only_difference':'Three FILES freeze-list additions: canonical_audit.py, qualify_integration.py, prerequisite-073-policy.json',
        'original_derivation_record_preserved':True,'finalization_before_cohort_freeze':True,
        'no_workload_or_observation_or_gate_change':True,'final_hash_is_cohort_policy_authority':True}
p=W/'harness-finalization.json';assert not p.exists()
p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
