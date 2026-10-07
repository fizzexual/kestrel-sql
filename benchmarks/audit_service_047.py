"""Recompute service metrics from retained raw samples after every load has stopped."""
import ast
import datetime
import gzip
import hashlib
import json
import statistics
from pathlib import Path

from stress_compare import percentile

ROOT = Path(__file__).resolve().parents[1]
B = ROOT / 'benchmarks'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def group_summary(cases):
    return {variant: {
        'version': selected[0]['version'], 'runs': len(selected),
        'median_successful_rps': statistics.median(c['successful_rps_in_arrival_window'] for c in selected),
        'median_run_p99_ms': statistics.median(c['latency_ms']['p99'] for c in selected),
        'p99_range_ms': [min(c['latency_ms']['p99'] for c in selected), max(c['latency_ms']['p99'] for c in selected)],
        'query_median_run_p99_ms': statistics.median(c['operation_latency_ms']['query']['p99'] for c in selected),
        'append_median_run_p99_ms': statistics.median(c['operation_latency_ms']['append']['p99'] for c in selected),
        'offered': sum(c['offered_operations'] for c in selected),
        'unsuccessful_or_unexecuted': sum(c['unsuccessful_or_unexecuted'] for c in selected),
        'runs_zero_loss_and_p99_at_most_100ms': sum(c['unsuccessful_or_unexecuted'] == 0 and c['latency_ms']['p99'] <= 100 for c in selected),
        'acked_batches': sum(c['reconciliation']['acknowledged_batches'] for c in selected),
        'unacknowledged_committed_batches': sum(c['reconciliation']['unacknowledged_but_committed'] for c in selected)
    } for variant in sorted({c['variant'] for c in cases})
      if (selected := [c for c in cases if c['variant'] == variant])}


def main():
    provenance = json.loads((B / 'baseline-0.3.16-provenance.json').read_text())
    qualification = json.loads((ROOT / 'verification.json').read_text())
    assert qualification['version'] == provenance['version'] == '0.3.16'
    assert qualification['source_sha256'] == provenance['core_source_sha256']
    for relative, expected in qualification['source_sha256'].items():
        assert sha(ROOT / relative) == expected, relative
        assert sha(B / 'baseline-0.3.16-source' / relative) == expected, relative
    for name, expected in provenance['baseline_binary_sha256'].items():
        assert sha(ROOT / 'bin' / name) == expected, name
        assert sha(ROOT / 'bin/baseline-0.3.16' / name) == expected, name
    reports, evidence, all_cases = {}, {}, []
    samples_total = offered_total = 0
    for label in ['baseline', 'policy', 'reference']:
        path = B / f'service-047-{label}.json'
        report = json.loads(path.read_text())
        assert report['complete'] and not report['failed_cases'], label
        assert report['bridge_sha256'] == provenance['baseline_binary_sha256']['kestrel-stress.exe']
        assert report['base_rows'] == 1_000_000
        frozen = B / f'service-047-{label}-harness.py'
        assert sha(frozen) == report['harness_sha256']['service_047.py']
        ast.parse(frozen.read_text())
        for name in ['stress_compare.py', 'host_telemetry.py']:
            assert sha(B / name) == report['harness_sha256'][name]
        for case in report['cases']:
            sample_path = B / case['raw_samples_file']
            assert sample_path.resolve().is_relative_to(B.resolve())
            assert sha(sample_path) == case['raw_samples_sha256']
            with gzip.open(sample_path, 'rt', encoding='utf-8') as stream:
                raw = [json.loads(line) for line in stream]
            sequences = {s['sequence'] for s in raw}
            expired = case['expired_sequences']
            assert len(sequences) == len(raw) and len(set(expired)) == len(expired)
            assert not sequences.intersection(expired)
            assert all(0 <= s < case['offered_operations'] for s in sequences.union(expired))
            ok = [s for s in raw if s['ok']]
            failed = [s for s in raw if not s['ok']]
            assert len(raw) + case['queue_dropped'] + len(expired) == case['offered_operations']
            assert len(ok) == case['successful_operations']
            assert len(failed) + case['queue_dropped'] + len(expired) == case['unsuccessful_or_unexecuted']
            assert len(case['errors']) == len(failed), 'Connection errors must not be silently counted as completed requests'
            cutoff = case['arrival_start_monotonic_ns'] + int(case['scheduled_seconds'] * 1e9)
            completed = sum(s['finished_ns'] <= cutoff for s in ok)
            assert completed == case['completed_in_arrival_window']
            assert completed / case['scheduled_seconds'] == case['successful_rps_in_arrival_window']
            assert sum(s['latency_ms'] <= 100 for s in ok) / case['offered_operations'] == case['offered_fraction_successful_within_100ms']
            for op in ['query', 'append']:
                selected = [s for s in ok if s['operation'] == op]
                measured = case['operation_latency_ms'][op]
                assert measured['successful'] == len(selected)
                for field, p in [('p50', .5), ('p95', .95), ('p99', .99)]:
                    assert measured[field] == percentile([s['latency_ms'] for s in selected], p)
                assert measured['service_p99'] == percentile([s['service_ms'] for s in selected], .99)
            for field, p in [('p50', .5), ('p95', .95), ('p99', .99)]:
                assert case['latency_ms'][field] == percentile([s['latency_ms'] for s in ok], p)
            reconciled = case['reconciliation']
            assert reconciled['all_acknowledged_batches_present'] and reconciled['batch_atomicity_and_sums']
            assert reconciled['numpy_reference_windows'] == 20
            assert reconciled['acknowledged_batches'] == case['write_successes']
            assert reconciled['rows'] == 1_000_000 + 100 * reconciled['published_batches']
            if case['engine'] == 'kestrel':
                assert case['version'] == '0.3.16'
                assert reconciled['full_kestrel_scrub']['verified_bytes'] == 24 * reconciled['rows']
                assert not case['live_state_before_reopen']['ingest']['writer_poisoned']
                before = case['publication_profile_before_load']
                after = case['live_state_before_reopen']['publication_profile']
                stages = {name: {
                    'count': after[name]['count'] - before[name]['count'],
                    'total_ms': after[name]['total_ms'] - before[name]['total_ms'],
                    'histogram_delta': [a - b for a, b in zip(after[name]['histogram'], before[name]['histogram'])]
                } for name in ['prepare', 'segment_write', 'segment_sync', 'catalog_encode',
                               'catalog_write', 'catalog_sync', 'catalog_rename']}
                for values in stages.values():
                    assert values['count'] == sum(values['histogram_delta'])
                    assert min(values['histogram_delta']) >= 0 and values['total_ms'] >= 0
                total = sum(v['total_ms'] for v in stages.values())
                case['derived_publication_stages'] = stages
                case['derived_sync_share'] = ((stages['segment_sync']['total_ms'] + stages['catalog_sync']['total_ms']) / total if total else None)
            samples_total += len(raw)
            offered_total += case['offered_operations']
        reports[label] = report
        evidence[label] = {'path': path.name, 'sha256': sha(path), 'cases': len(report['cases']), 'frozen_harness_sha256': sha(frozen)}
        all_cases.extend(report['cases'])
    assert [len(reports[n]['cases']) for n in ['baseline', 'policy', 'reference']] == [7, 27, 18]
    reference = group_summary(reports['reference']['cases'])
    assert len(reference) == 6 and all(v['runs'] == 3 for v in reference.values())
    reference_pairs = {}
    reference_cases = reports['reference']['cases']
    for name in reference:
        assert len({c['version'] for c in reference_cases if c['variant'] == name}) == 1
        if name == 'kestrel':
            continue
        reference_pairs[name] = {}
        for metric in ['mixed', 'query', 'append']:
            ratios = []
            for turn in range(3):
                kestrel = next(c for c in reference_cases if c['variant'] == 'kestrel' and c['round'] == turn)
                other = next(c for c in reference_cases if c['variant'] == name and c['round'] == turn)
                def value(c):
                    return (c['latency_ms']['p99'] if metric == 'mixed' else c['operation_latency_ms'][metric]['p99'])
                ratios.append(value(kestrel) / value(other))
            reference_pairs[name][metric] = {'kestrel_over_reference_p99_by_round': ratios,
                                           'median_ratio': statistics.median(ratios),
                                           'rounds_kestrel_lower_p99': sum(v < 1 for v in ratios)}
    policy = {f'{profile}/{rate}': group_summary([c for c in reports['policy']['cases'] if c['profile'] == profile and c['offered_rps'] == rate])
              for profile, rate in [('mixed', 2000), ('mixed', 10000), ('write', 500)]}
    result = {'version': '0.3.16', 'engine_changed': False,
              'audited_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'reports': evidence, 'cases': len(all_cases), 'offered_operations': offered_total,
              'executed_raw_samples': samples_total,
              'raw_samples_accounting_and_quantiles_recomputed': True,
              'all_acknowledged_batches_reconciled': True,
              'all_final_batch_atomicity_and_numpy_windows_passed': True,
              'source_and_supported_binaries_match_released_baseline': True,
              'same_current_qualification': '77 debug and 77 release tests; 4000 SQL cases/reference; publication/source fault suites already qualified in 046. No redundant engine build or rerun in 047',
              'reference_summary': reference, 'reference_within_round_ratios': reference_pairs,
              'policy_summary': policy,
              'acknowledged_batches_checked': sum(c['reconciliation']['acknowledged_batches'] for c in all_cases),
              'unacknowledged_committed_batches': sum(c['reconciliation']['unacknowledged_but_committed'] for c in all_cases),
              'numpy_reference_windows_checked': sum(c['reconciliation']['numpy_reference_windows'] for c in all_cases),
              'kestrel_cold_reopen_cases': sum(c['engine'] == 'kestrel' for c in all_cases),
              'kestrel_full_scrub_bytes': sum(c['reconciliation']['full_kestrel_scrub']['verified_bytes'] for c in all_cases if c['engine'] == 'kestrel'),
              'baseline_cases': reports['baseline']['cases'],
              'decision': 'Do not change the default or claim an engine improvement. Existing coalescing options do not consistently solve write-tail failures; strong temporal variability remains. Preserve failures and prioritize a separately defined, fault-tested publication-format hypothesis.',
              'limits': 'Shared local desktop; different test-bridge/native interfaces and physical indexes. No version-to-version pair, production qualification, Facebook scale, distributed result or universal ranking.'}
    (B / 'service-047-audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ['cases', 'offered_operations', 'executed_raw_samples', 'engine_changed']}))
    print(json.dumps(reference, indent=2))


if __name__ == '__main__':
    main()
