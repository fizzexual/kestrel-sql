"""Independent per-event/stage conservation and retained-store verification."""
from collections import Counter
from datetime import datetime, timezone
import hashlib, json, math, statistics
from pathlib import Path
W=Path(__file__).resolve().parent
STAGES=['prepare','segment_write','segment_sync','catalog_encode','catalog_write','catalog_sync','catalog_rename']
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def quantile(xs,p):
    values=sorted(xs);index=(len(values)-1)*p;lo=math.floor(index);hi=math.ceil(index)
    return values[lo]+(values[hi]-values[lo])*(index-lo)
def summarise(events):
    values=[e['outer_ms'] for e in events];slow=[e for e in events if e['outer_ms']>500]
    summed=[sum(e['trace']['stage_ms'][i] for e in events) for i in range(7)]
    outer=sum(values)
    return {'count':len(events),'outer_total_ms':outer,'p50_ms':quantile(values,.5),'p99_ms':quantile(values,.99),'max_ms':max(values),
        'slow_over_500ms':len(slow),'stage_total_ms':dict(zip(STAGES,summed)),
        'sync_fraction_of_outer':(summed[2]+summed[5])/outer,
        'encode_fraction_of_outer':summed[3]/outer,'residual_fraction_of_outer':(outer-sum(summed))/outer,
        'largest_measured_stage_counts_slow':dict(Counter(STAGES[max(range(7),key=lambda i:e['trace']['stage_ms'][i])] for e in slow)),
        'strict_majority_stage_counts_slow':dict(Counter(STAGES[i] for e in slow for i in range(7) if e['trace']['stage_ms'][i]>.5*e['outer_ms']))}
p=load(W/'diagnostic-policy.json');r=load(W/'diagnostic-results.json')
assert r['complete'] and not r['failures'] and len(r['cases'])==6
assert p['independent_auditor_sha256']==sha(Path(__file__)) and r['policy_sha256']==sha(W/'diagnostic-policy.json')
assert len(p['cases'])==6 and [x['spec'] for x in r['cases']]==p['cases']
assert not load(W/'post-timing-process-check.json')['active_processes']
cases=[];all_events=[];all_reclaims=[];slow_events=[];inventory=[];store_contents={};crc=0
for c in r['cases']:
    raw=W/'diagnostic-raw';label=c['label'];spec=c['spec']
    for suffix,key in [('stdout.json','stdout_sha256'),('status.json','status_sha256'),('stderr.txt','stderr_sha256')]:assert sha(raw/f'{label}.{suffix}')==c[key]
    status=load(raw/f'{label}.status.json');x=load(raw/f'{label}.stdout.json');seed=spec['seed_receipts']
    assert status['exit_code']==0 and x['stage_names']==STAGES and x['repetitions']==128 and x['prefill_receipt_count']==seed
    assert all(x[k] for k in ['rows_and_sum_match','reopen_original_generations_retry_and_full_scrub_passed','cold_trace_and_retry_remain_empty','output_only_after_timed_calls','feature_overhead_unmeasured'])
    assert not x['performance_comparison'] and x['trace_option_bytes']<=192
    events=x['events'];assert len(events)==131
    append=[e for e in events if e['operation']=='append'];compact=[e for e in events if e['operation']=='compact']
    assert [e['batch'] for e in append]==list(range(128)) and [e['batch'] for e in compact]==[63,94,125]
    assert [e['after_batch'] for e in x['reclaim']]==[63,94,125]
    assert x['before']['rows']==seed and x['after']['rows']==seed+12800
    assert x['before']['recorded_batch_ids']==seed and x['after']['recorded_batch_ids']==seed+128
    initial=1 if seed else 0
    assert x['before']['publication_profile']['attempts']==initial
    for offset,e in enumerate(events,1):
        t=e['trace'];values=t['stage_ms'];outer=e['outer_ms']
        assert t['attempt']==t['generation']==initial+offset and t['completed']
        assert t['checkpoint']==((t['generation']-1)%32==0)
        assert t['receipt_base']==(None if t['checkpoint'] else t['generation']-1)
        assert all(math.isfinite(v) and v>=0 for v in [outer,*values])
        assert sum(values)<=outer+p['stage_sum_tolerance_ms']
        assert t['segment_payload_bytes']==t['rows']*24
        assert t['receipts_before']==seed+e['batch']+(1 if e['operation']=='compact' else 0)
        assert t['new_receipts']==(1 if e['operation']=='append' else 0)
        assert t['removed_segments']==(0 if e['operation']=='append' else 32)
        if e['operation']=='append':assert t['rows']==100
        if outer>500:
            largest=max(range(7),key=lambda i:values[i])
            slow_events.append({'label':label,'seed_receipts':seed,'round':spec['round'],'operation':e['operation'],'batch':e['batch'],
                'generation':t['generation'],'checkpoint':t['checkpoint'],'outer_ms':outer,
                'largest_measured_stage':STAGES[largest],'largest_stage_ms':values[largest],
                'largest_stage_fraction_of_outer':values[largest]/outer,'stage_ms':dict(zip(STAGES,values)),
                'unmeasured_residual_ms':max(0,outer-sum(values))})
    before=x['before']['publication_profile'];after=x['after']['publication_profile']
    assert after['attempts']-before['attempts']==after['completed']-before['completed']==131
    assert after['catalog_checkpoints']-before['catalog_checkpoints']==sum(e['trace']['checkpoint'] for e in events)
    assert after['catalog_deltas']-before['catalog_deltas']==sum(not e['trace']['checkpoint'] for e in events)
    assert after['catalog_bytes_published']-before['catalog_bytes_published']==sum(e['trace']['catalog_envelope_bytes'] for e in events)
    for i,stage in enumerate(STAGES):
        vals=[e['trace']['stage_ms'][i] for e in events]
        assert after[stage]['count']-before[stage]['count']==131
        assert math.isclose(after[stage]['total_ms']-before[stage]['total_ms'],sum(vals),rel_tol=1e-12,abs_tol=1e-6)
        histogram=[0]*8
        for v in vals:histogram[sum(v>limit for limit in [.1,1,5,20,100,500,1000])]+=1
        assert histogram==[a-b for a,b in zip(after[stage]['histogram'],before[stage]['histogram'])]
        maximum=max([*vals,*([x['seed_trace']['stage_ms'][i]] if initial else [])])
        assert math.isclose(maximum,after[stage]['max_ms'],rel_tol=1e-12,abs_tol=1e-6)
    directory=Path(status['fixture']);assert directory.is_dir()
    assert not list(directory.glob('*.pending'))
    files={f.name:{'size':f.stat().st_size,'sha256':sha(f)} for f in directory.glob('*.ks2')}
    assert files
    for e in events:
        name=f"catalog-{e['trace']['generation']:020}.ks2"
        if name in files:assert files[name]['size']==e['trace']['catalog_envelope_bytes']
    if seed in store_contents:assert files==store_contents[seed]
    else:store_contents[seed]=files
    inventory.append({'label':label,'seed_receipts':seed,'files':files,'bytes':sum(f['size'] for f in files.values())})
    summary={'label':label,'spec':spec,'append':summarise(append),'compact':summarise(compact),
             'reclaim_calls':len(x['reclaim']),'reclaim_total_ms':sum(e['outer_ms'] for e in x['reclaim']),
             'reclaim_max_ms':max(e['outer_ms'] for e in x['reclaim']),'reopen_ms':x['reopen_ms'],
             'crc_bytes_twice':(seed+12800)*24*2,'trace_option_bytes':x['trace_option_bytes']}
    crc+=summary['crc_bytes_twice'];cases.append(summary);all_events+=events;all_reclaims+=x['reclaim']
assert len(all_events)==786 and len(all_reclaims)==18 and crc==17990400
by_history=[]
for seed in [0,50000,99000]:
    chosen=[c for c in cases if c['spec']['seed_receipts']==seed]
    by_history.append({'seed_receipts':seed,'rounds':2,'append_p50_round_ms':[c['append']['p50_ms'] for c in chosen],
        'append_p99_round_ms':[c['append']['p99_ms'] for c in chosen],'append_max_round_ms':[c['append']['max_ms'] for c in chosen],
        'slow_append_count':sum(c['append']['slow_over_500ms'] for c in chosen),
        'slow_compact_count':sum(c['compact']['slow_over_500ms'] for c in chosen),
        'summary_is_descriptive_not_speedup':True})
a={'audited_utc':datetime.now(timezone.utc).isoformat(),'complete':True,'passed':True,'cases':cases,'by_history':by_history,
   'all_append':summarise([e for e in all_events if e['operation']=='append']),
   'all_compact':summarise([e for e in all_events if e['operation']=='compact']),
   'slow_events_over_500ms':slow_events,'reclaim_slow_over_500ms':sum(e['outer_ms']>500 for e in all_reclaims),
   'total_new_rows':76800,'publications_observed':786,'durable_retries':18,'crc_scrubbed_bytes':crc,
   'per_event_stage_profile_counts_totals_maxima_histograms_conserved':True,
   'all_six_final_store_files_checked_two_rounds_byte_identical':True,
   'file_instances':sum(len(s['files']) for s in inventory),'full_file_bytes':sum(s['bytes'] for s in inventory),
   'inventory_sha256':None,'native_067_is_prior_work_not_comparison':True,
   'feature_overhead_unmeasured':True,'no_speedup_competitor_production_or_physical_cause_claim':True,
   'diagnostic_policy_sha256':sha(W/'diagnostic-policy.json'),'results_sha256':sha(W/'diagnostic-results.json')}
save(W/'diagnostic-file-inventory.json',inventory);a['inventory_sha256']=sha(W/'diagnostic-file-inventory.json')
save(W/'diagnostic-audit.json',a)
print(json.dumps({k:v for k,v in a.items() if k not in ['cases','by_history','slow_events_over_500ms']}))
