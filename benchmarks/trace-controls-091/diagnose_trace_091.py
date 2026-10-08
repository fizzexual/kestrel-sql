"""Post-cohort descriptive trace analysis; never changes frozen gates or runs native."""
from pathlib import Path
import gzip
import hashlib
import json
import math
import statistics
import sys


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def q(values, fraction):
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)] if values else None


def diagnose(directory):
    directory = Path(directory)
    report = json.loads((directory / 'paired-service.json').read_text(encoding='utf-8'))
    audit = json.loads((directory / 'audit.json').read_text(encoding='utf-8'))
    assert report['complete'] and audit['correctness_passed'] and audit['all_required_scopes_passed']
    groups, cases, waits = [], [], []
    counts = {'append': 0, 'compact': 0, 'reclaim': 0}
    for case in report['cases']:
        trace = case['post_load_diagnostic']['trace']
        if trace is None:
            continue
        assert trace['dropped_events'] == 0 and not trace['active_cycle']
        raw_path = directory / case['raw_samples_file']
        assert sha(raw_path) == case['raw_samples_sha256']
        with gzip.open(raw_path, 'rt', encoding='utf-8') as stream:
            raw = {sample['sequence']: sample for sample in map(json.loads, stream)}
        durations = {'append': [], 'compact': [], 'reclaim': []}
        stages = [0.0] * 7
        previous_kind = None
        case_waits = []
        for event in trace['events']:
            kind = event['kind']
            counts[kind] += 1
            duration = (event['end_ns'] - event['start_ns']) / 1e6
            durations[kind].append(duration)
            publication = event['publication']
            if publication is not None:
                for index, value in enumerate(publication['stage_ms']):
                    stages[index] += value
            if kind == 'append':
                requests = trace['requests'][event['request_start']:event['request_start'] + event['request_len']]
                samples = []
                request_waits = []
                for request in requests:
                    key = request['first_key']
                    assert (key - 500000) % 100 == 0
                    sequence = (key - 500000) // 100
                    sample = raw[sequence]
                    assert sample['ok'] and sample['operation'] == 'append'
                    assert sample['append_receipt']['generation'] == publication['generation']
                    samples.append(sample)
                    request_waits.append(request['enqueue_to_collection_ns'] / 1e6)
                waits.extend(request_waits)
                case_waits.extend(request_waits)
                groups.append({'case_index': case['case_index'], 'core': case['core'], 'round': case['round'],
                    'attempt': publication['attempt'], 'generation': publication['generation'],
                    'requests': len(requests), 'native_append_interval_ms': duration,
                    'recorded_stage_ms': publication['stage_ms'],
                    'summed_stage_ms': sum(publication['stage_ms']),
                    'summed_sync_stage_ms': publication['stage_ms'][2] + publication['stage_ms'][5],
                    'previous_recorded_event_kind': previous_kind,
                    'maximum_enqueue_to_collection_ms': max(request_waits),
                    'maximum_associated_service_latency_ms': max(s['latency_ms'] for s in samples),
                    'associated_service_samples_over_100ms': sum(s['latency_ms'] > 100 for s in samples),
                    'sequences': [s['sequence'] for s in samples]})
            previous_kind = kind
        cases.append({'case_index': case['case_index'], 'core': case['core'], 'profile': case['profile'],
            'requests': len(case_waits), 'enqueue_to_collection_p99_ms': q(case_waits, .99),
            'native_event_p99_ms': {kind: q(values, .99) for kind, values in durations.items()},
            'native_event_distributions_ms': {kind: {'count': len(values), 'p50': q(values,.5),
                'p95': q(values,.95), 'p99': q(values,.99), 'max': max(values,default=None),
                'sum': sum(values)} for kind,values in durations.items()},
            'recorded_publication_stage_sums_ms': stages,
            'sync_fraction_of_summed_publication_stage_time': (stages[2] + stages[5]) / sum(stages) if sum(stages) else None})
    assert len(waits) == audit['traced_requests_correlated']
    failures = []
    for scope in audit['scopes']:
        identity = {(check['profile'], check['criterion']): check['passed'] for check in scope['identity_checks']}
        for check in scope['candidate_guards']:
            if not check['passed']:
                failures.append({**check, 'corresponding_identity_passed': identity[check['profile'], check['criterion']]})
    return {'trial': 91, 'raw_report_sha256': sha(directory / 'paired-service.json'),
        'raw_audit_sha256': sha(directory / 'audit.json'), 'post_cohort_descriptive_only': True,
        'writer_latency_overhead_qualified_in_091_two_profile_full_and_halves': True, 'no_exclusive_p99_or_physical_cause': True,
        'clock_domains_not_aligned': True, 'no_gate_or_comparator_change': True,
        'trace_event_counts': counts, 'traced_requests': len(waits),
        'pooled_traced_request_enqueue_to_collection_p99_ms': q(waits, .99),
        'append_groups': len(groups), 'groups_with_service_sample_over_100ms': sum(g['associated_service_samples_over_100ms'] > 0 for g in groups),
        'associated_service_samples_over_100ms': sum(g['associated_service_samples_over_100ms'] for g in groups),
        'candidate_failures': failures, 'calibrated_candidate_failure_count': sum(f['corresponding_identity_passed'] for f in failures),
        'cases': cases, 'append_group_records': groups}


if __name__ == '__main__':
    directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('D:/Codex/Kestrel/work/perf-091')
    result = diagnose(directory)
    (directory / 'trace-group-diagnostics.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ['cases', 'append_group_records', 'candidate_failures']}, indent=2))
