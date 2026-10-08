"""Independent conservation, ACK/event correlation, raw quantiles and fixed gates."""
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import itertools
import json
import math
import statistics

W = Path('D:/Codex/Kestrel/work/perf-090')
STAGES = ['prepare', 'segment_write', 'segment_sync', 'catalog_encode', 'catalog_write', 'catalog_sync', 'catalog_rename']

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
def quantile(values, fraction):
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)] if values else None
def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')

def verify_order(cases, policy):
    assert len(cases) == policy['expected_cases']
    for index, (case, spec) in enumerate(zip(cases, policy['cases'])):
        for name in ['round', 'block', 'family', 'stage', 'core', 'variant', 'binary', 'profile']:
            assert case[name] == spec[name], (index, name)
        assert case['offered_rps'] == spec['rate'] and case['scheduled_seconds'] == spec['seconds']
        assert case['case_index'] == index
    permutations = sorted(itertools.permutations(['baseline_a', 'baseline_b', 'candidate']))
    for family in policy['families']:
        assert family['binaries']['baseline_a'] == family['binaries']['baseline_b']
        for profile, _, _ in policy['configs']:
            for rounds in [list(range(12)), *policy['blocks']]:
                orders = [tuple(c['variant'] for c in cases if c['round'] == r and c['family'] == family['name'] and c['profile'] == profile) for r in rounds]
                assert sorted(orders) == sorted(permutations * (2 if len(rounds) == 12 else 1))

def trace_check(case, raw, base_rows):
    diagnostic = case['post_load_diagnostic']
    before, after = diagnostic['before'], diagnostic['after_before_trace_getter']
    assert before['pid'] == after['pid'] and before['creation_filetime'] == after['creation_filetime']
    assert before['peak_working_set_bytes'] <= after['peak_working_set_bytes']
    assert after['working_set_bytes'] <= after['peak_working_set_bytes']
    assert after['commit_bytes'] <= after['peak_commit_bytes']
    assert before['sample_monotonic_ns'] <= case['arrival_start_monotonic_ns']
    assert after['sample_monotonic_ns'] >= case['arrival_start_monotonic_ns'] + int(case['including_drain_seconds'] * 1e9) - 1
    cpu = after['kernel_100ns'] + after['user_100ns'] - before['kernel_100ns'] - before['user_100ns']
    assert cpu == diagnostic['charged_native_cpu_100ns'] and diagnostic['charged_native_cpu_seconds'] == cpu / 10000000
    assert diagnostic['peak_working_set_bytes'] == after['peak_working_set_bytes']
    trace = diagnostic['trace']
    if not case['binary'].endswith('-writer'):
        assert trace is None
        return {'traced': False, 'requests': 0, 'events': 0, 'publications': 0}
    assert not trace['active_cycle'] and trace['dropped_events'] == 0
    assert (trace['event_capacity'], trace['request_capacity']) == (4096, 16384)
    assert len(trace['events']) <= 4096 and len(trace['requests']) <= 16384
    attempts = {s['sequence']: s for s in raw if s['operation'] == 'append'}
    assert all(s['ok'] for s in attempts.values())
    assert len(trace['requests']) == len(attempts) == case['write_successes']
    seen = set()
    next_request, end = 0, 0
    prior = case['publication_profile_before_load']
    final = case['live_state_before_reopen']['publication_profile']
    attempt = prior['attempts']
    publications = []
    counts = {'append': 0, 'compact': 0, 'reclaim': 0}
    for event in trace['events']:
        assert event['kind'] in counts and event['completed']
        counts[event['kind']] += 1
        assert end <= event['start_ns'] <= event['end_ns'] <= trace['elapsed_ns']
        end = event['end_ns']
        assert event['request_start'] == next_request
        next_request += event['request_len']
        assert next_request <= len(trace['requests'])
        assert (event['request_len'] == 0) == (event['kind'] != 'append')
        publication = event['publication']
        if event['kind'] == 'reclaim':
            assert publication is None
            continue
        assert publication is not None and publication['completed']
        attempt += 1
        assert publication['attempt'] == attempt and publication['generation'] == attempt
        assert publication['new_receipts'] == publication['receipts_before'] == 0
        assert len(publication['stage_ms']) == 7 and all(math.isfinite(v) and v >= 0 for v in publication['stage_ms'])
        publications.append(publication)
        if event['kind'] == 'append':
            assert publication['rows'] == event['request_len'] * 100
            for request in trace['requests'][event['request_start']:next_request]:
                assert request['rows'] == 100 and 0 <= request['enqueue_to_collection_ns'] <= event['start_ns']
                key = request['first_key']
                assert (key - base_rows // 2) % 100 == 0
                seq = (key - base_rows // 2) // 100
                assert seq in attempts and seq not in seen
                receipt = attempts[seq]['append_receipt']
                assert receipt['affected'] == 100 and not receipt['duplicate'] and receipt['generation'] == publication['generation']
                seen.add(seq)
    assert seen == set(attempts) and next_request == len(trace['requests'])
    assert attempt == final['attempts'] and attempt == case['live_state_before_reopen']['generation']
    assert final['completed'] - prior['completed'] == len(publications)
    assert final['catalog_bytes_published'] - prior['catalog_bytes_published'] == sum(p['catalog_envelope_bytes'] for p in publications)
    stage_ms = []
    for index, name in enumerate(STAGES):
        total = sum(p['stage_ms'][index] for p in publications)
        assert math.isclose(total, final[name]['total_ms'] - prior[name]['total_ms'], rel_tol=1e-9, abs_tol=1e-6)
        stage_ms.append(total)
    ingest = case['live_state_before_reopen']['ingest']
    assert counts['append'] == ingest['durable_group_commits']
    assert counts['compact'] == ingest['compactions'] and counts['reclaim'] == ingest['durable_group_commits'] // 32
    assert not ingest['writer_poisoned'] and ingest['maintenance_errors'] == 0 and ingest['queued_payload_bytes'] == 0
    return {'traced': True, 'requests': len(seen), 'events': len(trace['events']), 'publications': len(publications), 'kinds': counts, 'stage_ms': stage_ms}

def metric(case, name):
    if name == 'overall':
        return case['latency_ms']['p99']
    if name == 'rps':
        return case['successful_rps_in_arrival_window']
    if name == 'peak':
        return case['post_load_diagnostic']['peak_working_set_bytes']
    if name == 'cpu':
        return case['post_load_diagnostic']['charged_native_cpu_seconds']
    return case['operation_latency_ms'][name]['p99']

def scope(cases, policy, family, name, rounds):
    gates = policy[family['stage'] + '_gates']
    rows, identities, guards = [], [], []
    for profile, rate, seconds in policy['configs']:
        by = {v: sorted([c for c in cases if c['family'] == family['name'] and c['round'] in rounds and c['profile'] == profile and c['variant'] == v], key=lambda c: c['round']) for v in ['baseline_a', 'baseline_b', 'candidate']}
        assert all(len(v) == len(rounds) for v in by.values())
        row = {'profile': profile, 'variants': {}, 'comparisons': {}}
        for variant, values in by.items():
            row['variants'][variant] = {'median_case_p99_ms': {n: statistics.median(metric(c, n) for c in values) if metric(values[0], n) is not None else None for n in ['overall', 'query', 'append']},
                'median_case_peak_working_set_bytes': statistics.median(metric(c, 'peak') for c in values),
                'median_case_cpu_seconds_diagnostic_only': statistics.median(metric(c, 'cpu') for c in values),
                'median_window_rps': statistics.median(metric(c, 'rps') for c in values),
                'lost': sum(c['unsuccessful_or_unexecuted'] for c in values), 'offered': sum(c['offered_operations'] for c in values),
                'all_rounds': [{'round': c['round'], 'p99_ms': c['latency_ms']['p99'], 'operation_p99': {n: c['operation_latency_ms'][n]['p99'] for n in ['query', 'append']},
                    'peak_working_set_bytes': metric(c, 'peak'), 'lost': c['unsuccessful_or_unexecuted']} for c in values]}
        for label, numerator, denominator in [('identity_b_over_a', 'baseline_b', 'baseline_a'), ('primary_candidate_over_a', 'candidate', 'baseline_a'), ('diagnostic_candidate_over_b', 'candidate', 'baseline_b')]:
            ratios = {}
            for n in ['overall', 'query', 'append', 'rps', 'peak', 'cpu']:
                paired = [metric(b, n) / metric(a, n) for a, b in zip(by[denominator], by[numerator]) if metric(a, n) not in [None, 0]]
                ratios[n] = {'all_rounds': paired, 'median': statistics.median(paired) if paired else None}
            peak_differences = [metric(b, 'peak') - metric(a, 'peak') for a, b in zip(by[denominator], by[numerator])]
            peak_difference = statistics.median(peak_differences)
            data = {'paired_ratios': ratios, 'paired_peak_difference_bytes': peak_differences, 'median_peak_difference_bytes': peak_difference}
            names = ['overall', 'query'] + (['append'] if profile != 'read' else [])
            if label == 'identity_b_over_a':
                low, high = gates['identity_p99_and_rps_range']
                checks = {n + '_p99': low <= ratios[n]['median'] <= high for n in names}
                checks['window_rps'] = low <= ratios['rps']['median'] <= high
                checks['zero_loss'] = row['variants'][numerator]['lost'] == row['variants'][denominator]['lost'] == 0
                ml, mh = gates['identity_peak_working_set_ratio_range']
                checks['peak_working_set_ratio'] = ml <= ratios['peak']['median'] <= mh
                checks['peak_working_set_difference'] = abs(peak_difference) <= gates['identity_peak_working_set_absolute_difference_max_bytes']
                identities.extend({'family': family['name'], 'scope': name, 'profile': profile, 'criterion': n, 'passed': passed} for n, passed in checks.items())
                data['identity_checks'] = checks
            elif label == 'primary_candidate_over_a':
                checks = {n + '_p99': ratios[n]['median'] <= gates['candidate_p99_max'] for n in names}
                checks['window_rps'] = ratios['rps']['median'] >= gates['candidate_window_rps_min']
                checks['zero_loss'] = row['variants'][numerator]['lost'] == 0
                checks['peak_working_set_ratio'] = ratios['peak']['median'] <= gates['candidate_peak_working_set_ratio_max']
                checks['peak_working_set_difference'] = peak_difference <= gates['candidate_peak_working_set_difference_max_bytes']
                guards.extend({'family': family['name'], 'scope': name, 'profile': profile, 'criterion': n, 'passed': passed} for n, passed in checks.items())
                data['candidate_guards'] = checks
            else:
                data['diagnostic_only_no_comparator_selection'] = True
            row['comparisons'][label] = data
        rows.append(row)
    assert len(identities) == len(guards) == 13
    return {'family': family['name'], 'scope': name, 'rounds': rounds, 'summaries': rows,
        'identity_checks': identities, 'candidate_guards': guards,
        'identity_failed': sum(not c['passed'] for c in identities), 'candidate_failed': sum(not c['passed'] for c in guards),
        'passed': all(c['passed'] for c in identities + guards)}

def main():
    report, policy = load(W / 'paired-service.json'), load(W / 'policy.json')
    assert report['complete'] and not report['failed_cases']
    assert report['policy_sha256'] == sha(W / 'policy.json') and report['freeze_sha256'] == sha(W / 'timing-freeze.json')
    for name, digest in load(W / 'timing-freeze.json')['sha256'].items():
        assert sha(W / name) == digest
    verify_order(report['cases'], policy)
    offered = successful = batches = scrubbed = 0
    trace_results = []
    stalls = []
    for case in report['cases']:
        path = W / case['raw_samples_file']
        assert sha(path) == case['raw_samples_sha256']
        with gzip.open(path, 'rt', encoding='utf-8') as stream:
            raw = [json.loads(line) for line in stream]
        assert len({s['sequence'] for s in raw}) == len(raw)
        assert all(s['operation'] in ['query', 'append'] for s in raw)
        assert len(raw) == case['offered_operations'] == int(case['scheduled_seconds'] * case['offered_rps'])
        assert sorted(s['sequence'] for s in raw) == list(range(len(raw)))
        assert all(s['ok'] for s in raw) and not case['errors']
        assert case['queue_dropped'] == case['queue_expired'] == case['unsuccessful_or_unexecuted'] == 0
        assert case['successful_operations'] == len(raw)
        start = case['arrival_start_monotonic_ns']
        end = start + int(case['scheduled_seconds'] * 1e9)
        within = sum(s['finished_ns'] <= end for s in raw)
        assert within == case['completed_in_arrival_window'] and within / case['scheduled_seconds'] == case['successful_rps_in_arrival_window']
        for sample in raw:
            assert sample['arrival_ns'] == start + int(sample['sequence'] * 1e9 / case['offered_rps'])
            assert math.isclose(sample['latency_ms'], (sample['finished_ns'] - sample['arrival_ns']) / 1e6, abs_tol=1e-12)
            assert sample['service_ms'] >= 0 and sample['latency_ms'] + 1e-9 >= sample['service_ms']
            if sample['operation'] == 'append':
                receipt = sample['append_receipt']
                assert receipt['affected'] == 100 and not receipt['duplicate'] and receipt['generation'] > 1
            else:
                assert sample['append_receipt'] is None
            if sample['latency_ms'] > 100:
                stalls.append({'case_index': case['case_index'], **sample})
        for operation in ['overall', 'query', 'append']:
            chosen = raw if operation == 'overall' else [s for s in raw if s['operation'] == operation]
            metrics = case['latency_ms'] if operation == 'overall' else case['operation_latency_ms'][operation]
            values = [s['latency_ms'] for s in chosen]
            for name, fraction in [('p50', .5), ('p95', .95), ('p99', .99)]:
                assert metrics[name] == quantile(values, fraction)
            assert metrics['max'] == max(values, default=None)
            if operation != 'overall':
                assert metrics['successful'] == len(chosen)
                assert metrics['service_p99'] == quantile([s['service_ms'] for s in chosen], .99)
        acked = sum(s['operation'] == 'append' for s in raw)
        assert acked == case['write_successes'] and len(raw) - acked == case['read_successes']
        recovery = case['reconciliation']
        assert recovery['acknowledged_batches'] == recovery['published_batches'] == acked
        assert recovery['unacknowledged_but_committed'] == 0 and recovery['all_acknowledged_batches_present'] and recovery['batch_atomicity_and_sums']
        assert recovery['rows'] == policy['base_rows'] + acked * 100 and recovery['numpy_reference_windows'] == 20
        assert recovery['full_kestrel_scrub']['verified_bytes'] == recovery['rows'] * 24
        trace_results.append({'case_index': case['case_index'], **trace_check(case, raw, policy['base_rows'])})
        offered += len(raw)
        successful += case['successful_operations']
        batches += acked
        scrubbed += recovery['full_kestrel_scrub']['verified_bytes']
    scopes = [scope(report['cases'], policy, family, name, rounds) for family in policy['families'] for name, rounds in [('full', list(range(12))), ('block_0', policy['blocks'][0]), ('block_1', policy['blocks'][1])]]
    result = {'trial': 90, 'correctness_passed': True, 'cases': len(report['cases']), 'offered': offered, 'successful': successful,
        'lost': 0, 'acknowledged_batches': batches, 'numpy_windows': len(report['cases']) * 20, 'full_crc_bytes': scrubbed,
        'scopes': scopes, 'all_required_scopes_passed': all(s['passed'] for s in scopes),
        'identity_failed_total': sum(s['identity_failed'] for s in scopes), 'candidate_failed_total': sum(s['candidate_failed'] for s in scopes),
        'trace_results': trace_results, 'traced_requests_correlated': sum(t['requests'] for t in trace_results),
        'events_over_100ms': len(stalls), 'all_events_over_100ms': stalls, 'supported': '0.3.16',
        'no_supported_release_or_competitor_claim': True, 'cpu_diagnostic_only': True, 'no_exclusive_p99_or_physical_cause': True}
    save(W / 'audit.json', result)
    print(json.dumps({k: result[k] for k in ['correctness_passed', 'cases', 'offered', 'successful', 'lost', 'all_required_scopes_passed', 'identity_failed_total', 'candidate_failed_total']}))
    return result

if __name__ == '__main__':
    main()
