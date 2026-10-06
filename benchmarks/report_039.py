"""Gate qualification and retain all current shapes, controls and losing trials."""
import argparse
import datetime
import hashlib
import json
import statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def read(name): return json.loads((ROOT/name).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def summaries(report):
    assert report['complete']
    results = []
    for fixture in report['fixtures']:
        for name, sql in fixture['queries']:
            series = {}
            for variant in ['baseline', 'candidate', 'duckdb']:
                series[variant] = [next(q for q in c['queries'] if q['name']==name) for c in report['cases']
                    if c['fixture']==fixture['label'] and c['variant']==variant]
                assert len(series[variant])==3
                assert all(len(q['samples_ms'])==11 and q['all_repeated_and_reference_results_equal'] for q in series[variant])
            medians = {v:statistics.median(q['median_ms'] for q in cases) for v,cases in series.items()}
            speedups = [a['median_ms']/b['median_ms'] for a,b in zip(series['baseline'],series['candidate'])]
            results.append({'fixture':fixture['label'], 'query':name, 'sql':sql, 'rows':fixture['rows'],
                'run_median_ms':medians, 'run_medians_ms':{v:[q['median_ms'] for q in cases] for v,cases in series.items()},
                'paired_baseline_over_candidate_median':statistics.median(speedups), 'paired_speedup_range':[min(speedups),max(speedups)],
                'candidate_vs_duckdb':'win' if medians['candidate']<medians['duckdb'] else 'loss',
                'candidate_faster_than_duckdb_rounds':sum(c['median_ms']<d['median_ms'] for c,d in zip(series['candidate'],series['duckdb'])),
                'candidate_plan':series['candidate'][0]['result']['plan'], 'results_equal':True})
    return results

def score(cases):
    wins = sum(c['candidate_vs_duckdb']=='win' for c in cases)
    return {'wins':wins,'losses':len(cases)-wins,'query_shapes':len(cases)}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--progress',action='store_true'); args=parser.parse_args()
    if args.progress:
        for scope in ['typed','nyc','large','extended']:
            path=ROOT/f'benchmarks/group-039-{scope}-comparison.json'
            if path.exists() and read(path.relative_to(ROOT))['complete']:
                cases=summaries(read(path.relative_to(ROOT)))
                print(json.dumps({'scope':scope,'score':score(cases), 'groups':[c for c in cases if c['query'] in ['group_full','all_zones']]}))
        return
    build=read('benchmarks/rust-checks-039.json')
    assert build['rust_tests']=={'debug':69,'release':69,'passed':True}
    for relative,digest in build['source_sha256'].items(): assert sha(ROOT/relative)==digest,relative
    reports=[read(f'benchmarks/group-039-{scope}-comparison.json') for scope in ['typed','nyc','large','extended']]
    assert [len(r['cases']) for r in reports]==[27,9,18,27]
    assert all(r['binary_sha256']['candidate']==build['group_probe_sha256'] for r in reports)
    primary=[c for r in reports[:3] for c in summaries(r)]
    extended=summaries(reports[3]); assert len(primary)==30 and len(extended)==15
    controls=read('benchmarks/group-039-paired-controls.json'); cache=read('benchmarks/group-039-cache-pairs.json')
    large_pairs=read('benchmarks/group-039-large-pairs.json')
    assert large_pairs['complete'] and len(large_pairs['cases'])==2
    assert all(len(c['pairs'])==7 and c['all_results_equal'] for c in large_pairs['cases'])
    assert controls['complete'] and len(controls['cases'])==8
    assert cache['complete'] and len(cache['cases'])==7
    for case in controls['cases']: assert len(case['pairs'])==21 and case['all_results_equal']
    for case in cache['cases']: assert len(case['pairs'])==11 and case['all_results_equal']
    trial=read('benchmarks/group-039-typed-trial-provenance.json')
    assert cache['binary_sha256']['baseline']==trial['binary_sha256']
    assert controls['binary_sha256']['candidate']==cache['binary_sha256']['candidate']==build['group_probe_sha256']
    differential=read('benchmarks/archive-039-verification.json'); group_diff=read('benchmarks/group-039-differential.json')
    assert differential['queries_checked_against_each_reference']==500 and all(q['passed'] for q in differential['queries'])
    assert group_diff['complete'] and group_diff['queries_checked_against_each_reference']==500
    assert all(c['duckdb_equal'] and c['sqlite_equal'] for c in group_diff['cases'])
    assert all(c['reopen_replay_and_scrub_passed'] for c in group_diff['modes'])
    faults=read('benchmarks/publication-039-faults.json')
    assert len(faults['cut_points'])==56 and len(faults['corruption_cases'])==22
    assert all(c['original_receipts_preserved'] and c['atomic_rows_and_sum'] and c['retry_deduplication_passed'] and c['full_scrub_passed'] for c in faults['cut_points'])
    assert all(c['rejected'] for c in faults['corruption_cases'])
    recovery=read('benchmarks/group-039-recovery.json'); source=read('benchmarks/source-039-faults.json')
    assert len(recovery['cycles'])==32 and not recovery['failed_cases']
    assert len(source['cases'])==14 and len(source['kill_cycles'])==8 and not source['failed_cases']
    pipeline=read('portfolio/source-pipeline-039-results.json')
    assert pipeline['stats']['archive']['rows']==30000 and sum(p['committed_batches'] for p in pipeline['positions'])==300
    assert pipeline['exact_sql_cases_against_duckdb']==42 and pipeline['full_scrub_passed']
    assert pipeline['source_positions_and_data_reopen_together'] and pipeline['replay_and_invalid_intervals_passed']
    wire=read('benchmarks/wire-039-audit.json')
    assert wire['cli_sha256']==differential['binary_sha256']==build['cli_sha256']
    assert wire['bridge_sha256']==group_diff['binary_sha256']==recovery['binary_sha256']==build['bridge_sha256']
    assert faults['binary_sha256']==build['bridge_sha256'] and faults['fault_driver_sha256']==build['fault_driver_sha256']
    order=read('benchmarks/correctness-039-run-order.json'); timed_order=read('benchmarks/group-039-run-order.json')
    assert len([r for r in order if r['returncode']==0])==8
    assert len({r['suite'] for r in order if r['returncode']==0})==8
    assert len(timed_order)==4 and all(r['returncode']==0 for r in timed_order)
    adapter=read('benchmarks/source-039-typed-adapter-build.json')
    latest_build=max(r['completed_at_utc'] for r in build['build_run_order'])
    assert latest_build<adapter['started_at_utc'] and adapter['completed_at_utc']<timed_order[0]['started_at_utc']
    assert all(a['completed_at_utc']<b['started_at_utc'] for a,b in zip(timed_order,timed_order[1:]))
    assert timed_order[-1]['completed_at_utc']<controls['started_at_utc']<controls['completed_at_utc']<cache['started_at_utc']
    assert cache['completed_at_utc']<large_pairs['started_at_utc']<large_pairs['completed_at_utc']<order[0]['started_at_utc']
    base=read('benchmarks/baseline-0.3.8-provenance.json')
    for relative,digest in base['core_source_sha256'].items(): assert sha(ROOT/'benchmarks/baseline-0.3.8-source'/relative)==digest
    changed={p for p,d in base['core_source_sha256'].items() if sha(ROOT/p)!=d}
    assert changed=={'Cargo.toml','Cargo.lock','src/archive.rs','tests/archive.rs'},changed
    old=(ROOT/'benchmarks/baseline-0.3.8-source/src/archive.rs').read_text(); new=(ROOT/'src/archive.rs').read_text()
    query='    fn query_inner<const PROFILE: bool>('
    def prefix(s):
        return '\n'.join(line for line in s.split(query)[0].splitlines() if not line.startswith((
            'const MAX_DENSE_GROUP_SLOTS:', 'const GROUP_KEY_CACHE_', 'type GroupKeyCache =')))
    assert prefix(old)==prefix(new)
    verify='    /// Read every data block and validate its checksum and cumulative aggregate index.'
    dense='/// A query-local direct-address table for bounded integer domains.'
    assert old.split(verify)[1].split(dense)[0]==new.split(verify)[1].split(dense)[0]
    assert old.split('impl Cell {\n')[1].split('    fn update(')[0]==new.split('impl Cell {\n')[1].split('    fn value(')[0]
    assert old.split('fn retain_matching(')[1].split('#[cfg(test)]')[0]==new.split('fn retain_matching(')[1].split('#[cfg(test)]')[0]
    audit={'version':'0.3.9','recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source_sha256':build['source_sha256'],'rust_tests_each_mode':69,'current_cases':81,'current_query_shapes':45,
        'current_timed_query_samples':4455,'primary_score':score(primary),'extended_score':score(extended),
        'summaries':primary,'extended_summaries':extended,'paired_controls':controls['cases'],'cache_pairs':cache['cases'],
        'additional_control_samples':5530,'initial_typed_trial_timed_samples':1485,
        'paired_large_controls':large_pairs['cases'],
        'qualification_harness_failures':[r for r in order if r['returncode']!=0],
        'sql_differential_against_each_reference':1000,'publication_fault_cut_points':56,'catalog_corruption_rejections':22,
        'concurrent_forced_kills':32,'source_fault_cut_points':14,'source_forced_kills':8,'parquet_rows':30000,
        'source_intervals':300,'parquet_sql_oracles':42,'source_pipeline_proof':'portfolio/source-pipeline-039-results.json',
        'storage_publication_live_source_and_scan_helpers_unchanged':True,'no_compilation_overlap_with_timed_database_work':True,
        'service_qualification':'No new network req/s qualification; prior mixed-write stalls and SLO failures remain visible',
        'limits':['Shared Windows computer, warm single-thread timings, direct Rust API versus DuckDB Python execute/fetch',
            'Only DuckDB freshly compared; the last multi-server matrix remains 0.3.1',
            'No cold-I/O, physical power-loss, distributed-scale or production qualification'],
        'prior_art':'Rust default HashMap retained; typed reductions and lookup caches are established techniques; no novelty claim'}
    (ROOT/'benchmarks/group-039-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    lines=['# 0.3.9: wider bounded grouping and typed sparse states','',
        'Compact integer groups now use direct-address arrays for up to 65,536 slots, while keeping the conservative 8 MiB query-local budget. Above the original 4,096-slot range, the slot count must also fit the archive row count. Wide domains use a standard randomized HashMap from key to slot and the same typed reductions. A query-local tagged cache holds 256 key/slot entries (6 KiB on this host), verifies exact keys on every hit and is released after 128 distinct keys or a block of at least 64 selected rows with fewer than half cache hits. Disabled-cache blocks use a separate plain-hash kernel with cache checks compiled out. SUM/AVG and repeated reductions share accumulators. The 100,000-result group limit remains.', '',
        'Fresh comparisons contain 81 sequential engine/fixture/round cases, 45 query shapes and 4,455 timed samples. Each shape has three rotated engine orders, three warmups and eleven samples. Tables show the median of run medians and the median paired before/after ratio. Both engines use one thread and warm caches. Rust timers cover ArchiveSnapshot::query; DuckDB timers include Python execute/fetchall, with native compression and a 256 MB buffer limit. Setup, JSON framing, assertions and scrubs are outside Rust timers. These are descriptive shared-desktop measurements.', '',
        f"The matched 30-shape matrix has {score(primary)['wins']} median wins and {score(primary)['losses']} losses against DuckDB. The additional 15-shape stress matrix has {score(extended)['wins']} wins and {score(extended)['losses']} losses. Per-round outcomes and every loss remain below.", '']
    for title,cases in [('Matched matrix',primary),('Additional wide/collision/high-cardinality matrix',extended)]:
        lines += ['## '+title,'','| Fixture | Query | 0.3.8 ms | 0.3.9 ms | DuckDB ms | Paired improvement | vs DuckDB |','|---|---|---:|---:|---:|---:|---|']
        for c in cases:
            m=c['run_median_ms']; mark='\u2705' if c['candidate_vs_duckdb']=='win' else '\u274c'
            lines.append(f"| {c['fixture']} | {c['query']} | {m['baseline']:.3f} | {m['candidate']:.3f} | {m['duckdb']:.3f} | {c['paired_baseline_over_candidate_median']:.2f}x | {mark}; {c['candidate_faster_than_duckdb_rounds']}/3 rounds |")
        lines += ['']
    for title,report in [('Short controls against released 0.3.8',controls),('Cache versus the preserved uncached 0.3.9 trial',cache),('Large controls on the same 100M-row archive',large_pairs)]:
        lines += ['## '+title,'',report['methodology']+'. A ratio above 1 means the final candidate was slower.','',
            '| Fixture | Query | Baseline ms | Final ms | Paired final/baseline |','|---|---|---:|---:|---:|']
        for c in report['cases']: lines.append(f"| {c['fixture']} | {c['name']} | {c['baseline_median_ms']:.3f} | {c['candidate_median_ms']:.3f} | {c['paired_candidate_over_baseline_median']:.3f} |")
        lines += ['']
    lines += ['The original rotated 100M-row full-grouping slowdown did not repeat in seven short alternating pairs. The unordered scan control remains about 5-7% slower in paired 1M/100M checks and is a known regression. These observations are preserved even though the ungrouped scan helpers are byte-identical in source. Shared-desktop variation is substantial; unchanged algorithm text is not evidence of unchanged measured latency.', '']
    lines += ['## Correctness and recovery','',
        'All 69 Rust tests pass in debug/release, with formatting and default/fault-feature Clippy. New tests cover larger compact domains, signed edges, holes, exact wide sums and duplicate SUM/AVG outputs, tagged-cache collisions and cardinality release, and accepting known keys at the 100,000-group limit. One thousand seeded SQL queries match both DuckDB and SQLite: 500 general archive cases and 500 expanded/signed-sparse group cases over eight overlapping sorted runs. Both group modes also pass reopen, known-receipt replay and full scrubs.', '',
        'The current CLI/bridge pass exact positive/negative i128 sparse sums through JSON, invalid-query continuity, replay/reopen and CRC scrub. Current binaries pass 56 publication cut points, 22 corrupt-catalog rejections, 32 concurrent forced kills, 14 source failures, eight source kills and the 30,000-row/300-interval Parquet demo with 42 SQL oracles. Storage/publication/live/source and ungrouped scan helpers are unchanged. These are process/IO failure checks, not physical power-loss qualification.', '',
        'The uncached typed trial and its 1,485 timed samples, source and binary hashes are preserved. Its expanded-domain gain passed, while low-cardinality sparse grouping still lost to DuckDB and motivated the bounded cache. The first cached candidate, its 4,455 comparison samples, 5,390 paired samples, 68-test build and exact source/probe are also preserved. Its 4-7% cache penalty on colliding/wider keys motivated block specialization and cache usefulness detection. The initial profile-runner result-envelope error is recorded. Earlier releases, failed experiments, service failures and all original timing samples remain unchanged.', '',
        'The authoritative sparse map keeps Rust\'s default randomized hashing. Cache misses and collisions always return to that map; the cache cannot alias keys. [Rust HashMap documentation](https://doc.rust-lang.org/std/collections/struct.HashMap.html) describes its default randomized protection and the tradeoffs of replacing the hasher. This experiment changes state layout and reuses confirmed key lookups.', '',
        'No new requests/s, cold-I/O, sustained mixed-write, distributed-scale or production readiness claim follows from these read-query measurements. The previous multi-server matrix is [0.3.1](PERFORMANCE_031.md).', '',
        '## Reproduce and inspect','',
        'Run serially: `python benchmarks/checks_039.py`, `python benchmarks/build_source_adapter_039.py`, then `group_compare_039.py` for each scope with fresh output names. Small and extended scopes can regenerate integer fixtures; `--reuse-small-fixtures` reuses this computer\'s retained 0.3.8 datasets. Large/NYC paths are configurable with `--scale-root` and `--nyc-root`. Use the pinned local DuckDB installation. Never overlap compilation, tests, packaging or other heavy work with query timing. Completed outputs and release packages refuse replacement.', '',
        '- [All qualified summaries and limits](benchmarks/group-039-audit.json)',
        '- [Matched 1M-row samples](benchmarks/group-039-typed-comparison.json)',
        '- [NYC samples](benchmarks/group-039-nyc-comparison.json)',
        '- [10M/100M-row samples](benchmarks/group-039-large-comparison.json)',
        '- [Collision/wide/70,001-key samples](benchmarks/group-039-extended-comparison.json)',
        '- [Short paired controls](benchmarks/group-039-paired-controls.json)',
        '- [100M-row same-archive controls](benchmarks/group-039-large-pairs.json)',
        '- [Cache pairs and original trial](benchmarks/group-039-cache-pairs.json)',
        '- [Original uncached trial samples](benchmarks/group-039-typed-trial-comparison.json)',
        '- [Initial stage profiles](benchmarks/group-039-baseline-profiles.json)',
        '- [Preserved first-cache trial and regressions](benchmarks/trial-039-first-cache/trial-audit.json)',
        '- [Final stage profiles](benchmarks/group-039-final-profiles.json)',
        '- [Expanded/sparse SQL oracle cases](benchmarks/group-039-differential.json)',
        '- [Serial builds](benchmarks/rust-checks-039.json)',
        '- [Serial timed scopes](benchmarks/group-039-run-order.json)',
        '- [Correctness/recovery order](benchmarks/correctness-039-run-order.json)',
        '- [Complete historical index](BENCHMARK_HISTORY.md)','']
    (ROOT/'PERFORMANCE_039.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'primary':score(primary),'extended':score(extended),'tests_each_mode':69,'qualification':'passed'}))

if __name__=='__main__': main()
