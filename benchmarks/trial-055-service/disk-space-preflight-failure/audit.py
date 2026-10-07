from pathlib import Path
import datetime,gzip,hashlib,json,math,statistics
w=Path(__file__).parent;root=w.parents[1]/'outputs/kestrel-sql'
def sha(p):return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
def quantile(xs,p):return sorted(xs)[math.ceil(len(xs)*p)-1] if xs else None
path=w/'paired-service.json';r=json.loads(path.read_text(encoding='utf-8'));assert r['complete'] and not r['failed_cases']
assert len(r['cases'])==36
policy=json.loads((w/'policy.json').read_text(encoding='utf-8'));assert sha(w/'policy.json')==r['policy_sha256']
for name,d in r['harness_sha256'].items():assert sha(w/name if name=='paired_service.py' else root/'benchmarks'/name)==d
build=json.loads((w/'build-provenance.json').read_text(encoding='utf-8'))
for name,d in build['source'].items():assert sha(w/'candidate'/name)==d
for name,d in build['binaries'].items():assert sha(w/'bin'/name)==d
base=json.loads((w/'baseline.json').read_text(encoding='utf-8'))
for name,d in base['core_source_sha256'].items():assert sha(root/name)==d
assert r['binary_sha256']['baseline']==base['baseline_binary_sha256']['kestrel-stress.exe']
assert r['binary_sha256']['bundle_trial']==build['binaries']['kestrel-stress.exe']
totals={'offered':0,'samples':0,'acknowledged_batches':0,'uncertain_committed_batches':0,'scrubbed_bytes':0,'numpy_windows':0}
stages=[]
for c in r['cases']:
    p=w/c['raw_samples_file'];assert p.resolve().is_relative_to(w.resolve()) and sha(p)==c['raw_samples_sha256']
    with gzip.open(p,'rt',encoding='utf-8') as f:raw=[json.loads(line) for line in f]
    seq={s['sequence'] for s in raw};exp=set(c['expired_sequences']);assert len(seq)==len(raw) and len(exp)==c['queue_expired']
    assert not seq&exp and all(0<=i<c['offered_operations'] for i in seq|exp)
    ok=[s for s in raw if s['ok']];failed=[s for s in raw if not s['ok']]
    assert len(raw)+c['queue_dropped']+len(exp)==c['offered_operations']
    assert len(ok)==c['successful_operations'] and len(failed)==len(c['errors'])
    assert len(failed)+c['queue_dropped']+len(exp)==c['unsuccessful_or_unexecuted']
    cutoff=c['arrival_start_monotonic_ns']+int(c['scheduled_seconds']*1e9)
    completed=sum(s['finished_ns']<=cutoff for s in ok)
    assert completed==c['completed_in_arrival_window'] and completed/c['scheduled_seconds']==c['successful_rps_in_arrival_window']
    assert sum(s['latency_ms']<=100 for s in ok)/c['offered_operations']==c['offered_fraction_successful_within_100ms']
    for field,q in [('p50',.5),('p95',.95),('p99',.99)]:assert c['latency_ms'][field]==quantile([s['latency_ms'] for s in ok],q)
    for op in ['query','append']:
        selected=[s for s in ok if s['operation']==op];v=c['operation_latency_ms'][op];assert len(selected)==v['successful']
        for field,q in [('p50',.5),('p95',.95),('p99',.99)]:assert v[field]==quantile([s['latency_ms'] for s in selected],q)
        assert v['service_p99']==quantile([s['service_ms'] for s in selected],.99)
    rec=c['reconciliation'];assert rec['all_acknowledged_batches_present'] and rec['batch_atomicity_and_sums']
    assert rec['acknowledged_batches']==c['write_successes'] and rec['numpy_reference_windows']==20
    assert rec['rows']==1000000+100*rec['published_batches'] and rec['full_kestrel_scrub']['verified_bytes']==rec['rows']*24
    assert not c['live_state_before_reopen']['ingest']['writer_poisoned']
    before=c['publication_profile_before_load'];after=c['live_state_before_reopen']['publication_profile']
    names=['prepare','catalog_encode','catalog_rename']+(['bundle_write','bundle_sync','bundle_reopen'] if c['variant']=='bundle_trial' else ['segment_write','segment_sync','catalog_write','catalog_sync'])
    v={n:{'count':after[n]['count']-before[n]['count'],'total_ms':after[n]['total_ms']-before[n]['total_ms'],'histogram':[a-b for a,b in zip(after[n]['histogram'],before[n]['histogram'])]} for n in names}
    for values in v.values():assert values['count']==sum(values['histogram']) and min(values['histogram'])>=0 and values['total_ms']>=0
    stages.append({'round':c['round'],'variant':c['variant'],'profile':c['profile'],'rate':c['offered_rps'],'seconds':c['scheduled_seconds'],'stages':v,'attempts':after['attempts']-before['attempts'],'compactions':c['live_state_before_reopen']['ingest']['compactions']-c['ingest_state_before_load']['compactions']})
    totals['offered']+=c['offered_operations'];totals['samples']+=len(raw);totals['acknowledged_batches']+=rec['acknowledged_batches'];totals['uncertain_committed_batches']+=rec['unacknowledged_but_committed'];totals['numpy_windows']+=20;totals['scrubbed_bytes']+=rec['full_kestrel_scrub']['verified_bytes']
summaries=[]
for profile,rate,seconds in [(c['profile'],c['offered_rps'],c['scheduled_seconds']) for c in r['cases'][::2]][:6]:
    selected=[c for c in r['cases'] if (c['profile'],c['offered_rps'],c['scheduled_seconds'])==(profile,rate,seconds)]
    variants={v:sorted([c for c in selected if c['variant']==v],key=lambda c:c['round']) for v in ['baseline','bundle_trial']}
    assert all(len(cs)==3 for cs in variants.values())
    def metric(c,n):return c['latency_ms']['p99'] if n=='mixed' else c['operation_latency_ms'][n]['p99']
    row={'profile':profile,'rate':rate,'seconds':seconds,'variants':{},'paired_ratios':{}}
    for v,cs in variants.items():row['variants'][v]={'p99':{n:statistics.median(metric(c,n) for c in cs) if metric(cs[0],n) is not None else None for n in ['mixed','query','append']},'lost':sum(c['unsuccessful_or_unexecuted'] for c in cs),'offered':sum(c['offered_operations'] for c in cs),'throughput_median':statistics.median(c['successful_rps_in_arrival_window'] for c in cs),'per_round':[{n:metric(c,n) for n in ['mixed','query','append']}|{'lost':c['unsuccessful_or_unexecuted']} for c in cs]}
    for n in ['mixed','query','append']:
        ratios=[metric(t,n)/metric(b,n) for b,t in zip(variants['baseline'],variants['bundle_trial']) if metric(b,n) not in [None,0]]
        row['paired_ratios'][n]={'rounds':ratios,'median':statistics.median(ratios) if ratios else None,'trial_faster_rounds':sum(x<1 for x in ratios)}
    summaries.append(row)
write=next(v for v in summaries if v['profile']=='write');soak=next(v for v in summaries if v['seconds']==60)
guards=[v for v in summaries if v['profile'] in ['read','scan']]
gate={'all_append_profiles_below_0_90':all(v['paired_ratios']['append']['median']<.9 for v in summaries if v['profile'] in ['mixed','write']),'write_p99_below_0_90':write['paired_ratios']['append']['median']<.9,'write_improves_at_least_two_rounds':write['paired_ratios']['append']['trial_faster_rounds']>=2,'trial_all_soaks_zero_loss':soak['variants']['bundle_trial']['lost']==0,'read_guards_below_1_05':all(v['paired_ratios']['query']['median']<1.05 for v in guards)}
a={'status':'unreleased CAT6 service trial 055 on unchanged 053; supported engine unchanged','report_sha256':sha(path),'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':36,'totals':totals,'raw_quantiles_accounting_uniqueness_and_hashes_recomputed':True,'current_default_core_matches_released_0_3_16':True,'summaries':summaries,'publication_stage_deltas':stages,'predeclared_performance_gates':gate,'performance_gates_passed':all(gate.values()),'release_gates_completed':False,'trial_promoted':False}
(w/'paired-service-audit.json').write_text(json.dumps(a,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'totals':totals,'summaries':summaries,'gates':gate},indent=2))
