"""One fixed native cohort, serial owned processes; preserve every miss, partial and unstarted case."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,traceback
ROOT=Path('D:/Codex/Kestrel');W=ROOT/'work/perf-099'
sys.path.insert(0,str(W));from native_resources_088 import read_process
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def utc():return datetime.now(timezone.utc).isoformat()
policy=load(W/'policy.json');freeze=load(W/'timing-freeze.json')
assert sha(W/'policy.json')=='1853ca1638e9227517f67ff5ce32bd0a18165bb84769505637b530522744170c'
assert load(W/'oracle-proof.json')['complete'] and load(W/'helper-validation.json')['passed']
guard=sorted((ROOT/'work').glob('guard-pretime-099-*.json'))[-1]
assert not load(guard)['active_processes'] and load(guard)['reset_phase']=='waiting-for-full-codex-exit'
assert all(sha(W/n)==h for n,h in freeze['sha256'].items())
assert not (W/'paired-retirement.json').exists() and not (W/'cases').exists()
report={'complete':False,'started_utc':utc(),'policy_sha256':sha(W/'policy.json'),'freeze_sha256':sha(W/'timing-freeze.json'),
        'cases':[],'failed_cases':[],'unstarted_cases':policy['cases']}
save(W/'paired-retirement.json',report);(W/'cases').mkdir()
for index,spec in enumerate(policy['cases']):
    d=W/'cases'/f'{index:03d}';d.mkdir();argv=list(map(str,[W/'binaries/retirement_probe_099.exe',d/'archive',spec['variant'],spec['history']]))
    record={'case_index':index,**spec,'argv':argv,'started_utc':utc(),'raw':(d/'stdout.json').relative_to(W).as_posix(),
            'stderr':(d/'stderr.log').relative_to(W).as_posix()};proc=None
    try:
        with (d/'stdout.json').open('wb') as stdout,(d/'stderr.log').open('wb') as stderr:
            proc=subprocess.Popen(argv,stdout=stdout,stderr=stderr,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            identity=read_process(proc.pid);record['owned_process_identity']={k:identity[k] for k in ['pid','creation_filetime']}
            save(d/'status.json',record)
            try:code=proc.wait(timeout=240)
            except subprocess.TimeoutExpired:
                record.update(timeout=True,error='Native health deadline; not a passing shutdown',failed_utc=utc())
                save(d/'status.json',record);report['failed_cases'].append(record.copy());report['unstarted_cases']=policy['cases'][index+1:]
                save(W/'paired-retirement.json',report)
                if proc.poll() is None:
                    now=read_process(proc.pid);assert now['creation_filetime']==identity['creation_filetime']
                    proc.kill();proc.wait(timeout=10);record['exact_owned_handle_killed_after_failure_journal']=True
                raise
        record.update(exit_code=code,finished_utc=utc());save(d/'status.json',record)
        assert code==0,record
        x=load(d/'stdout.json');assert x['trial']==99 and len(x['records'])==8 and len(x['append_records'])==256
        assert x['rows']==58368 and x['worker_actually_joined_and_pending_empty'] and x['cold_reopen_passed']
        report['cases'].append(record);report['unstarted_cases']=policy['cases'][index+1:];save(W/'paired-retirement.json',report)
        print(json.dumps({'case':index+1,'of':len(policy['cases']),**spec}),flush=True)
    except BaseException:
        record.update(error=traceback.format_exc(),finished_utc=utc());save(d/'status.json',record)
        if not report['failed_cases']:report['failed_cases'].append(record)
        report['unstarted_cases']=policy['cases'][index+1:];save(W/'paired-retirement.json',report)
        if proc is not None and proc.poll() is None:
            proc.kill();proc.wait(timeout=10)
            record['exact_owned_handle_killed_after_failure_journal']=True;save(d/'status.json',record)
        raise
report.update(complete=True,finished_utc=utc());save(W/'paired-retirement.json',report)
assert all(sha(W/n)==h for n,h in freeze['sha256'].items())
print(json.dumps({'complete':True,'cases':len(report['cases']),'no_selective_repeat':True}),flush=True)
