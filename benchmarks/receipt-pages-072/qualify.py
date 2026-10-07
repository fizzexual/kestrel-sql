"""Actual changing receipts, exact Python oracle, durable errors and owned kills.
No timed performance cohort or real database processes are launched.
"""
from datetime import datetime, timezone
import hashlib, json, os, queue, shutil, subprocess, threading
from pathlib import Path
import oracle
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';EXE=W/'bin/receipt-page-model.exe'
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W/'qualification.json').exists() and not (W/'fixtures').exists()
assert shutil.disk_usage(W).free>=2_500_000_000,'qualification disk guard; no timed run'
proof=load(W/'build-proof.json');assert proof['complete'] and sha(EXE)==proof['binary_sha256']
for n,d in proof['source_sha256'].items():assert sha(W/'model'/n)==d,n
(W/'raw').mkdir();(W/'fixtures').mkdir();(W/'inputs').mkdir()
commands=[];checks=[];sequence=0
def run(args,success=True):
    global sequence
    assert sha(EXE)==proof['binary_sha256']
    sequence+=1;key=f'{sequence:03}';r=subprocess.run([str(EXE),*map(str,args)],capture_output=True,text=True,timeout=180)
    (W/'raw'/f'{key}-stdout.txt').write_text(r.stdout,encoding='utf-8');(W/'raw'/f'{key}-stderr.txt').write_text(r.stderr,encoding='utf-8')
    commands.append({'number':sequence,'args':list(map(str,args)),'exit':r.returncode,'expected_success':success,'utc':now()});save(W/'commands.json',commands)
    assert (r.returncode==0)==success,(args,r.stdout,r.stderr)
    return [json.loads(line) for line in r.stdout.splitlines() if line.startswith('{')]
def audit(path,expected,label):
    native=run(['inspect',path])[-1];independent,ledger,root,refs=oracle.read_store(path)
    for k,v in independent.items():assert native[k]==v,(label,k,native[k],v)
    assert ledger==expected,label
    checks.append({'label':label,'path':str(path),'native_and_independent_full_ledger_match':True,**independent,
        'current_root_bytes':(path/f"root-{root['generation']:020}.model").stat().st_size,'referenced_page_bytes':sum((path/n).stat().st_size for n in refs)})
    save(W/'oracle-checks.json',checks);return root
inputs=[];growth=[]
for item in load(W.parent/'perf-071/input-provenance.json')['inputs']:
    original=Path(item['path']);assert sha(original)==item['sha256'];copy=W/'inputs'/original.name;shutil.copy2(original,copy)
    old=oracle.legacy(copy);count=len(old['batches']);assert count==item['actual_receipts']
    path=W/'fixtures'/f'grow-{count}';run(['import',path,copy]);expected=dict(old['batches']);audit(path,expected,f'import-{count}')
    migration={p.name:p.stat().st_size for p in path.iterdir()};before_hash={p.name:sha(p) for p in path.iterdir()};operations=[]
    # Three actual ordinary receipts followed by interleaved contiguous source receipts.
    for n in range(3):
        id=f'new-{count}-{n}';g=oracle.read_store(path)[0]['next_generation'];out=run(['commit',path,id,n+1])[0]
        assert not out['duplicate'] and out['receipt_generation']==g;expected[id]=oracle.new_record(n+1,len(old['columns']),g)
        audit(path,expected,f'ordinary-{count}-{n}');operations.append({'kind':'ordinary','id':id,'generation':g})
    for name,start,next,n in [('feed-a',10,20,10),('feed-b',100,101,20),('feed-a',20,25,11),('feed-b',101,105,21),('feed-a',25,30,12)]:
        id=oracle.source_id(name,start,next);g=oracle.read_store(path)[0]['next_generation'];out=run(['source',path,name,start,next,n])[0]
        assert not out['duplicate'] and out['receipt_generation']==g;expected[id]=oracle.new_record(n,len(old['columns']),g)
        audit(path,expected,f'source-{count}-{name}-{start}');operations.append({'kind':'source','id':id,'generation':g})
    files={p.name:sha(p) for p in path.iterdir()}
    first=operations[0];out=run(['commit',path,first['id'],1])[0];assert out=={'duplicate':True,'receipt_generation':first['generation']}
    out=run(['source',path,'feed-a',10,20,10])[0];assert out=={'duplicate':True,'receipt_generation':operations[3]['generation']}
    for args in [['commit',path,first['id'],999],['source',path,'feed-a',10,20,999],['source',path,'feed-a',31,35,1],['source',path,'feed-a',29,32,1]]:run(args,False)
    assert files=={p.name:sha(p) for p in path.iterdir()},'retries/rejections wrote files'
    prior=oracle.read_store(path)[2]['pages'];run(['metadata',path]);latest=audit(path,expected,f'metadata-{count}');assert prior==latest['pages']
    for n,d in before_hash.items():assert sha(path/n)==d,'immutable page/root changed'
    for id,r in old['batches'].items():assert expected[id]==r
    total=sum(p.stat().st_size for p in path.iterdir());added=total-sum(migration.values())
    growth.append({'original_receipts':count,'final_receipts':len(expected),'actual_new_receipts':8,'metadata_only_publications':1,
        'migration_files':len(migration),'migration_bytes':sum(migration.values()),'post_migration_new_file_bytes':added,
        'files_after_growth':len(list(path.iterdir())),'old_files_unchanged':True,'operations':operations,'all_current_pages_retained':True})
    inputs.append({**item,'path':str(copy),'original_068_path_and_hash_note':str(W.parent/'perf-071/input-origin-note.json'),'source_copy':str(original)})
save(W/'input-provenance.json',{'inputs':inputs,'all_original_bytes_unchanged':True,'copied_utc':now()});save(W/'growth.json',growth)
# A tail at 511 exercises filling/sealing and a new page after recovery.
small=W/'inputs/rollover-511.ks2';batches={f'old-{n:06}':{'digest':[n%256]*32,'rows':1,'generation':1} for n in range(511)}
small.write_bytes(oracle.frame(b'KSQLCAT4',{'generation':1,'receipt_base':None,'table':'events','columns':['ts','value'],'segments':[],'batches':batches}))
base=W/'fixtures/rollover-base';run(['import',base,small]);audit(base,batches,'rollover-base')
cutnames=['page_partial','page_written','page_synced','root_partial','root_written','root_synced','root_published'];cuts=[]
for mode in ['error','kill']:
    for cut in cutnames:
        path=W/'fixtures'/f'{mode}-{cut}';shutil.copytree(base,path)
        if mode=='error':
            out=run(['probe',path,cut,'error',70])[0];assert out['poisoned'] and out['second_commit_rejected'] and 'outcome unknown' in out['injected_error']
            event={'mode':mode,'cut':cut,'poisoned':True,'second_commit_rejected':True}
        else:
            # Only this freshly spawned task-owned child is killed, after a named cut token.
            argv=[str(EXE),'probe',str(path),cut,'hold','70'];p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            mailbox=queue.Queue();thread=threading.Thread(target=lambda:mailbox.put(p.stdout.readline()),daemon=True);thread.start()
            try:
                token=mailbox.get(timeout=60);assert token.strip()==f'CUT {cut}',token
            finally:
                if p.poll() is None:p.kill()
                stdout,stderr=p.communicate(timeout=30);thread.join(timeout=1)
            (W/'raw'/f'kill-{cut}-stdout.txt').write_text(token+stdout,encoding='utf-8');(W/'raw'/f'kill-{cut}-stderr.txt').write_text(stderr,encoding='utf-8')
            assert p.returncode!=0;event={'mode':mode,'cut':cut,'pid':p.pid,'argv':argv,'exit':p.returncode,'child_exited':True,'named_cut_observed':True}
        expected=dict(batches)
        committed=cut=='root_published'
        if committed:expected['probe-new-receipt']=oracle.new_record(70,2,2)
        root=audit(path,expected,f'{mode}-{cut}-after-interrupt');next=oracle.read_store(path)[0]['next_generation'];assert next>2
        out=run(['commit',path,'probe-new-receipt',70])[0];assert out['duplicate']==committed
        g=2 if committed else next;assert out['receipt_generation']==g;expected['probe-new-receipt']=oracle.new_record(70,2,g)
        audit(path,expected,f'{mode}-{cut}-after-retry')
        # The recovered tail is now full; a fresh actual receipt must open page two.
        g=oracle.read_store(path)[0]['next_generation'];run(['commit',path,'rollover-next',71]);expected['rollover-next']=oracle.new_record(71,2,g)
        root=audit(path,expected,f'{mode}-{cut}-after-rollover');assert len(root['pages'])==2 and root['pages'][0]['count']==512
        before={p.name:sha(p) for p in path.iterdir()};run(['commit',path,'probe-new-receipt',999],False);assert before=={p.name:sha(p) for p in path.iterdir()}
        event.update(next_generation_after_interrupt=next,committed_before_retry=committed,exact_retry_and_rollover_passed=True);cuts.append(event);save(W/'cuts.json',cuts)
for n,d in proof['source_sha256'].items():assert sha(W/'model'/n)==d
assert sha(EXE)==proof['binary_sha256'] and len(cuts)==14 and len(growth)==3 and len(checks)==73
save(W/'qualification.json',{'complete':True,'model_only':True,'timed_cohort_started':False,'performance_claim':False,'growth_stores':3,'real_checkpoint_receipts':[g['original_receipts'] for g in growth],
    'new_receipts_in_growth_stores':24,'metadata_publications':3,'injected_error_cases':7,'owned_process_kills':7,'exact_full_ledger_oracle_checks':len(checks),
    'all_error_and_kill_retry_rollover_checks_passed':True,'all_model_files_retained':True,'no_engine_edit_or_sql_crash_qualification':True,'no_power_loss_qualification':True,
    'ended_utc':now(),'binary_sha256':sha(EXE),'free_bytes':shutil.disk_usage(W).free})
print(json.dumps(load(W/'qualification.json')))
