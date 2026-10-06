"""Report every current query shape, controls, failures and exact qualification."""
import datetime
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def read(name): return json.loads((ROOT / name).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    build = read('benchmarks/rust-checks-038.json')
    assert build['rust_tests'] == {'debug': 63, 'release': 63, 'passed': True}
    query_build = read('benchmarks/rust-checks-038-query-final.json')
    wire = read('benchmarks/wire-038-audit.json')
    assert wire['benchmarked_group_probe_byte_identical']
    assert build['group_probe_sha256'] == query_build['group_probe_sha256']
    for relative in ['src/archive.rs', 'src/lib.rs', 'src/live.rs', 'src/source.rs', 'src/query.rs', 'src/sql.rs', 'src/scale.rs']:
        assert build['source_sha256'][relative] == query_build['source_sha256'][relative]
    for relative, digest in build['source_sha256'].items(): assert sha(ROOT / relative) == digest
    reports = [read(f'benchmarks/group-038-{scope}-comparison.json') for scope in ['typed', 'nyc', 'large']]
    assert [len(r['cases']) for r in reports] == [27, 9, 18] and all(r['complete'] for r in reports)
    summaries = []
    for report in reports:
        for fixture in report['fixtures']:
            for name, sql in fixture['queries']:
                series = {}
                for variant in ['baseline', 'candidate', 'duckdb']:
                    series[variant] = [next(q for q in c['queries'] if q['name'] == name) for c in report['cases'] if c['fixture'] == fixture['label'] and c['variant'] == variant]
                    assert len(series[variant]) == 3
                    assert all(len(q['samples_ms']) == 11 and q['all_repeated_and_reference_results_equal'] for q in series[variant])
                medians = {v: statistics.median(q['median_ms'] for q in qs) for v, qs in series.items()}
                speedups = [a['median_ms']/b['median_ms'] for a, b in zip(series['baseline'], series['candidate'])]
                round_wins = sum(c['median_ms'] < d['median_ms'] for c, d in zip(series['candidate'], series['duckdb']))
                summaries.append({'fixture': fixture['label'], 'query': name, 'sql': sql, 'rows': fixture['rows'],
                    'run_median_ms': medians, 'run_medians_ms': {v: [q['median_ms'] for q in qs] for v, qs in series.items()},
                    'paired_baseline_over_candidate_median': statistics.median(speedups), 'paired_speedup_range': [min(speedups), max(speedups)],
                    'candidate_vs_duckdb': 'win' if medians['candidate'] < medians['duckdb'] else 'loss', 'candidate_faster_than_duckdb_rounds': round_wins,
                    'candidate_plan': series['candidate'][0]['result']['plan'], 'results_equal': True})
    controls = read('benchmarks/group-038-paired-controls.json')
    assert controls['complete'] and len(controls['cases']) == 8
    large_control = read('benchmarks/group-038-large-paired-control.json')
    assert large_control['complete'] and len(large_control['pairs']) == 7 and large_control['all_results_equal']
    differential = read('benchmarks/archive-038-verification.json')
    assert differential['queries_checked_against_each_reference'] == 500
    faults = read('benchmarks/publication-038-faults.json')
    assert len(faults['cut_points']) == 56 and len(faults['corruption_cases']) == 22
    recovery = read('benchmarks/group-038-recovery.json')
    assert len(recovery['cycles']) == 32 and not recovery['failed_cases']
    source = read('benchmarks/source-038-faults.json')
    assert len(source['cases']) == 14 and len(source['kill_cycles']) == 8 and not source['failed_cases']
    pipeline = read('portfolio/source-pipeline-038-results.json')
    assert pipeline['stats']['archive']['rows'] == 30000
    assert sum(p['committed_batches'] for p in pipeline['positions']) == 300
    assert pipeline['exact_sql_cases_against_duckdb'] == 42 and pipeline['full_scrub_passed']
    assert pipeline['source_positions_and_data_reopen_together'] and pipeline['replay_and_invalid_intervals_passed']
    order = read('benchmarks/correctness-038-run-order.json')
    assert len(order) == 6 and all(r['returncode'] == 0 for r in order)
    latest_build = max(record['completed_at_utc'] for record in query_build['build_run_order'])
    latest_build = max(latest_build, read('benchmarks/source-038-typed-adapter-build.json')['completed_at_utc'])
    assert latest_build < min(r['started_at_utc'] for r in reports)
    assert max(r['completed_at_utc'] for r in reports) < controls['started_at_utc']
    assert controls['completed_at_utc'] < large_control['started_at_utc']
    assert large_control['completed_at_utc'] < order[0]['started_at_utc']
    assert order[-1]['completed_at_utc'] < build['build_run_order'][0]['started_at_utc']
    wire_order = read('benchmarks/correctness-038-wire-run-order.json')
    assert len(wire_order) == 4 and all(record['returncode'] == 0 for record in wire_order)
    assert build['build_run_order'][-1]['completed_at_utc'] < wire_order[0]['started_at_utc']
    base = read('benchmarks/baseline-0.3.7-provenance.json')
    assert sha(ROOT.parent / 'kestrel-sql-0.3.7.zip') == base['archive_sha256']
    for relative, digest in base['core_source_sha256'].items(): assert sha(ROOT / 'benchmarks/baseline-0.3.7-source' / relative) == digest
    changed = [p for p, digest in base['core_source_sha256'].items() if sha(ROOT / p) != digest]
    assert set(changed) == {'Cargo.toml', 'Cargo.lock', 'src/archive.rs', 'tests/archive.rs', 'src/main.rs', 'src/bin/kestrel-stress.rs'}
    old = (ROOT / 'benchmarks/baseline-0.3.7-source/src/archive.rs').read_text()
    new = (ROOT / 'src/archive.rs').read_text()
    query = '    fn query_inner<const PROFILE: bool>('
    verify = '    /// Read every data block and validate its checksum and cumulative aggregate index.'
    dense = '/// A query-local direct-address table for bounded integer domains.'
    cell = '#[derive(Clone, Default)]\nstruct Cell {'
    tests = '\n#[cfg(test)]\nmod dense_group_tests {'
    prefix = new.split(query)[0].replace('const MAX_DENSE_GROUP_SLOTS: usize = 4096;\n', '').replace('const MAX_DENSE_GROUP_BYTES: usize = 8 * 1024 * 1024;\n', '')
    assert old.split(query)[0] == prefix
    assert old.split(verify)[1].split(cell)[0] == new.split(verify)[1].split(dense)[0]
    assert old.split(cell)[1] == new.split(cell)[1].split(tests)[0]
    stats = {'version': '0.3.8', 'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_sha256': build['source_sha256'], 'rust_tests_each_mode': 63, 'current_cases': 54, 'current_query_shapes': 30, 'current_timed_query_samples': 2970,
        'summaries': summaries, 'paired_controls': controls['cases'], 'paired_100m_unordered_control': large_control,
        'additional_control_samples': 3850, 'sql_differential_against_each_reference': 500,
        'publication_fault_cut_points': 56, 'catalog_corruption_rejections': 22, 'concurrent_forced_kills': 32,
        'source_fault_cut_points': 14, 'source_forced_kills': 8, 'parquet_rows': 30000, 'source_intervals': 300, 'parquet_sql_oracles': 42,
        'source_pipeline_proof': 'portfolio/source-pipeline-038-results.json',
        'storage_publication_live_source_and_scan_helpers_unchanged': True, 'no_compilation_overlap_with_timed_database_work': True,
        'wire_serialization_fix': wire, 'timed_query_probe_byte_identical_in_final_build': True,
        'initial_candidate_evidence': ['group-038-comparison.json', 'group-038-cell-trial-audit.json', 'rust-checks-038-cell-trial.json', 'trial-038-cell-source/'],
        'service_qualification': 'No current network req/s test in this experiment; earlier mixed-write stalls and failed SLOs remain unresolved',
        'limits': ['One shared Windows computer, warm single-thread timings, supported integer aggregate subset',
            'Only DuckDB freshly compared here; five-engine service comparison remains historical 0.3.1',
            'Direct-address grouping is established prior art; no algorithmic novelty or universal superiority claim',
            'No physical power-loss or distributed-scale qualification; production readiness remains incomplete']}
    (ROOT / 'benchmarks/group-038-audit.json').write_text(json.dumps(stats, indent=2) + '\n', encoding='utf-8')
    lines = ['# 0.3.8: bounded adaptive integer grouping', '',
        'The archive chooses a direct-address aggregation table when the group-column extrema fit at most 4,096 slots and a conservative 8 MiB query-local budget. Wider domains use the original hash path. SUM and AVG of the same column share one exact i128 reduction; MIN/MAX use narrow arrays and membership/counts are shared. No storage format, publication synchronization, source-checkpoint contract or live-writer policy changed.', '',
        'Fresh evidence: 54 sequential engine/fixture/round cases, 30 query shapes and 2,970 timed query samples. Each shape ran three rotated engine orders, three warmups and eleven samples. Tables show the median of the three run medians. Rust samples time the direct query API; DuckDB samples include its Python execute/fetch API. JSON framing, fixture creation, result checks and full CRC scrubs are outside Rust timers. Both use one thread and warm OS caches; DuckDB has a 256 MB buffer-manager limit and native compressed storage, while Kestrel reads uncompressed integer segments.', '',
        '| Fixture | Query | 0.3.7 ms | 0.3.8 ms | DuckDB ms | Paired before/after | vs DuckDB |',
        '|---|---|---:|---:|---:|---:|---|']
    for case in summaries:
        m = case['run_median_ms']; mark = '✅' if case['candidate_vs_duckdb'] == 'win' else '❌'
        lines.append(f"| {case['fixture']} | {case['query']} | {m['baseline']:.3f} | {m['candidate']:.3f} | {m['duckdb']:.3f} | {case['paired_baseline_over_candidate_median']:.2f}x | {mark}; {case['candidate_faster_than_duckdb_rounds']}/3 rounds |")
    lines += ['', 'Checkmarks describe these measured medians only. A narrow median win, mixed round results or microsecond prefix timing is not a general database ranking. Sparse and higher-cardinality losses are included.', '',
        '## Short paired controls', '',
        'Controls that appeared slower were repeated in 21 alternating pairs using exact-byte independent archive copies. Each pair contains eleven timed samples per engine. Candidate/baseline above 1 means slower; the raw original three-round outcomes remain visible.', '',
        '| Fixture | Query | Before ms | After ms | Paired candidate/baseline |', '|---|---|---:|---:|---:|']
    for case in controls['cases']:
        lines.append(f"| {case['fixture']} | {case['name']} | {case['baseline_median_ms']:.3f} | {case['candidate_median_ms']:.3f} | {case['paired_candidate_over_baseline_median']:.3f} |")
    lines.append(f"| 100M; seven pairs | unordered_control | {large_control['baseline_median_ms']:.3f} | {large_control['candidate_median_ms']:.3f} | {large_control['paired_candidate_over_baseline_median']:.3f} |")
    lines += ['', '## Correctness and recovery', '',
        'All 63 Rust tests pass in debug and release, with formatting and default/fault-feature Clippy checks. New cases cover signed extrema, holes, empty/filtered groups, exact wide sums, output aliases/limits, pinned snapshots, compaction/reopen, metadata-bound rejection, allocation limits, hash fallback and the 100,000-group result budget. Five hundred seeded queries match both DuckDB and SQLite over eight overlapping sorted runs.', '',
        'The current binaries also passed 56 publication cut points, 22 corrupt-catalog rejections, 32 concurrent forced kills, 14 source publication failures and eight source pipeline kills. Exact acknowledged receipts, output/source positions, retries and full scrubs are checked after reopen. The current Parquet source pipeline proof is linked below. These are live-filesystem process/IO-failure tests, not physical power failures.', '',
        'A final boundary check found an existing CLI panic for SUM results outside the serde_json::Value integer range: both 0.3.7 and the first candidate failed positive and negative three-row extreme sums. The CLI and test bridge now serialize typed results directly, keeping exact i128 numeric tokens without changing dependency features. Wide archive/RAM CLI results, bridge error continuity and retry/reopen are tested. The affected final CLI/bridge differential and publication/kill checks were rerun. The timed group probe is byte-identical to the final build, and every query-library source file is unchanged by this framing fix; no heavy build overlapped timing.', '',
        '## Preserved experiments and limits', '',
        'The initial Cell-array candidate and its raw comparison are preserved. Its “sparse17” generator used `(i*17)%17`, so that fixture was actually a single-key group. Its audit explicitly corrects the label. The current sparse fixture uses 19 distinct widely spaced keys and independently checks distinct count. Initial lockfile-version, pinned-test lifetime, Clippy, sandbox-library, baseline-validator and adapter-LTO failures remain in the build/harness evidence.', '',
        'This experiment measures core read queries. It establishes no new requests/s result or sustained mixed-write service envelope. Historical write stalls, durability boundaries, SQL/NULL/type limitations and missing distributed/production qualification remain. The last fresh multi-server matrix is still 0.3.1.', '',
        '## Reproduce and inspect', '',
        'Run serially on this computer: `python benchmarks/checks_038.py`, build the matched preserved probe with `python benchmarks/build_group_baseline_038.py`, then run `group_compare_038.py` once for each scope (`small`, `nyc`, `large`) with separate fresh output names. The large and NYC scopes reuse the retained locally generated datasets described in their reports. Install/use the pinned local DuckDB libraries. Never run build, test, packaging or other heavy jobs concurrently with query timing. The scripts refuse to overwrite completed comparison reports.', '',
        '- [Current audit and every before/after value](benchmarks/group-038-audit.json)',
        '- [Corrected 1M-row shapes and raw samples](benchmarks/group-038-typed-comparison.json)',
        '- [10M/100M-row raw samples](benchmarks/group-038-large-comparison.json)',
        '- [Real taxi-data raw samples](benchmarks/group-038-nyc-comparison.json)',
        '- [Short paired controls](benchmarks/group-038-paired-controls.json)',
        '- [100M-row paired unordered control](benchmarks/group-038-large-paired-control.json)',
        '- [Separate stage profiles](benchmarks/group-038-profiles.json)',
        '- [SQL differential checks](benchmarks/archive-038-verification.json)',
        '- [Final CLI/bridge wide-JSON fix and preserved failures](benchmarks/wire-038-audit.json)',
        '- [Final CLI differential rerun](benchmarks/archive-038-wire-verification.json)',
        '- [Final bridge publication/corruption rerun](benchmarks/publication-038-wire-faults.json)',
        '- [Final bridge forced-kill rerun](benchmarks/group-038-wire-recovery.json)',
        '- [Publication/corruption proof](benchmarks/publication-038-faults.json)',
        '- [Concurrent kills](benchmarks/group-038-recovery.json)',
        '- [Source failures and kills](benchmarks/source-038-faults.json)',
        '- [Current Parquet pipeline](portfolio/source-pipeline-038-results.json)',
        '- [Serial correctness order](benchmarks/correctness-038-run-order.json)',
        '- [Initial candidate and fixture correction](benchmarks/group-038-cell-trial-audit.json)',
        '- [All earlier wins, losses and downloads](BENCHMARK_HISTORY.md)', '']
    (ROOT / 'PERFORMANCE_038.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'cases': 54, 'samples': 2970, 'current_tests': 63, 'report': 'PERFORMANCE_038.md'}), flush=True)


if __name__ == '__main__': main()
