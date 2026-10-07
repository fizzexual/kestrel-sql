"""Post-timing exact file audit across all54 stores; no new performance decision."""
from datetime import datetime, timezone
import hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
a=json.loads((W/'native-audit.json').read_text(encoding='utf-8'));assert a['complete']
assert not json.loads((W/'post-timing-process-check.json').read_text(encoding='utf-8-sig'))['active_processes']
references={};rows=[]
for c in a['cases']:
    directory=W/'native-fixtures'/c['label']
    assert not list(directory.glob('*.pending'))
    files={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(directory.glob('*.ks2'))}
    size=c['spec']['seed_receipts']
    if size not in references:references[size]={'label':c['label'],'files':files}
    assert files==references[size]['files'],c['label']
    rows.append({'label':c['label'],'size':size,'compared_with':references[size]['label'],'files':len(files),
        'bytes':sum(f['bytes'] for f in files.values()),'all_bytes_hashes_and_names_identical':True})
assert len(rows)==54
result={'passed':True,'utc':datetime.now(timezone.utc).isoformat(),'posthoc_correctness_only':True,'no_new_timing_or_threshold_change':True,
    'full_native_stores_checked':54,'file_instances_checked':sum(x['files'] for x in rows),'bytes_hashed':sum(x['bytes'] for x in rows),
    'each_history_identical_across_all_versions_labels_and_rounds':True,'references':references,'cases':rows}
(W/'native-format-audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['references','cases']}))
