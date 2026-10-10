"""Fresh declaration after untimed123 exposed unchanged driver seed limit."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,shutil
R=Path('D:/Codex/Kestrel/work');W=R/'perf-124'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert not W.exists();assert not (R/'perf-123/component-cases.jsonl').exists()
assert load(R/'perf-123/preflight-failure-proof.json')['all_648_cases_unstarted']
assert load(R/'perf-123/smoke-proof-v2.json')['complete']
W.mkdir();policy=load(R/'perf-123/policy.json')
policy.update(trial=124,declared_utc=datetime.now(timezone.utc).isoformat(),
 previous_trial='123 had no timed cases: excluded seed17 violated the unchanged driver1..12 assertion. A second excluded seed5 check passed full rows/CRC and inherited mask256. Original declaration, failing source/stderr and unstarted cohort are preserved.',
 input_seed_policy='36 round labels repeat the exact12 valid seeds three times; seed=(round-1)%12+1. This improves sample density without changing common driver or workload rows. No new engine or same-seed tuning.',
 cases=[s|{'seed':(s['round']-1)%12+1} for s in policy['cases']])
assert all(1<=s['seed']<=12 for s in policy['cases'])
(W/'policy.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8')
(W/'declaration-proof.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(W/'policy.json'),'before_copy_and_controller_derivation':True,'no_timer_started':True},indent=2)+'\n',encoding='utf-8')
for name in ['binary','logs','tmp']:(W/name).mkdir()
source=R/'perf-123/binary/compaction_stage_121.exe';assert sha(source)==policy['actual_binary_sha256']
shutil.copy2(source,W/'binary/compaction_stage_121.exe')
run=(R/'run_controls_123.py').read_text(encoding='utf-8').replace('perf-123','perf-124')
run=run.replace("spec['name'],str(spec['round'])", "spec['name'],str(spec['seed'])")
run=run.replace("result['seed']==spec['round']", "result['seed']==spec['seed']")
audit=(R/'audit_controls_123.py').read_text(encoding='utf-8').replace('perf-123','perf-124').replace("spec['round']", "spec['seed']")
marker="    result=load(W/case['stdout']);assert result['component_only'] and result['all_checks_passed']"
assert audit.count(marker)==1
audit=audit.replace(marker,marker+"\n    assert result['workload']==spec['name'] and result['seed']==spec['seed'] and case['identity']['affinity_mask']==256")
smoke=(R/'smoke_controls_123_v2.py').read_text(encoding='utf-8').replace('perf-123','perf-124').replace('run_controls_123.py','run_controls_124.py').replace('audit_controls_123.py','audit_controls_124.py').replace('smoke-fixtures-v2','smoke-fixtures').replace('smoke-proof-v2','smoke-proof')
for name,text in [('run_controls_124.py',run),('audit_controls_124.py',audit),('smoke_controls_124.py',smoke)]:
    ast.parse(text);(R/name).write_text(text,encoding='utf-8',newline='\n');shutil.copy2(R/name,W/name)
shutil.copy2(R/'prepare_controls_124.py',W/'prepare_controls_124.py')
(W/'preparation-proof.json').write_text(json.dumps({'complete':True,'policy_sha256':sha(W/'policy.json'),'binary_sha256':sha(W/'binary/compaction_stage_121.exe'),'all_three_labels_same_supported016_binary':True,'fresh_compile_tests':0,'only_controller_changes':True,'no_timer_started':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'trial':124,'cases':648,'rounds':36,'valid_seed_cycle':[1,12],'same_actual_baseline_binary':True,'123_unstarted_preserved':True}))
