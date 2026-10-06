"""Audit raw evidence and generate the 0.3.1 report; timings are never rerun here."""
import argparse
import json
import math
import statistics
from pathlib import Path

from report_v03 import audit

ROOT = Path(__file__).resolve().parents[1]
LABELS = {'baseline':'Kestrel 0.3.0','candidate':'Kestrel 0.3.1','postgres':'PostgreSQL',
    'mysql':'MySQL','mariadb':'MariaDB','sqlite':'SQLite','duckdb':'DuckDB'}


def read(name):
    return json.loads((ROOT/'benchmarks'/name).read_text(encoding='utf-8'))


def raw_percentile(values, p):
    """Rust probes publish unrounded nearest-rank values; stress rounds to 4dp."""
    return sorted(values)[math.ceil(len(values)*p)-1]


def summaries(report,profile):
    variants = list(dict.fromkeys(c['variant'] for c in report['cases']))
    rows = []
    for variant in variants:
        cases = [c for c in report['cases'] if c['variant']==variant and c['profile']==profile]
        assert len(cases)==3
        p99 = [c['latency_ms']['p99'] for c in cases]
        rows.append({'variant':variant,'median_rps':statistics.median(c['successful_rps_in_arrival_window'] for c in cases),
            'median_p99':statistics.median(p99),'p99_min':min(p99),'p99_max':max(p99),
            'loss':sum(c['unsuccessful_or_unexecuted'] for c in cases),
            'offered':sum(c['offered_operations'] for c in cases),
            'slo_passes':sum(c['unsuccessful_or_unexecuted']==0 and c['latency_ms']['p99']<=100 for c in cases)})
    return rows


def table(rows):
    lines = ['| Build / engine | Median successful requests/s | Median run p99, ms | Run p99 range, ms | Unsuccessful / offered | 100 ms, zero-loss passes |',
        '|---|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {LABELS[r['variant']]} | {r['median_rps']:,.2f} | {r['median_p99']:.2f} | {r['p99_min']:.2f} - {r['p99_max']:.2f} | {r['loss']:,} / {r['offered']:,} | {r['slo_passes']} / 3 |")
    return '\n'.join(lines)


def plots(mixed,replay,core):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows = summaries(mixed,'mixed')
    fig,axes = plt.subplots(1,2,figsize=(14,6))
    fig.subplots_adjust(bottom=.26,top=.84,wspace=.3)
    fig.suptitle('Repeated local mixed traffic: three runs per engine',fontsize=16,weight='bold')
    names = [LABELS[r['variant']] for r in rows]
    for axis,field,label in [(axes[0],'median_rps','Median successful requests/s'),
        (axes[1],'median_p99','Median of run p99 (ms, log scale)')]:
        values = [r[field] for r in rows]
        bars = axis.bar(names,values,width=.65,color=['#8395a7','#247765']+['#637b96']*5)
        axis.set_ylabel(label);axis.tick_params(axis='x',rotation=35,labelsize=9)
        axis.spines[['right','top']].set_visible(False)
        if field=='median_p99':axis.set_yscale('log');axis.set_ylim(min(values)*.5,max(values)*2.8)
        else:axis.set_ylim(0,2450);axis.axhline(2000,color='#555',ls='--')
        for bar,value,r in zip(bars,values,rows):
            note=f'{value:,.1f}'
            if field=='median_rps':note+=f"\n{100*r['loss']/r['offered']:.1f}% loss"
            axis.text(bar.get_x()+bar.get_width()/2,value*(1.13 if field=='median_p99' else 1)+(30 if field=='median_rps' else 0),note,ha='center',fontsize=8)
    fig.text(.5,.03,'1M base rows | 64 clients | 2,000 offered requests/s | 15 seconds/run | 5% durable 100-row appends\nBars are run medians; loss aggregates all three runs. Order rotates; fresh fixtures.\nShared Windows desktop, unequal interfaces and SQL coverage.',ha='center',fontsize=9)
    for extension in ['png','svg']:fig.savefig(ROOT/'portfolio'/f'perf-031-mixed.{extension}',dpi=160,bbox_inches='tight')
    plt.close(fig)
    fig,axes = plt.subplots(1,2,figsize=(10,5.5))
    fig.subplots_adjust(bottom=.23,top=.83,wspace=.35)
    fig.suptitle('Focused core improvements: three alternating runs',fontsize=15,weight='bold')
    for axis,probe,label in [(axes[0],'replay','Median exact-retry latency (microseconds, log)'),
        (axes[1],'grouped','Median grouped-query time (ms)')]:
        values = []
        for variant in ['baseline','candidate']:
            if probe=='replay':value=statistics.median(c['latency_ms']['p50'] for c in replay['cases'] if c['variant']==variant)*1000
            else:value=statistics.median(next(q['median_us'] for q in c['queries'] if q['name']=='grouped') for c in core['cases'] if c['variant']==variant)/1000
            values.append(value)
        bars=axis.bar(['0.3.0','0.3.1'],values,color=['#8395a7','#247765'])
        if probe=='replay':axis.set_yscale('log');axis.set_ylim(min(values)*.4,max(values)*4)
        else:axis.set_ylim(0,max(values)*1.3)
        axis.set_ylabel(label);axis.spines[['right','top']].set_visible(False)
        for bar,value in zip(bars,values):axis.text(bar.get_x()+bar.get_width()/2,value*1.12,f'{value:,.3f}',ha='center')
    fig.text(.5,.035,'Retry: 50K persisted IDs, one-row payload, 1,000 replays/run, in-process (no network).\nGrouping: 1M ordered rows, 97 groups, one thread, 3 warmups + 31 repetitions/run.',ha='center',fontsize=9)
    for extension in ['png','svg']:fig.savefig(ROOT/'portfolio'/f'perf-031-core.{extension}',dpi=160,bbox_inches='tight')
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plot',action='store_true');args=parser.parse_args()
    names={'baseline':('perf-031-baseline.json',11),'buffered_trial':('perf-031-candidate.json',11),
        'final':('perf-031-final.json',11),'interleaved':('perf-031-interleaved.json',42),
        'analytics':('perf-031-analytics.json',9)}
    reports={key:read(name) for key,(name,_) in names.items()}
    build=read('rust-checks-031.json');baseline=read('baseline-0.3-provenance.json')
    for key in ['interleaved','analytics']:
        assert reports[key]['binary_sha256']['candidate']==build['bridge_sha256']
        assert reports[key]['binary_sha256']['baseline']==baseline['baseline_binary_sha256']['kestrel-stress.exe']
    assert reports['final']['bridge_sha256']==build['bridge_sha256']
    proof={}
    for key,(_,expected) in names.items():
        fields=('variant','round','profile','clients','offered_rps','scheduled_seconds') if key in ['interleaved','analytics'] else ('engine','profile','clients','offered_rps','scheduled_seconds')
        proof[key]=audit(reports[key],expected,key_fields=fields)
    replay=read('perf-031-replay.json');core=read('perf-031-core.json')
    assert replay['binary_sha256']['candidate']==build['probe_sha256']
    assert core['binary_sha256']['candidate']==build['cli_sha256']
    assert replay['probe_source_sha256']==build['source_sha256']['examples/performance_probe.rs']
    for data in [replay,core]:
        assert len(data['cases'])==6
        for c in data['cases']:
            assert c['version']=={'baseline':'0.3.0','candidate':'0.3.1'}[c['variant']]
    for c in replay['cases']:
        assert c['receipt_count']==50000 and c['repetitions']==1000
        assert c['no_new_publication'] and c['rows_and_sum_match'] and c['full_scrub_passed']
        for key,p in [('p50',.5),('p95',.95),('p99',.99)]:assert raw_percentile(c['raw_latency_ms'],p)==c['latency_ms'][key]
    expected=None
    for c in core['cases']:
        assert c['verified_bytes']==24_000_000 and c['results_equal_across_builds']
        results={q['sql']:q['result']['rows'] for q in c['queries']}
        if expected is None:expected=results
        assert results==expected
        for q in c['queries']:
            assert statistics.median(q['samples_us'])==q['median_us']
            assert raw_percentile(q['samples_us'],.95)==q['p95_us']
    proof['replay_probe']={'cases':6,'samples_checked':6000,'one_row_payload':True,'no_new_publication':True}
    proof['core_probe']={'cases':6,'sql_cases':36,'samples_checked':1116,'all_results_equal':True}
    rejected=read('perf-031-replay-invalid-build.json');assert rejected['valid_for_comparison'] is False
    proof['invalid_build_comparison']={'excluded':True,'retained_cases':len(rejected['cases']),'reason':rejected['rejection_reason']}
    for key in ['interleaved','analytics']:
        for c in reports[key]['cases']:
            assert c['host_telemetry']['error'] is None and len(c['host_telemetry']['samples'])>=3
            assert all(0<=s.get('host_cpu_busy_percent',0)<=100 and s['physical_available_bytes']<=s['physical_total_bytes'] for s in c['host_telemetry']['samples'])
    for key in ['buffered_trial','final','interleaved','analytics']:
        for c in reports[key]['cases']:
            if c['version']!='0.3.1':continue
            after=c['live_state_before_reopen']['publication_profile'];before=c['publication_profile_before_load']
            assert after['attempts']==after['completed']
            for stage in ['prepare','segment_write','segment_sync','catalog_encode','catalog_write','catalog_sync','catalog_rename']:
                a,b=after[stage],before[stage]
                assert sum(a['histogram'])==a['count']==after['attempts']
                assert a['count']>=b['count'] and a['total_ms']>=b['total_ms']
    (ROOT/'benchmarks'/'perf-031-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    mixed=reports['interleaved'];analytics=reports['analytics']
    mixed_summary = {r['variant']:r for r in summaries(mixed,'mixed')}
    candidate_mixed = mixed_summary['candidate']; baseline_mixed = mixed_summary['baseline']
    replay_lines=['| Build | Median of run medians, microseconds | Run p99 range, microseconds |','|---|---:|---:|']
    for variant in ['baseline','candidate']:
        cases=[c for c in replay['cases'] if c['variant']==variant]
        replay_lines.append(f"| {LABELS[variant]} | {statistics.median(c['latency_ms']['p50'] for c in cases)*1000:.3f} | {min(c['latency_ms']['p99'] for c in cases)*1000:.3f} - {max(c['latency_ms']['p99'] for c in cases)*1000:.3f} |")
    core_lines=['| Query | 0.3.0 median of run medians, ms | 0.3.1 median of run medians, ms |','|---|---:|---:|']
    for name in [q['name'] for q in core['cases'][0]['queries']]:
        values=[statistics.median(next(q['median_us'] for q in c['queries'] if q['name']==name) for c in core['cases'] if c['variant']==variant)/1000 for variant in ['baseline','candidate']]
        core_lines.append(f'| {name} | {values[0]:.4f} | {values[1]:.4f} |')
    full_lines=['| Profile | Clients | Offered/s | Seconds | Success/s | p99 success, ms | Unsuccessful |','|---|---:|---:|---:|---:|---:|---:|']
    for c in reports['final']['cases']:
        full_lines.append(f"| {c['profile']} | {c['clients']} | {c['offered_rps']} | {c['scheduled_seconds']} | {c['successful_rps_in_arrival_window']:.2f} | {c['latency_ms']['p99']:.2f} | {c['unsuccessful_or_unexecuted']} |")
    compactions=['| Stage / single-client mixed case | Compactions | Total compaction time, ms | Average per compaction, ms | Run p99, ms |','|---|---:|---:|---:|---:|']
    for label,key in [('0.3.0 fresh baseline','baseline'),('0.3.1 buffered trial','buffered_trial'),('0.3.1 retained compaction handles','final')]:
        c=next(c for c in reports[key]['cases'] if c['profile']=='mixed' and c['clients']==1)
        stats=c['live_state_before_reopen']['ingest'];n=stats['compactions'];total=stats['compaction_total_ms']
        compactions.append(f"| {label} | {n} | {total:.2f} | {total/max(1,n):.2f} | {c['latency_ms']['p99']:.2f} |")
    recovery=read('perf-031-recovery.json')
    pipeline=json.loads((ROOT/'portfolio'/'live-pipeline-031-results.json').read_text(encoding='utf-8'))
    recheck=read('release-recheck-031.json');compatibility=read('format-031.json');capability=read('capability-031.json')
    assert pipeline['exact_sql_cases_against_duckdb']==42 and pipeline['replayed_sources_not_duplicated']
    assert recheck['all_retained_results_match'] and recheck['binary_sha256']==build['cli_sha256']
    assert compatibility['legacy_catalog_read'] and compatibility['older_binary_rejects_new_catalog']
    assert len(capability['engines'])==6 and capability['engines'][0]['version']=='0.3.1'
    offered=sum(p['offered_operations'] for key,p in proof.items() if key in names)
    executed=sum(p['raw_executed_samples_checked'] for key,p in proof.items() if key in names)
    text='\n'.join(['# KestrelSQL 0.3.1: measured improvements and repeated comparisons','',
        'This performance release removes full-ledger copying from exact retries, reuses retained segment handles during compaction, buffers small publication writes, avoids an extra GROUP BY hash lookup, and adds publication-stage diagnostics. It preserves the 0.3 catalog/segment format and durable acknowledgment contract. It remains an experimental embedded BIGINT aggregate store.','',
        f"The repeated 2,000/s mixed comparison changed median run p99 from {baseline_mixed['median_p99']:.2f} to {candidate_mixed['median_p99']:.2f} ms. The candidate completed all offers in {candidate_mixed['slo_passes']}/3 runs with p99 below 100 ms. The standalone 10,000/s case still lost 25,367 offers; single-client mixed p99 remained 147.72 ms. The direct unordered-filter probe also regressed. These boundaries remain visible alongside improvements.",'',
        '## Repeated mixed traffic: six database engines, two Kestrel builds','',
        'Three runs per build/engine, each with a fresh 1M-row fixture, 64 clients, 2,000 offered requests/s for 15 seconds, 95% range reads and 5% durable 100-row appends. Five percent of appended timestamps are late. Engine order rotates by two positions per round. Medians and ranges below describe separate run statistics; they are not pooled percentiles or confidence intervals. Loss counts include errors, expiry and unexecuted offers.','',table(summaries(mixed,'mixed')),'',
        '![Repeated mixed traffic](portfolio/perf-031-mixed.png)','',
        '## Generic scans','',
        'Three eight-second cases per variant at 200 offered requests/s. The common scan profile includes full grouping, unordered filters, range reads and 10% durable appends. All results are retained, including saturation of less suitable engines.','',table(summaries(mixed,'scan')),'',
        '## Broad windows at 10M rows','',
        'Three 15-second cases per build/engine, 64 clients, 2,000 offered requests/s. Random windows cover 25-50% of the base rows, with 5% durable append batches. Kestrel maintains exact aggregate checkpoints; DuckDB uses normal raw aggregate execution and zonemaps. Maintenance, storage and interfaces differ; this is not an equivalent-materialized-view comparison.','',table(summaries(analytics,'analytics')),'',
        '## Exact retries with a large receipt ledger','',
        'Three alternating release-build runs per version: 50,000 persisted IDs, 1,000 exact one-row replays per run. Timings include caller allocation, payload hashing, lookup and validation within the Rust process. Setup, network, source reading and final scrub are excluded. Every run checks original generation, unchanged disk size, exact count/sum and every payload checksum. These numbers do not describe network request throughput.','', '\n'.join(replay_lines),'',
        '## Direct query costs','',
        'Three alternating runs per version, 1M ordered rows, one execution thread, three warmups and 31 repetitions per fixed query. Every result matches across builds and every archive passes a full scrub. Repeated fixed-query timings characterize this fixture; randomized/concurrent traffic is tested separately above.','', '\n'.join(core_lines),'',
        'Grouping improved from 89.01 to 67.77 ms by median of run medians. The unordered-filter probe regressed from 16.69 to 20.80 ms. The filter operator did not change directly; these observations do not isolate code generation or host variation as a cause. Further profiling must address the regression before claiming a generic scan improvement.','',
        '![Focused core probes](portfolio/perf-031-core.png)','',
        '## Why the next change targeted compaction','',
        'The buffered-write trial exposed five compactions with preparation stages over 100 ms in the single-client mixed case; ordinary append preparation stayed under 0.1 ms. The preparation stage includes compaction input reads and sorting. The final change reuses each immutable input segment handle for checked positional reads, eliminating path reopen work per compaction input. Long concurrent query scans still use independent handles. The table is an observation across separate runs, not an isolated causal estimate.','', '\n'.join(compactions),'',
        'Publication diagnostics split preparation, segment writing, segment synchronization, catalog encoding, catalog writing, catalog synchronization and rename. Inclusive histogram boundaries are 0.1, 1, 5, 20, 100, 500 and 1,000 ms, followed by an unbounded bucket. Counts/totals/histograms are differenced against pre-load state; lifetime maxima include fixture setup. Diagnostics are process-local and shared across snapshots, not durable data at the snapshot generation. Failed I/O attempts can have unexecuted stages represented by zero duration.','',
        '## Complete final local sweep','', '\n'.join(full_lines),'',
        'A request means one query or an entire 100-row append. Latency starts at scheduled arrival and includes dispatch, client queue and service. p99 includes successful requests only, including drain completions. Throughput counts successes completed during the arrival window. The client queue has 256 slots, two-second expiry and eight-second connection/statement deadlines.','',
        '## Verification and reproducibility','',
        f'- 31 Rust tests passed in debug and release; formatting and Clippy with warnings as errors passed. The new capacity test commits 100,000 IDs, rejects an additional ID, reopens, replays old IDs and checks exact data and full checksums.',
        f'- {len(recovery["cycles"])} forced process-kill cycles passed acknowledged-write recovery, atomicity, full scrub and identified replay checks. Process death is not a power-loss qualification.',
        '- The Parquet replay/backfill demonstration passed 42 exact DuckDB SQL checks; both sources replayed without new rows and changed content was rejected. An untimed recheck matched 153 retained scale/real-data results, including 100M ordered and late-data archives. The 64-column import boundary, partial-row rejection, legacy catalog read and old-binary downgrade rejection also passed.',
        f'- The audit checked {executed:,} raw executed samples from {sum(expected for _,expected in names.values())} new stress cases and {offered:,} offered requests, plus 6,000 replay timings and 1,116 direct query timings. All acknowledged batches and independent NumPy windows reconciled.',
        '- A shared-target Cargo output collision produced an invalid probe comparison. Both executables reported 0.3.0; all six cases are retained and explicitly excluded. The replacement candidate probe was built in an isolated target directory, and both probe/bridge harnesses now reject unexpected versions.',
        '- Whole-host CPU and physical-memory observations use the documented Windows GetSystemTimes and GlobalMemoryStatusEx APIs at 1 Hz. Samples are restricted to each timed arrival window. They do not attribute stalls to a process or measure storage latency. No compilation or second timed load overlapped these comparisons.','',
        '```powershell',
        'cargo build --release --locked --bins',
        'cargo test --release --locked',
        'cargo build --release --locked --example performance_probe --target-dir target/probe-031',
        'python benchmarks/replay_compare.py --baseline bin/baseline-0.3/performance-probe.exe --candidate target/probe-031/release/examples/performance_probe.exe',
        'python benchmarks/core_scan_compare.py --baseline bin/baseline-0.3/kestrel.exe --candidate bin/kestrel.exe',
        'python benchmarks/portable_servers.py start',
        'python benchmarks/interleaved_compare.py --baseline bin/baseline-0.3/kestrel-stress.exe --candidate bin/kestrel-stress.exe --scans',
        'python benchmarks/interleaved_compare.py --baseline bin/baseline-0.3/kestrel-stress.exe --candidate bin/kestrel-stress.exe --variants baseline,candidate,duckdb --analytics --rows 10000000 --output benchmarks/perf-031-analytics.json',
        'python benchmarks/portable_servers.py stop',
        'python benchmarks/report_031.py --plot','```','',
        'Install the pinned benchmark drivers and plot dependencies before using the Python tools. Baseline binaries and the identical probe source are included; the baseline library source is preserved under benchmarks/baseline-0.3-source. Build that historical crate into a separate target directory to avoid output collisions. Reference package versions, hashes and settings remain in [reference-packages.json](benchmarks/reference-packages.json).','',
        'Reports: [full baseline](benchmarks/perf-031-baseline.json), [buffered trial](benchmarks/perf-031-candidate.json), [final sweep](benchmarks/perf-031-final.json), [repeated six-engine runs](benchmarks/perf-031-interleaved.json), [10M windows](benchmarks/perf-031-analytics.json), [retry probe](benchmarks/perf-031-replay.json), [direct queries](benchmarks/perf-031-core.json), [invalid build comparison](benchmarks/perf-031-replay-invalid-build.json), [audit](benchmarks/perf-031-audit.json), [Rust/build proof](benchmarks/rust-checks-031.json), [crash tests](benchmarks/perf-031-recovery.json), [Parquet workflow](portfolio/live-pipeline-031-results.json), [retained-data recheck](benchmarks/release-recheck-031.json), [format checks](benchmarks/format-031.json), [SQL capability probes](benchmarks/capability-031.json). Raw sample paths, individual rounds, diagnostics and host observations are in their respective JSON reports. Historical [0.3 evidence](V03_RESULTS.md) and [0.2 evidence](HARD_TESTS.md) remain unchanged.','',
        '## Remaining limits','',
        'A shared Windows desktop, warm caches, client/interface differences and three short repetitions do not establish production service or universal superiority. The receipt-capacity test verifies correctness at 100,000 IDs; unique-ID catalog rewrite cost and long ledger endurance remain unqualified. Durable writes still synchronize segment and catalog files before acknowledgment. File-system failures poison the writer and require reopen/reconciliation.','',
        'Archive still lacks raw row retrieval, joins, strings, nullable types, updates/deletes, SQL transactions, production authentication, complete backups/retention/orphan cleanup, Linux qualification and replication. ClickHouse, SQL Server, Oracle and distributed workloads were not executed. Performance targets and every failed offer remain visible above.',''])
    (ROOT/'PERFORMANCE_031.md').write_text(text,encoding='utf-8')
    if args.plot:plots(mixed,replay,core)
    print(json.dumps({'audit':proof,'offered_requests':offered},indent=2))


if __name__=='__main__':main()
