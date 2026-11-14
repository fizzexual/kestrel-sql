"""Audit every diagnostic case, independent index field, policy and complete metrics."""
from pathlib import Path
from datetime import datetime,timezone
from statistics import median
from collections import Counter
import hashlib,json,itertools,sys,traceback
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-142'
sys.path.insert(0,str(R));from index_reference_142 import expected,check
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
try:
    assert not (W/'audit.json').exists()
    exitproof=load(R/'profile142-actual-exits.json');assert exitproof['cohort_actual_exit']==0 and exitproof['actual_controller_wait_completed']
    policy=load(W/'policy.json');assert sha(W/'policy.json')==load(W/'declaration-proof.json')['policy_sha256']
    cases=[json.loads(line) for line in (W/'component-cases.jsonl').read_text().splitlines()]
    assert len(cases)==216 and load(W/'cohort-completion.json')['complete']
    for name in policy['component_configs']:
        for half in (range(1,7),range(7,13)):
            permutations=[]
            for round in half:
                group=[c for c in policy['cases'] if c['round']==round and c['name']==name]
                assert len(group)==3 and {c['seed'] for c in group}=={round}
                permutations.append(tuple(c['variant'] for c in group))
            assert Counter(permutations)==Counter(itertools.permutations(('baseline_a','baseline_b','candidate')))
    checks=[];results=[];oracles={}
    for spec,case in zip(policy['cases'],cases):
        assert all(case[key]==value for key,value in spec.items()) and case['actual_exit']==0 and case['actual_wait_completed'] and not case.get('timeout')
        assert case['identity']['affinity_mask']==256 and case['identity']['owned_Popen_handle']
        assert case['argv']==[str(W/'binary'/'index_profile142.exe'),spec['name'],str(spec['seed']),spec['variant']]
        assert (W/case['stderr']).read_bytes()==b''
        result=load(W/case['stdout']);key=(spec['name'],spec['seed'])
        if key not in oracles:oracles[key]=expected(*key)
        checks.append({'index':spec['index'],**check(result,spec,oracles[key])});results.append((spec,result))
    freeze=load(W/'freeze.json');assert all(sha(W/name)==value for name,value in freeze['files'].items())
    assert all(sha(R/name)==value for name,value in freeze['files'].items() if name in freeze['actual_source_names'])
    assert load(W/'cooldown-proof.json')['continuous_quiet_seconds']>=120
    workers=[json.loads(s) for s in (W/'worker-exits.jsonl').read_text().splitlines()]
    assert len(workers)==3 and all(w['actual_exit']==0 and w['actual_wait_completed'] and not w['forced_owned_worker_kill'] for w in workers)
    table=[];controls=[];guards=[];goals=[];profiles=[]
    zones=['sum_ns','serialize_ns','crc_ns','block_extrema_ns','global_extrema_ns','monotonic_ns','total_ns']
    for name in policy['component_configs']:
        for scope in policy['scopes']:
            selected={ (s['round'],s['variant']):r for s,r in results if s['name']==name and (scope=='full' or (s['round']<=6)==(scope=='first_half')) }
            rounds=range(1,13) if scope=='full' else range(1,7) if scope=='first_half' else range(7,13)
            a=[selected[(i,'baseline_a')]['elapsed_ns'] for i in rounds];b=[selected[(i,'baseline_b')]['elapsed_ns'] for i in rounds];c=[selected[(i,'candidate')]['elapsed_ns'] for i in rounds]
            aa=median(y/x for x,y in zip(a,b));ratio=median(y/x for x,y in zip(a,c))
            base={'name':name,'scope':scope,'metric':'index_kernel_ns','AA_ratio':aa,'candidate_ratio':ratio,'samples_per_variant':len(a)}
            control=base|{'kind':'AA','passed':policy['AA_lower']<=aa<=policy['AA_upper']};controls.append(control)
            guards.append(base|{'kind':'guard','numerical_passed':ratio<=policy['candidate_guard_upper'],'corresponding_AA_passed':control['passed'],'passed':ratio<=policy['candidate_guard_upper'] and control['passed']})
            goals.append(base|{'kind':'goal','numerical_passed':ratio<=policy['index_goal_upper'],'corresponding_AA_passed':control['passed'],'passed':ratio<=policy['index_goal_upper'] and control['passed']})
            table.append(base|{'baseline_p50_ms':median(a)/1e6/16,'candidate_p50_ms':median(c)/1e6/16,'baseline_max_ms':max(a)/1e6/16,'candidate_max_ms':max(c)/1e6/16,'AA_passed':control['passed']})
        stages={zone:median(r['legacy_profile'][zone] for s,r in results if s['name']==name and s['variant']=='baseline_a') for zone in zones}
        profiles.append({'name':name,'median_stage_ns':stages,'global_rescan_fraction_of_instrumented_total':stages['global_extrema_ns']/stages['total_ns'],'instrumented_clocks_overhead_and_exclusions':True})
    assert len(controls)==len(guards)==len(goals)==18
    failures=[row for row in controls+guards+goals if not row['passed']]
    proof={'complete':True,'correctness_passed':True,'utc':datetime.now(timezone.utc).isoformat(),'cases':216,'rows':sum(c['rows'] for c in checks),'CRC_bytes':sum(c['CRC_bytes'] for c in checks),
           'controls':controls,'guards':guards,'goals':goals,'failed_checks':failures,'failed_AA':sum(not x['passed'] for x in controls),'failed_guards':sum(not x['passed'] for x in guards),'failed_goals':sum(not x['passed'] for x in goals),
           'checks':checks,'table':table,'legacy_stage_profiles':profiles,'all_stalls_retained_once':True,'all_frozen_bytes_exact':True,'diagnostic_only':True,'all_Archive_IO_sync_ACK_excluded':True,'release017_qualified':False}
    (W/'audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in proof.items() if k not in ('checks','table','controls','guards','goals','failed_checks','legacy_stage_profiles')}),flush=True)
except BaseException:
    (W/'audit-failure.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'error':traceback.format_exc(),'no_case_retimed':True},indent=2)+'\n',encoding='utf-8',newline='\n');raise
