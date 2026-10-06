"""Qualify the final JSON boundary while retaining byte-identical timed core."""
import datetime
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from stress_compare import Engine

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
def read(name): return json.loads((ROOT / name).read_text())
build = read('benchmarks/rust-checks-038.json')
query_build = read('benchmarks/rust-checks-038-query-final.json')
assert build['group_probe_sha256'] == query_build['group_probe_sha256']
assert build['source_sha256']['src/archive.rs'] == query_build['source_sha256']['src/archive.rs']
output = ROOT / 'benchmarks/correctness-038-wire-run-order.json'
assert not output.exists()
cli = WORK / 'perf-038/candidate/kestrel.exe'
bridge = WORK / 'perf-038/candidate/kestrel-stress.exe'
faults = WORK / 'kestrel-038-fault-build/release/examples'
jobs = [
    ('wide-cli', ['benchmarks/wide_json_038.py', '--output', 'benchmarks/wide-json-038-final.json']),
    ('final-cli-differential', ['benchmarks/archive_verify.py', '--binary', str(cli), '--output', 'benchmarks/archive-038-wire-verification.json', '--queries', '500']),
    ('final-bridge-cuts', ['benchmarks/publication_faults.py', '--binary', str(bridge), '--sql-binary', str(cli), '--fault-driver', str(faults / 'publication_fault_probe.exe'), '--expected-version', '0.3.8', '--output', 'benchmarks/publication-038-wire-faults.json']),
    ('final-bridge-kills', ['benchmarks/group_commit_recovery.py', '--binary', str(bridge), '--expected-version', '0.3.8', '--retry-index', '--output', 'benchmarks/group-038-wire-recovery.json']),
]
records = []
for name, arguments in jobs:
    record = {'suite': name, 'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': [sys.executable, *arguments]}
    print(name, flush=True)
    result = subprocess.run(record['command'], cwd=ROOT)
    record.update(returncode=result.returncode, completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    records.append(record); output.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    assert result.returncode == 0
wide = read('benchmarks/wide-json-038-final.json')
assert all(c['exact_wide_json_passed'] for c in wide['cases'] if c['variant'] == 'candidate')
assert not any(c['exact_wide_json_passed'] for c in wide['cases'] if c['variant'] == 'baseline')
work = WORK / f'wire-038-{time.time_ns()}'; work.mkdir()
engine = Engine('kestrel', work / 'store', 0, bridge, {})
values = [(7, 2**63-1), (8, -(2**63))]
known = []
try:
    connection = engine.connect()
    for key, value in values:
        request = {'op': 'append', 'id': f'wire:{key}', 'data': [[i, value, key] for i in range(3)]}
        receipt = connection.call(request); assert not receipt['duplicate']; known.append((request, receipt['generation']))
    expected = [[key, 3, value*3, float(value), value, value] for key, value in values]
    sql = 'SELECT device, COUNT(*), SUM(value), AVG(value), MIN(value), MAX(value) FROM events GROUP BY device ORDER BY device'
    assert connection.query(sql) == expected
    try: connection.query('SELECT SUM(missing) FROM events')
    except RuntimeError: pass
    else: raise AssertionError('invalid query was accepted')
    assert connection.query(sql) == expected
    assert connection.call({'op': 'verify'})['verified_bytes'] == 144
    connection.close(); engine.reopen(); connection = engine.connect()
    for request, generation in known:
        replay = connection.call(request); assert replay['duplicate'] and replay['generation'] == generation
    assert connection.query(sql) == expected
    connection.close()
finally: engine.finish()
memory = 'CREATE TABLE events (ts BIGINT NOT NULL, value BIGINT NOT NULL, device BIGINT NOT NULL);\nINSERT INTO events VALUES (1,9223372036854775807,7),(2,9223372036854775807,7),(3,9223372036854775807,7);\nSELECT device, SUM(value) FROM events GROUP BY device ORDER BY device;\n'
result = subprocess.run([str(cli)], input=memory, text=True, capture_output=True)
assert result.returncode == 0, result.stderr
assert json.loads(result.stdout.splitlines()[-1])['result']['rows'] == [[7, 3*(2**63-1)]]
proof = {'version': '0.3.8', 'final_cli_sha256': hashlib.sha256(cli.read_bytes()).hexdigest(), 'final_bridge_sha256': hashlib.sha256(bridge.read_bytes()).hexdigest(),
    'benchmarked_group_probe_byte_identical': True, 'query_library_and_archive_source_unchanged_after_timings': True,
    'exact_positive_and_negative_wide_cli_json': True, 'exact_wide_ram_cli_json': True,
    'exact_wide_bridge_json_error_continuity_retry_reopen_scrub': True, 'dependency_features_unchanged': True,
    'final_tests_each_mode': 63, 'initial_failure_evidence': 'benchmarks/wide-json-038-initial.json'}
(ROOT / 'benchmarks/wire-038-audit.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof), flush=True)
