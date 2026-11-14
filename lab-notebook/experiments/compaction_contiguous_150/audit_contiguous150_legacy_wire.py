"""Excluded correctness-only exact legacy wire comparison; no speed qualification."""
from pathlib import Path
from datetime import datetime, timezone
import ctypes, hashlib, json, subprocess, sys, traceback
sys.dont_write_bytecode = True
R = Path('D:/Codex/Kestrel/work'); W = R/'perf-150'
PS = 'D:/Codex/Migration-20261007/helper-runtime/powershell/pwsh.exe'
sys.path.insert(0, str(R))
import archive_audit_099 as independent

def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()

reference = {}
text = (R/'audit_phase_compare_133.py').read_text(encoding='utf-8')
exec(text[text.index('def rows('):text.index('def nearest(')], reference)
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.GetCurrentProcess.restype = ctypes.c_void_p
kernel.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(ctypes.c_uint64)]*4
born, end, system, user = [ctypes.c_uint64() for _ in range(4)]
assert kernel.GetProcessTimes(kernel.GetCurrentProcess(), *(ctypes.byref(v) for v in [born,end,system,user]))

def guard():
    result = subprocess.run([PS,'-NoProfile','-File',str(R/'check_contiguous150_wire_activity.ps1'),
                             '-OwnerPid',str(__import__('os').getpid()),'-OwnerCreationFileTime',str(born.value)],
                            capture_output=True, timeout=30, creationflags=0x08000000)
    report = {'utc':now(),'actual_exit':result.returncode,'stdout':result.stdout.decode(), 'stderr':result.stderr.decode()}
    with (W/'wire-activity.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(report)+'\n')
    assert result.returncode == 0, report
    result = subprocess.run([PS,'-NoProfile','-File',str(R/'check_global_build_activity.ps1')],capture_output=True,timeout=30,creationflags=0x08000000)
    assert result.returncode == 0, result.stdout.decode()

checks=[]; pairs=[]
try:
    build=load(W/'build-proof.json'); audit=load(W/'store-audit.json')
    assert build['complete'] and audit['all52_declared_stores_checked']
    assert load(R/'contiguous150-build-actual-exits.json')['build_actual_exit']==0
    assert load(R/'contiguous150-audit-actual-exits.json')['audit_actual_exit']==0
    root=W/'legacy-wire-fixtures'; assert not root.exists()
    names=['ordered','clustered','interleaved','duplicates','late','extreme']
    binaries={'legacy016':R/'compaction-kit-122/baseline.exe','candidate150':W/'binary/candidate150.exe'}
    hashes={'legacy016':'2392cb6e53c0736a2d3bb67fd89369016848e6e12010989369b46a7a4ec2c1c7','candidate150':build['candidate_sha256']}
    assert all(sha(p)==hashes[n] for n,p in binaries.items())
    declared={'utc':now(),'cases':[{'shape':n,'variant':v,'seed':5} for n in names for v in binaries],
              'all12_excluded_from_future_performance_cohorts':True,'speed_claim':False,'binary_sha256':hashes,
              'exact_same_driver_inputs':True,'no_retiming_or_outlier_selection':True}
    assert not (W/'legacy-wire-declaration.json').exists()
    (W/'legacy-wire-declaration.json').write_text(json.dumps(declared,indent=2)+'\n',encoding='utf-8',newline='\n')
    root.mkdir()
    for shape in names:
        files={}
        for variant,binary in binaries.items():
            guard()
            store=root/(shape+'-'+variant); started=now()
            child=subprocess.Popen([str(binary),str(store),shape,'5'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
            stdout,stderr=child.communicate(timeout=90); completed=now()
            (root/(shape+'-'+variant+'.stdout')).write_bytes(stdout)
            (root/(shape+'-'+variant+'.stderr')).write_bytes(stderr)
            record={'shape':shape,'variant':variant,'actual_exit':child.returncode,'actual_wait_completed':True,
                    'started_utc':started,'completed_utc':completed,'excluded_correctness_only':True}
            with (W/'legacy-wire-cases.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(record)+'\n')
            assert child.returncode==0,record
            guard()
            result=json.loads(stdout); assert result['all_checks_passed'] and result['seed']==5 and result['workload']==shape
            expected=[row for run in range(32) for row in reference['rows'](shape,run,5)]
            declared_receipts=[[f'merge121:{run}',run,run+1] for run in range(32)] if shape in ['clustered','late'] else []
            assert result['receipts']==declared_receipts
            receipts={id:(reference['rows'](shape,run,5),run+1) for id,run,generation in declared_receipts}
            decoded=independent.check(store,expected,receipts)
            assert decoded['rows']==32768 and decoded['head']==33 and len(decoded['segments'])==1 and decoded['full_block_crc_bytes']==786432
            files[variant]={p.name:p.read_bytes() for p in store.glob('*.ks2') if p.is_file()}
            checks.append(record|{'rows':decoded['rows'],'CRC_bytes':decoded['full_block_crc_bytes'],'all_original_receipts_and_indexes_checked':True})
        assert files['legacy016'].keys()==files['candidate150'].keys()
        assert all(files['legacy016'][n]==files['candidate150'][n] for n in files['legacy016']),shape
        pairs.append({'shape':shape,'all_remaining_segment_catalog_bytes_exact':True,'files':len(files['legacy016']),
                      'bytes_each':sum(map(len,files['legacy016'].values()))})
    proof={'complete':True,'utc':now(),'checks':checks,'pairs':pairs,'independent_rows':sum(x['rows'] for x in checks),
           'independent_CRC_bytes':sum(x['CRC_bytes'] for x in checks),'all12_actual_exit0':True,'all_six_wire_pairs_exact':True,
           'performance_cases_declared':0,'speed_claim':False,'fresh_process_kill_recovery_claim':False,'release017_qualified':False}
    assert proof['independent_rows']==393216 and proof['independent_CRC_bytes']==9437184
    assert not (W/'legacy-wire-audit.json').exists()
    (W/'legacy-wire-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in proof.items() if k not in ['checks','pairs']}),flush=True)
except BaseException:
    (W/'legacy-wire-failure.json').write_text(json.dumps({'utc':now(),'error':traceback.format_exc(),'completed_checks':checks,'completed_pairs':pairs,
          'no_selected_retiming':True,'performance_cases_declared':0},indent=2)+'\n',encoding='utf-8',newline='\n')
    raise
