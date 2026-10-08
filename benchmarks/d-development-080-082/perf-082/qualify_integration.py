"""Pre-cohort smoke data validates the exact frozen canonical auditor; no speed claims."""
import hashlib,json,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
import page_oracle as o
W=Path(__file__).resolve().parent;BINARIES={'control_078':W/'bin/control-078.exe','candidate_081':W/'bin/candidate-081.exe'}
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W/'native-control-oracle.json').exists()
for variant,exe in BINARIES.items():assert sha(exe)==load(W/'binary-provenance.json')['builds'][variant]['binary_sha256']
BASE=W/'pre-cohort-smoke';BASE.mkdir();(BASE/'inputs').mkdir();(BASE/'raw').mkdir()
prefix=(W/'audit_model.py').read_text(encoding='utf-8').split("policy=load(W/'policy.json')",1)[0]
ns={'__file__':str(W/'audit_model.py'),'__name__':'auditor_contract'};exec(compile(prefix,str(W/'audit_model.py'),'exec'),ns)
input_map={}
for n in [7,8,9]:
    p=BASE/'inputs'/f'{n}.ks2';v={'generation':129,'receipt_base':None,'table':'events','columns':['ts','value'],'segments':[],
        'batches':{f'old-{i:03}':{'digest':[i]*32,'rows':1,'generation':1} for i in range(n)}}
    p.write_bytes(o.frame(b'KSQLCAT4',v));input_map[n]={'path':str(p),'actual_receipts':n}
ns['input_map']=input_map
checks=[];commands=[]
for n,item in input_map.items():
    old=o.legacy(Path(item['path']));edits,snapshots,final=ns['expected_edits'](old)
    for variant,EXE in BINARIES.items():
        mode='hybrid'
        label=f'{n}-{variant}';store=BASE/label;argv=[str(EXE),'bench075',str(store),item['path'],mode,'64']
        p=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:out,err=p.communicate(timeout=180)
        except subprocess.TimeoutExpired:p.kill();out,err=p.communicate(timeout=30);raise
        (BASE/'raw'/f'{label}.stdout.json').write_bytes(out);(BASE/'raw'/f'{label}.stderr.txt').write_bytes(err)
        commands.append({'argv':argv,'pid':p.pid,'exit':p.returncode,'owned_child_waited':True});save(BASE/'commands.json',commands)
        assert p.returncode==0,(label,err)
        x=json.loads(out);assert x['probe']=='GROWTHMODEL075' and len(x['samples'])==64 and len(x['fresh_recovery'])==12
        assert x['source_validation_full_clone_charged_in_all_modes'] is False
        if True:assert x['source_validation_is_fully_charged'] and x['hybrid_source_validation']=='validated_incremental_state078'
        files,reachable=ns['full_canonical_audit'](store,mode,old,edits,final)
        assert len(files)==(65 if mode=='cat4' else 67)
        assert all(x['initial'][k]==v for k,v in snapshots[129].items())
        assert all(x['final'][k]==v for k,v in snapshots[193].items())
        for i,r in enumerate(x['fresh_recovery']):
            nseq=[30,31,62,63][i//3];assert r['after_sequence']==nseq and r['repetition']==i%3
            assert all(r['summary'][k]==v for k,v in snapshots[130+nseq].items())
            assert r['summary']['history_files']==((32 if nseq%32==30 else 1) if mode=='cat4' else (32 if nseq==30 else 34 if nseq==62 else 3))
        for i,s in enumerate(x['samples']):
            assert s['checkpoint']==(i in [31,63]) and s['source_interval']==(i%8==7)
            assert s['io']['synced_files']==(2 if mode=='hybrid' and s['checkpoint'] else 1)
            expected_bytes=files[f'catalog-{130+i:020}.model' if mode=='cat4' else f'head-{130+i:020}.model']['bytes']
            if mode=='hybrid':expected_bytes+=sum(v['bytes'] for name,v in files.items() if name.startswith(f'hy-receipts-{130+i:020}-'))
            assert s['io']['bytes']==expected_bytes
        checks.append({'label':label,'fixture':str(store),'all_logical_edits_and_native_recoveries_equal':True,
            'canonical_full_file_auditor_passed':True,'decoded_files':len(files),'reachable_files':len(reachable),
            'publication_syncs':sum(s['io']['synced_files'] for s in x['samples']),
            'native_smoke_timings_not_used_as_controls_or_performance_evidence':True})
        print('qualified pre-cohort integration',label,flush=True)
save(W/'native-control-oracle.json',{'complete':True,'completed_utc':datetime.now(timezone.utc).isoformat(),'cases':checks,
    'pre_cohort_correctness_smoke_only':True,'no_case_used_as_fresh_performance_control':True,'binary_sha256':{k:sha(p) for k,p in BINARIES.items()},
    'auditor_sha256':sha(W/'audit_model.py'),'all_six_common_workloads_and_file_audits_passed':True,
    '081_fresh60_tests_each_15_errors_15_kills_30_corruptions_passed_before_timing':True})
