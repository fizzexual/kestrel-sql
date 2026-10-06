"""Gate the scan candidate and retain every matrix loss and unsuccessful trial."""
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
    build = read('benchmarks/rust-checks-040.json')
    assert build['version'] == '0.3.10' and build['rust_tests'] == {'debug': 70, 'release': 70, 'passed': True}
    for name, digest in build['source_sha256'].items():
        assert sha(ROOT / name) == digest, name
    base = read('benchmarks/baseline-0.3.9-provenance.json')
    for name, digest in base['core_source_sha256'].items():
        assert sha(ROOT / 'benchmarks/baseline-0.3.9-source' / name) == digest, name
    assert sha(ROOT.parent / 'kestrel-sql-0.3.9.zip') == base['archive_sha256']
    changed = {name for name, digest in base['core_source_sha256'].items() if sha(ROOT / name) != digest}
    assert changed == {'Cargo.toml', 'Cargo.lock', 'src/archive.rs', 'tests/archive.rs'}, changed
    old = (ROOT / 'benchmarks/baseline-0.3.9-source/src/archive.rs').read_text(encoding='utf-8')
    new = (ROOT / 'src/archive.rs').read_text(encoding='utf-8')
    assert old[:old.index('    fn query_inner<const PROFILE: bool>(')] == new[:new.index('    fn query_inner<const PROFILE: bool>(')]
    assert old[old.index('    /// Read every data block'):old.index('#[cfg(test)]')] == new[new.index('    /// Read every data block'):new.index('#[cfg(test)]')].replace(new[new.index('\nfn select_matching_range('):new.index('\n#[cfg(test)]')], '')
    reports = [read(f'benchmarks/group-040-{scope}-comparison.json') for scope in ['typed', 'nyc', 'large', 'extended']]
    assert [len(r['cases']) for r in reports] == [27, 9, 18, 27]
    assert all(r['complete'] and r['binary_sha256']['candidate'] == build['group_probe_sha256'] for r in reports)
    primary = [c for report in reports[:3] for c in summaries(report)]
    extra = summaries(reports[3])
    assert len(primary) == 30 and len(extra) == 15
    controls = {}
    for name, expected_cases, turns, repeats, profiled in [
        ('final-pairs', 4, 21, 11, False), ('final-large-pairs', 1, 7, 5, False),
        ('anchor038-pairs', 2, 21, 11, False), ('final-profiles', 4, 7, 11, True),
    ]:
        report = read(f'benchmarks/scan-040-{name}.json')
        assert report['complete'] and len(report['cases']) == expected_cases
        assert report['binary_sha256']['candidate'] == build['group_probe_sha256']
        assert report['methodology']['instrumented'] == profiled
        for case in report['cases']:
            assert case['all_results_equal'] and len(case['pairs']) == turns
            for pair in case['pairs']:
                assert all(len(p['samples_ms']) == repeats for p in pair.values())
            assert all(p['full_scrub_bytes'] == report['fixture']['rows'] * 24 for p in case['pairs'][-1].values())
        controls[name] = report
    for name in ['final-pairs', 'final-large-pairs']:
        assert next(c for c in controls[name]['cases'] if c['name'] == 'unordered')['paired_candidate_over_baseline_median'] < 1, name
    general = read('benchmarks/archive-040-verification.json')
    groups = read('benchmarks/group-040-differential.json')
    scans = read('benchmarks/scan-040-differential.json')
    assert general['binary_sha256'] == build['cli_sha256'] and general['queries_checked_against_each_reference'] == 500
    assert all(q['passed'] for q in general['queries'])
    for proof, count in [(groups, 500), (scans, 600)]:
        assert proof['binary_sha256'] == build['bridge_sha256'] and proof['complete']
        assert proof['queries_checked_against_each_reference'] == count
        assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in proof['cases'])
    assert all(f['reopen_retry_and_scrub_passed'] for f in scans['fixtures'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in groups['modes'])
    faults = read('benchmarks/publication-040-faults.json')
    assert faults['binary_sha256'] == build['bridge_sha256'] and faults['fault_driver_sha256'] == build['fault_driver_sha256']
    assert len(faults['cut_points']) == 56 and len(faults['corruption_cases']) == 22
    assert all(c['original_receipts_preserved'] and c['atomic_rows_and_sum'] and c['retry_deduplication_passed'] and c['full_scrub_passed'] for c in faults['cut_points'])
    assert all(c['rejected'] for c in faults['corruption_cases'])
    recovery = read('benchmarks/group-040-recovery.json')
    source = read('benchmarks/source-040-faults.json')
    assert recovery['binary_sha256'] == build['bridge_sha256'] and len(recovery['cycles']) == 32 and not recovery['failed_cases']
    assert len(source['cases']) == 14 and len(source['kill_cycles']) == 8 and not source['failed_cases']
    pipeline = read('portfolio/source-pipeline-040-results.json')
    assert pipeline['stats']['archive']['rows'] == 30000 and sum(p['committed_batches'] for p in pipeline['positions']) == 300
    assert pipeline['exact_sql_cases_against_duckdb'] == 42 and pipeline['full_scrub_passed']
    assert pipeline['source_positions_and_data_reopen_together'] and pipeline['replay_and_invalid_intervals_passed']
    wire = read('benchmarks/wire-040-audit.json')
    assert wire['cli_sha256'] == build['cli_sha256'] and wire['bridge_sha256'] == build['bridge_sha256']
    assert all(wire[k] for k in ['exact_positive_and_negative_wide_archive_json', 'exact_wide_ram_json', 'sparse_bridge_error_continuity_retry_reopen_and_scrub'])
    timed = read('benchmarks/scan-040-run-order.json')
    qualified = read('benchmarks/correctness-040-run-order.json')
    assert len(timed) == 8 and all(r['returncode'] == 0 for r in timed)
    assert len({r['suite'] for r in qualified if r['returncode'] == 0}) == 8
    assert all(a['completed_at_utc'] < b['started_at_utc'] for a, b in zip(timed, timed[1:]))
    adapter = read('benchmarks/source-040-typed-adapter-build.json')
    assert max(r['completed_at_utc'] for r in build['build_run_order']) < adapter['started_at_utc'] < adapter['completed_at_utc'] < timed[0]['started_at_utc']
    assert timed[-1]['completed_at_utc'] < qualified[0]['started_at_utc']
    assert all(a['completed_at_utc'] < b['started_at_utc'] for a, b in zip(qualified, qualified[1:]))
    for name in ['noinline', 'fused-first']:
        trial = read(f'benchmarks/trial-040-{name}/proof.json')
        for relative, digest in trial['source_sha256'].items():
            assert sha(ROOT / f'benchmarks/trial-040-{name}/source' / relative) == digest
        assert sha(ROOT / f'bin/trials/scan-040-{name}/group-probe.exe') == trial['group_probe_sha256']
        report = read(f'benchmarks/scan-040-{name}-pairs.json')
        assert report['complete'] and report['binary_sha256']['candidate'] == trial['group_probe_sha256']
    audit = {
        'version': '0.3.10', 'recorded_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_sha256': build['source_sha256'], 'rust_tests_each_mode': 70,
        'current_cases': 81, 'current_query_shapes': 45, 'current_timed_query_samples': 4455,
        'current_paired_control_samples': 2842, 'instrumented_control_samples_excluded': 616,
        'primary_score': score(primary), 'extended_score': score(extra), 'summaries': primary + extra,
        'paired_controls': {name: r['cases'] for name, r in controls.items()},
        'sql_differential_against_each_reference': 1600, 'ram_filter_boundary_comparisons': 360,
        'publication_fault_cut_points': 56, 'catalog_corruption_rejections': 22,
        'concurrent_forced_kills': 32, 'source_fault_cut_points': 14, 'source_forced_kills': 8,
        'parquet_rows': 30000, 'source_intervals': 300, 'parquet_sql_oracles': 42,
        'no_compilation_overlap_with_timed_database_work': True,
        'storage_publication_live_source_prefix_reader_and_group_helpers_unchanged': True,
        'service_qualification': 'No new network requests/s qualification; previous mixed-write losses and stalls remain visible',
        'qualification_harness_failures': [r for r in qualified if r['returncode'] != 0],
        'rejected_trial': 'noinline: no reliable end-to-end gain; exact source, binaries and measurements preserved',
        'limits': ['Warm single-thread queries on one shared Windows computer',
            'Rust direct query timer versus DuckDB Python execute/fetchall; native storage layouts differ',
            'Only DuckDB freshly compared; last multi-server matrix remains 0.3.1',
            'No new network, cold-I/O, power-loss, distributed-scale or production qualification'],
    }
    (ROOT / 'benchmarks/scan-040-audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    lines = ['# 0.3.10: direct first-filter selection', '',
        'Streaming scans now generate row positions directly from the first predicate not already enforced by sorted bounds. Later predicates retain those positions. This removes a full range fill and avoids indirect value reads on the first comparison. All six integer operators, signed values, filter order, partial blocks and independently sorted overlapping segments keep their SQL meaning. Group states, prefix queries, readers, storage/publication formats, live/source contracts and default policy are unchanged.', '',
        'The 0.3.9 unordered-scan regression motivated stage profiling. The separate-function `inline(never)` trial produced no reliable gain and is retained. The direct-selection trial reduced the selection stage; final binaries were rebuilt and measured again. [Rust documents inline attributes as compiler hints](https://doc.rust-lang.org/reference/attributes/codegen.html#the-inline-attribute); outlining and operator fusion are established techniques, with no novelty claim.', '',
        'Fresh comparisons retain 81 sequential engine/fixture/round cases, 45 shapes and 4,455 samples, plus 2,842 uninstrumented paired control samples. Three rotated engine orders, three warmups and eleven samples are used for every matrix shape. All queries use one thread and warm caches on this shared Windows computer. Rust samples cover ArchiveSnapshot::query, excluding framing/assertions; DuckDB samples include Python execute/fetchall, use native compression and a 256 MB buffer limit. Full scrubs and setup are untimed. Stage timings are instrumented and excluded from competitive totals.', '',
        f"The matched matrix has {score(primary)['wins']} median DuckDB wins and {score(primary)['losses']} {'loss' if score(primary)['losses']==1 else 'losses'}; the extra stress matrix has {score(extra)['wins']} wins and {score(extra)['losses']} losses. Every round count and loss is retained below. These scores describe this run, not universal performance.", '']
    for title, name in [('Final 1M-row pairs against 0.3.9', 'final-pairs'),
                        ('Final 100M-row unordered pairs against 0.3.9', 'final-large-pairs'),
                        ('Checks against pre-regression 0.3.8', 'anchor038-pairs')]:
        lines += ['## ' + title, '',
            'Alternating same-archive pairs; each engine opens and closes sequentially. A final/baseline ratio above 1 means slower. Paired ratios and ratios of displayed median times can differ.', '',
            '| Query | Baseline ms | 0.3.10 ms | Paired final/baseline |', '|---|---:|---:|---:|']
        for c in controls[name]['cases']:
            lines.append(f"| {c['name']} | {c['baseline_median_ms']:.3f} | {c['candidate_median_ms']:.3f} | {c['paired_candidate_over_baseline_median']:.4f} |")
        lines += ['']
    lines += ['## Instrumented 1M-row stage checks', '',
        'Median stage times from seven alternating profiled pairs; these samples are excluded from competitive timing totals.', '',
        '| Query | Read 0.3.9 ms | Read 0.3.10 ms | Select 0.3.9 ms | Select 0.3.10 ms | Aggregate 0.3.9 ms | Aggregate 0.3.10 ms |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for c in controls['final-profiles']['cases']:
        before = c['stage_median_ms']['baseline']
        after = c['stage_median_ms']['candidate']
        values = [before['page_read_ms'], after['page_read_ms'], before['selection_ms'], after['selection_ms'], before['aggregate_ms'], after['aggregate_ms']]
        lines.append('| ' + c['name'] + ' | ' + ' | '.join(f'{value:.3f}' for value in values) + ' |')
    lines += ['']
    for title, cases in [('Matched matrix', primary), ('Additional stress matrix', extra)]:
        lines += ['## ' + title, '', '| Fixture | Query | 0.3.9 ms | 0.3.10 ms | DuckDB ms | Paired before/after | vs DuckDB |', '|---|---|---:|---:|---:|---:|---|']
        for c in cases:
            m = c['run_median_ms']
            mark = '\u2705' if c['candidate_vs_duckdb'] == 'win' else '\u274c'
            lines.append(f"| {c['fixture']} | {c['query']} | {m['baseline']:.3f} | {m['candidate']:.3f} | {m['duckdb']:.3f} | {c['paired_baseline_over_candidate_median']:.3f}x | {mark}; {c['candidate_faster_than_duckdb_rounds']}/3 rounds |")
        lines += ['']
    lines += ['## Correctness, recovery and limitations', '',
        'All 70 Rust tests pass in debug/release, with formatting and default/fault-feature Clippy. The added public-API regression test compares 180 signed-edge/filter-order/partial-block queries with the independent RAM engine, then repeats all 180 after reopening. The final CLI/bridge also match 1,600 SQL cases against each DuckDB and SQLite: 500 general archive queries, 500 expanded/signed-sparse groups and 600 scan/selectivity cases. Reopen, confirmed retries, full CRC scrubs and exact positive/negative i128 JSON outputs pass.', '',
        'Current binaries pass 56 publication cut points, 22 corrupt-catalog rejections, 32 concurrent process kills, 14 source fault points, eight source kills and the 30,000-row/300-interval Parquet pipeline with 42 SQL oracles. These checks cover process and injected I/O failures; they do not qualify physical power loss. Storage and writer policy are unchanged.', '',
        'The unchanged unfiltered-group controls are used to detect broad code-generation effects; their measured ratios remain evidence, even when they fluctuate. Profiling alone is not an end-to-end speed claim. No new network capacity, sustained mixed-write latency, cold-I/O, distributed-scale or production readiness is established. Older service failures remain in the history. The previous multi-server comparison is [0.3.1](PERFORMANCE_031.md).', '',
        '## Reproduce and inspect', '',
        'Run serially with the pinned local Python dependencies: `checks_040.py`, `build_source_adapter_040.py`, `time_040.py`, `run_040.py`, `report_040.py`, `docs_040.py`, then `package_040.py`. Never overlap build, test, packaging or any heavy job with timed workloads. Matrix helpers accept configurable large/NYC fixture roots and can regenerate small fixtures. Controls require local retained datasets and refuse completed-output replacement. Current release is 0.3.10; 040 is the internal experiment/evidence identifier.', '',
        '- [All current summaries and gates](benchmarks/scan-040-audit.json)',
        '- [Final paired controls](benchmarks/scan-040-final-pairs.json)',
        '- [Final 100M-row controls](benchmarks/scan-040-final-large-pairs.json)',
        '- [Pre-regression 0.3.8 controls](benchmarks/scan-040-anchor038-pairs.json)',
        '- [Final stage profiles](benchmarks/scan-040-final-profiles.json)',
        '- [Initial stage diagnosis](benchmarks/scan-040-stage-profiles.json)',
        '- [Rejected outlining trial](benchmarks/trial-040-noinline/proof.json)',
        '- [Rejected trial timings](benchmarks/scan-040-noinline-pairs.json)',
        '- [Direct-selection trial](benchmarks/trial-040-fused-first/proof.json)',
        '- [Initial direct-selection 100M-row pairs](benchmarks/scan-040-fused-first-large-pairs.json)',
        '- [1M-row full matrix](benchmarks/group-040-typed-comparison.json)',
        '- [NYC full matrix](benchmarks/group-040-nyc-comparison.json)',
        '- [10M/100M-row full matrix](benchmarks/group-040-large-comparison.json)',
        '- [Wide/collision/high-cardinality matrix](benchmarks/group-040-extended-comparison.json)',
        '- [New scan SQL oracle cases](benchmarks/scan-040-differential.json)',
        '- [Build order and hashes](benchmarks/rust-checks-040.json)',
        '- [Timed work order](benchmarks/scan-040-run-order.json)',
        '- [Correctness and recovery order](benchmarks/correctness-040-run-order.json)',
        '- [Complete historical index](BENCHMARK_HISTORY.md)', '']
    (ROOT / 'PERFORMANCE_040.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'version': '0.3.10', 'tests_each_mode': 70,
        'sql_cases_each_reference': 1600, 'primary': score(primary), 'extra': score(extra)}), flush=True)


if __name__ == '__main__':
    main()
