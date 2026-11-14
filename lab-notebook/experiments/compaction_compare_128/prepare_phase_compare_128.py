"""Declare one complete comparison of supported016 and the exact phase127 binary."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, itertools, json, platform, random, shutil, subprocess
R = Path('D:/Codex/Kestrel/work'); W = R / 'perf-128'; REPO = R.parent / 'outputs/kestrel-sql'
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
assert not W.exists()
git = ['git', '--no-optional-locks', '-c', 'safe.directory='+REPO.as_posix(), '-c', 'gc.auto=0', '-C', str(REPO)]
assert not subprocess.check_output(git+['status', '--porcelain=v1', '--untracked-files=all']).strip()
head = subprocess.check_output(git+['rev-parse', 'HEAD'], text=True).strip()
assert head == '8e9e5fafcf79a68b43a01aa1acee92b0f039c010'
kit = load(R/'compaction-kit-122/provenance.json'); candidate = load(R/'compaction-kit-127/provenance.json')
assert all(sha(REPO/n)==v for n,v in kit['source_core_sha256'].items())
assert load(R/'phase127-storage-cleanup-proof.json')['completed127_test_stores_and_build_outputs_closed']
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
binary = {'baseline.exe':baseline['sha256'],'candidate127.exe':candidate['useful_executable']['sha256']}
policy = {'trial':128,'declared_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,
 'kind':'Archive component comparison: identical supported016 A/B versus exact phase127 C',
 'hypothesis':'Deriving ordered concatenation while collecting CRC-validated inputs avoids late merge probing for ordered input; bounded merge retains clustered preparation gains without material regressions. All phase selection/input work is inside the existing compaction clock. This tests the combined127 implementation versus016, not isolated caller effect versus122.',
 'component_configs':configs,'cases':cases,'rounds':12,'schedule_rng':'Python random.Random(20261011), fixed before timing; all six permutations once per workload per half',
 'affinity_mask':256,'cooldown_seconds':120,'AA_lower':.9,'AA_upper':1.1,'candidate_guard_upper':1.1,
 'scopes':['full','first_half','second_half'],'metrics':['wall_ms','prepare_ms','segment_sync_ms','catalog_sync_ms'],
 'goals':{'clustered_wall_ms_max_ratio':.95,'clustered_prepare_ms_max_ratio':.90},
 'runs_per_case':32,'rows_per_run':1024,'columns':3,'same_original_driver':True,'binary_sha256':binary,
 'prerequisites_reused':{'baseline_tests':154,'candidate_tests':336,'candidate_strict_lints':2,'new_Rust_build_or_tests':0,'candidate_source_commit':candidate['source_private_commit']},
 'unchanged_release_gates':{'Native':324,'service':252,'goals':42,'AA':153,'guards':171},
 'same_physical_D':True,'resource_bound_bytes':600_000_000,'timeout_seconds':90,'no_selected_retiming':True,
 'no_global_CPU_power_ASLR_or_security_change':True,'platform':platform.platform(),
 'timer':'Instant around entire Archive.compact_small; preparation begins at input CRC/read/collection. Setup, native verification/pins/reclaim/reopen outside timer.',
 'environment_limits':'Other local development/server apps remain running; no app stopped. Reset/task work and visible build checks required before timing and each complete round. A/A controls decide qualification; snapshots cannot exclude every brief background task.',
 'storage':'Concise private Markdown outcomes/failures and useful source, fresh byte-exact remote verification, then native scoped completed fixture cleanup; no raw bundle.'}
W.mkdir(); (W/'policy.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8')
(W/'declaration-proof.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(W/'policy.json'),'before_binary_copy_or_smoke':True,'no_timer_started':True},indent=2)+'\n',encoding='utf-8')
for n in ['binary','logs','tmp']: (W/n).mkdir()
for src,dest in [(R/'compaction-kit-122/baseline.exe',W/'binary/baseline.exe'),(R/'compaction-kit-127/candidate127.exe',W/'binary/candidate127.exe')]:
    assert sha(src)==binary[dest.name]; shutil.copy2(src,dest); assert sha(dest)==binary[dest.name]
code=(R/'run_controls_125.py').read_text(encoding='utf-8').replace('perf-125','perf-128')
code=code.replace("files={'policy.json':sha(W/'policy.json'),'binary/compaction_stage_121.exe':sha(W/'binary/compaction_stage_121.exe')}\nassert files['binary/compaction_stage_121.exe']==policy['actual_binary_sha256']", "files={'policy.json':sha(W/'policy.json')}\nfiles.update({'binary/'+n:sha(W/'binary'/n) for n in policy['binary_sha256']})\nassert all(files['binary/'+n]==h for n,h in policy['binary_sha256'].items())\nassert load(W/'smoke-proof.json')['complete']")
code=code.replace("current=sum(p.stat().st_size", "helper=Path('D:/Codex/Migration-20261007/fresh-profile-20261008/fresh_reset.ps1')\nassert sha(helper)=='005d2246f6948eb9d2cef36a9169d9bcd82c9289c9bb0c5f7565fdae79b27e3b'\nfor source in ['run_phase_compare_128.py','audit_phase_compare_128.py','check_round_activity_128.ps1','launch_phase_compare_128.ps1']:\n    assert sha(R/source)==sha(W/source)\n    files[source]=sha(W/source)\ncurrent=sum(p.stat().st_size")
code=code.replace("current+len(policy['cases'])*2_000_000<8_000_000_000", "current+len(policy['cases'])*2_000_000<policy['resource_bound_bytes']")
code=code.replace("'all_three_labels_same_supported016_binary':True", "'A_and_B_same_supported016_binary':True,'candidate_exact_phase127':True")
code=code.replace("for spec in policy['cases']:", "for spec in policy['cases']:\n        if spec['index']%18==0:\n            times=[wintypes.FILETIME() for _ in range(4)]\n            assert k.GetProcessTimes(own,*(ctypes.byref(t) for t in times))\n            creation=times[0].dwLowDateTime+(times[0].dwHighDateTime<<32)\n            checked=subprocess.run(['D:/Codex/Migration-20261007/helper-runtime/powershell/pwsh.exe','-NoProfile','-File',str(R/'check_round_activity_128.ps1'),'-OwnerPid',str(os.getpid()),'-OwnerCreationFileTime',str(creation)],capture_output=True,timeout=20)\n            with (W/'round-build-checks.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps({'utc':utc(),'before_index':spec['index'],'exit':checked.returncode,'stdout':checked.stdout.decode('utf-8-sig'),'stderr':checked.stderr.decode('utf-8-sig')})+'\\n')\n            assert checked.returncode==0,('Reset/task/build activity: stop with preserved prefix; no retiming',checked.stdout[-1000:],checked.stderr[-1000:])")
code=code.replace("argv=[str(W/'binary/compaction_stage_121.exe'),", "binary=W/'binary'/('candidate127.exe' if spec['variant']=='candidate' else 'baseline.exe')\n        argv=[str(binary),")
code=code.replace("'total':648", "'total':216").replace("'all_variants_supported016_no_candidate':True", "'A_B_identical_supported016_and_C_exact_phase127':True")
code=code.replace("assert all(sha(W/n)==v for n,v in files.items())", "assert len(completed)==216\n    assert all(sha(W/n)==v for n,v in files.items())")
code=code.replace("(W/'cohort-completion.json').write_text", "assert all(sha(R/n)==files[n] for n in ['run_phase_compare_128.py','audit_phase_compare_128.py','check_round_activity_128.ps1','launch_phase_compare_128.ps1'])\n    (W/'cohort-completion.json').write_text")
ast.parse(code); (R/'run_phase_compare_128.py').write_text(code,encoding='utf-8',newline='\n')
audit=(R/'audit_component_122.py').read_text(encoding='utf-8').replace('perf-122','perf-128')
audit=audit.replace("result=load(W/case['stdout']);assert result['component_only'] and result['all_checks_passed']", "result=load(W/case['stdout']);assert result['component_only'] and result['all_checks_passed']\n    assert result['workload']==spec['name'] and result['seed']==spec['seed'] and case['identity']['affinity_mask']==256")
ast.parse(audit); (R/'audit_phase_compare_128.py').write_text(audit,encoding='utf-8',newline='\n')
for n in ['prepare_phase_compare_128.py','run_phase_compare_128.py','audit_phase_compare_128.py','smoke_phase_compare_128.py','check_round_activity_128.ps1','launch_phase_compare_128.ps1','wait_start_phase128.ps1','wait_start_phase128_v2.ps1','append_phase128_declared.py']:
    shutil.copy2(R/n,W/n)
(W/'preparation-proof.json').write_text(json.dumps({'complete':True,'policy_sha256':sha(W/'policy.json'),'binary_sha256':binary,'new_Rust_build_or_tests':0,'same_driver_both_artifacts':True,'no_timer_started':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'declared_and_prepared':True,'trial':128,'cases':216,'fresh_Rust_tests':0,'all_prerequisites_explicitly_reused':True,'no_timer_started':True}))
