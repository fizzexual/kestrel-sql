"""Untimed bridge oracles for handle reuse, concurrent reads and warmed corruption."""
import concurrent.futures
import datetime
import hashlib
import json
import time
from pathlib import Path

from stress_compare import Engine

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
output = ROOT / 'benchmarks/reader-067-verification.json'
assert not output.exists()
binary = WORK / 'perf-067/candidate/kestrel-stress.exe'
directory = WORK / f'reader-067-bridge-{time.time_ns()}'
engine = Engine('kestrel', directory, 0, binary, {})
report = {'version': '0.3.17-dev.67', 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
          'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'methodology': 'Untimed manual Python integer oracles; eight local clients; task-owned bridge',
          'cases': [], 'complete': False}


def save():
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


data = [[i*17 % 9001 - batch*137, i*37 % 1000 - 500,
         2**63-1 if i % 3 == 0 else -(2**63)]
        for batch in range(4) for i in range(5003)]
thresholds = [-500, -17, 0, 127, 501]


def oracle(threshold):
    selected = [row for row in data if row[1] >= threshold]
    return [[len(selected), sum(row[1] for row in selected) if selected else None,
             sum(row[2] for row in selected) if selected else None]]


def sql(threshold):
    return f'SELECT COUNT(*), SUM(value), SUM(device) FROM events WHERE value >= {threshold}'


connection = engine.connect()
known = []
save()
try:
    assert engine.version == '0.3.17-dev.67'
    for batch in range(4):
        request = {'op': 'append', 'id': f'reader:known:{batch}', 'data': data[batch*5003:(batch+1)*5003]}
        receipt = connection.call(request)
        assert not receipt['duplicate']
        known.append((request, receipt['generation']))
    initial = connection.call({'op': 'stats'})
    assert initial['segments'] == 4 and initial['retained_stream_handles'] == 0
    for repeat in range(2):
        actual = connection.query(sql(0))
        assert actual == oracle(0) and type(actual[0][2]) is int
        report['cases'].append({'phase': 'warm', 'repeat': repeat, 'threshold': 0, 'exact_python_integer_oracle': True})
    warmed = connection.call({'op': 'stats'})
    assert warmed['retained_stream_handles'] == 4
    assert warmed['stream_handle_opens'] == 4 and warmed['stream_handle_reuses'] == 4
    assert connection.call({'op': 'verify'})['verified_bytes'] == len(data)*24
    scrubbed = connection.call({'op': 'stats'})
    assert all(scrubbed[k] == warmed[k] for k in ['retained_stream_handles', 'stream_handle_opens', 'stream_handle_reuses'])
    report['fresh_full_scrub_bypasses_handle_reuse'] = True
    save()

    def worker(worker_id):
        client = engine.connect()
        cases = []
        try:
            for turn in range(12):
                threshold = thresholds[(worker_id*7 + turn*3) % len(thresholds)]
                actual = client.query(sql(threshold))
                assert actual == oracle(threshold), (worker_id, turn, actual)
                assert actual[0][2] is None or type(actual[0][2]) is int
                cases.append({'phase': 'concurrent', 'client': worker_id, 'turn': turn,
                              'threshold': threshold, 'exact_python_integer_oracle': True})
        finally:
            client.close()
        return cases

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for cases in executor.map(worker, range(8)):
            report['cases'].extend(cases)
    concurrent = connection.call({'op': 'stats'})
    assert 0 < concurrent['retained_stream_handles'] <= 4
    assert concurrent['stream_handle_reuses'] > warmed['stream_handle_reuses']
    report['eight_clients_exact_wide_outputs_and_bounded_idle_handles'] = True
    save()

    segment = directory / 'archive/segment-00000000000000000001.ks2'
    original = segment.read_bytes()
    offset = 16 + int.from_bytes(original[8:12], 'little')
    damaged = bytearray(original)
    damaged[offset + 5003*8 + 123*8] ^= 1
    segment.write_bytes(damaged)
    try:
        connection.query(sql(0))
        raise AssertionError('warmed corruption was accepted')
    except RuntimeError as error:
        assert 'checksum mismatch' in str(error)
    try:
        connection.call({'op': 'verify'})
        raise AssertionError('corrupt full scrub was accepted')
    except RuntimeError as error:
        assert 'checksum mismatch' in str(error)
    assert connection.call({'op': 'stats'})['retained_stream_handles'] == 0
    segment.write_bytes(original)
    assert connection.query(sql(0)) == oracle(0)
    report['cases'].append({'phase': 'restored', 'threshold': 0, 'exact_python_integer_oracle': True})
    assert connection.call({'op': 'verify'})['verified_bytes'] == len(data)*24
    report['warm_corruption_rejected_and_idle_handles_invalidated'] = True
    connection.close()
    engine.reopen()
    connection = engine.connect()
    assert connection.call({'op': 'stats'})['retained_stream_handles'] == 0
    for request, generation in known:
        replay = connection.call(request)
        assert replay['duplicate'] and replay['generation'] == generation
    for threshold in thresholds:
        assert connection.query(sql(threshold)) == oracle(threshold)
        report['cases'].append({'phase': 'reopen', 'threshold': threshold, 'exact_python_integer_oracle': True})
    assert connection.call({'op': 'verify'})['verified_bytes'] == len(data)*24
    report['volatile_reuse_resets_on_reopen_and_known_receipts_survive'] = True
    report['rows'] = len(data)
    report['segments'] = 4
    report['confirmed_receipts'] = len(known)
    report['manual_sql_oracles'] = len(report['cases'])
    report.update(complete=True, completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save()
    print(json.dumps({k: v for k, v in report.items() if k != 'cases'}), flush=True)
finally:
    connection.close()
    engine.finish()
