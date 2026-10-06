"""Gate seeded group cache qualification while preserving every matrix loss."""
import datetime
import hashlib
import json
from pathlib import Path

from report_039 import summaries, score

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    build = read('benchmarks/rust-checks-041.json')
    assert build['version'] == '0.3.11' and build['rust_tests'] == {'debug': 70, 'release': 70, 'passed': True}
    for name, digest in build['source_sha256'].items():
        assert sha(ROOT / name) == digest, name
    base = read('benchmarks/baseline-0.3.10-provenance.json')
    for name, digest in base['core_source_sha256'].items():
        assert sha(ROOT / 'benchmarks/baseline-0.3.10-source' / name) == digest, name
    assert sha(ROOT.parent / 'kestrel-sql-0.3.10.zip') == base['archive_sha256']
    changed = {name for name, digest in base['core_source_sha256'].items() if sha(ROOT / name) != digest}
    assert changed == {'Cargo.toml', 'Cargo.lock', 'src/archive.rs'}, changed
    old = (ROOT / 'benchmarks/baseline-0.3.10-source/src/archive.rs').read_text(encoding='utf-8')
    new = (ROOT / 'src/archive.rs').read_text(encoding='utf-8')
    assert old[:old.index('struct SparseGroups {')] == new[:new.index('struct SparseGroups {')]
    marker = '#[derive(Clone, Default)]\nstruct Cell'
    assert old[old.index(marker):old.index('#[cfg(test)]')] == new[new.index(marker):new.index('#[cfg(test)]')]
    reports = [read(f'benchmarks/group-041-{scope}-comparison.json') for scope in ['typed', 'nyc', 'large', 'extended', 'patterns']]
    assert [len(r['cases']) for r in reports] == [27, 9, 18, 27, 18]
    assert all(r['complete'] and r['binary_sha256']['candidate'] == build['group_probe_sha256'] for r in reports)
    primary = [c for report in reports[:3] for c in summaries(report)]
    extra = summaries(reports[3])
    patterns = summaries(reports[4])
    assert len(primary) == 30 and len(extra) == 15
    controls = {}
    for name, expected_cases, turns, repeats, profiled in [
        ('final-pairs', 3, 21, 11, False), ('sparse-guard-pairs', 3, 21, 11, False),
        ('scan-guard-pairs', 4, 21, 11, False), ('final-profiles', 3, 7, 11, True),
    ]:
        report = read(f'benchmarks/cache-041-{name}.json')
        assert report['complete'] and len(report['cases']) == expected_cases
        assert report['binary_sha256']['candidate'] == build['group_probe_sha256']
        assert report['methodology']['instrumented'] == profiled
        for case in report['cases']:
            assert case['all_results_equal'] and len(case['pairs']) == turns
            for pair in case['pairs']:
                assert all(len(p['samples_ms']) == repeats for p in pair.values())
            assert all(p['full_scrub_bytes'] == report['fixture']['rows'] * 24 for p in case['pairs'][-1].values())
        controls[name] = report
    assert all(c['paired_candidate_over_baseline_median'] < 0.8 for c in controls['final-pairs']['cases'])
    for name in ['sparse-guard-pairs','scan-guard-pairs']:
        assert all(c['paired_candidate_over_baseline_median'] < 1.1 for c in controls[name]['cases']), name
    general = read('benchmarks/archive-041-verification.json')
    groups = read('benchmarks/group-041-differential.json')
    scans = read('benchmarks/scan-041-differential.json')
    assert general['binary_sha256'] == build['cli_sha256'] and general['queries_checked_against_each_reference'] == 500
    assert all(q['passed'] for q in general['queries'])
    for proof, count in [(groups, 500), (scans, 600)]:
        assert proof['binary_sha256'] == build['bridge_sha256'] and proof['complete']
        assert proof['queries_checked_against_each_reference'] == count
        assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in proof['cases'])
    assert all(f['reopen_retry_and_scrub_passed'] for f in scans['fixtures'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in groups['modes'])
    cache = read('benchmarks/cache-041-differential.json')
    assert cache['complete'] and cache['queries_checked_against_each_reference'] == 600
    assert cache['binary_sha256'] == build['bridge_sha256']
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in cache['cases'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in cache['modes'])
    faults = read('benchmarks/publication-041-faults.json')
    assert faults['binary_sha256'] == build['bridge_sha256'] and faults['fault_driver_sha256'] == build['fault_driver_sha256']
    assert len(faults['cut_points']) == 56 and len(faults['corruption_cases']) == 22
    assert all(c['original_receipts_preserved'] and c['atomic_rows_and_sum'] and c['retry_deduplication_passed'] and c['full_scrub_passed'] for c in faults['cut_points'])
    assert all(c['rejected'] for c in faults['corruption_cases'])
    recovery = read('benchmarks/group-041-recovery.json')
    source = read('benchmarks/source-041-faults.json')
    assert recovery['binary_sha256'] == build['bridge_sha256'] and len(recovery['cycles']) == 32 and not recovery['failed_cases']
    assert len(source['cases']) == 14 and len(source['kill_cycles']) == 8 and not source['failed_cases']
    pipeline = read('portfolio/source-pipeline-041-results.json')
    assert pipeline['stats']['archive']['rows'] == 30000 and sum(p['committed_batches'] for p in pipeline['positions']) == 300
    assert pipeline['exact_sql_cases_against_duckdb'] == 42 and pipeline['full_scrub_passed']
    assert pipeline['source_positions_and_data_reopen_together'] and pipeline['replay_and_invalid_intervals_passed']
    wire = read('benchmarks/wire-041-audit.json')
    assert wire['cli_sha256'] == build['cli_sha256'] and wire['bridge_sha256'] == build['bridge_sha256']
    assert all(wire[k] for k in ['exact_positive_and_negative_wide_archive_json', 'exact_wide_ram_json', 'sparse_bridge_error_continuity_retry_reopen_and_scrub'])
    timed = read('benchmarks/cache-041-run-order.json')
    qualified = read('benchmarks/correctness-041-run-order.json')
    assert len(timed) == 9 and all(r['returncode'] == 0 for r in timed)
    assert len({r['suite'] for r in qualified if r['returncode'] == 0}) == 9
    assert all(a['completed_at_utc'] < b['started_at_utc'] for a, b in zip(timed, timed[1:]))
    adapter = read('benchmarks/source-041-typed-adapter-build.json')
    assert max(r['completed_at_utc'] for r in build['build_run_order']) < adapter['started_at_utc'] < adapter['completed_at_utc'] < timed[0]['started_at_utc']
    assert timed[-1]['completed_at_utc'] < qualified[0]['started_at_utc']
    assert all(a['completed_at_utc'] <= b['started_at_utc'] for a, b in zip(qualified, qualified[1:]))
    trial = read('benchmarks/trial-041-seeded-multiply/proof.json')
    assert trial['debug_tests_passed'] == 70
    for relative,digest in trial['source_sha256'].items():
        assert sha(ROOT / 'benchmarks/trial-041-seeded-multiply/source' / relative) == digest
    assert sha(Path(trial['group_probe'])) == trial['group_probe_sha256']
    assert (ROOT / 'benchmarks/trial-041-seeded-multiply/source/src/archive.rs').read_bytes() == (ROOT/'src/archive.rs').read_bytes()
    assert trial['build_run_order'][-1]['completed_at_utc'] < read('benchmarks/cache-041-trial-pairs.json')['started_at_utc']
    assert read('benchmarks/cache-041-trial-guard-pairs.json')['completed_at_utc'] < build['build_run_order'][0]['started_at_utc']
    for report in reports:
        assert report['binary_sha256']['baseline'] == base['baseline_binary_sha256']['group-probe.exe']
    for control in controls.values():
        assert control['binary_sha256']['baseline'] == base['baseline_binary_sha256']['group-probe.exe']
    samples = sum(len(q['samples_ms']) for r in reports for c in r['cases'] for q in c['queries'])
    assert samples == 5445
    audit = {'version':'0.3.11', 'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_sha256':build['source_sha256'], 'rust_tests_each_mode':70,
        'baseline':'0.3.10', 'baseline_provenance':base,
        'primary_score':score(primary), 'extended_score':score(extra), 'pattern_score':score(patterns),
        'current_comparison_cases':99, 'current_query_shapes':55, 'current_timed_query_samples':samples,
        'current_comparisons':primary, 'extended_comparisons':extra, 'pattern_comparisons':patterns,
        'paired_controls':{name:[{k:v for k,v in c.items() if k!='pairs'} for c in r['cases']] for name,r in controls.items()},
        'unprofiled_control_samples':4620, 'profiled_control_samples_excluded':462,
        'sql_cases_against_each_reference':2200, 'publication_cut_points':56, 'catalog_corruption_rejections':22,
        'forced_kills':32, 'source_fault_cut_points':14, 'source_forced_kills':8,
        'parquet_rows':30000, 'source_intervals':300, 'parquet_sql_oracles':42,
        'no_compilation_overlap_with_timed_database_work':True,
        'storage_publication_live_source_prefix_reader_and_dense_helpers_unchanged':True,
        'service_qualification':'No new network requests/s qualification; previous mixed-write losses and stalls remain visible',
        'qualification_harness_failures':[r for r in qualified if r['returncode'] != 0],
        'report_harness_repairs':[read('benchmarks/report-041-repair.json')],
        'preserved_development_trial':'seeded-multiply: source and binary retained; final version rebuilt and remeasured',
        'limits':['Warm single-thread queries on one shared Windows computer',
          'Rust direct query timer versus DuckDB Python execute/fetchall; native storage layouts differ',
          'Cache multiplier changes per query; unlucky seeds and constructed collisions still fall back, without a latency guarantee',
          'Only DuckDB freshly compared; last multi-server matrix remains 0.3.1',
          'No new network, cold-I/O, power-loss, distributed-scale or production qualification']}
    (ROOT / 'benchmarks/cache-041-audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    lines = ['# 0.3.11: seeded sparse-group cache indexing', '',
        'The 256-slot tagged GROUP BY cache now indexes the upper bits of a wrapping multiplication with an odd multiplier derived once per query from the existing randomized HashMap state. This spreads low-bit-aligned keys across slots. Every hit still checks the exact signed key; misses use the unchanged authoritative randomized HashMap. The 128-key limit, low-hit-rate fallback, typed i128 reductions, result limit, dense grouping, storage and writer policy remain intact.', '',
        'The historical collision19 keys occupied only two old cache slots. Initial instrumented profiles placed most cost in aggregation. A fixed golden-ratio multiplier can itself collapse a Fibonacci-spaced key pattern, so the candidate uses a per-query seed. Unit tests deliberately invert the actual odd multiplier to generate real collisions, then verify exact counts/sums, fallback and cache release. This cache is not a cryptographic hash or a promise of collision-free execution. [Rust documents randomized HashMap state](https://doc.rust-lang.org/std/collections/hash_map/struct.RandomState.html) and [hash_one](https://doc.rust-lang.org/std/hash/trait.BuildHasher.html#method.hash_one); these are established techniques, without a novelty claim.', '',
        'Fresh comparisons retain 99 sequential engine/fixture/round cases, 55 shapes and 5,445 query samples, plus 4,620 uninstrumented paired controls. The matched and prior stress shapes remain comparable with 0.3.10; ten added shapes exercise Fibonacci spacing and power-of-two spacing. Three rotated orders, three warmups and eleven samples are used for every matrix shape. All queries use one thread and warm caches on this shared Windows computer. Rust samples time ArchiveSnapshot::query; DuckDB samples include Python execute/fetchall with native compression and a 256 MB buffer limit. Build/setup, assertions and scrubs are untimed. Instrumented samples are excluded from competitive totals.', '',
        f"Matched score: {score(primary)['wins']} wins / {score(primary)['losses']} losses against DuckDB; prior extra shapes: {score(extra)['wins']} / {score(extra)['losses']}; new key patterns: {score(patterns)['wins']} / {score(patterns)['losses']}. These describe this run; every loss and round count follows.", '']
    for title,name in [('Final collision19 pairs against 0.3.10','final-pairs'),
                       ('Ordinary sparse19 guard pairs','sparse-guard-pairs'),
                       ('Unchanged scan and dense-group guards','scan-guard-pairs')]:
        lines += ['## '+title, '',
            'Twenty-one alternating same-archive pairs, eleven samples per variant per pair. Each process closes before the next opens. Ratios above 1 mean slower. A ratio of paired medians can differ from the ratio of the displayed times. Raw samples retain variation from changing cache seeds and the shared desktop; actual seed values are not exposed or fixed by the harness.', '',
            '| Query | 0.3.10 ms | 0.3.11 ms | Paired final/baseline |', '|---|---:|---:|---:|']
        for c in controls[name]['cases']:
            lines.append(f"| {c['name']} | {c['baseline_median_ms']:.3f} | {c['candidate_median_ms']:.3f} | {c['paired_candidate_over_baseline_median']:.4f} |")
        lines += ['']
    lines += ['## Instrumented collision19 stages', '', 'Seven alternating profiled pairs; excluded from competitive totals.', '',
      '| Query | Read before/after ms | Select before/after ms | Aggregate before/after ms |', '|---|---:|---:|---:|']
    for c in controls['final-profiles']['cases']:
        before=c['stage_median_ms']['baseline']; after=c['stage_median_ms']['candidate']
        lines.append('| '+c['name']+' | '+' | '.join(f"{before[stage]:.3f} / {after[stage]:.3f}" for stage in ['page_read_ms','selection_ms','aggregate_ms'])+' |')
    lines += ['']
    for title,cases in [('Matched matrix',primary),('Prior additional stress matrix',extra),('New key-pattern matrix',patterns)]:
        lines += ['## '+title, '', '| Fixture | Query | 0.3.10 ms | 0.3.11 ms | DuckDB ms | Paired before/after | vs DuckDB |', '|---|---|---:|---:|---:|---:|---|']
        for c in cases:
            m=c['run_median_ms']; mark='\u2705' if c['candidate_vs_duckdb']=='win' else '\u274c'
            lines.append(f"| {c['fixture']} | {c['query']} | {m['baseline']:.3f} | {m['candidate']:.3f} | {m['duckdb']:.3f} | {c['paired_baseline_over_candidate_median']:.3f}x | {mark}; {c['candidate_faster_than_duckdb_rounds']}/3 rounds |")
        lines += ['']
    lines += ['## Correctness and remaining scope', '',
      'All 70 Rust tests pass in debug/release, formatting and both Clippy configurations. Collision tests construct real collisions for each actual seed rather than relying on the previous hash formula. The final CLI/bridge match 2,200 SQL cases against each DuckDB and SQLite: 500 general archive, 500 expanded/signed-sparse grouping, 600 scans and 600 new low-bit/Fibonacci/signed-power/over-cache-limit cases. Reopen, confirmed retry, CRC scrubs and exact signed i128 JSON pass.', '',
      'The initial report audit rejected four equal adjacent Windows timestamps after all nine qualification suites passed. Blocking subprocess execution was already serial. The repaired no-overlap check accepts equal boundary timestamps; the original harness, diagnostic and raw timestamps remain visible.', '',
      'Current binaries pass 56 publication cut points, 22 corrupt-catalog rejections, 32 concurrent process kills, 14 source faults, eight source kills and the 30,000-row/300-interval Parquet workflow with 42 DuckDB SQL checks. Process/injected I/O checks do not qualify physical power loss.', '',
      'Randomly chosen cache multipliers can still collide, including deliberately constructed keys; fallback bounds cache memory and preserves correctness, without guaranteeing the fastest latency. Broad matrix shifts on unchanged dense/scan/prefix paths are retained as measurements, not attributed to this cache change. Only DuckDB was freshly competed. The last six-engine network matrix is [0.3.1](PERFORMANCE_031.md); its mixed-write losses remain. No new network capacity, cold-I/O, distributed-scale or production qualification is established.', '',
      '## Reproduce and inspect', '',
      'Run serially with pinned local Python dependencies: checks_041.py, build_source_adapter_041.py, time_041.py, run_041.py, report_041.py, docs_041.py and package_041.py. Never overlap timed database work with compilation, tests or packaging. Matrix helpers reuse retained fixtures or generate fresh small/key-pattern fixtures; controls require retained local datasets and refuse completed-output replacement. Release 0.3.11 uses internal experiment identifier 041.', '',
      '- [Complete gates and scores](benchmarks/cache-041-audit.json)',
      '- [Final collision pairs](benchmarks/cache-041-final-pairs.json)',
      '- [Sparse guards](benchmarks/cache-041-sparse-guard-pairs.json)',
      '- [Scan/dense guards](benchmarks/cache-041-scan-guard-pairs.json)',
      '- [Final stage profiles](benchmarks/cache-041-final-profiles.json)',
      '- [Initial unchanged-binary stage diagnosis](benchmarks/cache-041-baseline-profiles.json)',
      '- [Preserved trial source/build](benchmarks/trial-041-seeded-multiply/proof.json)',
      '- [Trial pairs](benchmarks/cache-041-trial-pairs.json)',
      '- [Trial stage profiles](benchmarks/cache-041-trial-profiles.json)',
      '- [Trial guards](benchmarks/cache-041-trial-guard-pairs.json)',
      '- [Matched 1M shapes](benchmarks/group-041-typed-comparison.json)',
      '- [NYC shapes](benchmarks/group-041-nyc-comparison.json)',
      '- [10M/100M shapes](benchmarks/group-041-large-comparison.json)',
      '- [Prior extra stress shapes](benchmarks/group-041-extended-comparison.json)',
      '- [New key patterns](benchmarks/group-041-patterns-comparison.json)',
      '- [New SQL oracles](benchmarks/cache-041-differential.json)',
      '- [Build provenance](benchmarks/rust-checks-041.json)',
      '- [Timed work order](benchmarks/cache-041-run-order.json)',
      '- [Correctness/recovery order](benchmarks/correctness-041-run-order.json)',
      '- [Preserved report-clock gate failure and repair](benchmarks/report-041-repair.json)',
      '- [Original failing report harness](benchmarks/report-041-before-clock-repair.py)',
      '- [Previous results](BENCHMARK_HISTORY.md)', '']
    (ROOT / 'PERFORMANCE_041.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'version': '0.3.11', 'tests_each_mode': 70,
        'sql_cases_each_reference': 2200, 'primary': score(primary), 'extra': score(extra)}), flush=True)


if __name__ == '__main__':
    main()
