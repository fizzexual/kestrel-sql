"""Post-run descriptive stage analysis of every133 case, with no retiming."""
from pathlib import Path
from datetime import datetime,timezone
import json
W=Path('D:/Codex/Kestrel/work/perf-133')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(W/'audit.json')['complete']
cases=[json.loads(line) for line in (W/'component-cases.jsonl').read_text().splitlines()]
rows=[]
for case in cases:
    result=load(W/case['stdout']);before=result['before']['publication_profile'];after=result['after']['publication_profile']
    stages={n:after[n]['total_ms']-before[n]['total_ms'] for n in ['prepare','segment_write','segment_sync','catalog_encode','catalog_write','catalog_sync','catalog_rename']}
    rows.append({k:case[k] for k in ['index','name','variant','round']}|{'wall_ms':result['compaction_ns']/1e6,'stage_ms':stages,'unattributed_ms':result['compaction_ns']/1e6-sum(stages.values())})
assert len(rows)==216
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'all216_analyzed_without_retiming':True,'all_rows':rows,'top10_descriptive_only':sorted(rows,key=lambda row:row['wall_ms'],reverse=True)[:10],'no_physical_disk_cause_claim':True}
assert not (W/'sync-tail-analysis.json').exists()
(W/'sync-tail-analysis.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'complete':True,'all216_analyzed':True,'worst_case':proof['top10_descriptive_only'][0]}))
