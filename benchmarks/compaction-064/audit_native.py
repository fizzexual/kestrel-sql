"""Independent post-timing native checks and predeclared decision; no reruns."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,statistics
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def quantile(v,q):
    a=sorted(v);x=(len(a)-1)*q;l=math.floor(x);r=math.ceil(x);return a[l]+(a[r]-a[l])*(x-l)
policy=load(W/'policy.json');p=load(W/'native-policy.json');r=load(W/'native-results.json')
assert r['complete'] and not r['failures'] and len(r['cases'])==len(p['cases'])==27
assert r['native_policy_sha256']==sha(W/'native-policy.json') and p['trial_policy_sha256']==sha(W/'policy.json')
assert p['harness_sha256']==sha(W/'native_publication.py') and p['memory_helper_sha256']==sha(W/'process_memory.py')
assert p['driver_sha256']==sha(W/'native_publication_probe.rs')
build=load(W/'native-driver-build.json')
assert p['binary_sha256']['baseline_a']==p['binary_sha256']['baseline_b']==sha(W/'native-binaries/baseline-publication.exe')==build['baseline_sha256']
assert p['binary_sha256']['candidate']==sha(W/'native-binaries/candidate-publication.exe')==build['candidate_sha256']
cases=[]
for item,spec in zip(r['cases'],p['cases']):
    assert item['spec']==spec;label=item['label'];raw=W/'native-raw'
    for suffix,key in [('stdout.json','stdout_sha256'),('stderr.txt','stderr_sha256'),('status.json','status_sha256')]:assert sha(raw/f'{label}.{suffix}')==item[key]
    status=load(raw/f'{label}.status.json');x=load(raw/f'{label}.stdout.json')
    assert status['spec']==spec and status['exit_code']==0 and not status.get('timeout')
    assert x['version']==('0.3.17-dev.64' if spec['variant']=='candidate' else '0.3.16')
    n=spec['seed_receipts']+25600
    assert x['after']['rows']==n and x['after']['recorded_batch_ids']==spec['seed_receipts']+256
    assert x['rows_and_sum_match'] and x['reopen_retry_and_full_scrub_passed']
    v=x['raw_latency_ms'];maint=x['maintenance_ms']
    assert len(v)==len(x['raw_catalog_bytes'])==256 and all(math.isfinite(y) and y>=0 for y in v+maint)
    assert len(maint)==(4 if spec['variant']=='candidate' else 7)
    assert x['after']['segments']==(4 if spec['variant']=='candidate' else 39)+(1 if spec['seed_receipts'] else 0)
    initial=x['before']['publication_profile'];final=x['after']['publication_profile'];stages={}
    counters={k:final[k]-initial[k] for k in final if not isinstance(final[k],dict)}
    assert counters['attempts']==counters['completed']==256+len(maint)
    for k,f in final.items():
        if not isinstance(f,dict):continue
        b=initial[k];d={'count':f['count']-b['count'],'total_ms':f['total_ms']-b['total_ms'],'histogram':[u-v for u,v in zip(f['histogram'],b['histogram'])],'cumulative_max_including_seed_ms':f['max_ms']}
        assert sum(d['histogram'])==d['count'] and min(d['histogram'])>=0;stages[k]=d
    m=status['memory'];available=m['success'] and m['peak_working_set_bytes']>0 and m['peak_commit_bytes']>0
    cases.append({'spec':spec,'label':label,'rows':n,'p50_ms':quantile(v,.5),'p95_ms':quantile(v,.95),'p99_ms':quantile(v,.99),'max_ms':max(v),
        'append_total_ms':sum(v),'maintenance_total_ms':sum(maint),'maintenance_calls':len(maint),'append_plus_maintenance_ms':sum(v)+sum(maint),
        'reopen_ms':x['reopen_ms'],'peak_working_set_bytes':m['peak_working_set_bytes'] if available else None,'peak_commit_bytes':m['peak_commit_bytes'] if available else None,
        'memory_available':available,'publication_counter_deltas_including_maintenance':counters,'stage_deltas_including_maintenance':stages,
        'physical_bytes':x['after']['physical_bytes'],'final_segments':x['after']['segments'],'slow_over_500ms':sum(y>500 for y in v),
        'tails_over_500ms':[{'index':i,'ms':y,'catalog_file_bytes':x['raw_catalog_bytes'][i]} for i,y in enumerate(v) if y>500]})
metrics=p['identity_metrics'];summaries=[];checks=[]
goals={'append_plus_maintenance_ms':policy['native']['primary_goals']['append_plus_maintenance_ratio_max'],'p99_ms':policy['native']['primary_goals']['append_p99_ratio_max']}
guards={'p50_ms':policy['native']['guards']['append_p50_ratio_max'],'max_ms':policy['native']['guards']['append_max_ratio_max'],'reopen_ms':policy['native']['guards']['reopen_ratio_max'],'peak_working_set_bytes':policy['native']['memory_guard_peak_working_set_ratio_max']}
for size in [0,50000,99000]:
    pairs=[];selected=[c for c in cases if c['spec']['seed_receipts']==size]
    for turn in range(3):
        matched={label:next(c for c in selected if c['spec']['round']==turn and c['spec']['variant']==label) for label in ['baseline_a','baseline_b','candidate']}
        ratios={}
        for comp,num,den in [('candidate_a','candidate','baseline_a'),('identity_b_a','baseline_b','baseline_a'),('candidate_b_diagnostic','candidate','baseline_b')]:
            ratios[comp]={key:(matched[num][key]/matched[den][key] if matched[num][key] is not None and matched[den][key] is not None and matched[den][key]>0 else None) for key in metrics}
        pairs.append({'round':turn,'ratios':ratios})
    medians={comp:{key:(statistics.median(pair['ratios'][comp][key] for pair in pairs) if all(pair['ratios'][comp][key] is not None for pair in pairs) else None) for key in metrics} for comp in pairs[0]['ratios']}
    display={label:{key:(statistics.median(c[key] for c in selected if c['spec']['variant']==label) if all(c[key] is not None for c in selected if c['spec']['variant']==label) else None) for key in metrics+['maintenance_total_ms','maintenance_calls','append_total_ms','peak_commit_bytes','physical_bytes','final_segments']} for label in ['baseline_a','baseline_b','candidate']}
    for kind,limits in [('goal',goals),('guard',guards)]:
        for key,limit in limits.items():
            ratio=medians['candidate_a'][key];checks.append({'size':size,'kind':kind,'metric':key,'paired_ratio':ratio,'limit':limit,'passed':ratio is not None and ratio<=limit})
    low,high=policy['native']['identity_calibration_ratio_interval']
    for key in metrics:
        ratio=medians['identity_b_a'][key];checks.append({'size':size,'kind':'identity','metric':key,'paired_ratio':ratio,'interval':[low,high],'passed':ratio is not None and low<=ratio<=high})
    summaries.append({'seed_receipts':size,'variants_median_display_only':display,'pairs':pairs,'median_paired_ratios':medians})
failed=[c for c in checks if not c['passed']]
out={'audited_utc':datetime.now(timezone.utc).isoformat(),'complete':True,'cases':cases,'summaries':summaries,'checks':checks,'failed_checks':failed,
    'advance_to_service':not failed,'default_engine_changed':False,'trial_promoted':False,'quantile_method':'Type7 linear interpolation over all256 raw append samples',
    'append_samples':27*256,'rows_appended_under_timers':27*25600,'cold_duplicate_retries':27*3,'crc_scrubbed_bytes':sum(c['rows']*24*2 for c in cases),
    'raw_hashes_counts_receipts_oracles_stages_and_case_order_passed':True,'scope':'Sequential native closed-loop trial on same host; newly linked identical driver, exact released core versus dev64; no fresh competitor or open-loop service measurement',
    'decision':'Service allowed only when all goals, guards and identity checks pass; preserve unsuccessful results'}
(W/'native-audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ['cases','checks']},indent=2))
