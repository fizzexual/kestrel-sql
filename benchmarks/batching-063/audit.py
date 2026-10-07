"""Independently audit raw requests, four-label controls and recovery coverage."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import math
import statistics

W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def quantile(values,p):return sorted(values)[max(0,math.ceil(len(values)*p)-1)] if values else None
def main():
    r=load(W/'paired-service.json'); policy=load(W/'policy.json'); recovery=load(W/'recovery.json')
    assert r['complete'] and len(r['cases'])==32 and not r['failed_cases']
    assert r['policy_sha256']==sha(W/'policy.json') and r['recovery_sha256']==sha(W/'recovery.json')
    assert r['binary_sha256']==policy['binary_sha256']==sha(W/'binaries/released-016.exe')==recovery['binary_sha256']
    for n,d in r['harness_sha256'].items():assert sha(W/n if n=='run.py' else ROOT/'benchmarks'/n)==d,n
    base=load(W/'baseline.json')
    for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d,n
    for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
    morning=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json')
    assert sha(ROOT/morning['report_file'])==morning['report_sha256']
    assert not load(W/'post-qualification-process-check.json')['active_processes']
    assert not recovery['failed_cases'] and len(recovery['cycles'])==24
    assert recovery['policy_sha256']==sha(W/'policy.json')
    recovery_totals={'attempted_batches':0,'acknowledged_batches':0,'published_batches':0,'unacknowledged_committed_batches':0}
    for i,c in enumerate(recovery['cycles']):
        assert c['group_delay_ms']==[0,1,4][i//8] and c['kill_delay_seconds']==policy['recovery']['kill_delays_seconds'][i%8]
        assert all(c[n] for n in ['acknowledged_data_present','whole_batches_and_sums','original_receipt_generations_preserved','retry_exactly_once_after_second_reopen','full_scrubs_passed'])
        assert 0<=c['acknowledged_batches']<=c['published_batches']<=c['attempted_batches']<=64
        assert c['unacknowledged_committed_batches']==c['published_batches']-c['acknowledged_batches']
        for n in recovery_totals:recovery_totals[n]+=c[n]
        assert (W/'recovery-fixtures'/f"{c['group_delay_ms']}-{i%8}"/'archive').is_dir()
    totals={"offered":0,"samples":0,"acknowledged_batches":0,"uncertain_committed_batches":0,"scrubbed_bytes":0,"numpy_windows":0}
    stages=[]; components=[]
    configs=policy['comparison']['configs']
    for index,c in enumerate(r['cases']):
        turn=index//8; config_index=(index%8)//4; profile,rate,seconds=configs[config_index]
        variants=list(policy['variants']); shift=(turn+config_index)%4
        variants=variants[shift:]+variants[:shift]
        assert (c['round'],c['profile'],c['offered_rps'],c['scheduled_seconds'],c['variant'])==(turn,profile,rate,seconds,variants[index%4])
        assert c['case_started_utc']>policy['declared_utc'] and c['version']==policy['version']
        assert c['group_delay_ms']==policy['variants'][c['variant']]
        assert c['ingest_state_before_load']['group_delay_ns']==c['group_delay_ms']*1_000_000
        assert c['live_state_before_reopen']['ingest']['group_delay_ns']==c['group_delay_ms']*1_000_000
        p=W/c["raw_samples_file"]
        assert p.resolve().is_relative_to(W.resolve()) and sha(p)==c["raw_samples_sha256"]
        with gzip.open(p,"rt",encoding="utf-8") as f: raw=[json.loads(line) for line in f]
        seq={s["sequence"] for s in raw}; exp=set(c["expired_sequences"])
        assert len(seq)==len(raw) and len(exp)==c["queue_expired"] and not seq&exp
        assert all(0<=i<c["offered_operations"] for i in seq|exp)
        ok=[s for s in raw if s["ok"]]; failed=[s for s in raw if not s["ok"]]
        decomposition={}
        for op in ("query","append"):
            chosen=[s for s in ok if s["operation"]==op]
            waiting=[s["latency_ms"]-s["service_ms"] for s in chosen]
            assert all(v>=-1e-9 for v in waiting)
            decomposition[op]={"successful":len(chosen),
                "scheduled_to_worker_start_p99_ms":quantile(waiting,.99),
                "worker_start_to_response_p99_ms":quantile([s["service_ms"] for s in chosen],.99)}
        components.append({"round":turn,"variant":c["variant"],"profile":profile,"rate":rate,"seconds":seconds,
                           "posthoc_diagnostic_only":True,"operations":decomposition})
        assert len(raw)+c["queue_dropped"]+len(exp)==c["offered_operations"]
        assert len(ok)==c["successful_operations"] and len(failed)==len(c["errors"])
        assert len(failed)+c["queue_dropped"]+len(exp)==c["unsuccessful_or_unexecuted"]
        cutoff=c["arrival_start_monotonic_ns"]+int(seconds*1e9)
        completed=sum(s["finished_ns"]<=cutoff for s in ok)
        assert completed==c["completed_in_arrival_window"] and completed/seconds==c["successful_rps_in_arrival_window"]
        assert sum(s["latency_ms"]<=100 for s in ok)/c["offered_operations"]==c["offered_fraction_successful_within_100ms"]
        for field,q in [("p50",.5),("p95",.95),("p99",.99)]: assert c["latency_ms"][field]==quantile([s["latency_ms"] for s in ok],q)
        for op in ("query","append"):
            selected=[s for s in ok if s["operation"]==op]; v=c["operation_latency_ms"][op]
            assert len(selected)==v["successful"]
            for field,q in [("p50",.5),("p95",.95),("p99",.99)]: assert v[field]==quantile([s["latency_ms"] for s in selected],q)
            assert v["service_p99"]==quantile([s["service_ms"] for s in selected],.99)
        rec=c["reconciliation"]
        assert rec["all_acknowledged_batches_present"] and rec["batch_atomicity_and_sums"]
        assert rec["acknowledged_batches"]==c["write_successes"] and rec["numpy_reference_windows"]==20
        assert rec["rows"]==1_000_000+100*rec["published_batches"]
        assert rec["full_kestrel_scrub"]["verified_bytes"]==rec["rows"]*24
        assert not c["live_state_before_reopen"]["ingest"]["writer_poisoned"]
        before=c["publication_profile_before_load"]; after=c["live_state_before_reopen"]["publication_profile"]
        names=["prepare","catalog_encode","catalog_rename","segment_write","segment_sync","catalog_write","catalog_sync"]
        v={n:{"count":after[n]["count"]-before[n]["count"],"total_ms":after[n]["total_ms"]-before[n]["total_ms"],
              "histogram":[a-b for a,b in zip(after[n]["histogram"],before[n]["histogram"])]} for n in names}
        for value in v.values(): assert value["count"]==sum(value["histogram"]) and min(value["histogram"])>=0 and value["total_ms"]>=0
        stages.append({"round":turn,"variant":c["variant"],"profile":profile,"rate":rate,"seconds":seconds,
                       "stages":v,"attempts":after["attempts"]-before["attempts"],
                       "compactions":c["live_state_before_reopen"]["ingest"]["compactions"]-c["ingest_state_before_load"]["compactions"]})
        totals["offered"]+=c["offered_operations"]; totals["samples"]+=len(raw)
        totals["acknowledged_batches"]+=rec["acknowledged_batches"]
        totals["uncertain_committed_batches"]+=rec["unacknowledged_but_committed"]
        totals["numpy_windows"]+=20; totals["scrubbed_bytes"]+=rec["full_kestrel_scrub"]["verified_bytes"]
    assert totals['offered']==600000 and totals['numpy_windows']==640
    def attempts(c):
        return c['live_state_before_reopen']['publication_profile']['attempts']-c['publication_profile_before_load']['attempts']
    def metric(c,n):
        if n=='rps':return c['successful_rps_in_arrival_window']
        if n=='attempts':return attempts(c)
        if n=='overall':return c['latency_ms']['p99']
        return c['operation_latency_ms'][n]['p99']
    def collection(c):
        before=c['ingest_state_before_load']; after=c['live_state_before_reopen']['ingest']
        groups=after['collected_groups']-before['collected_groups']
        commits=after['durable_group_commits']-before['durable_group_commits']
        batches=after['committed_batches']-before['committed_batches']
        elapsed=after['collection_total_ms']-before['collection_total_ms']
        publication_ms=after['publication_total_ms']-before['publication_total_ms']
        compaction_ms=after['compaction_total_ms']-before['compaction_total_ms']
        assert groups>0 and commits>0 and batches>=commits and elapsed>=0
        assert publication_ms>=0 and compaction_ms>=0
        return {'collected_groups':groups,'durable_group_commits':commits,'committed_batches':batches,
            'batches_per_durable_group':batches/commits,'mean_collection_ms':elapsed/groups,
            'compactions':after['compactions']-before['compactions'],
            'publication_total_ms':publication_ms,'compaction_total_ms':compaction_ms,
            'compaction_fraction_of_measured_writer_work':compaction_ms/(publication_ms+compaction_ms)}
    summaries=[]; identity=[]; candidate=[]
    for profile,rate,seconds in configs:
        variants={v:sorted([c for c in r['cases'] if c['variant']==v and c['profile']==profile],key=lambda c:c['round']) for v in policy['variants']}
        row={'profile':profile,'rate':rate,'seconds':seconds,'variants':{},'comparisons':{}}
        for v,cases in variants.items():
            row['variants'][v]={'delay_ms':policy['variants'][v],
                'medians':{n:statistics.median(metric(c,n) for c in cases) for n in ['overall','query','append','rps','attempts']},
                'lost':sum(c['unsuccessful_or_unexecuted'] for c in cases),'offered':sum(c['offered_operations'] for c in cases),
                'collection_diagnostics_medians':{n:statistics.median(collection(c)[n] for c in cases) for n in collection(cases[0])},
                'all_rounds':[{'round':c['round'],'lost':c['unsuccessful_or_unexecuted'],**{n:metric(c,n) for n in ['overall','query','append','rps','attempts']}} for c in cases]}
        for numerator,denominator,kind in [('baseline_b','baseline_a','identity'),('delay1','baseline_a','primary'),('delay4','baseline_a','primary'),('delay1','baseline_b','diagnostic'),('delay4','baseline_b','diagnostic')]:
            data={'kind':kind,'paired_ratios':{}}
            for n in ['overall','query','append','rps','attempts']:
                values=[metric(c,n)/metric(b,n) for c,b in zip(variants[numerator],variants[denominator])]
                data['paired_ratios'][n]={'rounds':values,'median':statistics.median(values)}
            p={n:v['median'] for n,v in data['paired_ratios'].items()}
            difference=row['variants'][numerator]['lost']-row['variants'][denominator]['lost']
            tolerance=row['variants'][denominator]['offered']*.01
            if kind=='identity':
                checks={n+'_ratio':.90<=p[n]<=1.10 for n in ['overall','query','append','rps']}
                checks['loss_difference']=abs(difference)<=tolerance
                identity.extend({'profile':profile,'criterion':n,'passed':v} for n,v in checks.items())
                data['calibration_checks']=checks
            elif kind=='primary':
                checks={'append_p99_improvement':p['append']<=.90,'overall_p99_guard':p['overall']<=1.10,
                    'query_p99_guard':p['query']<=1.10,'window_rps_guard':p['rps']>=.90,
                    'loss_increase_guard':difference<=tolerance,'publication_attempt_reduction':p['attempts']<=.85}
                if seconds==60:checks['every_soak_zero_loss']=all(c['unsuccessful_or_unexecuted']==0 for c in variants[numerator])
                candidate.extend({'variant':numerator,'profile':profile,'criterion':n,'passed':v} for n,v in checks.items())
                data['candidate_criteria']=checks
            else:data['diagnostic_only_no_comparator_selection']=True
            row['comparisons'][numerator+'/'+denominator]=data
        summaries.append(row)
    identity_ok=all(g['passed'] for g in identity)
    decisions={v:{'own_criteria_passed':all(g['passed'] for g in candidate if g['variant']==v),
        'all_identity_controls_passed':identity_ok,
        'demonstrated_scoped_improvement':identity_ok and all(g['passed'] for g in candidate if g['variant']==v),
        'supported_promotion':False} for v in ['delay1','delay4']}
    a={'trial':63,'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'report_sha256':sha(W/'paired-service.json'),
        'cases':32,'totals':totals,'raw_sample_accounting_hashes_quantiles_recomputed':True,
        'same_exact_binary_for_all_labels':True,'engine_default_binaries_morning_unchanged':True,
        'no_new_correctness_failure':True,'summaries':summaries,'identity_checks':identity,
        'identity_checks_failed':sum(not g['passed'] for g in identity),'candidate_criteria':candidate,
        'candidate_criteria_failed':sum(not g['passed'] for g in candidate),'decisions':decisions,
        'publication_stage_deltas':stages,'client_latency_decomposition':components,
        'recovery_cycles':24,'recovery_totals':recovery_totals,
        'all_soaks_all_four_labels_zero_loss':all(c['unsuccessful_or_unexecuted']==0 for c in r['cases'] if c['scheduled_seconds']==60),
        'engine_changed':False,'supported_promotion':False,
        'limits':['No retroactive change to 034 policy results or 061/062 failures.',
            'Four paired rounds on a shared Windows desktop are descriptive, not a causal p99 decomposition or statistical proof.',
            'Primary A comparator and all failed checks/outliers retained; diagnostic B cannot replace it.',
            'ACK/cold recovery and process kills are not physical power-loss, production or capacity qualification.']}
    (W/'audit.json').write_text(json.dumps(a,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:a[k] for k in ['cases','totals','identity_checks_failed','candidate_criteria_failed','decisions','recovery_totals']},indent=2))
if __name__=='__main__':main()
