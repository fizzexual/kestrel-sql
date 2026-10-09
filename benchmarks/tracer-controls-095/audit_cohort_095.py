"""Independent loss-aware raw/ACK/trace/CRC audit and every immutable 095 gate."""
from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, importlib.util, json, math, random, sys
W=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-095')
sys.path.insert(0,str(W))
sys.path.insert(0,str(W/'harness'))
import audit_service_095 as a
from stress_compare import make_task
load,sha,quantile=a.load,a.sha,a.quantile

def outcomes(case,raw):
    count=int(case['scheduled_seconds']*case['offered_rps'])
    assert case['offered_operations']==count
    seqs=[s['sequence'] for s in raw]
    assert len(set(seqs))==len(seqs) and all(type(s) is int and 0<=s<count for s in seqs)
    expired=case['expired_sequences']
    assert len(set(expired))==len(expired)==case['queue_expired']
    assert all(type(s) is int and 0<=s<count for s in expired) and not set(expired).intersection(seqs)
    missing=sorted(set(range(count)).difference(seqs)); dropped=sorted(set(missing).difference(expired))
    assert len(dropped)==case['queue_dropped'] and count==len(raw)+len(expired)+len(dropped)
    good=[s for s in raw if s['ok']]; failed=[s for s in raw if not s['ok']]
    assert len(good)==case['successful_operations']
    assert len(failed)+len(missing)==case['unsuccessful_or_unexecuted']
    errors=[e for e in case['errors'] if e['sequence'] is not None]
    assert {(e['sequence'],e['operation']) for e in errors}=={(s['sequence'],s['operation']) for s in failed}
    assert len(errors)==len(failed) and not [e for e in case['errors'] if e['sequence'] is None]
    return good,{'case_index':case['case_index'],'offered':count,'executed':len(raw),'successful':len(good),
        'executed_failed':len(failed),'queue_dropped':len(dropped),'queue_expired':len(expired),'lost':len(failed)+len(missing),
        'missing_sequences_reconstructed_from_exact_offer_range':missing,
        'dropped_sequences_inferred_not_recorded_execution':dropped,'expired_sequences_recorded':expired}

def negatives():
    from copy import deepcopy
    c={'scheduled_seconds':1,'offered_rps':3,'offered_operations':3,'expired_sequences':[1],
        'queue_expired':1,'queue_dropped':1,'successful_operations':1,'unsuccessful_or_unexecuted':2,
        'errors':[],'case_index':-1}
    raw=[{'sequence':0,'ok':True,'operation':'query'}]; outcomes(c,raw); checks=[]
    for name in ['duplicate_raw','expired_raw_overlap','wrong_drop_count','wrong_loss_count','unknown_sequence','duplicate_expiry']:
        x,y=deepcopy(c),deepcopy(raw)
        if name=='duplicate_raw': y+=deepcopy(y)
        elif name=='expired_raw_overlap': x['expired_sequences']=[0]
        elif name=='wrong_drop_count': x['queue_dropped']=0
        elif name=='wrong_loss_count': x['unsuccessful_or_unexecuted']=0
        elif name=='unknown_sequence': y[0]['sequence']=3
        else: x['expired_sequences']=[1,1]; x['queue_expired']=2
        try: outcomes(x,y)
        except AssertionError: checks.append(name)
        else: raise AssertionError(('invalid outcome accepted',name))
    return {'validation_only_not_timing':True,'six_invalid_outcome_records_rejected':checks}

def main():
    report,policy=load(W/'paired-service.json'),load(W/'service-policy.json')
    original=load(W/'policy.json')
    assert {k:policy[k] for k in original}==original
    assert policy['original_pre_build_policy_sha256']==sha(W/'policy.json')
    assert report['complete'] and not report['failed_cases']
    assert report['policy_sha256']==sha(W/'service-policy.json') and report['freeze_sha256']==sha(W/'timing-freeze.json')
    for n,h in load(W/'timing-freeze.json')['sha256'].items(): assert sha(W/n)==h,n
    a.verify_order(report['cases'],policy); validation=negatives()
    totals={n:0 for n in ['offered','successful','lost','queue_dropped','queue_expired','executed_failed','acknowledged_batches','full_crc_bytes']}
    native=[]; resources=[]; conservation=[]; stalls=[]; losses=[]; publication=[]
    for case in report['cases']:
        path=W/case['raw_samples_file']; assert sha(path)==case['raw_samples_sha256']
        with gzip.open(path,'rt',encoding='utf-8') as f: raw=[json.loads(line) for line in f]
        good,counts=outcomes(case,raw); conservation.append(counts)
        assert all(s['operation'] in ['query','append'] for s in raw)
        rng=random.Random(20261006)
        intended={seq:make_task(rng,seq,policy['base_rows'],case['profile'])[1] for seq in range(counts['offered'])}
        assert all(s['operation']==intended[s['sequence']] for s in raw)
        counts['missing_intended_operations_reconstructed_not_executed']=[{'sequence':seq,'operation':intended[seq]} for seq in counts['missing_sequences_reconstructed_from_exact_offer_range']]
        start=case['arrival_start_monotonic_ns']; end=start+int(case['scheduled_seconds']*1e9)
        within=sum(s['finished_ns']<=end for s in good)
        assert within==case['completed_in_arrival_window'] and within/case['scheduled_seconds']==case['successful_rps_in_arrival_window']
        assert len(good)/case['including_drain_seconds']==case['successful_rps_including_drain']
        assert sum(s['latency_ms']<=100 for s in good)/counts['offered']==case['offered_fraction_successful_within_100ms']
        for sample in raw:
            assert sample['arrival_ns']==start+int(sample['sequence']*1e9/case['offered_rps'])
            assert math.isclose(sample['latency_ms'],(sample['finished_ns']-sample['arrival_ns'])/1e6,abs_tol=1e-12)
            assert sample['service_ms']>=0 and sample['latency_ms']+1e-9>=sample['service_ms']
            if sample['operation']=='append' and sample['ok']:
                receipt=sample['append_receipt']; assert receipt['affected']==100 and not receipt['duplicate'] and receipt['generation']>1
            elif sample['operation']=='query': assert sample['append_receipt'] is None
            if sample['latency_ms']>100: stalls.append({'case_index':case['case_index'],**sample})
        for operation in ['overall','query','append']:
            chosen=good if operation=='overall' else [s for s in good if s['operation']==operation]
            metrics=case['latency_ms'] if operation=='overall' else case['operation_latency_ms'][operation]
            values=[s['latency_ms'] for s in chosen]
            for name,fraction in [('p50',.5),('p95',.95),('p99',.99)]: assert metrics[name]==quantile(values,fraction)
            assert metrics['max']==max(values,default=None)
            if operation!='overall':
                assert metrics['successful']==len(chosen) and metrics['service_p99']==quantile([s['service_ms'] for s in chosen],.99)
        acked=sum(s['operation']=='append' for s in good)
        assert acked==case['write_successes'] and len(good)-acked==case['read_successes']
        recovery=case['reconciliation']; assert recovery['acknowledged_batches']==recovery['published_batches']==acked
        assert recovery['unacknowledged_but_committed']==0 and recovery['all_acknowledged_batches_present'] and recovery['batch_atomicity_and_sums']
        assert recovery['rows']==policy['base_rows']+acked*100 and recovery['numpy_reference_windows']==20
        assert recovery['full_kestrel_scrub']['verified_bytes']==recovery['rows']*24
        ingest=case['live_state_before_reopen']['ingest']
        assert not ingest['writer_poisoned'] and ingest['maintenance_errors']==0 and ingest['queued_payload_bytes']==0
        native.append(a.verify_native_store(W,case,raw,policy['base_rows']))
        resources.append({'case_index':case['case_index'],**a.trace_check(case,raw,policy['base_rows'])})
        before=case['publication_profile_before_load']; after=case['live_state_before_reopen']['publication_profile']
        assert after['completed']-before['completed']==ingest['durable_group_commits']+ingest['compactions']
        deltas={n:after[n]['total_ms']-before[n]['total_ms'] for n in a.STAGES}; assert all(v>=-1e-8 for v in deltas.values())
        publication.append({'case_index':case['case_index'],'binary':case['binary'],'family':case['family'],'variant':case['variant'],
            'profile':case['profile'],'lost':counts['lost'],'durable_groups':ingest['durable_group_commits'],
            'compactions':ingest['compactions'],'stage_total_ms_after_subtracting_seed':deltas,
            'publication_max_append_ms':ingest['publication_max_ms'],'dispatch_lag_ms':case['dispatch_lag_ms'],
            'seed_stage_max_not_load_stage_max':True,'not_exclusive_p99_or_physical_cause':True})
        if counts['lost']: losses.append({'family':case['family'],'round':case['round'],'variant':case['variant'],**counts})
        for name in ['offered','successful','lost','queue_dropped','queue_expired','executed_failed']: totals[name]+=counts[name]
        totals['acknowledged_batches']+=acked; totals['full_crc_bytes']+=recovery['full_kestrel_scrub']['verified_bytes']
        bridges=load(W/'service-fixtures'/Path(case['fixture']).name/'owned-bridges.json')
        assert len(bridges)==2 and all('completed_utc' in b for b in bridges)
        print(json.dumps({'audited':case['case_index']+1,'total':288,'lost':counts['lost'],'full_current_store_passed':True}),flush=True)
    scopes=[a.scope(report['cases'],policy,family,name,rounds) for family in policy['families']
        for name,rounds in [('full',list(range(policy['rounds']))),('block_0',policy['blocks'][0]),('block_1',policy['blocks'][1])]]
    qualified={family['name']:all(s['passed'] for s in scopes if s['family']==family['name']) for family in policy['families']}
    result={'trial':95,'correctness_passed':True,'loss_aware_raw_audit_passed':True,'cases':288,**totals,
        'scopes':scopes,'family_overhead_qualified':qualified,'all_required_scopes_passed':all(qualified.values()),
        'identity_failed_total':sum(s['identity_failed'] for s in scopes),'candidate_failed_total':sum(s['candidate_failed'] for s in scopes),
        'loss_cases':losses,'conservation':conservation,'native_store_audits':native,'numpy_windows':288*20,
        'independent_complete_ACK_row_and_CRC_bytes':sum(s['full_data_crc_bytes'] for s in native),
        'trace_results':resources,'traced_requests_correlated':sum(t['requests'] for t in resources),
        'events_over_100ms':len(stalls),'all_events_over_100ms':stalls,'publication_stage_diagnostics':publication,
        'validation':validation,'immutable_original_policy_and_all_gates_unchanged':True,
        'no_native_launches_or_timing_reruns':True,'no_engine_speed_between_family_competitor_or_release_claim':True,'supported':'0.3.16'}
    assert totals['lost']==totals['offered']-totals['successful']
    if totals['lost']: assert not result['all_required_scopes_passed']
    a.save(W/'audit.json',result)
    print(json.dumps({k:result[k] for k in ['cases','offered','successful','lost','family_overhead_qualified','identity_failed_total','candidate_failed_total']}),flush=True)
    return result

if __name__=='__main__':
    if len(sys.argv)>1: W=Path(sys.argv[1]); a.W=W
    main()
