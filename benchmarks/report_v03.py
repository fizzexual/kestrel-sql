"""Audit retained 0.3 samples and produce the report; never rerun timings.
Use --plot for static charts after installing plot-requirements.txt.
"""
import argparse
import gzip
import json
from pathlib import Path

from stress_compare import percentile

ROOT = Path(__file__).resolve().parents[1]
NAMES = {'kestrel':'KestrelSQL 0.3', 'postgres':'PostgreSQL', 'mysql':'MySQL',
         'mariadb':'MariaDB', 'sqlite':'SQLite', 'duckdb':'DuckDB'}


def read(name):
    return json.loads((ROOT/'benchmarks'/name).read_text(encoding='utf-8'))


def audit(report, expected, key_fields=('engine','profile','clients','offered_rps','scheduled_seconds')):
    cases = report['cases']
    keys = [tuple(c[field] for field in key_fields) for c in cases]
    assert len(keys)==len(set(keys))==expected
    checked=0
    for c in cases:
        path=(ROOT/'benchmarks'/c['raw_samples_file']).resolve()
        assert path.is_relative_to((ROOT/'benchmarks').resolve())
        with gzip.open(path,'rt',encoding='utf-8') as file:
            samples=[json.loads(line) for line in file]
        sequences={s['sequence'] for s in samples};expired=set(c['expired_sequences'])
        assert len(sequences)==len(samples) and len(expired)==c['queue_expired']
        assert not sequences.intersection(expired)
        assert all(0<=n<c['offered_operations'] for n in sequences|expired)
        good=[s for s in samples if s['ok']]
        errors=len(samples)-len(good)
        assert len(good)==c['successful_operations']
        assert errors==sum(e['sequence'] is not None for e in c['errors'])
        assert len(samples)+c['queue_dropped']+c['queue_expired']==c['offered_operations']
        assert errors+c['queue_dropped']+c['queue_expired']==c['unsuccessful_or_unexecuted']
        assert sum(s['operation']=='append' for s in good)==c['write_successes']
        for key,p in [('p50',.5),('p95',.95),('p99',.99)]:
            assert percentile([s['latency_ms'] for s in good],p)==c['latency_ms'][key]
        assert sum(s['latency_ms']<=100 for s in good)/c['offered_operations']==c['offered_fraction_successful_within_100ms']
        r=c['reconciliation']
        assert r['all_acknowledged_batches_present'] and r['batch_atomicity_and_sums']
        assert r['acknowledged_batches']==c['write_successes'] and r['numpy_reference_windows']==20
        if c['engine']=='kestrel':
            assert r['full_kestrel_scrub']['verified_bytes']==r['rows']*24
            assert c['live_state_before_reopen']['ingest']['maintenance_errors']==0
            assert c['live_state_before_reopen']['retained_page_cache_bytes']<=32*1024*1024
        checked+=len(samples)
    assert all(f.get('resolved_by_later_successful_case') for f in report['failed_cases'])
    return {'completed_cases':len(cases),'engines':len({c['engine'] for c in cases}),
        'offered_operations':sum(c['offered_operations'] for c in cases),
        'successful_operations':sum(c['successful_operations'] for c in cases),
        'unsuccessful_or_unexecuted':sum(c['unsuccessful_or_unexecuted'] for c in cases),
        'raw_executed_samples_checked':checked,'numpy_reference_windows':20*len(cases),
        'all_acknowledged_batches_present':True,'batch_atomicity_and_sums':True,
        'sample_accounting_and_percentiles':True,'no_kestrel_maintenance_errors':True}


def selected(report, rate, seconds):
    return [next(c for c in report['cases'] if c['engine']==name and c['profile']=='mixed'
        and c['clients']==64 and c['offered_rps']==rate and c['scheduled_seconds']==seconds) for name in NAMES]


def table(cases):
    lines=['| Engine / case | Successful requests/s in arrival window | p99 success latency, ms | Failed / unexecuted | ACK batches |',
           '|---|---:|---:|---:|---:|']
    for c in cases:
        loss=c['unsuccessful_or_unexecuted']/c['offered_operations']*100
        lines.append(f"| {NAMES[c['engine']]} | {c['successful_rps_in_arrival_window']:,.2f} | {c['latency_ms']['p99']:,.2f} | {c['unsuccessful_or_unexecuted']:,} ({loss:.2f}%) | {c['write_successes']:,} |")
    return '\n'.join(lines)


def draw(report, analytics):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cases=selected(report,2000,8)
    names=['Kestrel','Postgres','MySQL','MariaDB','SQLite','DuckDB']
    fig,axes=plt.subplots(1,2,figsize=(12,6.1))
    fig.subplots_adjust(left=.08,right=.98,top=.83,bottom=.23,wspace=.3)
    fig.suptitle('Kestrel 0.3: fresh local mixed-load comparison',fontsize=16,weight='bold')
    for axis,values,ylabel in [(axes[0],[c['successful_rps_in_arrival_window'] for c in cases],'Successful requests/s in arrival window'),
        (axes[1],[c['latency_ms']['p99'] for c in cases],'p99 successful latency (ms, log scale)')]:
        bars=axis.bar(names,values,color=['#2a786b']+['#637b96']*5)
        if axis is axes[1]:
            axis.set_yscale('log');axis.set_ylim(max(.1,min(values)/2),max(values)*3)
        else:
            axis.axhline(2000,ls='--',color='#444',lw=1);axis.set_ylim(0,2350)
        for bar,value,c in zip(bars,values,cases):
            label=f'{value:,.1f}'
            if axis is axes[0]:label+=f"\n{c['unsuccessful_or_unexecuted']/c['offered_operations']*100:.1f}% loss"
            axis.text(bar.get_x()+bar.get_width()/2,value*(1.15 if axis is axes[1] else 1)+ (35 if axis is axes[0] else 0),label,ha='center',fontsize=9)
        axis.set_ylabel(ylabel);axis.tick_params(axis='x',rotation=25)
        axis.spines[['top','right']].set_visible(False)
    fig.text(.5,.03,'1M initial rows | 64 clients | 2,000 offered requests/s | 95% reads / 5% durable 100-row appends\n8 seconds | shared Windows desktop | dropped work shown explicitly | not a universal ranking',ha='center',fontsize=9)
    for ext in ['png','svg']:fig.savefig(ROOT/'portfolio'/f'v03-stress.{ext}',dpi=160,bbox_inches='tight')
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,5.5))
    fig.subplots_adjust(left=.09,right=.98,top=.83,bottom=.24,wspace=.35)
    cases=[c for c in analytics['cases'] if c['offered_rps']==2000]
    names=[NAMES[c['engine']] for c in cases]
    fig.suptitle('10M rows: broad time-window reads during ingestion',fontsize=15,weight='bold')
    for axis,values,ylabel in [(axes[0],[c['successful_rps_in_arrival_window'] for c in cases],'Successful requests/s'),
        (axes[1],[c['latency_ms']['p99'] for c in cases],'p99 successful latency (ms)')]:
        bars=axis.bar(names,values,color=['#2a786b','#637b96'])
        axis.set_ylim(0,max(values)*1.3)
        for bar,value,c in zip(bars,values,cases):
            label=f'{value:,.1f}'
            if axis is axes[0]:label+=f"\n{c['unsuccessful_or_unexecuted']/c['offered_operations']*100:.1f}% loss"
            axis.text(bar.get_x()+bar.get_width()/2,value+max(values)*.035,label,ha='center',fontsize=10)
        axis.set_ylabel(ylabel);axis.spines[['top','right']].set_visible(False)
    fig.text(.5,.03,'64 clients | 2,000 offered requests/s | windows cover 25-50% of base rows | 5% durable append batches\nKestrel maintains aggregate checkpoints; DuckDB uses zonemaps/raw aggregates. Interfaces differ.',ha='center',fontsize=9)
    for ext in ['png','svg']:fig.savefig(ROOT/'portfolio'/f'v03-analytics.{ext}',dpi=160,bbox_inches='tight')
    plt.close(fig)
    (ROOT/'portfolio'/'v03-chart-runtime.json').write_text(json.dumps({'matplotlib':matplotlib.__version__,
        'sources':['benchmarks/stress-v03-release.json','benchmarks/stress-v03-release-analytics.json'],
        'method':'retained samples; no timings rerun'},indent=2)+'\n')


def document(report,analytics,proof):
    baseline=read('stress-results.json')
    old=next(c for c in baseline['cases'] if c['engine']=='kestrel' and c['offered_rps']==2000)
    current=selected(report,2000,8)[0]
    stage=read('stress-v03-results.json');stalled=read('stress-v03-final.json');repeat=read('stress-v03-confirmation.json');handles=read('stress-v03-handles.json')
    def k2k(d):return next(c for c in d['cases'] if c['engine']=='kestrel' and c['offered_rps']==2000)
    variants=[('0.2 baseline',old),('0.3 cache + 2 ms delay (earlier code)',k2k(stage)),
        ('0.3 zero delay, first full run',k2k(stalled)),('0.3 zero delay, repeat before retained handles',k2k(repeat)),('0.3 retained handles for all reads',k2k(handles)),('0.3 final: boundary handles / independent scans',current)]
    variation=['| Run | Success/s | p99 success, ms | Failed / unexecuted |','|---|---:|---:|---:|']
    for label,c in variants:
        variation.append(f"| {label} | {c['successful_rps_in_arrival_window']:,.2f} | {c['latency_ms']['p99']:.2f} | {c['unsuccessful_or_unexecuted']:,} / {c['offered_operations']:,} |")
    variation_table='\n'.join(variation)
    full_matrix='\n'.join(f"| {c['profile']} | {c['clients']} | {c['offered_rps']} | {c['scheduled_seconds']} | {c['successful_rps_in_arrival_window']:.2f} | {c['latency_ms']['p99']:.2f} | {c['unsuccessful_or_unexecuted']} |" for c in report['cases'] if c['engine']=='kestrel')
    slo_table='\n'.join(['| Final Kestrel case | Zero loss and p99 at most 100 ms |', '|---|---|',
        f"| Mixed 2,000/s, 8 seconds | {'PASS' if proof['mixed_2k_slo_passed'] else 'FAIL'} |",
        f"| Mixed 500/s, 60 seconds | {'PASS' if proof['soak_500_slo_passed'] else 'FAIL'} |",
        f"| 10M analytics 1,000/s, 30 seconds | {'PASS' if proof['analytics_1k_30s_slo_passed'] else 'FAIL'} |"])
    versions=', '.join(f"{'KestrelSQL' if n=='kestrel' else NAMES[n]} {next(c['version'] for c in report['cases'] if c['engine']==n)}" for n in NAMES)
    recovery=read('hard-recovery-v03.json')
    live=json.loads((ROOT/'portfolio'/'live-pipeline-results.json').read_text(encoding='utf-8'))
    text=f'''# KestrelSQL 0.3: live ingestion and measured limits

**0.3 improves concurrent aggregate service and adds replayable ingestion; sustained service qualification remains a production gate.** In the final retained-handle 2,000-request/s mixed test, Kestrel completed {current['successful_rps_in_arrival_window']:,.2f} successful requests/s versus {old['successful_rps_in_arrival_window']:,.2f} in the 0.2 baseline. Its successful-request p99 was {current['latency_ms']['p99']:.2f} ms, with {current['unsuccessful_or_unexecuted']:,}/{current['offered_operations']:,} failed or unexecuted offers. A short local run is insufficient to qualify production service.

{slo_table}

The final 2,000/s mixed and lower-rate broad-window analytics cases still miss the 100 ms p99 target. The single-client mixed and 10,000/s overload cases also lose work; all results are included below. These remaining failures are priorities for the next storage and scheduling experiments.

The changes are immutable read snapshots, durable coalesced publication, batch IDs with SHA-256 payload identities, bounded small-run compaction, reference-aware reclamation, retained boundary handles and a 32 MiB retained decoded-page/prefix cache. [LIVE_METRICS.md](LIVE_METRICS.md) explains the APIs and [RESEARCH.md](RESEARCH.md) connects them to primary literature.

## Mixed workload: fresh six-engine comparison

{versions}. One million initial rows in each fresh fixture, 64 clients, 95% time-range COUNT/SUM requests and 5% durable 100-row appends, 5% late append timestamps. The 2,000/s case lasts eight seconds. Engines run sequentially on one shared Windows desktop; these results are not a ranking under controlled hardware conditions.

{table(selected(report,2000,8))}

![Fresh mixed-workload results](portfolio/v03-stress.png)

## Repeated runs and the unresolved tail

{variation_table}

The 17 ms result used an earlier implementation with a 2 ms batching delay. Both subsequent zero-delay runs are retained, including the markedly slower first run. The final full Kestrel matrix, including single-client and generic scans, is listed below. The second zero-delay run was an explicit reproducibility check. The final implementation retains immutable segment handles for boundary reads at explicit offsets and gives long scans independent handles; a new 512-query concurrent-read regression covers distinct pages and columns. The first retained-handle iteration regressed the generic scan case; it is retained and audited. The final correction restores independent synchronous scan handles on Windows. Reference results in the final comparison are reused from the same-session native-engine runs performed before that Kestrel-only change; original raw sample paths are preserved. There is no statistical confidence interval or isolated causal estimate for either change. Some fresh reference results also vary substantially from their earlier baseline; the host, OS caches, storage and client scheduling are uncontrolled. We have not established the cause of every stall.

Publication diagnostics capture synchronized segment/catalog work; the first zero-delay run includes publication calls exceeding seven seconds in some low-rate cases. Compaction does not hold readers' execution lock, but still occupies the writer. Next work is stage-by-stage storage profiling and repeated interleaved testing, as specified in the research notebook. Turning off durability would change the contract.

## Full final Kestrel matrix

| Profile | Clients | Offered requests/s | Seconds | Success/s | p99 success, ms | Failed / unexecuted |
|---|---:|---:|---:|---:|---:|---:|
{full_matrix}

The generic scan profile mixes full grouping, an unordered value filter and range reads with 10% appends. These operators are a separate performance boundary from indexed COUNT/SUM ranges. Single-client mixed latency includes its serialized durable writes.

## One-minute soak and overload

500 offered requests/s, 64 clients, 60 seconds:

{table(selected(report,500,60))}

10,000 offered requests/s, 64 clients, eight seconds:

{table(selected(report,10000,8))}

Loss, expiry and errors are included in the failed/unexecuted column. Percentiles describe successful requests only, including drain completions. Throughput counts successes completed in the arrival window. Each read or complete 100-row append is one request; these are not inserted-row rates. Client queue capacity is 256, with two-second queued-request expiry and eight-second connection/statement deadlines. Python load-generator dispatch and interface costs are part of observed latency.

## The specialized 10M-row analytical workload

Random windows cover 25-50% of the ten-million-row base, or 2.5-5 million rows per read. The offered mixture is 95% COUNT/SUM reads and 5% durable 100-row appends, at 2,000 requests/s, 64 clients, eight seconds. Both engines use one execution thread per query. The same exact row results and acknowledged-write reconciliation are checked after the run.

{table([c for c in analytics['cases'] if c['offered_rps']==2000])}

![Broad-window analytics during ingestion](portfolio/v03-analytics.png)

Kestrel's maintained sparse aggregate checkpoints avoid scanning the full selected window. DuckDB uses its normal aggregate execution and zonemaps. Index maintenance and storage are different; this experiment does not compare equivalent maintained materialized views. It tests our intended automatic time-window feature, not general SQL superiority. Historical 100M timing evidence is retained in [SCALE.md](SCALE.md); new untimed regression checks matched all 153 retained scale/real-data cases with the 0.3 CLI.

The deliberate lower-rate follow-up uses 1,000 offered requests/s for 30 seconds, with the same ten-million-row fixture and read/write mixture. Its purpose is to estimate a more reliable operating range; it does not replace or hide the 2,000/s failures:

{table([c for c in analytics['cases'] if c['offered_rps']==1000])}

## Correctness and the pipeline

- 30 Rust tests pass in debug and release, including concurrent identified writes, stable snapshots, compaction, receipt preservation and corruption detection after cache warming. Formatting and Clippy with warnings treated as errors pass. The runnable Rust example also checks replay and pinned versus fresh read views.
- {len(recovery['cycles'])} actual forced process kills: every acknowledged batch recovered, published batches remained whole, full scrubs passed, and replay of all attempted IDs produced one copy per batch. Unknown unacknowledged commits are explicitly counted. This models process death, not power loss.
- The Parquet demo ingested {live['initial_rows']:,} base plus {live['late_backfill_rows']:,} late rows; both source replays were deduplicated. {live['exact_sql_cases_against_duckdb']} SQL cases matched DuckDB after reopening. A prior window changed from {live['window_before_backfill']} to {live['window_after_backfill']}; changed content under an existing ID was rejected.
- Legacy catalogs were read, new receipt catalogs survived reopening, and an older binary rejected the upgraded format. Wider 64-column import and partial-row rejection checks passed.
- The current benchmark audit checked {proof['main']['raw_executed_samples_checked']:,} executed samples over {proof['main']['completed_cases']} cases and {proof['main']['offered_operations']:,} offers, plus {proof['analytics']['raw_executed_samples_checked']:,} samples over four broad-window cases. All acknowledged batches and {proof['main']['numpy_reference_windows']+proof['analytics']['numpy_reference_windows']} independent NumPy windows reconciled. Earlier 0.3 iterations are audited separately and retained.

## Reproduce and inspect

```powershell
cargo build --release --locked
cargo test --release --locked
python -m pip install -r benchmarks/stress_requirements.txt
python benchmarks/portable_servers.py start
python benchmarks/stress_compare.py --engines kestrel --output benchmarks/my-kestrel.json
python benchmarks/stress_compare.py --engines postgres,mysql,mariadb,sqlite,duckdb --targets --resume --output benchmarks/my-kestrel.json
python benchmarks/stress_compare.py --engines kestrel,duckdb --analytics --rows 10000000 --output benchmarks/my-analytics.json
python benchmarks/stress_compare.py --engines kestrel,duckdb --analytics --analytics-rps 1000 --seconds 30 --rows 10000000 --resume --output benchmarks/my-analytics.json
python benchmarks/hard_recovery.py --identified --output benchmarks/my-recovery.json
python benchmarks/live_pipeline_demo.py
python benchmarks/portable_servers.py stop
python benchmarks/report_v03.py --plot
```

The helper downloads pinned official portable packages to task-local folders and starts loopback-only processes, without installing Windows services. Setup/import is outside timed arrivals. References use durable commits and covering range indexes where applicable; [reference-packages.json](benchmarks/reference-packages.json) records pinned package hashes, hardware and native settings. CLI overrides accept freshly built binaries; default commands use bundled `bin` executables. A full rerun takes time and several gigabytes of temporary storage.

Reports: [current mixed/raw sample paths](benchmarks/stress-v03-release.json), [10M analytics](benchmarks/stress-v03-release-analytics.json), [all-reads handle regression](benchmarks/stress-v03-handles.json), [prior handles analytics](benchmarks/stress-v03-handles-analytics.json), [prior zero-delay/native comparison](benchmarks/stress-v03-confirmation.json), [prior analytics](benchmarks/stress-v03-analytics.json), [audit](benchmarks/v03-audit.json), [earlier cache iteration](benchmarks/stress-v03-results.json), [first zero-delay run](benchmarks/stress-v03-final.json), [identified crash/retry tests](benchmarks/hard-recovery-v03.json), [pipeline](portfolio/live-pipeline-results.json), [retained-data regression](benchmarks/release-recheck-v03.json), [format compatibility](benchmarks/format-v03.json), [current capability probes](benchmarks/capability-v03.json). The historical [0.2 matrix](HARD_TESTS.md) remains unchanged.

## Readiness boundaries

This remains an embedded BIGINT aggregate prototype. Archive does not support raw row retrieval, joins, strings, nullable input, updates/deletes or SQL transactions. The stress adapter is unauthenticated test infrastructure. Stable error codes, production health, native Arrow/Parquet APIs, comprehensive retention/orphan cleanup, backups, migrations, long endurance, physical power loss and Linux qualification remain work. Durable IDs stop at a disclosed 100,000-record budget; this suite does not qualify the performance of a full receipt ledger.

ClickHouse, SQL Server, Oracle and distributed clusters were not executed on this computer. Our workload is not TAOBench and cannot certify Facebook-scale operation. Shared-machine timings, different API boundaries, warm caches, selected short workloads and unequal SQL coverage limit every speed claim here.
'''
    (ROOT/'V03_RESULTS.md').write_text(text,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plot',action='store_true');args=parser.parse_args()
    report=read('stress-v03-release.json');analytics=read('stress-v03-release-analytics.json')
    proof={'main':audit(report,26),'analytics':audit(analytics,4),
        'earlier_cache_iteration':audit(read('stress-v03-results.json'),11),
        'first_zero_delay_run':audit(read('stress-v03-final.json'),11),'zero_delay_confirmation':audit(read('stress-v03-confirmation.json'),26),'analytics_before_retained_handles':audit(read('stress-v03-analytics.json'),4),'all_reads_retained_handles':audit(read('stress-v03-handles.json'),11),'all_reads_retained_handles_analytics':audit(read('stress-v03-handles-analytics.json'),2)}
    k=selected(report,2000,8)[0];soak=selected(report,500,60)[0]
    proof['mixed_2k_slo_passed']=k['unsuccessful_or_unexecuted']==0 and k['latency_ms']['p99']<=100
    proof['soak_500_slo_passed']=soak['unsuccessful_or_unexecuted']==0 and soak['latency_ms']['p99']<=100
    operating=next(c for c in analytics['cases'] if c['engine']=='kestrel' and c['offered_rps']==1000)
    proof['analytics_1k_30s_slo_passed']=operating['unsuccessful_or_unexecuted']==0 and operating['latency_ms']['p99']<=100
    (ROOT/'benchmarks'/'v03-audit.json').write_text(json.dumps(proof,indent=2)+'\n')
    document(report,analytics,proof)
    if args.plot:draw(report,analytics)
    print(json.dumps(proof,indent=2))


if __name__=='__main__':main()
