"""Declare one complete comparison of supported016 and the exact phase131 binary."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, itertools, json, platform, random, shutil, subprocess
R = Path('D:/Codex/Kestrel/work'); W = R / 'perf-132'; REPO = R.parent / 'outputs/kestrel-sql'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
assert not W.exists()
git = ['git', '--no-optional-locks', '-c', 'safe.directory='+REPO.as_posix(), '-c', 'gc.auto=0', '-C', str(REPO)]
assert not subprocess.check_output(git+['status', '--porcelain=v1', '--untracked-files=all']).strip()
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
assert head == load(R/'phase131-publication-proof.json')['private_main']
assert load(R/'phase131-storage-cleanup-proof.json')['completed131_test_stores_and_build_outputs_closed'] and not (R/'perf-131').exists()
kit = load(R/'compaction-kit-122/provenance.json'); candidate = load(R/'compaction-kit-131/provenance.json')
assert all(sha(REPO/n)==v for n,v in kit['source_core_sha256'].items())
assert load(R/'phase131-storage-cleanup-proof.json')['completed131_test_stores_and_build_outputs_closed']
configs = ['ordered','clustered','interleaved','duplicates','late','extreme']
variants = ['baseline_a','baseline_b','candidate']; permutations = list(itertools.permutations(variants))
rng = random.Random(20261011); cases = []
for block in range(2):
    orders = {n: permutations.copy() for n in configs}
    for n in configs: rng.shuffle(orders[n])
    for offset in range(6):
        round_number=block*6+offset+1; names=configs.copy(); rng.shuffle(names)
        for name in names:
            for variant in orders[name][offset]:
                cases.append({'index':len(cases),'round':round_number,'seed':round_number,'name':name,'variant':variant})
assert len(cases)==216
for n in configs:
    for rounds in [range(1,13),range(1,7),range(7,13)]:
        observed=[tuple(s['variant'] for s in cases if s['name']==n and s['round']==r) for r in rounds]
        assert sorted(observed)==sorted(permutations*(len(rounds)//6))
baseline = next(x for x in kit['files'] if x['variant']=='baseline')
binary = {'baseline.exe':baseline['sha256'],'candidate131.exe':candidate['useful_executable']['sha256']}
policy = {'trial':132,'declared_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,
 'kind':'Archive component comparison: identical supported016 A/B versus exact phase131 C',
 'hypothesis':'Deriving ordered concatenation while collecting CRC-validated inputs avoids late merge probing for ordered input; bounded merge retains clustered preparation gains without material regressions. All phase selection/input work is inside the existing compaction clock. This tests combined131 versus016, not the isolated131 effect versus127; ordered workspace is only constructed after disorder.',
 'component_configs':configs,'cases':cases,'rounds':12,'schedule_rng':'Python random.Random(20261011), fixed before timing; all six permutations once per workload per half',
 'affinity_mask':256,'cooldown_seconds':120,'cooldown_poll_seconds':10,'cooldown_deadline_seconds':7200,'AA_lower':.9,'AA_upper':1.1,'candidate_guard_upper':1.1,
 'scopes':['full','first_half','second_half'],'metrics':['wall_ms','prepare_ms','segment_sync_ms','catalog_sync_ms'],
 'goals':{'clustered_wall_ms_max_ratio':.95,'clustered_prepare_ms_max_ratio':.90},
 'runs_per_case':32,'rows_per_run':1024,'columns':3,'same_original_driver':True,'binary_sha256':binary,
 'prerequisites_reused':{'baseline_tests':154,'candidate_tests':340,'candidate_strict_lints':2,'new_Rust_build_or_tests':0,'candidate_source_commit':candidate['source_private_commit']},
 'unchanged_release_gates':{'Native':324,'service':252,'goals':42,'AA':153,'guards':171},
 'same_physical_D':True,'resource_bound_bytes':600_000_000,'timeout_seconds':90,'no_selected_retiming':True,
 'no_global_CPU_power_ASLR_or_security_change':True,'platform':platform.platform(),
 'new_protocol':'One owned persistent PowerShell metadata worker blocks on stdin between requests; identical reset/task/supervisor/global-build checks before/after every native case and during120-second continuous quiet window. Worker does no probe during native lifetime and must actually exit0 after all cases. No engine/numerical gate/input reduction; removed repeated PowerShell startup is outside compaction clock. Bounded nonsecret blocker reasons retained; no command-line dumping.',
 'timer':'Instant around entire Archive.compact_small; preparation begins at input CRC/read/collection. Setup, native verification/pins/reclaim/reopen outside timer.',
 'environment_limits':'Other local development/server apps remain running; no app stopped. Reset/task work and visible build checks required before timing and before and after each actual native case. A/A controls decide qualification; snapshots cannot exclude every brief background task.',
 'storage':'Concise private Markdown outcomes/failures and useful source, fresh byte-exact remote verification, then native scoped completed fixture cleanup; no raw bundle.'}
W.mkdir(); (W/'policy.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8')
(W/'declaration-proof.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(W/'policy.json'),'before_binary_copy_or_smoke':True,'no_timer_started':True},indent=2)+'\n',encoding='utf-8')
for n in ['binary','logs','tmp']: (W/n).mkdir()
for src,dest in [(R/'compaction-kit-122/baseline.exe',W/'binary/baseline.exe'),(R/'compaction-kit-131/candidate131.exe',W/'binary/candidate131.exe')]:
    assert sha(src)==binary[dest.name]; shutil.copy2(src,dest); assert sha(dest)==binary[dest.name]
ast.parse((R/'run_phase_compare_132.py').read_text(encoding='utf-8'))
ast.parse((R/'audit_phase_compare_132.py').read_text(encoding='utf-8'))
for n in ['prepare_phase_compare_132.py','run_phase_compare_132.py','audit_phase_compare_132.py','smoke_phase_compare_132.py','activity_worker_132.ps1','launch_phase_compare_132.ps1','append_phase132_declared.py','derive_phase_compare_132.py']:
    shutil.copy2(R/n,W/n)
(W/'preparation-proof.json').write_text(json.dumps({'complete':True,'policy_sha256':sha(W/'policy.json'),'binary_sha256':binary,'new_Rust_build_or_tests':0,'same_driver_both_artifacts':True,'no_timer_started':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'declared_and_prepared':True,'trial':132,'cases':216,'fresh_Rust_tests':0,'all_prerequisites_explicitly_reused':True,'no_timer_started':True}))
