"""Fresh135 isolates writer134 versus131, retaining the complete133 safety protocol."""
from pathlib import Path
import ast,hashlib,json
R=Path('D:/Codex/Kestrel/work')
assert not (R/'perf-135').exists()
def renamed(s):return s.replace('133','135').replace('candidate131.exe','candidate134.exe')
def save(name,text):
    assert not (R/name).exists(),name
    if name.endswith('.py'):ast.parse(text)
    (R/name).write_text(text,encoding='utf-8',newline='\n')
parents={}
for old in ['run_phase_compare_133.py','activity_worker_133.ps1','smoke_phase_compare_133.py']:
    text=renamed((R/old).read_text(encoding='utf-8'))
    text=text.replace('A_and_B_same_supported016_binary','A_and_B_same_exact131_binary').replace('candidate_exact_phase131','candidate_exact_write134').replace('A_B_identical_supported016_and_C_exact_phase131','A_B_identical131_and_C_exact_write134')
    save(old.replace('133','135'),text);parents[old]=hashlib.sha256((R/old).read_bytes()).hexdigest()
prepare=renamed((R/'prepare_phase_compare_133.py').read_text(encoding='utf-8'))
prepare=prepare.replace("load(R/'phase132-storage-cleanup-proof.json')['completed132_prefix_stores_closed'] and not (R/'perf-132').exists()","load(R/'write134-storage-cleanup-proof.json')['completed134_stores_and_regenerable_builds_closed'] and not (R/'perf-134').exists()")
prepare=prepare.replace("head == load(R/'phase132-publication-proof.json')['private_main']","head == load(R/'write134-publication-proof.json')['private_main']")
prepare=prepare.replace("kit = load(R/'compaction-kit-122/provenance.json'); candidate = load(R/'compaction-kit-131/provenance.json')","core_kit = load(R/'compaction-kit-122/provenance.json'); kit = load(R/'compaction-kit-131/provenance.json'); candidate = load(R/'compaction-kit-134/provenance.json')")
prepare=prepare.replace("kit['source_core_sha256']","core_kit['source_core_sha256']")
prepare=prepare.replace("baseline = next(x for x in kit['files'] if x['variant']=='baseline')","baseline = kit['useful_executable']")
prepare=prepare.replace("R/'compaction-kit-122/baseline.exe'","R/'compaction-kit-131/candidate131.exe'")
prepare=prepare.replace("R/'compaction-kit-131/candidate134.exe'","R/'compaction-kit-134/candidate134.exe'")
marker="W.mkdir(); (W/'policy.json')"
assert prepare.count(marker)==1
add="""policy['kind']='Isolated writer comparison: exact131 A/B versus exact134 C'
policy['hypothesis']='133 largest tails were inside sync intervals. Bounded Windows compaction write-through/coalescing may reduce total segment write+sync and whole compaction without median/tail/setup regressions; it may instead move/worsen cost. Exact same driver and all inputCRC/read/phase/index/write/sync costs remain charged. Compare131 versus134 to isolate writer mode; this is not supported016 whole-engine qualification.'
policy['metrics']=['wall_ms','prepare_ms','segment_write_ms','segment_sync_ms','catalog_sync_ms','write_sync_ms','wall_p95_ms','setup_p95_ms']
policy['goals']={'clustered_wall_ms_max_ratio':.95,'clustered_write_sync_ms_max_ratio':.90}
policy['prerequisites_reused']={'baseline131_tests':340,'candidate134_tests':344,'candidate_strict_lints':2,'new_Rust_build_or_tests':0,'baseline_source_commit':kit['source_private_commit'],'candidate_source_commit':candidate['source_private_commit'],'candidate_legacy_wire_pairs':6,'candidate_recovery_cases':14}
policy['quantile_guards']='For wall/setup p95, nearest-rank quantile ratio B/A and C/A in full and both halves; controls[.90,1.10], guard<=1.10. With12/full or6/half samples, p95 equals max; retain every stall, no outlier removal. Other metrics use median within-round ratios. This adds tail/write/setup guards; original release gates unchanged.'
policy['component_checks']={'AA':144,'guards':144,'clustered_goals':6}
"""
prepare=prepare.replace(marker,add+marker,1)
save('prepare_phase_compare_135.py',prepare)
audit=renamed((R/'audit_phase_compare_133.py').read_text(encoding='utf-8'))
audit=audit.replace("metrics[(spec['name'],spec['variant'],spec['round'])]=values","values['write_sync_ms']=stages['segment_write']+stages['segment_sync']\n    metrics[(spec['name'],spec['variant'],spec['round'])]=values")
audit=audit.replace("for metric in ['wall_ms','prepare_ms','segment_sync_ms','catalog_sync_ms']:","for metric in policy['metrics']:\n            source_metric=metric.replace('_p95_ms','_ms')")
audit=audit.replace("metrics[(name,v,r)][metric]","metrics[(name,v,r)][source_metric]")
old="aa=statistics.median(y/x for x,y in zip(a,b));ca=statistics.median(y/x for x,y in zip(a,c))"
new="""if metric.endswith('_p95_ms'):
                aa=nearest(b,.95)/nearest(a,.95);ca=nearest(c,.95)/nearest(a,.95)
            else:aa=statistics.median(y/x for x,y in zip(a,b));ca=statistics.median(y/x for x,y in zip(a,c))"""
assert audit.count(old)==1;audit=audit.replace(old,new,1)
audit=audit.replace("metric in ['wall_ms','prepare_ms']","metric in ['wall_ms','write_sync_ms']")
audit=audit.replace("summaries.append(row)","row['ratio_method']='nearest-rank p95 C/A and B/A' if metric.endswith('_p95_ms') else 'median within-round ratios'\n            summaries.append(row)")
audit=audit.replace("assert not (W/'audit.json').exists();","assert len(summaries)==144 and sum('goal_pass' in s for s in summaries)==6\nassert not (W/'audit.json').exists();")
save('audit_phase_compare_135.py',audit)
launch=renamed((R/'launch_phase_compare_133.ps1').read_text(encoding='utf-8'))
marker="if($LASTEXITCODE -ne 0){throw 'Checkpoint failed before timing'}"
assert launch.count(marker)==1
launch=launch.replace(marker,marker+"\n& 'D:\\Codex\\Kestrel\\work\\guard_cleanup_20261010.ps1' -Phase pretime *> 'D:\\Codex\\Kestrel\\work\\phase135-pretime-guard.log'\nif(-not $? -or $LASTEXITCODE -eq 3){throw 'Task/reset pretime guard held'}\n& 'D:\\Codex\\Kestrel\\work\\check_global_build_activity.ps1' *> 'D:\\Codex\\Kestrel\\work\\phase135-pretime-global.log'\nif(-not $? -or $LASTEXITCODE -eq 3){throw 'Global build before timing'}",1)
save('launch_phase_compare_135.ps1',launch)
parents['prepare_phase_compare_133.py']=hashlib.sha256((R/'prepare_phase_compare_133.py').read_bytes()).hexdigest()
parents['audit_phase_compare_133.py']=hashlib.sha256((R/'audit_phase_compare_133.py').read_bytes()).hexdigest()
(R/'write135-controller-derivation.json').write_text(json.dumps({'parent_sha256':parents,'only_new_ids_baseline_candidate_provenance_and_predeclared_metrics_goals_changed':True,'same_complete_safety_and_lifecycle_protocol':True,'release_gates_unchanged':True,'no_case_timed':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print('135 controllers prepared; safety protocol retained, write+sync and tail guards predeclared')
