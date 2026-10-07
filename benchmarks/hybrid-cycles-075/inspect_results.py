"""Compact post-cohort inspection; no modified observations."""
import json
from pathlib import Path
W = Path(__file__).resolve().parent
def load(name): return json.loads((W/name).read_text(encoding='utf-8-sig'))
a = load('model-audit.json')
r = load('model-results.json')
print(json.dumps({'rounds':[{'actual_receipts':s['actual_receipts'],'total_ratios':[p['hybrid_a']['total_ms'] for p in s['pairs']],'faster_rounds':sum(p['hybrid_a']['total_ms']<1 for p in s['pairs'])} for s in a['summaries']]},indent=2))
