"""Post-cohort descriptive stages, client tails and recorded resource bounds."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, statistics

W=Path('D:/Codex/Kestrel/work/perf-086')
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert load(W/'post-timing-process-check.json')['active_processes']==[]
a=load(W/'audit.json');r=load(W/'paired-service.json')
assert a['report_sha256']==sha(W/'paired-service.json') and not a['scoped_advance_passed']
rows=[]
for profile in ['read','write','mixed']:
    for variant in ['baseline_a','baseline_b','candidate']:
        selected=[s for s in a['publication_stage_deltas'] if s['profile']==profile and s['variant']==variant]
        names=list(selected[0]['stages'])
        sums={n:sum(s['stages'][n]['total_ms'] for s in selected) for n in names}
        total=sum(sums.values())
        fraction=(sums['segment_sync']+sums['catalog_sync'])/total if total else None
        cases=[c for c in r['cases'] if c['profile']==profile and c['variant']==variant]
        resources=[]
        for c in cases:
            av=[s['physical_available_bytes'] for s in c['host_telemetry']['samples'] if 'physical_available_bytes' in s]
            resources.append({'case_index':c['case_index'],'host_available_min_bytes':min(av) if av else None,
                'host_available_max_bytes':max(av) if av else None,'host_telemetry_error':c['host_telemetry']['error'],
                'live_state':c['live_state_before_reopen']})
        rows.append({'profile':profile,'variant':variant,'summed_recorded_stage_ms':sums,
            'synchronization_fraction_of_summed_seven_stage_time':fraction,
            'attempts':sum(s['attempts'] for s in selected),'compactions':sum(s['compactions'] for s in selected),
            'resources':resources})
doc={'trial':86,'derived_utc':datetime.now(timezone.utc).isoformat(),'audit_sha256':sha(W/'audit.json'),
     'posthoc_diagnostic_only':True,'rows':rows,'limits':[
     'Stage totals include appends and compactions; synchronization fractions are sums, not a p99 decomposition or physical cause.',
     'Client dispatch and response quantiles are separate; their quantiles must not be added.',
     'Whole-host memory is sampled; native logical index/queue/live-state bounds are retained. Process peak RSS was not measured.',
     'The clean-core candidate changes the query parser, not publication policy. A calibrated regression is evidence to investigate, not proof the parser causes storage tails.']}
(W/'publication-diagnostic.json').write_text(json.dumps(doc,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'write_diagnostics':[{'variant':v['variant'],'sync_fraction':v['synchronization_fraction_of_summed_seven_stage_time'],
                  'stages_ms':v['summed_recorded_stage_ms'],'attempts':v['attempts'],'compactions':v['compactions']} for v in rows if v['profile']=='write'],
                  'whole_host_memory_and_live_bounds_retained':True},indent=2))
