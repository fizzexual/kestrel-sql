"""Decode the entire rejected145 prefix without evaluating selected timings."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, sys
sys.dont_write_bytecode = True
R = Path('D:/Codex/Kestrel/work'); W = R/'perf-145'
sys.path.insert(0, str(R))
import archive_audit_099 as independent
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
oracle = ast.parse((W/'audit_phase_compare_145.py').read_text(encoding='utf-8'))
node = next(n for n in oracle.body if isinstance(n, ast.FunctionDef) and n.name == 'rows')
exec(compile(ast.Module(body=[node], type_ignores=[]), '<frozen independent145 row oracle>', 'exec'))
policy = load(W/'policy.json'); frozen = load(W/'freeze.json'); failed = load(W/'cohort-failure.json')
actual = load(R/'phase145-actual-exits.json')
assert actual['cohort_actual_exit'] == 1 and actual['actual_controller_wait_completed']
assert failed['completed'] == 118 and failed['unstarted_indices'] == list(range(118,216)) and failed['failed_case_not_retimed']
assert 'Possible in-case interference' in failed['error']
assert not (W/'cohort-completion.json').exists() and not (W/'audit.json').exists()
assert all(sha(W/n) == h for n,h in frozen['files'].items())
assert all(sha(R/n) == h for n,h in frozen['files'].items() if n.endswith(('.py','.ps1')))
assert load(W/'cooldown-proof.json')['continuous_quiet_seconds'] >= 120
cases = [json.loads(s) for s in (W/'component-cases.jsonl').read_text(encoding='utf-8').splitlines()]
assert len(cases) == 118 and len(policy['cases']) == 216
assert {c['index'] for c in cases} == set(range(118))
assert len(list((W/'fixtures').iterdir())) == 118
workers = [json.loads(s) for s in (W/'worker-exits.jsonl').read_text(encoding='utf-8').splitlines()]
assert len(workers) == 2 and all(e['actual_exit'] == 0 and e['actual_wait_completed'] and not e['forced_owned_worker_kill'] for e in workers)
assert load(W/'protocol-proof.json')['dummy_detected_busy_then_clear']
assert load(W/'smoke-proof.json')['complete'] and len(load(W/'smoke-proof.json')['checks']) == 6
checks = []
for case, spec in zip(cases, policy['cases']):
    assert all(case[k] == v for k,v in spec.items())
    assert case['actual_exit'] == 0 and case['actual_wait_completed'] and not case.get('timeout')
    assert case['identity']['owned_Popen_handle'] and case['identity']['affinity_mask'] == 256
    result = load(W/case['stdout'])
    assert result['component_only'] and result['all_checks_passed'] and result['version'] == '0.3.16'
    assert result['workload'] == spec['name'] and result['seed'] == spec['seed'] and result['cold_rows'] == 32768
    expected = [row for run in range(32) for row in rows(spec['name'], run, spec['round'])]
    declared = [[f'merge121:{r}',r,r+1] for r in range(32)] if spec['name'] in ['clustered','late'] else []
    assert result['receipts'] == declared
    receipts = {key:(rows(spec['name'],r,spec['round']),r+1) for key,r,generation in declared}
    decoded = independent.check(W/case['fixture'], expected, receipts)
    assert decoded['rows'] == 32768 and decoded['head'] == 33 and len(decoded['segments']) == 1
    assert decoded['full_block_crc_bytes'] == result['full_crc_bytes'] == 786432
    assert result['before']['generation'] == 32 and result['after']['generation'] == 33 and result['reduced'] == 31
    before = result['before']['publication_profile']; after = result['after']['publication_profile']
    stages = {key:after[key]['total_ms']-before[key]['total_ms'] for key in ['prepare','segment_write','segment_sync','catalog_encode','catalog_write','catalog_sync','catalog_rename']}
    assert all(value >= 0 for value in stages.values())
    assert after['completed']-before['completed'] == 1 and after['attempts']-before['attempts'] == 1
    assert result['compaction_ns'] > 0 and sum(stages.values()) <= result['compaction_ns']/1e6+.001
    checks.append(spec | {'actual_exit':0,'rows':decoded['rows'],'CRC_bytes':decoded['full_block_crc_bytes'],
        'generation':33,'original_receipts_from_declared_run_plus_one':len(receipts),
        'wall_ms':result['compaction_ns']/1e6,'stages_ms':stages,'stdout_sha256':sha(W/case['stdout'])})
    if len(checks)%24 == 0: print(json.dumps({'independently_decoded':len(checks),'total':118}),flush=True)
proof = {'complete_prefix_audit':True,'utc':datetime.now(timezone.utc).isoformat(),'completed_cases':118,
    'unstarted_indices':list(range(118,216)),'controller_actual_exit':1,'independent_correctness_passed':True,
    'full_payload_rows':sum(c['rows'] for c in checks),'fully_checked_crc_bytes':sum(c['CRC_bytes'] for c in checks),
    'original_receipts_checked':sum(c['original_receipts_from_declared_run_plus_one'] for c in checks),
    'all_frozen_bytes_unchanged':True,'case_checks':checks,'all_samples_retained_once':True,
    'paired_full_or_half_controls_evaluated':False,'performance_rejected_possible_overlap':True,
    'policy_sha256':sha(W/'policy.json'),'journal_sha256':sha(W/'component-cases.jsonl'),
    'release017_qualified':False,'no_selected_retiming':True}
assert proof['full_payload_rows'] == 3866624 and proof['fully_checked_crc_bytes'] == 92798976
assert not (W/'prefix-audit.json').exists()
(W/'prefix-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in proof.items() if k not in ['case_checks','unstarted_indices']}),flush=True)
