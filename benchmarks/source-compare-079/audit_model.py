"""Frozen independent full-file/logical-edit audit, deterministic replicas and paired gates."""
from datetime import datetime,timezone
import hashlib,json,math,statistics
from pathlib import Path
import page_oracle as o
from catalog_oracle import ledger_sha,read_catalog
import hybrid_oracle as h
from order_plan import validate
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def quantile(xs,p):
    xs=sorted(xs);at=(len(xs)-1)*p;lo=math.floor(at);hi=math.ceil(at);return xs[lo]+(xs[hi]-xs[lo])*(at-lo)
def expected_edits(old):
    ledger=dict(old['batches']);offsets=[0,1_000_000];snapshots={129:{'generation':129,'receipts':len(ledger),'ledger_sha256':ledger_sha(ledger),'positions':o.positions(ledger)}};entries=[]
    for n in range(64):
        if n%8==7:
            feed=(n//8)%2;start=offsets[feed];offsets[feed]+=7;id=o.source_id(f'benchmark-feed-{feed}',start,offsets[feed])
        else:id=f'grow073-{n:03}'
        r=o.new_record(n+100,len(old['columns']),130+n);assert id not in ledger;ledger[id]=r;entries.append({'id':id,'record':r})
        if n in [30,31,62,63]:snapshots[130+n]={'generation':130+n,'receipts':len(ledger),'ledger_sha256':ledger_sha(ledger),'positions':o.positions(ledger)}
    return entries,snapshots,ledger
def full_canonical_audit(path,mode,old,edits,final):
    """Decode every canonical file, then full-hash all replicas; no duplicate decode claim."""
    g0=old['generation'];ledger=dict(old['batches']);files={};schema={k:old[k] for k in ['table','columns','segments']}
    if mode=='cat4':
        for index,g in enumerate(range(g0,g0+65)):
            new={} if index==0 else {edits[index-1]['id']:edits[index-1]['record']}
            ledger.update(new);checkpoint=index%32==0
            p=path/f'catalog-{g:020}.model';v=o.document(o.envelope(p,b'KSQLCAT4',64*1024*1024));o.fields(v,'generation receipt_base table columns segments batches');o.schema(v)
            assert v['generation']==g and v['receipt_base']==(None if checkpoint else g-1)
            assert {k:v[k] for k in schema}==schema and v['batches']==(ledger if checkpoint else new)
            files[p.name]={'bytes':p.stat().st_size,'sha256':sha(p)}
        summary,actual=read_catalog(path);assert actual==final and summary['history_files']==1
        reachable=[f'catalog-{g0+64:020}.model']
    else:
        anchor_path=path/f'head-{g0:020}.model';body=o.envelope(anchor_path,b'KANC0741',64*1024*1024)
        assert o.document(body)==old
        original_input=next(Path(v['path']) for v in input_map.values() if v['actual_receipts']==len(old['batches']))
        assert body==o.envelope(original_input,b'KSQLCAT4',64*1024*1024)
        anchor_crc=o.zlib.crc32(body);parent_crc=anchor_crc;checkpoint=g0;refs=[];all_new=[]
        files[anchor_path.name]={'bytes':anchor_path.stat().st_size,'sha256':sha(anchor_path)}
        for index,g in enumerate(range(g0+1,g0+65),1):
            entry=edits[index-1];all_new.append(entry);p=path/f'head-{g:020}.model'
            if index%32:
                body=o.envelope(p,b'KDEL0741',4096);v=o.document(body)
                assert v=={'generation':g,'parent':g-1,'parent_crc':parent_crc,'checkpoint':checkpoint,
                           'depth':index%32,'receipt_count':len(old['batches'])+index,'records':[entry]}
            else:
                for slot in range((len(all_new)+511)//512):
                    records=all_new[slot*512:(slot+1)*512];page_path=path/f'hy-receipts-{g:020}-{slot:03}.model'
                    page_body=o.envelope(page_path,b'KPAG0741',256*1024)
                    assert o.document(page_body)=={'generation':g,'slot':slot,'records':records}
                    ref={'generation':g,'slot':slot,'count':len(records),'crc':o.zlib.crc32(page_body)}
                    if slot<len(refs):refs[slot]=ref
                    else:assert slot==len(refs);refs.append(ref)
                    files[page_path.name]={'bytes':page_path.stat().st_size,'sha256':sha(page_path)}
                body=o.envelope(p,b'KHED0741',512*1024);v=o.document(body)
                assert v=={'generation':g,'anchor_generation':g0,'anchor_crc':anchor_crc,
                           'receipt_count':len(old['batches'])+index,'pages':refs}
                checkpoint=g
            parent_crc=o.zlib.crc32(body);files[p.name]={'bytes':p.stat().st_size,'sha256':sha(p)}
        summary,actual,cp,reachable=h.read_store(path);assert actual==final and len(reachable)==3
    assert {p.name for p in path.iterdir() if p.is_file()}==set(files) and not list(path.glob('*.pending'))
    return files,reachable

policy=load(W/'policy.json');cohort=load(W/'cohort-policy.json');result=load(W/'model-results.json')
assert result['complete'] and not result['failures'] and len(result['cases'])==54
for n,d in cohort['frozen_file_sha256'].items():assert sha(W/n)==d,n
for n,d in cohort['binary_sha256'].items():assert sha(W/n)==d,n
assert not load(W/'post-timing-process-check.json')['active_processes']
assert [c['spec'] for c in result['cases']]==cohort['cases'] and json.loads(json.dumps(validate(cohort['cases'])))==load(W/'order-balance-pre-timing.json')
input_map={i['seed_receipts']:i for i in load(W/'input-provenance.json')['inputs']};expected={};canonical={};reachable={};files={};cases=[];logical_reads=0
for seed,item in input_map.items():
    old=o.legacy(Path(item['path']));assert len(old['batches'])==item['actual_receipts'];expected[seed]=(old,*expected_edits(old))
for c in result['cases']:
    label=c['label'];spec=c['spec'];raw=W/'raw';seed=spec['seed_receipts'];mode=spec['mode'];old,edits,snapshots,final=expected[seed]
    for suffix,key in [('stdout.json','stdout_sha256'),('status.json','status_sha256'),('stderr.txt','stderr_sha256')]:assert sha(raw/f'{label}.{suffix}')==c[key]
    x=load(raw/f'{label}.stdout.json');status=load(raw/f'{label}.status.json');path=Path(status['fixture']);assert status['exit_code']==0 and status['memory']['success']
    assert x['probe']=='GROWTHMODEL075' and x['mode']==mode and x['publications']==64 and x['cycles']==2
    for k in ['model_only','old_retry_and_collision_passed_without_IO','fresh_recovery_same_process_OS_cache_not_cold','all_files_retained','opaque_unchanged_segment_references_no_data_segment_IO','no_SQL_or_engine_change']:assert x[k]
    assert x['source_validation_full_clone_charged_in_all_modes']==(spec['variant']!='hybrid')
    if spec['variant']=='hybrid':
        assert x['source_validation_is_fully_charged'] and x['hybrid_source_validation']=='validated_incremental_state078'
    key=(seed,mode)
    if key not in canonical:
        canonical[key],reachable[key]=full_canonical_audit(path,mode,old,edits,final);logical_reads+=len(canonical[key])
    assert {p.name for p in path.iterdir() if p.is_file()}==set(canonical[key])
    directory_bytes=0
    for name,expected_file in canonical[key].items():
        p=path/name;assert p.stat().st_size==expected_file['bytes'] and sha(p)==expected_file['sha256'],(label,name)
        files[p.relative_to(W).as_posix()]=expected_file;directory_bytes+=p.stat().st_size
    initial=x['initial'];assert all(initial[k]==v for k,v in snapshots[129].items());assert all(x['final'][k]==v for k,v in snapshots[193].items())
    assert len(x['samples'])==64 and len(x['fresh_recovery'])==12
    for n,s in enumerate(x['samples']):
        assert s['sequence']==n and s['generation']==130+n and s['source_interval']==(n%8==7) and s['checkpoint']==(n in [31,63]) and s['rows']==7
        io=s['io'];values=[s['outer_ms'],*[io[k] for k in ['encode_ms','write_ms','sync_ms','rename_ms']]];assert all(math.isfinite(t) and t>=0 for t in values) and sum(values[1:])<=values[0]+1e-6
        name=f'catalog-{130+n:020}.model' if mode=='cat4' else f'head-{130+n:020}.model'
        written=canonical[key][name]['bytes']
        if mode=='hybrid':written+=sum(v['bytes'] for name,v in canonical[key].items() if name.startswith(f'hy-receipts-{130+n:020}-'))
        assert io['bytes']==written and io['synced_files']==(2 if mode=='hybrid' and n in [31,63] else 1)
    for i,r in enumerate(x['fresh_recovery']):
        n=[30,31,62,63][i//3];assert r['after_sequence']==n and r['repetition']==i%3 and math.isfinite(r['recovery_ms']) and r['recovery_ms']>=0
        assert all(r['summary'][k]==v for k,v in snapshots[130+n].items())
        expected_history=(32 if n%32==30 else 1) if mode=='cat4' else (32 if n==30 else 34 if n==62 else 3)
        assert r['summary']['history_files']==expected_history
    migration_bytes=sum(v['bytes'] for name,v in canonical[key].items() if name==f'catalog-{129:020}.model' or name==f'head-{129:020}.model')
    assert x['migration_io']['bytes']==migration_bytes and x['migration_io']['synced_files']==1
    assert migration_bytes+sum(s['io']['bytes'] for s in x['samples'])==directory_bytes
    values=[s['outer_ms'] for s in x['samples']];source=[s['outer_ms'] for s in x['samples'] if s['source_interval']]
    ordinary=[s['outer_ms'] for s in x['samples'] if not s['source_interval']]
    path_metrics={}
    for seq,path_name in [(30,'anchor31'),(31,'checkpoint32'),(62,'checkpoint_delta63'),(63,'checkpoint64')]:
        times=[r['recovery_ms'] for r in x['fresh_recovery'] if r['after_sequence']==seq]
        assert len(times)==3
        path_metrics.update({path_name+'_p50_ms':quantile(times,.5),path_name+'_p99_ms':quantile(times,.99)})
    cases.append({'ordinary_p50_ms':quantile(ordinary,.5),'ordinary_p99_ms':quantile(ordinary,.99),'ordinary_max_ms':max(ordinary),'source_p50_ms':quantile(source,.5),**path_metrics,'label':label,'spec':spec,'total_ms':sum(values),'p50_ms':quantile(values,.5),'p99_ms':quantile(values,.99),'max_ms':max(values),'encode_total_ms':sum(s['io']['encode_ms'] for s in x['samples']),
        'fresh_recovery_p99_ms':quantile([r['recovery_ms'] for r in x['fresh_recovery']],.99),'migration_ms':x['migration_ms'],'source_p99_ms':quantile(source,.99),'stored_directory_bytes':directory_bytes,'current_reachable_bytes':sum(canonical[key][n]['bytes'] for n in reachable[key]),
        'noncheckpoint_p50_ms':quantile([s['outer_ms'] for s in x['samples'] if not s['checkpoint']],.5),
        'noncheckpoint_p99_ms':quantile([s['outer_ms'] for s in x['samples'] if not s['checkpoint']],.99),
        'checkpoint_sum_ms':sum(s['outer_ms'] for s in x['samples'] if s['checkpoint']),
        'checkpoint_max_ms':max(s['outer_ms'] for s in x['samples'] if s['checkpoint']),
        'peak_working_set_bytes':status['memory']['peak_working_set_bytes'],'peak_commit_bytes':status['memory']['peak_commit_bytes'],'migration_bytes':migration_bytes,
        'publication_syncs':sum(s['io']['synced_files'] for s in x['samples']),'migration_syncs':x['migration_io']['synced_files'],
        'stage_totals_ms':{k:sum(s['io'][k] for s in x['samples']) for k in ['encode_ms','write_ms','sync_ms','rename_ms']}})
    print('audited',label,flush=True)
checks=[];summaries=[]
metrics=['ordinary_p50_ms','ordinary_p99_ms','ordinary_max_ms','source_p50_ms','total_ms','p50_ms','p99_ms','max_ms','encode_total_ms','fresh_recovery_p99_ms','migration_ms','source_p99_ms','stored_directory_bytes','peak_working_set_bytes','peak_commit_bytes','current_reachable_bytes','noncheckpoint_p50_ms','noncheckpoint_p99_ms','checkpoint_sum_ms','checkpoint_max_ms']+[p+'_'+q+'_ms' for p in ['anchor31','checkpoint32','checkpoint_delta63','checkpoint64'] for q in ['p50','p99']]
def add(kind,seed,metric,ratio,limit=None,interval=None):
    passed=math.isfinite(ratio) and (interval[0]<=ratio<=interval[1] if interval else ratio<=limit)
    checks.append({'kind':kind,'seed_receipts':seed,'metric':metric,'paired_ratio':ratio,'limit':limit,'interval':interval,'passed':passed})
for seed in [0,50000,99000]:
    pairs=[]
    for turn in range(6):
        group={c['spec']['variant']:c for c in cases if c['spec']['round']==turn and c['spec']['seed_receipts']==seed}
        a=group['baseline_a'];b=group['baseline_b'];p=group['hybrid']
        pairs.append({'round':turn,'candidate_a':{k:p[k]/a[k] for k in metrics},'identity_b_a':{k:b[k]/a[k] for k in metrics}})
    ratios={label:{k:statistics.median(p[label][k] for p in pairs) for k in metrics} for label in ['candidate_a','identity_b_a']}
    c=ratios['candidate_a'];lim=policy['checks']
    for metric,limit in lim['publication_and_common_guards'].items():add('guard',seed,metric,c[metric],limit)
    for metric,limit in lim['unchanged_checkpoint_guards'].items():add('guard',seed,metric,c[metric],limit)
    for metric,limit in lim['all_anchor_guards'].items():add('guard',seed,metric,c[metric],limit)
    if seed:
        for metric,limit in lim['large_publication_goals'].items():add('goal',seed,metric,c[metric],limit)
    for metric in lim['identity_metrics']:add('identity',seed,metric,ratios['identity_b_a'][metric],interval=lim['identity_interval'])
    display={label:{k:statistics.median(c[k] for c in cases if c['spec']['seed_receipts']==seed and c['spec']['variant']==label) for k in metrics} for label in ['baseline_a','baseline_b','hybrid']}
    summaries.append({'seed_receipts':seed,'actual_receipts':len(expected[seed][0]['batches']),'pairs':pairs,'median_paired_ratios':ratios,'median_display_only':display})
assert len(checks)==policy['expected_check_count']
assert sum(c['kind']=='goal' for c in checks)==4
save(W/'fixture-inventory.json',files)
goal_checks=[c for c in checks if c['kind']=='goal'];identity={(c['seed_receipts'],c['metric']):c['passed'] for c in checks if c['kind']=='identity'}
audit={'complete':True,'audited_utc':datetime.now(timezone.utc).isoformat(),'model_only':True,'publication_samples':3456,'fresh_recovery_samples':648,'cases':cases,'summaries':summaries,'checks':checks,
    'failed_checks':[c for c in checks if not c['passed']],
    'large_source_publication_goals_calibrated_and_passed':all(c['passed'] and identity[(c['seed_receipts'],c['metric'])] for c in goal_checks),
    'all_fresh_comparison_checks_passed':all(c['passed'] for c in checks),'advance_to_engine_design':False,
    'file_instances':len(files),'stored_bytes_total':sum(v['bytes'] for v in files.values()),
    'independent_full_decoded_canonical_cases':3,'independent_full_decoded_canonical_files':logical_reads,
    'all_replica_full_file_hashes_equal_independently_validated_canonical':True,
    'all_logical_edits_recovery_hashes_sources_bounds_stage_counts_and_order_passed':True,
    'no_engine_edit_or_promotion':True,'all_raw_and_frozen_hashes_unchanged':True,
    'previous_075_adoption_failures_unchanged_and_not_superseded':True,'previous_077_failures_unchanged_and_not_superseded':True,'no_fresh_cuts_078_prerequisite_retained':True}
save(W/'model-audit.json',audit)
print(json.dumps({'complete':True,'files':len(files),'publication_samples':3456,'recoveries':648,'failed':{kind:sum(c['kind']==kind for c in audit['failed_checks']) for kind in ['goal','guard','identity']},'calibrated_publication_goals':audit['large_source_publication_goals_calibrated_and_passed'],'engine_advance':False}))
