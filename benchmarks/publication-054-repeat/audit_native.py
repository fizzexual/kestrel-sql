"""Independent post-timing audit; no execution during database timings."""
from pathlib import Path
import datetime, hashlib, json, math, statistics

W = Path(__file__).resolve().parent

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def quantile(values, q):
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    left = math.floor(index)
    right = math.ceil(index)
    return ordered[left] + (ordered[right] - ordered[left]) * (index - left)

policy = json.loads((W / 'policy.json').read_text(encoding='utf-8'))
report = json.loads((W / 'native-results.json').read_text(encoding='utf-8'))
assert report['completed'] and len(report['cases']) == len(policy['cases']) == 14 and not report['failures']
assert sha(W / 'policy.json') == report['policy_sha256']
cases = []
for item, spec in zip(report['cases'], policy['cases']):
    assert item['spec'] == spec
    raw = W / 'raw' / (item['label'] + '.stdout.json')
    status = json.loads(raw.with_name(item['label'] + '.status.json').read_text(encoding='utf-8'))
    assert status['exit_code'] == 0 and not status.get('timeout') and sha(raw) == item['stdout_sha256']
    result = json.loads(raw.read_text(encoding='utf-8'))
    n = spec['seed_receipts'] + 100 * 256
    assert result['after']['rows'] == n and result['after']['recorded_batch_ids'] == spec['seed_receipts'] + 256
    assert result['rows_and_sum_match'] and result['reopen_retry_and_full_scrub_passed']
    latency = result['raw_latency_ms']
    assert len(latency) == len(result['raw_catalog_bytes']) == 256
    assert all(math.isfinite(v) and v >= 0 for v in latency)
    before = result['before']['publication_profile']
    after = result['after']['publication_profile']
    stages = {}
    for key, final in after.items():
        if not isinstance(final, dict):
            continue
        initial = before[key]
        delta = {'count': final['count'] - initial['count'], 'total_ms': final['total_ms'] - initial['total_ms'],
                 'histogram': [a - b for a, b in zip(final['histogram'], initial['histogram'])],
                 'cumulative_max_including_prefill_ms': final['max_ms']}
        assert sum(delta['histogram']) == delta['count'] and min(delta['histogram']) >= 0
        stages[key] = delta
    counters = {key: after[key] - before[key] for key in after if not isinstance(after[key], dict)}
    assert counters['attempts'] == counters['completed']
    assert counters['attempts'] >= 256
    sync_ms = sum(v['total_ms'] for k, v in stages.items() if k.endswith('_sync'))
    total_ms = sum(v['total_ms'] for v in stages.values())
    tails = [{'append_index': i, 'latency_ms': v, 'catalog_file_bytes': result['raw_catalog_bytes'][i]}
             for i, v in enumerate(latency) if v > 500]
    cases.append({'spec': spec, 'label': item['label'], 'rows': n,
                  'p50_ms': quantile(latency, .5), 'p95_ms': quantile(latency, .95), 'p99_ms': quantile(latency, .99),
                  'max_ms': max(latency), 'append_total_ms': sum(latency),
                  'slow_over_500ms': sum(v > 500 for v in latency), 'slow_over_1000ms': sum(v > 1000 for v in latency),
                  'tail_samples': tails, 'catalog_file_bytes_sampled': sum(result['raw_catalog_bytes']),
                  'maintenance_ms': result['maintenance_ms'], 'reopen_ms': result['reopen_ms'],
                  'publication_counter_deltas_including_maintenance': counters,
                  'stage_deltas_including_maintenance': stages, 'stage_total_ms_including_maintenance': total_ms,
                  'sync_total_ms_including_maintenance': sync_ms, 'sync_fraction_of_stages': sync_ms / total_ms})
summaries = []
for size in [99000]:
    matched = {}
    for variant in ['base_050', 'compact_053']:
        selected = [c for c in cases if c['spec']['variant'] == variant and c['spec']['seed_receipts'] == size]
        assert len(selected) == 7
        matched[variant] = {key: statistics.median(c[key] for c in selected)
                            for key in ['p50_ms', 'p95_ms', 'p99_ms', 'max_ms', 'reopen_ms']}
        matched[variant].update(slow_over_500ms=sum(c['slow_over_500ms'] for c in selected),
                                slow_over_1000ms=sum(c['slow_over_1000ms'] for c in selected))
    pairs = []
    for turn in range(7):
        b = next(c for c in cases if c['spec'] == {'round': turn, 'seed_receipts': size, 'variant': 'base_050', 'repetitions': 256, 'batch_rows': 100})
        t = next(c for c in cases if c['spec'] == {'round': turn, 'seed_receipts': size, 'variant': 'compact_053', 'repetitions': 256, 'batch_rows': 100})
        pairs.append({'round': turn, 'p50_ratio': t['p50_ms'] / b['p50_ms'], 'p99_ratio': t['p99_ms'] / b['p99_ms'],
                      'baseline_p99_ms': b['p99_ms'], 'trial_p99_ms': t['p99_ms']})
    summaries.append({'seed_receipts': size, 'variants': matched, 'pairs': pairs,
                      'paired_p50_ratio': statistics.median(p['p50_ratio'] for p in pairs),
                      'paired_p99_ratio': statistics.median(p['p99_ratio'] for p in pairs)})
out = {'audited_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
       'cases': cases, 'summaries': summaries, 'quantile_method': 'linear Type 7, all 256 raw append samples per case',
       'append_samples': 14 * 256, 'rows_appended_under_timers': 14 * 256 * 100,
       'cold_duplicate_retries': 14 * 3, 'scrubbed_bytes': sum(c['rows'] * 24 * 2 for c in cases),
       'all_raw_hashes_status_counts_histogram_deltas_and_correctness_flags_verified': True,
       'driver_checks': 'Exact COUNT/SUM, two full CRC scrubs, cold reopen and three duplicate retries per fixture; no forced crash in this fresh diagnostic',
       'scope': '054 independent follow-up on unchanged 050/053; original 053 failure retained. Native closed-loop profiling only; stage deltas include maintenance; no fresh competitor or promotion claim',
       'default_engine_changed': False, 'trial_promoted': False}
(W / 'native-audit.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: v for k, v in out.items() if k != 'cases'}, indent=2))
