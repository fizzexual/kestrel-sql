"""Repair only the exact one-off metadata helper identity; no native case started."""
from pathlib import Path
import ast, hashlib, json
from datetime import datetime,timezone
R=Path('D:/Codex/Kestrel/work');W=R/'perf-148'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (W/'smoke-fixtures').exists() and not (R/'phase148-preflight-actual-exits.json').exists()
assert json.loads((R/'phase148-preflight-quiet-actual-exits.json').read_text(encoding='utf-8-sig'))['actual_exit']==1
parent=R/'activity_worker_148.ps1';worker=parent.read_text(encoding='utf-8')
worker=worker.replace('(run_phase_compare_148|smoke_phase_compare_148)', '(wait_quiet_preflight148_v2)')
dest=R/'activity_quiet_preflight148_v2.ps1';assert not dest.exists();dest.write_text(worker,encoding='utf-8',newline='\n')
source=(R/'wait_quiet_preflight148.py').read_text(encoding='utf-8')
source=source.replace("api={};exec(", "source=source.replace(\"activity_worker_148.ps1\",\"activity_quiet_preflight148_v2.ps1\")\napi={};exec(")
source=source.replace('phase148-preflight-quiet-proof.json','phase148-preflight-quiet-v2-proof.json')
ast.parse(source);dest=R/'wait_quiet_preflight148_v2.py';assert not dest.exists();dest.write_text(source,encoding='utf-8',newline='\n')
launch=(R/'launch_ready_preflight148.ps1').read_text(encoding='utf-8')
launch=launch.replace('wait_quiet_preflight148.py','wait_quiet_preflight148_v2.py').replace('phase148-preflight-quiet.log','phase148-preflight-quiet-v2.log').replace('phase148-preflight-quiet-actual-exits.json','phase148-preflight-quiet-v2-actual-exits.json')
dest=R/'launch_ready_preflight148_v2.ps1';assert not dest.exists();dest.write_text(launch,encoding='utf-8',newline='\n')
proof={'utc':datetime.now(timezone.utc).isoformat(),'failed_quiet_source_sha256':sha(R/'wait_quiet_preflight148.py'),'failed_launcher_sha256':sha(R/'launch_ready_preflight148.ps1'),'failed_parent_worker_source_sha256':sha(parent),'policy_sha256':sha(W/'policy.json'),'no_database_native_case_started':True,'failed_worker_actual_exit_not_separately_waited_or_saved':True,'only_new_exact_quiet_owner_name_permitted':True,'main_worker_engine_policy_order_gates_unchanged':True}
(R/'phase148-quiet-helper-correction.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Fixed quiet-only owner identity; engine and qualification sources unchanged')
