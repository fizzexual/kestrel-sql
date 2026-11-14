"""Test temporal-order correlation with one fixed random balanced schedule."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,itertools,json,random,shutil,subprocess
R=Path('D:/Codex/Kestrel/work');W=R/'perf-125';REPO=R.parent/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
kit=load(R/'compaction-kit-122/provenance.json')
assert load(R/'controls124-storage-cleanup-proof.json')['all121122123124_completed_stores_closed']
assert not W.exists()
git=['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-C',str(REPO)]
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all']).strip()
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip();assert head=='d3b92c443e7b72cdb987869595b6e9f0f678ca8d'
assert all(sha(REPO/n)==v for n,v in kit['source_core_sha256'].items())
configs=['ordered','clustered','interleaved','duplicates','late','extreme']
variants=['baseline_a','baseline_b','baseline_c'];permutations=list(itertools.permutations(variants))
rng=random.Random(20261010);cases=[]
for block in range(6):
    orders={name:permutations.copy() for name in configs}
    for name in configs:rng.shuffle(orders[name])
    for offset in range(6):
        round_number=block*6+offset+1;names=configs.copy();rng.shuffle(names)
        for name in names:
            for variant in orders[name][offset]:
                cases.append({'index':len(cases),'round':round_number,'seed':(round_number-1)%12+1,'name':name,'variant':variant})
assert len(cases)==648
assert sorted((s['round'],s['seed'],s['name'],s['variant']) for s in cases)==sorted((r,(r-1)%12+1,n,v) for r in range(1,37) for n in configs for v in variants)
for name in configs:
    for rounds in [range(1,37),range(1,19),range(19,37)]:
        observed=[tuple(s['variant'] for s in cases if s['name']==name and s['round']==r) for r in rounds]
        assert sorted(observed)==sorted(permutations*(len(rounds)//6))
baseline=next(row for row in kit['files'] if row['variant']=='baseline')
policy={'trial':125,'declared_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,
 'kind':'Supported016 identical-baseline A/A/A calibration; no candidate engine',
 'hypothesis':'124 fixedCPU8 and36 rounds still failed24/144 controls. Its fixed workload/permutation cycle can correlate label with temporal/background/fixture effects. Predeclare one seed20261010 balanced shuffle of workload order and permutation-to-round assignment; benefit is unproven. Only execution order changes versus124. Do not search alternative seeds, cores, thresholds or selected reruns.',
 'component_configs':configs,'cases':cases,'rounds':36,'input_seed_policy':'Same12 valid input seeds repeated three times; every case input/label multiset matches124.',
 'schedule_rng':'Python random.Random(20261010); fixed before timing','affinity_mask':256,'cooldown_seconds':120,'AA_lower':.9,'AA_upper':1.1,
 'scopes':['full','first_half','second_half'],'metrics':['wall_ms','prepare_ms','segment_sync_ms','catalog_sync_ms'],
 'actual_binary_sha256':baseline['sha256'],'same_original_driver':True,'runs_per_case':32,'rows_per_run':1024,'columns':3,
 'unchanged_release_gates':{'Native':324,'service':252,'goals':42,'AA':153,'guards':171},
 'no_global_CPU_power_ASLR_or_security_change':True,'same_physical_D':True,'resource_bound_bytes':8_000_000_000,
 'all_completed_outcomes_short_private_MD_then_scoped_cleanup':True,
 'research':['https://github.com/google/benchmark/blob/main/docs/random_interleaving.md','https://github.com/google/benchmark/blob/main/docs/reducing_variance.md']}
W.mkdir();(W/'policy.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8')
(W/'declaration-proof.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(W/'policy.json'),'before_binary_copy_or_controller_derivation':True,'only_schedule_changes_versus124':True,'case_input_multiset_matches124':True,'no_timer_started':True},indent=2)+'\n',encoding='utf-8')
for name in ['binary','logs','tmp']:(W/name).mkdir()
src=R/'compaction-kit-122/baseline.exe';assert sha(src)==policy['actual_binary_sha256'];shutil.copy2(src,W/'binary/compaction_stage_121.exe')
for source,dest in [('run_controls_124.py','run_controls_125.py'),('audit_controls_124_v2.py','audit_controls_125.py'),('smoke_controls_124.py','smoke_controls_125.py')]:
    text=(R/source).read_text(encoding='utf-8').replace('perf-124','perf-125').replace('run_controls_124.py','run_controls_125.py').replace('audit_controls_124.py','audit_controls_125.py')
    ast.parse(text);(R/dest).write_text(text,encoding='utf-8',newline='\n');shutil.copy2(R/dest,W/dest)
shutil.copy2(R/'prepare_controls_125.py',W/'prepare_controls_125.py')
(W/'preparation-proof.json').write_text(json.dumps({'complete':True,'policy_sha256':sha(W/'policy.json'),'binary_sha256':sha(W/'binary/compaction_stage_121.exe'),'engine_and_driver_unchanged':True,'new_Rust_build_or_tests':0,'no_timer_started':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'declared_and_prepared':True,'trial':125,'cases':648,'only_schedule_changes':True,'fixed_rng_seed':20261010,'supported016_binary_exact':True}))
