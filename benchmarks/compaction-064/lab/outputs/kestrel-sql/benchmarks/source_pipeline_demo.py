"""Executed Parquet ingestion with atomic archive-local source offsets; no Kafka connector."""
import argparse
import hashlib
import json
import random
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Adapter:
    def __init__(self, binary, directory):
        self.process = subprocess.Popen([str(binary), str(directory)], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.closed = False

    def call(self, **request):
        self.process.stdin.write(json.dumps(request, separators=(',', ':')) + '\n')
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        assert line, ('adapter stopped', self.process.poll())
        response = json.loads(line)
        if not response['ok']: raise RuntimeError(response['error'])
        return response['value']

    def finish(self):
        if self.closed: return
        if self.process.poll() is None:
            self.process.stdin.close()
            try: self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill(); self.process.wait(timeout=5)
        stderr = self.process.stderr.read()
        self.process.stdout.close(); self.process.stderr.close()
        self.closed = True
        assert self.process.returncode == 0, stderr


def main():
    import duckdb
    parser = argparse.ArgumentParser()
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected-version', default='0.3.7')
    args = parser.parse_args()
    assert not args.output.exists()
    work = ROOT.parent.parent / 'work' / f'source-pipeline-{time.time_ns()}'
    work.mkdir()
    db = duckdb.connect()
    db.execute('SET threads=1')
    db.execute('CREATE TABLE base AS SELECT i::BIGINT AS ts, ((i*37)%1000-500)::BIGINT AS "value", ((i*17)%97)::BIGINT AS device FROM range(25000) t(i)')
    db.execute('CREATE TABLE late AS SELECT ((i*13)%5000)::BIGINT AS ts, ((i*11)%1000-500)::BIGINT AS "value", ((i*7)%97)::BIGINT AS device FROM range(5000) t(i)')
    sources = []
    for name in ['base', 'late']:
        filename = work / (name + '.parquet')
        db.execute(f'COPY {name} TO ? (FORMAT PARQUET)', [str(filename)])
        identity = 'parquet:sha256:' + hashlib.sha256(filename.read_bytes()).hexdigest()
        rows = db.execute('SELECT ts,value,device FROM read_parquet(?)', [str(filename)]).fetchall()
        sources.append((identity, rows))
    adapter = Adapter(args.binary.resolve(), work / 'archive')
    report = {'binary_sha256': hashlib.sha256(args.binary.read_bytes()).hexdigest(),
        'workflow': 'two Parquet sources; source-content identities; half-open row offsets; atomically published data/position; replay, rejected gap/conflict, late backfill, reopen and SQL oracle',
        'imports': [], 'positions': []}
    try:
        for identity, rows in sources:
            for replay in [False, True]:
                duplicates = 0
                for start in range(0, len(rows), 100):
                    columns = [list(column) for column in zip(*rows[start:start+100])]
                    receipt = adapter.call(op='commit', source=identity, start=start, next=min(start+100, len(rows)), columns=columns)
                    assert receipt['duplicate'] == replay and receipt['rows'] == len(columns[0])
                    duplicates += receipt['duplicate']
                    if not replay and (start//100+1) % 32 == 0: adapter.call(op='maintenance')
                position = adapter.call(op='position', source=identity)
                assert position['next_offset'] == len(rows)
                report['imports'].append({'source': identity, 'rows': len(rows), 'batches': len(rows)//100, 'duplicates': duplicates})
            report['positions'].append(adapter.call(op='position', source=identity))
        identity, rows = sources[0]
        changed = [list(column) for column in zip(*rows[:100])]; changed[1][0] += 1
        for start, next_offset, columns, expected_error in [(0, 100, changed, 'different content'),
                (25001, 25101, [list(column) for column in zip(*rows[:100])], 'offset is not current')]:
            try:
                adapter.call(op='commit', source=identity, start=start, next=next_offset, columns=columns)
                raise AssertionError('invalid source commit accepted')
            except RuntimeError as error: assert expected_error in str(error)
        assert adapter.call(op='position', source=identity)['next_offset'] == 25000
        adapter.finish()
        adapter = Adapter(args.binary.resolve(), work / 'archive')
        for identity, rows in sources: assert adapter.call(op='position', source=identity)['next_offset'] == len(rows)
        db.execute('CREATE VIEW expected AS SELECT * FROM base UNION ALL SELECT * FROM late')
        rng = random.Random(20261006)
        queries = ['SELECT COUNT(*), SUM(value) FROM events', 'SELECT device, COUNT(*), SUM(value) FROM events GROUP BY device ORDER BY device']
        for _ in range(40):
            lo = rng.randrange(25000); hi = lo + rng.randrange(1, 10000)
            queries.append(f'SELECT COUNT(*), SUM(value), MIN(value), MAX(value) FROM events WHERE ts >= {lo} AND ts < {hi}')
        for sql in queries:
            actual = adapter.call(op='query', sql=sql)
            expected = [list(row) for row in db.execute(sql.replace('FROM events', 'FROM expected')).fetchall()]
            assert actual == expected, (sql, actual, expected)
        assert adapter.call(op='verify') == 30000 * 24
        stats = adapter.call(op='stats')
        assert stats['version'] == args.expected_version and stats['source']['sources'] == 2 and stats['source']['committed_source_batches'] == 300
        report.update(exact_sql_cases_against_duckdb=42, full_scrub_passed=True, source_positions_and_data_reopen_together=True,
            replay_and_invalid_intervals_passed=True, stats=stats, limits='archive-local checkpoint atomicity; source positions are caller-supplied row offsets; no Kafka transaction, distributed consumer fencing, empty-output advance or retention contract')
    finally:
        adapter.finish(); db.close()
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'source_rows': 30000, 'source_batches': 300, 'queries': 42, 'passed': True}), flush=True)


if __name__ == '__main__': main()
