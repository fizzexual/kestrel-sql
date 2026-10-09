"""Exact 095 loss-aware conservation and its six invalid-record controls."""
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


