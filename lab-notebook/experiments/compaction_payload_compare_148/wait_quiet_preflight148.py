"""One owned metadata-only quiet interval before the fresh excluded preflight."""
from pathlib import Path
import json, time
R=Path('D:/Codex/Kestrel/work');W=R/'perf-148'
source=(R/'run_phase_compare_148.py').read_text(encoding='utf-8')
api={};exec(compile(source[:source.index('policy=load(')],'phase148.quietAPI','exec'),api)
assert not (W/'smoke-fixtures').exists() and not (R/'phase148-preflight-quiet-proof.json').exists()
k=api['k'];own=k.GetCurrentProcess();original,system=api['mask'](own)
assert original&256 and system&256
worker=None;started=api['utc']();begin=time.monotonic();quiet=None;resets=0
try:
    assert k.SetProcessAffinityMask(own,256)
    worker=api['SafetyWorker']()
    while True:
        assert time.monotonic()-begin<7200,'Quiet deadline; no native preflight started'
        probe=worker.check('preflight_continuous_quiet');now=time.monotonic()
        if probe['exit']==0:
            if quiet is None:quiet=now
            if now-quiet>=120:break
        else:quiet=None;resets+=1
        time.sleep(10)
    stopped=worker.stop();worker=None
    assert stopped['actual_exit']==0 and not stopped['forced_owned_worker_kill']
    proof={'started_utc':started,'completed_utc':api['utc'](),'continuous_quiet_seconds':now-quiet,'elapsed_seconds':now-begin,'busy_resets':resets,'metadata_worker_actual_exit':0,'no_native_cases_started':True}
    (R/'phase148-preflight-quiet-proof.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(proof),flush=True)
finally:
    if worker is not None:worker.stop()
    assert k.SetProcessAffinityMask(own,original)
