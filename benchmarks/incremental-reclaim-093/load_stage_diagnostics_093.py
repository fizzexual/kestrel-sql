"""Post-cohort descriptive publication analysis. No exclusions, Native, timers or cause claim."""
from pathlib import Path
import hashlib,json,statistics
ROOT=Path('D:/Codex/Kestrel');W=ROOT/'work/perf-093'
source=W/'loss-aware-audit.json';a=json.loads(source.read_text())
report=json.loads((W/'paired-service.json').read_text())
assert a['failed_experiment_audit_passed'] and len(report['cases'])==144
rows=[]
for d,c in zip(a['publication_stage_diagnostics'],report['cases']):
    assert d['case_index']==c['case_index']
    stage=d['stage_total_ms_after_subtracting_seed'];total=sum(stage.values());sync=stage['segment_sync']+stage['catalog_sync']
    rows.append({**d,'sum_seven_stages_ms':total,'sum_two_sync_stages_ms':sync,'sync_share_of_summed_stages':sync/total if total else None,
        'append_publication_total_ms':c['live_state_before_reopen']['ingest']['publication_total_ms'],
        'compaction_total_ms':c['live_state_before_reopen']['ingest']['compaction_total_ms'],
        'append_ms_per_durable_group_mean_not_tail':c['live_state_before_reopen']['ingest']['publication_total_ms']/d['durable_groups'] if d['durable_groups'] else None,
        'ACK_requests_per_durable_group_mean':c['write_successes']/d['durable_groups'] if d['durable_groups'] else None,
        'overall_successful_p99_ms':c['latency_ms']['p99'],'append_successful_p99_ms':c['operation_latency_ms']['append']['p99']})
summaries=[]
for variant in ['baseline_a','baseline_b','candidate']:
    chosen=[r for r in rows if r['profile']=='write' and r['variant']==variant]
    total=sum(r['sum_seven_stages_ms'] for r in chosen);sync=sum(r['sum_two_sync_stages_ms'] for r in chosen)
    summaries.append({'variant':variant,'cases':len(chosen),'lost':sum(r['lost'] for r in chosen),
        'median_case_mean_append_publication_ms':statistics.median(r['append_ms_per_durable_group_mean_not_tail'] for r in chosen),
        'median_case_mean_ACKs_per_group':statistics.median(r['ACK_requests_per_durable_group_mean'] for r in chosen),
        'median_case_sync_share':statistics.median(r['sync_share_of_summed_stages'] for r in chosen),
        'sync_share_of_all_summed_stages':sync/total,'all_round_indices_retained':[r['case_index'] for r in chosen]})
result={'trial':93,'post_cohort_diagnostic_only':True,'no_native_launches_or_timing_reruns':True,
    'source_audit_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'all_144_cases':rows,'write_summaries':summaries,
    'no_qualified_speed_gain_or_exclusive_engine_disk_OS_cause':True,
    'seed_subtracted_totals_are_not_load_stage_maxima_or_per_group_quantiles':True,
    'no_samples_or_failures_excluded':True,
    'next_hypothesis':'Separate load publication stalls and queue backlog using bounded per-group diagnostics with fresh overhead controls and actual cut-point recovery before another writer change; preserve all synchronization/ACK contracts.'}
out=ROOT/'work/load-stage-diagnostics-093.json';assert not out.exists()
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(summaries),flush=True)
