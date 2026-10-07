"""Independent Python/zlib byte oracle, charged metrics and fixed paired gates."""
from datetime import datetime, timezone
import hashlib, json, math, statistics, struct, zlib
from pathlib import Path
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def q(xs,p):
    xs=sorted(xs);at=(len(xs)-1)*p;lo=math.floor(at);hi=math.ceil(at);return xs[lo]+(xs[hi]-xs[lo])*(at-lo)
policy=load(W/'policy.json');cohort=load(W/'cohort-policy.json');result=load(W/'model-results.json')
assert result['complete'] and not result['failures'] and len(result['cases'])==36
assert cohort['independent_auditor_sha256']==sha(Path(__file__)) and cohort['policy_sha256']==sha(W/'policy.json')
assert result['cohort_policy_sha256']==sha(W/'cohort-policy.json') and [c['spec'] for c in result['cases']]==cohort['cases']
assert not load(W/'post-timing-process-check.json')['active_processes']
input_map={i['seed_receipts']:i for i in load(W/'input-provenance.json')['inputs']}
cases=[];files={};mode_hashes={};decoded_bytes=0
for c in result['cases']:
    label=c['label'];spec=c['spec'];raw=W/'raw'
    for suffix,key in [('stdout.json','stdout_sha256'),('status.json','status_sha256'),('stderr.txt','stderr_sha256')]:assert sha(raw/f'{label}.{suffix}')==c[key]
    x=load(raw/f'{label}.stdout.json');status=load(raw/f'{label}.status.json');assert status['exit_code']==0 and status['memory']['success']
    source=Path(input_map[spec['seed_receipts']]['path']).read_bytes();assert x['input_bytes']==len(source) and x['mode']==spec['mode']
    assert all(x[k] for k in ['model_only','all_bytes_match_original','one_sync_all_per_publication','all_files_retained','no_sql_or_engine_change','bounded_output_exact_stream_consumption','fresh_open_not_cold_os_cache'])
    assert x['decode_limit_bytes']==64*1024*1024 and len(x['samples'])==len(x['fresh_read_decode_ms'])==12
    directory=Path(status['fixture']);assert len(list(directory.glob('*.model')))==12 and not list(directory.glob('*.pending'))
    sizes=[]
    for index,s in enumerate(x['samples']):
        assert s['sequence']==index
        times=[s[k] for k in ['outer_ms','encode_ms','write_ms','sync_ms','rename_ms']]
        assert all(math.isfinite(t) and t>=0 for t in times) and sum(times[1:])<=times[0]+1e-6
        p=directory/f'checkpoint-{index:03}.model';frame=p.read_bytes();assert len(frame)==s['stored_bytes'] and frame[:8]==b'KCMP0691'
        codec,raw_len,stored_len,raw_crc,stored_crc,header_crc=struct.unpack('<IIIIII',frame[8:32]);payload=frame[32:]
        assert codec==(1 if spec['mode']=='zlib' else 0) and raw_len==len(source) and stored_len==len(payload)
        assert raw_len<=64*1024*1024 and stored_len<=64*1024*1024
        assert zlib.crc32(frame[:28])==header_crc and zlib.crc32(payload)==stored_crc
        if codec:
            decoder=zlib.decompressobj();decoded=decoder.decompress(payload,raw_len+1)
            assert decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail and len(decoded)==raw_len
        else:decoded=payload
        assert decoded==source and zlib.crc32(decoded)==raw_crc
        digest=sha(p);key=(spec['seed_receipts'],spec['mode'])
        if key in mode_hashes:assert mode_hashes[key]==digest
        else:mode_hashes[key]=digest
        files[p.relative_to(W).as_posix()]={'bytes':len(frame),'sha256':digest};sizes.append(len(frame));decoded_bytes+=raw_len
    assert len(set(sizes))==1
    values=[s['outer_ms'] for s in x['samples']];fresh=x['fresh_read_decode_ms']
    cases.append({'label':label,'spec':spec,'total_ms':sum(values),'p50_ms':q(values,.5),'p99_ms':q(values,.99),'max_ms':max(values),
        'stored_bytes_per_frame':sizes[0],'encode_total_ms':sum(s['encode_ms'] for s in x['samples']),
        'sync_total_ms':sum(s['sync_ms'] for s in x['samples']),'fresh_read_decode_p99_ms':q(fresh,.99),
        'peak_working_set_bytes':status['memory']['peak_working_set_bytes'],'peak_commit_bytes':status['memory']['peak_commit_bytes'],
        'stage_totals_ms':{k:sum(s[k] for s in x['samples']) for k in ['encode_ms','write_ms','sync_ms','rename_ms']}})
checks=[];summaries=[]
def add(kind,size,metric,ratio,limit=None,interval=None):
    passed=ratio is not None and math.isfinite(ratio) and (interval[0]<=ratio<=interval[1] if interval else ratio<=limit)
    checks.append({'kind':kind,'size':size,'metric':metric,'paired_ratio_or_absolute':ratio,'limit':limit,'interval':interval,'passed':passed})
for seed in [0,50000,99000]:
    pairs=[]
    for turn in range(4):
        group={c['spec']['variant']:c for c in cases if c['spec']['round']==turn and c['spec']['seed_receipts']==seed}
        a=group['baseline_a'];b=group['baseline_b'];candidate=group['compressed']
        metrics=['total_ms','p50_ms','p99_ms','max_ms','encode_total_ms','fresh_read_decode_p99_ms','peak_working_set_bytes','peak_commit_bytes','stored_bytes_per_frame']
        pairs.append({'round':turn,'compressed_a':{k:candidate[k]/a[k] for k in metrics},'identity_b_a':{k:b[k]/a[k] for k in metrics}})
    paired={label:{k:statistics.median(p[label][k] for p in pairs) for k in metrics} for label in ['compressed_a','identity_b_a']}
    c=paired['compressed_a'];limits=policy['checks']
    if seed:
        add('goal',seed,'stored_bytes_per_frame',c['stored_bytes_per_frame'],limit=limits['large_stored_byte_ratio_max'])
        add('goal',seed,'total_ms',c['total_ms'],limit=limits['large_charged_publication_total_ratio_max'])
    else:add('guard',seed,'total_ms',c['total_ms'],limit=limits['small_total_guard_max'])
    for metric,limit in [('p50_ms','p50_guard_max'),('p99_ms','p99_guard_max'),('max_ms','max_guard_max'),('peak_working_set_bytes','peak_working_set_and_commit_guard_max'),('peak_commit_bytes','peak_working_set_and_commit_guard_max')]:add('guard',seed,metric,c[metric],limit=limits[limit])
    maximum=max(c['fresh_read_decode_p99_ms'] for c in cases if c['spec']['seed_receipts']==seed and c['spec']['variant']=='compressed')
    add('guard',seed,'fresh_read_decode_p99_absolute_ms',maximum,limit=limits['fresh_read_decode_p99_absolute_max_ms'])
    for metric in limits['identity_metrics']:add('identity',seed,metric,paired['identity_b_a'][metric],interval=limits['identity_interval'])
    display={label:{k:statistics.median(c[k] for c in cases if c['spec']['seed_receipts']==seed and c['spec']['variant']==label) for k in metrics} for label in ['baseline_a','baseline_b','compressed']}
    summaries.append({'seed_receipts':seed,'actual_receipts':input_map[seed]['actual_receipts'],'input_bytes':input_map[seed]['bytes'],
                      'pairs':pairs,'median_paired_ratios':paired,'median_display_only':display})
save(W/'fixture-inventory.json',files)
a={'audited_utc':datetime.now(timezone.utc).isoformat(),'complete':True,'cases':cases,'summaries':summaries,'checks':checks,
    'failed_checks':[c for c in checks if not c['passed']],'advance_to_engine_design':all(c['passed'] for c in checks),
    'model_only':True,'no_sql_engine_edit_or_promotion':True,'raw_hashes_order_stages_counts_frames_and_python_decoder_passed':True,
    'fixed_mode_frames_byte_identical_across_all_rounds_and_sequences':True,'file_instances':len(files),
    'stored_bytes_total':sum(f['bytes'] for f in files.values()),'independent_decoded_bytes':decoded_bytes,
    'samples':432,'fresh_open_decode_samples':432,'fixture_inventory_sha256':sha(W/'fixture-inventory.json'),
    'policy_and_auditor_unchanged_since_before_timing':True}
assert len(files)==432 and len(checks)==47
save(W/'model-audit.json',a)
print(json.dumps({'complete':True,'samples':432,'files':len(files),'stored_bytes':a['stored_bytes_total'],'decoded_bytes':decoded_bytes,
    'failed':{k:sum(c['kind']==k for c in a['failed_checks']) for k in ['goal','guard','identity']},'advance_to_engine_design':a['advance_to_engine_design']}))
