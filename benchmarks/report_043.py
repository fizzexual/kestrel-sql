"""Gate exact fused dense reductions while preserving every matrix loss."""
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
    build = read('benchmarks/rust-checks-043.json')
    assert build['version'] == '0.3.13' and build['rust_tests'] == {'debug': 73, 'release': 73, 'passed': True}
    for name, digest in build['source_sha256'].items():
        assert sha(ROOT / name) == digest, name
    base = read('benchmarks/baseline-0.3.12-provenance.json')
    for name, digest in base['core_source_sha256'].items():
        assert sha(ROOT / 'benchmarks/baseline-0.3.12-source' / name) == digest, name
    assert sha(ROOT.parent / 'kestrel-sql-0.3.12.zip') == base['archive_sha256']
    changed = {name for name, digest in base['core_source_sha256'].items() if sha(ROOT / name) != digest}
    assert changed == {'Cargo.toml', 'Cargo.lock', 'src/archive.rs'}, changed
    old = (ROOT / 'benchmarks/baseline-0.3.12-source/src/archive.rs').read_text(encoding='utf-8')
    new = (ROOT / 'src/archive.rs').read_text(encoding='utf-8')
    marker='    fn update_selected('
    a=old.index(marker,old.index('impl DenseGroups {'))
    b=new.index(marker,new.index('impl DenseGroups {'))
    assert old[:a]==new[:b]
    marker='    fn push_group('
    assert old[old.index(marker):old.index('#[cfg(test)]')]==new[new.index(marker):new.index('#[cfg(test)]')]
    reports = [read(f'benchmarks/group-043-{scope}-comparison.json') for scope in ['typed', 'nyc', 'large', 'extended', 'patterns', 'irregular']]
    assert [len(r['cases']) for r in reports] == [27, 9, 18, 27, 18, 9]
    assert all(r['complete'] and r['binary_sha256']['candidate'] == build['group_probe_sha256'] for r in reports)
    primary = [c for report in reports[:3] for c in summaries(report)]
    extra = summaries(reports[3])
    patterns = summaries(reports[4])
    irregular = summaries(reports[5])
    assert len(patterns) == 10 and len(irregular) == 5
    assert len(primary) == 30 and len(extra) == 15
    controls = {}
    for name, expected_cases, turns, repeats, profiled in [
        ('final-pairs',3,21,11,False),('dense5003-guard-pairs',3,21,11,False),
        ('sparse-guard-pairs',3,21,11,False),('wide-guard-pairs',3,21,11,False),
        ('irregular-guard-pairs',4,21,11,False),('highcard-guard-pairs',2,21,11,False),
        ('scan-guard-pairs',4,21,11,False),('tiny-guard-pairs',3,21,101,False),
        ('large-pairs',2,7,5,False),('final-profiles',3,7,11,True),('large-profiles',1,3,3,True),
    ]:
        report=read(f'benchmarks/dense-043-{name}.json')
        assert report['complete'] and len(report['cases'])==expected_cases
        assert report['binary_sha256']['candidate']==build['group_probe_sha256']
        assert report['methodology']['instrumented']==profiled
        for c in report['cases']:
            assert c['all_results_equal'] and len(c['pairs'])==turns
            for pair in c['pairs']:assert all(len(v['samples_ms'])==repeats for v in pair.values())
            assert all(v['full_scrub_bytes']==report['fixture']['rows']*24 for v in c['pairs'][-1].values())
        controls[name]=report
    assert next(c for c in controls['final-pairs']['cases'] if c['name']=='group_sum')['paired_candidate_over_baseline_median']<0.98
    assert next(c for c in controls['large-pairs']['cases'] if c['name']=='group_sum')['paired_candidate_over_baseline_median']<1.0
    for name,r in controls.items():
        if not r['methodology']['instrumented']:
            assert all(c['paired_candidate_over_baseline_median']<1.1 for c in r['cases']),name
    general = read('benchmarks/archive-043-verification.json')
    groups = read('benchmarks/group-043-differential.json')
    scans = read('benchmarks/scan-043-differential.json')
    assert general['binary_sha256'] == build['cli_sha256'] and general['queries_checked_against_each_reference'] == 500
    assert all(q['passed'] for q in general['queries'])
    for proof, count in [(groups, 500), (scans, 600)]:
        assert proof['binary_sha256'] == build['bridge_sha256'] and proof['complete']
        assert proof['queries_checked_against_each_reference'] == count
        assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in proof['cases'])
    assert all(f['reopen_retry_and_scrub_passed'] for f in scans['fixtures'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in groups['modes'])
    cache = read('benchmarks/cache-043-differential.json')
    assert cache['complete'] and cache['queries_checked_against_each_reference'] == 600
    assert cache['binary_sha256'] == build['bridge_sha256']
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in cache['cases'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in cache['modes'])
    medium = read('benchmarks/medium-043-differential.json')
    assert medium['complete'] and medium['binary_sha256'] == build['bridge_sha256']
    assert medium['queries_checked_against_each_reference'] == 600
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in medium['cases'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in medium['modes'])
    assert medium['exact_medium_signed_wide_group_json_and_reopen_retry']
    dense=read('benchmarks/dense-043-differential.json')
    assert dense['complete'] and dense['binary_sha256']==build['bridge_sha256']
    assert dense['queries_checked_against_each_reference']==600
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in dense['cases'])
    assert all(c['reopen_replay_and_scrub_passed'] for c in dense['modes'])
    assert len(dense['wide_dense_checks'])==2 and all(c['exact_i128_json'] and c['confirmed_retry_reopen_and_scrub'] for c in dense['wide_dense_checks'])
    faults = read('benchmarks/publication-043-faults.json')
    assert faults['binary_sha256'] == build['bridge_sha256'] and faults['fault_driver_sha256'] == build['fault_driver_sha256']
    assert len(faults['cut_points']) == 56 and len(faults['corruption_cases']) == 22
    assert all(c['original_receipts_preserved'] and c['atomic_rows_and_sum'] and c['retry_deduplication_passed'] and c['full_scrub_passed'] for c in faults['cut_points'])
    assert all(c['rejected'] for c in faults['corruption_cases'])
    recovery = read('benchmarks/group-043-recovery.json')
    source = read('benchmarks/source-043-faults.json')
    assert recovery['binary_sha256'] == build['bridge_sha256'] and len(recovery['cycles']) == 32 and not recovery['failed_cases']
    assert source['driver_sha256'] == build['source_fault_driver_sha256']
    assert source['adapter_sha256'] == read('benchmarks/source-043-typed-adapter-build.json')['binary_sha256']
    assert len(source['cases']) == 14 and len(source['kill_cycles']) == 8 and not source['failed_cases']
    pipeline = read('portfolio/source-pipeline-043-results.json')
    assert pipeline['stats']['archive']['rows'] == 30000 and sum(p['committed_batches'] for p in pipeline['positions']) == 300
    assert pipeline['exact_sql_cases_against_duckdb'] == 42 and pipeline['full_scrub_passed']
    assert pipeline['source_positions_and_data_reopen_together'] and pipeline['replay_and_invalid_intervals_passed']
    wire = read('benchmarks/wire-043-audit.json')
    assert wire['cli_sha256'] == build['cli_sha256'] and wire['bridge_sha256'] == build['bridge_sha256']
    assert all(wire[k] for k in ['exact_positive_and_negative_wide_archive_json', 'exact_wide_ram_json', 'sparse_bridge_error_continuity_retry_reopen_and_scrub'])
    timed=read('benchmarks/dense-043-run-order.json')
    qualified=read('benchmarks/correctness-043-run-order.json')
    assert len(timed)==17 and all(r['returncode']==0 for r in timed)
    assert len({r['suite'] for r in qualified if r['returncode']==0})==11
    assert all(a['completed_at_utc']<=b['started_at_utc'] for a,b in zip(timed,timed[1:]))
    assert all(a['completed_at_utc']<=b['started_at_utc'] for a,b in zip(qualified,qualified[1:]))
    adapter=read('benchmarks/source-043-typed-adapter-build.json')
    assert max(r['completed_at_utc'] for r in build['build_run_order'])<=adapter['started_at_utc']<adapter['completed_at_utc']<=timed[0]['started_at_utc']
    assert timed[-1]['completed_at_utc']<=qualified[0]['started_at_utc']
    for r in timed:assert r['harness_sha256']==sha(ROOT/r['command'][1])
    for r in qualified:assert r['harness_sha256']==sha(ROOT/r['command'][1])
    trial=read('benchmarks/trial-043-fused-shared-sum/proof.json')
    assert trial['debug_tests_passed']==73
    for relative,digest in trial['source_sha256'].items():assert sha(ROOT/'benchmarks/trial-043-fused-shared-sum/source'/relative)==digest
    assert sha(Path(trial['group_probe']))==trial['group_probe_sha256']
    assert (ROOT/'benchmarks/trial-043-fused-shared-sum/source/src/archive.rs').read_bytes()==(ROOT/'src/archive.rs').read_bytes()
    assert trial['build_run_order'][-1]['completed_at_utc']<=read('benchmarks/dense-043-trial-10m-pairs.json')['started_at_utc']
    assert read('benchmarks/dense-043-trial-sparse-pairs.json')['completed_at_utc']<=build['build_run_order'][0]['started_at_utc']
    for report in reports:
        assert report['binary_sha256']['baseline'] == base['baseline_binary_sha256']['group-probe.exe']
    for control in controls.values():
        assert control['binary_sha256']['baseline'] == base['baseline_binary_sha256']['group-probe.exe']
    samples = sum(len(q['samples_ms']) for r in reports for c in r['cases'] for q in c['queries'])
    assert samples == 5940
    for report in reports:
        for c in report['cases']:
            assert all(q['all_repeated_and_reference_results_equal'] for q in c['queries'])
            if c['variant'] != 'duckdb':
                fixture=next(f for f in report['fixtures'] if f['label']==c['fixture'])
                assert c['full_scrub_bytes']==fixture['rows']*24
    def sample_count(report):
        return sum(len(v['samples_ms']) for c in report['cases'] for pair in c['pairs'] for v in pair.values())
    assert sum(sample_count(r) for k,r in controls.items() if not r['methodology']['instrumented']) == 23030
    assert sum(sample_count(r) for r in controls.values() if r['methodology']['instrumented'])==480
    audit = {'version':'0.3.13', 'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_sha256':build['source_sha256'], 'rust_tests_each_mode':73,
        'baseline':'0.3.12', 'baseline_provenance':base,
        'primary_score':score(primary), 'extended_score':score(extra), 'pattern_score':score(patterns), 'irregular_score':score(irregular),
        'current_comparison_cases':108, 'current_query_shapes':60, 'current_timed_query_samples':samples,
        'previous_release_scores':{k:read('benchmarks/cache-042-audit.json')[k] for k in ['primary_score','extended_score','pattern_score','irregular_score']},
        'current_comparisons':primary, 'extended_comparisons':extra, 'pattern_comparisons':patterns, 'irregular_comparisons':irregular,
        'paired_controls':{name:[{k:v for k,v in c.items() if k!='pairs'} for c in r['cases']] for name,r in controls.items()},
        'unprofiled_control_samples':23030, 'profiled_control_samples_excluded':480,
        'sql_cases_against_each_reference':3400, 'publication_cut_points':56, 'catalog_corruption_rejections':22,
        'forced_kills':32, 'source_fault_cut_points':14, 'source_forced_kills':8,
        'parquet_rows':30000, 'source_intervals':300, 'parquet_sql_oracles':42,
        'no_compilation_overlap_with_timed_database_work':True,
        'storage_publication_live_source_prefix_reader_and_sparse_helpers_unchanged':True,
        'service_qualification':'No new network requests/s qualification; previous mixed-write losses and stalls remain visible',
        'qualification_harness_failures':[r for r in qualified if r['returncode'] != 0],
        'qualification_harness_repairs':[],
        'preserved_development_trial':'fused-shared-sum: exact source, binary, 10M profiles/pairs, dense5003 and sparse guards retained; final version rebuilt and remeasured',
        'dense_reduction_policy':'If all SUM/AVG projections share one column and no MIN/MAX reduction is needed, validate keys, count rows and update the exact i128 sum in one pass; existing multi-reduction and sparse paths retained',
        'limits':['Warm single-thread queries on one shared Windows computer',
          'Rust direct query timer versus DuckDB Python execute/fetchall; native storage layouts differ',
          'Sparse cache behavior is inherited from 0.3.12, with its existing memory and collision tradeoffs',
          'Only DuckDB freshly compared; last multi-server matrix remains 0.3.1',
          'No new network, cold-I/O, power-loss, distributed-scale or production qualification']}
    (ROOT / 'benchmarks/dense-043-audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')

    lines = ['# 0.3.13: fused dense GROUP SUM and AVG', '',
        'Dense grouping now validates each selected key, counts its rows and updates a shared exact i128 SUM in one pass when the query needs a single SUM/AVG column and no MIN/MAX reduction. Repeated SUM and AVG projections share that state. This avoids filling the intermediate slot vector and revisiting selected rows; its existing reserved capacity remains. Multi-reduction queries, sparse grouping, storage formats, readers, publication, ingestion and source checkpoints are unchanged.', '',
        'The released 0.3.12 ten-million-row GROUP SUM loss was profiled before editing. Its aggregation stage took about 27 ms of an 83 ms instrumented query. The preserved development trial reduced aggregation from 25.153 to 18.388 ms with similar page-read times. These trial results motivated the change; the final version was separately rebuilt and independently timed below.', '',
        'Fresh comparisons retain 108 engine/fixture/round cases, 60 query shapes and 5,940 samples. There are 23,030 additional uninstrumented paired samples, including 10M and 100M rows, and 480 instrumented samples excluded from competitive totals. Matrix cases use three rotated orders, three warmups, eleven samples and one thread. Rust samples time ArchiveSnapshot::query; DuckDB samples include Python execute/fetchall. Native storage layouts differ. Builds, setup, checks and scrubs are untimed. Workloads run serially on this shared Windows computer.', '',
        f"DuckDB scores: matched {score(primary)['wins']} wins / {score(primary)['losses']} losses; prior stress {score(extra)['wins']} / {score(extra)['losses']}; key patterns {score(patterns)['wins']} / {score(patterns)['losses']}; irregular keys {score(irregular)['wins']} / {score(irregular)['losses']}. Every shape and round count is shown below.", '',
        'The released 0.3.12 matrix measured 56 wins and four losses over these same 60 shapes. The current matrix has two additional wins: 10M-row GROUP SUM and NYC all_zones. Both queries use the changed dense shared-SUM path. Stage profiles and 21 alternating pairs specifically validate the 10M improvement; the NYC win is supported by the three rotated matrix rounds and is retained with that narrower evidence. Older raw measurements remain visible and are not replaced.', '',
        '## Final alternating controls', '',
        'Before/after times are medians of pair medians. The paired ratio is the median candidate/baseline ratio within each pair; these summaries can differ under desktop variance. Lower ratios are faster. Most controls use 21 pairs of eleven samples per binary; tiny queries use 21 pairs of 101, and the 100M-row control uses seven pairs of five. Every repeated result matches and every final archive is scrubbed.', '',
        '| Control | Rows | Query | 0.3.12 ms | 0.3.13 ms | Paired candidate / baseline |', '|---|---:|---|---:|---:|---:|']
    for name,r in controls.items():
        if r['methodology']['instrumented']:continue
        for c in r['cases']:
            lines.append(f"| {name} | {r['fixture']['rows']:,} | {c['name']} | {c['baseline_median_ms']:.4f} | {c['candidate_median_ms']:.4f} | {c['paired_candidate_over_baseline_median']:.4f} |")
    lines += ['', '## Stage diagnosis, excluded from competitive results', '',
        '| Rows | Query | Read before / after ms | Selection before / after ms | Aggregate before / after ms |', '|---:|---|---:|---:|---:|']
    for name in ['final-profiles','large-profiles']:
        for c in controls[name]['cases']:
            before=c['stage_median_ms']['baseline'];after=c['stage_median_ms']['candidate']
            lines.append('| '+f"{controls[name]['fixture']['rows']:,}"+' | '+c['name']+' | '+' | '.join(f"{before[stage]:.3f} / {after[stage]:.3f}" for stage in ['page_read_ms','selection_ms','aggregate_ms'])+' |')
    for title,cases in [('Matched matrix',primary),('Prior stress matrix',extra),('Prior key-pattern matrix',patterns),('Irregular signed-key matrix',irregular)]:
        lines += ['', '## '+title, '', '| Fixture | Query | 0.3.12 ms | 0.3.13 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |', '|---|---|---:|---:|---:|---:|---|']
        for c in cases:
            m=c['run_median_ms'];mark='\u2705' if c['candidate_vs_duckdb']=='win' else '\u274c'
            lines.append(f"| {c['fixture']} | {c['query']} | {m['baseline']:.3f} | {m['candidate']:.3f} | {m['duckdb']:.3f} | {c['paired_baseline_over_candidate_median']:.3f}x | {mark}; {c['candidate_faster_than_duckdb_rounds']}/3 rounds |")
    lines += ['', '## Correctness, durability and limits', '',
        'All 73 Rust tests pass in debug and release, formatting and both Clippy configurations. A new independent BTreeMap oracle verifies shared SUM/AVG, exact filtered counts, empty selections, 4,097 rows, signed boundary domains and beyond-i64 outputs. Metadata-bound failures are checked on both the fused and preceding reduction paths. Source hashes prove that only Cargo versions and dense reduction code/tests differ from preserved 0.3.12; sparse helpers, storage, readers, writers, source contract and SQL parsing are unchanged.', '',
        'The frozen final binaries match 3,400 SQL cases against each DuckDB and SQLite: 500 general, 500 grouping, 600 sparse key patterns, 600 medium groups, 600 focused dense/shared-SUM cases and 600 scans. Two independent 411-row/137-group signed-boundary fixtures verify exact beyond-i64 integer JSON, shared AVG, repeated SUM, confirmed retry and reopen through the actual dense bridge plan. Existing sparse and medium wide-JSON checks remain. All current binaries pass 56 publication cuts, 22 catalog corruption rejections, 32 process kills, 14 source faults, eight source kills and the 30,000-row/300-interval Parquet workflow with 42 SQL checks. Injected faults and process kills do not qualify physical power loss.', '',
        'The optimization adds no per-query allocation. The previous reserved intermediate capacity remains, and mixed-reduction queries continue using the preceding path. Broad timing shifts on unchanged sparse/scan/mixed paths cannot be attributed to this change. Every loss, guard and development trial remains visible. Only DuckDB is freshly competed; the last multi-server network comparison remains [0.3.1](PERFORMANCE_031.md), including mixed-write losses and stalls. Network requests/s, cold I/O, distributed scale and production readiness remain unqualified.', '',
        '## Reproduce and inspect', '',
        'Run checks_043.py, build_source_adapter_043.py, time_043.py, run_043.py, report_043.py, docs_043.py and package_043.py serially with the pinned local Python dependencies. Completed outputs and release archives are immutable. Controls reuse retained fixtures; matrix scripts can seed independently. Never overlap compilation, tests or packaging with timed database work. Release 0.3.13 uses experiment identifier 043.', '',
        '- [Complete gates and scores](benchmarks/dense-043-audit.json)',
        '- [10M-row final pairs](benchmarks/dense-043-final-pairs.json)',
        '- [100M-row final pairs](benchmarks/dense-043-large-pairs.json)',
        '- [10M-row final profiles](benchmarks/dense-043-final-profiles.json)',
        '- [100M-row final profiles](benchmarks/dense-043-large-profiles.json)',
        '- [Dense 5,003-key guard](benchmarks/dense-043-dense5003-guard-pairs.json)',
        '- [Sparse guard](benchmarks/dense-043-sparse-guard-pairs.json)',
        '- [Wide sparse guard](benchmarks/dense-043-wide-guard-pairs.json)',
        '- [Irregular signed-key guard](benchmarks/dense-043-irregular-guard-pairs.json)',
        '- [High-cardinality guard](benchmarks/dense-043-highcard-guard-pairs.json)',
        '- [Scan guard](benchmarks/dense-043-scan-guard-pairs.json)',
        '- [Tiny-query guard](benchmarks/dense-043-tiny-guard-pairs.json)',
        '- [Shared-SUM SQL and signed wide JSON qualification](benchmarks/dense-043-differential.json)',
        '- [Released baseline profiles](benchmarks/dense-043-baseline-profiles.json)',
        '- [Preserved development trial source and build](benchmarks/trial-043-fused-shared-sum/proof.json)',
        '- [Trial 10M pairs](benchmarks/dense-043-trial-10m-pairs.json)',
        '- [Trial stage profiles](benchmarks/dense-043-trial-10m-profiles.json)',
        '- [Trial dense guard](benchmarks/dense-043-trial-dense5003-pairs.json)',
        '- [Trial sparse guard](benchmarks/dense-043-trial-sparse-pairs.json)',
        '- [Build provenance](benchmarks/rust-checks-043.json)',
        '- [Timed work order](benchmarks/dense-043-run-order.json)',
        '- [Qualification work order](benchmarks/correctness-043-run-order.json)',
        '- [All previous results and unsuccessful evidence](BENCHMARK_HISTORY.md)', '']
    (ROOT/'PERFORMANCE_043.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'version':'0.3.13','rust_tests_each_mode':73,'sql_cases_each_reference':3400,
        'primary':score(primary),'extra':score(extra),'patterns':score(patterns),'irregular':score(irregular)}),flush=True)

if __name__=='__main__':main()
