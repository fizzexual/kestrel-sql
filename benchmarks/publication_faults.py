"""CAT4 cut points using a separate feature-enabled driver and default recovery.

Process exits and injected disk-full OS errors occur on a live filesystem. These
are not power failures or actual device exhaustion. No supported binary has hooks.
"""
import argparse
import hashlib
import json
import os
import shutil
import struct
import subprocess
import time
import zlib
from pathlib import Path

from stress_compare import Engine

ROOT = Path(__file__).resolve().parents[1]
POINTS = ['segment_partial', 'segment_written', 'segment_synced', 'catalog_partial',
          'catalog_written', 'catalog_synced', 'catalog_published']


def write_catalog(path, body):
    data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
    path.write_bytes(b'KSQLCAT4'+struct.pack('<II', len(data), zlib.crc32(data))+data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--sql-binary', type=Path, required=True)
    parser.add_argument('--fault-driver', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.binary, args.sql_binary, args.fault_driver = [p.resolve() for p in [args.binary, args.sql_binary, args.fault_driver]]
    work = ROOT.parent.parent/'work'/f'catalog-faults-{time.time_ns()}'
    work.mkdir()
    report = {'fault_model': 'separate feature-enabled driver; process exit at seven publication cut points and injected disk-full OS errors; live OS/filesystem; default non-instrumented binaries reopen/retry; no physical power-loss or actual disk-full claim',
              'binary_sha256': hashlib.sha256(args.binary.read_bytes()).hexdigest(),
              'sql_binary_sha256': hashlib.sha256(args.sql_binary.read_bytes()).hexdigest(),
              'fault_driver_sha256': hashlib.sha256(args.fault_driver.read_bytes()).hexdigest(),
              'cut_points': [], 'corruption_cases': []}

    def save():
        args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')

    sources = {}
    for count in [3, 32]:
        directory = work/f'source-{count}'
        engine = Engine('kestrel', directory, 0, args.binary, {})
        try:
            assert engine.version == '0.3.3'
            connection = engine.connect()
            for i in range(count):
                receipt = connection.call({'op': 'append', 'id': f'seed:{i}', 'data': [[i, i*2, 1]]})
                assert not receipt['duplicate'] and receipt['generation'] == i+1
            stats = connection.call({'op': 'stats'})
            assert stats['catalog_chain_files'] == count and stats['recorded_batch_ids'] == count
            connection.close()
        finally:
            engine.finish()
        sources[count] = directory
    scenarios = [('append_delta', 3, 'append'), ('append_checkpoint', 32, 'append'),
                 ('compact_delta', 3, 'compact'), ('compact_checkpoint', 32, 'compact')]
    for scenario, count, action in scenarios:
        for point in POINTS:
            for mode in ['exit', 'io_error']:
                directory = work/f'{scenario}-{point}-{mode}'
                shutil.copytree(sources[count], directory)
                environment = {**os.environ, 'KESTREL_FAULT_POINT': point, 'KESTREL_FAULT_MODE': mode}
                failure = subprocess.run([str(args.fault_driver), str(directory/'archive'), action],
                                         env=environment, text=True, capture_output=True, timeout=30)
                assert failure.returncode == (86 if mode == 'exit' else 87), (scenario, point, mode, failure)
                if mode == 'io_error':
                    assert 'poisoned writer; old snapshot readable' in failure.stderr
                engine = Engine('kestrel', directory, 0, args.binary, {}, existing=True)
                try:
                    connection = engine.connect()
                    published = point == 'catalog_published'
                    extra = 10_000 if action == 'append' and published else 0
                    assert connection.query('SELECT COUNT(*), SUM(value) FROM events') == [[count+extra, count*(count-1)+extra*7]]
                    for i in range(count):
                        receipt = connection.call({'op': 'append', 'id': f'seed:{i}', 'data': [[i, i*2, 1]]})
                        assert receipt['duplicate'] and receipt['generation'] == i+1
                    stats = connection.call({'op': 'stats'})
                    assert stats['generation'] == count+int(published)
                    assert stats['catalog_chain_files'] == (1 if count == 32 and published else count+int(published))
                    if action == 'append':
                        request = {'op': 'append', 'id': 'fault:target', 'data': [[1000, 7, 1]]*10_000}
                        assert connection.call(request)['duplicate'] == published
                        assert connection.call(request)['duplicate']
                        assert connection.query('SELECT COUNT(*), SUM(value) FROM events') == [[count+10_000, count*(count-1)+70_000]]
                    verified = connection.call({'op': 'verify'})['verified_bytes']
                    assert verified == (count+(10_000 if action == 'append' else 0))*24
                    connection.close()
                finally:
                    engine.finish()
                report['cut_points'].append({'scenario': scenario, 'point': point, 'mode': mode,
                    'returncode': failure.returncode, 'published_before_retry': published,
                    'original_receipts_preserved': True, 'atomic_rows_and_sum': True,
                    'retry_deduplication_passed': True, 'full_scrub_passed': True,
                    'writer_poison_and_pinned_read_passed': mode == 'io_error'})
                save()
        print(json.dumps({'scenario': scenario, 'cut_point_cases_passed': 14}), flush=True)

    # Every header truncation, selected body truncations, excess chain depth and
    # duplicate keys inside one otherwise valid checksummed JSON envelope.
    root_catalog = sources[3]/'archive'/'catalog-00000000000000000001.ks2'
    data = root_catalog.read_bytes()
    lengths = sorted(set([*range(17), 20, len(data)//2, len(data)-1]))
    corruptions = [('root_truncation', n) for n in lengths] + [('excess_chain', None), ('duplicate_key', None)]
    for index, (damage, length) in enumerate(corruptions):
        count = 32 if damage == 'excess_chain' else 3
        directory = work/f'corruption-{index}'
        shutil.copytree(sources[count], directory)
        if damage == 'root_truncation':
            (directory/'archive'/root_catalog.name).write_bytes(data[:length])
        elif damage == 'excess_chain':
            file = directory/'archive'/'catalog-00000000000000000032.ks2'
            body = json.loads(file.read_bytes()[16:])
            body['generation'], body['receipt_base'] = 33, 32
            body['batches'] = {'excess': {'digest': [0]*32, 'rows': 1, 'generation': 33}}
            write_catalog(directory/'archive'/'catalog-00000000000000000033.ks2', body)
        else:
            file = directory/'archive'/'catalog-00000000000000000003.ks2'
            body = json.loads(file.read_bytes()[16:])
            key, record = next(iter(body['batches'].items()))
            pair = json.dumps(key)+':'+json.dumps(record)
            text = json.dumps(body).replace(json.dumps(body['batches']), '{'+pair+','+pair+'}', 1)
            write_catalog(file, text)
        rejected = subprocess.run([str(args.sql_binary), '--archive', str(directory/'archive'), '--sql', 'SELECT COUNT(*) FROM events'], text=True, capture_output=True, timeout=30)
        assert rejected.returncode != 0, (damage, length, rejected.stdout)
        report['corruption_cases'].append({'damage': damage, 'length': length, 'rejected': True, 'error': rejected.stderr.strip()})
        save()
    assert len(report['cut_points']) == 56 and len(report['corruption_cases']) == len(corruptions)
    print(json.dumps({'report': str(args.output), 'cut_points_passed': 56, 'corruption_cases_passed': len(corruptions)}))


if __name__ == '__main__':
    main()
