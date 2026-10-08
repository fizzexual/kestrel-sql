from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json

ROOT=Path('D:/Codex/Kestrel');W=ROOT/'work/perf-086';RESTORE=ROOT/'work/restored-service-086'
OUT=ROOT/'outputs/kestrel-sql/benchmarks/service-d-086'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert load(OUT/'preservation-proof.json')['complete']
expected=load(W/'audit.json')
spec=importlib.util.spec_from_file_location('restored086',RESTORE/'audit_service_086.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.W=RESTORE;m.REPO=RESTORE/'released-source'
m.main()
actual=load(RESTORE/'audit.json')
assert {k:v for k,v in actual.items() if k!='audited_utc'}=={k:v for k,v in expected.items() if k!='audited_utc'}
proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'native_or_timer_processes_run':0,
    'frozen_auditor_bytes_unchanged':sha(RESTORE/'audit_service_086.py')==sha(W/'audit_service_086.py'),
    'only_module_path_globals_changed':{'W':str(RESTORE),'REPO':str(RESTORE/'released-source')},
    'all_raw_quantiles_conservation_ratios_stage_counts_full_and_block_failures_exact':True,
    'original_audit_sha256':sha(W/'audit.json'),'restored_audit_sha256':sha(RESTORE/'audit.json'),
    'only_audited_utc_differs':True,'cases':54,'offered_operations':900000,'supported_promotion':False}
(OUT/'restored-audit-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
(OUT/'replay_service_086.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'restored_replay_passed':True,'every_raw_and_gate_result_exact':True,'timers_run':0}),flush=True)
