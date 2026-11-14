"""Fourteen owned compaction publication faults; preserve every attempted prefix."""
from pathlib import Path
from datetime import datetime,timezone
import ctypes,hashlib,json,os,struct,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-144'
PS='D:/Codex/Migration-20261007/helper-runtime/powershell/pwsh.exe'
sys.path.insert(0,str(R));import archive_audit_099 as independent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def now():return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
k=ctypes.WinDLL('kernel32',use_last_error=True);k.GetCurrentProcess.restype=ctypes.c_void_p
k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.POINTER(ctypes.c_uint64)]*4
times=[ctypes.c_uint64() for _ in range(4)];assert k.GetProcessTimes(k.GetCurrentProcess(),*(ctypes.byref(v) for v in times))
def guard(label):
    result=subprocess.run([PS,'-NoProfile','-File',str(R/'check_extrema144_recovery_activity.ps1'),'-OwnerPid',str(os.getpid()),'-OwnerCreationFileTime',str(times[0].value)],capture_output=True,timeout=30,creationflags=0x08000000)
    row={'utc':now(),'place':label,'actual_exit':result.returncode,'stdout':result.stdout.decode(),'stderr':result.stderr.decode()}
    with (W/'recovery-activity.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
    assert result.returncode==0,row
    result=subprocess.run([PS,'-NoProfile','-File',str(R/'check_global_build_activity.ps1')],capture_output=True,timeout=30,creationflags=0x08000000)
    assert result.returncode==0,result.stdout.decode()

checks=[];commands=[]
try:
    declaration=load(W/'recovery-declaration.json');built=load(W/'recovery-artifact-build.json')
    assert declaration['fresh_owned_fault_cases']==14 and built['complete'] and load(W/'legacy-wire-audit.json')['all_six_wire_pairs_exact']
    assert all(sha(W/'binary'/n)==h for n,h in built['binary_sha256'].items())
    root=W/'recovery-fixtures';assert not root.exists();root.mkdir()
    first=[[r,(r*37)%1000-500,(r*17)%97] for r in range(1024)]
    second=[[-2000+r,(r*29)%1000-500,r%17-8] for r in range(1024)]
    expected=first+second;receipts={f'seed:{i}':(first[i*256:(i+1)*256],1) for i in range(4)}
    incoming=root/'second-row-major-i64.bin';incoming.write_bytes(b''.join(struct.pack('<qqq',*row) for row in second))
    cli=W/'binary/recovery144-cli.exe';seed=W/'binary/recovery144-seed.exe';fault=W/'binary/recovery144-fault.exe'
    assert not any(key.startswith('KESTREL_FAULT') for key in os.environ)
    def run(label,argv,expected_exit,env=None):
        started=now();child=subprocess.Popen(list(map(str,argv)),stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=os.environ|(env or {}),creationflags=0x08000000)
        stdout,stderr=child.communicate(timeout=60)
        row={'label':label,'pid':child.pid,'actual_exit':child.returncode,'expected_exit':expected_exit,'actual_wait_completed':True,'started_utc':started,'completed_utc':now()}
        (root/(label+'.stdout')).write_bytes(stdout);(root/(label+'.stderr')).write_bytes(stderr)
        commands.append(row)
        with (W/'recovery-command-exits.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
        assert child.returncode==expected_exit,row
        return stdout,stderr
    for point in declaration['points']:
        for mode in declaration['modes']:
            label=point+'-'+mode;store=root/label
            guard('before-'+label)
            run(label+'-seed',[seed,store,'4','1024'],0)
            run(label+'-import',[cli,'--archive',store,'--import-i64',incoming],0)
            before=independent.check(store,expected,receipts);assert before['head']==2 and len(before['segments'])==2
            stdout,stderr=run(label+'-fault',[fault,store,'compact'],86 if mode=='exit' else 87,{'KESTREL_FAULT_POINT':point,'KESTREL_FAULT_MODE':mode})
            if mode=='io_error':assert b'poisoned writer; old snapshot readable' in stderr and b'outcome unknown' in stderr
            guard('after-fault-'+label)
            stdout,stderr=run(label+'-cold-query',[cli,'--archive',store,'--sql','SELECT COUNT(*), SUM(value), MIN(ts), MAX(ts) FROM events'],0)
            response=json.loads(stdout);assert response['ok'] and response['result']['rows']==[[2048,sum(row[1] for row in expected),-2000,1023]]
            checked=independent.check(store,expected,receipts)
            wanted=3 if point=='catalog_published' else 2
            assert checked['head']==wanted and checked['rows']==2048 and checked['full_block_crc_bytes']==49152 and len(checked['segments'])==(1 if wanted==3 else 2)
            checks.append({'point':point,'mode':mode,'head':wanted,'rows':checked['rows'],'CRC_bytes':checked['full_block_crc_bytes'],
                           'all_acknowledged_input_rows_original_receipts_indexes_checked':True,'cold_query_passed':True,'writer_poison_old_snapshot_checked':mode=='io_error',
                           'controlled_owned_exit_not_forced_unrelated_kill':True})
    guard('completed-recovery')
    prep=load(W/'preparation-proof.json');assert all(sha(W/'candidate'/n)==h for n,h in prep['candidate_source_sha256'].items())
    proof={'complete':True,'utc':now(),'checks':checks,'commands':commands,'fresh_fault_cases':14,'actual_commands':56,
           'full_independent_rows':sum(c['rows'] for c in checks),'full_independent_CRC_bytes':sum(c['CRC_bytes'] for c in checks),
           'original_receipt_generations_preserved':True,'all_source_byte_exact':True,'controlled_process_exits':7,'injected_IO_errors':7,
           'no_physical_power_loss_claim':True,'no_forced_process_kill':True,'timed_performance_cases':0,'speed_claim':False,'release017_qualified':False}
    assert len(checks)==14 and len(commands)==56 and proof['full_independent_rows']==28672 and proof['full_independent_CRC_bytes']==688128
    assert not (W/'recovery-proof.json').exists()
    (W/'recovery-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in proof.items() if k not in ['commands','checks']}),flush=True)
except BaseException:
    (W/'recovery-failure.json').write_text(json.dumps({'utc':now(),'error':traceback.format_exc(),'completed_checks':checks,'actual_commands':commands,
          'timed_performance_cases':0,'no_selected_rerun':True},indent=2)+'\n',encoding='utf-8',newline='\n');raise
