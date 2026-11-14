"""Excluded six-store preflight plus safe owned idle-supervisor detection test."""
from pathlib import Path
import json,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-132'
namespace={};code=(R/'run_phase_compare_132.py').read_text(encoding='utf-8');exec(compile(code[:code.index('policy=load(')],'phase132.API','exec'),namespace)
reference={};code=(R/'audit_phase_compare_132.py').read_text(encoding='utf-8');exec(code[code.index('def rows('):code.index('def nearest(')],reference)
sys.path.insert(0,str(R));import archive_audit_099 as independent
k=namespace['k'];own=k.GetCurrentProcess();original,system=namespace['mask'](own)
assert original&256 and system&256
root=W/'smoke-fixtures';assert not root.exists();root.mkdir();checks=[];worker=None;dummy=None
try:
    assert k.SetProcessAffinityMask(own,256)
    worker=namespace['SafetyWorker']()
    idle=W/'idle_protocol_132.py';idle.write_text('import sys\nsys.stdin.readline()\n',encoding='utf-8',newline='\n')
    dummy=subprocess.Popen([sys.executable,str(idle)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
    dummy_identity=namespace['identity'](dummy)
    busy=worker.check('protocol_busy');messages=[json.loads(line) for line in busy['stdout'].splitlines()]
    assert busy['exit']==3 and any(row['pid']==dummy.pid for row in messages[0]['other_work'])
    out,err=dummy.communicate(b'finish\n',timeout=10);assert dummy.returncode==0
    clear=worker.check('protocol_clear');assert clear['exit']==0
    (W/'protocol-proof.json').write_text(json.dumps({'complete':True,'dummy_detected_busy_then_clear':True,'dummy_identity':dummy_identity,'dummy_actual_exit':dummy.returncode,'no_unrelated_process_changed':True,'worker_identity':worker.identity,'all_proto_outside_native_cases':True},indent=2)+'\n',encoding='utf-8',newline='\n')
    for name in ['ordered','clustered']:
        for variant in ['baseline_a','baseline_b','candidate']:
            assert worker.check('preflight_before')['exit']==0
            directory=root/(name+'-'+variant+'-seed5')
            binary=W/'binary'/('candidate131.exe' if variant=='candidate' else 'baseline.exe')
            child=subprocess.Popen([str(binary),str(directory),name,'5'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
            identity=namespace['identity'](child);out,err=child.communicate(timeout=90)
            (root/(name+'-'+variant+'.stdout')).write_bytes(out);(root/(name+'-'+variant+'.stderr')).write_bytes(err)
            assert child.returncode==0 and identity['affinity_mask']==256
            result=json.loads(out);assert result['all_checks_passed']
            expected=[row for run in range(32) for row in reference['rows'](name,run,5)]
            receipts={id:(reference['rows'](name,run,5),generation) for id,run,generation in result['receipts']}
            checked=independent.check(directory,expected,receipts)
            assert checked['rows']==32768 and checked['full_block_crc_bytes']==786432
            assert worker.check('preflight_after')['exit']==0
            checks.append({'name':name,'variant':variant,'actual_exit':child.returncode,'identity':identity,'full_rows':checked['rows'],'full_CRC_bytes':checked['full_block_crc_bytes']})
    stopped=worker.stop();worker=None;assert stopped['actual_exit']==0 and not stopped['forced_owned_worker_kill']
    proof={'complete':True,'checks':checks,'excluded_from_216_cases':True,'no_new_Rust_test_or_speed_claim':True,'metadata_worker_actual_exit':0,'protocol_guard_checks_passed':True}
    (W/'smoke-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'complete':True,'excluded_smokes':6,'full_rows':sum(x['full_rows'] for x in checks),'CRC_bytes':sum(x['full_CRC_bytes'] for x in checks),'owned_idle_dummy_detection_passed':True,'worker_actual_exit':0}))
except BaseException:
    (W/'preflight-failure.json').write_text(json.dumps({'error':traceback.format_exc(),'completed_preflights':checks,'all_216_timed_cases_unstarted':True},indent=2)+'\n',encoding='utf-8',newline='\n');raise
finally:
    if dummy is not None and dummy.poll() is None:
        dummy.communicate(b'finish\n',timeout=10)
    if worker is not None:worker.stop()
    assert k.SetProcessAffinityMask(own,original)
