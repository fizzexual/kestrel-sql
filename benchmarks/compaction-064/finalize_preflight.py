"""Preserve the encoding failure, repair only the independent auditor, freeze faults."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert not (W/'audit-encoding-failure').exists()
d=W/'audit-encoding-failure';d.mkdir()
for name in ['audit_qualification.py','qualification-audit-run.log']:shutil.copy2(W/name,d/name)
p=W/'audit_qualification.py';s=p.read_text(encoding='utf-8');assert s.count('.read_text()')==4
p.write_text(s.replace('.read_text()',".read_text(encoding='utf-8')"),encoding='utf-8')
save(d/'repair.json',{'utc':datetime.now(timezone.utc).isoformat(),'cause':'Independent source auditor used Windows cp1252 for UTF-8 source; no database failure or timing run',
    'repair':'Explicit UTF-8 in all four omitted source reads; rerun auditor only',
    'original_sha256':{n:sha(d/n) for n in ['audit_qualification.py','qualification-audit-run.log']},'repaired_auditor_sha256':sha(p)})
target=W/'fault-binaries';target.mkdir()
files={}
for name in ['publication_fault_probe.exe','live_retry_probe.exe','source_fault_probe.exe']:
    src=W/'lab/work/kestrel-064-fault-build/release/examples'/name
    dst=target/name;shutil.copy2(src,dst);assert sha(src)==sha(dst)
    files[name]={'sha256':sha(dst),'bytes':dst.stat().st_size,'origin':str(src)}
save(W/'fault-binary-freeze.json',{'utc':datetime.now(timezone.utc).isoformat(),'files':files,'test_only_fault_features':True})
shutil.copy2(W/'policy.json',W/'policy-pre-final-preflight.json')
p=W/'policy.json';v=json.loads(p.read_text(encoding='utf-8'))
v['native']['same_exact_released_probe_path_for_both_baselines']=False
v['native']['same_exact_freshly_linked_baseline_probe_path_for_both_baselines']=True
v['native']['baseline_label_clarification']='A and B share the newly linked identical driver on exact released source; they are not the released prebuilt probe file'
save(p,v)
print(json.dumps({'encoding_failure_preserved':True,'fault_binaries_frozen':files,'baseline_labels_clarified_before_timing':True}))
