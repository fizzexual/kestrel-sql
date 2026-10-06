"""Kill concurrent delayed groups; reconcile ACKs, whole batches and exact retries."""
import argparse
import hashlib
import json
import shutil
import threading
import time
from pathlib import Path

from stress_compare import Engine

ROOT = Path(__file__).resolve().parents[1]


def payload(key):
    return [[1000+key*100+i, key+1, 1000+key] for i in range(100)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--expected-version', default='0.3.4')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--retry-index',action='store_true')
    args = parser.parse_args()
    binary = args.binary.resolve()
    work = ROOT.parent.parent/'work'/f'group-recovery-{time.time_ns()}'
    work.mkdir()
    report = {'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
        'fault_model':'forcible process kill on a live filesystem; sixteen simultaneous producers; four uniquely identified batches each; kill delays span collection and publication but are not exact instruction cut points; no physical-power-loss claim',
        'cycles':[], 'failed_cases':[]}
    delays = [.0005,.002,.008,.012,.03,.08,.2,.5]
    for group_delay in [0,2,8,20]:
        for index, kill_delay in enumerate(delays):
            engine = Engine('kestrel',work/f'{group_delay}-{index}',1000,binary,{},bridge_args=(group_delay,1) if args.retry_index else (group_delay,))
            assert engine.version == args.expected_version
            attempts, acks, errors = set(), {}, []
            gate = threading.Barrier(17)
            active, finished, lock = threading.Event(), threading.Event(), threading.Lock()
            def producer(writer):
                connection = None
                try:
                    connection = engine.connect()
                    gate.wait(timeout=5)
                    for batch in range(4):
                        if finished.is_set():
                            break
                        key = writer*4+batch
                        with lock:
                            attempts.add(key)
                        active.set()
                        receipt = connection.call({'op':'append','id':f'kill:{key}','data':payload(key)})
                        with lock:
                            acks[key] = receipt
                except (OSError,ValueError):
                    pass
                except Exception as error:
                    with lock:
                        errors.append(repr(error))
                finally:
                    if connection is not None:
                        try:
                            connection.close()
                        except OSError:
                            pass
            threads = [threading.Thread(target=producer,args=(writer,)) for writer in range(16)]
            connection = None
            try:
                for thread in threads:
                    thread.start()
                gate.wait(timeout=5)
                assert active.wait(timeout=5)
                time.sleep(kill_delay)
                engine.process.kill()
                engine.process.wait(timeout=10)
                engine.process.stdout.close()
                finished.set()
                for thread in threads:
                    thread.join(timeout=10)
                assert not any(t.is_alive() for t in threads) and not errors, errors
                engine.start_bridge(0)
                connection = engine.connect()
                groups = connection.query('SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device')
                published = {device-1000:count for device,count,total in groups if device>=1000}
                assert set(acks) <= set(published) <= attempts
                for device,count,total in groups:
                    if device>=1000:
                        assert count==100 and total==100*(device-999), ('partial batch',device,count,total)
                count,total = connection.query('SELECT COUNT(*), SUM(value) FROM events')[0]
                assert count==1000+100*len(published) and total==-500+sum(100*(key+1) for key in published)
                assert connection.call({'op':'verify'})['verified_bytes']==count*24
                recovered_receipts = {}
                for key in sorted(attempts):
                    receipt = connection.call({'op':'append','id':f'kill:{key}','data':payload(key)})
                    assert receipt['duplicate'] == (key in published)
                    if key in acks:
                        assert receipt['generation']==acks[key]['generation']
                    recovered_receipts[key] = receipt['generation']
                assert connection.query('SELECT COUNT(*) FROM events')==[[1000+100*len(attempts)]]
                assert connection.call({'op':'verify'})['verified_bytes']==(1000+100*len(attempts))*24
                connection.close()
                connection = None
                engine.reopen()
                connection = engine.connect()
                for key,generation in recovered_receipts.items():
                    receipt = connection.call({'op':'append','id':f'kill:{key}','data':payload(key)})
                    assert receipt['duplicate'] and receipt['generation']==generation
                stats = connection.call({'op':'stats'})
                assert stats['recorded_batch_ids']==len(attempts) and stats['ingest']['queued_payload_bytes']==0
                record = {'group_delay_ms':group_delay,'kill_delay_seconds':kill_delay,
                    'attempted_batches':len(attempts),'acknowledged_batches':len(acks),
                    'published_batches':len(published),'unacknowledged_committed_batches':len(published)-len(acks),
                    'acknowledged_data_present':True,'whole_batches_and_sums':True,
                    'original_receipt_generations_preserved':True,'retry_exactly_once_after_second_reopen':True,'full_scrubs_passed':True}
                report['cycles'].append(record)
                print(json.dumps(record),flush=True)
            except Exception as error:
                report['failed_cases'].append({'group_delay_ms':group_delay,'kill_delay_seconds':kill_delay,'error':repr(error)})
                raise
            finally:
                if connection is not None:
                    connection.close()
                engine.finish()
                args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            resolved = engine.directory.resolve()
            assert resolved.is_relative_to(work.resolve()) and resolved != work.resolve()
            shutil.rmtree(resolved)
    assert len(report['cycles'])==32 and not report['failed_cases']


if __name__ == '__main__':
    main()
