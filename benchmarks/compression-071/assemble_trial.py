"""Independent fast-level model with corrected, prechecked balanced ordering."""
from datetime import datetime, timezone
import ast, hashlib, json, shutil
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-070'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert not (W/'model').exists();shutil.copytree(OLD/'model',W/'model')
s=(W/'model/src/main.rs').read_text().replace('070','071').replace('level1','level-5')
s=s.replace('const MAX_BYTES:', 'const COMPRESSION_LEVEL: i32 = -5;\nconst MAX_BYTES:')
s=s.replace('zstd_safe::compress(&mut payload, input, 1)','zstd_safe::compress(&mut payload, input, COMPRESSION_LEVEL)')
s=s.replace('"mode":args[3],', '"mode":args[3],"compression_level":COMPRESSION_LEVEL,')
(W/'model/src/main.rs').write_text(s,encoding='utf-8')
for name in ['build.py','check_processes.ps1','process_memory.py','zstd_frame_oracle.py','collect_final.py']:
    s=(OLD/name).read_text().replace('070','071')
    if name=='collect_final.py':s=s.replace("'cases':36,'samples':432", "'cases':54,'samples':648")
    (W/name).write_text(s,encoding='utf-8')
s=(OLD/'run_model.py').read_text().replace('070','071').replace('Frozen36','Frozen54').replace("'publication_samples':432","'publication_samples':648").replace("'total':36","'total':54")
s=s.replace('from process_memory import peak_memory','from process_memory import peak_memory\nfrom order_plan import plan, validate')
start=s.index("    p=load(W/'policy.json');cases=[]");end=s.index("    save(W/'cohort-policy.json'",start)
s=s[:start]+'''    p=load(W/'policy.json');assert p['method']['rounds']==6 and p['method']['cases']==54
    cases=plan();balance=validate(cases)
    save(W/'order-balance-pre-timing.json',balance)
'''+s[end:]
s=s.replace("'oracle_provenance_sha256':sha(W/'oracle-provenance.json'),", "'oracle_provenance_sha256':sha(W/'oracle-provenance.json'),'order_plan_sha256':sha(W/'order_plan.py'),'order_balance_sha256':sha(W/'order-balance-pre-timing.json'),")
start=s.index("    for i in load(W/'input-provenance.json')")
s=s[:start]+'''    assert sha(W/'order_plan.py')==p['order_plan_sha256'] and sha(W/'order-balance-pre-timing.json')==p['order_balance_sha256']
    assert validate(p['cases'])==load(W/'order-balance-pre-timing.json')
'''+s[start:]
# JSON normalizes integer dictionary keys; compare canonically rather than Python key types.
s=s.replace("assert validate(p['cases'])==load(W/'order-balance-pre-timing.json')", "assert json.loads(json.dumps(validate(p['cases'])))==load(W/'order-balance-pre-timing.json')")
(W/'run_model.py').write_text(s,encoding='utf-8')
s=(OLD/'audit_model.py').read_text().replace('070','071').replace('==36','==54').replace('range(4)','range(6)').replace('432','648')
s=s.replace('from zstd_frame_oracle import check_frame','from zstd_frame_oracle import check_frame\nfrom order_plan import validate')
at=s.index("assert result['cohort_policy_sha256']")
s=s[:at]+'''assert cohort['order_plan_sha256']==sha(W/'order_plan.py') and cohort['order_balance_sha256']==sha(W/'order-balance-pre-timing.json')
assert json.loads(json.dumps(validate(cohort['cases'])))==load(W/'order-balance-pre-timing.json')
'''+s[at:]
s=s.replace("x['native_zstd_version']=='1.5.7'", "x['native_zstd_version']=='1.5.7' and x['compression_level']==-5")
s=s.replace("'independent_frame_boundary_and_content_size_passed':True", "'independent_frame_boundary_and_content_size_passed':True,'balanced_size_variant_and_AB_relative_order_verified':True")
(W/'audit_model.py').write_text(s,encoding='utf-8')
s=(OLD/'prepare.py').read_text().replace("OLD=W.parent/'perf-069'", "OLD=W.parent/'perf-070'").replace('trial=70','trial=71').replace('native level1','native level-5')
s=s.replace("motivation='069 zlib saved bytes but regressed charged latency; 070 independently tests lower codec cost using exact real inputs and all unchanged gates'", "motivation='070 level1 regressed charged time; independently selected fast level-5 tests lower codec CPU, with corrected balanced order, fresh raw controls and unchanged thresholds'")
s=s.replace("assert policy['checks']==load(OLD/'policy.json')['checks'] and policy['method']==load(OLD/'policy.json')['method']", "policy['method'].update(rounds=6,cases=54,all_six_variant_orders_per_size=True,each_variant_each_position=2,balanced_AB_relative_order=True)\npolicy['aggregation']='Median of six matched per-round ratios; twelve samples per case, Type7 quantiles, every tail retained. Model gates never qualify SQL.'\nassert policy['checks']==load(OLD/'policy.json')['checks']")
s=s.replace("'cases':36", "'cases':54")
(W/'prepare.py').write_text(s,encoding='utf-8')
for p in W.glob('*.py'):ast.parse(p.read_text())
save(W/'derivation.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'from_trial':70,'new_trial':71,
    'same_publication_lifecycle_and_acceptance_thresholds':True,'no_previous_timed_results_reused':True,
    'changes':'only native compression level1 to independently selected -5; fresh magic/probe; corrected balanced six-permutation scheduling and pre/post balance checks',
    'source_sha256':{n:sha(OLD/n) for n in ['model/src/main.rs','run_model.py','audit_model.py','prepare.py','policy.json']},
    'default_sql_engine_unchanged':True})
print(json.dumps({'assembled':True,'cases':54,'tests_expected':12,'compression_level':-5}))
