"""Declare one complete comparison of supported016 and the joint131+144+147 binary."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, itertools, json, platform, random, shutil, subprocess
R = Path('D:/Codex/Kestrel/work'); W = R / 'perf-148'; REPO = R.parent / 'outputs/kestrel-sql'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
assert not W.exists()
assert load(R/'payload147-storage-cleanup-proof.json')['completed147_stores_and_builds_closed'] and not (R/'perf-147').exists()
git = ['git', '--no-optional-locks', '-c', 'safe.directory='+REPO.as_posix(), '-c', 'gc.auto=0', '-C', str(REPO)]
assert not subprocess.check_output(git+['status', '--porcelain=v1', '--untracked-files=all']).strip()
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
assert head == load(R/'payload147-publication-proof.json')['private_main']
assert load(R/'phase131-storage-cleanup-proof.json')['completed131_test_stores_and_build_outputs_closed'] and not (R/'perf-131').exists()
core_kit = load(R/'compaction-kit-122/provenance.json'); kit = core_kit; candidate = load(R/'compaction-kit-147/provenance.json')
assert all(sha(REPO/n)==v for n,v in core_kit['source_core_sha256'].items())
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
baseline = next(f for f in kit['files'] if f['variant']=='baseline')
binary = {'baseline.exe':baseline['sha256'],'candidate147.exe':candidate['useful_executable']['sha256']}
policy = {'trial':148,'declared_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,
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
 'new_protocol':'One owned persistent PowerShell metadata worker blocks on stdin between requests; identical reset/task/supervisor/global-build checks before/after every native case and during120-second continuous quiet window. Worker does no probe during native lifetime and must actually exit0 after all cases. Busy before a timer waits120 continuous clear seconds. Busy after a completed native child can wait ONLY if every observed blocker began after child exit+100ms and after the post-probe began; possible overlap rejects entire prefix. All samples/cases kept exactly once, no metric-dependent selection. No engine/numerical gate/input reduction; waits/startup outside compaction clock. Bounded nonsecret blocker reasons retained; no command-line dumping.',
 'timer':'Instant around entire Archive.compact_small; preparation begins at input CRC/read/collection. Setup, native verification/pins/reclaim/reopen outside timer.',
 'environment_limits':'Other local development/server apps remain running; no app stopped. Reset/task work and visible build checks required before timing and before and after each actual native case. A/A controls decide qualification; snapshots cannot exclude every brief background task.',
 'storage':'Concise private Markdown outcomes/failures and useful source, fresh byte-exact remote verification, then native scoped completed fixture cleanup; no raw bundle.'}
policy['kind']='Complete Archive compaction: supported016 identical A/B versus JOINT131+144+147 C'
policy['hypothesis']='147 reuses CRC output bytes once during eligible compaction with checked total actual Vec byte capacity<=1MiB, dropping all retention on overflow/overbudget and using original stream.131 selects ordered concatenation or bounded merge from charged input disorder;144 reduces existing block extrema. Original64KiB writer, all input/readCRC/phase/index/write/flush/sync, both explicit syncs, format, receipts/ACK and cutpoints remain. This compares JOINT131+144+147 against supported016, not isolated147 versus144; it cannot qualify release/service by itself.'
policy['metrics']=['wall_ms','prepare_ms','segment_write_ms','segment_sync_ms','catalog_sync_ms','write_sync_ms','wall_p95_ms','setup_p95_ms']
policy['goals']={'clustered_wall_ms_max_ratio':.95,'clustered_prepare_ms_max_ratio':.90}
policy['prerequisites_reused']={'baseline016_tests':154,'candidate147_tests':348,'candidate_strict_lints':2,'new_Rust_build_or_tests':0,'baseline_source_commit':kit['source_private_commit'],'candidate_source_commit':candidate['source_private_commit'],'candidate_independent_stores':52,'candidate_supported016_wire_pairs':6,'candidate_recovery_cases':14,'candidate_recovery_commands':56}
policy['quantile_guards']='For wall/setup p95, nearest-rank quantile ratio B/A and C/A in full and both halves; controls[.90,1.10], guard<=1.10. With12/full or6/half samples, p95 equals max; retain every stall, no outlier removal. Other metrics use median within-round ratios. This adds tail/write/setup guards; original release gates unchanged.'
policy['component_checks']={'AA':144,'guards':144,'clustered_goals':6}
policy['supplemental_independent_checks']={'all_probe_intervals_against_every_native_lifetime':True,'receipt_generations_from_declared_run_plus_one_not_stdout':True,'all_controller_and_decoder_sources_frozen':True}
W.mkdir(); (W/'policy.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8')
(W/'declaration-proof.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(W/'policy.json'),'before_binary_copy_or_smoke':True,'no_timer_started':True},indent=2)+'\n',encoding='utf-8')
for n in ['binary','logs','tmp']: (W/n).mkdir()
for src,dest in [(R/'compaction-kit-122/baseline.exe',W/'binary/baseline.exe'),(R/'compaction-kit-147/candidate147.exe',W/'binary/candidate147.exe')]:
    assert sha(src)==binary[dest.name]; shutil.copy2(src,dest); assert sha(dest)==binary[dest.name]
ast.parse((R/'run_phase_compare_148.py').read_text(encoding='utf-8'))
ast.parse((R/'audit_phase_compare_148.py').read_text(encoding='utf-8'))
for n in ['prepare_phase_compare_148.py', 'run_phase_compare_148.py', 'audit_phase_compare_148.py', 'smoke_phase_compare_148.py', 'activity_worker_148.ps1', 'launch_phase_compare_148.ps1', 'append_phase148_declared.py', 'derive_payload_compare_148.py', 'audit_lifecycle_receipts_148.py', 'launch_preflight_phase148.ps1', 'launch_audits_phase148.ps1', 'archive_audit_099.py']:
    shutil.copy2(R/n,W/n)
(W/'preparation-proof.json').write_text(json.dumps({'complete':True,'policy_sha256':sha(W/'policy.json'),'binary_sha256':binary,'new_Rust_build_or_tests':0,'same_driver_both_artifacts':True,'no_timer_started':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'declared_and_prepared':True,'trial':148,'cases':216,'fresh_Rust_tests':0,'all_prerequisites_explicitly_reused':True,'no_timer_started':True}))
