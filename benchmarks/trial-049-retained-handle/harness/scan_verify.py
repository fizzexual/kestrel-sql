"""Independent SQL oracles for selectivity, filter order and partial-block scans."""
import argparse
import datetime
import hashlib
import json
import random
import sqlite3
import time
from pathlib import Path

import compare
from stress_compare import Engine

ROOT = Path('C:\\Users\\Frizer\\Documents\\Codex\\2026-10-05\\letys\\outputs\\kestrel-sql')
WORK = ROOT.parent.parent / 'work'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, default=Path('C:\\Users\\Frizer\\Documents\\Codex\\2026-10-05\\letys\\work\\perf-049\\bin\\kestrel-stress.exe'))
    parser.add_argument('--output', type=Path, default=Path('C:\\Users\\Frizer\\Documents\\Codex\\2026-10-05\\letys\\work\\perf-049') / 'scan-049-differential.json')
    args = parser.parse_args()
    assert not args.output.exists()
    import duckdb
    binary = args.binary.resolve()
    work = WORK / f'scan-046-differential-{time.time_ns()}'
    work.mkdir()
    rng = random.Random(40046)
    report = {
        'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'seed': 40046,
        'references': {'duckdb': duckdb.__version__, 'sqlite': sqlite3.sqlite_version},
        'methodology': 'Four overlapping sorted runs per fixture; three key/value distributions; independent reference SQL; six operators, reordered multiple filters, bounded partial blocks, empty/full selections; exact retry, reopen and scrub outside any timers',
        'cases': [], 'fixtures': [], 'complete': False,
    }

    def save():
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')

    for mode in ['dense', 'wide', 'skew']:
        engine = Engine('kestrel', work / mode, 0, binary, {})
        duck = duckdb.connect(':memory:')
        duck.execute('SET threads=1')
        sqlite = sqlite3.connect(':memory:')
        for db in [duck, sqlite]:
            db.execute('CREATE TABLE events (ts BIGINT, value BIGINT, device BIGINT)')
        known = []
        try:
            connection = engine.connect()
            for batch in range(4):
                data = []
                for row in range(8211):
                    ts = row - 1200 + batch * 1700
                    value = row * 37 % 2003 - 1001
                    if mode == 'skew':
                        value = [0, 0, 0, 0, 0, 0, 0, 0, -1001, 1001][row % 10]
                    key = row * 17 % 97 - 48
                    if mode == 'wide':
                        key = -(2**63) if row % 19 == 0 else 2**63 - 1 if row % 19 == 1 else (row % 19 - 9) * 1000003
                    data.append([ts, value, key])
                request = {'op': 'append', 'id': f'scan:{mode}:{batch}', 'data': data}
                receipt = connection.call(request)
                assert not receipt['duplicate']
                known.append((request, receipt['generation']))
                for db in [duck, sqlite]:
                    db.executemany('INSERT INTO events VALUES (?,?,?)', data)
            assert connection.call({'op': 'verify'})['verified_bytes'] == 32844 * 24
            for case in range(200):
                op = ['=', '<>', '<', '<=', '>', '>='][case % 6]
                threshold = [-1001, -1000, -1, 0, 1, 1000, 1001, -(2**63), 2**63-1][case % 9] if case % 3 else rng.randrange(-1002, 1003)
                lo = 2933 + rng.randrange(-300, 301)
                hi = 6979 + rng.randrange(-300, 301)
                predicate = f'value {op} {threshold}'
                forms = [
                    predicate,
                    f'{predicate} AND ts >= {lo} AND ts < {hi}',
                    f'ts >= {lo} AND {predicate} AND ts < {hi}',
                    f'device <> 0 AND ts >= {lo} AND ts < {hi} AND {predicate}',
                    f'{predicate} AND device <> 0 AND ts >= {lo} AND ts < {hi}',
                    f'ts >= {lo} AND ts < {lo} AND {predicate}',
                    f'{predicate} AND value >= -1001 AND device <> 0',
                ]
                expressions = 'COUNT(*) AS n, SUM(value) AS s, AVG(value), MIN(value), MAX(value), SUM(ts), SUM(value)'
                grouped = case % 2 == 0
                if grouped:
                    expressions = 'device AS k, ' + expressions
                sql = f'SELECT {expressions} FROM events WHERE {forms[case % 7]}'
                if grouped:
                    sql += ' GROUP BY device ORDER BY k'
                    if case % 4 == 0:
                        sql += ' DESC'
                if case % 17 == 0:
                    sql += f' LIMIT {case % 5}'
                actual = connection.query(sql)
                record = {'fixture': mode, 'case': case, 'sql': sql, 'result_rows': len(actual),
                    'duckdb_equal': compare.same(actual, duck.execute(sql).fetchall()),
                    'sqlite_equal': compare.same(actual, sqlite.execute(sql).fetchall()),
                    'result_sha256': hashlib.sha256(json.dumps(actual).encode()).hexdigest()}
                report['cases'].append(record)
                save()
                assert record['duckdb_equal'] and record['sqlite_equal'], record
            connection.close()
            engine.reopen()
            connection = engine.connect()
            for request, generation in [known[0], known[-1]]:
                receipt = connection.call(request)
                assert receipt['duplicate'] and receipt['generation'] == generation
            sql = 'SELECT device, COUNT(*), SUM(value) FROM events WHERE value >= 0 GROUP BY device ORDER BY device'
            actual = connection.query(sql)
            assert compare.same(actual, duck.execute(sql).fetchall()) and compare.same(actual, sqlite.execute(sql).fetchall())
            assert connection.call({'op': 'verify'})['verified_bytes'] == 32844 * 24
            connection.close()
            report['fixtures'].append({'mode': mode, 'rows': 32844, 'queries': 200,
                'reopen_retry_and_scrub_passed': True})
            save()
            print(json.dumps(report['fixtures'][-1]), flush=True)
        finally:
            engine.finish()
            duck.close()
            sqlite.close()
    report.update(complete=True, queries_checked_against_each_reference=len(report['cases']),
        completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save()


if __name__ == '__main__':
    main()
