from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,queue,shutil,subprocess,sys,threading,time
W=Path(__file__).resolve().parent
sys.path.insert(0,str(W))
import page_oracle as oracle
from catalog_oracle import ledger_sha
from order_plan import plan,validate
from process_cpu_083 import snapshot,difference
from process_memory import peak_memory
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def block_validate(cases):
    from collections import Counter
    records=[]
    for low in [0,6]:
        part=[c for c in cases if low<=c['round']<low+6]
        assert len(part)==54
        for size in [0,50000,99000]:
            orders=[];slots={v:Counter() for v in ['baseline_a','baseline_b','bulk']};ab=Counter();size_slots=Counter()
            for r in range(low,low+6):
                group=[c for c in part if c['round']==r];sizes=[group[i]['seed_receipts'] for i in [0,3,6]]
                size_slots[sizes.index(size)]+=1
                block=[c['variant'] for c in group if c['seed_receipts']==size];orders.append(tuple(block))
                for i,v in enumerate(block):slots[v][i]+=1
                ab['a_before_b' if block.index('baseline_a')<block.index('baseline_b') else 'b_before_a']+=1
            assert len(set(orders))==6 and size_slots=={0:2,1:2,2:2}
            assert ab=={'a_before_b':3,'b_before_a':3} and all(x=={0:2,1:2,2:2} for x in slots.values())
        records.append({'start_round':low,'cases':54,'all_six_orders_each_size':True,'every_slot_twice':True,'ab_orders_each_direction':3})
    return {'complete':True,'blocks':records}
def execute(binary,input_path,stem):
    policy=load(W/'policy.json');lines=[];phases=[];done=None;start_time=time.perf_counter()
    with (W/'raw'/f'{stem}.stderr.txt').open('w',encoding='utf-8') as err:
        p=subprocess.Popen([str(binary),'profile083',str(input_path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,encoding='utf-8',bufsize=1)
        q=queue.Queue()
        def reader():
            for line in p.stdout:q.put(line)
            q.put(None)
        thread=threading.Thread(target=reader,daemon=True);thread.start()
        before=None;begin=None
        try:
            while True:
                line=q.get(timeout=policy['timeout_per_phase_seconds'])
                if line is None:break
                lines.append(line);x=json.loads(line)
                if x['event']=='begin':
                    assert begin is None
                    begin=x;before=snapshot(p);p.stdin.write('go\n');p.stdin.flush()
                elif x['event']=='end':
                    after=snapshot(p);assert begin and x['stage']==begin['stage'] and x['iterations']==begin['iterations']
                    cpu=difference(before,after);phases.append({**x,**cpu,'cpu_per_iteration_ms':cpu['cpu_ms']/x['iterations'],'eligible_cpu_window':cpu['cpu_ms']>=policy['minimum_cpu_window_ms']})
                    begin=None;p.stdin.write('go\n');p.stdin.flush()
                elif x['event']=='done':assert done is None;done=x
                else:raise AssertionError(x)
            code=p.wait(timeout=20);cpu_final=snapshot(p);memory=peak_memory(p)
            assert code==0 and done and begin is None and memory['success'],(code,stem)
            assert [x['stage'] for x in phases]==policy['phase_order']
            large=done['summary']['receipts']>1024;expected=policy['iterations_large' if large else 'iterations_small']
            assert all(x['iterations']==expected[x['stage']] for x in phases)
            result={'complete':True,'pid':p.pid,'binary':str(binary),'input':str(input_path),'phases':phases,'done':done,'exit_code':code,'full_process_cpu_ms':(cpu_final['kernel_ticks']+cpu_final['user_ticks'])/10000,'memory':memory,'observer_wall_seconds':time.perf_counter()-start_time}
        except Exception as e:
            if p.poll() is None:p.kill()
            p.wait();result={'complete':False,'pid':p.pid,'error':repr(e),'owned_child_waited':True,'phases':phases}
            save(W/'raw'/f'{stem}.status.json',result)
            (W/'raw'/f'{stem}.stdout.jsonl').write_text(''.join(lines),encoding='utf-8',newline='\n')
            raise
    save(W/'raw'/f'{stem}.status.json',result)
    (W/'raw'/f'{stem}.stdout.jsonl').write_text(''.join(lines),encoding='utf-8',newline='\n')
    return result
def initialize():
    assert not (W/'cohort-policy.json').exists();build=load(W/'build-proof.json');assert build['complete']
    cases=plan();balance=validate(cases);blocks=block_validate(cases)
    expected={}
    for size in [0,50000,99000]:
        path=W/f'inputs/{size}.ks2';old=oracle.legacy(path);body=oracle.envelope(path,b'KSQLCAT4',64*1024*1024)
        expected[str(size)]={'summary':{'generation':old['generation'],'receipts':len(old['batches']),'ledger_sha256':ledger_sha(old['batches']),'positions':oracle.positions(old['batches'])},'body_bytes':len(body),'body_sha256':hashlib.sha256(body).hexdigest(),'file_sha256':sha(path)}
    save(W/'independent-input-proof.json',{'complete':True,'inputs':expected})
    (W/'raw').mkdir()
    # Untimed observer/small-input integration checks, kept out of cohort statistics.
    smoke=[]
    for variant in ['baseline_a','baseline_b','bulk']:
        label='bulk' if variant=='bulk' else 'control';x=execute(W/f'bin/{label}.exe',W/'inputs/0.ks2','smoke-'+variant)
        assert x['done']['summary']==expected['0']['summary'];smoke.append({'variant':variant,'complete':True})
    save(W/'smoke-proof.json',{'complete':True,'cases':smoke,'not_benchmark_controls':True})
    names=['policy.json','source-derivation.json','setup-attempt1.py','setup-attempt1-failure.json','setup-resumption-proof.json','build-proof.json','environment.json','run_profile_083.py','process_cpu_083.py','process_memory.py','order_plan.py','page_oracle.py','catalog_oracle.py','independent-input-proof.json','smoke-proof.json','method-notes.json']
    names += [p.relative_to(W).as_posix() for directory in ['control-model','bulk-model','inputs','bin'] for p in (W/directory).rglob('*') if p.is_file()]
    save(W/'cohort-policy.json',{'complete':True,'declared_utc':now(),'before_first_cohort_timer':True,'cases':cases,'balance':balance,'block_balance':blocks,'frozen_sha256':{n:sha(W/n) for n in names}})
    print(json.dumps({'initialized':True,'cases':108,'both_blocks_balanced':True,'independent_input_and_smoke_passed':True}),flush=True)
def run():
    assert not (W/'profile-results.json').exists();cohort=load(W/'cohort-policy.json');assert cohort['complete']
    for n,d in cohort['frozen_sha256'].items():assert sha(W/n)==d,n
    assert not load(W/'pre-timing-process-check.json')['active_processes']
    expected=load(W/'independent-input-proof.json')['inputs'];policy=load(W/'policy.json')
    result={'complete':False,'started_utc':now(),'cases':[],'failures':[]};save(W/'profile-results.json',result)
    for i,c in enumerate(cohort['cases']):
        assert shutil.disk_usage(W).free>=policy['minimum_free_bytes']
        stem=f"{i:03}-r{c['round']}-{c['seed_receipts']}-{c['variant']}";label='bulk' if c['variant']=='bulk' else 'control'
        try:
            x=execute(W/f'bin/{label}.exe',W/f"inputs/{c['seed_receipts']}.ks2",stem)
            golden=expected[str(c['seed_receipts'])]
            assert x['done']['summary']==golden['summary'] and x['done']['body_bytes']==golden['body_bytes'] and x['done']['input_body_sha256']==golden['body_sha256']
            result['cases'].append({'label':stem,'spec':c});save(W/'profile-results.json',result)
            print(json.dumps({'completed':i+1,'total':108,'label':stem,'phase_ms':{p['stage']:round(p['per_iteration_ms'],4) for p in x['phases']}}),flush=True)
        except Exception as e:
            result['failures'].append({'label':stem,'error':repr(e),'no_observed_case_rerun':True});save(W/'profile-results.json',result);raise
    for n,d in cohort['frozen_sha256'].items():assert sha(W/n)==d,n
    result.update(complete=True,completed_utc=now());save(W/'profile-results.json',result)
    print(json.dumps({'complete':True,'cases':108,'every_semantic_result_equal':True,'all_frozen_files_unchanged':True}),flush=True)
if __name__=='__main__':
    if sys.argv[1:]==['--initialize']:initialize()
    else:assert not sys.argv[1:];run()
