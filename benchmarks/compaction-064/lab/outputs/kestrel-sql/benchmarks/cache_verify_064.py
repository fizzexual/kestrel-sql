"""Independent SQL oracles for low-bit, multiplier-adversarial, signed and cache-limit keys."""
import datetime
import hashlib
import json
import random
import sqlite3
import time
from pathlib import Path
import duckdb
import compare
from stress_compare import Engine

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
output = ROOT / 'benchmarks/cache-064-differential.json'
assert not output.exists()
binary = WORK / 'perf-064/candidate/kestrel-stress.exe'
work = WORK / f'cache-064-differential-{time.time_ns()}'; work.mkdir()
rng = random.Random(39064)
report = {'version': '0.3.17-dev.64', 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
    'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'seed': 39064,
    'references': {'duckdb': duckdb.__version__, 'sqlite': sqlite3.sqlite_version},
    'methodology': 'Eight overlapping sorted append runs per mode; independent DuckDB and SQLite SQL results; no performance timing',
    'cases': [], 'modes': [], 'complete': False}
mask = (1 << 64) - 1
report['index_characterization'] = {
    'method': 'Pure integer slot calculation, not engine timings or a compiled fixed-multiplier trial',
    'fixtures': []}
for label,spacing in [('old_collision19',999936),('fibonacci19',832040),('power19',524288)]:
    keys = [i*spacing-9 for i in range(19)]
    old_slots = [((k & mask) ^ ((k & mask) >> 32)) & 255 for k in keys]
    fixed_slots = [(((k & mask)*0x9e3779b97f4a7c15) & mask) >> 56 for k in keys]
    report['index_characterization']['fixtures'].append({'name':label,'keys':keys,
        'old_slots':old_slots,'old_distinct_slots':len(set(old_slots)),
        'fixed_golden_slots':fixed_slots,'fixed_golden_distinct_slots':len(set(fixed_slots))})
def save(): output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
for mode in ['fold-collision', 'fibonacci-step', 'signed-powers', 'over-cache-limit']:
    directory = work / mode
    engine = Engine('kestrel', directory, 0, binary, {})
    reference = duckdb.connect()
    reference.execute('SET threads=1')
    reference.execute("SET memory_limit='256MB'")
    domains = {'fold-collision':19, 'fibonacci-step':19, 'signed-powers':31, 'over-cache-limit':129}
    steps = {'fold-collision':999936, 'fibonacci-step':832040, 'over-cache-limit':999936}
    domain = domains[mode]
    key_sql = (f'(i%{domain}-{domain//2})*{steps[mode]}' if mode != 'signed-powers' else
        'CASE WHEN i%31=0 THEN -9223372036854775808 WHEN i%31=1 THEN 9223372036854775807 ELSE -9223372036854775808+(i%31)*72057594037927936 END')
    reference.execute(f'CREATE TABLE events AS SELECT ((i*17)%6007-b*97)::BIGINT AS ts, ((i*37)%1000-500)::BIGINT AS value, ({key_sql})::BIGINT AS device FROM range(5003) a(i), range(8) z(b)')
    sqlite = sqlite3.connect(':memory:')
    sqlite.execute('CREATE TABLE events (ts BIGINT, value BIGINT, device BIGINT)')
    known = []
    try:
        connection = engine.connect()
        for batch in range(8):
            data = []
            for i in range(5003):
                k = i % domain
                key = ((k-domain//2)*steps[mode] if mode != 'signed-powers' else
                    -(2**63) if k == 0 else 2**63-1 if k == 1 else -(2**63)+k*(2**56))
                data.append([i*17%6007-batch*97, i*37%1000-500, key])
            request = {'op': 'append', 'id': f'differential:{mode}:{batch}', 'data': data}
            receipt = connection.call(request); assert not receipt['duplicate']
            known.append((request, receipt['generation']))
            sqlite.executemany('INSERT INTO events VALUES (?,?,?)', data)
        assert reference.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 40024
        assert connection.call({'op': 'verify'})['verified_bytes'] == 40024*24
        for case in range(150):
            lo = rng.randrange(-800, 6000); hi = lo + rng.randrange(0, 1501)
            threshold = rng.randrange(-501, 501)
            forms = [
                '', f' WHERE ts >= {lo} AND ts < {hi}', f' WHERE value >= {threshold}',
                f' WHERE ts >= {lo} AND value < {threshold}', ' WHERE ts < -1000000',
                ' WHERE device = -9223372036854775808', ' WHERE device != 9223372036854775807',
                f' WHERE ts >= {lo} AND ts < {hi} AND value != {threshold}',
            ]
            where = forms[case % len(forms)]
            expressions = [
                'device AS k, COUNT(*) AS n, SUM(value) AS s, AVG(value), MIN(value), MAX(value), SUM(ts), SUM(value)',
                'SUM(value) AS s, device AS k, AVG(value), COUNT(*), SUM(ts)',
                'device AS k, COUNT(*), MIN(ts), MAX(ts)', 'device AS k',
            ][case % 4]
            sql = f'SELECT {expressions} FROM events{where} GROUP BY device ORDER BY k'
            if case % 3 == 1: sql += ' DESC'
            if case % 17: sql += f' LIMIT {case%32}'
            actual = connection.query(sql)
            duck_rows = reference.execute(sql).fetchall()
            sqlite_rows = sqlite.execute(sql).fetchall()
            record = {'mode': mode, 'case': case, 'sql': sql,
                'duckdb_equal': compare.same(actual, duck_rows), 'sqlite_equal': compare.same(actual, sqlite_rows),
                'result_rows': len(actual), 'result_sha256': hashlib.sha256(json.dumps(actual).encode()).hexdigest()}
            report['cases'].append(record); save()
            assert record['duckdb_equal'] and record['sqlite_equal'], record
        connection.close(); engine.reopen(); connection = engine.connect()
        for request, generation in [known[0], known[-1]]:
            replay = connection.call(request)
            assert replay['duplicate'] and replay['generation'] == generation
        sql = 'SELECT device, COUNT(*), SUM(value), AVG(value), MIN(value), MAX(value) FROM events GROUP BY device ORDER BY device'
        actual = connection.query(sql)
        assert compare.same(actual, reference.execute(sql).fetchall()) and compare.same(actual, sqlite.execute(sql).fetchall())
        assert connection.call({'op': 'verify'})['verified_bytes'] == 40024*24
        connection.close()
        report['modes'].append({'mode': mode, 'rows': 40024, 'queries': 150, 'reopen_replay_and_scrub_passed': True})
        save()
        print(json.dumps(report['modes'][-1]), flush=True)
    finally:
        engine.finish(); reference.close(); sqlite.close()
report.update(complete=True, queries_checked_against_each_reference=len(report['cases']),
    completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save()
