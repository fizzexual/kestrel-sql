"""Fresh fixed139 protocol for the tested138 input-allocation change."""
from pathlib import Path
import ast, hashlib, json, re
R=Path('D:/Codex/Kestrel/work'); assert not (R/'perf-139').exists()
parents={}
def read(name):
    p=R/name; parents[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    return p.read_text(encoding='utf-8-sig')
def rename(text):
    return text.replace('137','139').replace('136','138').replace('buffer138','reuse138')
def save(name,text):
    p=R/name; assert not p.exists(),name
    if name.endswith('.py'):ast.parse(text,filename=name)
    p.write_text(text,encoding='utf-8',newline='\n')
prep=rename(read('prepare_phase_compare_137.py'))
prep=prep.replace('bounded-buffer138 binary','input-reuse138 binary')
prep=prep.replace('derive_buffer_compare_139.py','derive_input_compare_139.py')
prep,count=re.subn(r"^policy\['kind'\]=.*$", "policy['kind']='Compaction input reuse: exact131 A/B versus exact138 C'",prep,flags=re.M); assert count==1
hypothesis='133 measured preparation gains;135/137 writer changes were rejected.138 reuses one decoded input Vec and one byte scratch across compaction instead of fresh per-block/per-run storage, using unchanged full CRC reads/decoding and exact131 phase/merge/original writer. It may reduce charged preparation and whole compaction; benefit unknown. All input/read/CRC/phase/index/write/flush/sync costs remain charged. This isolates138 versus131, not supported016 whole-engine qualification.'
prep,count=re.subn(r"^policy\['hypothesis'\]=.*$", "policy['hypothesis']="+repr(hypothesis),prep,flags=re.M); assert count==1
prep,count=re.subn(r"^policy\['goals'\]=.*$", "policy['goals']={'clustered_wall_ms_max_ratio':.95,'clustered_prepare_ms_max_ratio':.90}",prep,flags=re.M); assert count==1
save('prepare_phase_compare_139.py',prep)
for old,new in [('run_phase_compare_137.py','run_phase_compare_139.py'),('audit_phase_compare_137.py','audit_phase_compare_139.py'),
                ('smoke_phase_compare_137.py','smoke_phase_compare_139.py'),('activity_worker_137.ps1','activity_worker_139.ps1'),
                ('launch_phase_compare_137.ps1','launch_phase_compare_139.ps1'),('audit_lifecycle_receipts_137.py','audit_lifecycle_receipts_139.py'),
                ('launch_preflight_phase137.ps1','launch_preflight_phase139.ps1'),('launch_audits_phase137.ps1','launch_audits_phase139.ps1')]:
    text=rename(read(old)).replace('derive_buffer_compare_139.py','derive_input_compare_139.py')
    if new=='audit_phase_compare_139.py':
        assert text.count("metric in ['wall_ms','write_sync_ms']")==1
        text=text.replace("metric in ['wall_ms','write_sync_ms']","metric in ['wall_ms','prepare_ms']")
    save(new,text)
(R/'input139-controller-derivation.json').write_text(json.dumps({'parent_sha256':parents,'trial':139,'before_any_timing':True,
    'same_216_balanced_schedule_safety_protocol_144AA_144guards':True,'predeclared_goals_whole5pct_prepare10pct':True,
    'all_stage_write_sync_and_tail_guards_preserved':True,'all_release_gates_unchanged':True},indent=2)+'\n',encoding='utf-8',newline='\n')
print('139 fixed controllers derived; no build or timing started')
