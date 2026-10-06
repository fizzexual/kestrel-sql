"""Seeded independent SQL oracles for fused dense sums, averages, counts and signed boundaries."""
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
output = ROOT / 'benchmarks/dense-044-differential.json'
assert not output.exists()
binary = WORK / 'perf-044/candidate/kestrel-stress.exe'
work = WORK / f'dense-044-differential-{time.time_ns()}'; work.mkdir()
rng = random.Random(39044)
report = {'version': '0.3.14', 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
    'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'seed': 39044,
    'references': {'duckdb': duckdb.__version__, 'sqlite': sqlite3.sqlite_version},
    'methodology': 'Eight overlapping sorted append runs per mode; independent DuckDB and SQLite SQL results; no performance timing',
    'cases': [], 'modes': [], 'complete': False}
def save(): output.write_text(json.dumps(report, indent=2)+'\n',encoding='utf-8')
for mode in ['dense97','expanded5003','signed-min137','signed-max137']:
    directory = work / mode
    engine = Engine('kestrel', directory, 0, binary, {})
    reference = duckdb.connect()
    reference.execute('SET threads=1')
    reference.execute("SET memory_limit='256MB'")
    key_sql={'dense97':'(i*17)%97-48','expanded5003':'i%5003-2501','signed-min137':'-9223372036854775808+(i*17)%137','signed-max137':'9223372036854775671+(i*17)%137'}[mode]
    reference.execute(f'CREATE TABLE events AS SELECT ((i*17)%6007-b*97)::BIGINT AS ts, ((i*37)%1000-500)::BIGINT AS value, ({key_sql})::BIGINT AS device FROM range(5003) a(i), range(8) z(b)')
    sqlite = sqlite3.connect(':memory:')
    sqlite.execute('CREATE TABLE events (ts BIGINT, value BIGINT, device BIGINT)')
    known = []
    try:
        connection = engine.connect()
        for batch in range(8):
            data = []
            for i in range(5003):
                k = i % 41
                key={'dense97':i*17%97-48,'expanded5003':i%5003-2501,'signed-min137':-(2**63)+i*17%137,'signed-max137':2**63-1-136+i*17%137}[mode]
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
            group_column='ts' if case%11==0 else 'device'
            sum_column=['value','ts','device' if mode in ['dense97','expanded5003'] else 'ts'][case%3]
            expressions = [
                f'{group_column} AS k, COUNT(*) AS n, SUM({sum_column}) AS s, AVG({sum_column}), SUM({sum_column})',
                f'SUM({sum_column}) AS s, {group_column} AS k, AVG({sum_column}), COUNT(*)',
                f'COUNT(*), {group_column} AS k, SUM({sum_column}), SUM({sum_column}), AVG({sum_column})',
                f'{group_column} AS k, SUM({sum_column}) AS s',
            ][case%4]
            sql = f'SELECT {expressions} FROM events{where} GROUP BY {group_column} ORDER BY k'
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
        sql = 'SELECT device, COUNT(*), SUM(value), AVG(value), SUM(value) FROM events GROUP BY device ORDER BY device'
        actual = connection.query(sql)
        assert compare.same(actual, reference.execute(sql).fetchall()) and compare.same(actual, sqlite.execute(sql).fetchall())
        assert connection.call({'op': 'verify'})['verified_bytes'] == 40024*24
        connection.close()
        report['modes'].append({'mode': mode, 'rows': 40024, 'queries': 150, 'reopen_replay_and_scrub_passed': True})
        save()
        print(json.dumps(report['modes'][-1]), flush=True)
    finally:
        engine.finish(); reference.close(); sqlite.close()
# Exact wide SUM JSON on both dense signed-boundary domains, after three confirmed batches.
report['wide_dense_checks']=[]
for label,base in [('min',-(2**63)),('max',2**63-1-136)]:
    directory=work/('wide-'+label)
    engine=Engine('kestrel',directory,0,binary,{})
    data=[[i,(2**63-1) if (i*17%137)%2==0 else -(2**63),base+i*17%137] for i in range(411)]
    expected=[[base+k,3,((2**63-1) if k%2==0 else -(2**63))*3,
        float(((2**63-1) if k%2==0 else -(2**63))*3)/3,
        ((2**63-1) if k%2==0 else -(2**63))*3] for k in range(137)]
    sql='SELECT device, COUNT(*), SUM(value), AVG(value), SUM(value) FROM events GROUP BY device ORDER BY device'
    known=[]
    try:
        connection=engine.connect()
        for lo in range(0,len(data),137):
            request={'op':'append','id':f'dense:{label}:{lo}','data':data[lo:lo+137]}
            receipt=connection.call(request);assert not receipt['duplicate']
            known.append((request,receipt['generation']))
        result=connection.call({'op':'query','sql':sql})
        assert result['plan']=='streamed-dense-group' and result['rows']==expected
        assert all(type(row[2]) is int and type(row[4]) is int for row in result['rows'])
        connection.close();engine.reopen();connection=engine.connect()
        for request,generation in known:
            replay=connection.call(request);assert replay['duplicate'] and replay['generation']==generation
        assert connection.query(sql)==expected and connection.call({'op':'verify'})['verified_bytes']==411*24
        connection.close()
        report['wide_dense_checks'].append({'boundary':label,'rows':411,'groups':137,'exact_i128_json':True,'confirmed_retry_reopen_and_scrub':True})
        save()
    finally:engine.finish()
report.update(complete=True, queries_checked_against_each_reference=len(report['cases']),
    completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
save()
