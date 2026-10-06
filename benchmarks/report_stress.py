"""Audit retained stress samples and generate the report; no timings are rerun.
Use --plot after installing plot-requirements.txt to regenerate the figures.
"""
import argparse
import gzip
import json
from pathlib import Path

from stress_compare import percentile

ROOT = Path(__file__).resolve().parents[1]
NAMES = {'kestrel':'KestrelSQL Archive', 'postgres':'PostgreSQL', 'mysql':'MySQL',
         'mariadb':'MariaDB', 'sqlite':'SQLite', 'duckdb':'DuckDB'}
ORDER = list(NAMES)


def audit(report):
    cases = report['cases']
    keys = [(c['engine'], c['profile'], c['clients'], c['offered_rps'], c['scheduled_seconds']) for c in cases]
    assert len(keys) == len(set(keys)) == 66, 'The full published matrix must contain 66 distinct cases'
    assert all(sum(c['engine']==name for c in cases)==11 for name in ORDER)
    checked = 0
    for case in cases:
        path = (ROOT/'benchmarks'/case['raw_samples_file']).resolve()
        assert path.is_relative_to((ROOT/'benchmarks'/'stress-samples').resolve())
        with gzip.open(path,'rt',encoding='utf-8') as file:
            samples = [json.loads(line) for line in file]
        sequences = {s['sequence'] for s in samples}
        expired = set(case['expired_sequences'])
        assert len(sequences)==len(samples) and len(expired)==case['queue_expired']
        assert not sequences.intersection(expired)
        assert all(0<=n<case['offered_operations'] for n in sequences|expired)
        successful = [s for s in samples if s['ok']]
        errors = sum(not s['ok'] for s in samples)
        assert len(successful)==case['successful_operations']
        assert errors==sum(e['sequence'] is not None for e in case['errors'])
        assert len(samples)+case['queue_expired']+case['queue_dropped']==case['offered_operations']
        assert errors+case['queue_expired']+case['queue_dropped']==case['unsuccessful_or_unexecuted']
        assert sum(s['operation']=='append' for s in successful)==case['write_successes']
        for key,p in [('p50',.5),('p95',.95),('p99',.99)]:
            assert percentile([s['latency_ms'] for s in successful],p)==case['latency_ms'][key]
        assert sum(s['latency_ms']<=100 for s in successful)/case['offered_operations']==case['offered_fraction_successful_within_100ms']
        reconciliation = case['reconciliation']
        assert reconciliation['all_acknowledged_batches_present'] and reconciliation['batch_atomicity_and_sums']
        assert reconciliation['acknowledged_batches']==case['write_successes']
        assert reconciliation['numpy_reference_windows']==20
        if case['engine']=='kestrel':
            assert reconciliation['full_kestrel_scrub']['verified_bytes']==reconciliation['rows']*24
        checked += len(samples)
    assert all(f.get('resolved_by_later_successful_case') for f in report['failed_cases'])
    return {'completed_cases':len(cases), 'engines':len(ORDER),
        'offered_operations':sum(c['offered_operations'] for c in cases),
        'successful_operations':sum(c['successful_operations'] for c in cases),
        'unsuccessful_or_unexecuted':sum(c['unsuccessful_or_unexecuted'] for c in cases),
        'raw_executed_samples_checked':checked, 'max_concurrent_clients':max(c['clients'] for c in cases),
        'numpy_reference_windows':20*len(cases), 'all_acknowledged_batches_present':True,
        'batch_atomicity_and_sums':True, 'sample_accounting_and_percentiles':True,
        'initial_setup_errors_retained_and_resolved':len(report['failed_cases'])}


def selected(report, rate, seconds, profile='mixed'):
    return [next(c for c in report['cases'] if c['engine']==name and c['profile']==profile
        and c['clients']==64 and c['offered_rps']==rate and c['scheduled_seconds']==seconds) for name in ORDER]


def table(cases):
    lines = ['| Engine | Successful requests/s during arrival window | p99 success latency, ms | Unsuccessful / unexecuted | Acknowledged 100-row batches |',
             '|---|---:|---:|---:|---:|']
    for c in cases:
        loss = c['unsuccessful_or_unexecuted']/c['offered_operations']*100
        lines.append(f"| {NAMES[c['engine']]} | {c['successful_rps_in_arrival_window']:,.2f} | {c['latency_ms']['p99']:,.2f} | {c['unsuccessful_or_unexecuted']:,} ({loss:.2f}%) | {c['write_successes']:,} |")
    return '\n'.join(lines)


def draw(report):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cases = selected(report,2000,8)
    names = ['Kestrel','Postgres','MySQL','MariaDB','SQLite','DuckDB']
    colors = ['#d64b3b']+['#28758e']*5
    fig, axes = plt.subplots(1,2,figsize=(12,6.3))
    fig.subplots_adjust(left=.075,right=.985,top=.85,bottom=.25,wspace=.25)
    fig.suptitle('Local stress test: 2,000 offered requests/s, 64 clients',fontsize=16,weight='bold')
    values = [c['successful_rps_in_arrival_window'] for c in cases]
    bars = axes[0].bar(names,values,color=colors)
    axes[0].axhline(2000,color='#333333',ls='--',lw=1)
    axes[0].set_ylim(0,2350)
    axes[0].set_ylabel('Successful completions/s within arrival window')
    for bar,value,c in zip(bars,values,cases):
        loss=c['unsuccessful_or_unexecuted']/c['offered_operations']*100
        axes[0].text(bar.get_x()+bar.get_width()/2,value+35,f'{value:,.0f}\n{loss:.1f}% loss',ha='center',fontsize=9)
    p99 = [c['latency_ms']['p99'] for c in cases]
    bars = axes[1].bar(names,p99,color=colors)
    axes[1].set_yscale('log')
    axes[1].set_ylim(.7,max(p99)*3)
    axes[1].set_ylabel('p99 successful-request latency (ms, log scale)')
    for bar,value in zip(bars,p99):
        axes[1].text(bar.get_x()+bar.get_width()/2,value*1.15,f'{value:.2f}',ha='center',fontsize=10)
    for axis in axes:
        axis.spines[['top','right']].set_visible(False)
        axis.tick_params(axis='x',rotation=25)
    fig.text(.5,.025,'1M seed rows · 95% range reads / 5% durable 100-row appends · 8 seconds · shared Windows PC\nLoss includes queue drops, expiry and execution errors; interfaces differ. This is not a Meta-scale qualification.',ha='center',fontsize=10)
    for ext in ['png','svg']:
        fig.savefig(ROOT/'portfolio'/f'stress-chart.{ext}',dpi=160,bbox_inches='tight')
    plt.close(fig)
    fig,axis=plt.subplots(figsize=(11,5.7))
    fig.subplots_adjust(left=.08,right=.98,top=.9,bottom=.24)
    for c,name,color in zip(selected(report,500,60),names,['#d64b3b','#28758e','#8864a8','#469568','#d49a24','#5f6269']):
        bins=c['five_second_bins']
        axis.plot([b['seconds_from_start']+2.5 for b in bins],
            [b['latency_p99_ms'] for b in bins],marker='o',label=name,color=color,lw=2)
    axis.set_yscale('log')
    axis.set(xlabel='Seconds from start (five-second completion bins)',ylabel='p99 successful-request latency (ms, log scale)',
        title='One-minute mixed-write soak: 500 offered requests/s, 64 clients')
    axis.spines[['top','right']].set_visible(False)
    axis.legend(ncols=3,loc='upper left')
    axis.grid(axis='y',alpha=.15)
    fig.text(.5,.025,'1M seed rows · successful completions only; overall loss is reported in HARD_TESTS.md\nSingle shared machine, short soak, no distributed or physical power-loss claim.',ha='center',fontsize=10)
    for ext in ['png','svg']:
        fig.savefig(ROOT/'portfolio'/f'stress-soak.{ext}',dpi=160,bbox_inches='tight')
    plt.close(fig)
    (ROOT/'portfolio'/'stress-chart-runtime.json').write_text(json.dumps({'matplotlib':matplotlib.__version__,
        'source':'benchmarks/stress-results.json','method':'retained timings; no benchmark rerun'},indent=2)+'\n')


def document(report, proof, recovery, capability):
    versions = ', '.join(f"{NAMES[name]} {next(c['version'] for c in report['cases'] if c['engine']==name)}" for name in ORDER)
    mixed,soak,burst=selected(report,2000,8),selected(report,500,60),selected(report,10000,8)
    k=mixed[0]
    text=f'''# KestrelSQL: local concurrency and failure qualification

**Kestrel does not meet the tested mixed-write performance target and is not production qualified.** At 2,000 offered requests/s with 64 clients it completed {k['successful_rps_in_arrival_window']:,.2f}/s during the arrival window, with {k['latency_ms']['p99']:.2f} ms p99 among successful requests and {k['unsuccessful_or_unexecuted']/k['offered_operations']*100:.2f}% unsuccessful or unexecuted requests. Several reference engines sustained this offered rate with no request loss. The earlier 100M-row aggregate advantage is specific to indexed range analytics; it does not establish fast transactional service performance.

This is an executed comparison on one Windows computer, as requested. **66 cases, {proof['offered_operations']:,} offered requests, up to 64 clients**, six database engines, 1M initial rows per fresh case, plus actual process-kill and integrity tests. SQL clients are interfaces to engines; this report compares the six engines through the interfaces below. It cannot cover every SQL product.

## Results: 2,000 requests/s mixed workload

95% range COUNT/SUM queries, 5% append operations, 100 rows per durable append, 8-second arrival window. These are request rates, not inserted-row rates. A read or a whole append batch is one request.

{table(mixed)}

![Mixed-workload throughput and successful-request tail latency](portfolio/stress-chart.png)

Loss is part of the result. A low percentile after dropping work is not evidence of a faster service. Completion rate counts only successful requests finished inside the scheduled arrival window; successful requests during draining are separately recorded in the raw report. p99 includes successful operations from the window and drain, and excludes failed, dropped, and expired requests.

## One-minute mixed-write soak

500 offered requests/s, 64 clients, 60 seconds; same 95/5 mixture. This is a short soak, not a long-duration endurance qualification.

{table(soak)}

![Successful-request p99 over five-second completion bins](portfolio/stress-soak.png)

Kestrel's 64-client read-only case at 500 offered requests/s lost no requests. Its one-minute mixed-write case degraded despite the lower arrival rate. The Archive publication path synchronizes a segment and catalog per batch, rewrites catalog metadata, and accumulates files. The test bridge holds an exclusive write lock across append. These are plausible contributors to stalls; this run does not include profiling that isolates their individual costs.

## Overload burst

10,000 offered requests/s, 64 clients, 8 seconds. The generator, drivers, OS scheduling and database share one machine, so these are whole-path overload observations rather than maximum engine capacities.

{table(burst)}

## Workload and measurement contract

- Tested versions: {versions}. Python 3.12.10; 20 logical CPU threads and about 31.9 GiB physical RAM; Windows 10 build 19045. The desktop and OS caches were not isolated. Each query uses one execution thread; concurrent clients can execute together. No CPU affinity, cold-cache control, independent load host or repeated-run confidence intervals.
- Every case starts with a fresh three-column integer table: `ts`, `value`, `device`. Values follow a deterministic generator with seed 20261006. 80% of range reads target a 1% timestamp hotspot, with 100- or 1,000-row-width intervals. Appends contain 100 rows, 5% with late timestamps. This hotspot is read concentration, not contention on repeatedly updated social-graph rows.
- Per engine: read and 5% append profiles at 1/16/64 clients and 500 requests/s; 25% append profile at 64 clients and 500/s; scan/grouping profile with 10% appends at 64 clients and 200/s; 5% append at 2,000/s and 10,000/s; then the 60-second 500/s soak. Other sweeps last 8 seconds. Scan queries include full grouping and a filter on unsorted `value`.
- Open-loop arrivals are scheduled independently of completions. Latency starts at the scheduled arrival and includes dispatch lag, client queueing and execution. The queue holds 256 requests. A request older than two seconds when dequeued expires without execution. Queue-full drops, expiry, execution errors and ambiguous commits are recorded separately. Each request has an eight-second connection/statement or socket timeout where supported; native SQLite uses a five-second busy timeout. Native DuckDB has no harness-enforced statement cancellation. Setup uses 120 seconds and is outside timing.
- Kestrel uses one shared `Archive` behind a Rust `RwLock` and a loopback JSON bridge. Queries acquire shared locks; append acquires an exclusive lock. The bridge is a bounded-message benchmark helper, not a production service. It has no authentication, session transaction contract, connection admission limit or query cancellation. Independent Archive processes cannot read while another holds the store lock.
- PostgreSQL, MySQL and MariaDB use native loopback protocols; SQLite and DuckDB use Python bindings. The Python generator and drivers can impose their own limits, especially at 10,000/s. Dispatch-lag percentiles and full per-request timings are retained; differences in interface and serialization cost prevent a universal engine ranking.
- PostgreSQL gets a `ts INCLUDE(value)` covering index; MySQL/MariaDB/SQLite get `(ts,value)` covering indexes. Kestrel uses its aggregate checkpoints; DuckDB its normal storage/zonemaps. PostgreSQL buffers and InnoDB buffers are 128 MiB; DuckDB uses a 256 MB buffer-manager limit. These settings are not equal total-memory caps. No derived aggregate views were added to the references.
- Durable acknowledgments use Kestrel synchronized segment/catalog publication, SQLite WAL with `synchronous=FULL`, PostgreSQL `synchronous_commit=on`, MySQL/MariaDB `innodb_flush_log_at_trx_commit=1` with binary logging disabled, and DuckDB file-backed autocommit. This tests local commit behavior, not replicated durability or physical power loss. SQLite's WAL permits reader/writer concurrency but only one writer; FULL adds synchronization on commits. [SQLite WAL documentation](https://www.sqlite.org/wal.html)

{proof['initial_setup_errors_retained_and_resolved']} initial provisioning attempts failed because the original eight-second request timeout was also used for bulk seed loading. Missing cases were rerun with a separate 120-second setup timeout. The initial errors remain in `failed_cases`, marked resolved; their failed setup time is excluded from load results. The raw report combines the completed first-pass and missing-case rerun results. There was no performance rerun chosen to replace a slower result.

## Correctness and failure results

Every completed stress case reopens Kestrel or uses fresh native reference connections, reconciles all seed rows and every batch against independent expected counts/sums, and checks 20 NumPy reference windows after concurrent late writes. All acknowledged batches remained present; published batches were complete and had correct sums. Unacknowledged-but-committed batches are reported explicitly, rather than assuming a timeout means rollback. All 11 Kestrel cases also passed a complete payload scrub. This is post-run reconciliation; it does not verify every live query's snapshot against an online oracle.

The sample audit checked {proof['raw_executed_samples_checked']:,} executed request samples, success/loss accounting, unique sequence identifiers, and the published percentiles. Across six engines there were {proof['successful_operations']:,} successes and {proof['unsuccessful_or_unexecuted']:,} unsuccessful/unexecuted offers. {proof['numpy_reference_windows']:,} independent reference windows matched.

{len(recovery['cycles'])} forced OS process kills interrupted active Archive ingestion at delays from 2 ms to 500 ms. After reopening, every acknowledged batch survived, published batches were whole, exact prefix counts/sums matched, and full scrubs passed. A committed batch whose acknowledgment was lost may still appear, so this is not an exactly-once retry guarantee. The OS and disk remained running: no physical power-loss, disk-full, filesystem write-failure or replicated failover qualification is claimed.

Boundary checks rejected {recovery['boundaries']['malformed_or_unsupported_statements_rejected_without_data_changes']:,} malformed/unsupported SQL statements without data changes, rejected an independent store opener, and explicitly failed the group-materialization guard with a healthy store afterward. A flipped payload byte was rejected when its page was read and by the full scrub. Metadata-only totals still succeeded, as designed; they do not scrub all payload pages.

## SQL capability checks

Executed against fresh 1,000-row fixtures. This matrix applies to the `Archive` path used for all new stress cases. The original RAM `Database` has a separate, limited transaction API.

| Executed check | Kestrel Archive | PostgreSQL / MySQL / MariaDB / SQLite / DuckDB |
|---|---|---|
| Exact range COUNT/SUM | Pass | Pass on all five |
| Raw row point projection | Unsupported | Pass on all five |
| Self join | Unsupported | Pass on all five |
| String and nullable schema | Unsupported | Pass on all five |
| SQL INSERT | Unsupported; append API used for load | Pass on all five |
| UPDATE / DELETE in a transaction, then verified rollback | Unsupported | Pass on all five |
| Independent Archive process reader while bridge is open | Rejected by store lock | Native connection concurrency checked; SQLite/DuckDB used two connections in one process |

The machine had no usable Docker/Linux test environment for ClickHouse and no local SQL Server or Oracle instance. CockroachDB, TiDB, YugabyteDB and Spanner distributed tests were not executed. These omissions are recorded in [capability-results.json](benchmarks/capability-results.json); no invented numbers or parity claims are supplied.

## What a Facebook-level test would require

Meta's published transactional TAOBench models social-graph access, contention and skew, with substantially more application behavior than aggregate event reads and appends. Our narrow common workload does not implement that benchmark or its operating scale. [Meta TAOBench article](https://engineering.fb.com/2022/09/07/core-infra/taobench/)

The separate DCPerf TaoBench package is a TAO-cache workload, with Linux and multi-host/network recommendations; it is not the transactional TAOBench implementation. [DCPerf package instructions](https://github.com/facebookresearch/DCPerf/blob/main/packages/tao_bench/README.md)

Before a credible transactional social-graph comparison, Kestrel needs point retrieval, typed objects and associations, mutation/transaction semantics, concurrent snapshots, retry identifiers and operational instrumentation. A production gate also needs compaction, retention, backup/restore, long endurance runs, disk faults and supported-platform qualification. Distributed Meta-scale validation further requires machines and an independent load fleet. This computer-only result establishes none of those qualifications.

For the next local iteration, use a project acceptance target of **2,000 offered mixed requests/s, zero loss and p99 at or below 100 ms**, with correctness reconciliation. This is our proposed target, not Meta's SLO. Preserve these results as the baseline, profile publication and locking, then evaluate batching/compaction and snapshot concurrency without weakening commit behavior.

## Reproduce on Windows x64

From this repository, with Python 3.12 and Rust 1.89+:

```powershell
python -m pip install -r benchmarks\\stress_requirements.txt
cargo build --release --locked --bin kestrel-stress
python benchmarks\\portable_servers.py start
try {{
    python benchmarks\\stress_compare.py --binary target\\release\\kestrel-stress.exe
    python benchmarks\\hard_recovery.py --binary target\\release\\kestrel-stress.exe --sql-binary bin\\kestrel.exe
    python benchmarks\\capability_probe.py --binary target\\release\\kestrel-stress.exe --sql-binary bin\\kestrel.exe
}} finally {{
    python benchmarks\\portable_servers.py stop
}}
python -m pip install -r benchmarks\\plot-requirements.txt
python benchmarks\\report_stress.py --plot
```

The bundled `bin/kestrel-stress.exe` can replace a local build. The portable helper downloads pinned official PostgreSQL/MySQL/MariaDB archives, verifies SHA-256, starts only loopback listeners with task-local data directories, and registers no Windows service. Its stop command verifies the server's data directory before requesting shutdown. Do not expose these password-free benchmark servers to a network. Allow approximately 0.7 GB for downloads and several GB for extraction/data/logs; the suite deletes its own completed case fixtures after reconciliation. Raw scale datasets and reference-server packages are omitted from the release ZIP. Fresh runs overwrite the result files; preserve the baseline copy before rerunning. `--resume` retries missing matrix cases and retains failures.

Evidence: [stress results](benchmarks/stress-results.json), per-request gzip files under `benchmarks/stress-samples/`, [sample audit](benchmarks/stress-audit.json), [forced kills and boundaries](benchmarks/hard-recovery-results.json), [capability checks](benchmarks/capability-results.json), [package provenance](benchmarks/reference-packages.json). The separate [100M analytics tests](SCALE.md) and [real-data pipeline](PORTFOLIO.md) provide complementary data-engineering evidence.

## Full executed matrix

| Engine | Profile | Clients | Offered/s | Duration, s | Success/s in window | p99 ms | Loss / unexecuted |
|---|---|---:|---:|---:|---:|---:|---:|
'''
    for name in ORDER:
        cases = [c for c in report['cases'] if c['engine']==name]
        cases.sort(key=lambda c:(['read','mixed','write','scan'].index(c['profile']),c['scheduled_seconds'],c['offered_rps'],c['clients']))
        for c in cases:
            text+=f"| {NAMES[name]} | {c['profile']} | {c['clients']} | {c['offered_rps']:,} | {c['scheduled_seconds']:g} | {c['successful_rps_in_arrival_window']:,.2f} | {c['latency_ms']['p99']:,.2f} | {c['unsuccessful_or_unexecuted']:,} |\n"
    (ROOT/'HARD_TESTS.md').write_text(text,encoding='utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--plot',action='store_true')
    args=parser.parse_args()
    report=json.loads((ROOT/'benchmarks'/'stress-results.json').read_text())
    recovery=json.loads((ROOT/'benchmarks'/'hard-recovery-results.json').read_text())
    capability=json.loads((ROOT/'benchmarks'/'capability-results.json').read_text())
    proof=audit(report)
    assert len(recovery['cycles'])==24 and all(c['sum_and_full_scrub_passed'] for c in recovery['cycles'])
    assert len(capability['engines'])==6
    for c in capability['engines']:
        assert c['probes']['exact_range_aggregate']['supported']
        if c['engine']!='kestrel':
            assert all(p['supported'] for p in c['probes'].values())
        else:
            assert all(not p['supported'] for key,p in c['probes'].items() if key!='exact_range_aggregate')
    (ROOT/'benchmarks'/'stress-audit.json').write_text(json.dumps(proof,indent=2)+'\n')
    if args.plot: draw(report)
    document(report,proof,recovery,capability)
    print(json.dumps(proof,indent=2))


if __name__=='__main__':
    main()
