"""Gate adaptive sparse reductions while preserving every matrix loss and failed trial."""
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
    build = read('benchmarks/rust-checks-044.json')
    assert build['version'] == '0.3.14' and build['rust_tests'] == {'debug': 74, 'release': 74, 'passed': True}
    for name, digest in build['source_sha256'].items():
        assert sha(ROOT / name) == digest, name
    base = read('benchmarks/baseline-0.3.13-provenance.json')
    for name, digest in base['core_source_sha256'].items():
        assert sha(ROOT / 'benchmarks/baseline-0.3.13-source' / name) == digest, name
    assert sha(ROOT.parent / 'kestrel-sql-0.3.13.zip') == base['archive_sha256']
    changed = {name for name, digest in base['core_source_sha256'].items() if sha(ROOT / name) != digest}
    assert changed == {'Cargo.toml', 'Cargo.lock', 'src/archive.rs'}, changed
    old = (ROOT / 'benchmarks/baseline-0.3.13-source/src/archive.rs').read_text(encoding='utf-8')
    new = (ROOT / 'src/archive.rs').read_text(encoding='utf-8')
    marker='impl SparseGroups {'
    assert old[:old.index(marker)]==new[:new.index(marker)]
    marker='fn group_cache_slot('
    assert old[old.index(marker):old.index('#[cfg(test)]')]==new[new.index(marker):new.index('#[cfg(test)]')]
    reports = [read(f'benchmarks/group-044-{scope}-comparison.json') for scope in ['typed', 'nyc', 'large', 'extended', 'patterns', 'irregular']]
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
        ('final-pairs',3,21,11,False),('wide-pairs',3,21,11,False),('irregular-pairs',4,21,11,False),
        ('highcard-guard-pairs',2,21,11,False),('dense-guard-pairs',3,21,11,False),('scan-guard-pairs',4,21,11,False),
        ('tiny-guard-pairs',3,21,101,False),('10m-guard-pairs',3,21,11,False),('100m-guard-pairs',2,7,5,False),
        ('final-profiles',3,7,11,True),('irregular-profiles',3,7,11,True),
    ]:
        report=read(f'benchmarks/sparse-044-{name}.json')
        assert report['complete'] and len(report['cases'])==expected_cases
        assert report['binary_sha256']['candidate']==build['group_probe_sha256']
        assert report['methodology']['instrumented']==profiled
        for c in report['cases']:
            assert c['all_results_equal'] and len(c['pairs'])==turns
            for pair in c['pairs']:assert all(len(v['samples_ms'])==repeats for v in pair.values())
            assert all(v['full_scrub_bytes']==report['fixture']['rows']*24 for v in c['pairs'][-1].values())
        controls[name]=report
    for name in ['final-pairs','wide-pairs']:
        assert next(c for c in controls[name]['cases'] if c['name']=='group_sum')['paired_candidate_over_baseline_median']<0.98
    for name,r in controls.items():
        if not r['methodology']['instrumented']:
            assert all(c['paired_candidate_over_baseline_median']<1.1 for c in r['cases']),name
    general = read('benchmarks/archive-044-verification.json')
    groups = read('benchmarks/group-044-differential.json')
    scans = read('benchmarks/scan-044-differential.json')
    assert general['binary_sha256'] == build['cli_sha256'] and general['queries_checked_against_each_reference'] == 500
    assert all(q['passed'] for q in general['queries'])
    for proof, count in [(groups, 500), (scans, 600)]:
        assert proof['binary_sha256'] == build['bridge_sha256'] and proof['complete']
        assert proof['queries_checked_against_each_reference'] == count
        assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in proof['cases'])
    assert all(f['reopen_retry_and_scrub_passed'] for f in scans['fixtures'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in groups['modes'])
    cache = read('benchmarks/cache-044-differential.json')
    assert cache['complete'] and cache['queries_checked_against_each_reference'] == 600
    assert cache['binary_sha256'] == build['bridge_sha256']
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in cache['cases'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in cache['modes'])
    medium = read('benchmarks/medium-044-differential.json')
    assert medium['complete'] and medium['binary_sha256'] == build['bridge_sha256']
    assert medium['queries_checked_against_each_reference'] == 600
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in medium['cases'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in medium['modes'])
    assert medium['exact_medium_signed_wide_group_json_and_reopen_retry']
    dense=read('benchmarks/dense-044-differential.json')
    assert dense['complete'] and dense['binary_sha256']==build['bridge_sha256']
    assert dense['queries_checked_against_each_reference']==600
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in dense['cases'])
    assert all(c['reopen_replay_and_scrub_passed'] for c in dense['modes'])
    assert len(dense['wide_dense_checks'])==2 and all(c['exact_i128_json'] and c['confirmed_retry_reopen_and_scrub'] for c in dense['wide_dense_checks'])
    focused=read('benchmarks/sparse-044-differential.json')
    assert focused['complete'] and focused['binary_sha256']==build['bridge_sha256']
    assert focused['queries_checked_against_each_reference']==600
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in focused['cases'])
    assert all(m['reopen_replay_and_scrub_passed'] for m in focused['modes'])
    assert focused['exact_sparse_shared_signed_wide_group_json_and_reopen_retry']
    faults = read('benchmarks/publication-044-faults.json')
    assert faults['binary_sha256'] == build['bridge_sha256'] and faults['fault_driver_sha256'] == build['fault_driver_sha256']
    assert len(faults['cut_points']) == 56 and len(faults['corruption_cases']) == 22
    assert all(c['original_receipts_preserved'] and c['atomic_rows_and_sum'] and c['retry_deduplication_passed'] and c['full_scrub_passed'] for c in faults['cut_points'])
    assert all(c['rejected'] for c in faults['corruption_cases'])
    recovery = read('benchmarks/group-044-recovery.json')
    source = read('benchmarks/source-044-faults.json')
    assert recovery['binary_sha256'] == build['bridge_sha256'] and len(recovery['cycles']) == 32 and not recovery['failed_cases']
    assert source['driver_sha256'] == build['source_fault_driver_sha256']
    assert source['adapter_sha256'] == read('benchmarks/source-044-typed-adapter-build.json')['binary_sha256']
    assert len(source['cases']) == 14 and len(source['kill_cycles']) == 8 and not source['failed_cases']
    pipeline = read('portfolio/source-pipeline-044-results.json')
    assert pipeline['stats']['archive']['rows'] == 30000 and sum(p['committed_batches'] for p in pipeline['positions']) == 300
    assert pipeline['exact_sql_cases_against_duckdb'] == 42 and pipeline['full_scrub_passed']
    assert pipeline['source_positions_and_data_reopen_together'] and pipeline['replay_and_invalid_intervals_passed']
    wire = read('benchmarks/wire-044-audit.json')
    assert wire['cli_sha256'] == build['cli_sha256'] and wire['bridge_sha256'] == build['bridge_sha256']
    assert all(wire[k] for k in ['exact_positive_and_negative_wide_archive_json', 'exact_wide_ram_json', 'sparse_bridge_error_continuity_retry_reopen_and_scrub'])
    timed=read('benchmarks/sparse-044-run-order.json')
    qualified=read('benchmarks/correctness-044-run-order.json')
    assert len(timed)==17 and all(r['returncode']==0 for r in timed)
    assert len({r['suite'] for r in qualified if r['returncode']==0})==12
    assert all(a['completed_at_utc']<=b['started_at_utc'] for a,b in zip(timed,timed[1:]))
    assert all(a['completed_at_utc']<=b['started_at_utc'] for a,b in zip(qualified,qualified[1:]))
    adapter=read('benchmarks/source-044-typed-adapter-build.json')
    assert max(r['completed_at_utc'] for r in build['build_run_order'])<=adapter['started_at_utc']<adapter['completed_at_utc']<=timed[0]['started_at_utc']
    assert timed[-1]['completed_at_utc']<=qualified[0]['started_at_utc']
    for r in timed:assert r['harness_sha256']==sha(ROOT/r['command'][1])
    for r in qualified:assert r['harness_sha256']==sha(ROOT/r['command'][1])
    for trial_name,tests in [('write-on-miss',73),('fused-shared-sum',74),('typed-shared-sum',74),('small-cache-shared-sum',74)]:
        trial=read(f'benchmarks/trial-044-{trial_name}/proof.json')
        assert trial['debug_tests_passed']==tests
        for relative,digest in trial['source_sha256'].items():assert sha(ROOT/f'benchmarks/trial-044-{trial_name}/source'/relative)==digest
        assert sha(Path(trial['group_probe']))==trial['group_probe_sha256']
        order=read(f'benchmarks/sparse-044-{trial_name}-run-order.json')
        assert len(order)==(5 if trial_name=='write-on-miss' else 6) and all(r['returncode']==0 for r in order)
        assert trial['build_run_order'][-1]['completed_at_utc']<=order[0]['started_at_utc']
        assert all(a['completed_at_utc']<=b['started_at_utc'] for a,b in zip(order,order[1:]))
        for r in order:assert r['harness_sha256']==sha(ROOT/r['command'][1])
    selected=(ROOT/'benchmarks/trial-044-small-cache-shared-sum/source/src/archive.rs').read_text(encoding='utf-8')
    assert selected[:selected.index('#[cfg(test)]')]==new[:new.index('#[cfg(test)]')]
    assert read('benchmarks/sparse-044-small-cache-shared-sum-run-order.json')[-1]['completed_at_utc']<=build['build_run_order'][0]['started_at_utc']
    rejected=read('benchmarks/sparse-044-rejected-enum-fusion.json')
    assert rejected['status']=='rejected development trial'
    assert rejected['ratios']['wide']['group_sum']>1.08
    assert read('benchmarks/sparse-044-rejected-wide-typed-fusion.json')['status']=='not selected development trial'
    repair=read('benchmarks/sparse-044-clippy-repair.json')
    failed_build=read('benchmarks/build-044-before-clippy-repair-logs/run-order.json')
    assert len(failed_build)==4 and failed_build[-1]['returncode']!=0
    assert failed_build[-1]['completed_at_utc']<=build['build_run_order'][0]['started_at_utc']
    assert repair['production_code_before_cfg_test_byte_identical'] and repair['after_sha256']==sha(ROOT/'src/archive.rs')
    assert repair['before_sha256']==sha(ROOT/'benchmarks/trial-044-small-cache-shared-sum/source/src/archive.rs')
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
    assert sum(sample_count(r) for r in controls.values() if r['methodology']['instrumented'])==924
    audit = {'version':'0.3.14', 'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_sha256':build['source_sha256'], 'rust_tests_each_mode':74,
        'baseline':'0.3.13', 'baseline_provenance':base,
        'primary_score':score(primary), 'extended_score':score(extra), 'pattern_score':score(patterns), 'irregular_score':score(irregular),
        'current_comparison_cases':108, 'current_query_shapes':60, 'current_timed_query_samples':samples,
        'previous_release_scores':{k:read('benchmarks/dense-043-audit.json')[k] for k in ['primary_score','extended_score','pattern_score','irregular_score']},
        'current_comparisons':primary, 'extended_comparisons':extra, 'pattern_comparisons':patterns, 'irregular_comparisons':irregular,
        'paired_controls':{name:[{k:v for k,v in c.items() if k!='pairs'} for c in r['cases']] for name,r in controls.items()},
        'observed_slower_unprofiled_controls':[
            {'control':name,'rows':r['fixture']['rows'],'query':c['name'],
             'paired_candidate_over_baseline_median':c['paired_candidate_over_baseline_median']}
            for name,r in controls.items() if not r['methodology']['instrumented']
            for c in r['cases'] if c['paired_candidate_over_baseline_median']>1.0],
        'unprofiled_control_samples':23030, 'profiled_control_samples_excluded':924,
        'sql_cases_against_each_reference':4000, 'publication_cut_points':56, 'catalog_corruption_rejections':22,
        'forced_kills':32, 'source_fault_cut_points':14, 'source_forced_kills':8,
        'parquet_rows':30000, 'source_intervals':300, 'parquet_sql_oracles':42,
        'no_compilation_overlap_with_timed_database_work':True,
        'storage_publication_live_source_prefix_reader_and_dense_helpers_unchanged':True,
        'service_qualification':'No new network requests/s qualification; previous mixed-write losses and stalls remain visible',
        'qualification_harness_failures':[r for r in qualified if r['returncode'] != 0],
        'qualification_harness_repairs':[], 'test_only_clippy_repair':repair, 'preserved_initial_build_failure':failed_build,
        'preserved_development_trials':['write-on-miss: useful baseline for cache stores','fused-shared-sum: rejected for wide and high-cardinality SUM regressions','typed-shared-sum: small-group benefit, not selected for wider kernels','small-cache-shared-sum: selected adaptive kernel, separately rebuilt and remeasured'],
        'sparse_reduction_policy':'Only cache misses rewrite tags. At small-cache block entry, a single shared SUM/AVG column can reduce directly in the lookup loop; wider and fallback modes retain the preceding two-pass mapper.',
        'limits':['Warm single-thread queries on one shared Windows computer',
          'Rust direct query timer versus DuckDB Python execute/fetchall; native storage layouts differ',
          'Cache budgets and seeded exact tags are retained; small-cache block fusion changes query code without new allocations',
          'Only DuckDB freshly compared; last multi-server matrix remains 0.3.1',
          'No new network, cold-I/O, power-loss, distributed-scale or production qualification']}
    (ROOT / 'benchmarks/sparse-044-audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')


    lines=['# 0.3.14: adaptive sparse SUM kernels and fewer cache writes','',
        'Exact tagged cache hits now retain their existing key/slot entry; only misses populate or replace it. At a block entered with the small cache active, a single shared SUM/AVG column can update exact counts and its typed i128 sum during key lookup. Repeated SUM/AVG projections share state. Larger-cache and plain-hash modes retain the preceding two-pass mapper; mixed reductions retain their preceding arrays. The selected block finishes its kernel before growth or collision fallback changes the next block. Cache budgets, seeded tags, randomized authoritative HashMap, dense grouping, readers, storage and writers are unchanged. Existing reserved slot capacity remains; no extra query allocation is introduced.','',
        'Profiles of released 0.3.13 put about 13 ms of a 21 ms irregular-key SUM query in aggregation. Skipping redundant cache stores improved the first trial. A general enum-based fused loop then regressed wide SUM about 9% and high-cardinality SUM about 8.5%; its complete source, binary and timings are preserved. Moving the typed vector outside dispatch helped small groups but still failed to improve irregular SUM and slowed high-cardinality SUM about 3.8%. The selected trial limits fusion to the small-cache kernel and keeps the earlier wider mapper. It passes the trial guards, then is independently rebuilt and remeasured below.','',
        'Fresh comparisons retain 108 engine/fixture/round cases, 60 shapes and 5,940 samples. Additional uninstrumented controls retain 23,030 samples; 924 instrumented samples are excluded from competitive totals. Matrix cases use three rotated orders, three warmups, eleven samples and one thread. Rust timers measure ArchiveSnapshot::query; DuckDB timers include Python execute/fetchall. Native storage layouts differ. Builds, setup, result checks and scrubs are untimed, and workloads run serially on this shared Windows computer.','',
        f"DuckDB scores: matched {score(primary)['wins']} wins / {score(primary)['losses']} losses; prior stress {score(extra)['wins']} / {score(extra)['losses']}; patterns {score(patterns)['wins']} / {score(patterns)['losses']}; irregular keys {score(irregular)['wins']} / {score(irregular)['losses']}. The released 0.3.13 matrix measured 58 wins and two losses; older measurements remain preserved.",'',
        '## Final alternating controls','',
        'Before/after times are medians of pair medians. The paired ratio is the median candidate/baseline ratio within each pair; these summaries can differ during desktop variance. Lower ratios are faster. Controls use 21 pairs of eleven samples per binary, except tiny queries (21 pairs of 101) and 100M rows (seven pairs of five). Every repeated result matches, and final archives are scrubbed.','',
        '| Control | Rows | Query | 0.3.13 ms | 0.3.14 ms | Paired candidate / baseline |','|---|---:|---|---:|---:|---:|']
    for name,r in controls.items():
        if r['methodology']['instrumented']:continue
        for c in r['cases']:lines.append(f"| {name} | {r['fixture']['rows']:,} | {c['name']} | {c['baseline_median_ms']:.4f} | {c['candidate_median_ms']:.4f} | {c['paired_candidate_over_baseline_median']:.4f} |")
    slower=audit['observed_slower_unprofiled_controls']
    if slower:
        largest=max(slower,key=lambda c:c['paired_candidate_over_baseline_median'])
        lines+=['',f"Observed slower controls are retained in the table and audit. The largest is {largest['control']}/{largest['query']} at {largest['rows']:,} rows: paired ratio {largest['paired_candidate_over_baseline_median']:.4f} ({(largest['paired_candidate_over_baseline_median']-1)*100:.2f}% slower in this run). The candidate does not improve every query; these desktop measurements do not establish whether small timing shifts persist across machines."]
    lines+=['','## Stage diagnosis, excluded from competitive results','','| Fixture | Query | Read before / after ms | Selection before / after ms | Aggregate before / after ms |','|---|---|---:|---:|---:|']
    for name in ['final-profiles','irregular-profiles']:
        for c in controls[name]['cases']:
            before=c['stage_median_ms']['baseline'];after=c['stage_median_ms']['candidate']
            lines.append('| '+controls[name]['fixture']['label']+' | '+c['name']+' | '+' | '.join(f"{before[k]:.3f} / {after[k]:.3f}" for k in ['page_read_ms','selection_ms','aggregate_ms'])+' |')
    for title,cases in [('Matched matrix',primary),('Prior stress matrix',extra),('Key-pattern matrix',patterns),('Irregular signed-key matrix',irregular)]:
        lines+=['','## '+title,'','| Fixture | Query | 0.3.13 ms | 0.3.14 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |','|---|---|---:|---:|---:|---:|---|']
        for c in cases:
            m=c['run_median_ms'];mark='\u2705' if c['candidate_vs_duckdb']=='win' else '\u274c'
            lines.append(f"| {c['fixture']} | {c['query']} | {m['baseline']:.3f} | {m['candidate']:.3f} | {m['duckdb']:.3f} | {c['paired_baseline_over_candidate_median']:.3f}x | {mark}; {c['candidate_faster_than_duckdb_rounds']}/3 rounds |")
    lines+=['','## Correctness, durable retry and limits','',
        'All 74 Rust tests pass in debug/release, formatting and both Clippy configurations. The new independent BTreeMap oracle verifies filtered wide counts, exact i128 SUM/AVG and repeated SUM across small, constructed-collision, large and plain-hash cache modes. It includes 25,015 rows per mode, signed extremes, empty selections and cache/fallback transitions. The final binaries match 4,000 SQL cases against each DuckDB and SQLite: 500 general, 500 grouping and 600 each for key patterns, medium groups, dense shared sums, focused sparse shared sums and scans. Actual dense and sparse bridge plans emit exact signed beyond-i64 sums after confirmed retry and reopen, including AVG and repeated SUM.','',
        'The current binaries pass 56 publication cuts, 22 catalog corruption rejections, 32 forced process kills, 14 source faults, eight source kills and the 30,000-row/300-interval Parquet pipeline with 42 SQL checks. Source hashes verify unchanged readers, writers, formats, dense kernels, source contract and parsing. Injected failures and process kills do not qualify physical power loss.','',
        'The initial full build passed its 74 debug/release tests but Clippy rejected a parity expression in the new test. Its logs and original source are preserved. The equivalent is_multiple_of expression changes test code only; all full checks were rerun. Restricted PowerShell and a subsequent parameter-set error initially blocked preservation of the log directory without replacing it. Native absolute-path checks and Move-Item then preserved the directory; the workflow note is linked below.','',
        'The selected kernel adds code specialization and preserves an intermediate vector reservation. Existing cache seeds and collisions still vary lookup cost; every guard and unsuccessful trial remains visible. Timing shifts on unchanged dense/scan/prefix paths cannot be attributed to this sparse change. Only DuckDB is freshly competed; the last multi-server network comparison remains [0.3.1](PERFORMANCE_031.md), including mixed-write losses and stalls. Network requests/s, cold I/O, distributed scale and production readiness remain unqualified.','',
        '## Reproduce and inspect','',
        'Run checks_044.py, build_source_adapter_044.py, time_044.py, run_044.py, report_044.py, docs_044.py and package_044.py serially with pinned local dependencies. Completed outputs and release archives are immutable. Controls reuse retained fixtures; matrices can seed independently. Never overlap compilation, tests or packaging with timed database work. Release 0.3.14 uses experiment identifier 044.','',
        '- [Complete gates and scores](benchmarks/sparse-044-audit.json)',
        '- [Small sparse final pairs](benchmarks/sparse-044-final-pairs.json)',
        '- [Wide sparse final pairs](benchmarks/sparse-044-wide-pairs.json)',
        '- [Irregular signed-key pairs](benchmarks/sparse-044-irregular-pairs.json)',
        '- [High-cardinality guard](benchmarks/sparse-044-highcard-guard-pairs.json)',
        '- [Dense guard](benchmarks/sparse-044-dense-guard-pairs.json)',
        '- [Scan guard](benchmarks/sparse-044-scan-guard-pairs.json)',
        '- [Tiny-query guard](benchmarks/sparse-044-tiny-guard-pairs.json)',
        '- [10M-row guard](benchmarks/sparse-044-10m-guard-pairs.json)',
        '- [100M-row guard](benchmarks/sparse-044-100m-guard-pairs.json)',
        '- [Final small-cache profiles](benchmarks/sparse-044-final-profiles.json)',
        '- [Final irregular-key profiles](benchmarks/sparse-044-irregular-profiles.json)',
        '- [Released baseline profiles](benchmarks/irregular-044-baseline-profiles.json)',
        '- [Focused sparse SQL/wide JSON qualification](benchmarks/sparse-044-differential.json)',
        '- [First write-on-miss trial](benchmarks/trial-044-write-on-miss/proof.json)',
        '- [Rejected enum-based fusion](benchmarks/sparse-044-rejected-enum-fusion.json)',
        '- [Unselected broad typed fusion](benchmarks/sparse-044-rejected-wide-typed-fusion.json)',
        '- [Selected adaptive trial](benchmarks/trial-044-small-cache-shared-sum/proof.json)',
        '- [Trial selection and every ratio](benchmarks/sparse-044-selection.json)',
        '- [Preserved Clippy failure and workflow repair](benchmarks/sparse-044-clippy-repair.json)',
        '- [Build provenance](benchmarks/rust-checks-044.json)',
        '- [Final timed work order](benchmarks/sparse-044-run-order.json)',
        '- [Qualification work order](benchmarks/correctness-044-run-order.json)',
        '- [All previous results and unsuccessful evidence](BENCHMARK_HISTORY.md)','']
    (ROOT/'PERFORMANCE_044.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'version':'0.3.14','rust_tests_each_mode':74,'sql_cases_each_reference':4000,
        'primary':score(primary),'extra':score(extra),'patterns':score(patterns),'irregular':score(irregular)}),flush=True)

if __name__=='__main__':main()
