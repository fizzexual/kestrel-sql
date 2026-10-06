"""Gate bounded stream-handle reuse while preserving every matrix loss and unselected trial."""
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
    build = read('benchmarks/rust-checks-046.json')
    assert build['version'] == '0.3.16' and build['rust_tests'] == {'debug': 77, 'release': 77, 'passed': True}
    for name, digest in build['source_sha256'].items():
        assert sha(ROOT / name) == digest, name
    base = read('benchmarks/baseline-0.3.15-provenance.json')
    for name, digest in base['core_source_sha256'].items():
        assert sha(ROOT / 'benchmarks/baseline-0.3.15-source' / name) == digest, name
    assert sha(ROOT.parent / 'kestrel-sql-0.3.15.zip') == base['archive_sha256']
    changed = {name for name, digest in base['core_source_sha256'].items() if sha(ROOT / name) != digest}
    assert changed == {'Cargo.toml', 'Cargo.lock', 'src/archive.rs'}, changed
    old = (ROOT / 'benchmarks/baseline-0.3.15-source/src/archive.rs').read_text(encoding='utf-8')
    new = (ROOT / 'src/archive.rs').read_text(encoding='utf-8')
    marker='/// Inclusive histogram buckets'
    end='impl SparseGroups {'
    assert old[old.index(marker):old.index(end)]==new[new.index(marker):new.index(end)]
    assert old[:old.index('type LargeGroupKeyCache =')]==new[:new.index('#[derive(Debug, Clone, Copy, Default)]')]
    reports = [read(f'benchmarks/group-046-{scope}-comparison.json') for scope in ['typed', 'nyc', 'large', 'extended', 'patterns', 'irregular']]
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
        ('final-profiles',3,7,11,True),('irregular-profiles',4,7,11,True),
    ]:
        report=read(f'benchmarks/packed-046-{name}.json')
        assert report['complete'] and len(report['cases'])==expected_cases
        assert report['binary_sha256']['candidate']==build['group_probe_sha256']
        assert report['methodology']['instrumented']==profiled
        for c in report['cases']:
            assert c['all_results_equal'] and len(c['pairs'])==turns
            for pair in c['pairs']:assert all(len(v['samples_ms'])==repeats for v in pair.values())
            assert all(v['full_scrub_bytes']==report['fixture']['rows']*24 for v in c['pairs'][-1].values())
        controls[name]=report
    policy=read('benchmarks/packed-046-trial-policy.json')
    target=next(c for c in controls['irregular-pairs']['cases'] if c['name']=='group_sum')
    assert target['paired_candidate_over_baseline_median']<policy['maximum_primary_paired_candidate_over_baseline']
    for name,r in controls.items():
        if not r['methodology']['instrumented']:
            assert all(c['paired_candidate_over_baseline_median']<policy['maximum_unprofiled_guard_paired_candidate_over_baseline'] for c in r['cases']),name
    general = read('benchmarks/archive-046-verification.json')
    groups = read('benchmarks/group-046-differential.json')
    scans = read('benchmarks/scan-046-differential.json')
    assert general['binary_sha256'] == build['cli_sha256'] and general['queries_checked_against_each_reference'] == 500
    assert all(q['passed'] for q in general['queries'])
    for proof, count in [(groups, 500), (scans, 600)]:
        assert proof['binary_sha256'] == build['bridge_sha256'] and proof['complete']
        assert proof['queries_checked_against_each_reference'] == count
        assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in proof['cases'])
    assert all(f['reopen_retry_and_scrub_passed'] for f in scans['fixtures'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in groups['modes'])
    cache = read('benchmarks/cache-046-differential.json')
    assert cache['complete'] and cache['queries_checked_against_each_reference'] == 600
    assert cache['binary_sha256'] == build['bridge_sha256']
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in cache['cases'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in cache['modes'])
    medium = read('benchmarks/medium-046-differential.json')
    assert medium['complete'] and medium['binary_sha256'] == build['bridge_sha256']
    assert medium['queries_checked_against_each_reference'] == 600
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in medium['cases'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in medium['modes'])
    assert medium['exact_medium_signed_wide_group_json_and_reopen_retry']
    dense=read('benchmarks/dense-046-differential.json')
    assert dense['complete'] and dense['binary_sha256']==build['bridge_sha256']
    assert dense['queries_checked_against_each_reference']==600
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in dense['cases'])
    assert all(c['reopen_replay_and_scrub_passed'] for c in dense['modes'])
    assert len(dense['wide_dense_checks'])==2 and all(c['exact_i128_json'] and c['confirmed_retry_reopen_and_scrub'] for c in dense['wide_dense_checks'])
    focused=read('benchmarks/sparse-046-differential.json')
    assert focused['complete'] and focused['binary_sha256']==build['bridge_sha256']
    assert focused['queries_checked_against_each_reference']==600
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in focused['cases'])
    assert all(m['reopen_replay_and_scrub_passed'] for m in focused['modes'])
    assert focused['exact_sparse_shared_signed_wide_group_json_and_reopen_retry']
    faults = read('benchmarks/publication-046-faults.json')
    assert faults['binary_sha256'] == build['bridge_sha256'] and faults['fault_driver_sha256'] == build['fault_driver_sha256']
    assert len(faults['cut_points']) == 56 and len(faults['corruption_cases']) == 22
    assert all(c['original_receipts_preserved'] and c['atomic_rows_and_sum'] and c['retry_deduplication_passed'] and c['full_scrub_passed'] for c in faults['cut_points'])
    assert all(c['rejected'] for c in faults['corruption_cases'])
    recovery = read('benchmarks/group-046-recovery.json')
    source = read('benchmarks/source-046-faults.json')
    assert recovery['binary_sha256'] == build['bridge_sha256'] and len(recovery['cycles']) == 32 and not recovery['failed_cases']
    assert source['driver_sha256'] == build['source_fault_driver_sha256']
    assert source['adapter_sha256'] == read('benchmarks/source-046-typed-adapter-build.json')['binary_sha256']
    assert len(source['cases']) == 14 and len(source['kill_cycles']) == 8 and not source['failed_cases']
    pipeline = read('portfolio/source-pipeline-046-results.json')
    assert pipeline['stats']['archive']['rows'] == 30000 and sum(p['committed_batches'] for p in pipeline['positions']) == 300
    assert pipeline['exact_sql_cases_against_duckdb'] == 42 and pipeline['full_scrub_passed']
    assert pipeline['source_positions_and_data_reopen_together'] and pipeline['replay_and_invalid_intervals_passed']
    wire = read('benchmarks/wire-046-audit.json')
    assert wire['cli_sha256'] == build['cli_sha256'] and wire['bridge_sha256'] == build['bridge_sha256']
    assert all(wire[k] for k in ['exact_positive_and_negative_wide_archive_json', 'exact_wide_ram_json', 'sparse_bridge_error_continuity_retry_reopen_and_scrub'])
    timed=read('benchmarks/packed-046-run-order.json')
    qualified=read('benchmarks/correctness-046-run-order.json')
    assert len(timed)==17 and all(r['returncode']==0 for r in timed)
    assert len({r['suite'] for r in qualified if r['returncode']==0})==13
    assert all(a['completed_at_utc']<=b['started_at_utc'] for a,b in zip(timed,timed[1:]))
    assert all(a['completed_at_utc']<=b['started_at_utc'] for a,b in zip(qualified,qualified[1:]))
    adapter=read('benchmarks/source-046-typed-adapter-build.json')
    assert max(r['completed_at_utc'] for r in build['build_run_order'])<=adapter['started_at_utc']<adapter['completed_at_utc']<=timed[0]['started_at_utc']
    assert timed[-1]['completed_at_utc']<=qualified[0]['started_at_utc']
    closest=read('benchmarks/packed-046-closest-duck-pairs.json')
    assert closest['complete'] and closest['candidate_sha256']==build['group_probe_sha256']
    assert len(closest['pairs'])==21 and closest['timed_samples']==462
    assert closest['harness_sha256']==sha(ROOT/'benchmarks/closest_duck_046.py')
    assert timed[-1]['completed_at_utc']<=closest['started_at_utc']<=closest['completed_at_utc']<=qualified[0]['started_at_utc']
    assert closest['full_scrub_bytes']==24000000
    assert all(v['all_repeated_results_equal'] and len(v['samples_ms'])==11 for pair in closest['pairs'] for v in pair.values())
    for r in timed:assert r['harness_sha256']==sha(ROOT/r['command'][1])
    for r in qualified:assert r['harness_sha256']==sha(ROOT/r['command'][1])
    trial_name='packed-medium-tags-corrected'
    trial=read(f'benchmarks/trial-046-{trial_name}/proof.json')
    assert trial['debug_tests_passed']==77
    for relative,digest in trial['source_sha256'].items():assert sha(ROOT/f'benchmarks/trial-046-{trial_name}/source'/relative)==digest
    assert sha(Path(trial['group_probe']))==trial['group_probe_sha256']
    assert sha(ROOT/trial['build_harness_snapshot'])==trial['build_harness_sha256']
    order=read(f'benchmarks/packed-046-{trial_name}-run-order.json')
    assert len(order)==7 and all(r['returncode']==0 for r in order)
    assert trial['build_run_order'][-1]['completed_at_utc']<=order[0]['started_at_utc']
    assert all(a['completed_at_utc']<=b['started_at_utc'] for a,b in zip(order,order[1:]))
    for r in order:assert r['harness_sha256']==sha(ROOT/r['command'][1])
    assert (ROOT/f'benchmarks/trial-046-{trial_name}/source/src/archive.rs').read_text(encoding='utf-8')==new
    assert order[-1]['completed_at_utc']<=build['build_run_order'][0]['started_at_utc']
    selection=read('benchmarks/packed-046-selection.json')
    assert selection['all_predeclared_ratio_gates_passed'] and selection['large_cache_bytes']==262144
    failures=read('benchmarks/packed-046-build-repairs.json')['failed_attempts']
    assert len(failures)==2
    for path in failures:
        failure=read(path);folder=(ROOT/path).parent
        for relative,digest in failure['source_sha256'].items():assert sha(folder/'source'/relative)==digest
        assert sha(ROOT/failure['build_harness_snapshot'])==failure['build_harness_sha256']
        assert any(r['returncode']!=0 for r in read((folder/'run-order.json').relative_to(ROOT)))
    reader=read('benchmarks/reader-046-verification.json')
    assert reader['complete'] and reader['binary_sha256']==build['bridge_sha256']
    assert reader['manual_sql_oracles']==104 and reader['rows']==20012 and reader['segments']==4
    assert all(c['exact_python_integer_oracle'] for c in reader['cases'])
    assert all(reader[k] for k in ['fresh_full_scrub_bypasses_handle_reuse','eight_clients_exact_wide_outputs_and_bounded_idle_handles','warm_corruption_rejected_and_idle_handles_invalidated','volatile_reuse_resets_on_reopen_and_known_receipts_survive'])
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
    assert sum(sample_count(r) for r in controls.values() if r['methodology']['instrumented'])==1078
    audit = {'version':'0.3.16', 'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_sha256':build['source_sha256'], 'rust_tests_each_mode':77,
        'baseline':'0.3.15', 'baseline_provenance':base,
        'primary_score':score(primary), 'extended_score':score(extra), 'pattern_score':score(patterns), 'irregular_score':score(irregular),
        'current_comparison_cases':108, 'current_query_shapes':60, 'current_timed_query_samples':samples,
        'previous_release_scores':{k:read('benchmarks/reader-045-audit.json')[k] for k in ['primary_score','extended_score','pattern_score','irregular_score']},
        'closest_competitive_result':min(primary+extra+patterns+irregular,key=lambda c:abs(c['run_median_ms']['candidate']/c['run_median_ms']['duckdb']-1)),
        'current_comparisons':primary, 'extended_comparisons':extra, 'pattern_comparisons':patterns, 'irregular_comparisons':irregular,
        'paired_controls':{name:[{k:v for k,v in c.items() if k!='pairs'} for c in r['cases']] for name,r in controls.items()},
        'observed_slower_unprofiled_controls':[
            {'control':name,'rows':r['fixture']['rows'],'query':c['name'],
             'paired_candidate_over_baseline_median':c['paired_candidate_over_baseline_median']}
            for name,r in controls.items() if not r['methodology']['instrumented']
            for c in r['cases'] if c['paired_candidate_over_baseline_median']>1.0],
        'unprofiled_control_samples':23030, 'profiled_control_samples_excluded':1078, 'additional_closest_case_samples':462, 'closest_case_repeat':{k:v for k,v in closest.items() if k!='pairs'},
        'sql_cases_against_each_reference':4000, 'publication_cut_points':56, 'catalog_corruption_rejections':22,
        'forced_kills':32, 'source_fault_cut_points':14, 'source_forced_kills':8,
        'parquet_rows':30000, 'source_intervals':300, 'parquet_sql_oracles':42,
        'no_compilation_overlap_with_timed_database_work':True,
        'formats_publication_policy_source_contract_reader_and_dense_helpers_unchanged':True,
        'service_qualification':'No new network requests/s qualification; previous mixed-write losses and stalls remain visible',
        'qualification_harness_failures':[r for r in qualified if r['returncode'] != 0],
        'qualification_harness_repairs':failures, 'reader_manual_sql_oracles':104, 'idle_stream_handle_budget_per_store':128, 'idle_stream_handle_budget_per_segment':1,
        'preserved_development_trials':['packed-medium-tags-corrected: selected under predeclared gates; independently rebuilt and remeasured'], 'packed_medium_cache_bytes':262144, 'preceding_medium_cache_bytes':393216, 'packed_entry_bytes':16,
        'stream_handle_policy':'At most one idle independently opened synchronous file per immutable segment and 128 idle files per store. Borrow removes a file from the cache; queries retain exclusive ownership. Segment lifetime governs retirement. Full verification opens fresh files and clears idle files on failure. Every streamed payload block is read and CRC-checked; indexed-page caching retains its preceding behavior.',
        'limits':['Warm single-thread queries on one shared Windows computer',
          'Rust direct query timer versus DuckDB Python execute/fetchall; native storage layouts differ',
          'Idle handle reuse adds per-segment cache state and at most 128 idle kernel file resources per store; active readers remain additional independent handles',
          'Only DuckDB freshly compared; last multi-server matrix remains 0.3.1',
          'No new network, cold-I/O, power-loss, distributed-scale or production qualification']}
    (ROOT / 'benchmarks/packed-046-audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')


    write_report(audit, reports, controls, primary, extra, patterns, irregular)
    print(json.dumps({'version':'0.3.16','rust_tests_each_mode':77,'sql_cases_each_reference':4000,
        'reader_manual_sql_oracles':104,'primary':score(primary),'extra':score(extra),'patterns':score(patterns),'irregular':score(irregular)}),flush=True)


def write_report(audit, reports, controls, primary, extra, patterns, irregular):
    scores=[score(cases) for cases in [primary,extra,patterns,irregular]]
    wins=sum(s['wins'] for s in scores);losses=sum(s['losses'] for s in scores)
    loss_word='loss' if losses==1 else 'losses'
    closest=audit['closest_competitive_result'];cm=closest['run_median_ms']
    close_description=f"Closest competitive result: {closest['fixture']}/{closest['query']}, candidate {cm['candidate']:.4f} ms versus DuckDB {cm['duckdb']:.4f} ms; {closest['candidate_faster_than_duckdb_rounds']}/3 rounds. The relative median gap is {abs(cm['candidate']/cm['duckdb']-1)*100:.2f}%. A small median edge on this desktop is a near tie, not evidence of a universal ranking."
    repeated=audit['closest_case_repeat']
    repeat_mark=chr(0x2705) if repeated['candidate_vs_duckdb']=='win' else chr(0x274c)
    repeat_description=f"Separate 21-pair closest-case repeat: {repeat_mark} {repeated['candidate_vs_duckdb']}; Kestrel {repeated['candidate_median_ms']:.4f} ms vs DuckDB {repeated['duckdb_median_ms']:.4f} ms, paired candidate/DuckDB ratio {repeated['paired_candidate_over_duckdb_median']:.4f}, Kestrel faster in {repeated['candidate_faster_pairs']}/21 pairs. Its 462 samples use one persistent process per engine and a single-query history; they remain separate from the 60-shape score. This repeat is retained regardless of outcome."
    lines=['# 0.3.16: smaller exact tags for medium sparse groups','',
        'The promoted sparse key cache now stores an exact signed key and a checked u32 group index plus one. Zero in the index field marks an empty entry, so key zero and both i64 boundaries remain ordinary valid keys. The authoritative randomized HashMap, 16,384 cache slots, 8,192-key ceiling, hit-rate fallback, deferred promotion, counts and exact i128 reductions retain their preceding behavior.','',
        'On this 64-bit Windows build, each entry is 16 bytes rather than the preceding 24-byte Option tuple. The promoted payload table is **256 KiB instead of 384 KiB**, a one-third reduction. Group-index encoding uses a checked conversion and a compile-time result-budget bound. This is query-local memory, not a reduction in persisted archive size or total process memory. The 0.3.15 reader cache and its active/idle handle policy remain unchanged.','',
        'The development trial measured about 11.4% faster irregular SUM and 10.6% faster full grouping in alternating pairs. Before those timings, the policy required irregular SUM ratio below 0.95 and every unprofiled guard below 1.05; the trial passed both. Two earlier build attempts are preserved: a missing Debug derive prevented compilation, then an existing footprint test retained the old 384 KiB expectation. The repaired expectation verifies the new budget, with SQL oracles retained. The candidate below is independently rebuilt and remeasured.','',
        f'Fresh DuckDB matrix: **{wins} wins / {losses} {loss_word}** over 60 shapes; released 0.3.15 measured 59 wins and one loss. All 108 engine/fixture/round cases and 5,940 samples remain visible. Separate uninstrumented controls retain 23,030 samples; 1,078 instrumented samples are excluded from competitive totals. The development trial adds 20,118 uninstrumented and 616 excluded instrumented samples.','',
        close_description,'',repeat_description,'',
        'These are warm local queries on one shared Windows computer. The matrix rotates three engine orders with three warmups, eleven samples and one thread. Rust timers measure ArchiveSnapshot::query; DuckDB includes Python execute/fetchall. Native storage layouts and interfaces differ. Builds, setup, qualification and full scrubs are untimed, and timed workloads run serially. No new network requests/s or general database-service qualification is claimed.','',
        '## Final alternating controls','',
        'Times are medians of pair medians. The paired ratio is the median candidate/baseline ratio within each pair; desktop variance can make those summaries differ. Smaller ratios are faster. There are 21 pairs of eleven samples per binary, except tiny queries (21 pairs of 101) and 100M rows (seven pairs of five). Every repeated result matches and final archives are fully scrubbed.','',
        '| Control | Rows | Query | 0.3.15 ms | 0.3.16 ms | Paired candidate / baseline |','|---|---:|---|---:|---:|---:|']
    for name,r in controls.items():
        if r['methodology']['instrumented']:continue
        for c in r['cases']:lines.append(f"| {name} | {r['fixture']['rows']:,} | {c['name']} | {c['baseline_median_ms']:.4f} | {c['candidate_median_ms']:.4f} | {c['paired_candidate_over_baseline_median']:.4f} |")
    slower=audit['observed_slower_unprofiled_controls']
    if slower:
        largest=max(slower,key=lambda c:c['paired_candidate_over_baseline_median'])
        lines+=['',f"Every slower control is retained. The largest is {largest['control']}/{largest['query']} at {largest['rows']:,} rows: paired ratio {largest['paired_candidate_over_baseline_median']:.4f}, or {(largest['paired_candidate_over_baseline_median']-1)*100:.2f}% slower in this run."]
    lines+=['','## Stage diagnosis, excluded from competitive results','','| Fixture | Query | Read before / after ms | Selection before / after ms | Aggregate before / after ms |','|---|---|---:|---:|---:|']
    for name in ['final-profiles','irregular-profiles']:
        for c in controls[name]['cases']:
            before=c['stage_median_ms']['baseline'];after=c['stage_median_ms']['candidate']
            lines.append('| '+controls[name]['fixture']['label']+' | '+c['name']+' | '+' | '.join(f"{before[k]:.3f} / {after[k]:.3f}" for k in ['page_read_ms','selection_ms','aggregate_ms'])+' |')
    for title,cases in [('Matched matrix',primary),('Prior stress matrix',extra),('Key-pattern matrix',patterns),('Irregular signed-key matrix',irregular)]:
        lines+=['','## '+title,'','| Fixture | Query | 0.3.15 ms | 0.3.16 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |','|---|---|---:|---:|---:|---:|---|']
        for c in cases:
            m=c['run_median_ms'];mark=chr(0x2705) if c['candidate_vs_duckdb']=='win' else chr(0x274c)
            lines.append(f"| {c['fixture']} | {c['query']} | {m['baseline']:.3f} | {m['candidate']:.3f} | {m['duckdb']:.3f} | {c['paired_baseline_over_candidate_median']:.3f}x | {mark}; {c['candidate_faster_than_duckdb_rounds']}/3 rounds |")
    lines+=['','## Correctness and durability','',
        'All 77 Rust tests pass in debug/release, formatting and both Clippy configurations. The new manual BTreeMap oracle starts with group key zero, forces real tagged-cache collisions, exercises both signed key boundaries and beyond-i64 sums with AVG, and verifies the 256 KiB table. Existing promotion/demotion, group-budget and wide-reduction oracles remain.','',
        'The final CLI/bridge match 4,000 SQL cases against each DuckDB and SQLite: 500 general, 500 grouping and 600 each for key patterns, medium, dense, sparse and scan cases. Exact signed wide shared SUM/AVG JSON survives confirmed retry/reopen. Another 104 manual integer bridge oracles include 96 requests across eight clients, handle reuse, fresh scrub behavior, warmed corruption rejection and receipt-preserving cold reopen. Those concurrent correctness requests are untimed.','',
        'Current binaries also pass 56 publication cuts, 22 catalog corruption rejections, 32 forced process kills, 14 source faults, eight source kills and the 30,000-row/300-interval Parquet pipeline with 42 SQL checks. Reader ownership, snapshot retirement, serialized formats and durable writer/source policy retain exact preceding source identity. Process kills and injected failures do not qualify physical power loss.','',
        'Only DuckDB is freshly competed. The last multi-server network matrix remains [0.3.1](PERFORMANCE_031.md), including mixed-write losses and stalls. Cold I/O, server requests/s, distributed scale, universal superiority and production readiness remain unqualified. Smaller cache payloads do not imply that every query is faster.','',
        '## Reproduce and inspect','',
        'Run checks_046.py, build_source_adapter_046.py, time_046.py, run_046.py, report_046.py, docs_046.py and package_046.py serially with pinned local dependencies. Trial sources, binaries, exact build harnesses, failures and work orders are preserved. Restore frozen trial sources in an isolated checkout before rebuilding. Never overwrite completed evidence or overlap compilation/qualification/packaging with timed database workloads. Release 0.3.16 uses experiment identifier 046.','']
    for title,path in [
        ('Complete gates and all scores','benchmarks/packed-046-audit.json'),
        ('Separate closest-case Kestrel/DuckDB pairs','benchmarks/packed-046-closest-duck-pairs.json'),
        ('Final irregular pairs','benchmarks/packed-046-irregular-pairs.json'),
        ('Final profiles','benchmarks/packed-046-irregular-profiles.json'),
        ('Small sparse final pairs','benchmarks/packed-046-final-pairs.json'),
        ('Wide sparse final pairs','benchmarks/packed-046-wide-pairs.json'),
        ('Tiny guards','benchmarks/packed-046-tiny-guard-pairs.json'),
        ('Scan guards','benchmarks/packed-046-scan-guard-pairs.json'),
        ('High-cardinality guards','benchmarks/packed-046-highcard-guard-pairs.json'),
        ('Dense guards','benchmarks/packed-046-dense-guard-pairs.json'),
        ('10M guards','benchmarks/packed-046-10m-guard-pairs.json'),
        ('100M guards','benchmarks/packed-046-100m-guard-pairs.json'),
        ('Predeclared policy','benchmarks/packed-046-trial-policy.json'),
        ('Selection and every trial ratio','benchmarks/packed-046-selection.json'),
        ('Frozen trial source/binary','benchmarks/trial-046-packed-medium-tags-corrected/proof.json'),
        ('Initial compile failure','benchmarks/trial-046-packed-medium-tags/failure.json'),
        ('Old footprint expectation failure','benchmarks/trial-046-packed-medium-tags-ready/failure.json'),
        ('Build repairs','benchmarks/packed-046-build-repairs.json'),
        ('Current SQL oracles','benchmarks/medium-046-differential.json'),
        ('Current bridge concurrency/reuse/corruption','benchmarks/reader-046-verification.json'),
        ('Final build provenance','benchmarks/rust-checks-046.json'),
        ('Timed work order','benchmarks/packed-046-run-order.json'),
        ('Qualification work order','benchmarks/correctness-046-run-order.json'),
        ('All history and unsuccessful evidence','BENCHMARK_HISTORY.md')]:
        lines.append(f'- [{title}]({path})')
    lines.append('')
    (ROOT/'PERFORMANCE_046.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':main()
