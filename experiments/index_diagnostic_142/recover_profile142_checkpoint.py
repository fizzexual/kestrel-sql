"""Verify the already appended checkpoint; never append/rewrite it again."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
R=Path('D:/Codex/Kestrel/work');N=Path('D:/Codex/KESTREL_NEXT.md')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
expected=load(R/'phase141-closed-next-proof.json')['new_sha256']
raw=N.read_bytes();marker=b'###142 actual index diagnostic implemented; example prerequisites running'
assert raw.count(marker)==1
at=raw.index(marker)
matches=[at-off for off in range(8) if hashlib.sha256(raw[:at-off]).hexdigest()==expected]
assert len(matches)==1,matches
length=matches[0];note=raw[length:].decode('utf-8')
assert note.startswith('\n') and note.endswith('\n') and 'timing started' in note
stamp=re.search(r'— ([^\n]+)',note).group(1)
target=R/'profile142-started-next-proof.json';assert not target.exists()
proof={'utc':stamp,'verified_utc':datetime.now(timezone.utc).isoformat(),'old_sha256':expected,
 'new_sha256':hashlib.sha256(raw).hexdigest(),'old_history_prefix_exact':True,'old_length':length,'new_length':len(raw),
 'diagnostic142_implemented':True,'timed_cases_started':0,'release017_qualified':False,
 'first_append_actual_exit':1,'failure_after_append':'PowerShell cannot convert ByRef-like ReadOnlySpan for SequenceEqual; append itself completed',
 'exact_existing_append_recovered_without_rewrite':True,'failed_append_source_sha256':hashlib.sha256((R/'append_profile142_started.ps1').read_bytes()).hexdigest()}
target.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
assert N.read_bytes()==raw
print('Already appended142 checkpoint/preserved141 prefix verified; no rewritten or repeated appendix')
