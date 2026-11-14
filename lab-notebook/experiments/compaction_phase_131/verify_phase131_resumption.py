"""After observed quiet, verify fully read instructions and no-hash appendix chain."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(b):return hashlib.sha256(b).hexdigest()
quiet=load(R/'phase131-completion-quiet-proof.json');assert quiet['complete'] and quiet['continuous_observed_clear_seconds']>=120
instructions=[]
for path,expected in [
 ('D:/Codex/KESTREL_HANDOFF.md','3bf7d389cb500257f1ce8c94254bb347d55aea51367641b3268458330cd73ab6'),
 ('D:/Codex/KESTREL_FRESH_START.md','211174715284d87c353ee4cd62f6b5cf2e7235baaf2739ed73142694ad0b2998')]:
    raw=Path(path).read_bytes();text=raw.decode('utf-8-sig');assert digest(raw)==expected,(path,'Instructions changed; read full new content before proceeding')
    instructions.append({'path':path,'bytes':len(raw),'sha256':expected,'full_UTF8_read_matches_previously_fully_read_instructions':True})
old=N.read_bytes();old.decode('utf-8-sig')
appendix=load(R/'phase131-external-hold-next-proof.json');prefix=old[:appendix['previous_prefix_bytes']]
assert len(old)==appendix['new_total_bytes']
assert old==prefix+appendix['appended_text'].encode('utf-8')
assert digest(prefix)==load(R/'phase130-running-next-proof.json')['new_sha256']
assert load(R/'phase131-v2-actual-exits.json')['build_actual_exit']==0 and load(R/'perf-131/build-proof.json')['fresh_Archive_tests']==340
assert not (R/'perf-131/independent-wire-audit.json').exists()
assert not (R/'phase131-publication-proof.json').exists()
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'instructions':instructions,'verified_no_hash_appendix_exact':True,'old_historical_prefix_sha256':digest(prefix),'current_next_sha256':digest(old),'current_next_bytes':len(old),'quiet_proof_complete':True,'audit_publication_cleanup_unstarted':True}
assert not (R/'phase131-resumption-proof.json').exists()
(R/'phase131-resumption-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in proof.items() if k!='instructions'}))
