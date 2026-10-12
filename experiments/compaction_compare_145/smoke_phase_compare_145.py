"""Excluded six-store preflight plus safe owned idle-supervisor detection test."""
from pathlib import Path
import json,subprocess,sys,traceback
from datetime import datetime,timezone
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-145'
namespace={};code=(R/'run_phase_compare_145.py').read_text(encoding='utf-8');exec(compile(code[:code.index('policy=load(')],'phase145.API','exec'),namespace)
reference={};code=(R/'audit_phase_compare_145.py').read_text(encoding='utf-8');exec(code[code.index('def rows('):code.index('def nearest(')],reference)
sys.path.insert(0,str(R));import archive_audit_099 as independent
k=namespace['k'];own=k.GetCurrentProcess();original,system=namespace['mask'](own)
assert original&256 and system&256
root=W/'smoke-fixtures';assert not root.exists();root.mkdir();checks=[];worker=None;dummy=None
try:
    assert k.SetProcessAffinityMask(own,256)
    worker=namespace['SafetyWorker']()
    idle=W/'idle_protocol_145.py';idle.write_text('import sys\nsys.stdin.readline()\n',encoding='utf-8',newline='\n')
    dummy=subprocess.Popen([sys.executable,str(idle)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
    dummy_identity=namespace['identity'](dummy)
    busy=worker.check('protocol_busy');messages=[json.loads(line) for line in busy['stdout'].splitlines()]
    assert busy['exit']==3 and any(row['pid']==dummy.pid for row in messages[0]['other_work'])
    out,err=dummy.communicate(b'finish\n',timeout=10);assert dummy.returncode==0
    clear=worker.check('protocol_clear');assert clear['exit']==0
    classify=namespace['blockers_began_after_exit']
    sample={'exit':3,'started_utc':'2026-10-12T00:00:01+00:00','stdout':json.dumps({'other_work':[{'creation_utc':'2026-10-12T00:00:02+00:00'}],'reset_jobs':[]})}
    assert classify(sample,'2026-10-12T00:00:00+00:00')
    assert not classify(sample,'2026-10-12T00:00:02+00:00')
    sample['stdout']=json.dumps({'other_work':[{'creation_utc':'2026-10-12T00:00:00.05+00:00'}],'reset_jobs':[]})
    assert not classify(sample,'2026-10-12T00:00:00+00:00')
    sample['stdout']=json.dumps({'other_work':[{'creation_utc':'2026-10-12T00:00:02+00:00'},{}],'reset_jobs':[]})
    assert not classify(sample,'2026-10-12T00:00:00+00:00')
    sample['stdout']=json.dumps({'other_work':[{'creation_utc':'2026-10-12T00:00:02+00:00'}],'reset_jobs':[{'pid':123}]})
    assert not classify(sample,'2026-10-12T00:00:00+00:00')

    (W/'protocol-proof.json').write_text(json.dumps({'complete':True,'dummy_detected_busy_then_clear':True,'dummy_identity':dummy_identity,'dummy_actual_exit':dummy.returncode,'no_unrelated_process_changed':True,'worker_identity':worker.identity,'all_proto_outside_native_cases':True,'late_early_near_boundary_missing_time_reset_classification_tests':5},indent=2)+'\n',encoding='utf-8',newline='\n')
    for name in ['ordered','clustered']:
        for variant in ['baseline_a','baseline_b','candidate']:
            assert worker.check('preflight_before')['exit']==0
            directory=root/(name+'-'+variant+'-seed5')
            binary=W/'binary'/('candidate144.exe' if variant=='candidate' else 'baseline.exe')
            native_started=datetime.now(timezone.utc).isoformat()
            child=subprocess.Popen([str(binary),str(directory),name,'5'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
            identity=namespace['identity'](child);out,err=child.communicate(timeout=90)
            actual={'name':name,'variant':variant,'seed':5,'identity':identity,'actual_exit':child.returncode,'actual_wait_completed':True,'started_utc':native_started,'completed_utc':datetime.now(timezone.utc).isoformat(),'excluded_from_216_cases':True}
            with (W/'preflight-native-exits.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(actual)+'\n')
            (root/(name+'-'+variant+'.stdout')).write_bytes(out);(root/(name+'-'+variant+'.stderr')).write_bytes(err)
            assert child.returncode==0 and identity['affinity_mask']==256
            result=json.loads(out);assert result['all_checks_passed']
            expected=[row for run in range(32) for row in reference['rows'](name,run,5)]
            declared_receipts=[[f'merge121:{run}',run,run+1] for run in range(32)] if name in ['clustered','late'] else []
            assert result['receipts']==declared_receipts
            receipts={id:(reference['rows'](name,run,5),run+1) for id,run,generation in declared_receipts}
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
