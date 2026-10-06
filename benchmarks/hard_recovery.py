"""Force-kill Archive publication and test integrity/resource/grammar boundaries.
These are process failures on a live OS, not physical power failures.
"""
import argparse
import hashlib
import json
import random
import shutil
import struct
import subprocess
import threading
import time
from pathlib import Path

from stress_compare import Engine, KestrelConnection

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary',type=Path,default=ROOT/'bin'/'kestrel-stress.exe')
    parser.add_argument('--sql-binary',type=Path,default=ROOT/'bin'/'kestrel.exe')
    parser.add_argument('--work',type=Path,default=ROOT.parent.parent/'work'/f'hard-recovery-{time.time_ns()}')
    parser.add_argument('--cycles',type=int,default=24)
    parser.add_argument('--identified',action='store_true',help='Persist batch IDs and reconcile retries after every kill')
    parser.add_argument('--output',type=Path,default=ROOT/'benchmarks'/'hard-recovery-results.json')
    args = parser.parse_args()
    if not 1<=args.cycles<=100:
        parser.error('forced-kill cycles must be 1..100')
    args.work.mkdir(parents=True)
    report = {'fault_model':'forcible OS process kill, live filesystem; no power-loss or replicated failover claim',
        'binary_sha256':hashlib.sha256(args.binary.resolve().read_bytes()).hexdigest(),
        'sql_binary_sha256':hashlib.sha256(args.sql_binary.resolve().read_bytes()).hexdigest(),
        'cycles':[],'boundaries':{}}
    delays = [.002,.005,.01,.02,.05,.10,.25,.50]
    for cycle in range(args.cycles):
        engine = Engine('kestrel',args.work/f'crash-{cycle}',1000,args.binary.resolve(),{})
        acks, attempts = [],[]
        finished = threading.Event()
        active = threading.Event()
        unexpected = []
        def producer():
            connection = None
            try:
                connection = engine.connect()
                for batch in range(1000):
                    attempts.append(batch)
                    data = [[i,i,1] for i in range(1000+batch*1000,2000+batch*1000)]
                    active.set()
                    connection.call({'op':'append','data':data,**({'id':f'crash:{batch}'} if args.identified else {})})
                    acks.append(batch)
                    if finished.is_set(): break
            except (OSError, ValueError):
                pass
            except Exception as error:
                unexpected.append(repr(error))
            finally:
                if connection is not None:
                    connection.close()
        thread = threading.Thread(target=producer)
        thread.start()
        assert active.wait(timeout=5), 'producer never reached an append attempt'
        time.sleep(delays[cycle%len(delays)])
        engine.process.kill()
        engine.process.wait(timeout=10)
        engine.process.stdout.close()
        finished.set()
        thread.join(timeout=10)
        assert not thread.is_alive()
        assert not unexpected, unexpected
        engine.start_bridge(0)
        connection = engine.connect()
        count, total = connection.query('SELECT COUNT(*), SUM(value) FROM events')[0]
        published = (count-1000)//1000
        assert count>=1000 and (count-1000)%1000==0, 'partially published batch'
        assert len(acks)<=published<=len(attempts), 'lost acknowledged data or extra batches'
        expected = -500 + (1000+count-1)*(count-1000)//2
        assert total==expected, ('non-prefix/partial publication',count,total,expected)
        scrub = connection.call({'op':'verify'})
        assert scrub['verified_bytes']==count*24
        if args.identified:
            duplicates=0
            for batch in attempts:
                data=[[i,i,1] for i in range(1000+batch*1000,2000+batch*1000)]
                receipt=connection.call({'op':'append','id':f'crash:{batch}','data':data})
                duplicates+=int(receipt['duplicate'])
            assert duplicates==published, 'deduplication ledger differs from recovered rows'
            assert connection.query('SELECT COUNT(*) FROM events')==[[1000+len(attempts)*1000]]
            connection.call({'op':'verify'})
        connection.close()
        engine.finish()
        record = {'cycle':cycle,'kill_after_seconds':delays[cycle%len(delays)],
            'acknowledged_batches':len(acks),'attempted_batches':len(attempts),
            'published_batches':published,'recovered_rows':count,'sum_and_full_scrub_passed':True,
            'unacknowledged_committed_batches':published-len(acks)}
        if args.identified:
            record['retry_deduplication_passed']=True
            record['replayed_existing_batches']=duplicates
            record['retry_rows']=1000+len(attempts)*1000
        report['cycles'].append(record)
        print(json.dumps(record),flush=True)
        directory = engine.directory.resolve()
        assert directory.is_relative_to(args.work.resolve()) and directory!=args.work.resolve()
        shutil.rmtree(directory)

    engine = Engine('kestrel',args.work/'boundaries',1000,args.binary.resolve(),{})
    connection = engine.connect()
    # An independent Archive process cannot open the directory held by this one.
    locked = subprocess.run([str(args.sql_binary.resolve()),'--archive',str(engine.directory/'archive'),
        '--sql','SELECT COUNT(*) FROM events'],capture_output=True,text=True)
    assert locked.returncode and 'lock unavailable' in locked.stderr
    report['boundaries']['independent_process_opener_rejected'] = True
    rng = random.Random(20261006)
    corpus = ['SELECT * FROM events','UPDATE events SET value=1 WHERE ts=1',
        'DELETE FROM events WHERE ts=1','BEGIN','SELECT SUM(value) FROM events; DELETE FROM events',
        'SELECT COUNT(*) FROM events WHERE ts >= 9223372036854775808',
        'SELECT SUM(value) FROM events WHERE ts >= ?']
    alphabet = 'xyz012;()\'"=<>-/*'
    corpus += [''.join(rng.choice(alphabet) for _ in range(rng.randrange(1,150))) for _ in range(1000)]
    for sql in corpus:
        connection.file.write(json.dumps({'op':'query','sql':sql}).encode()+b'\n')
        connection.file.flush()
        assert not json.loads(connection.file.readline())['ok'], sql
    assert connection.query('SELECT COUNT(*) FROM events')==[[1000]]
    report['boundaries']['malformed_or_unsupported_statements_rejected_without_data_changes'] = len(corpus)
    # Distinct values exceed the documented group materialization guard, even LIMIT 1.
    for lo in range(0,150_001,10_000):
        connection.append([[i+1000,i,i+1000] for i in range(lo,min(lo+10_000,150_001))])
    connection.file.write(json.dumps({'op':'query','sql':'SELECT device, SUM(value) FROM events GROUP BY device LIMIT 1'}).encode()+b'\n')
    connection.file.flush()
    failure = json.loads(connection.file.readline())
    assert not failure['ok'] and 'budget' in failure['error'], failure
    assert connection.query('SELECT COUNT(*) FROM events')==[[151_001]]
    connection.call({'op':'verify'})
    report['boundaries']['group_budget_fails_explicitly_and_store_remains_healthy'] = True
    connection.close()
    engine.finish()

    # Flip a payload byte in an isolated fixture. Metadata-only totals can still
    # succeed by design; reading the page and the full scrub must reject it.
    segment = sorted((engine.directory/'archive').glob('segment-*.ks2'))[0]
    with segment.open('r+b') as file:
        header = file.read(16)
        offset = 16+struct.unpack('<I',header[8:12])[0]+1000*8+20*8
        file.seek(offset)
        original = file.read(1)
        file.seek(offset)
        file.write(bytes([original[0]^1]))
    engine.start_bridge(0)
    connection = engine.connect()
    metadata_result = connection.query('SELECT SUM(value) FROM events')
    failures = []
    for request in [{'op':'query','sql':'SELECT SUM(value) FROM events WHERE ts >= 10 AND ts < 30'}, {'op':'verify'}]:
        connection.file.write(json.dumps(request).encode()+b'\n')
        connection.file.flush()
        response = json.loads(connection.file.readline())
        assert not response['ok'] and 'checksum' in response['error'], response
        failures.append(response['error'])
    report['boundaries']['corrupt_payload'] = {'metadata_only_query_succeeds_by_design':metadata_result,
        'page_read_rejected':True,'full_scrub_rejected':True,'errors':failures}
    connection.close()
    engine.finish()
    output = args.output
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'report':str(output),'forced_kill_cycles_passed':len(report['cycles']),
        'boundaries':report['boundaries']},indent=2))


if __name__=='__main__':
    main()
