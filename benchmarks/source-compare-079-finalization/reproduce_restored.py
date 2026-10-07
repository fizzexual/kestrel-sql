"""Audit extracted079 evidence; additive correction of the archived relocation helper."""
import ast,hashlib,json,sys,tempfile
from pathlib import Path
assert len(sys.argv)==3 and sys.argv[1]=='--directory'
W=Path(sys.argv[2]).resolve();assert W.is_dir()
cohort=json.loads((W/'cohort-policy.json').read_text(encoding='utf-8'))
for name,digest in cohort['frozen_file_sha256'].items():
    with (W/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest,name
for name,digest in cohort['binary_sha256'].items():
    with (W/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest,name
first=json.loads((W/'model-results.json').read_text(encoding='utf-8'))['cases'][0]['label']
status=json.loads((W/'raw'/(first+'.status.json')).read_text(encoding='utf-8'))
original=status['fixture'].replace('\\','/').rsplit('/fixtures/',1)[0]
def relocated_path(value):
    raw=str(value).replace('\\','/')
    if raw==original:return W
    if raw.startswith(original+'/'):return W/raw[len(original)+1:]
    return Path(value)
output=Path(tempfile.mkdtemp(prefix='audit-restored-corrected-',dir=W))
def redirected_save(path,value):
    assert Path(path).name in ['fixture-inventory.json','model-audit.json']
    (output/Path(path).name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
source=(W/'audit_model.py').read_text(encoding='utf-8')
import_line='from pathlib import Path'
save_lines=[line for line in source.splitlines() if line.startswith('def save(p,v):')]
assert source.count(import_line)==1 and len(save_lines)==1
save_line=save_lines[0];assert source.count(save_line)==1
parsed=ast.parse(save_line);node=parsed.body[0]
assert isinstance(node,ast.FunctionDef) and len(node.body)==1 and isinstance(node.body[0],ast.Expr)
assert isinstance(node.body[0].value,ast.Call) and isinstance(node.body[0].value.func,ast.Attribute) and node.body[0].value.func.attr=='write_text'
derived=source.replace(import_line,'Path=relocated_path').replace(save_line,'def save(p,v):redirected_save(p,v)')
ast.parse(derived);(output/'relocated-audit.py').write_text(derived,encoding='utf-8')
(output/'derivation.json').write_text(json.dumps({'original_auditor_sha256':hashlib.sha256(source.encode()).hexdigest(),'derived_auditor_sha256':hashlib.sha256(derived.encode()).hexdigest(),'original_absolute_path_prefix':original,'relocated_directory':str(W),'only_changes':['Path constructor binding for original absolute paths','single-line save function bound to fresh output directory'],'canonical_logic_policy_raw_and_frozen_files_unchanged':True,'no_native_workload_or_timing_run':True},indent=2)+'\n',encoding='utf-8')
sys.path.insert(0,str(W))
exec(compile(derived,str(output/'relocated-audit.py'),'exec'),{'__file__':str(W/'audit_model.py'),'__name__':'restored_evidence_audit','relocated_path':relocated_path,'redirected_save':redirected_save})
original_audit=json.loads((W/'model-audit.json').read_text(encoding='utf-8'))
replayed=json.loads((output/'model-audit.json').read_text(encoding='utf-8'))
for key in ['checks','summaries','failed_checks','file_instances','stored_bytes_total']:assert replayed[key]==original_audit[key],key
print(json.dumps({'restored_audit_passed':True,'fresh_output':str(output),'no_original_evidence_rewritten':True,'no_new_benchmark':True}))
