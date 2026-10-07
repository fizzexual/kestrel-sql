"""Separate predeclared replication; retain failed065 calibration unchanged."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-065'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert not (W/'policy.json').exists()
a=load(OLD/'audit.json');assert a['complete'] and a['identity_checks_failed']==1 and a['goals_failed']==a['guards_failed']==0
assert a['failed_checks'][0]['metric']=='first_encode_ms' and a['failed_checks'][0]['paired_ratio']>1.10
assert all(not d['justifies_engine_buffer_experiment'] for d in a['decisions'].values())
for n in ['baseline.json','input-provenance.json','build.json','smoke.json','encoder_probe.rs','released_encoder_models.rs','process_memory.py','serde_to_vec_excerpt.rs.txt']:
    shutil.copy2(OLD/n,W/n)
shutil.copytree(OLD/'bin',W/'bin');shutil.copytree(OLD/'inputs',W/'inputs');shutil.copytree(OLD/'diagnostics',W/'diagnostics')
p=load(OLD/'policy.json');p['trial']=66;p['rounds']=12;p['cases']=[]
for turn in range(12):
    for index,size in enumerate([0,50000,99000]):
        k=(turn+index)%4
        for variant in p['variants'][k:]+p['variants'][:k]:p['cases'].append({'round':turn,'starting_receipts':size,'variant':variant,'repetitions':33})
p.update(declared_utc=datetime.now(timezone.utc).isoformat(),before_build_and_timing=False,before_timing=True,
    reason='Independent144-case replication after065 cold-first identity ratio1.100009 exceeds1.10; triple paired rounds, all thresholds unchanged, original failure retained',
    original_failed_cohort_audit_sha256=sha(OLD/'audit.json'),original_failed_cohort_never_replaced=True,
    binary_and_smoke_inherited_without_rebuilding_or_rerunning=True,original_binary_path=str(OLD/'bin/encoder-probe.exe'))
for item in p['inputs']:item['body_path']=str(W/item['body_relative'])
save(W/'policy.json',p)
for name in ['run.py','audit.py','check_processes.ps1']:
    original=(OLD/name).read_text(encoding='utf-8');text=original
    if name=='run.py':text=text.replace("'total':48","'total':len(policy['cases'])")
    if name=='audit.py':
        text=text.replace("==48 and not r['failures']","==144 and not r['failures']").replace('for turn in range(4):','for turn in range(12):').replace("'timed_encodes':48*33","'timed_encodes':144*33").replace('Median of four','Median of twelve')
    if name=='check_processes.ps1':text=text.replace('perf-065','perf-066')
    (W/name).write_text(text,encoding='utf-8')
save(W/'replication-provenance.json',{'utc':datetime.now(timezone.utc).isoformat(),'original_work':str(OLD),'original_audit_sha256':sha(OLD/'audit.json'),
    'original_policy_sha256':sha(OLD/'policy.json'),'identical_goal_guard_calibration_thresholds':True,'independent_new_cases_no_prior_case_restarted':True,
    'same_binary_sha256':sha(W/'bin/encoder-probe.exe'),'source_and_model_byte_identical':sha(W/'encoder_probe.rs')==sha(OLD/'encoder_probe.rs') and sha(W/'released_encoder_models.rs')==sha(OLD/'released_encoder_models.rs'),
    'harness_original_sha256':{n:sha(OLD/n) for n in ['run.py','audit.py']},'harness_adapted_sha256':{n:sha(W/n) for n in ['run.py','audit.py']},
    'build_record_inherited_from065_actual_original_build_dates_paths_preserved':True,'smoke_diagnostics_inherited_from065_excluded':True})
print(json.dumps({'prepared':True,'new_cases':144,'thresholds_unchanged':True,'original_failure_preserved':True,'no_engine_change':True}))
