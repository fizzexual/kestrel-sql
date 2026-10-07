from pathlib import Path
import datetime, hashlib, json, statistics
W=Path(__file__).resolve().parent; ROOT=W.parents[1]/'outputs/kestrel-sql'
OLD=ROOT/'benchmarks/trial-053-compact-receipts'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
old=read(OLD/'native-audit.json'); new=read(W/'native-audit.json'); original=read(OLD/'advance-audit.json')
assert not original['advance_to_service'] and not original['predeclared_gates']['all_typical_latency_guards']
fresh=read(W/'new-series-audit.json'); policy=read(W/'trial-policy.json'); g=policy['criteria']
assert fresh['paired_logical_catalogs_equal'] and fresh['paired_segment_frames_and_payloads_byte_identical']
for variant in ['base_050','compact_053']:
    p=read(W/'policy.json')
    rel='trial-050-generation-identity' if variant=='base_050' else 'trial-053-compact-receipts'
    assert sha(ROOT/'benchmarks'/rel/'bin/publication-probe.exe')==p['binary_sha256'][variant]
    assert sha(ROOT/'benchmarks'/rel/'candidate/examples/publication_probe.rs')==p['driver_source_sha256'][variant]
pairs=[]; summaries=[]
for size in [0,50000,99000]:
    ratios=[]; selected=[]
    for label,series in [('original_053',old),('followup_054',new)]:
        cs=[c for c in series['cases'] if c['spec']['seed_receipts']==size]
        selected+=cs
        for turn in sorted({c['spec']['round'] for c in cs}):
            b=next(c for c in cs if c['spec']['round']==turn and c['spec']['variant']=='base_050')
            t=next(c for c in cs if c['spec']['round']==turn and c['spec']['variant']=='compact_053')
            ratios.append({'series':label,'round':turn,**{k+'_ratio':t[k]/b[k] for k in ['append_total_ms','p50_ms','p99_ms','max_ms','reopen_ms']}})
    assert len(ratios)==(10 if size==99000 else 3)
    pairs.append({'seed_receipts':size,'pairs':len(ratios),'rounds':ratios,**{k:statistics.median(r[k] for r in ratios) for k in ratios[0] if k not in ['series','round']}})
    summaries.append({'seed_receipts':size,'pairs':len(ratios),'variants':{v:{k:statistics.median(c[k] for c in selected if c['spec']['variant']==v) for k in ['append_total_ms','p50_ms','p99_ms','max_ms','reopen_ms']} for v in ['base_050','compact_053']}})
big=next(c for c in pairs if c['seed_receipts']==99000); f=fresh['pairs'][0]
combined_gates={'large_ledger_total':big['append_total_ms_ratio']<=g['large_paired_append_total_at_most'],
    'large_ledger_p99':big['p99_ms_ratio']<=g['large_paired_p99_at_most'],
    'all_size_p50_guards':all(c['p50_ms_ratio']<=g['paired_p50_guard_at_all_sizes_at_most'] for c in pairs),
    'all_size_maximum_guards':all(c['max_ms_ratio']<=g['paired_max_guard_at_all_sizes_at_most'] for c in pairs),
    'all_size_reopen_guards':all(c['reopen_ms_ratio']<=g['paired_reopen_guard_at_all_sizes_at_most'] for c in pairs)}
fresh_gates={'large_ledger_total':f['append_total_ms_ratio']<=g['large_paired_append_total_at_most'],
    'large_ledger_p99':f['p99_ms_ratio']<=g['large_paired_p99_at_most'],
    'large_ledger_p50_guard':f['p50_ms_ratio']<=g['paired_p50_guard_at_all_sizes_at_most'],
    'large_ledger_maximum_guard':f['max_ms_ratio']<=g['paired_max_guard_at_all_sizes_at_most'],
    'large_ledger_reopen_guard':f['reopen_ms_ratio']<=g['paired_reopen_guard_at_all_sizes_at_most']}
orders={'base_050':0,'compact_053':0}
for p in [read(OLD/'policy.json'),read(W/'policy.json')]:
    for turn in sorted({c['round'] for c in p['cases']}):
        first=next(c for c in p['cases'] if c['seed_receipts']==99000 and c['round']==turn)
        orders[first['variant']]+=1
assert orders=={'base_050':5,'compact_053':5}
classification=[]
for label,folder,series in [('original_053',OLD,old),('followup_054',W,new)]:
    for c in series['cases']:
        if c['spec']['seed_receipts']!=99000: continue
        raw=read(folder/'raw'/(c['label']+'.stdout.json'))
        groups={'small_catalog':[],'large_checkpoint':[]}
        for index,(latency,bytes_) in enumerate(zip(raw['raw_latency_ms'],raw['raw_catalog_bytes'])):
            kind='large_checkpoint' if bytes_>1_000_000 else 'small_catalog'
            groups[kind].append({'index':index,'latency_ms':latency,'catalog_file_bytes':bytes_})
        assert sum(map(len,groups.values()))==256
        classification.append({'series':label,'label':c['label'],'variant':c['spec']['variant'],
            'groups':{k:{'samples':len(v),'p50_ms':statistics.median(x['latency_ms'] for x in v) if v else None,'append_total_ms':sum(x['latency_ms'] for x in v),'slow_over_500ms':sum(x['latency_ms']>500 for x in v),'slow_over_1000ms':sum(x['latency_ms']>1000 for x in v),'large_samples':v if k=='large_checkpoint' else []} for k,v in groups.items()}})
out={'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'new_engine_code':False,
    'original_053_failed_qualification_retained':True,'original_advance_audit_sha256':sha(OLD/'advance-audit.json'),
    'fresh_seven_pair_gates':fresh_gates,'combined_ten_large_pair_and_original_small_guards':combined_gates,
    'eligible_for_separate_service_qualification':all(fresh_gates.values()) and all(combined_gates.values()),
    'large_pair_order_balanced':orders,'combined_pairs':pairs,'combined_median_values':summaries,
    'fresh_append_samples':3584,'fresh_rows_timed':358400,'fresh_cold_duplicate_retries':42,'fresh_scrubbed_bytes':84403200,
    'all_original_plus_fresh_append_samples':8192,'all_original_plus_fresh_rows_timed':819200,
    'all_original_plus_fresh_cold_retries':96,'all_original_plus_fresh_scrubbed_bytes':149433600,
    'trial_promoted':False,'default_engine_changed':False,'competitor_benchmark':False,
    'small_vs_large_catalog_analysis':classification,
    'interpretation':'Native-only repeat on identical frozen engines. All ten large-ledger p50 pairs remain slower; the aggregate guard is not proof of a p50 improvement. Original failed qualification and new stalls remain visible. No causal attribution to device/OS or production service claim.'}
assert all(r['p50_ms_ratio']>1 for r in big['rounds'])
(W/'combined-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['small_vs_large_catalog_analysis','combined_pairs']},indent=2))
