"""Prove confirmed retry availability during a stalled writer and fail-closed health.

Only a separate feature-enabled driver is instrumented; default bridge recovers.
Injected OS errors/process stalls occur on a live filesystem, not physical power loss.
"""
import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

from publication_faults import POINTS
from stress_compare import Engine

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--driver', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    binary,driver = args.binary.resolve(),args.driver.resolve()
    work = ROOT.parent.parent/'work'/f'live-retry-faults-{time.time_ns()}'
    work.mkdir()
    report = {'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
        'driver_sha256':hashlib.sha256(driver.read_bytes()).hexdigest(),
        'fault_model':'feature-only deterministic writer stall and seven disk-full OS-error injection points; default bridge recovery; live filesystem; no physical-power-loss claim',
        'cases':[], 'failed_cases':[]}
    for mode,point in [('pause',None),*[('poison',p) for p in POINTS]]:
        directory = work/f'{mode}-{point}'
        engine = Engine('kestrel',directory,0,binary,{})
        connection = engine.connect()
        known = {'op':'append','id':'known','data':[[1000,3,1]]*100}
        receipt = connection.call(known)
        assert receipt['generation']==1 and not receipt['duplicate']
        connection.close()
        engine.finish()
        try:
            environment = dict(os.environ)
            if mode=='pause':
                environment['KESTREL_LIVE_PAUSE'] = str(directory/'pause')
            else:
                environment.update(KESTREL_FAULT_POINT=point,KESTREL_FAULT_MODE='io_error')
            result = subprocess.run([str(driver),str(directory/'archive'),mode],env=environment,text=True,capture_output=True,timeout=20)
            assert result.returncode==0,(mode,point,result)
            proof=json.loads(result.stdout)
            assert proof['version']=='0.3.5' and proof['passed']
            engine=Engine('kestrel',directory,0,binary,{},existing=True)
            connection=engine.connect()
            replay=connection.call(known)
            assert replay['duplicate'] and replay['generation']==1
            target={'op':'append','id':'target','data':[[1000,7,1]]*100}
            assert connection.call(target)['duplicate']==(mode=='pause' or point=='catalog_published')
            assert connection.call(target)['duplicate']
            assert connection.query('SELECT COUNT(*), SUM(value) FROM events')==[[200,1000]]
            assert connection.call({'op':'verify'})['verified_bytes']==4800
            connection.close()
            record={'mode':mode,'point':point,'driver_proof':proof,'recovery_original_receipt':True,'atomic_rows_and_sum':True,'retry_deduplication':True,'full_scrub':True}
            report['cases'].append(record)
            print(json.dumps({'mode':mode,'point':point,'passed':True}),flush=True)
        except Exception as error:
            report['failed_cases'].append({'mode':mode,'point':point,'error':repr(error)})
            raise
        finally:
            engine.finish()
            args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    assert len(report['cases'])==8 and not report['failed_cases']


if __name__=='__main__':
    main()
