"""Independent exact-input and post-timing policy audit of CPU-only models."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math,statistics,struct,zlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def quantile(v,q):
    v=sorted(v);x=(len(v)-1)*q;left=math.floor(x);right=math.ceil(x);return v[left]+(v[right]-v[left])*(x-left)
def dt(s):return datetime.fromisoformat(s)
p=load(W/'policy.json');r=load(W/'results.json');f=load(W/'timing-provenance.json');b=load(W/'build.json')
assert r['complete'] and len(r['cases'])==len(p['cases'])==48 and not r['failures']
assert sha(W/'timing-provenance.json')==r['timing_provenance_sha256']
for name,key in [('policy.json','policy_sha256'),('bin/encoder-probe.exe','binary_sha256'),('encoder_probe.rs','probe_source_sha256'),('released_encoder_models.rs','models_sha256'),('run.py','harness_sha256'),('process_memory.py','memory_helper_sha256'),('build.json','build_sha256'),('smoke.json','smoke_sha256'),('pre-timing-process-check.json','pre_timing_process_check_sha256')]:assert sha(W/name)==f[key],name
assert b['complete'] and b['binary_sha256']==f['binary_sha256']
assert dt(b['completed_utc'])<=dt(load(W/'smoke.json')['completed_utc'])<=dt(f['declared_utc'])<=dt(r['started_utc'])
assert not load(W/'pre-timing-process-check.json')['active_processes'] and not load(W/'post-timing-process-check.json')['active_processes']
baseline=load(W/'baseline.json')
for name,digest in baseline['core_source_sha256'].items():assert sha(ROOT/name)==digest,name
for name,digest in baseline['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/name)==digest,name
source=(ROOT/'src/archive.rs').read_text(encoding='utf-8');start=source.index('#[derive(Serialize)]\nstruct CatalogOutput');end=source.index('impl BatchRecord {',start)
assert (W/'released_encoder_models.rs').read_text(encoding='utf-8')==source[start:end]
inputs={i['starting_receipts']:i for i in p['inputs']}
for item in inputs.values():
    assert sha(W/item['body_relative'])==item['body_sha256'] and sha(W/item['envelope_relative'])==item['envelope_sha256']
    envelope=(W/item['envelope_relative']).read_bytes();body=(W/item['body_relative']).read_bytes()
    assert envelope[:8]==b'KSQLCAT4' and envelope[16:]==body
    length,crc=struct.unpack('<II',envelope[8:16]);assert length==len(body) and zlib.crc32(body)==crc
    obj=json.loads(body);assert obj['receipt_base'] is None and len(obj['batches'])==item['receipts'] and next(reversed(obj['batches']))==item['last_id']
expected=[];labels=p['variants']
for turn in range(4):
    for index,size in enumerate([0,50000,99000]):
        k=(turn+index)%4
        for label in labels[k:]+labels[:k]:expected.append({'round':turn,'starting_receipts':size,'variant':label,'repetitions':33})
assert expected==p['cases']
cases=[];last_end=dt(r['started_utc'])
for item,spec in zip(r['cases'],expected):
    assert item['spec']==spec;label=item['label'];raw=W/'raw'
    for suffix,key in [('stdout.json','stdout_sha256'),('stderr.txt','stderr_sha256'),('status.json','status_sha256')]:assert sha(raw/f'{label}.{suffix}')==item[key]
    x=load(raw/f'{label}.stdout.json');s=load(raw/f'{label}.status.json');inp=inputs[spec['starting_receipts']]
    assert s['spec']==spec and s['exit']==0 and not s.get('timeout')
    assert last_end<=dt(s['started_utc'])<=dt(s['ended_utc']);last_end=dt(s['ended_utc'])
    mode='baseline' if spec['variant'].startswith('baseline') else spec['variant']
    assert x['mode']==mode and x['receipt_count']==inp['receipts'] and x['input_bytes']==inp['bytes']
    assert x['encoder_model_only'] and x['no_database_publication'] and x['every_output_matches_original_catalog_bytes']
    v=x['raw_ms'];caps=x['capacities'];assert len(v)==len(caps)==x['repetitions']==33
    assert all(math.isfinite(y) and y>=0 for y in v) and all(c>=inp['bytes'] for c in caps)
    assert len(set(caps))==1
    if mode=='reserve_exact':assert caps[0]==inp['bytes']
    if mode=='baseline':assert caps[0]>=128 and caps[0]&(caps[0]-1)==0
    m=s['memory'];available=m['success'] and m['peak_working_set_bytes']>0 and m['peak_commit_bytes']>0
    cases.append({'spec':spec,'label':label,'receipts':inp['receipts'],'input_bytes':inp['bytes'],'total_ms':sum(v),'p50_ms':quantile(v,.5),
        'p99_ms':quantile(v,.99),'max_ms':max(v),'first_encode_ms':v[0],'warm_only_p50_diagnostic_ms':quantile(v[1:],.5),
        'capacity_bytes':caps[0],'memory_available':available,'peak_working_set_bytes':m['peak_working_set_bytes'] if available else None,
        'peak_commit_bytes':m['peak_commit_bytes'] if available else None})
metrics=p['identity_metrics'];summaries=[];checks=[]
for size in [0,50000,99000]:
    selected=[c for c in cases if c['spec']['starting_receipts']==size];pairs=[]
    for turn in range(4):
        matched={label:next(c for c in selected if c['spec']['round']==turn and c['spec']['variant']==label) for label in labels};ratios={}
        for comparison,num,den in [('identity_b_a','baseline_b','baseline_a'),('reserve_exact_a','reserve_exact','baseline_a'),('reuse_a','reuse','baseline_a'),('reserve_exact_b_diagnostic','reserve_exact','baseline_b'),('reuse_b_diagnostic','reuse','baseline_b')]:
            ratios[comparison]={key:matched[num][key]/matched[den][key] if matched[num][key] is not None and matched[den][key] is not None and matched[den][key]>0 else None for key in metrics}
        pairs.append({'round':turn,'ratios':ratios})
    medians={comp:{key:statistics.median(pair['ratios'][comp][key] for pair in pairs) if all(pair['ratios'][comp][key] is not None for pair in pairs) else None for key in metrics} for comp in pairs[0]['ratios']}
    display={label:{key:statistics.median(c[key] for c in selected if c['spec']['variant']==label) if all(c[key] is not None for c in selected if c['spec']['variant']==label) else None for key in metrics+['peak_commit_bytes','capacity_bytes','max_ms','warm_only_p50_diagnostic_ms']} for label in labels}
    low,high=p['identity_ratio_interval']
    for key in metrics:
        ratio=medians['identity_b_a'][key];checks.append({'size':size,'variant':'identity_b_a','kind':'identity','metric':key,'paired_ratio':ratio,'interval':[low,high],'passed':ratio is not None and low<=ratio<=high})
    for variant in ['reserve_exact','reuse']:
        values=medians[variant+'_a']
        if size:
            for key,limit in [('total_ms',p['goals_large_histories']['total_ratio_max']),('p50_ms',p['goals_large_histories']['p50_ratio_max'])]:
                ratio=values[key];checks.append({'size':size,'variant':variant,'kind':'goal','metric':key,'paired_ratio':ratio,'limit':limit,'passed':ratio is not None and ratio<=limit})
        guards={'p99_ms':p['guards_all_histories']['p99_ratio_max'],'first_encode_ms':p['guards_all_histories']['first_encode_ratio_max'],'peak_working_set_bytes':p['guards_all_histories']['peak_working_set_ratio_max']}
        if not size:guards['p50_ms']=p['small_history_p50_guard_max']
        for key,limit in guards.items():
            ratio=values[key];checks.append({'size':size,'variant':variant,'kind':'guard','metric':key,'paired_ratio':ratio,'limit':limit,'passed':ratio is not None and ratio<=limit})
    summaries.append({'starting_receipts':size,'receipts':inputs[size]['receipts'],'input_bytes':inputs[size]['bytes'],'variants_median_display_only':display,'pairs':pairs,'median_paired_ratios':medians})
failed=[c for c in checks if not c['passed']];identity_ok=all(c['passed'] for c in checks if c['kind']=='identity')
decisions={variant:{'own_goals_and_guards_passed':all(c['passed'] for c in checks if c['variant']==variant),'all_identity_checks_passed':identity_ok,
    'justifies_engine_buffer_experiment':identity_ok and all(c['passed'] for c in checks if c['variant']==variant)} for variant in ['reserve_exact','reuse']}
out={'audited_utc':datetime.now(timezone.utc).isoformat(),'complete':True,'cases':cases,'summaries':summaries,'checks':checks,'failed_checks':failed,'decisions':decisions,
    'timed_encodes':48*33,'exact_output_bytes_checked':sum(c['input_bytes']*33 for c in cases),'quantile_method':'Type7 over33 encodes including cold first encode; warm-only median diagnostic excludes first',
    'identity_checks_failed':sum(c['kind']=='identity' for c in failed),'goals_failed':sum(c['kind']=='goal' for c in failed),'guards_failed':sum(c['kind']=='guard' for c in failed),
    'policy_and_source_and_inputs_and_raw_hashes_case_order_and_timelines_passed':True,'byte_equality_per_encode_passed':True,
    'all_task_processes_stopped':True,'engine_change':False,'default_promoted':False,'database_benchmark':False,'new_correctness_crash_suite':False,
    'scope':'Exact released borrowed serializer CPU/output-allocation models; no append, sync, SQL, network throughput or production qualification'}
(W/'audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k not in ['cases','summaries','checks']},indent=2))
