"""Audit every offered request and report retry gains alongside control regressions."""
import gzip
import hashlib
import json
import random
import statistics
from collections import Counter
from pathlib import Path

from stress_compare import make_task, percentile

ROOT=Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT/name).read_text(encoding='utf-8'))


def summary(cases):
    assert cases
    return {'runs':len(cases),
        'median_successful_rps':statistics.median(c['successful_rps_in_arrival_window'] for c in cases),
        'median_run_p99_ms':statistics.median(c['latency_ms']['p99'] for c in cases),
        'run_p99_range_ms':[min(c['latency_ms']['p99'] for c in cases),max(c['latency_ms']['p99'] for c in cases)],
        'unsuccessful_or_unexecuted':sum(c['unsuccessful_or_unexecuted'] for c in cases),
        'offered_operations':sum(c['offered_operations'] for c in cases),
        'zero_loss_p99_100ms_runs':sum(c['unsuccessful_or_unexecuted']==0 and c['latency_ms']['p99']<=100 for c in cases),
        'median_replay_p99_ms':statistics.median(c['replay_latency_ms']['p99'] for c in cases) if cases[0].get('replay_successes') else None,
        'median_replay_call_p99_ms':statistics.median(c['operation_call_ms']['replay']['p99'] for c in cases) if cases[0].get('replay_successes') else None,
        'median_append_p99_ms':statistics.median(c['append_latency_ms']['p99'] for c in cases) if cases[0].get('write_successes') else None,
        'successful_new_appends':sum(c['write_successes'] for c in cases)}


def main():
    build=read('benchmarks/rust-checks-035-final.json')
    trial_build=read('benchmarks/rust-checks-035.json')
    prior=read('verification-v034.json') if (ROOT/'verification-v034.json').exists() else read('verification.json')
    assert prior['version']=='0.3.4'
    reports={name:read('benchmarks/'+file) for name,file in {
        'exploratory_baseline':'retry-035-baseline.json','confirmation':'retry-035-confirmation.json',
        'burst':'retry-035-burst.json','controls':'retry-035-controls.json','reference':'retry-035-reference.json',
        'final_retry':'retry-035-final-retry.json','final_controls':'retry-035-final-controls.json','final_reference':'retry-035-final-reference.json'}.items()}
    expected={'exploratory_baseline':4,'confirmation':24,'burst':6,'controls':18,'reference':6,'final_retry':12,'final_controls':27,'final_reference':9}
    intervals=[]
    audit={'version':'0.3.5','completed_cases':0,'offered_operations':0,'numpy_windows':0,'reports':{},'groups':{},
        'service_qualification':'failed; experimental retry improvement, production envelope unqualified',
        'historical_timing':'Prior 0.3.4 and earlier evidence is preserved, not counted as new. Exploratory baseline is reported separately from confirmation.',
        'source_sha256':build['source_sha256']}
    for name,report in reports.items():
        assert len(report['cases'])==expected[name] and not report['failed_cases']
        if name!='exploratory_baseline':
            assert report['binary_sha256']['candidate']==(build if name.startswith('final_') else trial_build)['bridge_sha256']
        for case in report['cases']:
            start=case['arrival_start_monotonic_ns']
            intervals.append((start,start+int(case['including_drain_seconds']*1e9),name,case['scenario'],case['variant'],case['round']))
            with gzip.open(ROOT/'benchmarks'/case['raw_samples_file'],'rt',encoding='utf-8') as stream:
                samples=[json.loads(line) for line in stream]
            good=[s for s in samples if s['ok']]
            assert len(samples)+case['queue_dropped']+case['queue_expired']==case['offered_operations']
            assert len(good)==case['successful_operations']
            assert len({s['sequence'] for s in samples})==len(samples)
            assert all(0<=s['sequence']<case['offered_operations'] for s in samples)
            assert len({*case['expired_sequences']})==case['queue_expired']
            assert not set(case['expired_sequences']).intersection(s['sequence'] for s in samples)
            assert case['offered_operations']-len(good)==case['unsuccessful_or_unexecuted']
            latency=[s['latency_ms'] for s in good]
            assert case['latency_ms']=={'p50':percentile(latency,.5),'p95':percentile(latency,.95),'p99':percentile(latency,.99),'max':max(latency)}
            assert case['completed_in_arrival_window']==sum(s['finished_ns']<=start+int(case['scheduled_seconds']*1e9) for s in good)
            assert case['successful_rps_in_arrival_window']==case['completed_in_arrival_window']/case['scheduled_seconds']
            case['operation_call_ms']={kind:{'p99':percentile([s['service_ms'] for s in good if s['operation']==kind],.99)} for kind in ['append','replay','query']}
            oracle=case['reconciliation']
            assert oracle['all_acknowledged_batches_present'] and oracle['batch_atomicity_and_sums']
            assert oracle['numpy_reference_windows']==20
            if case['engine']=='kestrel':
                assert oracle['full_kestrel_scrub']['verified_bytes']==oracle['rows']*24
                before=case['ingest_state_before_load']
                after=case['live_state_before_reopen']['ingest']
                assert after['queued_payload_bytes']==0 and after['max_group_requests']<=64
                assert case['live_state_before_reopen']['retained_page_cache_bytes']<=32*1024*1024
                if case['version']=='0.3.5':
                    assert not after['writer_poisoned'] and not after['writer_stopped']
                    if after.get('retry_index_enabled',True):
                        assert after['retry_index_ids']==case['live_state_before_reopen']['recorded_batch_ids']
                        if case['profile'] in ['retry','retry_mixed']:
                            assert after['fast_retry_hits']-before['fast_retry_hits']==case['replay_successes']
                    else:
                        assert after['retry_index_ids']==after['retry_index_logical_bytes']==after['fast_retry_hits']==0
                if case['profile'] in ['retry','retry_mixed']:
                    assert case['known_receipts_after_reopen']==128 and case['seed_replay_passed']
                    rng=random.Random(20261006)
                    counts=Counter(make_task(rng,seq,1_012_800,case['profile'])[1] for seq in range(case['offered_operations']))
                    case['offered_by_operation']=dict(counts)
                    case['unsuccessful_by_operation']={kind:count-sum(s['operation']==kind for s in good) for kind,count in counts.items()}
                    assert sum(case['unsuccessful_by_operation'].values())==case['unsuccessful_or_unexecuted']
                    if case['profile']=='retry':
                        assert case['load_group_commits']==0 and case['write_successes']==0
            audit['completed_cases']+=1
            audit['offered_operations']+=case['offered_operations']
            audit['numpy_windows']+=oracle['numpy_reference_windows']
        audit['reports'][name]={'cases':len(report['cases']),'offers':sum(c['offered_operations'] for c in report['cases']),
            'loss':sum(c['unsuccessful_or_unexecuted'] for c in report['cases'])}
        for scenario in sorted({c['scenario'] for c in report['cases']}):
            for variant in sorted({c['variant'] for c in report['cases'] if c['scenario']==scenario}):
                cases=[c for c in report['cases'] if c['scenario']==scenario and c['variant']==variant]
                result=summary(cases)
                if cases[0]['profile'] in ['retry','retry_mixed']:
                    result['loss_by_operation']={kind:sum(c['unsuccessful_by_operation'].get(kind,0) for c in cases) for kind in ['append','replay']}
                audit['groups'][f'{name}/{scenario}/{variant}']=result
    intervals.sort()
    assert all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:])), 'timed workloads overlapped'
    assert (audit['completed_cases'],audit['offered_operations'],audit['numpy_windows'])==(106,3_480_000,2120)
    audit['final_binary_cases']=48
    audit['final_binary_offers']=1_440_000
    audit['preserved_trial_cases']=58
    audit['timed_database_workloads_no_overlap']=True
    for filename,count,fields in [('retry-035-faults.json',8,['recovery_original_receipt','atomic_rows_and_sum','retry_deduplication','full_scrub']),
        ('group-035-recovery.json',32,['acknowledged_data_present','whole_batches_and_sums','original_receipt_generations_preserved','retry_exactly_once_after_second_reopen','full_scrubs_passed'])]:
        proof=read('benchmarks/'+filename)
        cases=proof['cases'] if 'cases' in proof else proof['cycles']
        assert len(cases)==count and not proof['failed_cases']
        assert proof['binary_sha256']==build['bridge_sha256'] and all(all(c[f] for f in fields) for c in cases)
    faults=read('benchmarks/publication-035-faults.json')
    assert read('benchmarks/retry-035-faults.json')['driver_sha256']==build['live_retry_driver_sha256']
    assert faults['binary_sha256']==build['bridge_sha256'] and faults['fault_driver_sha256']==build['fault_driver_sha256']
    assert len(faults['cut_points'])==56 and len(faults['corruption_cases'])==22
    assert all(all(c[k] for k in ['original_receipts_preserved','atomic_rows_and_sum','retry_deduplication_passed','full_scrub_passed']) for c in faults['cut_points'])
    assert all(c['rejected'] for c in faults['corruption_cases'])
    pipeline=read('portfolio/live-pipeline-035-results.json')
    assert pipeline['exact_sql_cases_against_duckdb']==42 and pipeline['replayed_sources_not_duplicated'] and pipeline['changed_content_rejected']
    assert pipeline['binary_sha256']==build['bridge_sha256']
    differential=read('benchmarks/archive-035-verification.json')
    assert differential['queries_checked_against_each_reference']==500 and differential['binary_sha256']==build['cli_sha256']
    retained=read('benchmarks/release-recheck-035.json')
    assert retained['all_retained_results_match'] and retained['binary_sha256']==build['cli_sha256']
    audit.update(live_retry_fault_cases=8,concurrent_kill_cycles=32,publication_cut_point_cases=56,corruption_cases=22,
        differential_cases_each_reference=500,parquet_exact_sql_cases=42,retained_result_checks=sum(retained[k] for k in ['retained_fixed_scale_cases','retained_random_window_cases','retained_real_data_cases']))
    for filename in ['timed-035-run-order.json','timed-035-final-run-order.json','correctness-035-final-run-order.json']:
        records=read('benchmarks/'+filename)
        assert len(records)==({'timed-035-run-order.json':4,'timed-035-final-run-order.json':3,'correctness-035-final-run-order.json':6}[filename]) and all(r['returncode']==0 for r in records)
        for record in records:
            for file,digest in record['harness_sha256'].items():
                directory=ROOT/'benchmarks/trial-035-harness' if filename=='timed-035-run-order.json' else ROOT/'benchmarks'
                assert hashlib.sha256((directory/file).read_bytes()).hexdigest()==digest,file
        assert all(a['completed_monotonic_ns']<=b['started_monotonic_ns'] for a,b in zip(records,records[1:]))
    timed=read('benchmarks/timed-035-final-run-order.json')
    correct=read('benchmarks/correctness-035-final-run-order.json')
    assert timed[-1]['completed_monotonic_ns']<=correct[0]['started_monotonic_ns']
    assert build['build_run_order'][-1]['completed_at_utc']<=timed[0]['started_at_utc']
    trial_order=read('benchmarks/timed-035-run-order.json')
    assert trial_build['build_run_order'][-1]['completed_at_utc']<=trial_order[0]['started_at_utc']
    assert trial_order[-1]['completed_at_utc']<=build['build_run_order'][0]['started_at_utc']
    direct=read('benchmarks/retry-035-direct.json')
    assert len(direct['cases'])==18 and not direct['failed_cases']
    assert direct['probe_source_sha256']==hashlib.sha256((ROOT/'benchmarks/live_retry_inprocess.rs').read_bytes()).hexdigest()
    assert direct['builds']['candidate']['core_source_sha256']==build['source_sha256']
    direct_rows=['| Caller threads | Baseline median calls/s | Enabled candidate median calls/s | Ratio | Baseline sampled p99 µs | Candidate sampled p99 µs |','|---:|---:|---:|---:|---:|---:|']
    audit['embedded_retry']={}
    for clients in [1,16,64]:
        values={}
        for variant in ['baseline','candidate']:
            cases=[c for c in direct['cases'] if c['clients']==clients and c['variant']==variant]
            assert len(cases)==3
            for case in cases:
                assert case['all_receipts_valid'] and case['no_publications_during_load'] and case['full_scrub_passed']
                assert case['ingest_after']['duplicate_batches']-case['ingest_before']['duplicate_batches']==case['successful_calls']
                if variant=='candidate':
                    assert case['ingest_after']['fast_retry_hits']-case['ingest_before']['fast_retry_hits']==case['successful_calls']
                with gzip.open(ROOT/'benchmarks'/case['raw_latency_samples'],'rt',encoding='utf-8') as stream:
                    raw=json.load(stream)
                assert len(raw)==case['sampled_calls']
                assert case['sampled_latency_us']=={name:percentile(raw,p)/1000 for name,p in [('p50',.5),('p95',.95),('p99',.99)]}
            values[variant]={'median_calls_per_second':statistics.median(c['successful_rps_in_window'] for c in cases),
                'median_sampled_run_p99_us':statistics.median(c['sampled_latency_us']['p99'] for c in cases),
                'calls_per_second_range':[min(c['successful_rps_in_window'] for c in cases),max(c['successful_rps_in_window'] for c in cases)]}
        ratio=values['candidate']['median_calls_per_second']/values['baseline']['median_calls_per_second']
        audit['embedded_retry'][str(clients)]={**values,'ratio':ratio}
        direct_rows.append(f"| {clients} | {values['baseline']['median_calls_per_second']:,.0f} | {values['candidate']['median_calls_per_second']:,.0f} | {ratio:.2f}× | {values['baseline']['median_sampled_run_p99_us']:.2f} | {values['candidate']['median_sampled_run_p99_us']:.2f} |")
    assert timed[-1]['completed_at_utc']<=direct['builds']['baseline']['started_at_utc']
    assert direct['builds']['candidate']['completed_at_utc']<=direct['run_order'][0]['started_at_utc']
    assert all(a['completed_at_utc']<=b['started_at_utc'] for a,b in zip(direct['run_order'],direct['run_order'][1:]))
    assert direct['run_order'][-1]['completed_at_utc']<=correct[0]['started_at_utc']
    audit['embedded_retry_cases']=18
    audit['build_and_correctness_outside_timed_suites']=True
    (ROOT/'benchmarks/retry-035-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    def table(name):
        lines=['| Scenario / variant | Median req/s | Median run p99 ms | Run p99 range ms | Loss / offers | Runs meeting zero loss + p99 ≤100 ms |',
            '|---|---:|---:|---:|---:|---:|']
        for key,g in audit['groups'].items():
            if key.startswith(name+'/'):
                label=key[len(name)+1:]
                lo,hi=g['run_p99_range_ms']
                lines.append(f"| {label} | {g['median_successful_rps']:.2f} | {g['median_run_p99_ms']:.2f} | {lo:.2f}–{hi:.2f} | {g['unsuccessful_or_unexecuted']:,} / {g['offered_operations']:,} | {g['zero_loss_p99_100ms_runs']} / {g['runs']} |")
        return '\n'.join(lines)
    mixed=['| Variant | Median retry arrival p99 ms | Median retry call p99 ms | Median new-write arrival p99 ms | Failed/unexecuted new writes | Failed/unexecuted retries |','|---|---:|---:|---:|---:|---:|']
    for variant in ['baseline','indexed0']:
        g=audit['groups']['final_retry/retry-mixed/'+variant]
        mixed.append(f"| {variant} | {g['median_replay_p99_ms']:.2f} | {g['median_replay_call_p99_ms']:.2f} | {g['median_append_p99_ms']:.2f} | {g['loss_by_operation']['append']:,} | {g['loss_by_operation']['replay']:,} |")
    profile_notes=[]
    for variant in ['baseline','indexed0']:
        cases=[c for c in reports['final_retry']['cases'] if c['scenario']=='retry-mixed' and c['variant']==variant]
        totals={stage:sum(c['live_state_before_reopen']['publication_profile'][stage]['total_ms']-c['publication_profile_before_load'][stage]['total_ms'] for c in cases)
            for stage in ['prepare','segment_write','segment_sync','catalog_encode','catalog_write','catalog_sync','catalog_rename']}
        share=(totals['segment_sync']+totals['catalog_sync'])/sum(totals.values())*100
        audit['groups']['final_retry/retry-mixed/'+variant]['publication_stage_totals_ms']=totals
        profile_notes.append(f"- {variant}: synchronized segment/catalog stages account for {share:.2f}% of the sum of seven timed publication stages over the three retry-mixed loads. This is process-local profiling, not device attribution.")
    (ROOT/'benchmarks/retry-035-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    final_old=audit['groups']['final_retry/retry-mixed/baseline']
    final_new=audit['groups']['final_retry/retry-mixed/indexed0']
    document=f'''# KestrelSQL 0.3.5: opt-in confirmed retries during live ingestion

Experimental prototype on one shared Windows computer. The change makes confirmed exact retries independent of writer queueing and coalescing. It does not qualify production durability, a distributed service, Facebook-scale traffic or universal superiority. Fresh-write controls and every losing case are retained below.

On the final 95%-retry / 5%-new-write fixture, median combined p99 changes from {final_old['median_run_p99_ms']:.2f} to {final_new['median_run_p99_ms']:.2f} ms; final enabled runs lose {final_new['unsuccessful_or_unexecuted']:,} of {final_new['offered_operations']:,} offers versus {final_old['unsuccessful_or_unexecuted']:,} for the baseline. New-write tails remain separate. The initial always-enabled write-heavy control regressed materially, so the added map stays off by default.

![Audited medians and individual runs for embedded retries and the final retry-heavy JSON workload](portfolio/perf-035-retries.png)

## Change and contract

`LiveArchive::with_retry_index(archive, LiveOptions::default())` opts into a lookup cloned once at startup. `new` and `with_options` allocate no second map and keep queued retries. Enabled wrappers extend the lookup only after synchronized publication and publication of the read snapshot, before ACKs. Every known retry still checks shape, SHA-256 of the exact submitted column/row order, and the original receipt generation. The lookup lock is released before hashing. Unknown and pending IDs retain writer admission and whole-group conflict behavior; known conflicts fail independently. Observed writer poisoning or exit rejects both fast and new appends until reopening. Old snapshots remain readable.

The extra lookup is bounded by the existing 100K-ID ceiling; `retry_index_logical_bytes` counts key capacity, String values and fixed receipt records, excluding tree nodes and allocator overhead. It adds memory and startup work. New receipts extend it incrementally; there is no full-map copy per commit. CAT4/SEG2 and the fingerprint domain are unchanged. Default collection delay remains zero.

## Method

Frozen 0.3.4 baseline and 0.3.5 candidate; fresh 1M standard-row fixtures with 50,000 retained IDs. Retry cases add 128 committed 100-row known batches before arrivals and retain their original generations. 64 clients, 256 client queue slots, 2-second expiry, 8-second socket timeout, deterministic paced arrivals. `retry-only` offers 100% known retries; `retry-mixed` offers 95% retries and 5% new identified 100-row writes. Main comparisons use 2,000 offers/s for 15 seconds, three rotating rounds. In the initial trial, `baseline` / `baseline8` are 0.3.4 at 0 / 8 ms; `delay0` / `delay8` are the initial 0.3.5 build with the map always enabled at 0 / 8 ms. Final labels are defined with their tables below. Fixture build, scrubs, reconciliation and compression are outside arrivals.

Req/s counts successful completions inside arrivals. Percentiles include successful requests only; losses include every error, drop and expiry separately. Medians are across run summaries, not pooled percentiles. The 10K retry screen is eight seconds and is an overload screen, not sustained capacity. Client JSON/Python costs, Windows scheduling and shared-desktop activity are included. No compilation or other task CPU-heavy job runs during any timed database workload. Only task-owned database processes are used and stopped.

The first always-on trial regressed the write-heavy control: median completion fell from 1,977.87 to 955.67 req/s, with 31,231 failed/unexecuted candidate offers versus 652 for the baseline over 90K offers each. The slow candidate runs spent most measured publication time in synchronization. This does not establish lookup CPU as the cause, but it prevented enabling the extra state by default. The trial source, binaries, harnesses, proof and all samples are preserved separately. Final comparisons below use the rebuilt opt-in API.

## Final repeated retry comparisons

Here `baseline` is frozen 0.3.4 at zero delay; `indexed0` is the final 0.3.5 build with the lookup explicitly enabled at zero delay. Three alternating rounds, same fixture and client workload.

{table('final_retry')}

Separate retry and new-write tails reveal whether a favorable combined percentile hides ingestion problems:

{chr(10).join(mixed)}

Arrival latency includes waiting in the shared client worker pool. Call latency begins when a worker starts the operation and includes JSON, network and database work; it is not server-only time. If slow writes occupy all workers, even a database retry that bypasses the writer can wait before dispatch. All affected retries and new-write losses remain in the same report. Splitting caller capacity is a future experiment, not a delivered guarantee.

{chr(10).join(profile_notes)}

## 10,000 offered retries/s

{table('burst')}

This overload screen used the initial always-on trial. It did not establish a clear JSON-client throughput gain and is preserved without replacement. It is not a final-default measurement.

## Embedded Rust API comparison

The identical test probe is compiled on verified copies of both source trees after open-loop loads stop. A compatibility trait invokes the original queued constructor on 0.3.4; the candidate's inherent opt-in constructor takes precedence on 0.3.5. No network, JSON or Python client loop is inside these timed calls. Every call clones the same 100-row payload and checks duplicate status, row count and original generation. Five-second closed-loop runs at 1/16/64 caller threads, three alternating rounds, 50K retained IDs and 1M base rows. Fixture construction, initial publication and full scrub are outside timing. Call counts are complete; latency is systematically sampled every 64 calls per worker and retained. This isolates the embedded API; it does not qualify an arrival-rate SLO or compare other database engines.

{chr(10).join(direct_rows)}

## Fresh-write and anonymous controls

Anonymous mixed contains 5% new anonymous writes; receipt mixed and receipt write contain 5% and 25% new identified writes respectively. Both use the default 0 ms policy. Receipt controls retain 50K IDs. These workloads do not exercise known fast retries, so any improvement or regression is an indirect effect or desktop variance.

Final `baseline` is 0.3.4; `delay0` is 0.3.5 default with no second map; `indexed0` enables it on the same final binary.

{table('final_controls')}

The initial always-on control is retained separately:

{table('controls')}

## Fresh DuckDB reference

Anonymous 5%-write workload only, same open-loop harness, three rotating rounds. This preserves the historical reference interface and does not compare idempotent receipt semantics or broad SQL capability parity.

{table('final_reference')}

The initial trial/reference runs are preserved in the linked raw report and not pooled into final comparisons.

## Initial baseline evidence

Four exploratory 0.3.4 cases ran before implementation. They motivated the change, have only one round, and are not pooled into confirmation.

{table('exploratory_baseline')}

The initial always-on same-binary 0/8 ms retry trial is also preserved:

{table('confirmation')}

## Correctness and release checks

- 41 Rust tests pass in debug and release; format and Clippy pass, including the separately enabled fault-driver feature. The default-versus-opt-in regression proves no extra map and queued retry behavior at default.
- One deterministic paused writer proves a known retry and known conflict finish before writer release; publication visibility and pinned views are checked.
- Seven injected disk-full publication failures prove cached receipts cannot conceal poisoning; default recovery preserves original generations and whole batches.
- 56 exact publication cut cases (process exit / OS error, append / compaction, delta / checkpoint) and 22 metadata corruption cases pass on the current build.
- 32 concurrent process-kill cycles across 0/2/8/20 ms policies preserve all ACKs, whole-batch counts/sums, original generations, retries after a second reopen and full scrubs. These are live-filesystem failures, not physical power-loss certification.
- 500 differential SQL cases against each of DuckDB and SQLite pass. The 30K-row Parquet retry/backfill demo matches 42 DuckDB SQL results. {audit['retained_result_checks']} untimed retained scale/NYC results match, including the existing 100M-row store; original scale timings are preserved.
- {audit['completed_cases']} retained open-loop load cases / {audit['offered_operations']:,} offers / {audit['numpy_windows']:,} independent NumPy windows reconcile after reopen and full scrubs, including 48 final-build cases / 1,440,000 offers and the preserved initial trial. Eighteen additional embedded API comparisons check every receipt and full scrubs. Default executables contain no injection environment keys. Raw successes, failures, expiries and initial evidence remain available.

The release gate remains **failed**: repeated service cases still exceed 100 ms or lose offered operations. Faster confirmed retries do not solve new-write synchronization/checkpoint tails, retention, broad SQL coverage, access control, cancellation, distributed execution or long endurance.

## Outstanding work

Continue from this release without repeating completed suites. Profile the fresh-write synchronization/checkpoint tails and the embedded retry CPU path separately. Keep the optional lookup disabled by default until write controls and longer endurance establish its cost. The JSON-client overload screen does not prove the embedded engine's maximum capacity; the direct Rust probe isolates that narrower path. A future mixed workload with separate caller capacity can investigate retry starvation, while retaining the shared-worker failures above. Arrow/timestamp/NULL/schema/retention work remains outside this release. Any publication redesign must retain synchronized acknowledgments, original receipts, fail-closed poisoning and the exact crash/corruption checks before promotion.

## Reproduction and evidence

Build checks: `python benchmarks/checks_035.py --final`. After those finish, run `python benchmarks/run_035.py timed --final`, then `python benchmarks/direct_retry_compare.py`, then `python benchmarks/run_035.py correctness --final`, then `python benchmarks/report_035.py`. The runner refuses to replace existing order logs; retain each attempt and use a new log for repairs. Install the pinned comparison dependencies from the benchmark requirements. These scripts use task-local fixtures and isolated default/fault Cargo targets.

[Final build proof](benchmarks/rust-checks-035-final.json), [complete audit](benchmarks/retry-035-audit.json), [final timed order](benchmarks/timed-035-final-run-order.json), [correctness order](benchmarks/correctness-035-final-run-order.json), [final retry](benchmarks/retry-035-final-retry.json), [final controls](benchmarks/retry-035-final-controls.json), [final reference](benchmarks/retry-035-final-reference.json), [embedded API comparison](benchmarks/retry-035-direct.json), [trial proof](benchmarks/rust-checks-035.json), [trial order](benchmarks/timed-035-run-order.json), [trial confirmation](benchmarks/retry-035-confirmation.json), [burst](benchmarks/retry-035-burst.json), [trial controls](benchmarks/retry-035-controls.json), [trial reference](benchmarks/retry-035-reference.json), [initial baseline](benchmarks/retry-035-baseline.json), [live retry faults](benchmarks/retry-035-faults.json), [publication faults](benchmarks/publication-035-faults.json), [concurrent kills](benchmarks/group-035-recovery.json), [pipeline](portfolio/live-pipeline-035-results.json), [SQL differential](benchmarks/archive-035-verification.json), [retained checks](benchmarks/release-recheck-035.json), [baseline provenance](benchmarks/baseline-0.3.4-provenance.json), [prior policy experiment](PERFORMANCE_034.md).
'''
    (ROOT/'PERFORMANCE_035.md').write_text(document,encoding='utf-8')
    print(json.dumps({'cases':audit['completed_cases'],'offers':audit['offered_operations'],'status':audit['service_qualification']}))


if __name__=='__main__':
    main()
