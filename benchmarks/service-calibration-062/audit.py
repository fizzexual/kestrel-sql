"""Independent raw accounting and predeclared A/A/candidate calibration checks."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import math
import statistics

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
def quantile(values, p):
    return sorted(values)[max(0, math.ceil(len(values) * p) - 1)] if values else None
def main():
    r = load(W / 'paired-service.json')
    policy = load(W / 'policy.json')
    assert r['complete'] and len(r['cases']) == 27 and not r['failed_cases']
    initial = load(W / 'disk-space-preflight-failure/paired-service.json')
    preservation = load(W / 'preflight-failure-preservation.json')
    assert len(initial['cases']) == 8 and r['cases'][:8] == initial['cases']
    assert r['preserved_preflight_failures'] == initial['failed_cases']
    assert r['resumption']['unstarted_only_cases_completed'] == 19
    assert r['resumption']['script_sha256'] == sha(W / 'resume.py')
    assert r['resumption']['original_report_sha256'] == sha(W / 'disk-space-preflight-failure/paired-service.json')
    assert all(c['resumed_after_preflight_only'] for c in r['cases'][8:])
    for n, d in preservation['original_raw_sha256'].items():
        assert sha(W / n) == d, n
    for n, d in preservation['failure_snapshot_sha256'].items():
        assert sha(W / 'disk-space-preflight-failure' / n) == d, n
    for n, d in preservation['storage_reclamation_proofs'].items():
        assert sha(W / n) == d, n
    assert r['policy_sha256'] == sha(W / 'policy.json')
    assert r['binary_sha256'] == policy['binary_sha256']
    assert r['binary_sha256']['baseline_a'] == r['binary_sha256']['baseline_b'] == sha(W / 'binaries/released-016.exe')
    assert r['binary_sha256']['candidate'] == sha(W / 'binaries/clean-core-061.exe')
    for n, d in r['harness_sha256'].items():
        assert sha(W / n if n == 'run.py' else ROOT / 'benchmarks' / n) == d, n
    base = load(W / 'baseline.json')
    for n, d in base['core_source_sha256'].items():
        assert sha(ROOT / n) == d, n
    for n, d in base['baseline_binary_sha256'].items():
        assert sha(ROOT / 'bin' / n) == d, n
    assert r['binary_sha256']['baseline_a'] == base['baseline_binary_sha256']['kestrel-stress.exe']
    provenance = load(W / '061-source-provenance.json')
    for n, d in provenance['candidate'].items():
        assert sha(W.parent / 'perf-061/lab/outputs/kestrel-sql' / n) == d, n
    morning = load(ROOT / 'benchmarks/overnight-2026-10-07-report-check.json')
    assert sha(ROOT / morning['report_file']) == morning['report_sha256']
    assert sha(W.parent / 'perf-061/paired-service-audit.json') == load(W.parent / 'perf-061/audit.json')['service_raw_audit_sha256']
    totals={"offered":0,"samples":0,"acknowledged_batches":0,"uncertain_committed_batches":0,"scrubbed_bytes":0,"numpy_windows":0}
    stages=[]; components=[]
    configs=policy["comparison"]["configs"]
    for index,c in enumerate(r["cases"]):
        turn=index//9; config_index=(index%9)//3; profile,rate,seconds=configs[config_index]
        variants=["baseline_a","baseline_b","candidate"]
        shift=(turn+config_index)%3
        variants=variants[shift:]+variants[:shift]
        assert (c["round"],c["profile"],c["offered_rps"],c["scheduled_seconds"],c["variant"])==(turn,profile,rate,seconds,variants[index%3])
        assert c["case_started_utc"]>policy["declared_utc"]
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
    summaries = []
    identity_gates = []
    candidate_gates = []
    for profile, rate, seconds in configs:
        selected = [c for c in r['cases'] if (c['profile'], c['offered_rps'], c['scheduled_seconds']) == (profile, rate, seconds)]
        variants = {v: sorted((c for c in selected if c['variant'] == v), key=lambda c: c['round'])
                    for v in ('baseline_a', 'baseline_b', 'candidate')}
        assert all(len(cs) == 3 for cs in variants.values())
        def metric(c, name):
            if name == 'overall':
                return c['latency_ms']['p99']
            if name == 'rps':
                return c['successful_rps_in_arrival_window']
            return c['operation_latency_ms'][name]['p99']
        row = {'profile': profile, 'rate': rate, 'seconds': seconds, 'variants': {}, 'comparisons': {}}
        for v, cs in variants.items():
            row['variants'][v] = {'p99_ms': {n: statistics.median(metric(c, n) for c in cs)
                                                     if metric(cs[0], n) is not None else None
                                                for n in ('overall', 'query', 'append')},
                                 'lost': sum(c['unsuccessful_or_unexecuted'] for c in cs),
                                 'offered': sum(c['offered_operations'] for c in cs),
                                 'rps_median': statistics.median(metric(c, 'rps') for c in cs),
                                 'all_rounds': [{'round': c['round'], 'p99_ms': c['latency_ms']['p99'],
                                                 'append_p99_ms': c['operation_latency_ms']['append']['p99'],
                                                 'query_p99_ms': c['operation_latency_ms']['query']['p99'],
                                                 'lost': c['unsuccessful_or_unexecuted'],
                                                 'successful_window_rps': metric(c, 'rps')} for c in cs]}
        for label, numerator, denominator in [('identity_b_over_a', 'baseline_b', 'baseline_a'),
                                               ('primary_candidate_over_a', 'candidate', 'baseline_a'),
                                               ('diagnostic_candidate_over_b', 'candidate', 'baseline_b')]:
            data = {'paired_ratios': {}}
            crossing = []
            for d, n in zip(variants[denominator], variants[numerator]):
                if bool(d.get('resumed_after_preflight_only')) != bool(n.get('resumed_after_preflight_only')):
                    crossing.append(d['round'])
            data['rounds_spanning_maintenance_pause'] = crossing
            if label == 'primary_candidate_over_a':
                assert not crossing
            for name in ('overall', 'query', 'append', 'rps'):
                ratios = [metric(n, name) / metric(d, name)
                          for d, n in zip(variants[denominator], variants[numerator])
                          if metric(d, name) not in (None, 0)]
                data['paired_ratios'][name] = {'rounds': ratios, 'median': statistics.median(ratios) if ratios else None}
            difference = row['variants'][numerator]['lost'] - row['variants'][denominator]['lost']
            allowed_loss = row['variants'][denominator]['offered'] * .01
            if label == 'identity_b_over_a':
                checks = {'overall_p99': .90 <= data['paired_ratios']['overall']['median'] <= 1.10,
                          'query_p99': .90 <= data['paired_ratios']['query']['median'] <= 1.10,
                          'window_rps': .90 <= data['paired_ratios']['rps']['median'] <= 1.10,
                          'loss_difference': abs(difference) <= allowed_loss}
                if profile != 'read':
                    checks['append_p99'] = .90 <= data['paired_ratios']['append']['median'] <= 1.10
                identity_gates.extend({'profile': profile, 'criterion': n, 'passed': v} for n, v in checks.items())
                data['calibration_checks'] = checks
            elif label == 'primary_candidate_over_a':
                checks = {'overall_p99': data['paired_ratios']['overall']['median'] <= 1.10,
                          'query_p99': data['paired_ratios']['query']['median'] <= 1.10,
                          'window_rps': data['paired_ratios']['rps']['median'] >= .90,
                          'loss_increase': difference <= allowed_loss}
                if profile != 'read':
                    checks['append_p99'] = data['paired_ratios']['append']['median'] <= 1.10
                candidate_gates.extend({'profile': profile, 'criterion': n, 'passed': v} for n, v in checks.items())
                data['regression_guards'] = checks
            else:
                data['diagnostic_only_no_posthoc_comparator_selection'] = True
            row['comparisons'][label] = data
        summaries.append(row)
    assert totals['offered'] == 450000 and totals['numpy_windows'] == 540
    audit = {'trial': 62, 'audited_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'report_sha256': sha(W / 'paired-service.json'), 'cases': 27, 'totals': totals,
             'same_exact_executable_for_both_baseline_labels': True,
             'raw_sample_accounting_hashes_and_quantiles_recomputed': True,
             'default_core_supported_binaries_original_061_and_morning_unchanged': True,
             'no_new_correctness_failure': True, 'summaries': summaries,
             'publication_stage_deltas': stages, 'client_latency_decomposition': components,
             'identity_calibration_checks': identity_gates,
             'identity_checks_failed': sum(not g['passed'] for g in identity_gates),
             'primary_candidate_guards': candidate_gates,
             'primary_candidate_guards_failed': sum(not g['passed'] for g in candidate_gates),
             'all_soaks_all_three_labels_zero_loss': all(c['unsuccessful_or_unexecuted'] == 0 for c in r['cases'] if c['scheduled_seconds'] == 60),
             'original_061_service_failures_preserved': 10,
             'initial_timed_cases_unchanged': 8, 'preflight_only_unstarted_cases_completed': 19,
             'initial_preflight_failure_preserved': True,
             'comparisons_spanning_maintenance': r['resumption']['comparisons_spanning_maintenance'],
             'no_primary_candidate_pair_spans_maintenance': True,
             'engine_changed': False, 'supported_promotion': False,
             'limits': ['Posthoc stage/dispatch quantiles do not decompose p99 or establish a cause.',
                        'Three pairs per profile; A/A tolerance failures are measurement calibration evidence, not statistical proof.',
                        'Candidate/B diagnostics cannot replace the predeclared candidate/A comparator.',
                        'No original 061 failure is erased; this scoped calibration cannot establish production readiness.']}
    (W / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'cases': 27, 'totals': totals, 'identity_checks_failed': audit['identity_checks_failed'],
                      'primary_candidate_guards_failed': audit['primary_candidate_guards_failed']}, indent=2))
if __name__ == '__main__':
    main()
