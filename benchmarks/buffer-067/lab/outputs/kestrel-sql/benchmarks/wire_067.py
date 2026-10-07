"""Exact wide signed sparse aggregates through archive/RAM CLI and TCP bridge."""
import datetime
import hashlib
import json
import struct
import subprocess
import time
from pathlib import Path
from stress_compare import Engine

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
output = ROOT / 'benchmarks/wire-067-audit.json'
assert not output.exists()
work = WORK / f'wire-067-{time.time_ns()}'; work.mkdir()
cli = WORK / 'perf-067/candidate/kestrel.exe'
bridge = WORK / 'perf-067/candidate/kestrel-stress.exe'
data = [[i * 2 + turn, value, key] for i in range(3) for turn, (key, value) in
        enumerate([(-(2**63), 2**63-1), (2**63-1, -(2**63))])]
expected = [[key, 3, value*3, float(value), value, value, value*3] for key, value in
            [(-(2**63), 2**63-1), (2**63-1, -(2**63))]]
sql = 'SELECT device, COUNT(*), SUM(value), AVG(value), MIN(value), MAX(value), SUM(value) FROM events GROUP BY device ORDER BY device'
raw = work / 'rows.i64'; raw.write_bytes(b''.join(struct.pack('<qqq', *row) for row in data))
imported = json.loads(subprocess.check_output([str(cli), '--archive', str(work/'archive'), '--import-i64', str(raw)], text=True))
assert imported['ok'] and imported['verified_bytes'] == 144
archive = json.loads(subprocess.check_output([str(cli), '--archive', str(work/'archive'), '--sql', sql], text=True))
assert archive['ok'] and archive['result']['rows'] == expected
assert archive['result']['plan'] == 'streamed-hash-group'
memory = 'CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL);\n'
memory += 'INSERT INTO events VALUES ' + ','.join('('+','.join(map(str, row))+')' for row in data) + ';\n' + sql + ';\n'
responses = subprocess.check_output([str(cli)], input=memory, text=True).splitlines()
assert json.loads(responses[-1])['result']['rows'] == expected
engine = Engine('kestrel', work/'bridge', 0, bridge, {})
try:
    connection = engine.connect()
    request = {'op': 'append', 'id': 'wide:sparse:known', 'data': data}
    receipt = connection.call(request); assert not receipt['duplicate']
    assert connection.query(sql) == expected
    try: connection.query('SELECT SUM(missing) FROM events')
    except RuntimeError: pass
    else: raise AssertionError('invalid query accepted')
    assert connection.query(sql) == expected
    connection.close(); engine.reopen(); connection = engine.connect()
    replay = connection.call(request)
    assert replay['duplicate'] and replay['generation'] == receipt['generation']
    assert connection.query(sql) == expected and connection.call({'op': 'verify'})['verified_bytes'] == 144
    connection.close()
finally: engine.finish()
proof = {'version': '0.3.17-dev.67', 'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'cli_sha256': hashlib.sha256(cli.read_bytes()).hexdigest(), 'bridge_sha256': hashlib.sha256(bridge.read_bytes()).hexdigest(),
    'exact_positive_and_negative_wide_archive_json': True, 'exact_wide_ram_json': True,
    'sparse_bridge_error_continuity_retry_reopen_and_scrub': True, 'signed_extrema_and_repeated_sum_avg_outputs': True}
output.write_text(json.dumps(proof, indent=2)+'\n')
print(json.dumps(proof), flush=True)
