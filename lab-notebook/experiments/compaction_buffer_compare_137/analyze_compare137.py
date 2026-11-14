from pathlib import Path
import collections, json

W = Path('D:/Codex/Kestrel/work/perf-137')
a = json.loads((W / 'audit.json').read_text())
def summary(shape, metric, scope='full'):
    return next(s for s in a['summaries'] if s['workload'] == shape and s['metric'] == metric and s['scope'] == scope)
for shape in ['ordered', 'clustered', 'interleaved', 'duplicates', 'late', 'extreme']:
    w = summary(shape, 'wall_ms'); p = summary(shape, 'wall_p95_ms')
    print(json.dumps({'shape': shape, 'whole_p50_before': w['variants']['baseline_a']['p50'],
        'whole_p50_after': w['variants']['candidate']['p50'], 'paired_whole_change_percent': (w['CA_paired'] - 1) * 100,
        'whole_control': w['AA_paired'], 'whole_p95_before': p['variants']['baseline_a']['p95'],
        'whole_p95_after': p['variants']['candidate']['p95'], 'p95_AA': p['AA_paired'], 'p95_CA': p['CA_paired'],
        'paired_write_change_percent': (summary(shape, 'segment_write_ms')['CA_paired'] - 1) * 100,
        'paired_sync_change_percent': (summary(shape, 'segment_sync_ms')['CA_paired'] - 1) * 100,
        'paired_write_sync_change_percent': (summary(shape, 'write_sync_ms')['CA_paired'] - 1) * 100}))
print(json.dumps({'AA_failures_by_metric': collections.Counter(s['metric'] for s in a['identity_failed']),
    'guards_by_metric': collections.Counter(s['metric'] for s in a['guards_failed']),
    'calibrated_failed_guards': [s | {'variants': None} for s in a['guards_failed'] if s['AA_pass']],
    'goals': [s | {'variants': None} for s in a['summaries'] if 'goal_pass' in s]}))
