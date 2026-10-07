from pathlib import Path
import subprocess,os,json,hashlib,datetime,sys
w=Path(__file__).parent;root=w.parents[1]/'outputs/kestrel-sql';b=w/'bin';h=w/'harness'
env={**os.environ,'PYTHONPATH':os.pathsep.join([str(h),str(root/'benchmarks'),str(w.parent/'stress-deps'),str(w.parent/'python-deps')])}
steps=[
 ('cross-candidate',[str(h/'cross_candidate.py')]),
 ('compatibility',[str(h/'compatibility.py')]),
 ('publication-cuts',[str(h/'publication_faults.py'),'--binary',str(b/'kestrel-stress.exe'),'--sql-binary',str(b/'kestrel.exe'),'--fault-driver',str(b/'publication_fault_probe.exe'),'--output',str(w/'publication-049-faults.json'),'--expected-version','0.3.16']),
 ('source-cuts-kills',[str(h/'source_faults.py'),'--driver',str(b/'source_fault_probe.exe'),'--adapter',str(b/'source-pipeline.exe'),'--output',str(w/'source-049-faults.json')]),
 ('concurrent-kills',[str(root/'benchmarks/group_commit_recovery.py'),'--binary',str(b/'kestrel-stress.exe'),'--output',str(w/'group-049-recovery.json'),'--expected-version','0.3.16','--retry-index']),
 ('general-sql',[str(root/'benchmarks/archive_verify.py'),'--binary',str(b/'kestrel.exe'),'--output',str(w/'archive-049-verification.json'),'--queries','500']),
 *[(n,[str(h/f'{n}_verify.py')]) for n in ['group','cache','medium','dense','sparse','scan','reader']]
]
proof={'trial':'isolated CAT5, version string inherited from base, never released','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'steps':[],'complete':False}
if (w/'correctness-gates.json').exists():
    proof=json.loads((w/'correctness-gates.json').read_text(encoding='utf-8'))
for name,args in steps:
    if any(v['name']==name and v['returncode']==0 for v in proof['steps']):continue
    out=w/(name+'.txt')
    if out.exists():
        prior=w/(name+'-first-failure.txt');assert not prior.exists();out.rename(prior)
    started=datetime.datetime.now(datetime.timezone.utc).isoformat();print('START '+name,flush=True)
    with out.open('w',encoding='utf-8') as log:
        result=subprocess.run([sys.executable,*args],env=env,cwd=root,stdout=log,stderr=subprocess.STDOUT)
    proof['steps'].append({'name':name,'command':[sys.executable,*args],'started_utc':started,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'returncode':result.returncode,'log_sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
    (w/'correctness-gates.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    if result.returncode:print(out.read_text(encoding='utf-8')[-6000:],flush=True);raise SystemExit(result.returncode)
    print('PASS '+name,flush=True)
proof['complete']=True;(w/'correctness-gates.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print('All external correctness gates passed',flush=True)
