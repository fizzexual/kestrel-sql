"""Independent raw cohort, metadata, full block CRC and NumPy data reference replay. No native calls."""
from pathlib import Path
import hashlib,json,math,statistics,struct,zlib
import numpy as np
W=Path('D:/Codex/Kestrel/work/perf-092')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def q(v,p):return sorted(v)[max(0,math.ceil(len(v)*p)-1)]
def dist(v):return {n:q(v,p) for n,p in [('p50',.5),('p95',.95),('p99',.99)]}|{'max':max(v),'count':len(v)}
def envelope(p,magic):
    b=p.read_bytes();assert b[:8]==magic
    length,crc=struct.unpack_from('<II',b,8);raw=b[16:16+length]
    assert len(raw)==length and zlib.crc32(raw)==crc
    return json.loads(raw),b[16+length:]
def store(path,named):
    cats={int(p.name[8:28]):p for p in path.glob('catalog-*.ks2')}
    assert cats; gen=max(cats); head=None;seen=[];receipts={}
    while gen is not None:
        assert gen not in seen and len(seen)<32; seen.append(gen)
        c,tail=envelope(cats[gen],b'KSQLCAT4');assert not tail and c['generation']==gen
        assert c['table']=='events' and c['columns']==['ts','value']
        if head is None:head=c
        for k,v in c['batches'].items():assert k not in receipts;receipts[k]=v
        gen=c['receipt_base']
    assert len(receipts)==(288 if named else 0)
    if named:assert set(receipts)=={f'group:{i}' for i in range(1,289)}
    parts=[];crc_bytes=0
    for name in head['segments']:
        m,payload=envelope(path/name,b'KSQLSEG2');rows=m['rows'];assert len(payload)==rows*16
        cols=np.frombuffer(payload,dtype='<i8').reshape((2,rows))
        for column,index in zip(cols,m['indexes']):
            prefix=0;assert index['prefix'][0]==0
            assert int(column.min())==index['min'] and int(column.max())==index['max']
            for j,lo in enumerate(range(0,rows,4096)):
                block=column[lo:lo+4096];raw=block.tobytes();crc_bytes+=len(raw)
                assert zlib.crc32(raw)==index['crc'][j]
                prefix+=sum(map(int,block));assert prefix==index['prefix'][j+1]
                assert int(block[-1])==index['last'][j]
                assert int(block.min())==index['block_min'][j] and int(block.max())==index['block_max'][j]
        parts.append(cols)
    data=np.concatenate(parts,axis=1);order=np.argsort(data[0],kind='stable');data=data[:,order]
    expected=np.arange(61568,dtype=np.int64)
    assert np.array_equal(data[0],expected) and np.array_equal(data[1],expected*2)
    return {'rows':61568,'data_crc_bytes':crc_bytes,'chain':seen,'receipts':len(receipts),'segments':len(parts),'files':len(list(path.iterdir())),'disk_bytes':sum(p.stat().st_size for p in path.iterdir())}
def main():
    policy=load(W/'policy.json');report=load(W/'paired-reclaim.json');freeze=load(W/'timing-freeze.json')
    assert report['complete'] and not report['failed_cases'] and not report['unstarted_cases']
    assert report['policy_sha256']==sha(W/'policy.json') and report['freeze_sha256']==sha(W/'timing-freeze.json')
    assert all(sha(W/n)==h for n,h in freeze['sha256'].items())
    assert [{k:c[k] for k in ['round','block','mode','variant']} for c in report['cases']]==policy['cases']
    cases=[];phases=[];stalls=[];stores=[]
    for case in report['cases']:
        x=load(W/case['raw']); assert x['rows']==61568 and x['sum']==61568*61567 and x['verified_bytes']==61568*16
        assert x['same_process_lock_and_snapshot_retention_passed'] and x['cold_reopen_passed']
        assert x['named']==(case['mode']=='named') and x['profiled']==(case['variant']=='profiled')
        assert bool(x['retry'])==x['named'];assert not x['named'] or x['retry']['duplicate']
        assert [r['group'] for r in x['records']]==list(range(32,289,32))
        for r in x['records']:
            before=set(r['before_files']);after=set(r['after_files']);deleted=set(r['deleted'])
            assert len(before)==len(r['before_files']) and after<=before and deleted==before-after
            assert r['removed']==len(deleted) and r['outer_ns']>0
            assert r['pinned']==(64<=r['group']<=160)
            assert f"catalog-{r['generation']:020d}.ks2" in after
            if r['phase'] is not None:
                p=r['phase'];assert case['variant']=='profiled' and p['removed']==r['removed']
                assert p['catalog_deletes']==sum(n.startswith('catalog-') for n in deleted)
                assert p['retired_deletes']==sum(n.startswith('segment-') for n in deleted)
                times=['enumerate_ns','inspect_ns','catalog_delete_ns','retired_inspect_ns','retired_delete_ns']
                assert all(p[k]>=0 for k in times) and sum(p[k] for k in times)<=p['outer_ns']<=r['outer_ns']
                phases.append({'case_index':case['case_index'],'mode':case['mode'],'group':r['group'],**p})
            else:assert case['variant']!='profiled'
            if r['outer_ns']>100_000_000:stalls.append({'case_index':case['case_index'],**r})
        values=[r['outer_ns'] for r in x['records']]
        cases.append({k:case[k] for k in ['case_index','round','block','mode','variant']}|{'sum_reclaim_ns':sum(values),'case_reclaim_p99_ns':q(values,.99)})
        stores.append({'case_index':case['case_index'],**store((W/case['raw']).parent/'archive',x['named'])})
    scopes=[]
    for mode in ['anonymous','named']:
        for name,rounds in [('full',list(range(12))),('block_0',list(range(6))),('block_1',list(range(6,12)))]:
            checks=[]
            for metric in policy['metrics']:
                aa=[];ca=[]
                for rnd in rounds:
                    pair={c['variant']:c[metric] for c in cases if c['round']==rnd and c['mode']==mode}
                    aa.append(pair['baseline_b']/pair['baseline_a']);ca.append(pair['profiled']/pair['baseline_a'])
                a=statistics.median(aa);c=statistics.median(ca)
                checks.append({'metric':metric,'AA_paired_median':a,'CA_paired_median':c,
                    'AA_passed':policy['identity_range'][0]<=a<=policy['identity_range'][1],
                    'profile_passed':c<=policy['profiled_max_ratio'],'AA_all_ratios':aa,'CA_all_ratios':ca})
            scopes.append({'mode':mode,'scope':name,'checks':checks,'passed':all(c['AA_passed'] and c['profile_passed'] for c in checks)})
    phase_dist={mode:{k:dist([p[k] for p in phases if p['mode']==mode]) for k in ['outer_ns','enumerate_ns','inspect_ns','catalog_delete_ns','retired_inspect_ns','retired_delete_ns']} for mode in ['anonymous','named']}
    shares={mode:{k:sum(p[k] for p in phases if p['mode']==mode)/sum(p['outer_ns'] for p in phases if p['mode']==mode) for k in ['enumerate_ns','inspect_ns','catalog_delete_ns','retired_inspect_ns','retired_delete_ns']} for mode in ['anonymous','named']}
    result={'trial':92,'correctness_passed':True,'cases':len(cases),'reclaim_windows':len(cases)*9,'profile_windows':len(phases),
        'scopes':scopes,'all_required_scopes_passed':all(s['passed'] for s in scopes),'cases_metrics':cases,
        'stores':stores,'full_data_crc_bytes':sum(s['data_crc_bytes'] for s in stores),'phase_distributions_ns':phase_dist,
        'phase_total_shares':shares,'events_over_100ms':stalls,'profiled_counts':phases,'supported':'0.3.16',
        'native_reclaim_warm_directory_only':True,'no_service_latency_or_exclusive_physical_cause_claim':True}
    serialized=json.dumps(result,indent=2)+'\n';target=W/'audit.json'
    if target.exists():assert target.read_text(encoding='utf-8')==serialized
    else:target.write_text(serialized,encoding='utf-8',newline='\n')
    print(json.dumps({k:result[k] for k in ['cases','reclaim_windows','profile_windows','all_required_scopes_passed','full_data_crc_bytes','phase_total_shares']}),flush=True)
    return result
if __name__=='__main__':main()
