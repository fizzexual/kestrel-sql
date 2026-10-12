from pathlib import Path
import json
W=Path('D:/Codex/Kestrel/work/perf-146')
a=json.loads((W/'audit.json').read_text(encoding='utf-8-sig'))
def small(s):return {k:s[k] for k in ['workload','scope','metric','AA_paired','CA_paired','AA_pass','candidate_guard_pass'] if k in s}|{'A_p50':s['variants']['baseline_a']['p50'],'C_p50':s['variants']['candidate']['p50'],'A_p95':s['variants']['baseline_a']['p95'],'C_p95':s['variants']['candidate']['p95']}|({'goal_pass':s['goal_pass']} if 'goal_pass' in s else {})
print(json.dumps({'goals':[small(s) for s in a['summaries'] if 'goal_pass' in s]}))
print(json.dumps({'full':[small(s) for s in a['summaries'] if s['scope']=='full' and s['metric'] in ['wall_ms','prepare_ms','segment_write_ms','segment_sync_ms','catalog_sync_ms','wall_p95_ms']]}))
print(json.dumps({'calibrated_failed_guards':[small(s) for s in a['guards_failed'] if s['AA_pass']]}))
