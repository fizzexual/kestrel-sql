"""Fresh frozen workload and policies, before any benchmark cohort timers."""
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-072';PREV=W.parent/'perf-071'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assert not (W/'policy.json').exists();(W/'inputs').mkdir()
inputs=[]
for item in load(OLD/'input-provenance.json')['inputs']:
    src=Path(item['path']);assert sha(src)==item['sha256'];out=W/'inputs'/src.name;shutil.copy2(src,out);inputs.append({**item,'path':str(out),'source_072':str(src)})
save(W/'input-provenance.json',{'inputs':inputs,'copied_utc':datetime.now(timezone.utc).isoformat(),'all_original_068_checkpoint_bytes_unchanged':True})
shutil.copy2(OLD/'original-input-origin-note.json',W/'original-input-origin-note.json');shutil.copy2(PREV/'process_memory.py',W/'process_memory.py')
planner=(PREV/'order_plan.py').read_text(encoding='utf-8').replace("'compressed'","'pages'").replace("'zstd'","'pages'").replace("'raw'","'cat4'").replace('12','64')
(W/'order_plan.py').write_text(planner,encoding='utf-8');r=subprocess.run(['python',str(W/'order_plan.py')],capture_output=True,text=True)
(W/'order-tests.log').write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0
oracle=(OLD/'oracle.py').read_text(encoding='utf-8').replace('def read_store(path):','def read_store(path,generation=None):').replace('g=max(roots);integer(next,1,2**64-1)','g=max(roots) if generation is None else generation;assert g in roots;integer(next,1,2**64-1)')
(W/'page_oracle.py').write_text(oracle,encoding='utf-8')
save(W/'helper-derivation.json',{'order_071_original_sha256':sha(PREV/'order_plan.py'),'order_073_sha256':sha(W/'order_plan.py'),'order_regression_groups_passed':3,
    'oracle_072_original_sha256':sha(OLD/'oracle.py'),'oracle_073_sha256':sha(W/'page_oracle.py'),'only_oracle_change':'optional historical root generation for retained-file audit',
    'memory_helper_071_sha256':sha(PREV/'process_memory.py'),'memory_helper_073_sha256':sha(W/'process_memory.py')})
save(W/'policy.json',{'trial':73,'declared_utc':datetime.now(timezone.utc).isoformat(),'before_first_cohort_timer':True,'model_only':True,'default_engine_changed':False,
    'method':{'rounds':6,'cases':54,'variants':['baseline_a','baseline_b','pages'],'sizes':[0,50000,99000],'publications_per_case':64,'complete_32_publication_cycles':2,
        'source_intervals_per_case':8,'ordinary_receipts_per_case':56,'fresh_recoveries_per_case':12,'recovery_after_publications':[31,32,63,64],'all_six_orders_per_size':True,
        'every_variant_and_size_each_position':2,'AB_relative_order_each_direction':3,'same_binary_and_IO_helper':True,'all_files_retained':True,'no_case_reruns':True},
    'checks':{'large_publication_total_ratio_max':0.9,'large_full_directory_byte_ratio_max':0.65,'small_publication_total_max':1.1,'p50_max':1.05,'p99_max':1.1,'max_max':1.1,
        'fresh_recovery_p99_max':1.1,'migration_ms_max':1.35,'source_publication_p99_max':1.1,'peak_memory_max':1.35,'small_full_directory_bytes_max':1.35,
        'identity_interval':[0.9,1.1],'identity_metrics':['total_ms','p50_ms','p99_ms','max_ms','encode_total_ms','fresh_recovery_p99_ms','migration_ms','stored_directory_bytes','peak_working_set_bytes','peak_commit_bytes']},
    'timing':'Includes actual batch creation, digest/source full-clone validation, metadata copies/serialization/CRC, all changed-file writes/flushes/syncs/closes/renames and ledger updates. Recovery and migration measured separately; full ledger summary SHA outside timers.',
    'fresh_recovery':'Same process after dropping writer, three opens at each of31/32/63/64; potentially warm OS cache, not cold cache.',
    'scope':'Metadata models only; segment references unchanged/opaque, no segment IO/SQL or engine lock/compaction/reclaim/full legacy-chain migration/service/power-loss qualification.',
    'qualification':'All4 goals,26 guards and30 A/A checks must pass before proposing engine design. No model result promotes a supported engine or proves SQL superiority.',
    'minimum_free_bytes':3_000_000_000,'timeout_per_case_seconds':600,'process_policy':'This computer only, one owned child; no compilation/audit/package/Git during timed workloads',
    'language':'English','morning_report_frozen':True})
print(json.dumps({'prepared':True,'cases':54,'publications':3456,'fresh_recoveries':648,'order_regression_groups':3,'free_bytes':shutil.disk_usage(W).free}))
