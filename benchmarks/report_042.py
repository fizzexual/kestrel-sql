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
    build = read('benchmarks/rust-checks-042.json')
    assert build['version'] == '0.3.12' and build['rust_tests'] == {'debug': 72, 'release': 72, 'passed': True}
    for name, digest in build['source_sha256'].items():
        assert sha(ROOT / name) == digest, name
    base = read('benchmarks/baseline-0.3.11-provenance.json')
    for name, digest in base['core_source_sha256'].items():
        assert sha(ROOT / 'benchmarks/baseline-0.3.11-source' / name) == digest, name
    assert sha(ROOT.parent / 'kestrel-sql-0.3.11.zip') == base['archive_sha256']
    changed = {name for name, digest in base['core_source_sha256'].items() if sha(ROOT / name) != digest}
    assert changed == {'Cargo.toml', 'Cargo.lock', 'src/archive.rs'}, changed
    old = (ROOT / 'benchmarks/baseline-0.3.11-source/src/archive.rs').read_text(encoding='utf-8')
    new = (ROOT / 'src/archive.rs').read_text(encoding='utf-8')
    constants = 'const LARGE_GROUP_CACHE_SLOTS: usize = 16_384;\nconst LARGE_GROUP_CACHE_MAX_KEYS: usize = 8192;\ntype LargeGroupKeyCache = [Option<(i64, usize)>; LARGE_GROUP_CACHE_SLOTS];\n'
    assert old[:old.index('struct SparseGroups {')] == new[:new.index('struct SparseGroups {')].replace(constants, '')
    marker = '#[derive(Clone, Default)]\nstruct Cell'
    assert old[old.index(marker):old.index('#[cfg(test)]')] == new[new.index(marker):new.index('#[cfg(test)]')]
    reports = [read(f'benchmarks/group-042-{scope}-comparison.json') for scope in ['typed', 'nyc', 'large', 'extended', 'patterns', 'irregular']]
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
        ('final-pairs', 3, 21, 11, False), ('sparse-guard-pairs', 3, 21, 11, False),
        ('scan-guard-pairs', 4, 21, 11, False), ('highcard-guard-pairs', 2, 21, 11, False),
        ('tiny-guard-pairs', 3, 21, 101, False), ('final-profiles', 3, 7, 11, True),
        ('irregular-pairs',4,21,11,False), ('irregular-profiles',4,7,11,True),
    ]:
        report = read(f'benchmarks/cache-042-{name}.json')
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
    for name in ['sparse-guard-pairs','scan-guard-pairs','highcard-guard-pairs','tiny-guard-pairs']:
        assert all(c['paired_candidate_over_baseline_median'] < 1.1 for c in controls[name]['cases']), name
    assert all(c['paired_candidate_over_baseline_median'] < 0.95 for c in controls['irregular-pairs']['cases'] if c['name']!='unordered_control')
    assert next(c for c in controls['irregular-pairs']['cases'] if c['name']=='unordered_control')['paired_candidate_over_baseline_median'] < 1.1
    general = read('benchmarks/archive-042-verification.json')
    groups = read('benchmarks/group-042-differential.json')
    scans = read('benchmarks/scan-042-differential.json')
    assert general['binary_sha256'] == build['cli_sha256'] and general['queries_checked_against_each_reference'] == 500
    assert all(q['passed'] for q in general['queries'])
    for proof, count in [(groups, 500), (scans, 600)]:
        assert proof['binary_sha256'] == build['bridge_sha256'] and proof['complete']
        assert proof['queries_checked_against_each_reference'] == count
        assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in proof['cases'])
    assert all(f['reopen_retry_and_scrub_passed'] for f in scans['fixtures'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in groups['modes'])
    cache = read('benchmarks/cache-042-differential.json')
    assert cache['complete'] and cache['queries_checked_against_each_reference'] == 600
    assert cache['binary_sha256'] == build['bridge_sha256']
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in cache['cases'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in cache['modes'])
    medium = read('benchmarks/medium-042-differential.json')
    assert medium['complete'] and medium['binary_sha256'] == build['bridge_sha256']
    assert medium['queries_checked_against_each_reference'] == 600
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in medium['cases'])
    assert all(f['reopen_replay_and_scrub_passed'] for f in medium['modes'])
    assert medium['exact_medium_signed_wide_group_json_and_reopen_retry']
    faults = read('benchmarks/publication-042-faults.json')
    assert faults['binary_sha256'] == build['bridge_sha256'] and faults['fault_driver_sha256'] == build['fault_driver_sha256']
    assert len(faults['cut_points']) == 56 and len(faults['corruption_cases']) == 22
    assert all(c['original_receipts_preserved'] and c['atomic_rows_and_sum'] and c['retry_deduplication_passed'] and c['full_scrub_passed'] for c in faults['cut_points'])
    assert all(c['rejected'] for c in faults['corruption_cases'])
    recovery = read('benchmarks/group-042-recovery.json')
    source = read('benchmarks/source-042-faults.json')
    assert recovery['binary_sha256'] == build['bridge_sha256'] and len(recovery['cycles']) == 32 and not recovery['failed_cases']
    assert source['driver_sha256'] == build['source_fault_driver_sha256']
    assert source['adapter_sha256'] == read('benchmarks/source-042-typed-adapter-build.json')['binary_sha256']
    assert len(source['cases']) == 14 and len(source['kill_cycles']) == 8 and not source['failed_cases']
    pipeline = read('portfolio/source-pipeline-042-results.json')
    assert pipeline['stats']['archive']['rows'] == 30000 and sum(p['committed_batches'] for p in pipeline['positions']) == 300
    assert pipeline['exact_sql_cases_against_duckdb'] == 42 and pipeline['full_scrub_passed']
    assert pipeline['source_positions_and_data_reopen_together'] and pipeline['replay_and_invalid_intervals_passed']
    wire = read('benchmarks/wire-042-audit.json')
    assert wire['cli_sha256'] == build['cli_sha256'] and wire['bridge_sha256'] == build['bridge_sha256']
    assert all(wire[k] for k in ['exact_positive_and_negative_wide_archive_json', 'exact_wide_ram_json', 'sparse_bridge_error_continuity_retry_reopen_and_scrub'])
    timed = read('benchmarks/cache-042-run-order.json')
    qualified = read('benchmarks/correctness-042-run-order.json')
    assert len({r['scope'] for r in timed if r['returncode']==0}) == 12
    assert len(timed)==14 and len([r for r in timed if r['returncode']!=0])==2
    assert all(r['scope']=='irregular' for r in timed if r['returncode']!=0)
    prior_helper_hashes=set()
    for kind in ['setup','batch']:
        repair=read(f'benchmarks/cache-042-{kind}-repair.json')
        for name,digest in repair['before'].items():
            preserved=ROOT/'benchmarks'/(Path(name).stem+f'-before-{kind}-repair.py')
            assert sha(preserved)==digest
            if name=='group_compare_042.py':prior_helper_hashes.add(digest)
    for r in timed:
        helper=ROOT/r['command'][1]
        allowed={sha(helper)}
        if helper.name=='group_compare_042.py':allowed.update(prior_helper_hashes)
        assert r['harness_sha256'] in allowed
    assert len({r['suite'] for r in qualified if r['returncode'] == 0}) == 10
    assert all(a['completed_at_utc'] <= b['started_at_utc'] for a, b in zip(timed, timed[1:]))
    adapter = read('benchmarks/source-042-typed-adapter-build.json')
    assert max(r['completed_at_utc'] for r in build['build_run_order']) < adapter['started_at_utc'] < adapter['completed_at_utc'] < timed[0]['started_at_utc']
    followup=read('benchmarks/cache-042-follow-up-run-order.json')
    assert len(followup)==2 and all(r['returncode']==0 for r in followup)
    assert timed[-1]['completed_at_utc'] <= followup[0]['started_at_utc']
    assert followup[0]['completed_at_utc'] <= followup[1]['started_at_utc']
    assert followup[-1]['completed_at_utc'] <= qualified[0]['started_at_utc']
    for r in followup:assert r['harness_sha256']==sha(ROOT/r['command'][1])
    assert all(a['completed_at_utc'] <= b['started_at_utc'] for a, b in zip(qualified, qualified[1:]))
    for trial_name in ['reuse-gated-large','deferred-large']:
        trial = read(f'benchmarks/trial-042-{trial_name}/proof.json')
        assert trial['debug_tests_passed'] == 72
        for relative,digest in trial['source_sha256'].items():
            assert sha(ROOT / f'benchmarks/trial-042-{trial_name}/source' / relative) == digest
        assert sha(Path(trial['group_probe'])) == trial['group_probe_sha256']
    assert (ROOT / 'benchmarks/trial-042-deferred-large/source/src/archive.rs').read_bytes() == (ROOT/'src/archive.rs').read_bytes()
    assert read('benchmarks/cache-042-deferred-small-pairs.json')['completed_at_utc'] < build['build_run_order'][0]['started_at_utc']
    rejected = read('benchmarks/cache-042-trial-eager-tiny-pairs.json')
    assert rejected['complete'] and all(c['paired_candidate_over_baseline_median'] > 1.5 for c in rejected['cases'])
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
    assert sum(sample_count(r) for k,r in controls.items() if not r['methodology']['instrumented']) == 20118
    assert sum(sample_count(r) for r in controls.values() if r['methodology']['instrumented'])==1078
    audit = {'version':'0.3.12', 'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_sha256':build['source_sha256'], 'rust_tests_each_mode':72,
        'baseline':'0.3.11', 'baseline_provenance':base,
        'primary_score':score(primary), 'extended_score':score(extra), 'pattern_score':score(patterns), 'irregular_score':score(irregular),
        'current_comparison_cases':108, 'current_query_shapes':60, 'current_timed_query_samples':samples,
        'current_comparisons':primary, 'extended_comparisons':extra, 'pattern_comparisons':patterns, 'irregular_comparisons':irregular,
        'paired_controls':{name:[{k:v for k,v in c.items() if k!='pairs'} for c in r['cases']] for name,r in controls.items()},
        'unprofiled_control_samples':20118, 'profiled_control_samples_excluded':1078,
        'sql_cases_against_each_reference':2800, 'publication_cut_points':56, 'catalog_corruption_rejections':22,
        'forced_kills':32, 'source_fault_cut_points':14, 'source_forced_kills':8,
        'parquet_rows':30000, 'source_intervals':300, 'parquet_sql_oracles':42,
        'no_compilation_overlap_with_timed_database_work':True,
        'storage_publication_live_source_prefix_reader_and_dense_helpers_unchanged':True,
        'service_qualification':'No new network requests/s qualification; previous mixed-write losses and stalls remain visible',
        'qualification_harness_failures':[r for r in qualified if r['returncode'] != 0],
        'report_harness_repairs':[], 'benchmark_harness_repairs':[read('benchmarks/cache-042-setup-repair.json'),read('benchmarks/cache-042-batch-repair.json')],
        'benchmark_harness_failures':[r for r in timed if r['returncode']!=0],
        'preserved_development_trials':['reuse-gated-large: rejected for unused final-block allocation; exact source and binary retained', 'deferred-large: allocation waits for the next nonempty block; final version rebuilt and remeasured'],
        'extra_large_cache_bytes_on_this_64bit_platform':393216,
        'promotion_policy':'After the 128-key cache is abandoned, require at least 50% repeated keys in a block of 64 or more selected rows, at most 8192 keys, and a later nonempty block; one promotion attempt, exact tags, low-hit fallback',
        'limits':['Warm single-thread queries on one shared Windows computer',
          'Rust direct query timer versus DuckDB Python execute/fetchall; native storage layouts differ',
          'Cache multiplier changes per query; unlucky seeds and constructed collisions still fall back, without a latency guarantee',
          'Promoted sparse queries allocate an additional 384 KiB on this 64-bit computer; other shapes can trade speed for cache bookkeeping',
          'Only DuckDB freshly compared; last multi-server matrix remains 0.3.1',
          'No new network, cold-I/O, power-loss, distributed-scale or production qualification']}
    (ROOT / 'benchmarks/cache-042-audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    lines = ['# 0.3.12: reuse-triggered sparse GROUP BY acceleration', '',
        'A wider tagged lookup cache accelerates repeatedly used sparse keys after the small cache has been abandoned. Promotion requires at least 50% repeated keys in a selected block of at least 64 rows, at most 8,192 distinct keys, and another nonempty block. The optional 16,384-slot table occupies 384 KiB on this 64-bit computer. Queries get one promotion attempt; key growth or poor hit rate releases it. Every hit checks the exact signed key. The existing randomized HashMap remains authoritative, and exact i128 typed reductions are unchanged.', '',
        'The released 0.3.11 wide5003 loss was concentrated in hash mapping: initial stage profiles put roughly 16.3 ms of a 22.2 ms GROUP SUM query in aggregation. The first larger-cache trial improved this fixture but allocated its table after the final block of a tiny query. That trial regressed the 1,000-row/129-key guard by 75–79%. Its source, binary and complete timings remain preserved. The selected implementation defers allocation until another block actually needs it. Separate trial measurements recovered the tiny-query guard, and the final version is independently rebuilt and remeasured below.', '',
        'Fresh comparisons retain 108 engine/fixture/round cases, 60 shapes and 5,940 samples. The previous 55 shapes are retained; five added shapes use 5,003 irregular signed i64 keys, including both extremes, on one million rows. There are 20,118 additional uninstrumented paired samples, including a tiny-query guard, and 1,078 instrumented samples excluded from competitive totals. Matrix cases use three rotated orders, three warmups, eleven samples and one thread. Rust samples time ArchiveSnapshot::query; DuckDB samples include Python execute/fetchall. Storage layouts differ. Builds, setup, result assertions and scrubs are untimed; all workloads run serially on this shared Windows computer.', '',
        f"DuckDB scores: matched {score(primary)['wins']} wins / {score(primary)['losses']} losses; prior stress {score(extra)['wins']} / {score(extra)['losses']}; key patterns {score(patterns)['wins']} / {score(patterns)['losses']}; irregular keys {score(irregular)['wins']} / {score(irregular)['losses']}. Every per-shape win/loss and round count is retained below.", '',
        '## Final alternating controls', '',
        'Before/after medians are pooled across pair medians; the paired ratio is the median of candidate/baseline within each pair. These two summaries can differ during shared-desktop variance. Lower ratios are faster. All outputs match exactly.', '',
        '| Control | Query | 0.3.11 ms | 0.3.12 ms | Paired candidate / baseline |', '|---|---|---:|---:|---:|']
    for name in ['final-pairs','highcard-guard-pairs','sparse-guard-pairs','scan-guard-pairs','tiny-guard-pairs','irregular-pairs']:
        for c in controls[name]['cases']:
            lines.append(f"| {name} | {c['name']} | {c['baseline_median_ms']:.4f} | {c['candidate_median_ms']:.4f} | {c['paired_candidate_over_baseline_median']:.4f} |")
    lines += ['', '## Stage diagnosis, excluded from competitive results', '',
        '| Fixture | Query | Read before / after ms | Selection before / after ms | Aggregate before / after ms |', '|---|---|---:|---:|---:|']
    for name in ['final-profiles','irregular-profiles']:
        for c in controls[name]['cases']:
            before=c['stage_median_ms']['baseline']; after=c['stage_median_ms']['candidate']
            lines.append('| '+controls[name]['fixture']['label']+' | '+c['name']+' | '+' | '.join(f"{before[stage]:.3f} / {after[stage]:.3f}" for stage in ['page_read_ms','selection_ms','aggregate_ms'])+' |')
    lines += ['', 'The irregular-key rotated matrix showed GROUP SUM slower than baseline, alongside an untouched scan slowdown. Follow-up alternating pairs on the same archive measured grouping 15–20% faster than baseline and the scan within about 1%. Stage profiles show reduced aggregation cost with similar page-read times. These follow-ups support a grouping improvement while retaining the original rotated results and its two DuckDB losses; they do not replace them.', '']
    for title,cases in [('Matched matrix',primary),('Prior stress matrix',extra),('Prior key-pattern matrix',patterns),('Irregular signed-key matrix',irregular)]:
        lines += ['', '## '+title, '', '| Fixture | Query | 0.3.11 ms | 0.3.12 ms | DuckDB ms | Paired baseline / candidate | vs DuckDB |', '|---|---|---:|---:|---:|---:|---|']
        for c in cases:
            m=c['run_median_ms']; mark='✅' if c['candidate_vs_duckdb']=='win' else '❌'
            lines.append(f"| {c['fixture']} | {c['query']} | {m['baseline']:.3f} | {m['candidate']:.3f} | {m['duckdb']:.3f} | {c['paired_baseline_over_candidate_median']:.3f}x | {mark}; {c['candidate_faster_than_duckdb_rounds']}/3 rounds |")
    lines += ['', '## Correctness, durability and limits', '',
        'All 72 Rust tests pass in debug/release, formatting and both Clippy configurations. New tests cover deferred promotion, real seed-specific collisions, release after 8,193 keys, signed extremes, exact beyond-i64 sums and all typed grouped reductions against an independent BTreeMap. Unchanged readers, publication, dense grouping, live ingestion, source and SQL code are checked byte-for-byte against the preserved release; only Cargo versions and the sparse helper/tests change.', '',
        'The final binaries match 2,800 SQL cases against each DuckDB and SQLite: 500 general, 500 grouping, 600 key patterns, 600 medium/irregular/late-growth/high-cardinality and 600 scans. Medium signed groups also emit exact beyond-i64 integer JSON through the actual bridge after confirmed retry and reopen. Current binaries pass 56 publication cuts, 22 catalog corruption rejections, 32 process kills, 14 source faults, eight source kills and the 30,000-row/300-interval Parquet workflow with 42 SQL checks. Process/injected I/O tests do not qualify physical power loss.', '',
        'Promotion trades an optional 384 KiB allocation for less repeated hash work. The hit-rate gate, key budget and one-attempt policy bound the cache, but random seeds and constructed collisions still vary latency. All guard results, unsuccessful trial evidence and broad matrix shifts are visible. Changes on untouched dense/scan/prefix paths are measurements, without attribution to this cache. Only DuckDB is freshly competed; the last multi-server network comparison remains [0.3.1](PERFORMANCE_031.md), including mixed-write losses and stalls. Network capacity, cold I/O, distributed scale and production readiness are unqualified.', '',
        'The irregular-fixture harness initially created a directory before Engine.__init__ created it again. This stopped setup before any database query. A subsequent seed request exceeded the retained test bridge request limits; seeding now uses 10,000-row batches, and wide JSON tests use three 5,003-row batches. Both failures, source snapshots, logs and run-order entries are preserved. The repaired runner resumed only unfinished scopes; all five completed matrices remained unchanged.', '',
        '## Reproduce and inspect', '',
        'Run checks_042.py, build_source_adapter_042.py, time_042.py, follow_up_042.py, run_042.py, report_042.py, docs_042.py and package_042.py serially with the pinned local Python dependencies. Completed outputs and archives must remain immutable. Controls reuse retained fixtures; matrix scripts can seed fixtures independently. Never overlap compilation, testing or packaging with timed database work. Release 0.3.12 uses experiment identifier 042.', '',
        '- [Complete gates and scores](benchmarks/cache-042-audit.json)',
        '- [Final wide-key pairs](benchmarks/cache-042-final-pairs.json)',
        '- [Tiny-query guard](benchmarks/cache-042-tiny-guard-pairs.json)',
        '- [High-cardinality guard](benchmarks/cache-042-highcard-guard-pairs.json)',
        '- [Small sparse guards](benchmarks/cache-042-sparse-guard-pairs.json)',
        '- [Scan and dense guards](benchmarks/cache-042-scan-guard-pairs.json)',
        '- [Final stage profiles](benchmarks/cache-042-final-profiles.json)',
        '- [Original released-binary profiles](benchmarks/cache-042-baseline-wide-profiles.json)',
        '- [Rejected eager trial](benchmarks/trial-042-reuse-gated-large/proof.json)',
        '- [Rejected tiny-query regression](benchmarks/cache-042-trial-eager-tiny-pairs.json)',
        '- [Deferred trial source and build](benchmarks/trial-042-deferred-large/proof.json)',
        '- [Deferred trial wide-key pairs](benchmarks/cache-042-deferred-wide-pairs.json)',
        '- [Deferred trial tiny guard](benchmarks/cache-042-deferred-tiny-pairs.json)',
        '- [Irregular signed-key raw matrix](benchmarks/group-042-irregular-comparison.json)',
        '- [Irregular-key alternating pairs](benchmarks/cache-042-irregular-pairs.json)',
        '- [Irregular-key stage profiles](benchmarks/cache-042-irregular-profiles.json)',
        '- [Follow-up timing order](benchmarks/cache-042-follow-up-run-order.json)',
        '- [Medium-cardinality SQL oracles](benchmarks/medium-042-differential.json)',
        '- [Build provenance](benchmarks/rust-checks-042.json)',
        '- [Timed work order](benchmarks/cache-042-run-order.json)',
        '- [Qualification order](benchmarks/correctness-042-run-order.json)',
        '- [Preserved benchmark setup failure and repair](benchmarks/cache-042-setup-repair.json)',
        '- [Preserved seed request limit failure and repair](benchmarks/cache-042-batch-repair.json)',
        '- [Previous results](BENCHMARK_HISTORY.md)', '']
    (ROOT / 'PERFORMANCE_042.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'version':'0.3.12','rust_tests_each_mode':72,'sql_cases_each_reference':2800,
        'primary':score(primary),'extra':score(extra),'patterns':score(patterns),'irregular':score(irregular)}),flush=True)

if __name__ == '__main__': main()
