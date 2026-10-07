"""Posthoc stage totals; no causal claim about service p99."""
from datetime import datetime, timezone
import json
from pathlib import Path

W = Path(__file__).resolve().parent
a = json.loads((W / 'paired-service-audit.json').read_text())
rows = []
for summary in a['summaries']:
    row = {'profile': summary['profile'], 'rate': summary['rate'], 'seconds': summary['seconds'], 'variants': {}}
    for variant in ['baseline', 'candidate']:
        cases = [c for c in a['publication_stage_deltas'] if
                 (c['profile'], c['rate'], c['seconds'], c['variant']) == (row['profile'], row['rate'], row['seconds'], variant)]
        totals = {n: sum(c['stages'][n]['total_ms'] for c in cases) for n in cases[0]['stages']}
        counts = {n: sum(c['stages'][n]['count'] for c in cases) for n in cases[0]['stages']}
        recorded = sum(totals.values())
        sync = totals['segment_sync'] + totals['catalog_sync']
        row['variants'][variant] = {'recorded_stage_total_ms': recorded, 'sync_ms': sync,
                                   'sync_fraction_of_recorded_stages': sync / recorded if recorded else None,
                                   'stage_ms': totals, 'stage_counts': counts,
                                   'attempts': sum(c['attempts'] for c in cases),
                                   'compactions': sum(c['compactions'] for c in cases)}
    rows.append(row)
report = {'trial': 61, 'created_utc': datetime.now(timezone.utc).isoformat(), 'posthoc_diagnostic_only': True,
          'profiles': rows,
          'limits': ['Only recorded publication stages; not full workload elapsed time or a decomposition of p99.',
                     'Aggregate stage totals do not identify the cause of paired service regressions.',
                     'Parser is the only semantic core edit; no write-path change; shared-host variation and batching must be controlled independently.'],
          'next_control': ['Predeclare new identical-binary A/A service controls and balanced order; keep all 061 outcomes unchanged.',
                           'Compare durable attempts/grouping and sync distributions before changing write logic; no weakening durable ACK.']}
(W / 'publication-profile-analysis.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'profiles': len(rows), 'diagnostic_only': True}))
