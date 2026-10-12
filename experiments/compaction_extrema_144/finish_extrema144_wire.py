"""Finish the five unstarted wire checks; never repeat a native case."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ctypes,hashlib,json,subprocess,sys,os,time,traceback
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-144';PS='D:/Codex/Migration-20261007/helper-runtime/powershell/pwsh.exe'
sys.path.insert(0,str(R));import archive_audit_099 as independent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(ctypes.c_uint64)]*4
times=[ctypes.c_uint64() for _ in range(4)];assert k.GetProcessTimes(k.GetCurrentProcess(),*(ctypes.byref(t) for t in times))
def probe(place):
    started=now();reports=[]
    for args in [[PS,'-NoProfile','-File',str(R/'check_extrema144_wire_finish_activity.ps1'),'-OwnerPid',str(os.getpid()),'-OwnerCreationFileTime',str(times[0].value)], [PS,'-NoProfile','-File',str(R/'check_global_build_activity.ps1')]]:
        p=subprocess.run(args,capture_output=True,timeout=30,creationflags=0x08000000)
        assert p.returncode in (0,3),(p.returncode,p.stderr.decode())
        reports.append(json.loads(p.stdout));
        if p.returncode==3:break
    clear=reports[0]['no_other_task_work'] and len(reports)==2 and reports[1]['no_visible_build_jobs']
    row={'place':place,'started_utc':started,'completed_utc':now(),'clear':clear,'reports':reports}
    with (W/'wire-finish-activity.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(row)+'\n')
    return row
def wait_clear(initial,place):
    began=now();start=time.monotonic();quiet=None;resets=0
    while True:
        assert time.monotonic()-start<7200,'Quiet wait deadline; no next native case started'
        p=probe('wait-'+place);tick=time.monotonic()
        if p['clear']:
            if quiet is None:quiet=tick
            if tick-quiet>=120:break
        else:quiet=None;resets+=1
        time.sleep(10)
    row={'started_utc':began,'completed_utc':now(),'initial':initial,'continuous_clear_seconds':tick-quiet,'busy_resets':resets,'no_case_repeated':True}
    with (W/'wire-finish-pauses.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(row)+'\n')
def before(place):
    p=probe(place)
    if not p['clear']:wait_clear(p,place);assert probe(place+'-retry')['clear']
def after(place,exited):
    p=probe(place)
    if p['clear']:return
    reports=p['reports'];assert not reports[0]['reset_jobs']
    jobs=reports[0]['other_work']+([] if len(reports)==1 else reports[1]['visible_build_jobs'])
    cutoff=max(datetime.fromisoformat(exited)+timedelta(seconds=.1),datetime.fromisoformat(p['started_utc']))
    assert jobs and all(datetime.fromisoformat(j['creation_utc'])>=cutoff for j in jobs),'Possible in-case interference; preserve prefix'
    wait_clear(p,place)
checks=[];pairs=[]
try:
    original=load(W/'legacy-wire-declaration.json');assert len(original['cases'])==12
    old=[json.loads(s) for s in (W/'legacy-wire-cases.jsonl').read_text().splitlines()];assert len(old)==7 and all(r['actual_exit']==0 and r['actual_wait_completed'] for r in old)
    binaries={'legacy016':R/'compaction-kit-122/baseline.exe','candidate144':W/'binary/candidate144.exe'}
    assert all(sha(binaries[name])==h for name,h in original['binary_sha256'].items())
    assert load(W/'store-audit.json')['all28_stores_checked']
    (W/'wire-finish-declaration.json').write_text(json.dumps({'utc':now(),'reused_native_cases':7,'new_native_cases':5,'inputs_order_binaries_unchanged':True,'before_busy_wait120_no_timer_started':True,'after_busy_wait_only_proven_birth_after_exit100ms_and_post_start':True,'no_native_case_repeated':True,'qualified_performance_cases':0},indent=2)+'\n',encoding='utf-8',newline='\n')
    root=W/'legacy-wire-fixtures'
    for spec in original['cases'][7:]:
        shape=spec['shape'];variant=spec['variant'];assert spec['seed']==5
        before('before-'+shape+'-'+variant)
        store=root/(shape+'-'+variant);assert not store.exists()
        started=now();child=subprocess.Popen([str(binaries[variant]),str(store),shape,'5'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
        out,err=child.communicate(timeout=90);exited=now()
        (root/(shape+'-'+variant+'.stdout')).write_bytes(out);(root/(shape+'-'+variant+'.stderr')).write_bytes(err)
        record={'shape':shape,'variant':variant,'actual_exit':child.returncode,'actual_wait_completed':True,'started_utc':started,'completed_utc':exited,'excluded_correctness_only':True}
        with (W/'legacy-wire-cases.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(record)+'\n')
        assert child.returncode==0 and not err
        result=json.loads(out);assert result['all_checks_passed'] and result['seed']==5 and result['workload']==shape
        after('after-'+shape+'-'+variant,exited)
    # Now audit every original and new output once, without launching children.
    before('before-full-independent-wire-audit')
    reference={};text=(R/'audit_phase_compare_133.py').read_text();exec(text[text.index('def rows('):text.index('def nearest(')],reference)
    records=[json.loads(s) for s in (W/'legacy-wire-cases.jsonl').read_text().splitlines()]
    assert len(records)==12 and [(r['shape'],r['variant']) for r in records]==[(s['shape'],s['variant']) for s in original['cases']]
    for shape in ['ordered','clustered','interleaved','duplicates','late','extreme']:
        files={}
        for variant in binaries:
            store=root/(shape+'-'+variant);record=next(r for r in records if r['shape']==shape and r['variant']==variant)
            assert record['actual_exit']==0 and record['actual_wait_completed']
            result=load(root/(shape+'-'+variant+'.stdout'));assert result['all_checks_passed'] and result['seed']==5 and result['workload']==shape
            rows=[row for run in range(32) for row in reference['rows'](shape,run,5)]
            expected=[[f'merge121:{run}',run,run+1] for run in range(32)] if shape in ['clustered','late'] else []
            assert result['receipts']==expected
            receipts={id:(reference['rows'](shape,run,5),gen) for id,run,gen in expected}
            checked=independent.check(store,rows,receipts);assert checked['rows']==32768 and checked['head']==33 and checked['full_block_crc_bytes']==786432 and len(checked['segments'])==1
            checks.append(record|{'rows':32768,'CRC_bytes':786432,'all_original_receipts_and_indexes_checked':True})
            files[variant]={p.name:p.read_bytes() for p in store.glob('*.ks2') if p.is_file()}
        assert files['legacy016']==files['candidate144'],shape
        pairs.append({'shape':shape,'all_remaining_segment_catalog_bytes_exact':True,'files':len(files['legacy016']),'bytes_each':sum(map(len,files['legacy016'].values()))})
    proof={'complete':True,'utc':now(),'checks':checks,'pairs':pairs,'independent_rows':393216,'independent_CRC_bytes':9437184,'all12_actual_exit0':True,'all_six_wire_pairs_exact':True,'performance_cases_declared':0,'speed_claim':False,'release017_qualified':False,'seven_original_native_cases_reused_five_unstarted_finished':True,'no_native_case_repeated':True}
    assert not (W/'legacy-wire-audit.json').exists();(W/'legacy-wire-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in proof.items() if k not in ('checks','pairs')}),flush=True)
except BaseException:
    (W/'wire-finish-failure.json').write_text(json.dumps({'utc':now(),'error':traceback.format_exc(),'checks':checks,'pairs':pairs,'no_native_case_repeated':True},indent=2)+'\n',encoding='utf-8',newline='\n');raise
