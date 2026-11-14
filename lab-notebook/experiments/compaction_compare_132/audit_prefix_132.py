"""Audit every completed case of stopped132; no paired speed qualification."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, sys
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-132'
sys.path.insert(0,str(R))
import archive_audit_099 as independent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
module=ast.parse((R/'audit_phase_compare_132.py').read_text(encoding='utf-8'))
row_node=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='rows')
exec(compile(ast.Module(body=[row_node],type_ignores=[]),'<unchanged independent row oracle>','exec'))
policy=load(W/'policy.json');freeze=load(W/'freeze.json');failure=load(W/'cohort-failure.json')
actual=load(R/'phase132-actual-exits.json')
assert actual['cohort_actual_exit']==1 and actual['actual_controller_wait_completed']
assert failure['completed']==88 and failure['unstarted_indices']==list(range(88,216)) and failure['failed_case_not_retimed']
assert not (W/'cohort-completion.json').exists() and not (W/'audit.json').exists()
assert all(sha(W/n)==v for n,v in freeze['files'].items())
assert all(sha(R/n)==v for n,v in freeze['files'].items() if n.endswith(('.py','.ps1')))
assert load(W/'cooldown-proof.json')['continuous_quiet_seconds']>=120
activity=[json.loads(line) for line in (W/'activity-checks.jsonl').read_text().splitlines()]
probes=[x for x in activity if x['place'] in ['before_case','after_case']]
assert len(probes)==176
assert [(p['place'],p['index']) for p in probes]==[(place,i) for i in range(88) for place in ['before_case','after_case']]
assert all(p['exit']==0 for p in probes[:-1]) and probes[-1]['exit']==3
for p in [x for x in activity if x['place'] in ['cooldown','before_case','after_case']]:
    messages=[json.loads(line) for line in p['stdout'].splitlines() if line.strip()]
    assert messages[0]['verified_controller_pid']==52464 and messages[0]['verified_controller_creation_filetime']==134362604754622510
    if p['exit']==0:assert len(messages)==2 and messages[0]['no_other_task_work'] and messages[1]['no_visible_build_jobs']
blocked=json.loads(probes[-1]['stdout'])
assert len(blocked['other_work'])==1 and blocked['other_work'][0]['pid']==82952 and blocked['other_work'][0]['name']=='pwsh.exe' and blocked['other_work'][0]['creation_utc']=='2026-10-12T06:44:18.5201470Z'
cases=[json.loads(line) for line in (W/'component-cases.jsonl').read_text().splitlines()]
assert len(cases)==88
checks=[]
worker_exits=[json.loads(line) for line in (W/'worker-exits.jsonl').read_text().splitlines()]
assert len(worker_exits)==2 and all(e['actual_exit']==0 and e['actual_wait_completed'] and not e['forced_owned_worker_kill'] for e in worker_exits)
assert load(W/'protocol-proof.json')['dummy_detected_busy_then_clear']
assert all(p['exit']==0 for p in activity if p['place'].startswith('preflight_'))
assert datetime.fromisoformat(blocked['other_work'][0]['creation_utc'])>datetime.fromisoformat(cases[-1]['completed_utc'])
for case,spec in zip(cases,policy['cases']):
    assert all(case[k]==v for k,v in spec.items())
    assert case['actual_exit']==0 and case['actual_wait_completed'] and not case.get('timeout')
    assert case['identity']['owned_Popen_handle'] and case['identity']['affinity_mask']==256
    result=load(W/case['stdout'])
    assert result['all_checks_passed'] and result['component_only'] and result['version']=='0.3.16'
    assert result['workload']==spec['name'] and result['seed']==spec['seed'] and result['cold_rows']==32768
    expected=[item for run in range(32) for item in rows(spec['name'],run,spec['round'])]
    receipts={id:(rows(spec['name'],run,spec['round']),generation) for id,run,generation in result['receipts']}
    assert set(receipts)==({f'merge121:{run}' for run in range(32)} if spec['name'] in ['clustered','late'] else set())
    checked=independent.check(W/case['fixture'],expected,receipts)
    assert checked['rows']==32768 and checked['head']==33 and len(checked['segments'])==1
    assert checked['full_block_crc_bytes']==result['full_crc_bytes']==786432
    assert result['before']['generation']==32 and result['after']['generation']==33 and result['reduced']==31
    before=result['before']['publication_profile'];after=result['after']['publication_profile']
    stages={key:after[key]['total_ms']-before[key]['total_ms'] for key in ['prepare','segment_write','segment_sync','catalog_encode','catalog_write','catalog_sync','catalog_rename']}
    assert all(x>=0 for x in stages.values())
    assert after['completed']-before['completed']==1 and after['attempts']-before['attempts']==1
    assert result['compaction_ns']>0 and sum(stages.values())<=result['compaction_ns']/1e6+.001
    checks.append(spec|{'actual_exit':0,'rows':checked['rows'],'CRC_bytes':checked['full_block_crc_bytes'],'generation':33,'receipt_ids':len(receipts),
                        'wall_ms':result['compaction_ns']/1e6,'stage_ms':stages,'raw_stdout_sha256':sha(W/case['stdout'])})
audit={'complete_prefix_audit':True,'utc':datetime.now(timezone.utc).isoformat(),'completed_cases':88,'unstarted_indices':list(range(88,216)),
       'independent_correctness_passed':True,'full_payload_rows':sum(x['rows'] for x in checks),'fully_checked_crc_bytes':sum(x['CRC_bytes'] for x in checks),
       'all_frozen_inputs_unchanged':True,'controller_actual_exit':1,'blocked_after_case':87,'blocked_process':blocked['other_work'],
       'case_checks':checks,'all_samples_retained':True,'paired_full_or_half_controls_evaluated':False,'release017_qualified':False,
       'policy_sha256':sha(W/'policy.json'),'journal_sha256':sha(W/'component-cases.jsonl'),'no_selected_retiming':True}
assert not (W/'prefix-audit.json').exists()
(W/'prefix-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps({k:v for k,v in audit.items() if k not in ['case_checks','unstarted_indices','blocked_process']}))
