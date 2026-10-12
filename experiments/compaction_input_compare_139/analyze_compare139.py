from pathlib import Path
import collections, json

W = Path('D:/Codex/Kestrel/work/perf-139')
a = json.loads((W / 'audit.json').read_text())
assert a['complete'] and a['correctness_passed'] and a['fresh_cases'] == 216

def summary(shape, metric, scope='full'):
    return next(s for s in a['summaries'] if s['workload'] == shape and s['metric'] == metric and s['scope'] == scope)

for shape in ['ordered', 'clustered', 'interleaved', 'duplicates', 'late', 'extreme']:
    w = summary(shape, 'wall_ms'); p = summary(shape, 'wall_p95_ms'); prep = summary(shape, 'prepare_ms')
    print(json.dumps({'shape': shape, 'whole_p50_before': w['variants']['baseline_a']['p50'],
        'whole_p50_after': w['variants']['candidate']['p50'], 'paired_whole_change_percent': (w['CA_paired'] - 1) * 100,
        'whole_AA': w['AA_paired'], 'whole_AA_pass': w['AA_pass'],
        'prep_p50_before': prep['variants']['baseline_a']['p50'], 'prep_p50_after': prep['variants']['candidate']['p50'],
        'paired_prepare_change_percent': (prep['CA_paired'] - 1) * 100, 'prepare_AA': prep['AA_paired'], 'prepare_AA_pass': prep['AA_pass'],
        'whole_p95_before': p['variants']['baseline_a']['p95'], 'whole_p95_after': p['variants']['candidate']['p95'],
        'p95_AA': p['AA_paired'], 'p95_CA': p['CA_paired'], 'p95_AA_pass': p['AA_pass'],
        'paired_write_sync_change_percent': (summary(shape, 'write_sync_ms')['CA_paired'] - 1) * 100}))

print(json.dumps({'AA_failures_by_metric': collections.Counter(s['metric'] for s in a['identity_failed']),
    'guards_by_metric': collections.Counter(s['metric'] for s in a['guards_failed']),
    'calibrated_failed_guards': [s | {'variants': None} for s in a['guards_failed'] if s['AA_pass']],
    'goals': [s | {'variants': None} for s in a['summaries'] if 'goal_pass' in s],
    'clustered_all_scopes': [summary('clustered', metric, scope) | {'variants': None}
        for metric in ['wall_ms','prepare_ms','write_sync_ms','segment_write_ms','segment_sync_ms','catalog_sync_ms','wall_p95_ms','setup_p95_ms']
        for scope in ['full','first_half','second_half']]}))
