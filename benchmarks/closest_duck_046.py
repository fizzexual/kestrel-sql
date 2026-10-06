"""Resolve a thin matrix margin with separate, preserved alternating repeats."""
import datetime
import hashlib
import json
import statistics
import time
from pathlib import Path

import duckdb
import compare
from group_compare_046 import Probe

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
output = ROOT / 'benchmarks/packed-046-closest-duck-pairs.json'
assert not output.exists()
order = json.loads((ROOT / 'benchmarks/packed-046-run-order.json').read_text(encoding='utf-8'))
assert len(order) == 17 and all(r['returncode'] == 0 for r in order)
fixture = json.loads((ROOT / 'benchmarks/group-046-irregular-comparison.json').read_text(encoding='utf-8'))['fixtures'][0]
sql = next(sql for name, sql in fixture['queries'] if name == 'group_sum')
binary = WORK / 'perf-046/candidate/group-probe.exe'
build = json.loads((ROOT / 'benchmarks/rust-checks-046.json').read_text(encoding='utf-8'))
assert hashlib.sha256(binary.read_bytes()).hexdigest() == build['group_probe_sha256']
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
assert order[-1]['completed_at_utc'] <= started
work = WORK / f'closest-duck-046-{time.time_ns()}'
work.mkdir()
report = {
    'version': '0.3.16', 'started_at_utc': started, 'fixture': fixture, 'query': sql,
    'candidate_sha256': build['group_probe_sha256'], 'duckdb_version': duckdb.__version__,
    'harness_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'methodology': {
        'reason': 'Observed matrix margin about 0.3%; additional repeats resolve that uncertainty',
        'pairs': 21, 'repeats_per_binary_per_pair': 11, 'threads': 1,
        'order': 'candidate first on even pairs, DuckDB first on odd pairs',
        'history': 'One persistent process/connection per engine; this single-query history differs from the matrix',
        'timing': 'Rust ArchiveSnapshot::query only; DuckDB Python execute/fetchall; framing and result checks untimed',
        'warmups': 'Three warmups and one expected-result query per engine and pair',
        'reference_memory_limit': '256MB', 'instrumented': False,
        'limits': 'Shared Windows desktop, warm aggregate subset; not a network or production benchmark',
    },
    'pairs': [], 'complete': False,
}


def save():
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


save()
connection = duckdb.connect(fixture['reference'], read_only=True)
probe = None
try:
    connection.execute('SET threads=1')
    connection.execute("SET memory_limit='256MB'")
    assert connection.execute('SELECT COUNT(*) FROM events').fetchone()[0] == fixture['rows']
    probe = Probe(binary, Path(fixture['archive']), work / 'candidate.stderr.log')
    assert probe.header['version'] == '0.3.16' and probe.header['stats']['rows'] == fixture['rows']
    expected = [list(row) for row in connection.execute(sql).fetchall()]
    report['result_rows'] = len(expected)
    report['result_sha256'] = hashlib.sha256(json.dumps(expected, separators=(',', ':')).encode()).hexdigest()
    for turn in range(21):
        pair = {}
        engines = ['candidate', 'duckdb'] if turn % 2 == 0 else ['duckdb', 'candidate']
        for engine in engines:
            if engine == 'candidate':
                response = probe.call(op='query', sql=sql, repeats=11)
                assert compare.same(expected, response['result']['rows'])
                samples = response['samples_ms']
                assert response['result']['bytes_read'] == fixture['rows'] * 16
            else:
                values = connection.execute(sql).fetchall()
                assert compare.same(expected, values)
                for _ in range(3):
                    assert compare.same(expected, connection.execute(sql).fetchall())
                samples = []
                for _ in range(11):
                    before = time.perf_counter_ns()
                    actual = connection.execute(sql).fetchall()
                    samples.append((time.perf_counter_ns() - before) / 1e6)
                    assert compare.same(expected, actual)
            assert len(samples) == 11
            pair[engine] = {'samples_ms': samples, 'median_ms': statistics.median(samples),
                            'all_repeated_results_equal': True}
        report['pairs'].append(pair)
        save()
    report['candidate_median_ms'] = statistics.median(p['candidate']['median_ms'] for p in report['pairs'])
    report['duckdb_median_ms'] = statistics.median(p['duckdb']['median_ms'] for p in report['pairs'])
    ratios = [p['candidate']['median_ms'] / p['duckdb']['median_ms'] for p in report['pairs']]
    report['paired_candidate_over_duckdb_median'] = statistics.median(ratios)
    report['candidate_faster_pairs'] = sum(r < 1 for r in ratios)
    report['candidate_vs_duckdb'] = 'win' if report['candidate_median_ms'] < report['duckdb_median_ms'] else 'loss'
    report['timed_samples'] = 462
    report['full_scrub_bytes'] = probe.call(op='verify')['verified_bytes']
    assert report['full_scrub_bytes'] == fixture['rows'] * 24
    report.update(complete=True, completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save()
    print(json.dumps({k: v for k, v in report.items() if k not in ['pairs', 'fixture']}), flush=True)
finally:
    if probe:
        probe.finish()
    connection.close()
