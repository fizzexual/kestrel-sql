"""Serial, rotated 0.3.14/0.3.15/DuckDB grouping comparisons, including controls."""
import argparse
import datetime
import hashlib
import json
import os
import platform
import statistics
import subprocess
import time
from pathlib import Path
import compare

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'


class Probe:
    def __init__(self, binary, archive, stderr, seed=None):
        self.error = stderr.open('w', encoding='utf-8')
        command = [str(binary), str(archive), 'ts,value,device']
        if seed: command.extend(map(str, seed))
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.error, text=True)
        self.header = json.loads(self.process.stdout.readline())

    def call(self, **request):
        self.process.stdin.write(json.dumps(request) + '\n')
        self.process.stdin.flush()
        response = self.process.stdout.readline()
        assert response, ('probe stopped', self.process.poll())
        return json.loads(response)

    def finish(self):
        self.process.stdin.close()
        try: self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.process.kill(); self.process.wait(); raise
        finally:
            self.process.stdout.close(); self.error.close()
        assert self.process.returncode == 0, self.process.returncode


def queries(rows):
    return [
        ('group_sum', 'SELECT device, SUM(value) AS s FROM events GROUP BY device ORDER BY device'),
        ('group_full', 'SELECT device, COUNT(*) AS n, SUM(value) AS s, AVG(value), MIN(value), MAX(value) FROM events GROUP BY device ORDER BY device'),
        ('filtered_group', 'SELECT device, COUNT(*) AS n, SUM(value) AS s FROM events WHERE value >= 0 GROUP BY device ORDER BY device'),
        ('unordered_control', 'SELECT COUNT(*), SUM(value) FROM events WHERE value >= 0'),
        ('prefix_control', f'SELECT COUNT(*), SUM(value) FROM events WHERE ts >= {rows//4} AND ts < {rows//2}'),
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, default=ROOT / 'bin/baseline-0.3.14/group-probe.exe')
    parser.add_argument('--candidate', type=Path, default=WORK / 'perf-045/candidate/group-probe.exe')
    parser.add_argument('--output', type=Path, default=ROOT / 'benchmarks/group-045-comparison.json')
    parser.add_argument('--scope', choices=['small', 'large', 'nyc', 'extended', 'patterns', 'irregular'], default='small')
    parser.add_argument('--scale-root', type=Path, default=WORK / 'scale-1791221605946248600')
    parser.add_argument('--nyc-root', type=Path)
    parser.add_argument('--reuse-small-fixtures', action='store_true')
    parser.add_argument('--reuse-extended-fixtures', action='store_true')
    parser.add_argument('--rounds', type=int, default=3)
    args = parser.parse_args()
    assert 1 <= args.rounds <= 3 and not args.output.exists()
    import duckdb
    work = WORK / f'group-045-{args.scope}-{time.time_ns()}'; work.mkdir()
    binaries = {'baseline': args.baseline.resolve(), 'candidate': args.candidate.resolve()}
    fixtures = []
    fixture_details = {}
    if args.scope == 'small' and args.reuse_small_fixtures:
        prior = json.loads((ROOT / 'benchmarks/group-038-typed-comparison.json').read_text())
        for f in prior['fixtures']:
            fixtures.append((f['label'], Path(f['archive']), Path(f['reference']), f['rows'], queries(f['rows'])))
    elif args.scope == 'extended' and args.reuse_extended_fixtures:
        prior = json.loads((ROOT / 'benchmarks/group-040-extended-comparison.json').read_text())
        for f in prior['fixtures']:
            fixtures.append((f['label'], Path(f['archive']), Path(f['reference']), f['rows'], queries(f['rows'])))
    elif args.scope in ['small', 'extended', 'patterns']:
        domains = [('dense97', 97, 1), ('sparse19', 19, 1_000_003), ('cardinality5003', 5003, 1)] if args.scope == 'small' else [
            ('wide5003', 5003, 1_000_003), ('collision19', 19, 999_936), ('cardinality70001', 70_001, 1)] if args.scope == 'extended' else [('fibonacci19',19,832040), ('power19',19,524288)]
        for label, domain, step in domains:
            directory = work / label; directory.mkdir()
            seed = Probe(binaries['baseline'], directory / 'archive', directory / 'seed.stderr.log', (1_000_000, domain, step))
            try: assert seed.call(op='verify')['verified_bytes'] == 24_000_000
            finally: seed.finish()
            database = directory / 'reference.duckdb'
            connection = duckdb.connect(str(database))
            connection.execute('SET threads=1')
            connection.execute(f'CREATE TABLE events AS SELECT i::BIGINT AS ts, ((i*37)%1000-500)::BIGINT AS value, (((i*17)%{domain})*{step}-{domain//2})::BIGINT AS device FROM range(1000000) t(i)')
            assert connection.execute('SELECT COUNT(DISTINCT device) FROM events').fetchone()[0] == domain
            connection.execute('CHECKPOINT'); connection.close()
            fixtures.append((label, directory / 'archive', database, 1_000_000, queries(1_000_000)))
    elif args.scope == 'irregular':
        import random
        from stress_compare import Engine
        rng = random.Random(20261006)
        keys = [-(2**63), 2**63-1]
        seen = set(keys)
        while len(keys) < 5003:
            key = rng.randrange(-(2**63), 2**63)
            if key not in seen:
                seen.add(key); keys.append(key)
        directory = work / 'irregular5003'  # Engine owns creation.
        owner = Engine('kestrel', directory, 0, args.baseline.parent/'kestrel-stress.exe', {})
        try:
            connection = owner.connect()
            for lo in range(0,1_000_000,10_000):
                data = [[i,i*37%1000-500,keys[i*17%5003]] for i in range(lo,lo+10_000)]
                assert not connection.call({'op':'append','id':f'irregular:{lo}','data':data})['duplicate']
            assert connection.call({'op':'verify'})['verified_bytes'] == 24_000_000
            connection.close()
        finally: owner.finish()
        database = directory/'reference.duckdb'
        connection = duckdb.connect(str(database))
        try:
            connection.execute('SET threads=1')
            connection.execute('CREATE TABLE keymap (id BIGINT, k BIGINT)')
            connection.executemany('INSERT INTO keymap VALUES (?,?)',enumerate(keys))
            connection.execute('CREATE TABLE events AS SELECT i::BIGINT AS ts, ((i*37)%1000-500)::BIGINT AS value, k AS device FROM range(1000000) t(i) JOIN keymap ON (i*17)%5003=id')
            assert connection.execute('SELECT COUNT(DISTINCT device) FROM events').fetchone()[0] == 5003
            connection.execute('DROP TABLE keymap'); connection.execute('CHECKPOINT')
        finally: connection.close()
        fixture_details['irregular5003'] = {'seed':20261006,'signed_keys':keys,
            'formula':'ts=i, value=(i*37)%1000-500, device=keys[(i*17)%5003]; 10000-row append batches',
            'seed_keys_sha256':hashlib.sha256(json.dumps(keys,separators=(',',':')).encode()).hexdigest()}
        fixtures.append(('irregular5003',directory/'archive',database,1_000_000,queries(1_000_000)))
    elif args.scope == 'large':
        prior = args.scale_root.resolve()
        for rows in [10_000_000, 100_000_000]:
            directory = prior / f'{rows}-ordered'
            assert (directory / 'kestrel').is_dir() and (directory / 'reference.duckdb').is_file()
            fixtures.append((str(rows), directory / 'kestrel', directory / 'reference.duckdb', rows, queries(rows)))
    else:
        prior = json.loads((ROOT / 'benchmarks/nyc-results.json').read_text())
        directory = args.nyc_root.resolve() if args.nyc_root else Path(prior['pipeline_directory'])
        cases = [(case['name'], case['sql']) for case in prior['comparison']]
        fixtures.append(('nyc', directory / 'archive', directory / 'pipeline.duckdb', prior['quality']['accepted_rows'], cases))
    report = {'started_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'versions': {'baseline': '0.3.14', 'candidate': '0.3.15', 'duckdb': duckdb.__version__},
        'binary_sha256': {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in binaries.items()},
        'probe_source_sha256': hashlib.sha256((ROOT / 'examples/group_probe.rs').read_bytes()).hexdigest(),
        'platform': platform.platform(), 'logical_cpu_count': os.cpu_count(),
        'methodology': {'threads': 1, 'rounds': args.rounds, 'repetitions_per_query': 11, 'warmups': 3,
            'order': ['baseline,candidate,duckdb', 'candidate,duckdb,baseline', 'duckdb,baseline,candidate'],
            'timing': 'Rust ArchiveSnapshot::query only; DuckDB Python execute+fetchall; JSON/pipe/result assertions excluded from Rust samples',
            'storage': 'Persisted tables, Kestrel uncompressed BIGINT segments with CRC; DuckDB native compression, 256MB buffer limit; no explicit ART/materialized views',
            'cache': 'Warm queries; no OS cache flush or cold-I/O qualification',
            'serialization': 'Build/seed/verification and other heavy jobs never overlap timed queries',
            'limits': 'One shared Windows computer; exact supported aggregate subset; no network concurrency or universal ranking'},
        'fixtures': [], 'cases': [], 'complete': False}
    def save(): args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    for label, archive, database, rows, sql_cases in fixtures:
        expected = {}
        report['fixtures'].append({'label': label, 'archive': str(archive), 'reference': str(database), 'rows': rows,
            'reference_bytes': database.stat().st_size, 'queries': sql_cases, **fixture_details.get(label,{})})
        for turn in range(args.rounds):
            order = ['baseline', 'candidate', 'duckdb']; order = order[turn:] + order[:turn]
            for variant in order:
                probe = None; connection = None
                try:
                    if variant == 'duckdb':
                        connection = duckdb.connect(str(database), read_only=True)
                        connection.execute('SET threads=1'); connection.execute("SET memory_limit='256MB'")
                        assert connection.execute('SELECT COUNT(*) FROM events').fetchone()[0] == rows
                    else:
                        probe = Probe(binaries[variant], archive, work / f'{label}-{turn}-{variant}.stderr.log')
                        assert probe.header['version'] == report['versions'][variant]
                        assert probe.header['stats']['rows'] == rows
                    measured = []
                    for name, sql in sql_cases:
                        if connection:
                            values = [list(row) for row in connection.execute(sql).fetchall()]
                            for _ in range(3): connection.execute(sql).fetchall()
                            samples = []
                            for _ in range(11):
                                started = time.perf_counter_ns(); actual = connection.execute(sql).fetchall()
                                samples.append((time.perf_counter_ns()-started)/1e6)
                                assert compare.same(values, actual)
                            result = {'rows': values, 'plan': connection.execute('EXPLAIN ' + sql).fetchall()}
                        else:
                            response = probe.call(op='query', sql=sql, repeats=11)
                            result = response['result']; values = result['rows']; samples = response['samples_ms']
                        if name not in expected: expected[name] = values
                        assert compare.same(expected[name], values), (label, variant, name)
                        fingerprint = hashlib.sha256(json.dumps(values, separators=(',', ':')).encode()).hexdigest()
                        if len(values) > 512: result = {**result, 'rows': {'count': len(values), 'sha256': fingerprint, 'first': values[:3], 'last': values[-3:]}}
                        measured.append({'name': name, 'sql': sql, 'samples_ms': samples, 'median_ms': statistics.median(samples), 'result': result,
                            'all_repeated_and_reference_results_equal': True})
                        print(json.dumps({'fixture': label, 'round': turn, 'variant': variant, 'query': name, 'median_ms': statistics.median(samples)}), flush=True)
                    scrub = probe.call(op='verify')['verified_bytes'] if probe else None
                    if probe: assert scrub == rows * 24
                    report['cases'].append({'fixture': label, 'round': turn, 'variant': variant, 'queries': measured,
                        'full_scrub_bytes': scrub, 'archive_stats': probe.header['stats'] if probe else None})
                    save()
                finally:
                    if probe: probe.finish()
                    if connection: connection.close()
    report['complete'] = True
    report['completed_at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save()
    print(json.dumps({'output': str(args.output), 'cases': len(report['cases']), 'complete': True}), flush=True)


if __name__ == '__main__': main()
