"""Run exactly the predeclared native cohort, serially, preserving failed and unstarted cases."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,subprocess
W=Path('D:/Codex/Kestrel/work/perf-092')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
policy=load(W/'policy.json'); freeze=load(W/'timing-freeze.json')
assert load(W/'pre-timing-process-check.json')['active_processes']==[]
assert not (W/'paired-reclaim.json').exists()
assert all(sha(W/n)==h for n,h in freeze['sha256'].items())
out=W/'cases';out.mkdir()
report={'complete':False,'started_utc':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(W/'policy.json'),
        'freeze_sha256':sha(W/'timing-freeze.json'),'cases':[],'failed_cases':[],'unstarted_cases':policy['cases']}
save(W/'paired-reclaim.json',report)
for index,spec in enumerate(policy['cases']):
    d=out/f'{index:03d}';d.mkdir();argv=list(map(str,[W/'binaries/reclaim_phase_probe.exe',d/'archive',spec['variant'],spec['mode']]))
    started=datetime.now(timezone.utc).isoformat()
    try:
        with (d/'stdout.json').open('wb') as so,(d/'stderr.log').open('wb') as se:
            r=subprocess.run(argv,stdout=so,stderr=se,timeout=240)
        status={'case_index':index,**spec,'argv':argv,'started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),'exit':r.returncode}
        save(d/'status.json',status)
        assert r.returncode==0,status
        x=load(d/'stdout.json'); assert len(x['records'])==9 and x['rows']==61568 and x['cold_reopen_passed']
        report['cases'].append({**status,'raw':(d/'stdout.json').relative_to(W).as_posix()})
        report['unstarted_cases']=policy['cases'][index+1:];save(W/'paired-reclaim.json',report)
        print(json.dumps({'case':index+1,'of':len(policy['cases']),**spec}),flush=True)
    except BaseException as e:
        report['failed_cases'].append({'case_index':index,**spec,'error':repr(e)})
        report['unstarted_cases']=policy['cases'][index+1:];save(W/'paired-reclaim.json',report);raise
report['complete']=True;report['finished_utc']=datetime.now(timezone.utc).isoformat();save(W/'paired-reclaim.json',report)
assert all(sha(W/n)==h for n,h in freeze['sha256'].items())
print(json.dumps({'complete':True,'cases':len(report['cases'])}),flush=True)
