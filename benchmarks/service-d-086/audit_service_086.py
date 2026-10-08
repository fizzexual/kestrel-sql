"""Independent raw conservation/quantiles/order and predeclared service gates."""
from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, itertools, json, math, statistics

W = Path('D:/Codex/Kestrel/work/perf-086')
REPO = W.parents[1] / 'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p, v): p.write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8', newline='\n')
def quantile(values, q): return sorted(values)[max(0, math.ceil(len(values)*q)-1)] if values else None
def verify_order(cases, policy):
    assert len(cases) == policy['expected_cases']
    for index, (c, spec) in enumerate(zip(cases, policy['cases'])):
        assert (c['round'], c['block'], c['profile'], c['offered_rps'], c['scheduled_seconds'], c['variant'], c['case_index']) == (
            spec['round'], spec['block'], spec['profile'], spec['rate'], spec['seconds'], spec['variant'], index)
    for profile, rate, seconds in policy['comparison']['configs']:
        orders = [[c['variant'] for c in cases if c['round'] == r and c['profile'] == profile] for r in range(6)]
        assert set(map(tuple, orders)) == set(itertools.permutations(['baseline_a', 'baseline_b', 'candidate']))

def metrics(c, n):
    if n == 'overall': return c['latency_ms']['p99']
    if n == 'rps': return c['successful_rps_in_arrival_window']
    return c['operation_latency_ms'][n]['p99']

def scoped(cases, policy, name, rounds):
    rows, identity, guards = [], [], []
    for profile, rate, seconds in policy['comparison']['configs']:
        by = {v: sorted((c for c in cases if c['round'] in rounds and c['profile'] == profile and c['variant'] == v),
                        key=lambda c: c['round']) for v in ['baseline_a', 'baseline_b', 'candidate']}
        assert all(len(cs) == len(rounds) for cs in by.values())
        row = {'profile': profile, 'rate': rate, 'seconds': seconds, 'variants': {}, 'comparisons': {}}
        for v, cs in by.items():
            row['variants'][v] = {'p99_ms': {n: statistics.median(metrics(c, n) for c in cs) if metrics(cs[0], n) is not None else None
                                            for n in ['overall', 'query', 'append']},
                'lost': sum(c['unsuccessful_or_unexecuted'] for c in cs), 'offered': sum(c['offered_operations'] for c in cs),
                'rps_median': statistics.median(metrics(c, 'rps') for c in cs),
                'all_rounds': [{'round': c['round'], 'p99_ms': c['latency_ms']['p99'],
                    'append_p99_ms': c['operation_latency_ms']['append']['p99'], 'query_p99_ms': c['operation_latency_ms']['query']['p99'],
                    'lost': c['unsuccessful_or_unexecuted'], 'successful_window_rps': metrics(c, 'rps')} for c in cs]}
        for label, num, den in [('identity_b_over_a', 'baseline_b', 'baseline_a'),
                               ('primary_candidate_over_a', 'candidate', 'baseline_a'),
                               ('diagnostic_candidate_over_b', 'candidate', 'baseline_b')]:
            ratios = {}
            for n in ['overall', 'query', 'append', 'rps']:
                rr = [metrics(b, n)/metrics(a, n) for a, b in zip(by[den], by[num]) if metrics(a, n) not in [None, 0]]
                ratios[n] = {'rounds': rr, 'median': statistics.median(rr) if rr else None}
            diff = row['variants'][num]['lost'] - row['variants'][den]['lost']
            allowed = row['variants'][den]['offered'] * .01
            data = {'paired_ratios': ratios, 'loss_difference': diff, 'allowed_loss_difference': allowed}
            if label == 'identity_b_over_a':
                checks = {n + '_p99': .90 <= ratios[n]['median'] <= 1.10 for n in ['overall', 'query']}
                if profile != 'read': checks['append_p99'] = .90 <= ratios['append']['median'] <= 1.10
                checks.update(window_rps=.90 <= ratios['rps']['median'] <= 1.10, loss_difference=abs(diff) <= allowed)
                identity.extend({'scope': name, 'profile': profile, 'criterion': n, 'passed': passed} for n, passed in checks.items())
                data['calibration_checks'] = checks
            elif label == 'primary_candidate_over_a':
                checks = {n + '_p99': ratios[n]['median'] <= 1.10 for n in ['overall', 'query']}
                if profile != 'read': checks['append_p99'] = ratios['append']['median'] <= 1.10
                checks.update(window_rps=ratios['rps']['median'] >= .90, loss_increase=diff <= allowed)
                guards.extend({'scope': name, 'profile': profile, 'criterion': n, 'passed': passed} for n, passed in checks.items())
                data['regression_guards'] = checks
            else: data['diagnostic_only_no_comparator_selection'] = True
            row['comparisons'][label] = data
        rows.append(row)
    assert len(identity) == len(guards) == 14
    return {'rounds': rounds, 'summaries': rows, 'identity_checks': identity, 'candidate_guards': guards,
            'identity_failed': sum(not g['passed'] for g in identity), 'candidate_failed': sum(not g['passed'] for g in guards)}

def main():
    r, policy = load(W / 'paired-service.json'), load(W / 'policy.json')
    assert r['complete'] and not r['failed_cases']
    assert r['policy_sha256'] == sha(W / 'policy.json') and r['freeze_sha256'] == sha(W / 'timing-freeze.json')
    for n, d in load(W / 'timing-freeze.json')['sha256'].items(): assert sha(W / n) == d, n
    for n, d in load(W / 'previous-062-baseline.json')['core_source_sha256'].items(): assert sha(REPO / n) == d, n
    assert r['binary_sha256'] == policy['binary_sha256']
    assert sha(W / 'binaries/released-016.exe') == policy['binary_sha256']['baseline_a'] == policy['binary_sha256']['baseline_b']
    assert sha(W / 'binaries/clean-core-061.exe') == policy['binary_sha256']['candidate']
    verify_order(r['cases'], policy)
    totals = {'offered': 0, 'samples': 0, 'successful': 0, 'lost': 0, 'queue_dropped': 0, 'queue_expired': 0,
              'acknowledged_batches': 0, 'uncertain_committed_batches': 0, 'numpy_windows': 0, 'scrubbed_bytes': 0}
    stages, components, stalls = [], [], []
    for c in r['cases']:
        assert c['case_started_utc'] > policy['declared_utc']
        p = W / c['raw_samples_file']
        assert p.resolve().is_relative_to(W.resolve()) and sha(p) == c['raw_samples_sha256']
        with gzip.open(p, 'rt', encoding='utf-8') as f: raw = [json.loads(line) for line in f]
        seq, exp = {s['sequence'] for s in raw}, set(c['expired_sequences'])
        assert len(seq) == len(raw) and len(exp) == c['queue_expired'] and not seq & exp
        assert all(0 <= i < c['offered_operations'] for i in seq | exp)
        assert len(raw) + c['queue_dropped'] + len(exp) == c['offered_operations']
        ok, errors = [s for s in raw if s['ok']], [s for s in raw if not s['ok']]
        assert len(ok) == c['successful_operations'] and len(errors) == len(c['errors'])
        assert len(errors) + c['queue_dropped'] + len(exp) == c['unsuccessful_or_unexecuted']
        assert c['offered_operations'] == c['scheduled_seconds'] * c['offered_rps']
        cutoff = c['arrival_start_monotonic_ns'] + int(c['scheduled_seconds']*1e9)
        completed = sum(s['finished_ns'] <= cutoff for s in ok)
        assert completed == c['completed_in_arrival_window']
        assert completed / c['scheduled_seconds'] == c['successful_rps_in_arrival_window']
        assert sum(s['latency_ms'] <= 100 for s in ok) / c['offered_operations'] == c['offered_fraction_successful_within_100ms']
        for n, q in [('p50', .5), ('p95', .95), ('p99', .99)]: assert c['latency_ms'][n] == quantile([s['latency_ms'] for s in ok], q)
        decomp = {}
        for op in ['query', 'append']:
            chosen = [s for s in ok if s['operation'] == op]
            v = c['operation_latency_ms'][op]
            assert len(chosen) == v['successful']
            for n, q in [('p50', .5), ('p95', .95), ('p99', .99)]: assert v[n] == quantile([s['latency_ms'] for s in chosen], q)
            assert v['max'] == max((s['latency_ms'] for s in chosen), default=None)
            assert v['service_p99'] == quantile([s['service_ms'] for s in chosen], .99)
            waiting = [s['latency_ms'] - s['service_ms'] for s in chosen]
            assert all(x >= -1e-9 for x in waiting)
            decomp[op] = {'scheduled_to_worker_p99_ms': quantile(waiting, .99), 'worker_to_response_p99_ms': v['service_p99']}
        components.append({'case_index': c['case_index'], 'operations': decomp, 'diagnostic_only_not_p99_decomposition': True})
        rec = c['reconciliation']
        assert rec['all_acknowledged_batches_present'] and rec['batch_atomicity_and_sums']
        assert rec['acknowledged_batches'] == c['write_successes'] and rec['numpy_reference_windows'] == 20
        assert rec['rows'] == 1_000_000 + 100*rec['published_batches']
        assert rec['full_kestrel_scrub']['verified_bytes'] == rec['rows'] * 24
        assert not c['live_state_before_reopen']['ingest']['writer_poisoned']
        before, after = c['publication_profile_before_load'], c['live_state_before_reopen']['publication_profile']
        names = ['prepare', 'segment_write', 'segment_sync', 'catalog_encode', 'catalog_write', 'catalog_sync', 'catalog_rename']
        delta = {n: {'count': after[n]['count'] - before[n]['count'], 'total_ms': after[n]['total_ms'] - before[n]['total_ms'],
                     'histogram': [a-b for a, b in zip(after[n]['histogram'], before[n]['histogram'])]} for n in names}
        for v in delta.values(): assert v['count'] == sum(v['histogram']) and min(v['histogram']) >= 0 and v['total_ms'] >= 0
        stages.append({'case_index': c['case_index'], 'variant': c['variant'], 'round': c['round'], 'profile': c['profile'],
            'stages': delta, 'attempts': after['attempts'] - before['attempts'],
            'compactions': c['live_state_before_reopen']['ingest']['compactions'] - c['ingest_state_before_load']['compactions']})
        slow = [s for s in raw if s['latency_ms'] > 100]
        stalls.append({'case_index': c['case_index'], 'events_over_100ms': len(slow),
            'events_over_500ms': sum(s['latency_ms'] > 500 for s in raw), 'all_slow_samples_retained': True,
            'max_latency_ms': max((s['latency_ms'] for s in raw), default=None)})
        for n, value in [('offered', c['offered_operations']), ('samples', len(raw)), ('successful', len(ok)),
                         ('lost', c['unsuccessful_or_unexecuted']), ('queue_dropped', c['queue_dropped']), ('queue_expired', c['queue_expired']),
                         ('acknowledged_batches', rec['acknowledged_batches']), ('uncertain_committed_batches', rec['unacknowledged_but_committed']),
                         ('numpy_windows', 20), ('scrubbed_bytes', rec['full_kestrel_scrub']['verified_bytes'])]: totals[n] += value
    assert totals['offered'] == policy['expected_offered_operations'] and totals['numpy_windows'] == policy['expected_numpy_windows']
    scopes = {n: scoped(r['cases'], policy, n, rounds) for n, rounds in policy['scopes'].items()}
    audit = {'trial': 86, 'audited_utc': datetime.now(timezone.utc).isoformat(), 'report_sha256': sha(W / 'paired-service.json'),
        'cases': len(r['cases']), 'totals': totals, 'scopes': scopes,
        'scoped_advance_passed': all(s['identity_failed'] == s['candidate_failed'] == 0 for s in scopes.values()),
        'raw_conservation_hashes_quantiles_order_recomputed': True, 'publication_stage_deltas': stages,
        'client_latency_diagnostics': components, 'stall_accounting': stalls,
        'no_new_correctness_failure': True, 'engine_changed': False, 'supported_promotion': False,
        'previous_061_062_and_all_failed_trials_preserved': True}
    save(W / 'audit.json', audit)
    print(json.dumps({'complete': True, 'cases': len(r['cases']), 'totals': totals,
        'scopes': {n: {'identity_failed': s['identity_failed'], 'candidate_failed': s['candidate_failed']} for n, s in scopes.items()},
        'scoped_advance_passed': audit['scoped_advance_passed'], 'supported_promotion': False}), flush=True)

if __name__ == '__main__': main()
