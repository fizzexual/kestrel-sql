"""Pin retained inputs, runtime oracle and independently declared identical gates."""
from datetime import datetime, timezone
import hashlib, json, shutil, struct, zlib, sys
from pathlib import Path
import pyarrow
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-070';ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert not (W/'policy.json').exists()
baseline=load(OLD/'baseline.json')
for n,d in baseline['core_source_sha256'].items():assert sha(ROOT/n)==d,n
for n,d in baseline['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
shutil.copy2(OLD/'baseline.json',W/'baseline.json')
(W/'inputs').mkdir();inputs=[]
for item in load(OLD/'input-provenance.json')['inputs']:
    source=Path(item['path']);assert sha(source)==item['sha256']
    file=W/'inputs'/source.name;shutil.copy2(source,file);assert sha(file)==item['sha256']
    data=file.read_bytes();size,crc=struct.unpack('<II',data[8:16]);assert data[:8]==b'KSQLCAT4' and size+16==len(data) and zlib.crc32(data[16:])==crc
    body=json.loads(data[16:]);assert body['generation']==129 and body['receipt_base'] is None and len(body['batches'])==item['actual_receipts']
    inputs.append({**item,'path':str(file),'source':str(source),'original_archive':item['source']})
save(W/'input-provenance.json',{'copied_utc':datetime.now(timezone.utc).isoformat(),'all_inputs_from_068_retained_real_archives':True,'unchanged069_inputs':True,'inputs':inputs,'no_new_database_job':True})
assert pyarrow.__version__=='25.0.1'
arrow_dir=Path(pyarrow.__file__).parent
files=[Path(pyarrow.__file__),*arrow_dir.glob('*.dll'),*arrow_dir.glob('lib.*.pyd')]
save(W/'oracle-provenance.json',{'version':pyarrow.__version__,'binding':'pyarrow.Codec(zstd)','python':sys.version,
    'files':{str(p):sha(p) for p in files},'separate_language_and_binding_not_independent_codec_implementation':True,
    'strict_stream_check_by_native_model_not_claimed_for_arrow':True,'recorded_before_timing':True})
policy=load(OLD/'policy.json');policy.update(trial=71,declared_utc=datetime.now(timezone.utc).isoformat(),
    codec='offline cached zstd-safe exactly7.2.4, zstd-sys locked2.0.16+zstd.1.5.7, native level-5, one-shot contexts charged',
    motivation='070 level1 regressed charged time; independently selected fast level-5 tests lower codec CPU, with corrected balanced order, fresh raw controls and unchanged thresholds',
    independent_previous_policy_sha256=sha(OLD/'policy.json'),
    decode_bounds='64MiB encoded/decoded payload; CRC header/stored/decoded; standard Zstandard magic; exactly one frame; known frame content size equals bounded outer length before output allocation; one-shot destination exactly raw_len')
policy['method'].update(rounds=6,cases=54,all_six_variant_orders_per_size=True,each_variant_each_position=2,balanced_AB_relative_order=True)
policy['aggregation']='Median of six matched per-round ratios; twelve samples per case, Type7 quantiles, every tail retained. Model gates never qualify SQL.'
assert policy['checks']==load(OLD/'policy.json')['checks']
save(W/'policy.json',policy)
print(json.dumps({'prepared':True,'cases':54,'all_gates_unchanged':True,'inputs':[i['bytes'] for i in inputs],'free_bytes':shutil.disk_usage(W).free}))
