"""Audit 0.3.2 evidence; regenerate prose/plots without rerunning timed loads."""
import argparse
import json
import math
import statistics
from pathlib import Path

from report_v03 import audit
from report_031 import summaries

ROOT=Path(__file__).resolve().parents[1]
LABELS={'baseline':'Kestrel 0.3.1','candidate':'Kestrel 0.3.2','duckdb':'DuckDB'}


def read(name):return json.loads((ROOT/'benchmarks'/name).read_text(encoding='utf-8-sig'))


def median_query(core,variant,name):
    return statistics.median(next(q['median_us'] for q in c['queries'] if q['name']==name)/1000
        for c in core['cases'] if c['variant']==variant)


def table(report,profile):
    lines=['| Build/engine | Median success/s | Median run p99, ms | Run p99 range, ms | Failed/unexecuted offers | 100 ms zero-loss passes |',
        '|---|---:|---:|---:|---:|---:|']
    for r in summaries(report,profile):
        lines.append(f"| {LABELS[r['variant']]} | {r['median_rps']:.2f} | {r['median_p99']:.2f} | {r['p99_min']:.2f} - {r['p99_max']:.2f} | {r['loss']} / {r['offered']} | {r['slo_passes']} / 3 |")
    return '\n'.join(lines)


def plot(core):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,5.2))
    fig.subplots_adjust(bottom=.24,top=.82,wspace=.3)
    fig.suptitle('Kestrel 0.3.2: alternating core query comparisons',fontsize=15,weight='bold')
    for axis,name,title in zip(axes,['unordered_filter','grouped'],['Unordered filter','Grouping']):
        values=[median_query(core,v,name) for v in ['baseline','candidate']]
        bars=axis.bar(['0.3.1','0.3.2'],values,color=['#8395a7','#247765'],width=.6)
        axis.set_title(title);axis.set_ylabel('Median of run medians (ms)');axis.set_ylim(0,max(values)*1.25)
        axis.spines[['right','top']].set_visible(False)
        for bar,value in zip(bars,values):
            axis.text(bar.get_x()+bar.get_width()/2,value+max(values)*.03,f'{value:.3f}',ha='center')
    fig.text(.5,.04,'1M ordered base rows | one thread | 3 alternating runs/version | 3 warmups + 31 samples/query/run\nOriginal 0.3.1 release binary; ordinary uninstrumented query calls. Shared Windows desktop.',ha='center',fontsize=9)
    for extension in ['png','svg']:fig.savefig(ROOT/'portfolio'/f'perf-032-core.{extension}',dpi=160,bbox_inches='tight')
    plt.close(fig)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plot',action='store_true');args=parser.parse_args()
    build=read('rust-checks-032.json');base=read('baseline-0.3.1-provenance.json')
    final=read('perf-032-final.json');mixed=read('perf-032-interleaved.json');analytics=read('perf-032-analytics.json')
    core=read('perf-032-core.json');profiles=read('perf-032-profile.json')
    proof={'final':audit(final,11),'interleaved':audit(mixed,18,key_fields=('variant','round','profile','clients','offered_rps','scheduled_seconds')),
        'analytics':audit(analytics,6,key_fields=('variant','round','profile','clients','offered_rps','scheduled_seconds'))}
    assert final['bridge_sha256']==build['bridge_sha256']
    for report in [mixed,analytics]:
        assert report['binary_sha256']['candidate']==build['bridge_sha256']
        assert report['binary_sha256']['baseline']==base['baseline_binary_sha256']['kestrel-stress.exe']
        for case in report['cases']:
            telemetry=case['host_telemetry']
            assert telemetry['error'] is None and len(telemetry['samples'])>=3
    assert core['binary_sha256']['candidate']==build['cli_sha256']
    assert core['binary_sha256']['baseline']==base['baseline_binary_sha256']['kestrel.exe']
    expected=None
    for case in core['cases']:
        assert case['version']=={'baseline':'0.3.1','candidate':'0.3.2'}[case['variant']]
        assert case['verified_bytes']==24_000_000
        rows={q['sql']:q['result']['rows'] for q in case['queries']}
        if expected is None:expected=rows
        assert rows==expected
        for query in case['queries']:
            assert len(query['samples_us'])==31
            assert statistics.median(query['samples_us'])==query['median_us']
            assert sorted(query['samples_us'])[math.ceil(31*.95)-1]==query['p95_us']
    assert len(core['cases'])==6
    assert profiles['binary_sha256']['candidate']==build['scan_probe_sha256']
    assert profiles['binary_sha256']['baseline']==base['profiled_baseline']['binary_sha256']
    assert profiles['probe_source_sha256']==build['source_sha256']['examples/scan_profile.rs']
    assert profiles['probe_source_sha256']==base['profiled_baseline']['source_sha256']['examples/scan_profile.rs']
    expected=None
    for case in profiles['cases']:
        assert case['verified_bytes']==24_000_000 and case['results_equal_across_builds']
        rows={q['sql']:q['result']['rows'] for q in case['cases']}
        if expected is None:expected=rows
        assert rows==expected
        for query in case['cases']:
            assert len(query['samples'])==11
            for sample in query['samples']:
                p=sample['profile']
                assert 0<=p['matched_rows']<=p['candidate_rows']<=1_000_000
                assert sum(p[k] for k in ['page_read_ms','selection_ms','aggregate_ms'])<=sample['elapsed_ms']+.01
    assert len(profiles['cases'])==6
    proof['core']={'cases':6,'sql_cases':36,'timings_checked':1116,'all_results_equal':True}
    proof['profiling']={'cases':6,'sql_cases':30,'timings_checked':330,'full_scrubs_passed':True,
        'instrumented_baseline_separate_from_original_release':True,
        'initial_setup_failures_excluded':'cold/warm byte-count invariant fixed before accepted runs; harness flattened-JSON key corrected before accepted comparisons'}
    offered=sum(proof[k]['offered_operations'] for k in ['final','interleaved','analytics'])
    assert offered==620000
    recovery=read('perf-032-recovery.json');recheck=read('release-recheck-032.json');compat=read('format-032.json')
    demo=json.loads((ROOT/'portfolio'/'live-pipeline-032-results.json').read_text(encoding='utf-8'))
    assert len(recovery['cycles'])==24 and all(c['retry_deduplication_passed'] and c['sum_and_full_scrub_passed'] for c in recovery['cycles'])
    assert recheck['all_retained_results_match'] and recheck['binary_sha256']==build['cli_sha256']
    assert demo['exact_sql_cases_against_duckdb']==42 and demo['replayed_sources_not_duplicated']
    assert compat['legacy_catalog_read'] and compat['older_binary_rejects_new_catalog']
    differential=read('archive-verification-032.json')
    assert differential['binary_sha256']==build['cli_sha256'] and differential['queries_checked_against_each_reference']==500
    assert all(q['passed'] for q in differential['queries'])
    (ROOT/'benchmarks'/'perf-032-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    operators=['| Query | 0.3.1 median of run medians, ms | 0.3.2 median of run medians, ms |','|---|---:|---:|']
    for name in [q['name'] for q in core['cases'][0]['queries']]:
        operators.append(f"| {name} | {median_query(core,'baseline',name):.4f} | {median_query(core,'candidate',name):.4f} |")
    stages=['| Instrumented query | Build | Page read/decode, ms | Selection, ms | Aggregate/row loop, ms | Total, ms |','|---|---|---:|---:|---:|---:|']
    for name in [q['name'] for q in profiles['cases'][0]['cases']]:
        for variant in ['baseline','candidate']:
            values=[]
            for key in ['page_read_ms','selection_ms','aggregate_ms','elapsed_ms']:
                values.append(statistics.median(statistics.median(s[key] if key=='elapsed_ms' else s['profile'][key] for s in q['samples'])
                    for case in profiles['cases'] if case['variant']==variant for q in case['cases'] if q['name']==name))
            stages.append(f"| {name} | {LABELS[variant]} | "+' | '.join(f'{v:.3f}' for v in values)+' |')
    sweep=['| Profile | Clients | Offers/s | Seconds | Success/s | p99, ms | Failed/unexecuted |','|---|---:|---:|---:|---:|---:|---:|']
    for c in final['cases']:
        sweep.append(f"| {c['profile']} | {c['clients']} | {c['offered_rps']} | {c['scheduled_seconds']} | {c['successful_rps_in_arrival_window']:.2f} | {c['latency_ms']['p99']:.2f} | {c['unsuccessful_or_unexecuted']} |")
    bad=next(c for c in final['cases'] if c['profile']=='mixed' and c['clients']==64 and c['offered_rps']==500 and c['scheduled_seconds']==8)
    a=bad['live_state_before_reopen']['publication_profile']['catalog_rename'];b=bad['publication_profile_before_load']['catalog_rename']
    text='\n'.join(['# KestrelSQL 0.3.2: faster filtered scans, unresolved service stalls','',
        f"The fresh alternating core comparison reduced unordered-filter median time from {median_query(core,'baseline','unordered_filter'):.2f} to {median_query(core,'candidate','unordered_filter'):.2f} ms. This verifies a focused query improvement. The live sweep also found {bad['unsuccessful_or_unexecuted']} failed/unexecuted offers at 500/s and {bad['latency_ms']['p99']:.2f} ms p99, so this release does not establish an improved production service envelope.",'',
        '## What changed','',
        'A query-local byte buffer and decoded column vectors are reused across streamed pages. Reusable row selections apply each residual predicate with its operator chosen outside the row loop. Sorted bounds already enforce their comparisons. Ungrouped COUNT/SUM/AVG/MIN/MAX kernels dispatch once per expression per page, with exact i128 sums and the existing empty-input semantics. Grouping retains its bounded hash-table path. CRC checks, independent long-scan handles, immutable snapshots and durable publication remain in place. No disk-format change was made.','',
        'The new opt-in `snapshot.query_profiled(sql)` returns `(ArchiveResult, ScanProfile)`. It counts scanned candidates/matches and times page read/CRC/decode, selection and aggregation. Ordinary `query` uses a const-generic specialization without per-block timing/counter work. The profile excludes index/planning/result formatting and is query-local; it is not a production tracing service.','',
        '## Direct query comparison','',
        'Three alternating runs per original 0.3.1 release CLI and final 0.3.2 CLI. Each creates a fresh deterministic 1M-row archive, uses one thread, three warmups and 31 repetitions/query. Every query result matches across versions and every archive passes a full scrub. These are medians of separate run medians, not pooled percentiles.','',
        '\n'.join(operators),'','![Core comparison](portfolio/perf-032-core.png)','',
        'The fresh 0.3.1 baseline differs substantially from earlier shared-desktop measurements. Compare paired builds within this run; substituting earlier absolute timings would overstate the gain.','',
        '## Diagnostic profiles','',
        '\n'.join(stages),'',
        'The profiling baseline is a separately preserved 0.3.1 source with timing instrumentation added, rather than the original release binary. Its row-loop stage combines predicate selection and aggregation; 0.3.2 separates those stages. Instrumentation and its counter placement can perturb timings, so this table diagnoses work and does not replace the uninstrumented comparison above. Baseline source and both profiling binaries are included. Each instrumented query has eleven samples after three warmups; all results and full scrubs pass.','',
        'The initial profiler compared cold-query bytes with warm-cache bytes and rejected that invalid invariant. It was corrected to compare the same warm state. The first comparison harness also assumed a nested result object rather than the existing flattened JSON shape. Both issues were fixed before the accepted six-case comparison; neither failed setup contributes a performance claim.','',
        '## Repeated local service cases','',
        'Three 15-second mixed runs per build/engine: 1M base rows, 64 clients, 2,000 offered requests/s, 95% range reads and 5% durable 100-row appends. Three eight-second scan runs at 200/s include grouping, unordered predicates and 10% appends. Variant order rotates, fixtures are fresh, and whole-host observations are retained. This focused release compares two Kestrel builds with DuckDB; the earlier [six-engine matrix](PERFORMANCE_031.md) remains historical evidence rather than a new five-competitor result.','',
        table(mixed,'mixed'),'',table(mixed,'scan'),'','## 10M broad-window regression checks','',
        'Three 15-second runs/build at 2,000/s, 64 clients, windows covering 25–50% of base rows, with 5% durable appends. This checks the aggregate-index path alongside the scan change.','',table(analytics,'analytics'),'','## Complete candidate sweep and observed stall','',
        '\n'.join(sweep),'',
        f"In the failed 500/s, 64-client case, catalog-rename maximum rose from {b['max_ms']:.2f} ms before load to {a['max_ms']:.2f} ms, with {a['total_ms']-b['total_ms']:.2f} ms spent in that stage during load. Preparation, writing and synchronization counters remain in the raw report. Long publication stalls can occupy write clients and overflow/expire the shared load-generator queue. This observation does not identify the external filesystem/storage cause or prove a code regression. Both old-build and candidate failures are retained in the paired tables. Physical power loss and a stable service envelope remain unqualified.",'',
        'Latency starts at scheduled arrival, includes dispatch/queue/service, and reports successes including drain. Throughput counts successes within the arrival window. Errors, queue drops and expired/unexecuted offers remain separate. One request is a query or a complete 100-row append. The queue has 256 slots, two-second expiry and eight-second connection/statement deadlines. No compilation or second heavy job overlapped timed loads.','',
        '## Correctness and reproducibility','',
        '- 32 Rust tests passed in debug and release, with formatting and Clippy warnings-as-errors. The new oracle test covers signed extremes, partial pages, empty selections, multiple filters, grouping and profile candidate/match counts; existing concurrent and corruption tests still pass.',
        '- 24 new forced process-kill/retry cycles passed atomic published batches, every acknowledged batch, exact sums and full scrubs. Process death is not physical power loss.',
        '- The Parquet replay/backfill demo passed 42 exact DuckDB checks. All 153 retained scale/real-data checks matched, including 100M ordered/late archives; wide imports, partial-row rejection and legacy/downgrade format checks passed.',
        '- A fresh seeded differential suite passed 500 queries against each of DuckDB and SQLite over eight overlapping late-data segments, covering grouped/empty aggregates and all six comparison operators.',
        f'- Raw accounting/percentiles, acknowledged writes and 700 independent NumPy windows passed across 35 new stress cases and {offered:,} offers, plus 1,116 direct query and 330 diagnostic timings.','',
        '```powershell','cargo test --release --locked','cargo build --release --locked --bins --example scan_profile',
        'python benchmarks/core_scan_compare.py --baseline bin/baseline-0.3.1/kestrel.exe --candidate bin/kestrel.exe --baseline-version 0.3.1 --candidate-version 0.3.2 --output benchmarks/perf-032-core.json',
        'python benchmarks/profile_scan_compare.py --baseline bin/baseline-0.3.1/scan-profile.exe --candidate bin/scan-profile.exe',
        'python benchmarks/interleaved_compare.py --baseline bin/baseline-0.3.1/kestrel-stress.exe --candidate bin/kestrel-stress.exe --baseline-version 0.3.1 --candidate-version 0.3.2 --variants baseline,candidate,duckdb --scans --output benchmarks/perf-032-interleaved.json',
        'python benchmarks/report_032.py --plot','```','',
        'Install the pinned drivers/plot dependencies first. Historical release sources are in benchmarks/baseline-0.3.1-source; instrumented baseline sources are in benchmarks/profile-baseline-031-source. Build each crate into its own target directory. Source/binary hashes bind the comparisons to [build proof](benchmarks/rust-checks-032.json) and [baseline provenance](benchmarks/baseline-0.3.1-provenance.json).','',
        'Evidence: [direct queries](benchmarks/perf-032-core.json), [diagnostics](benchmarks/perf-032-profile.json), [full sweep](benchmarks/perf-032-final.json), [repeated mixed/scans](benchmarks/perf-032-interleaved.json), [10M windows](benchmarks/perf-032-analytics.json), [audit](benchmarks/perf-032-audit.json), [crash checks](benchmarks/perf-032-recovery.json), [pipeline](portfolio/live-pipeline-032-results.json), [retained-data checks](benchmarks/release-recheck-032.json), [format checks](benchmarks/format-032.json), [current capability probes](benchmarks/capability-032.json).','',
        'Archive remains a restricted BIGINT aggregate engine. Broad SQL/types, Arrow integration, backups/retention/orphan cleanup, long receipt-ledger endurance, complete resource governance, Linux execution, power-loss behavior and replication remain work. The loopback adapter is unauthenticated and test-only. This prototype has not demonstrated Facebook-scale database activity or universal database superiority.',''])
    (ROOT/'PERFORMANCE_032.md').write_text(text,encoding='utf-8')
    if args.plot:plot(core)
    print(json.dumps({'stress_cases':35,'offered_requests':offered,'audit':'benchmarks/perf-032-audit.json'},indent=2))


if __name__=='__main__':main()
