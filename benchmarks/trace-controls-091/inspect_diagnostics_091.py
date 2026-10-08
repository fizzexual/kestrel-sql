"""Summarize every retained maintenance event and tail-associated append group."""
from pathlib import Path
import gzip
import hashlib
import json
import math
import statistics

W = Path('D:/Codex/Kestrel/work/perf-091')
def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def q(v,f):
    return sorted(v)[max(0,math.ceil(len(v)*f)-1)] if v else None
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()
def dist(v):
    return {'count':len(v),'p50':q(v,.5),'p95':q(v,.95),'p99':q(v,.99),'max':max(v,default=None),'sum':sum(v)}

a, run, d = load(W/'audit.json'), load(W/'paired-service.json'), load(W/'trace-group-diagnostics.json')
assert a['all_required_scopes_passed'] and a['traced_requests_correlated'] == d['traced_requests']
events = {k:[] for k in ['append','compact','reclaim']}
slow = []
stages = [[] for _ in range(7)]
for case in run['cases']:
    trace = case['post_load_diagnostic']['trace']
    if trace is None:
        continue
    for event in trace['events']:
        duration = (event['end_ns']-event['start_ns'])/1e6
        events[event['kind']].append(duration)
        if duration>100:
            slow.append({'case_index':case['case_index'],'round':case['round'],**event,'duration_ms':duration})
        if event['publication']:
            for i,v in enumerate(event['publication']['stage_ms']):
                stages[i].append(v)
write_cases = [c for c in d['cases'] if c['profile']=='write']
tails = [g for g in d['append_group_records'] if g['associated_service_samples_over_100ms']]
previous_counts = {k:sum(g['previous_recorded_event_kind']==k for g in tails) for k in ['append','compact','reclaim',None]}
bykind = {k:sum(e['kind']==k for e in slow) for k in events}
scope_summary = [{'scope':s['scope'],'passed':s['passed'],'summaries':[
    {'profile':r['profile'],'A':r['variants']['baseline_a']['median_case_p99_ms'],
     'C':r['variants']['candidate']['median_case_p99_ms'],
     'BA':{k:v['median'] for k,v in r['comparisons']['identity_b_over_a']['paired_ratios'].items()},
     'CA':{k:v['median'] for k,v in r['comparisons']['primary_candidate_over_a']['paired_ratios'].items()},
     'median_peak_difference_bytes':r['comparisons']['primary_candidate_over_a']['median_peak_difference_bytes']}
    for r in s['summaries']]} for s in a['scopes']]
worst = max(run['cases'],key=lambda c:c['latency_ms']['p99'])
result={'post_cohort_descriptive_only':True,'no_gate_changes_native_or_timing_runs':True,
    'not_exclusive_p99_or_disk_cause':True,'raw_report_sha256':sha(W/'paired-service.json'),
    'diagnostic_sha256':sha(W/'trace-group-diagnostics.json'),
    'every_trace_event_duration_ms':{k:dist(v) for k,v in events.items()},
    'recorded_publication_stage_ms':{k:dist(v) for k,v in zip(
        ['prepare','segment_write','segment_sync','catalog_encode','catalog_write','catalog_sync','catalog_rename'],stages)},
    'slow_native_event_counts':bykind,'all_native_events_over_100ms':slow,
    'tail_append_groups_by_immediately_previous_event_kind':{str(k):v for k,v in previous_counts.items()},
    'all_tail_append_groups':tails,
    'write_case_sync_fraction_of_summed_recorded_stages':{
        'min':min(c['sync_fraction_of_summed_publication_stage_time'] for c in write_cases),
        'median':statistics.median(c['sync_fraction_of_summed_publication_stage_time'] for c in write_cases),
        'max':max(c['sync_fraction_of_summed_publication_stage_time'] for c in write_cases)},
    'median_write_case_native_event_p99_ms':{k:statistics.median(c['native_event_p99_ms'][k] for c in write_cases) for k in events},
    'worst_service_case':{k:worst[k] for k in ['case_index','round','profile','variant','binary','latency_ms','operation_latency_ms']},
    'compact_source_sha256':sha(W/'sources/restored/src/archive.rs'),
    'live_source_sha256':sha(W/'sources/restored/src/live.rs'),
    'scope_summary':scope_summary}
target=W/'bottleneck-summary.json'
assert not target.exists()
target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['all_native_events_over_100ms','all_tail_append_groups','scope_summary','recorded_publication_stage_ms']},indent=2))
