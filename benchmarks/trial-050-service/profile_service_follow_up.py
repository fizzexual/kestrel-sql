from pathlib import Path
import datetime, hashlib, json

w = Path(__file__).parent
root = w.parents[1] / 'outputs/kestrel-sql'
r = json.loads((w / 'paired-service.json').read_text(encoding='utf-8'))
a = json.loads((w / 'paired-service-audit.json').read_text(encoding='utf-8'))
assert r['complete'] and a['raw_quantiles_accounting_uniqueness_and_hashes_recomputed']
cases = []
for c, stages in zip(r['cases'], a['publication_stage_deltas']):
    before = c['ingest_state_before_load']
    after = c['live_state_before_reopen']['ingest']
    live_ms = sum(after[n] - before[n] for n in ['publication_total_ms', 'compaction_total_ms'])
    stage_ms = sum(v['total_ms'] for v in stages['stages'].values())
    sync_ms = sum(v['total_ms'] for n, v in stages['stages'].items() if n.endswith('_sync'))
    reopened = stages['stages'].get('bundle_reopen', {'count': 0, 'total_ms': 0})
    assert live_ms + .01 >= stage_ms
    if c['variant'] == 'bundle_trial':
        assert reopened['count'] == 0 and reopened['total_ms'] == 0
    cases.append({k: c[k] for k in ['variant', 'round', 'profile', 'offered_rps', 'scheduled_seconds']} |
                 {'attempts': stages['attempts'], 'writer_plus_compaction_ms': live_ms,
                  'stage_sum_ms': stage_ms, 'outside_stage_sum_ms': live_ms - stage_ms,
                  'sync_ms': sync_ms, 'retained_reopen_count': reopened['count'],
                  'retained_reopen_ms': reopened['total_ms']})
totals = {}
for variant in ['baseline', 'bundle_trial']:
    selected = [c for c in cases if c['variant'] == variant]
    total = {n: sum(c[n] for c in selected) for n in
             ['attempts', 'writer_plus_compaction_ms', 'stage_sum_ms', 'outside_stage_sum_ms', 'sync_ms', 'retained_reopen_count', 'retained_reopen_ms']}
    total['sync_share_of_writer_plus_compaction'] = total['sync_ms'] / total['writer_plus_compaction_ms']
    totals[variant] = total
proof = {'audited_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'method': 'post-timing counter deltas, all 36 cases; writer and compaction timers versus non-overlapping publication-stage sums',
         'report_sha256': hashlib.sha256((w / 'paired-service.json').read_bytes()).hexdigest(),
         'totals': totals, 'cases': cases,
         'limits': 'Commit groups and stage counts differ. Aggregate stage totals are not paired per-request speed ratios and do not identify physical disk or filter-driver causes.',
         'decision': '050 correctness is qualified but sustained-service gate fails: 475/90000 minute-workload arrivals lost. Synchronization/tail stalls need native publication profiling; compare fully synchronized layouts without changing ACK or disabling sync. Unique-generation validation executes only at Archive::open; do not attribute live tail variation to that startup check. Preserve all 049 and 050 failures and current 0.3.16 baseline.'}
(root / 'benchmarks/trial-050-service-follow-up.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'totals': totals, 'decision': proof['decision']}))
