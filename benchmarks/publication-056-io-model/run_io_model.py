from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,time
W=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,j):p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def initialize():
    assert not (W/'policy.json').exists()
    b=json.loads((W/'build-provenance.json').read_text());assert sha(W/'io-lifecycle-probe.exe')==b['binary_sha256']
    cases=[];sizes=[2400,153600]
    for turn in range(3):
        order=['generation','journal'] if turn%2==0 else ['journal','generation']
        for size in (sizes if turn%2==0 else list(reversed(sizes))):
            for mode in order:cases.append({'round':turn,'mode':mode,'payload_bytes':size,'repetitions':256})
    save(W/'policy.json',{'declared_utc':now(),'model_only':True,'new_sql_engine':False,'default_engine_changed':False,
        'motivation':'055 measured sync78.63%, rename10.80%, bundlewrite9.36% of writer+compaction; catalog encode0.0625%. Test file lifecycle hypothesis before engine architecture changes.',
        'models':'Equal CRC-protected frames. generation=create_new/write/flush/sync_all/rename with retained handles; journal=retained bootstrap file/write/flush/sync_all. One complete file sync for every measured commit in both modes.',
        'payload_sizes':'2400 bytes=100 rows x3xi64;153600 bytes=64 such batches; raw byte-volume models, not actual SQL rows or catalog/index wire bytes',
        'timed':'Only file open/write/flush/sync/rename stages inside native profiler; equal frame generation/encoding/CRC allocation excluded; journal bootstrap creation+sync separately outside timers',
        'excluded_semantics':'No SQL, receipt IDs/source positions, checkpoint, truncation/recovery, migration, compaction, bounded WAL growth, pinned readers or concurrent service. Model cannot qualify an Archive WAL or forecast database throughput.',
        'method':'12 fresh serial cases; three alternating pairs per payload size; rotate size order; all failures/tails/raw output/fixtures preserved',
        'storage_model':'Live Windows filesystem; no physical power-loss or administrative flush/flags changes; shared-host variation remains',
        'control':'No compile/tests/audits/packaging/Git compression while native timers run; only one task-owned profiler',
        'predeclared_hypothesis_checks':{'paired_total_ratio_at_each_size_at_most':.85,'paired_p99_ratio_at_each_size_at_most':.95,'paired_p50_guard_at_each_size_at_most':1.05},
        'decision':'Even passing every primitive check only motivates an archive-specific design and full subsequent qualification. It never promotes SQL code or overwrites failed055.',
        'free_space_guard_bytes':500000000,'case_timeout_seconds':300,'binary_sha256':b['binary_sha256'],'source_sha256':b['source_sha256'],'cases':cases})
def run():
    p=json.loads((W/'policy.json').read_text());assert sha(W/'io-lifecycle-probe.exe')==p['binary_sha256']
    assert not (W/'model-results.json').exists()
    (W/'raw').mkdir();(W/'fixtures').mkdir();r={'started_utc':now(),'policy_sha256':sha(W/'policy.json'),'cases':[],'failures':[],'complete':False};save(W/'model-results.json',r)
    for index,s in enumerate(p['cases']):
        label=f"{index:02d}-r{s['round']}-{s['payload_bytes']}-{s['mode']}";store=W/'fixtures'/label
        assert shutil.disk_usage(W).free>p['free_space_guard_bytes']
        started=time.perf_counter();status={'label':label,'spec':s,'started_utc':now()}
        with (W/'raw'/(label+'.stdout.json')).open('w') as out,(W/'raw'/(label+'.stderr.txt')).open('w') as err:
            child=subprocess.Popen([str(W/'io-lifecycle-probe.exe'),str(store),s['mode'],str(s['payload_bytes']),str(s['repetitions'])],stdout=out,stderr=err);status['pid']=child.pid
            try:status['exit_code']=child.wait(timeout=p['case_timeout_seconds'])
            except subprocess.TimeoutExpired:child.kill();child.wait();status.update(exit_code=child.returncode,timeout=True)
        status.update(wall_seconds=time.perf_counter()-started,completed_utc=now());save(W/'raw'/(label+'.status.json'),status)
        if status['exit_code']!=0:
            r['failures'].append(status);save(W/'model-results.json',r);raise RuntimeError(status)
        raw=W/'raw'/(label+'.stdout.json');data=json.loads(raw.read_text())
        assert data['cold_exact_frame_bytes_verified'] and data['sync_all_each_commit'] and not data['sql_source_receipt_checkpoint_retention_and_crash_qualification']
        assert len(data['raw_samples'])==256 and data['payload_bytes']==s['payload_bytes'] and data['mode']==s['mode']
        r['cases'].append({'label':label,'spec':s,'stdout_sha256':sha(raw)});save(W/'model-results.json',r)
        print(json.dumps({'completed':index+1,'total':12,'label':label,'max_total_ms':max(x['total_ms'] for x in data['raw_samples']),'cold_frame_bytes_passed':True,'model_only':True}),flush=True)
    r.update(complete=True,completed_utc=now());save(W/'model-results.json',r)
if __name__=='__main__':
    import sys
    if sys.argv[1:]==['--initialize']:initialize()
    else:assert not sys.argv[1:];run()
