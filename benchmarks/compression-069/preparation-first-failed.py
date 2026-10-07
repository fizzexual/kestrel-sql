"""Pin real retained CAT4 input and a model-only policy before any timers."""
from datetime import datetime, timezone
import hashlib, json, shutil, struct, zlib
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';OLD=W.parent/'perf-068'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W/'policy.json').exists()
baseline=load(OLD/'baseline.json')
for n,d in baseline['core_source_sha256'].items():assert sha(ROOT/n)==d,n
for n,d in baseline['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
shutil.copy2(OLD/'baseline.json',W/'baseline.json');shutil.copy2(OLD/'process_memory.py',W/'process_memory.py') if (OLD/'process_memory.py').exists() else shutil.copy2(W.parent/'perf-067/process_memory.py',W/'process_memory.py')
(W/'inputs').mkdir();inputs=[]
for seed,prefix in [(0,'00-r0-0'),(50000,'01-r0-50000'),(99000,'02-r0-99000')]:
    source=OLD/'diagnostic-fixtures'/prefix/'catalog-00000000000000000129.ks2'
    file=W/'inputs'/f'{seed}.ks2';shutil.copy2(source,file);data=file.read_bytes()
    assert data[:8]==b'KSQLCAT4';size,crc=struct.unpack('<II',data[8:16]);assert size+16==len(data) and zlib.crc32(data[16:])==crc
    body=json.loads(data[16:]);assert body['receipt_base'] is None and body['generation']==129
    receipts=seed+(127 if seed==0 else 126);assert len(body['batches'])==receipts
    inputs.append({'seed_receipts':seed,'actual_receipts':receipts,'generation':129,'path':str(file),'source':str(source),
        'bytes':len(data),'sha256':sha(file),'stored_original_envelope_verified':True,'checkpoint_not_delta':True})
save(W/'input-provenance.json',{'copied_utc':datetime.now(timezone.utc).isoformat(),'all_inputs_from_068_retained_real_archives':True,'inputs':inputs,'no_new_database_job':True})
save(W/'policy.json',{'trial':69,'declared_utc':datetime.now(timezone.utc).isoformat(),'before_any_model_timers':True,
    'model_only':True,'new_sql_engine':False,'default_engine_changed':False,'codec':'offline cached miniz_oxide exactly0.8.9, zlib level1',
    'motivation':'068 eight checkpoint stalls dominated by catalog_sync; reducing stored bytes is a hypothesis, not a proven I/O cause',
    'compatibility':'Released reader chain budget32 is unchanged. This model is not a Kestrel disk format; no engine dependency or format edit.',
    'method':{'rounds':4,'variants':['baseline_a','baseline_b','compressed'],'cases':36,'repetitions':12,'sizes':[0,50000,99000],
        'same_frozen_executable_for_all_modes':True,'A_and_B_same_raw_mode_same_path':True,'rotate_variant_order_and_size_order':True,
        'all_commits_one_sync_all_and_rename':True,'all_files_retained':True,'no_case_retry_or_threshold_change':True},
    'timing':'Outer publication includes frame encoding, compression for candidate, both CRCs, allocation/copies, open/write/flush, sync_all, close, rename and frame release. Canonical input read and final byte checks excluded.',
    'decode':'Fresh file open+read+bounded decode+CRC measured after publication cohort within each child; same process, OS cache not cold. Exact byte comparison outside decode timer. Not Archive cold reopen.',
    'scope_excluded':['SQL','serde serialization','growing receipts','source offsets','migration','Archive recovery or crash/power-loss','query readers','compaction','service concurrency'],
    'checks':{'large_stored_byte_ratio_max':0.65,'large_charged_publication_total_ratio_max':0.90,'small_total_guard_max':1.10,
        'p50_guard_max':1.05,'p99_guard_max':1.10,'max_guard_max':1.10,'peak_working_set_and_commit_guard_max':1.35,
        'fresh_read_decode_p99_absolute_max_ms':200,'identity_interval':[0.90,1.10],
        'identity_metrics':['total_ms','p50_ms','p99_ms','max_ms','encode_total_ms','fresh_read_decode_p99_ms','peak_working_set_bytes','peak_commit_bytes']},
    'aggregation':'Median of four matched per-round ratios; twelve samples per case, Type7 quantiles, all tails retained. Model gates never qualify the SQL engine.',
    'advance':'Only all goals/guards/A-A checks passing motivates a separately designed engine candidate; never a supported release or speed claim.',
    'decode_bounds':'64MiB maximum encoded and decoded payload, CRC header/encoded/decoded, exact stream byte consumption, no trailing frames',
    'minimum_free_bytes':3000000000,'timeout_per_case_seconds':600,
    'process_policy':'This computer only, one task-owned child at a time; no compile/test/audit/package/Git during timed publications',
    'language':'English','morning_report_frozen_not_reissued':True})
print(json.dumps({'prepared':True,'inputs':[{k:i[k] for k in ['seed_receipts','actual_receipts','bytes']} for i in inputs],'cases':36,'free_bytes':shutil.disk_usage(W).free}))
