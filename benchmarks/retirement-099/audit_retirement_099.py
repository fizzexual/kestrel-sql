"""Complete pure raw/reference/control replay. No Native launches, timers or existing-file writes."""
from pathlib import Path
import collections,hashlib,importlib.util,itertools,json,math,re,statistics,sys
sys.dont_write_bytecode=True

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def q(values,p):return sorted(values)[max(0,math.ceil(len(values)*p)-1)]
def lines(p):return [json.loads(s) for s in p.read_bytes().splitlines() if s.strip()]
def files(p):return {f.name:f.stat().st_size for f in p.iterdir() if f.is_file()}

def validate_raw(spec,x):
    assert x['trial']==99 and x['variant']==spec['variant'] and x['named']==(spec['history']=='named')
    assert x['rows']==58368 and x['sum']==58368*58367 and x['generation']==261 and x['verified_bytes']==58368*24
    assert x['cold_reopen_passed'] and x['worker_actually_joined_and_pending_empty']
    assert x['manager_lease_after_join_until_drop_verified'] and x['pin_after_owner_drop_verified']
    assert (x['worker_selected'],x['worker_deleted'],x['worker_failures'])==(128,128,0)
    assert bool(x['retry'])==x['named']
    if x['named']:assert x['retry']['duplicate'] and x['retry']['rows']==100 and x['retry']['generation']==18
    assert len(x['append_records'])==256 and [a['group'] for a in x['append_records']]==list(range(1,257))
    for a in x['append_records']:
        assert type(a['append_ns']) is int and a['append_ns']>0 and a['rows']==100 and not a['duplicate']
        assert a['generation']==a['group']+1+(a['group']-1)//64
    assert len(x['records'])==8
    assert [(r['cycle'],r['count']) for r in x['records']]==[(cycle,n) for cycle in range(1,5) for n in [20,12]]
    for i,r in enumerate(x['records']):
        count=r['count'];cycle=r['cycle'];s=r['state']
        assert r['group']==64*cycle and r['condition']==('cached' if cycle%2==0 else 'cold')
        assert r['selected']==r['removed']==count and type(r['outer_ns']) is int and r['outer_ns']>0
        assert r['step_ns_diagnostic']>=0 and r['settle_wait_ns_diagnostic']>=0
        assert s['pending_batches']==1 and s['pending_arc_counts']==[1]
        assert s['retired_items']==s['unique_final_segment_refs']==count and s['failures']==0
        assert s['selected']==s['deleted']==sum([20,12]*(cycle-1))+ (20 if count==20 else 32)
        assert s['idle_streams']==(count if cycle%2==0 else 0)
        assert len(s['names'])==len(set(s['names']))==count and all(re.fullmatch(r'segment-\d{20}\.ks2',n) for n in s['names'])
        before=r['before_step'];mid=r['before_poll'];after=r['after_poll']
        assert set(after)<=set(mid)<=set(before) and all(after[n]==before[n] for n in after)
        assert set(before)-set(after)==set(r['deleted'])==set(s['names']) and r['deleted']==sorted(r['deleted'])
        assert f"catalog-{r['generation']:020d}.ks2" in after and r['generation']==1+cycle*65
        assert r['catalog_cleanup_outside_clock']>0
        for n,value in [('catalog-00000000000000000998.pending',b'untouched pending099'),('segment-00000000000000000999.ks2',b'untouched orphan099')]:
            assert n in after and after[n]==len(value)
        if spec['variant']=='profiled':assert type(r['inner_ns']) is int and 0<r['inner_ns']<=r['outer_ns']
        else:assert r['inner_ns'] is None
    v=[r['outer_ns'] for r in x['records']];cold=[r['outer_ns'] for r in x['records'] if r['condition']=='cold'];warm=[r['outer_ns'] for r in x['records'] if r['condition']=='cached']
    av=[r['append_ns'] for r in x['append_records']]
    return {'sum_poll_ns':sum(v),'case_poll_p99_ns':q(v,.99),'cold_sum_poll_ns':sum(cold),'cold_poll_p99_ns':q(cold,.99),
        'cached_sum_poll_ns':sum(warm),'cached_poll_p99_ns':q(warm,.99),'sum_append_ns':sum(av),'case_append_p99_ns':q(av,.99),
        'case_append_p50_ns':q(av,.5),'profile_inner_p99_ns':q([r['inner_ns'] for r in x['records']],.99) if spec['variant']=='profiled' else None}

def validate_order(policy,cases):
    assert len(cases)==144 and cases==policy['cases']
    perms=set(itertools.permutations(['baseline_a','baseline_b','profiled']))
    for half in range(2):
        for history in ['anonymous','named']:
            sequences=[]
            for rnd in range(half*12,(half+1)*12):
                row=[s for s in cases if s['round']==rnd and s['history']==history]
                assert [s['slot'] for s in row]==[0,1,2] and all(s['half']==half for s in row)
                sequences.append(tuple(s['variant'] for s in row))
            counts=collections.Counter(sequences);assert set(counts)==perms and set(counts.values())=={2}

def dependency(w,name):
    spec=importlib.util.spec_from_file_location(name,w/(name+'.py'));module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    assert Path(module.__file__).resolve().is_relative_to(w.resolve());return module

def audit_units(w,archive):
    fresh=[];workers=[]
    for p in sorted((w/'cargo-tests-v2').glob('retirement099-*')):
        m=re.fullmatch(r'retirement099-(warm|cold|settle-lease)-(\d+)-(\d+)',p.name);assert m
        for directory in ([p] if m[1]=='settle-lease' else [p/'original',p/'profile']):
            fresh.append({'directory':directory.relative_to(w).as_posix(),'decode':archive.check(directory,[[i,2*i,i%7] for i in range(32)],{})})
    assert len(fresh)==10
    for p in sorted((w/'cargo-tests-v2').glob('async-096-*')):
        m=re.fullmatch(r'async-096-(.+)-(\d+)-(\d+)',p.name);assert m;label=m[1]
        for directory in ([p/'full',p/'worker'] if label=='equivalence' else [p]):
            n=65 if label in ['bound','progress'] else 2 if label=='filesystem' else 66 if label=='source' else 64
            rows=[[i,2*i] for i in range(64)]+[[100,9],[-1,11]] if label=='source' else [[i,2*i] for i in range(n)]
            _,_,_,existing=archive.metadata(directory);receipts={}
            if label in ['equivalence','source'] and (label=='source' or existing):
                receipts={f'id:{i}':([[i,2*i]],i+1) for i in range(64)}
                if label=='source':key=hashlib.sha256(b'kestrelsql.source.v1\0orders').hexdigest();receipts[f'ksrc1:{key}:{100:016x}:{200:016x}']=([[100,9],[-1,11]],66)
            workers.append({'directory':directory.relative_to(w).as_posix(),'label':label,'decode':archive.check(directory,rows,receipts)})
    assert len(workers)==38
    return {'new_wrapper_stores':fresh,'worker_stores':workers,'full_crc_bytes':sum(u['decode']['full_block_crc_bytes'] for u in fresh+workers)}

def audit(w):
    assert sha(w/'policy.json')=='1853ca1638e9227517f67ff5ce32bd0a18165bb84769505637b530522744170c'
    policy=load(w/'policy.json');report=load(w/'paired-retirement.json');freeze=load(w/'timing-freeze.json')
    assert report['complete'] and not report['failed_cases'] and not report['unstarted_cases']
    assert report['policy_sha256']==sha(w/'policy.json') and report['freeze_sha256']==sha(w/'timing-freeze.json')
    assert all(sha(w/n)==h for n,h in freeze['sha256'].items())
    specs=[{k:r[k] for k in ['half','round','history','slot','variant']} for r in report['cases']];validate_order(policy,specs)
    archive=dependency(w,'archive_audit_099')
    build=load(w/'build-proof.json');assert build['complete'] and build['strict_lint_modes']==4 and build['fresh_native_test_executions']==184
    assert {p.relative_to(w/'source').as_posix():sha(p) for p in (w/'source').rglob('*') if p.is_file()}==load(w/'source-derivation.json')['final']
    failure=load(w/'first-build-failure-preservation.json');f=w/'failed-build-v1'
    assert all(sha(f/n)==h for n,h in failure['all_first_files'].items())
    assert {p.relative_to(f).as_posix() for p in f.rglob('*') if p.is_file()}==set(failure['all_first_files'])
    assert failure['compiled_executable_copies']==36 and failure['no_native_test_executions_or_external_probe_or_benchmark_started']
    units=audit_units(w,archive);cases=[];stores=[];stalls=[];raws={}
    reference=[[i,2*i,i%97] for i in range(58368)]
    for index,(spec,record) in enumerate(zip(specs,report['cases'])):
        assert record['case_index']==index and record['exit_code']==0 and not record.get('timeout')
        x=load(w/record['raw']);metrics=validate_raw(spec,x);d=(w/record['raw']).parent
        assert load(d/'status.json')==record and record['owned_process_identity']['pid']>0 and record['owned_process_identity']['creation_filetime']>0
        journal=lines(d/'native-journal.jsonl');assert journal==[{'append':r} for r in x['append_records'][:64]] + [{'poll':r} for r in x['records'][:2]] + [
            entry for start,ri in [(64,2),(128,4),(192,6)] for entry in ([{'append':r} for r in x['append_records'][start:start+64]]+[{'poll':r} for r in x['records'][ri:ri+2]])] + [{'complete':x}]
        assert files(d/'archive')==x['final_files']
        receipts={f'group:{r["group"]}':(reference[32768+(r['group']-1)*100:32768+r['group']*100],r['generation']) for r in x['append_records']} if x['named'] else {}
        decoded=archive.check(d/'archive',reference,receipts);assert decoded['head']==261 and decoded['rows']==58368
        for n,v in [('catalog-00000000000000000998.pending',b'untouched pending099'),('segment-00000000000000000999.ks2',b'untouched orphan099')]:assert (d/'archive'/n).read_bytes()==v
        stores.append({'case_index':index,'decode':decoded});cases.append({'case_index':index,**spec,**metrics});raws[index]=x
        for stage,items,key in [('poll',x['records'],'outer_ns'),('append',x['append_records'],'append_ns')]:
            stalls.extend({'case_index':index,'stage':stage,'group':r['group'],'ns':r[key]} for r in items if r[key]>100_000_000)
    for history in ['anonymous','named']:
        for rnd in range(24):
            trio=[c for c in cases if c['history']==history and c['round']==rnd]
            data=[{p.name:sha(p) for p in ((w/report['cases'][c['case_index']]['raw']).parent/'archive').iterdir() if p.is_file() and p.name!='archive.lockfile'} for c in trio]
            assert data[0]==data[1]==data[2]
    scopes=[];costs=[]
    for history in ['anonymous','named']:
        for name,rounds in [('full',list(range(24))),('half_0',list(range(12))),('half_1',list(range(12,24)))]:
            checks=[]
            for metric in policy['metrics']:
                aa=[];ca=[];cb=[]
                for rnd in rounds:
                    pair={c['variant']:c[metric] for c in cases if c['round']==rnd and c['history']==history}
                    aa.append(pair['baseline_b']/pair['baseline_a']);ca.append(pair['profiled']/pair['baseline_a']);cb.append(pair['profiled']/pair['baseline_b'])
                a=statistics.median(aa);c=statistics.median(ca)
                checks.append({'metric':metric,'AA_paired_median':a,'CA_paired_median':c,'CB_paired_median_diagnostic':statistics.median(cb),
                    'AA_passed':.90<=a<=1.10,'profile_passed':c<=1.10,'AA_all_ratios':aa,'CA_all_ratios':ca,'CB_all_ratios_diagnostic':cb})
            passed=all(c['AA_passed'] and c['profile_passed'] for c in checks);scopes.append({'history':history,'scope':name,'checks':checks,'passed':passed})
            selected=[c for c in cases if c['history']==history and c['round'] in rounds and c['variant']=='profiled']
            poll=statistics.median(c['profile_inner_p99_ns'] for c in selected);append=statistics.median(c['case_append_p50_ns'] for c in selected)
            costs.append({'history':history,'scope':name,'median_case_inner_poll_p99_ns':poll,'median_case_append_p50_ns':append,
                'poll_p99_over_append_p50':poll/append,'absolute_100us_passed':poll>=100000,'relative_5percent_passed':poll/append>=.05,
                'matching_scope_calibrated':passed,'material_cost_numeric_passed':poll>=100000 and poll/append>=.05})
    oracle=load(w/'oracle-proof.json');assert oracle['complete'] and oracle['probe_smokes']==4 and oracle['CLI_SQLite_queries']==16
    oracle_commands=load(w/'oracle-run-order.json');assert len(oracle_commands)==20
    for r in oracle_commands:
        assert r['exit_code']==0 and all(sha(w/r[k])==r[k+'_sha256'] for k in ['stdout','stderr'])
    by_label={r['label']:r for r in oracle_commands};assert len(by_label)==20 and len(oracle['comparisons'])==16
    expected_grouped=[[kind,sum(i%97==kind for i in range(58368)),sum(2*i for i in range(58368) if i%97==kind)] for kind in range(97)]
    for c in oracle['comparisons']:
        assert c['sql'] in ['SELECT COUNT(*), SUM(value) FROM events','SELECT kind, COUNT(*), SUM(value) FROM events GROUP BY kind ORDER BY kind']
        expected=[[58368,58368*58367]] if 'GROUP BY' not in c['sql'] else expected_grouped
        assert c['expected']==expected
        x=load(w/by_label[c['label']]['stdout']);assert x['ok'] and x['result']['rows']==expected
    smokes=[]
    for s in oracle['smokes']:
        x=load(w/s['raw']);validate_raw(s,x)
        expected={f'group:{r["group"]}':(reference[32768+(r['group']-1)*100:32768+r['group']*100],r['generation']) for r in x['append_records']} if x['named'] else {}
        smokes.append({'raw':s['raw'],'decode':archive.check(w/s['fixture'],reference,expected)})
    failedAA=sum(not c['AA_passed'] for s in scopes for c in s['checks']);failedC=sum(not c['profile_passed'] for s in scopes for c in s['checks'])
    calibrated=all(s['passed'] for s in scopes)
    return {'trial':99,'correctness_passed':True,'cases':144,'poll_windows':1152,'profiled_inner_windows':384,'append_publications':36864,
        'identity_failed':failedAA,'profile_guards_failed':failedC,'profile_controls_qualified':calibrated,'scopes':scopes,
        'cost_criteria':costs,'material_writer_retirement_hypothesis_supported':calibrated and all(c['material_cost_numeric_passed'] for c in costs),
        'case_metrics':cases,'stores':stores,'full_case_crc_bytes':sum(s['decode']['full_block_crc_bytes'] for s in stores),
        'unit_reference_checks':units,'smoke_reference_checks':smokes,'events_over_100ms':stalls,
        'all_raw_failures_preserved':True,'old_fault_matrices_reused_not_fresh':True,'supported':'0.3.16',
        'no_service_p99_pure_close_exclusive_cause_or_adoption_claim':True,'native_launches':0,'performance_timer_launches':0}

if __name__=='__main__':
    w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-099');result=audit(w);p=w/'audit.json'
    encoded=json.dumps(result,indent=2)+'\n'
    if p.exists():assert p.read_text(encoding='utf-8')==encoded
    else:p.write_text(encoded,encoding='utf-8',newline='\n')
    print(json.dumps({k:result[k] for k in ['cases','poll_windows','identity_failed','profile_guards_failed','profile_controls_qualified','material_writer_retirement_hypothesis_supported','full_case_crc_bytes']}))
