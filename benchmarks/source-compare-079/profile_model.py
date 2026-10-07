"""Post-timing descriptive profiles; no gates amended and no case dropped."""
import json,statistics
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
a=load(W/'model-audit.json');assert a['complete'] and not load(W/'post-timing-process-check.json')['active_processes']
groups=[];pubs=[];opens=[]
for case in a['cases']:
    x=load(W/'raw'/f"{case['label']}.stdout.json")
    for s in x['samples']:
        io=s['io'];pubs.append({'label':case['label'],'spec':case['spec'],**s,'unattributed_outer_ms':s['outer_ms']-sum(io[k] for k in ['encode_ms','write_ms','sync_ms','rename_ms'])})
    for r in x['fresh_recovery']:opens.append({'label':case['label'],'spec':case['spec'],**r})
for summary in a['summaries']:
    seed=summary['seed_receipts'];group={'seed_receipts':seed,'actual_receipts':summary['actual_receipts'],'variants':{},'per_metric_rounds_candidate_below_control_a':{}}
    for variant in ['baseline_a','baseline_b','hybrid']:
        selected=[p for p in pubs if p['spec']['seed_receipts']==seed and p['spec']['variant']==variant]
        by_case=[c for c in a['cases'] if c['spec']['seed_receipts']==seed and c['spec']['variant']==variant]
        outer=sum(p['outer_ms'] for p in selected)
        stages={k:sum(p['io'][k] for p in selected) for k in ['encode_ms','write_ms','sync_ms','rename_ms']}
        stages['unattributed_outer_ms']=sum(p['unattributed_outer_ms'] for p in selected)
        group['variants'][variant]={'publication_stage_totals_ms':stages,'stage_fraction_of_all_publication_ms':{k:v/outer for k,v in stages.items()},'total_publication_ms':outer,
            'ordinary_sum_ms':sum(p['outer_ms'] for p in selected if not p['source_interval']),
            'source_sum_ms':sum(p['outer_ms'] for p in selected if p['source_interval']),
            'noncheckpoint_sum_ms':sum(p['outer_ms'] for p in selected if not p['checkpoint']),
            'checkpoint_sum_ms':sum(p['outer_ms'] for p in selected if p['checkpoint']),
            'full_case_peak_memory_bytes':{k:statistics.median(c[k] for c in by_case) for k in ['peak_working_set_bytes','peak_commit_bytes']},
            'retained_bytes_per_case':by_case[0]['stored_directory_bytes'],'reachable_bytes_per_case':by_case[0]['current_reachable_bytes'],
            'all_64_publications_and_migration_syncs_per_case':{'publication':66,'migration':1}}
    group['per_metric_rounds_candidate_below_control_a']={metric:sum(p['candidate_a'][metric]<1 for p in summary['pairs']) for metric in summary['median_paired_ratios']['candidate_a']}
    groups.append(group)
result={'complete':True,'profiled_utc':datetime.now(timezone.utc).isoformat(),'post_timing_only':True,'all_3456_publications_included':True,'all_648_recoveries_included':True,'groups':groups,
    'top_25_publications':sorted(pubs,key=lambda p:p['outer_ms'],reverse=True)[:25],
    'top_25_recoveries':sorted(opens,key=lambda p:p['recovery_ms'],reverse=True)[:25],
    'publication_above_500ms':sum(p['outer_ms']>500 for p in pubs),
    'unattributed_outer_explanation':'Outer minus encode/write/sync/rename includes batch/digest/source validation and state installation and other model overhead; no physical cause or CPU attribution established.',
    'no_hardware_cause_or_general_engine_speed_claim':True,'failed_policy_checks_unchanged':a['failed_checks']}
save(W/'bottleneck-profile.json',result)
print(json.dumps({'complete':True,'above500ms':result['publication_above_500ms'],'largest_publication_ms':result['top_25_publications'][0]['outer_ms'],'largest_publication_case':result['top_25_publications'][0]['label'],
    'large_anchor_round_wins':[(g['actual_receipts'],g['per_metric_rounds_candidate_below_control_a']['anchor31_p50_ms'],g['per_metric_rounds_candidate_below_control_a']['anchor31_p99_ms']) for g in groups if g['seed_receipts']]}))
