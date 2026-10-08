"""Additive reader CPU diagnostic; preserve original 078/081 and all failures."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
ROOT=Path('D:/Codex/Kestrel');W=ROOT/'work/perf-083'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
assert not W.exists(),'Use a new experiment; never overwrite'
assert shutil.disk_usage(ROOT).free>5_000_000_000
W.mkdir();(W/'inputs').mkdir();(W/'bin').mkdir()
shutil.copy2(ROOT/'work/reader_profile_083.rs',W/'reader_profile_083.rs')
sources={}
for label,trial in [('control',78),('bulk',81)]:
    src=ROOT/f'work/perf-{trial:03}/model';dst=W/f'{label}-model';shutil.copytree(src,dst)
    sources[label]={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file()}
    p=dst/'src/main.rs';text=p.read_text(encoding='utf-8');needle='fn main() -> Result<()> {'
    assert text.count(needle)==1
    text=text.replace(needle,'include!("reader_profile_083.rs");\n\n'+needle+'\n    if std::env::args().nth(1).is_some_and(|s| s == "profile083") { return reader_profile083(); }')
    p.write_text(text,encoding='utf-8',newline='\n')
    shutil.copy2(W/'reader_profile_083.rs',dst/'src/reader_profile_083.rs')
for name in ['baseline.json','catalog_oracle.py','page_oracle.py','process_memory.py','order_plan.py']:
    shutil.copy2(ROOT/'work/perf-082'/name,W/name)
for n in [0,50000,99000]:shutil.copy2(ROOT/f'work/perf-082/inputs/{n}.ks2',W/f'inputs/{n}.ks2')
shutil.copy2(ROOT/'work/perf-081/prerequisite-environment.json',W/'environment.json')
save(W/'source-derivation.json',{'complete':True,'original_source_sha256':sources,'only_changes':'diagnostic include/CLI branch and reader_profile_083.rs; original readers/validators and limits unchanged','no_supported_engine_edit':True})
save(W/'policy.json',{'trial':83,'declared_utc':datetime.now(timezone.utc).isoformat(),'before_first_cohort_timer':True,'diagnostic_not_adoption_or_competitor_benchmark':True,
 'hypothesis':'Locate charged receipt reader cost; determine whether parsing dominates immutable-anchor validation and whether bulk081 helps that CPU phase.',
 'rounds':12,'balanced_blocks':2,'cases':108,'sizes':[0,50000,99000],'variants':{'baseline_a':'control','baseline_b':'control','bulk':'bulk'},
 'phase_order':['empty','read_crc','parse','record_validate','source_positions','complete_anchor'],
 'iterations_large':{'empty':256,'read_crc':128,'parse':16,'record_validate':128,'source_positions':1024,'complete_anchor':16},
 'iterations_small':{'empty':256,'read_crc':128,'parse':4096,'record_validate':16384,'source_positions':1024,'complete_anchor':4096},
 'wall_identity_bounds':[.9,1.1],'cpu_identity_bounds':[.9,1.1],'minimum_cpu_window_ms':250,'cpu_window_includes_native_pipe_handshake':True,
 'cpu_source':'Windows GetProcessTimes kernel+user, exact retained Popen child handle; snapshot before go and after end',
 'cpu_source_documentation':'https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes',
 'semantic_gate':'full legacy ledger checksum/generation/source positions equal independent Python decoder for every case; no original input mutation',
 'direction_gate':'Only infer dominant parse cost with matching large parse/complete A/A wall and eligible CPU controls in full cohort and each balanced half; otherwise mark inconclusive.',
 'minimum_free_bytes':3_000_000_000,'timeout_per_phase_seconds':180,'all_cases_and_stalls_retained':True,'no_bad_case_reruns':True,'no_heavy_work_concurrent_with_timers':True,
 'limitations':['warm repeated immutable CAT4 anchor body, not complete Hybrid::open or SQL service','stages are isolated repetitions and need not add up to full open','process peaks include retained setup map and repeated readers','100ns API units do not imply 100ns measurement resolution; short CPU windows remain unqualified','no physical disk/power-loss attribution']})
print(json.dumps({'prepared':True,'work':str(W),'supported_engine_unchanged':True}))
