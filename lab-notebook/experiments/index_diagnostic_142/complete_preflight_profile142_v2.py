"""Reuse all five correct excluded outputs; finish only the unstarted sixth input."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys,time,traceback
sys.dont_write_bytecode=True
R=Path('D:/Codex/Kestrel/work');W=R/'perf-142'
sys.path.insert(0,str(R));from index_reference_142 import check
namespace={};code=(R/'run_index_profile_142.py').read_text();exec(compile(code[:code.index('policy=load(')],'profile142.API','exec'),namespace)
namespace['policy']=json.loads((W/'policy.json').read_text())
k=namespace['k'];own=k.GetCurrentProcess();original,system=namespace['mask'](own);worker=None
root=W/'smoke-fixtures';checks=[]
def activity(place):return namespace['activity_check'](place)
try:
    assert not (W/'smoke-proof.json').exists() and not (W/'component-cases.jsonl').exists()
    assert json.loads((W/'protocol-proof.json').read_text())['complete']
    assert original&256 and system&256 and k.SetProcessAffinityMask(own,256)
    worker=namespace['SafetyWorker']();namespace['worker']=worker
    began=time.monotonic();quiet=None;resets=0
    while True:
        assert time.monotonic()-began<7200
        probe=activity('preflight_v2_cooldown');now=time.monotonic()
        if probe['exit']==0:
            if quiet is None:quiet=now
            if now-quiet>=120:break
        else:quiet=None;resets+=1
        time.sleep(10)
    (W/'preflight-v2-quiet.json').write_text(json.dumps({'continuous_quiet_seconds':now-quiet,'busy_resets':resets,'no_native_preflight_repeated':True},indent=2)+'\n',encoding='utf-8',newline='\n')
    failed=json.loads((W/'preflight-failure.json').read_text())
    assert len(failed['completed_preflights'])==4
    # The late case reached the AFTER guard only after exit0, affinity and full
    # independent index assertions. Its identity was not serialized before that
    # guard threw; disclose this rather than fabricating an identity record.
    prior=[('ordered','baseline_a'),('clustered','baseline_b'),('interleaved','candidate'),('duplicates','baseline_a'),('late','baseline_b')]
    for name,variant in prior:
        spec={'name':name,'seed':5,'variant':variant}
        assert (root/(name+'.stderr')).read_bytes()==b''
        checked=check(json.loads((root/(name+'.stdout')).read_text()),spec)
        old=next((c for c in failed['completed_preflights'] if c['name']==name),None)
        checks.append(spec|{'actual_exit':0,'exit0_checked_in_original_source_before_after_guard':True,'identity':old['identity'] if old else None,'original_late_identity_not_serialized':old is None,'reused_excluded_output_not_retimed':True,'full_rows':checked['rows'],'full_CRC_bytes':checked['CRC_bytes']})
    spec={'name':'extreme','seed':5,'variant':'candidate'}
    probe=activity('preflight_v2_before')
    if probe['exit']==3:namespace['wait_between_cases']('before',None,probe);probe=activity('preflight_v2_before_retry')
    assert probe['exit']==0
    started=datetime.now(timezone.utc).isoformat()
    child=subprocess.Popen([str(W/'binary'/'index_profile142.exe'),'extreme','5','candidate'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=0x08000000)
    identity=namespace['identity'](child);out,err=child.communicate(timeout=90);completed=datetime.now(timezone.utc).isoformat()
    (root/'extreme.stdout').write_bytes(out);(root/'extreme.stderr').write_bytes(err)
    actual=spec|{'actual_exit':child.returncode,'actual_wait_completed':True,'identity':identity,'started_utc':started,'completed_utc':completed}
    (W/'sixth-preflight-actual.json').write_text(json.dumps(actual,indent=2)+'\n',encoding='utf-8',newline='\n')
    assert child.returncode==0 and identity['affinity_mask']==256 and not err
    checked=check(json.loads(out),spec);checks.append(actual|{'full_rows':checked['rows'],'full_CRC_bytes':checked['CRC_bytes'],'reused_excluded_output_not_retimed':False})
    probe=activity('preflight_v2_after')
    if probe['exit']==3:namespace['wait_between_cases']('after',None,probe,completed)
    else:assert probe['exit']==0
    stopped=worker.stop();worker=None;namespace['worker']=None
    assert stopped['actual_exit']==0 and not stopped['forced_owned_worker_kill']
    proof={'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'checks':checks,'excluded_from_216_cases':True,'five_existing_exact_outputs_reused_one_unstarted_completed':True,'no_preflight_case_repeated':True,'first_post_guard_failure_retained':True,'protocol_guard_checks_reused_passed':True,'metadata_worker_actual_exit':0,'no_new_Rust_test_or_speed_claim':True}
    assert sum(x['full_rows'] for x in checks)==196608 and sum(x['full_CRC_bytes'] for x in checks)==4718592
    (W/'smoke-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in proof.items() if k!='checks'}),flush=True)
except BaseException:
    (W/'preflight-v2-failure.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'error':traceback.format_exc(),'checks':checks,'all216cases_unstarted':True},indent=2)+'\n',encoding='utf-8',newline='\n');raise
finally:
    if worker is not None:worker.stop()
    assert k.SetProcessAffinityMask(own,original)
