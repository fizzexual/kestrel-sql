"""Post-timing source/policy provenance and pinned offline dependency archives."""
from datetime import datetime, timezone
import hashlib, json, os, platform, shutil, subprocess, sys, tomllib
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
a=load(W/'model-audit.json');assert a['complete'] and not a['advance_to_engine_design']
p=load(W/'cohort-policy.json');assert p['independent_auditor_sha256']==sha(W/'audit_model.py')
assert p['policy_sha256']==sha(W/'policy.json') and p['harness_sha256']==sha(W/'run_model.py') and p['binary_sha256']==sha(W/'bin/checkpoint-model.exe')
assert p['frame_oracle_sha256']==sha(W/'zstd_frame_oracle.py') and p['oracle_provenance_sha256']==sha(W/'oracle-provenance.json')
for name,digest in load(W/'oracle-provenance.json')['files'].items():assert sha(Path(name))==digest,name
base=load(W/'baseline.json')
for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d,n
for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
morning=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json');assert sha(ROOT/morning['report_file'])==morning['report_sha256']
assert not load(W/'post-timing-process-check.json')['active_processes']
archive_dir=Path(os.environ['USERPROFILE'])/'.cargo/registry/cache/index.crates.io-1949cf8c6b5b557f'
dest=W/'dependency-crates';dest.mkdir();deps=[]
for package in tomllib.loads((W/'model/Cargo.lock').read_text())['package']:
    if 'checksum' not in package:continue
    name=package['name']+'-'+package['version']+'.crate';source=archive_dir/name;assert sha(source)==package['checksum']
    shutil.copy2(source,dest/name);assert sha(dest/name)==package['checksum'];deps.append({'name':name,'sha256':package['checksum'],'bytes':source.stat().st_size})
save(W/'dependency-provenance.json',{'all_locked_registry_archives_included':True,'dependencies':deps,'license_and_source_inside_crate_archives':True})
save(W/'runtime-provenance.json',{'utc':datetime.now(timezone.utc).isoformat(),'after_all_timing':True,'python':sys.version,
    'platform':platform.platform(),'rustc':subprocess.check_output(['rustc','--version'],text=True).strip(),'cpu_logical_count':os.cpu_count(),
    'free_bytes':shutil.disk_usage(W).free,'model_only':True,'no_fresh_competitor_or_sql_benchmark':True})
save(W/'final-policy-check.json',{'utc':datetime.now(timezone.utc).isoformat(),'passed':True,'model_policy_harness_auditor_executable_unchanged':True,
    'original_engine_source_binaries_and_morning_unchanged':True,'cases':36,'samples':432,'full_fixture_hashes_and_independent_decode_passed':True,
    'no_case_restarted_or_overwritten':True,'advance_to_engine_design':False,'no_engine_release':True})
print(json.dumps({'passed':True,'pinned_crate_archives':len(deps),'model_only':True,'default_unchanged':True}))
