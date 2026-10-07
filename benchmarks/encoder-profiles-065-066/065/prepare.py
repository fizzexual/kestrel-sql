"""Freeze an encoder-only model policy and exact released catalog inputs."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,shutil,struct,zlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';OLD=W.parent/'perf-064'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def unique(pairs):
    d={}
    for k,v in pairs:
        assert k not in d,('duplicate key',k);d[k]=v
    return d
assert not (W/'policy.json').exists()
base=load(OLD/'baseline.json')
for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d,n
for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
shutil.copy2(OLD/'baseline.json',W/'baseline.json')
archive=(ROOT/'src/archive.rs').read_text(encoding='utf-8')
start=archive.index('#[derive(Serialize)]\nstruct CatalogOutput')
end=archive.index('impl BatchRecord {',start)
models=archive[start:end]
(W/'released_encoder_models.rs').write_text(models,encoding='utf-8')
(W/'inputs').mkdir();inventory=load(OLD/'fixture-inventory.json');inputs=[]
cases=load(OLD/'native-results.json')['cases']
for size in [0,50000,99000]:
    case=next(c for c in cases if c['spec']['round']==0 and c['spec']['seed_receipts']==size and c['spec']['variant']=='baseline_a')
    directory=OLD/'native-fixtures'/case['label'];choices=[]
    for file in directory.glob('catalog-*.ks2'):
        data=file.read_bytes();assert data[:8]==b'KSQLCAT4'
        length,crc=struct.unpack('<II',data[8:16]);body=data[16:]
        assert length==len(body) and zlib.crc32(body)==crc
        obj=json.loads(body,object_pairs_hook=unique)
        if obj['receipt_base'] is None:choices.append((obj['generation'],file,body,obj))
    generation,file,body,obj=max(choices,key=lambda x:x[0]);rel=file.relative_to(OLD).as_posix();known=inventory[rel]
    assert known['sha256']==sha(file) and known['bytes']==file.stat().st_size
    assert 0<len(obj['batches'])<=100000
    for record in obj['batches'].values():
        assert set(record)=={'digest','rows','generation'} and len(record['digest'])==32
        assert all(type(v)==int and 0<=v<=255 for v in record['digest'])
    destination=W/'inputs'/f'{size}-checkpoint.json';destination.write_bytes(body)
    envelope=W/'inputs'/f'{size}-checkpoint.ks2';shutil.copy2(file,envelope)
    inputs.append({'starting_receipts':size,'source_path':str(file),'source_fixture_key':rel,'source_envelope_sha256':sha(file),
        'body_path':str(destination),'body_relative':destination.relative_to(W).as_posix(),'body_sha256':sha(destination),'bytes':len(body),
        'envelope_relative':envelope.relative_to(W).as_posix(),'envelope_sha256':sha(envelope),'generation':generation,'receipts':len(obj['batches']),
        'last_id':next(reversed(obj['batches'])),'receipt_base':None,'envelope_crc_passed':True,'all_duplicate_keys_rejected':True})
shutil.copy2(OLD/'process_memory.py',W/'process_memory.py')
serde_path=Path('C:/Users/Frizer/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/serde_json-1.0.151/src/ser.rs')
serde_source=serde_path.read_text(encoding='utf-8');begin=serde_source.index('pub fn to_vec<T>');finish=serde_source.index('/// Serialize',begin)
(W/'serde_to_vec_excerpt.rs.txt').write_text(serde_source[begin:finish],encoding='utf-8')
assert 'Vec::with_capacity(128)' in serde_source[begin:finish]
save(W/'input-provenance.json',{'inputs':inputs,'released_archive_sha256':sha(ROOT/'src/archive.rs'),'released_encoder_models_sha256':sha(W/'released_encoder_models.rs'),
    'source_extraction_begin':start,'source_extraction_end':end,'serde_json_locked_version':'1.0.151','serde_source_sha256':sha(serde_path),
    'source_private_asset':'https://github.com/fizzexual/kestrel-sql/releases/download/v0.3.16/kestrel-sql-development-064-compaction-evidence.zip'})
variants=['baseline_a','baseline_b','reserve_exact','reuse'];cases=[]
for turn in range(4):
    for index,size in enumerate([0,50000,99000]):
        k=(turn+index)%4
        for variant in variants[k:]+variants[:k]:cases.append({'round':turn,'starting_receipts':size,'variant':variant,'repetitions':33})
save(W/'policy.json',{'trial':65,'declared_utc':datetime.now(timezone.utc).isoformat(),'before_build_and_timing':True,'engine_change':False,
    'purpose':'Isolate output-buffer growth in exact released borrowed catalog serializer; hypothetical allocation models, not database performance',
    'variants':variants,'cases':cases,'same_exact_probe_path_and_sha_for_all_labels':True,'baseline_a_b_same_exact_mode':True,
    'inputs':inputs,'rounds':4,'repetitions':33,'warmups':0,'input_loading_deserialization_oracles_and_output_drop_outside_timer':True,
    'allocation_model':'Baseline: released to_vec starts128; reserve_exact: cold Vec sized from known input bytes; reuse: empty Vec at case start, first allocation timed, capacity retained thereafter',
    'oracle_size_limit':'Exact future output length is known only for this fixed-input model; not a proposed deployable reservation predictor',
    'aggregation':'Median of four within-round ratios per input; A primary, B identity, models/B diagnostic only',
    'goals_large_histories':{'total_ratio_max':.90,'p50_ratio_max':.90},
    'guards_all_histories':{'p99_ratio_max':1.10,'first_encode_ratio_max':1.10,'peak_working_set_ratio_max':1.10},
    'small_history_p50_guard_max':1.05,'identity_ratio_interval':[.90,1.10],
    'identity_metrics':['total_ms','p50_ms','p99_ms','first_encode_ms','peak_working_set_bytes'],
    'decision':'Only models passing all own goals/guards plus every identity check justify an engine buffer experiment; no engine promotion, service sweep or SQL speed claim from this profile',
    'retain':'All raw iterations, first encodes, errors, capacity traces, inputs and binary; no best-run selection or silently restarted cases',
    'process_policy':'One task-owned probe; all compilation, audits, packaging and cleanup outside timers',
    'timeout_seconds_per_case':120,'minimum_free_bytes_before_case':300000000,'profiled_engine_version':'0.3.16'})
print(json.dumps({'prepared':True,'cases':len(cases),'inputs':[{'start':i['starting_receipts'],'receipts':i['receipts'],'bytes':i['bytes']} for i in inputs],'engine_change':False}))
