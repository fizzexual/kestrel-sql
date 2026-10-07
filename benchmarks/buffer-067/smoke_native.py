"""Untimed, excluded smoke diagnostics for the identical native driver and memory API."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
from process_memory import peak_memory
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert json.loads((W/'qualification-audit.json').read_text(encoding='utf-8'))['passed']
d=W/'native-smoke';d.mkdir();results=[]
for label,version in [('baseline','0.3.16'),('candidate','0.3.17-dev.67')]:
    binary=W/'native-binaries'/f'{label}-publication.exe'
    argv=[str(binary),str(d/f'{label}-store'),'0','64']
    with (d/f'{label}.stdout.json').open('w',encoding='utf-8') as out,(d/f'{label}.stderr.txt').open('w',encoding='utf-8') as err:
        p=subprocess.Popen(argv,stdout=out,stderr=err)
        try:exit_code=p.wait(timeout=120)
        except subprocess.TimeoutExpired:p.kill();p.wait();raise
        memory=peak_memory(p)
    status={'label':label,'argv':argv,'pid':p.pid,'exit':exit_code,'memory':memory,'binary_sha256':sha(binary)}
    save(d/f'{label}.status.json',status);assert exit_code==0
    r=json.loads((d/f'{label}.stdout.json').read_text(encoding='utf-8'))
    assert r['version']==version and r['rows_and_sum_match'] and r['reopen_retry_and_full_scrub_passed']
    assert r['after']['rows']==6400 and r['after']['recorded_batch_ids']==64 and len(r['maintenance_ms'])==1
    assert memory['success'] and memory['peak_working_set_bytes']>0 and memory['peak_commit_bytes']>0,memory
    results.append(status)
save(W/'native-smoke.json',{'utc':datetime.now(timezone.utc).isoformat(),'passed':True,'excluded_from_all_competitive_samples_and_ratios':True,'cases':results})
print(json.dumps({'passed':True,'excluded_diagnostic_cases':2,'memory':[c['memory'] for c in results]}))
