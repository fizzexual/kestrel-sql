"""Add archival completion and standalone released source without replacing raw copies."""
from datetime import datetime, timezone
import hashlib, json, shutil
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';D=ROOT/'benchmarks/buffer-067'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
p=ROOT/'benchmarks/buffer-067-preservation.json';record=load(p);payload=record['payload_sha256']
for n,d in payload.items():assert sha(D/n)==d,n
added={}
def copy(source,name):
    target=D/name;assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target);assert sha(source)==sha(target);added[name]=sha(target)
copy(W/'preservation-run.log','preservation-completed.stdout.log')
copy(Path(__file__),'after_preservation.py')
released=W/'released-core-source';released.mkdir()
for n,d in load(W/'baseline.json')['core_source_sha256'].items():
    assert sha(ROOT/n)==d,n
    target=released/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,target)
    copy(target,'released-core-source/'+n)
frozen={}
for directory in [W/'native-binaries',W/'fault-binaries',W/'lab/work/perf-067/candidate']:
    for source in directory.glob('*.exe'):
        n=source.relative_to(W).as_posix();assert sha(D/n)==sha(source);frozen[n]=sha(source)
assert len(frozen)==15,len(frozen)
initial=load(W/'maintenance-derivation.json')['derived_sha256']
assert sha(W/'maintain_evidence.py')==sha(D/'maintain_evidence.py')
note={'utc':datetime.now(timezone.utc).isoformat(),'initial_archival_payload_files':len(payload),'standalone_released_source_paths':26,
    'source_and_binaries_sha256_verified':True,'frozen_default_fault_and_native_executables':frozen,
    'completed_preservation_stdout_added_separately':True,'initial_empty_inflight_wrapper_copy_retained':True,
    'maintenance_before_audit_sha256':initial,'maintenance_final_sha256':sha(W/'maintain_evidence.py'),
    'maintenance_note':'After native audit, latest-navigation prose added the measured encode reductions; packaging/publication algorithm and native policies were unchanged. Before-audit derivation and final script are both retained.',
    'native_policy_and_auditor_unchanged':all(load(W/'final-policy-check.json')[k] for k in ['native_auditor_matches_before_first_timer','native_policy_matches_before_first_timer']),
    'native_full_store_format_audit_sha256':sha(W/'native-format-audit.json')}
save(W/'archival-completion.json',note);copy(W/'archival-completion.json','archival-completion.json')
assert not set(added)&set(payload)
payload.update(added);record.update(payload_sha256=payload,completion_added_payload_files=len(added),standalone_released_core_source_included=True)
save(p,record)
print(json.dumps({'completed_payload_files':len(payload),'added_without_replacement':len(added),'released_core_source_paths':26,'frozen_executables':len(frozen)}))
