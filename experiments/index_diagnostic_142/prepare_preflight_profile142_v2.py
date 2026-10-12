from pathlib import Path
import hashlib,json
R=Path('D:/Codex/Kestrel/work');W=R/'perf-142'
assert not (W/'component-cases.jsonl').exists()
assert json.loads((R/'profile142-preflight-actual-exits.json').read_text(encoding='utf-8-sig'))['preflight_actual_exit']==1
names=['activity_worker_profile142.ps1','audit_index_profile_142.py','run_index_profile_142.py','derive_index_harness_142.py']
for name in names:(W/('before-preflight-v2-'+name+'.base64')).write_text(__import__('base64').b64encode((R/name).read_bytes()).decode()+'\n',encoding='ascii',newline='\n')
p=R/'activity_worker_profile142.ps1';text=p.read_text().replace('(run_index_profile_142|smoke_index_profile_142)', '(run_index_profile_142|smoke_index_profile_142|complete_preflight_profile142_v2)');p.write_text(text,encoding='utf-8',newline='\n')
p=R/'run_index_profile_142.py';text=p.read_text().replace("source_names=['derive_index_harness_142.py'", "source_names=['complete_preflight_profile142_v2.py','launch_preflight_profile142_v2.ps1','prepare_preflight_profile142_v2.py','derive_index_harness_142.py'");p.write_text(text,encoding='utf-8',newline='\n')
p=R/'audit_index_profile_142.py';text=p.read_text().replace('assert len(workers)==2','assert len(workers)==3');p.write_text(text,encoding='utf-8',newline='\n')
for name in names+['complete_preflight_profile142_v2.py','launch_preflight_profile142_v2.ps1','prepare_preflight_profile142_v2.py']:(W/name).write_bytes((R/name).read_bytes())
assert hashlib.sha256((W/'policy.json').read_bytes()).hexdigest()==json.loads((W/'declaration-proof.json').read_text())['policy_sha256']
print('Original failed preflight and exact helper bytes preserved; only unstarted sixth preflight can run; policy/binary unchanged',flush=True)
