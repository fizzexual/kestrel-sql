"""Preserve all untimed118 inputs/results and replay the unchanged pure auditor from a fresh restore."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,subprocess,zipfile
R=Path('D:/Codex/Kestrel/work');W=R/'perf-118';S=R/'restored-maintenance-tails-118'
OUT=Path('D:/Codex/Kestrel/outputs/kestrel-sql/benchmarks/maintenance-tails-118')
PY='C:/Users/Frizer/AppData/Local/Programs/Python/Python312/python.exe'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,indent=2)+'\n')
assert not S.exists() and not OUT.exists()
guard=load(sorted(R.glob('guard-final-117-*.json'))[-1]);assert guard['verified_idle_terminal_reset'] and not guard['active_processes']
assert (datetime.now(timezone.utc)-datetime.fromisoformat(guard['utc'])).total_seconds()<1800
original_audit=load(R/'audit-tails-118.log');assert original_audit['complete']
old=(W/'audit_tails_118.py').read_bytes();new=(R/'audit_tails_118.py').read_bytes()
a=b"p=W/'audit-proof.json';assert not p.exists();p.write_text(json.dumps(proof,indent=2)+'\\n',encoding='utf-8',newline='\\n');print(json.dumps(proof))"
b=b'print(json.dumps(proof))'
assert old.replace(a,b)==new
shutil.copy2(W/'audit_tails_118.py',W/'audit_tails_118_unexecuted_copy_draft.py')
shutil.copy2(R/'audit_tails_118.py',W/'audit_tails_118.py')
save(W/'pure-auditor-copy-correction.json',{'original_unexecuted_copied_draft_SHA256':hashlib.sha256(old).hexdigest(),
 'actual_Root_auditor_that_passed_SHA256':hashlib.sha256(new).hexdigest(),
 'sole_change':'Print pure audit result; do not write into the audited tree. Draft retained, actual original audit ran Root print-only version.',
 'original_audit_actual_API_exit':0,'no_data_gate_or_inference_change':True})
save(W/'original-audit-proof.json',original_audit)
for name in ['audit-tails-118.log','analyze-tails-118-v2.log']:
 p=W/name
 if p.exists():assert p.read_bytes()==(R/name).read_bytes()
 else:shutil.copy2(R/name,p)
shutil.copy2(Path(__file__),W/Path(__file__).name)
files={p.relative_to(W).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)} for p in W.rglob('*') if p.is_file()}
dirs=sorted(p.relative_to(W).as_posix() for p in W.rglob('*') if p.is_dir())
assert all(not p.is_symlink() and not p.is_junction() for p in [W,*W.rglob('*')])
groups=[];part=[];size=0
for name,v in sorted(files.items()):
 assert v['bytes']<=80*1024**2
 if part and size+v['bytes']>80*1024**2:groups.append(part);part=[];size=0
 part.append(name);size+=v['bytes']
if part:groups.append(part)
OUT.mkdir();save(OUT/'preservation-policy.json',{'utc':datetime.now(timezone.utc).isoformat(),'declared_before_archive':True,
 'exact_files':files,'exact_directories':dirs,'part_logical_ceiling':80*1024**2,
 'all_untimed118_inputs_results_drafts_and_helpers_retained':True,'reused117_full_engine_stores_remain_in_prior_verified_archive':True,
 'whole_restore_required':'Every current size/SHA/file/directory set and member CRC/order; exact print-only auditor in restored tree must return0 and match original output.'})
parts=[]
for i,group in enumerate(groups,1):
 p=OUT/f'evidence-{i:03d}.zip'
 with zipfile.ZipFile(p,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for name in group:z.write(W/name,name)
 with zipfile.ZipFile(p) as z:assert z.namelist()==group and z.testzip() is None
 h=sha(p);(OUT/(p.name+'.sha256')).write_text(h+'  '+p.name+'\n',encoding='utf-8',newline='\n')
 parts.append({'name':p.name,'bytes':p.stat().st_size,'sha256':h,'members':group})
S.mkdir()
for name in dirs:(S/name).mkdir(parents=True,exist_ok=True)
for part in parts:
 with zipfile.ZipFile(OUT/part['name']) as z:z.extractall(S)
def check():
 assert {p.relative_to(S).as_posix() for p in S.rglob('*') if p.is_file()}==set(files)
 assert {p.relative_to(S).as_posix() for p in S.rglob('*') if p.is_dir()}==set(dirs)
 for name,v in files.items():
  for root in [W,S]:assert (root/name).stat().st_size==v['bytes'] and sha(root/name)==v['sha256']
check()
p=subprocess.run([PY,str(S/'audit_tails_118.py'),str(S)],capture_output=True,timeout=180)
for suffix,data in [('stdout',p.stdout),('stderr',p.stderr)]:
 path=OUT/f'restored-audit.{suffix}.gz';path.write_bytes(gzip.compress(data,mtime=0));assert gzip.decompress(path.read_bytes())==data
assert p.returncode==0 and not p.stderr and json.loads(p.stdout)==original_audit
check()
assert all(sha(R/'perf-117'/n)==h for n,h in load(W/'policy.json')['all_inputs_SHA256'].items())
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'files':len(files),'directories':len(dirs),
 'logical_bytes':sum(v['bytes'] for v in files.values()),'parts':parts,'all_original_restored_full_file_SHA_size_set_directory_set_exact_before_and_after_audit':True,
 'actual_restored_pure_auditor_exit':p.returncode,'restored_audit_equals_original':True,
 'all479232_reused_ACKs_and216_reused_cases_independently_reconstructed':True,
 'zero_Native_timer_engine_build_test_or_source_changes':True,'new_performance_qualification':False,
 'private_remote_raw_download_verification_for118_not_yet_done':True}
save(OUT/'preservation-proof.json',proof)
for name in ['policy.json','analysis.json','original-audit-proof.json','input-preservation-proof.json','pure-auditor-copy-correction.json','audit_tails_118.py','analyze_tails_118.py','preserve_tails_118.py']:
 shutil.copy2(W/name,OUT/name)
(OUT/'REPRODUCE.md').write_text('Untimed post-hoc diagnostic only. Download every part and its SHA256 sidecar; verify SHA and member CRC/order against preservation-policy.json, extract to a new directory and create the declared empty directories. Run the preserved audit_tails_118.py with that absolute directory argument. The print-only auditor independently reconstructs all479232 annotations,216 cases and18 full/half summaries without an engine, timing or audited-tree writes. The original117 full tests/recovery and performance outcomes are reused, not rerun or requalified. Full117 raw archives remain preserved separately.\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in proof.items() if k!='parts'}),flush=True)
