"""Fresh complete146 cohort after rejected145 closure; no selected retiming."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json
R=Path('D:/Codex/Kestrel/work');P=Path('D:/Codex/Kestrel/outputs/kestrel-sql')
prior=P/'experiments/compaction_compare_145'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert load(R/'phase145-storage-cleanup-proof.json')['completed145_prefix_stores_closed']
assert load(R/'phase145-finish-wait-actual-exits.json')['actual_exit']==0
assert not (R/'perf-145').exists() and not (R/'perf-146').exists()
parents={}
names=['prepare_phase_compare_145.py','run_phase_compare_145.py','audit_phase_compare_145.py',
    'smoke_phase_compare_145.py','activity_worker_145.ps1','launch_phase_compare_145.ps1',
    'audit_lifecycle_receipts_145.py','launch_preflight_phase145.ps1','launch_audits_phase145.ps1']
for name in names:
    source=prior/name;parents[name]=sha(source)
    old=source.read_text(encoding='utf-8');new=old.replace('145','146')
    if name=='prepare_phase_compare_145.py':
        new=new.replace("assert head == load(R/'extrema144-remote-save-proof.json')['head']", "assert head == load(R/'phase145-publication-proof.json')['private_main']")
        assert "phase145-publication-proof.json" in new
        new=new.replace('derive_extrema_compare_146.py','derive_extrema_compare_146.py')
        new=new.replace("'hypothesis':'Deriving ordered concatenation", "'hypothesis':'Deriving ordered concatenation")
    if name=='audit_phase_compare_145.py':
        assert old[old.index('def rows('):old.index('def nearest(')]==new[new.index('def rows('):new.index('def nearest(')]
    dest=R/name.replace('145','146');assert not dest.exists(),dest
    if dest.suffix=='.py':ast.parse(new,filename=dest.name)
    dest.write_text(new,encoding='utf-8',newline='\n')
(R/'extrema146-controller-derivation.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),
    'parent_source_sha256':parents,'before_any146_timing':True,'full_new216_cases_not_selected145_retiming':True,
    'exact_same_engine_binaries_schedule_inputs_numerical_gates':True,'candidate144_prerequisites_reused':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print('146 actual controller sources derived; no native case or Rust build started')
