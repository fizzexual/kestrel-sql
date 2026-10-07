"""Audit complete extracted evidence without rewriting its frozen absolute records."""
import hashlib,json,sys,tempfile
from pathlib import Path
W=Path(__file__).resolve().parent
assert sys.argv[1:]==['--audit-restored'], 'Use --audit-restored after verifying/extracting every part'
cohort=json.loads((W/'cohort-policy.json').read_text(encoding='utf-8'))
for name,digest in cohort['frozen_file_sha256'].items():
    with (W/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest,name
for name,digest in cohort['binary_sha256'].items():
    with (W/name).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest,name
old_root=Path(json.loads((W/'model-results.json').read_text(encoding='utf-8'))['cases'][0]['label'])
status=json.loads((W/'raw'/(str(old_root)+'.status.json')).read_text(encoding='utf-8'))
# Stored paths are Windows strings even when the auditor runs on another platform.
original=status['fixture'].replace('\\','/').rsplit('/fixtures/',1)[0]
def relocated_path(value):
    raw=str(value).replace('\\','/')
    if raw==original:return W
    if raw.startswith(original+'/'):return W/raw[len(original)+1:]
    return Path(value)
output=Path(tempfile.mkdtemp(prefix='audit-restored-',dir=W))
def redirected_save(path,value):
    assert Path(path).name in ['fixture-inventory.json','model-audit.json']
    (output/Path(path).name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
source=(W/'audit_model.py').read_text(encoding='utf-8')
import_line='from pathlib import Path';save_body="    p.write_text(json.dumps(v,indent=2)+'\\n',encoding='utf-8')"
assert source.count(import_line)==1 and source.count(save_body)==1
derived=source.replace(import_line,'Path=relocated_path').replace(save_body,'    redirected_save(p,v)')
(output/'relocated-audit.py').write_text(derived,encoding='utf-8')
(output/'derivation.json').write_text(json.dumps({'original_auditor_sha256':hashlib.sha256(source.encode()).hexdigest(),'derived_auditor_sha256':hashlib.sha256(derived.encode()).hexdigest(),'only_changes':['Path constructor binding for original absolute paths','two output saves redirected to fresh directory'],'canonical_logic_policy_raw_and_frozen_files_unchanged':True,'no_native_workload_or_timing_run':True},indent=2)+'\n',encoding='utf-8')
sys.path.insert(0,str(W))
exec(compile(derived,str(output/'relocated-audit.py'),'exec'),{'__file__':str(W/'audit_model.py'),'__name__':'restored_evidence_audit','relocated_path':relocated_path,'redirected_save':redirected_save})
original_audit=json.loads((W/'model-audit.json').read_text(encoding='utf-8'))
replayed=json.loads((output/'model-audit.json').read_text(encoding='utf-8'))
for key in ['checks','summaries','failed_checks','file_instances','stored_bytes_total']:
    assert replayed[key]==original_audit[key],key
print(json.dumps({'restored_audit_passed':True,'fresh_output':str(output),'no_original_evidence_rewritten':True,'no_new_benchmark':True}))
