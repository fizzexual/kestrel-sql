"""Derive a fresh complete141 comparison for the tested140 read path."""
from pathlib import Path
import ast,hashlib,json,re
R=Path('D:/Codex/Kestrel/work');P=R.parent/'outputs/kestrel-sql'
assert not (R/'perf-141').exists()
parents={}
def read(name):
    p=R/name; assert p.read_bytes()==(P/'experiments/compaction_input_compare_139'/name).read_bytes()
    parents[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    return p.read_text(encoding='utf-8-sig')
def rename(text):
    return text.replace('139','141').replace('138','140').replace('reuse140','coalesce140').replace('derive_input_compare_141.py','derive_read_compare_141.py')
def save(name,text):
    p=R/name;assert not p.exists(),name
    if name.endswith('.py'):ast.parse(text,filename=name)
    p.write_text(text,encoding='utf-8',newline='\n')
prep=rename(read('prepare_phase_compare_139.py'))
prep=prep.replace('bounded-coalesce140 binary','bounded-read140 binary')
prep,count=re.subn(r"^policy\['kind'\]=.*$","policy['kind']='Bounded compaction read: exact131 A/B versus exact140 C'",prep,flags=re.M);assert count==1
hypothesis='139 allocation reuse failed full/both-half qualification.140 reads each immutable <=1MiB run payload with one existing positional exact-read request, validates every block CRC before decoding directly into final columns; larger runs retain exact131 block path. This targets repeated read requests and decoded temporary copies. Exact131 phase/merge and original64KiB writer remain. All read/CRC/phase/input/index/write/flush/sync costs are charged; speed unknown. This isolates140 versus131, not supported016 whole-engine qualification.'
prep,count=re.subn(r"^policy\['hypothesis'\]=.*$","policy['hypothesis']="+repr(hypothesis),prep,flags=re.M);assert count==1
assert prep.count("'candidate140_tests':344")==1
prep=prep.replace("'candidate140_tests':344","'candidate140_tests':352")
save('prepare_phase_compare_141.py',prep)
for old,new in [('run_phase_compare_139.py','run_phase_compare_141.py'),('audit_phase_compare_139.py','audit_phase_compare_141.py'),
 ('smoke_phase_compare_139.py','smoke_phase_compare_141.py'),('activity_worker_139.ps1','activity_worker_141.ps1'),
 ('launch_phase_compare_139.ps1','launch_phase_compare_141.ps1'),('audit_lifecycle_receipts_139.py','audit_lifecycle_receipts_141.py'),
 ('launch_preflight_phase139.ps1','launch_preflight_phase141.ps1'),('launch_audits_phase139.ps1','launch_audits_phase141.ps1')]:
    save(new,rename(read(old)))
(R/'read141-controller-derivation.json').write_text(json.dumps({'parent_sha256':parents,'trial':141,'before_any_timing':True,
 'same216_schedule_safety_144AA_144guards':True,'predeclared_whole5pct_prepare10pct_goals':True,'all_stage_write_sync_and_tail_guards_preserved':True,
 'all_release_gates_unchanged':True,'passed140_prerequisites_reused_no_build':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print('141 actual controllers derived; no new build or timing started')
