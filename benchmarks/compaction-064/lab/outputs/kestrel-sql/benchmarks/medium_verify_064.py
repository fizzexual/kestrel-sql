"""Independent SQL oracles for medium, irregular, late-growing and wide signed groups."""
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
output = ROOT / 'benchmarks/medium-064-differential.json'
assert not output.exists()
binary = WORK / 'perf-064/candidate/kestrel-stress.exe'
work = WORK / f'medium-064-differential-{time.time_ns()}'; work.mkdir()
rng = random.Random(39064)
report = {'version': '0.3.17-dev.64', 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
    'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'seed': 39064,
    'references': {'duckdb': duckdb.__version__, 'sqlite': sqlite3.sqlite_version},
    'methodology': 'Eight overlapping sorted append runs per mode; independent DuckDB and SQLite SQL results; no performance timing',
    'cases': [], 'modes': [], 'complete': False}
def save(): output.write_text(json.dumps(report, indent=2)+'\n',encoding='utf-8')
for mode in ['irregular5003', 'late-growth8193', 'high9001']:
    directory = work / mode
    engine = Engine('kestrel', directory, 0, binary, {})
    reference = duckdb.connect()
    reference.execute('SET threads=1')
    reference.execute("SET memory_limit='256MB'")
    import csv
    key_rng = random.Random(42064)
    keymap = [-(2**63),2**63-1]
    while len(keymap)<9001:
        k=key_rng.randrange(-(2**63),2**63)
        if k not in keymap: keymap.append(k)
    def key_for(i,batch):
        if mode=='irregular5003': return keymap[(i*17)%5003]
        if mode=='late-growth8193': return keymap[i%129] if batch<2 else keymap[(i+batch*4129)%8193]
        return keymap[(i+batch*5003)%9001]
    all_data = [[i*17%6007-batch*97,i*37%1000-500,key_for(i,batch)] for batch in range(8) for i in range(5003)]
    directory.mkdir(parents=True,exist_ok=True)
    csv_file=directory/'reference-input.csv'
    with csv_file.open('w',newline='',encoding='utf-8') as stream: csv.writer(stream).writerows(all_data)
    reference.execute("CREATE TABLE events AS SELECT * FROM read_csv(?, header=false, columns={'ts':'BIGINT','value':'BIGINT','device':'BIGINT'})",[str(csv_file)])
    sqlite = sqlite3.connect(':memory:')
    sqlite.execute('CREATE TABLE events (ts BIGINT, value BIGINT, device BIGINT)')
    known = []
    try:
        connection = engine.connect()
        for batch in range(8):
            data = all_data[batch*5003:(batch+1)*5003]
            request = {'op': 'append', 'id': f'differential:{mode}:{batch}', 'data': data}
            receipt = connection.call(request); assert not receipt['duplicate']
            known.append((request, receipt['generation']))
            sqlite.executemany('INSERT INTO events VALUES (?,?,?)', data)
        assert reference.execute('SELECT COUNT(*) FROM events').fetchone()[0] == 40024
        assert connection.call({'op': 'verify'})['verified_bytes'] == 40024*24
        for case in range(200):
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
        report['modes'].append({'mode': mode, 'rows': 40024, 'queries': 200, 'reopen_replay_and_scrub_passed': True})
        save()
        print(json.dumps(report['modes'][-1]), flush=True)
    finally:
        engine.finish(); reference.close(); sqlite.close()
# Exact i128 bridge output after medium-cardinality promotion, replay and reopen.
directory = work/'wide-json'
engine = Engine('kestrel',directory,0,binary,{})
keys = keymap[:5003]
data = [[i,(2**63-1) if (i%5003)%2==0 else -(2**63),keys[i%5003]] for i in range(15009)]
requests=[{'op':'append','id':f'medium:wide:{lo}','data':data[lo:lo+5003]} for lo in range(0,len(data),5003)]
expected=sorted([[key,3,((2**63-1) if j%2==0 else -(2**63))*3] for j,key in enumerate(keys)])
sql='SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device'
try:
    connection=engine.connect(); known=[]
    for request in requests:
        receipt=connection.call(request); assert not receipt['duplicate']
        known.append((request,receipt['generation']))
    actual=connection.query(sql)
    assert actual==expected and all(type(row[2]) is int for row in actual)
    connection.close(); engine.reopen(); connection=engine.connect()
    for request,generation in known:
        replay=connection.call(request)
        assert replay['duplicate'] and replay['generation']==generation
    actual=connection.query(sql)
    assert actual==expected and all(type(row[2]) is int for row in actual)
    assert connection.call({'op':'verify'})['verified_bytes']==len(data)*24
    connection.close()
finally: engine.finish()
report['exact_medium_signed_wide_group_json_and_reopen_retry']=True
report.update(complete=True, queries_checked_against_each_reference=len(report['cases']),
    completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save()
