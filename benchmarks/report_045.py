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
    build = read('benchmarks/rust-checks-045.json')
    assert build['version'] == '0.3.15' and build['rust_tests'] == {'debug': 76, 'release': 76, 'passed': True}
    for name, digest in build['source_sha256'].items():
        assert sha(ROOT / name) == digest, name
    base = read('benchmarks/baseline-0.3.14-provenance.json')
    for name, digest in base['core_source_sha256'].items():
        assert sha(ROOT / 'benchmarks/baseline-0.3.14-source' / name) == digest, name
    assert sha(ROOT.parent / 'kestrel-sql-0.3.14.zip') == base['archive_sha256']
    changed = {name for name, digest in base['core_source_sha256'].items() if sha(ROOT / name) != digest}
    assert changed == {'Cargo.toml', 'Cargo.lock', 'src/archive.rs', 'tests/archive.rs'}, changed
    old = (ROOT / 'benchmarks/baseline-0.3.14-source/src/archive.rs').read_text(encoding='utf-8')
    new = (ROOT / 'src/archive.rs').read_text(encoding='utf-8')
    marker='fn impossible('
    assert old[old.index(marker):old.index('#[cfg(test)]')]==new[new.index(marker):new.index('#[cfg(test)]')]
    marker='struct SegmentMetadata {'
    end='pub struct IngestBatch {'
    assert old[old.index(marker):old.index(end)]==new[new.index(marker):new.index(end)]
    marker='fn read_exact_at('
    end='fn impossible('
    assert old[old.index(marker):old.index(end)]==new[new.index(marker):new.index(end)]
    reports = [read(f'benchmarks/group-045-{scope}-comparison.json') for scope in ['typed', 'nyc', 'large', 'extended', 'patterns', 'irregular']]
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
        report=read(f'benchmarks/reader-045-{name}.json')
        assert report['complete'] and len(report['cases'])==expected_cases
        assert report['binary_sha256']['candidate']==build['group_probe_sha256']
        assert report['methodology']['instrumented']==profiled
        for c in report['cases']:
            assert c['all_results_equal'] and len(c['pairs'])==turns
            for pair in c['pairs']:assert all(len(v['samples_ms'])==repeats for v in pair.values())
            assert all(v['full_scrub_bytes']==report['fixture']['rows']*24 for v in c['pairs'][-1].values())
        controls[name]=report
    target=next(c for c in controls['irregular-pairs']['cases'] if c['name']=='unordered_control')
    assert target['paired_candidate_over_baseline_median']<0.8
    assert all(c['paired_candidate_over_baseline_median']<0.8 for c in controls['tiny-guard-pairs']['cases'])
    for name,r in controls.items():
        if not r['methodology']['instrumented']:
            assert all(c['paired_candidate_over_baseline_median']<1.1 for c in r['cases']),name
    general = read('benchmarks/archive-045-verification.json')
    groups = read('benchmarks/group-045-differential.json')
    scans = read('benchmarks/scan-045-differential.json')
    assert general['binary_sha256'] == build['cli_sha256'] and general['queries_checked_against_each_reference'] == 500
    assert all(q['passed'] for q in general['queries'])
    for proof, count in [(groups, 500), (scans, 600)]:
        assert proof['binary_sha256'] == build['bridge_sha256'] and proof['complete']
        assert proof['queries_checked_against_each_reference'] == count
        assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in proof['cases'])
    assert all(f['reopen_retry_and_scrub_passed'] for f in scans['fixtures'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in groups['modes'])
    cache = read('benchmarks/cache-045-differential.json')
    assert cache['complete'] and cache['queries_checked_against_each_reference'] == 600
    assert cache['binary_sha256'] == build['bridge_sha256']
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in cache['cases'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in cache['modes'])
    medium = read('benchmarks/medium-045-differential.json')
    assert medium['complete'] and medium['binary_sha256'] == build['bridge_sha256']
    assert medium['queries_checked_against_each_reference'] == 600
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in medium['cases'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in medium['modes'])
    assert medium['exact_medium_signed_wide_group_json_and_reopen_retry']
    dense=read('benchmarks/dense-045-differential.json')
    assert dense['complete'] and dense['binary_sha256']==build['bridge_sha256']
    assert dense['queries_checked_against_each_reference']==600
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in dense['cases'])
    assert all(c['reopen_replay_and_scrub_passed'] for c in dense['modes'])
    assert len(dense['wide_dense_checks'])==2 and all(c['exact_i128_json'] and c['confirmed_retry_reopen_and_scrub'] for c in dense['wide_dense_checks'])
    focused=read('benchmarks/sparse-045-differential.json')
    assert focused['complete'] and focused['binary_sha256']==build['bridge_sha256']
    assert focused['queries_checked_against_each_reference']==600
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in focused['cases'])
    assert all(m['reopen_replay_and_scrub_passed'] for m in focused['modes'])
    assert focused['exact_sparse_shared_signed_wide_group_json_and_reopen_retry']
    faults = read('benchmarks/publication-045-faults.json')
    assert faults['binary_sha256'] == build['bridge_sha256'] and faults['fault_driver_sha256'] == build['fault_driver_sha256']
    assert len(faults['cut_points']) == 56 and len(faults['corruption_cases']) == 22
    assert all(c['original_receipts_preserved'] and c['atomic_rows_and_sum'] and c['retry_deduplication_passed'] and c['full_scrub_passed'] for c in faults['cut_points'])
    assert all(c['rejected'] for c in faults['corruption_cases'])
    recovery = read('benchmarks/group-045-recovery.json')
    source = read('benchmarks/source-045-faults.json')
    assert recovery['binary_sha256'] == build['bridge_sha256'] and len(recovery['cycles']) == 32 and not recovery['failed_cases']
    assert source['driver_sha256'] == build['source_fault_driver_sha256']
    assert source['adapter_sha256'] == read('benchmarks/source-045-typed-adapter-build.json')['binary_sha256']
    assert len(source['cases']) == 14 and len(source['kill_cycles']) == 8 and not source['failed_cases']
    pipeline = read('portfolio/source-pipeline-045-results.json')
    assert pipeline['stats']['archive']['rows'] == 30000 and sum(p['committed_batches'] for p in pipeline['positions']) == 300
    assert pipeline['exact_sql_cases_against_duckdb'] == 42 and pipeline['full_scrub_passed']
    assert pipeline['source_positions_and_data_reopen_together'] and pipeline['replay_and_invalid_intervals_passed']
    wire = read('benchmarks/wire-045-audit.json')
    assert wire['cli_sha256'] == build['cli_sha256'] and wire['bridge_sha256'] == build['bridge_sha256']
    assert all(wire[k] for k in ['exact_positive_and_negative_wide_archive_json', 'exact_wide_ram_json', 'sparse_bridge_error_continuity_retry_reopen_and_scrub'])
    timed=read('benchmarks/reader-045-run-order.json')
    qualified=read('benchmarks/correctness-045-run-order.json')
    assert len(timed)==17 and all(r['returncode']==0 for r in timed)
    assert len({r['suite'] for r in qualified if r['returncode']==0})==13
    assert all(a['completed_at_utc']<=b['started_at_utc'] for a,b in zip(timed,timed[1:]))
    assert all(a['completed_at_utc']<=b['started_at_utc'] for a,b in zip(qualified,qualified[1:]))
    adapter=read('benchmarks/source-045-typed-adapter-build.json')
    assert max(r['completed_at_utc'] for r in build['build_run_order'])<=adapter['started_at_utc']<adapter['completed_at_utc']<=timed[0]['started_at_utc']
    assert timed[-1]['completed_at_utc']<=qualified[0]['started_at_utc']
    for r in timed:assert r['harness_sha256']==sha(ROOT/r['command'][1])
    for r in qualified:assert r['harness_sha256']==sha(ROOT/r['command'][1])
    for trial_name,tests in [('owned-offset-read',74),('bounded-owned-handles',76)]:
        trial=read(f'benchmarks/trial-045-{trial_name}/proof.json')
        assert trial['debug_tests_passed']==tests
        for relative,digest in trial['source_sha256'].items():assert sha(ROOT/f'benchmarks/trial-045-{trial_name}/source'/relative)==digest
        assert sha(Path(trial['group_probe']))==trial['group_probe_sha256']
        assert sha(ROOT/trial['build_harness_snapshot'])==trial['build_harness_sha256']
        order=read(f'benchmarks/reader-045-{trial_name}-run-order.json')
        assert len(order)==7 and all(r['returncode']==0 for r in order)
        assert trial['build_run_order'][-1]['completed_at_utc']<=order[0]['started_at_utc']
        assert all(a['completed_at_utc']<=b['started_at_utc'] for a,b in zip(order,order[1:]))
        for r in order:assert r['harness_sha256']==sha(ROOT/r['command'][1])
    selected=(ROOT/'benchmarks/trial-045-bounded-owned-handles/source/src/archive.rs').read_text(encoding='utf-8')
    assert selected==new
    assert (ROOT/'benchmarks/trial-045-bounded-owned-handles/source/tests/archive.rs').read_bytes()==(ROOT/'tests/archive.rs').read_bytes()
    assert read('benchmarks/reader-045-bounded-owned-handles-run-order.json')[-1]['completed_at_utc']<=build['build_run_order'][0]['started_at_utc']
    unselected=read('benchmarks/reader-045-offset-unselected.json')
    assert unselected['status']=='not selected standalone development trial'
    reader=read('benchmarks/reader-045-verification.json')
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
    audit = {'version':'0.3.15', 'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_sha256':build['source_sha256'], 'rust_tests_each_mode':76,
        'baseline':'0.3.14', 'baseline_provenance':base,
        'primary_score':score(primary), 'extended_score':score(extra), 'pattern_score':score(patterns), 'irregular_score':score(irregular),
        'current_comparison_cases':108, 'current_query_shapes':60, 'current_timed_query_samples':samples,
        'previous_release_scores':{k:read('benchmarks/sparse-044-audit.json')[k] for k in ['primary_score','extended_score','pattern_score','irregular_score']},
        'current_comparisons':primary, 'extended_comparisons':extra, 'pattern_comparisons':patterns, 'irregular_comparisons':irregular,
        'paired_controls':{name:[{k:v for k,v in c.items() if k!='pairs'} for c in r['cases']] for name,r in controls.items()},
        'observed_slower_unprofiled_controls':[
            {'control':name,'rows':r['fixture']['rows'],'query':c['name'],
             'paired_candidate_over_baseline_median':c['paired_candidate_over_baseline_median']}
            for name,r in controls.items() if not r['methodology']['instrumented']
            for c in r['cases'] if c['paired_candidate_over_baseline_median']>1.0],
        'unprofiled_control_samples':23030, 'profiled_control_samples_excluded':1078,
        'sql_cases_against_each_reference':4000, 'publication_cut_points':56, 'catalog_corruption_rejections':22,
        'forced_kills':32, 'source_fault_cut_points':14, 'source_forced_kills':8,
        'parquet_rows':30000, 'source_intervals':300, 'parquet_sql_oracles':42,
        'no_compilation_overlap_with_timed_database_work':True,
        'formats_publication_policy_source_contract_and_group_kernels_unchanged':True,
        'service_qualification':'No new network requests/s qualification; previous mixed-write losses and stalls remain visible',
        'qualification_harness_failures':[r for r in qualified if r['returncode'] != 0],
        'qualification_harness_repairs':[], 'reader_manual_sql_oracles':104, 'idle_stream_handle_budget_per_store':128, 'idle_stream_handle_budget_per_segment':1,
        'preserved_development_trials':['owned-offset-read: not selected standalone; target scan improvement about 0.4%','bounded-owned-handles: selected, independently rebuilt and remeasured'],
        'stream_handle_policy':'At most one idle independently opened synchronous file per immutable segment and 128 idle files per store. Borrow removes a file from the cache; queries retain exclusive ownership. Segment lifetime governs retirement. Full verification opens fresh files and clears idle files on failure. Every streamed payload block is read and CRC-checked; indexed-page caching retains its preceding behavior.',
        'limits':['Warm single-thread queries on one shared Windows computer',
          'Rust direct query timer versus DuckDB Python execute/fetchall; native storage layouts differ',
          'Idle handle reuse adds per-segment cache state and at most 128 idle kernel file resources per store; active readers remain additional independent handles',
          'Only DuckDB freshly compared; last multi-server matrix remains 0.3.1',
          'No new network, cold-I/O, power-loss, distributed-scale or production qualification']}
    (ROOT / 'benchmarks/reader-045-audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')


    write_report(audit, reports, controls, primary, extra, patterns, irregular)
    print(json.dumps({'version':'0.3.15','rust_tests_each_mode':76,'sql_cases_each_reference':4000,
        'reader_manual_sql_oracles':104,'primary':score(primary),'extra':score(extra),'patterns':score(patterns),'irregular':score(irregular)}),flush=True)


def write_report(audit, reports, controls, primary, extra, patterns, irregular):
    scores=[score(cases) for cases in [primary,extra,patterns,irregular]]
    wins=sum(s['wins'] for s in scores);losses=sum(s['losses'] for s in scores)
    loss_word='loss' if losses==1 else 'losses'
    lines=['# 0.3.15: bounded reuse of independent scan handles','',
        'Fragmented live archives repeatedly opened and closed one synchronous file per segment and query. The selected cache retains at most one idle independently opened File per immutable segment and 128 idle files per store. Borrowing removes the file from the cache, so concurrent readers keep exclusive ownership; a cold or concurrent miss opens another independent file. File::try_clone is not used. Cached files live inside their Segment, without another segment reference, so retirement follows the existing snapshot lifetime.','',
        'Every streamed payload block is still read and CRC-checked; existing indexed-page caching is unchanged. Streaming retains the preceding seek/read path. I/O and checksum errors discard the current stream; full verification opens fresh files, bypasses both page and handle reuse, and clears idle files in its snapshot on failure. The idle limit does not limit active query handles. Reuse adds per-segment bookkeeping and up to 128 idle kernel resources; its counts include pinned retired segments from the same store. New process-local stats expose retained_stream_handles, stream_handle_opens and stream_handle_reuses. Reopen starts with no cached handles. Writers, receipt/source contracts, persisted fields, parsing and group kernels remain unchanged.','',
        'An earlier owned-offset read trial removed a separate seek call. Rust 1.97.1 has separate seek and read implementations; this motivated the experiment, not a guaranteed speedup. Its target fragmented unordered scan improved only about 0.4% in the paired trial, despite other mixed gains and regressions. It was not selected on its own. The full source, binary, build-harness snapshot and seven timed workloads are preserved. The handle-cache trial instead reduced that target about 40%, and improved tiny queries, with some slower guards retained. The candidate below is independently rebuilt and remeasured. [Pinned Rust Windows filesystem source](https://raw.githubusercontent.com/rust-lang/rust/1.97.1/library/std/src/sys/fs/windows.rs), [Windows handle implementation](https://raw.githubusercontent.com/rust-lang/rust/1.97.1/library/std/src/sys/pal/windows/handle.rs), [FileExt cursor semantics](https://doc.rust-lang.org/std/os/windows/fs/trait.FileExt.html).','',
        f'Fresh DuckDB matrix: **{wins} wins / {losses} {loss_word}** over 60 shapes; released 0.3.14 measured 58 wins and two losses. The matrix retains 108 engine/fixture/round cases and 5,940 samples. Separate uninstrumented controls retain 23,030 samples; 1,078 instrumented samples are excluded from competitive totals. Three rotated orders, three warmups, eleven samples and one thread are used in the matrix. Rust timers measure ArchiveSnapshot::query; DuckDB includes Python execute/fetchall, and native storage layouts differ. Builds, setup, checks and scrubs are untimed; timed workloads run serially on this shared Windows computer.','',
        '## Final alternating controls','',
        'Times are medians of pair medians; the paired ratio is the median candidate/baseline ratio inside each pair. Desktop variance can make these summaries differ. Smaller ratios are faster. Controls use 21 pairs of eleven samples per binary, except tiny queries (21 pairs of 101) and 100M rows (seven pairs of five). Matrix and one-query-per-process controls have different process histories; compare their own paired measurements rather than combining absolute times. Every repeated result matches and final archives are fully scrubbed.','',
        '| Control | Rows | Query | 0.3.14 ms | 0.3.15 ms | Paired candidate / baseline |','|---|---:|---|---:|---:|---:|']
    for name,r in controls.items():
        if r['methodology']['instrumented']:continue
        for c in r['cases']:lines.append(f"| {name} | {r['fixture']['rows']:,} | {c['name']} | {c['baseline_median_ms']:.4f} | {c['candidate_median_ms']:.4f} | {c['paired_candidate_over_baseline_median']:.4f} |")
    slower=audit['observed_slower_unprofiled_controls']
    if slower:
        largest=max(slower,key=lambda c:c['paired_candidate_over_baseline_median'])
        lines+=['',f"Observed slower controls remain visible. The largest is {largest['control']}/{largest['query']} at {largest['rows']:,} rows: paired ratio {largest['paired_candidate_over_baseline_median']:.4f}, or {(largest['paired_candidate_over_baseline_median']-1)*100:.2f}% slower in this run. A faster target does not imply that every query improved."]
    lines+=['','## Stage diagnosis, excluded from competitive results','','| Fixture | Query | Read before / after ms | Selection before / after ms | Aggregate before / after ms |','|---|---|---:|---:|---:|']
    for name in ['final-profiles','irregular-profiles']:
        for c in controls[name]['cases']:
            before=c['stage_median_ms']['baseline'];after=c['stage_median_ms']['candidate']
            lines.append('| '+controls[name]['fixture']['label']+' | '+c['name']+' | '+' | '.join(f"{before[k]:.3f} / {after[k]:.3f}" for k in ['page_read_ms','selection_ms','aggregate_ms'])+' |')
    for title,cases in [('Matched matrix',primary),('Prior stress matrix',extra),('Key-pattern matrix',patterns),('Irregular signed-key matrix',irregular)]:
        lines+=['','## '+title,'','| Fixture | Query | 0.3.14 ms | 0.3.15 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |','|---|---|---:|---:|---:|---:|---|']
        for c in cases:
            m=c['run_median_ms'];mark=chr(0x2705) if c['candidate_vs_duckdb']=='win' else chr(0x274c)
            lines.append(f"| {c['fixture']} | {c['query']} | {m['baseline']:.3f} | {m['candidate']:.3f} | {m['duckdb']:.3f} | {c['paired_baseline_over_candidate_median']:.3f}x | {mark}; {c['candidate_faster_than_duckdb_rounds']}/3 rounds |")
    lines+=['','## Correctness, durable retry and resource lifetime','',
        'All 76 Rust tests pass in debug/release, formatting and both Clippy configurations. The existing eight-reader positional oracle now verifies actual handle reuse. A new 130-segment test verifies the 128-idle-file ceiling, fresh full scrubs, pinned snapshot correctness through compaction, release of 32 retired segment caches, and queries after the Archive owner is dropped. A second new test warms the cache, detects payload corruption and truncation, restores the fixture, verifies it and checks cold reopen.','',
        'The final CLI/bridge match 4,000 SQL cases against each DuckDB and SQLite: 500 general, 500 grouping and 600 each for key patterns, medium, dense, sparse and scan cases. Signed wide shared SUM/AVG JSON remains exact after confirmed retry/reopen. An additional untimed bridge suite checks 104 manual Python integer oracles, including 96 requests across eight clients, exact beyond-i64 sums, handle metrics, fresh scrub behavior, warmed corruption rejection, cache invalidation and known receipts after reopen. These concurrent correctness requests are not a new requests/s benchmark.','',
        'The same current binaries pass 56 publication cuts, 22 catalog corruption rejections, 32 forced process kills, 14 source faults, eight source kills and the 30,000-row/300-interval Parquet pipeline with 42 SQL checks. Snapshot retirement and cached descriptors remain process-local; they do not change durable publication. Process kills and injected failures do not qualify physical power loss.','',
        'The cache consumes extra idle handles and memory bookkeeping. Concurrent misses still open independent files, and active handle admission is unchanged. Beyond 128 retained files, other reads use the ordinary path. Only DuckDB is freshly competed; the last multi-server network matrix remains [0.3.1](PERFORMANCE_031.md), including mixed-write losses and stalls. Cold I/O, server requests/s, distributed scale, universal superiority and production readiness are unqualified.','',
        '## Reproduce and inspect','',
        'Run checks_045.py, build_source_adapter_045.py, time_045.py, run_045.py, report_045.py, docs_045.py and package_045.py serially with pinned local dependencies. Trials have their own immutable sources, binaries, build-harness snapshots and work orders. Restore trial core sources in an isolated checkout before rebuilding them. Never overwrite completed reports or archives, and never overlap compilation, qualification or packaging with timed database work. Release 0.3.15 uses experiment identifier 045.','']
    for title,path in [
        ('Complete gates and all scores','benchmarks/reader-045-audit.json'),
        ('Fragmented final pairs','benchmarks/reader-045-irregular-pairs.json'),
        ('Fragmented profiles','benchmarks/reader-045-irregular-profiles.json'),
        ('Small sparse final pairs','benchmarks/reader-045-final-pairs.json'),
        ('Wide sparse final pairs','benchmarks/reader-045-wide-pairs.json'),
        ('Tiny queries','benchmarks/reader-045-tiny-guard-pairs.json'),
        ('Single-segment scan guards','benchmarks/reader-045-scan-guard-pairs.json'),
        ('High-cardinality guards','benchmarks/reader-045-highcard-guard-pairs.json'),
        ('Dense guards','benchmarks/reader-045-dense-guard-pairs.json'),
        ('10M-row guards','benchmarks/reader-045-10m-guard-pairs.json'),
        ('100M-row guards','benchmarks/reader-045-100m-guard-pairs.json'),
        ('Actual bridge concurrency/reuse/corruption oracles','benchmarks/reader-045-verification.json'),
        ('Unselected offset-only trial','benchmarks/reader-045-offset-unselected.json'),
        ('Offset-only source and binary proof','benchmarks/trial-045-owned-offset-read/proof.json'),
        ('Selected cache trial','benchmarks/trial-045-bounded-owned-handles/proof.json'),
        ('Selection and every trial ratio','benchmarks/reader-045-selection.json'),
        ('Build provenance','benchmarks/rust-checks-045.json'),
        ('Final timed work order','benchmarks/reader-045-run-order.json'),
        ('Qualification work order','benchmarks/correctness-045-run-order.json'),
        ('All historical results and unsuccessful evidence','BENCHMARK_HISTORY.md')]:
        lines.append(f'- [{title}]({path})')
    lines.append('')
    (ROOT/'PERFORMANCE_045.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':main()
