from pathlib import Path
import json
R=Path('D:/Codex/Kestrel/work');P=R.parent/'outputs/kestrel-sql'
proof=json.loads((R/'phase149-actual-exits.json').read_text(encoding='utf-8-sig'))
assert proof['cohort_actual_exit']==0 and proof['actual_controller_wait_completed']
source=(P/'experiments/compaction_compare_145/wait_prefix145_audit_quiet.ps1').read_text(encoding='utf-8')
source=source.replace('phase145-prefix-audit','phase149-complete-audit')
dest=R/'wait_compare149_audit_quiet.ps1';assert not dest.exists();dest.write_text(source,encoding='utf-8',newline='\n')
print('Full149 audit quiet waiter prepared; no fixture audit started')
