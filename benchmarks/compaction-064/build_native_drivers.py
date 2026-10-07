"""Build identical native driver logic against exact016 and qualified64 libraries."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
LAB=W/'lab/outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert load(W/'qualification.json')['complete'] and load(W/'wide-faults.json')['complete']
assert not (W/'native-driver-build.json').exists()
base=load(W/'baseline.json')
source=ROOT/'examples/publication_probe.rs'
text=source.read_text(encoding='utf-8')
assert text==(LAB/'examples/publication_probe.rs').read_text(encoding='utf-8')
old='if (batch + 1).is_multiple_of(32) {'
assert text.count(old)==1
driver=W/'native_publication_probe.rs'
driver.write_text(text.replace(old,'if archive.small_segments() >= 64 {').replace('Sequential durable publications at fixed receipt-ledger sizes. Setup, checks,','Sequential durable publications with the live64-run maintenance trigger. Setup, checks,'),encoding='utf-8')
baseline=W/'baseline-native-source';baseline.mkdir()
for n,d in base['core_source_sha256'].items():
    assert sha(ROOT/n)==d,n
    p=baseline/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p)
target=W/'baseline-native-build'
environment={**os.environ,'CARGO_TARGET_DIR':str(target),'TMP':str(W/'lab/work/rust-temp-032'),'TEMP':str(W/'lab/work/rust-temp-032')}
record={'started_utc':datetime.now(timezone.utc).isoformat(),'driver_original_sha256':sha(source),'driver_adapted_sha256':sha(driver),
    'driver_logic_identical_for_all_labels':True,'baseline_core_source_sha256':base['core_source_sha256'],
    'candidate_library_from_qualified_default_build':True,'policy_correction_before_first_native_timing':True,'commands':[]}
command=['cargo','build','--release','--lib','--offline','--locked']
r=subprocess.run(command,cwd=baseline,env=environment,text=True,capture_output=True)
(W/'baseline-native-build.log').write_text(r.stdout+r.stderr,encoding='utf-8')
record['commands'].append({'argv':command,'cwd':str(baseline),'exit':r.returncode})
save(W/'native-driver-build-in-progress.json',record)
assert r.returncode==0,r.stderr
(W/'native-binaries').mkdir()
for label,version,deps in [('baseline','0.3.16',target/'release/deps'),('candidate','0.3.17-dev.64',W/'lab/work/kestrel-064-build/release/deps')]:
    libraries={}
    for name in ['kestrel_sql','serde_json']:
        found=list(deps.glob('lib'+name+'-*.rlib'));assert len(found)==1,found
        libraries[name]=found[0]
    destination=W/'native-binaries'/(label+'-publication.exe')
    command=['rustc','--edition=2024','-O','-C','lto=thin','-C','codegen-units=1','-D','warnings',str(driver),'-L','dependency='+str(deps),'-o',str(destination)]
    for name,p in libraries.items():command+=['--extern',name+'='+str(p)]
    r=subprocess.run(command,cwd=W,env={**environment,'CARGO_PKG_VERSION':version},text=True,capture_output=True)
    (W/(label+'-native-link.log')).write_text(r.stdout+r.stderr,encoding='utf-8')
    record['commands'].append({'argv':command,'exit':r.returncode,'version':version,
        'libraries':{n:{'path':str(p),'sha256':sha(p)} for n,p in libraries.items()}})
    save(W/'native-driver-build-in-progress.json',record)
    assert r.returncode==0,r.stderr
    data=destination.read_bytes()
    assert b'KESTREL_FAULT_POINT' not in data and b'KESTREL_LIVE_PAUSE' not in data
    record[label+'_sha256']=sha(destination)
shutil.copy2(W/'policy.json',W/'policy-pre-native-design.json')
policy=load(W/'policy.json')
policy['native']['maintenance_every_appends']=None
policy['native']['maintenance_trigger_small_runs']=64
policy['native']['baseline_probe']='new frozen probe linked to freshly built exact released016 source; A and B share one exact path'
policy['native']['same_driver_source_for_baseline_and_candidate']=str(driver)
policy['native']['memory_guard_peak_working_set_ratio_max']=1.10
policy['native']['memory_method']='Windows K32GetProcessMemoryInfo after task-owned native process exit, retained handle; full-process peak includes setup/verification; unavailable data fails memory guard'
policy['native']['design_correction']='Original every32 maintenance driver would hide live trigger changes; corrected before first performance case, original draft retained'
policy['native']['design_corrected_utc']=datetime.now(timezone.utc).isoformat()
save(W/'policy.json',policy)
record['completed_utc']=datetime.now(timezone.utc).isoformat();record['complete']=True
save(W/'native-driver-build.json',record)
print(json.dumps({'complete':True,'driver_identical':True,'baseline_sha256':record['baseline_sha256'],'candidate_sha256':record['candidate_sha256']}))
