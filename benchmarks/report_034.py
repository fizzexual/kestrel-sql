"""Audit all coalescing trials, including failures, and regenerate the policy report."""
import argparse
import hashlib
import json
import statistics as st
from pathlib import Path

from report_v03 import audit

ROOT = Path(__file__).resolve().parents[1]
DATASETS = {'tuning':12, 'confirmation':27, 'reference':9, 'boundaries':9, 'soak':2}
LABELS = {'baseline':'0.3.3 default', 'delay0':'0.3.4 / 0 ms', 'delay2':'0.3.4 / 2 ms', 'delay8':'0.3.4 / 8 ms', 'duckdb':'DuckDB'}


def read(relative):
    return json.loads((ROOT/relative).read_text(encoding='utf-8'))


def optional_median(values):
    present = [v for v in values if v is not None]
    return st.median(present) if present else None


def rows(report):
    for scenario in dict.fromkeys(c['scenario'] for c in report['cases']):
        for variant in report['policy_ms']:
            cases = [c for c in report['cases'] if c['scenario']==scenario and c['variant']==variant]
            if not cases:
                continue
            p99 = [c['latency_ms']['p99'] for c in cases]
            groups = [c.get('load_group_commits',0) for c in cases]
            collection_means = []
            for case in cases:
                if case['engine']=='kestrel' and case['variant']!='baseline':
                    before,after = case['ingest_state_before_load'],case['live_state_before_reopen']['ingest']
                    count = after['collected_groups']-before['collected_groups']
                    collection_means.append((after['collection_total_ms']-before['collection_total_ms'])/count if count else 0)
            yield {'scenario':scenario,'variant':variant,'rounds':len(cases),
                'median_rps':st.median(c['successful_rps_in_arrival_window'] for c in cases),
                'median_p99_ms':st.median(p99),'min_p99_ms':min(p99),'max_p99_ms':max(p99),
                'median_append_p99_ms':optional_median(c['append_latency_ms']['p99'] for c in cases),
                'lost_offers':sum(c['unsuccessful_or_unexecuted'] for c in cases),
                'offered_operations':sum(c['offered_operations'] for c in cases),
                'slo_passes':sum(c['unsuccessful_or_unexecuted']==0 and c['latency_ms']['p99']<=100 for c in cases),
                'median_group_commits':st.median(groups),
                'median_mean_collection_ms':st.median(collection_means) if collection_means else None,
                'median_batches_per_group':st.median(c.get('batches_per_durable_group',0) for c in cases)}


def table(report):
    lines = ['| Scenario | Policy / engine | Median success/s | Median p99, ms (range) | Median append p99, ms | Lost offers / total | Zero-loss / 100 ms passes |',
             '|---|---|---:|---:|---:|---:|---:|']
    for r in rows(report):
        append_p99 = 'n/a' if r['median_append_p99_ms'] is None else f"{r['median_append_p99_ms']:.2f}"
        lines.append(f"| {r['scenario']} | {LABELS[r['variant']]} | {r['median_rps']:.2f} | {r['median_p99_ms']:.2f} ({r['min_p99_ms']:.2f}–{r['max_p99_ms']:.2f}) | {append_p99} | {r['lost_offers']} / {r['offered_operations']} | {r['slo_passes']} / {r['rounds']} |")
    return '\n'.join(lines)


def plot(report):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    summaries = list(rows(report))
    fig, axes = plt.subplots(1,2,figsize=(12,6))
    fig.subplots_adjust(bottom=.28,top=.81,wspace=.32)
    fig.suptitle('Kestrel 0.3.4: explicit group-commit policy tradeoffs',weight='bold',fontsize=15)
    scenarios = ['anonymous-mixed','receipt-mixed','receipt-write']
    colors = ['#8395a7','#336f9b','#247765']
    for axis,field,title in [(axes[0],'median_rps','Median successful requests/s'),(axes[1],'median_p99_ms','Median run p99 latency (ms)')]:
        for i,variant in enumerate(['delay0','delay2','delay8']):
            values = [next(r[field] for r in summaries if r['scenario']==s and r['variant']==variant) for s in scenarios]
            axis.bar([n+(i-1)*.25 for n in range(3)],values,width=.23,label=LABELS[variant],color=colors[i])
        axis.set_xticks(range(3),['Anonymous\nmixed','50K IDs\nmixed','50K IDs\nwrite'])
        axis.set_title(title)
        axis.spines[['top','right']].set_visible(False)
    axes[0].axhline(2000,color='#444',linestyle='--',linewidth=1)
    axes[0].legend(fontsize=9)
    axes[1].axhline(100,color='#444',linestyle='--',linewidth=1)
    fig.text(.5,.035,'Same binary | 3 rotated fresh runs/policy/scenario | 1M rows | 64 clients | 2,000 offers/s for 15s\n100-row sync-before-ACK writes. Percentiles cover successes; complete offer losses are in the report.\nShared Windows desktop. Timers do not bound filesystem stalls or establish production readiness.',ha='center',fontsize=9)
    for extension in ['png','svg']:
        fig.savefig(ROOT/'portfolio'/f'perf-034-policies.{extension}',dpi=160,bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plot',action='store_true')
    args = parser.parse_args()
    build = read('benchmarks/rust-checks-034.json')
    base = read('benchmarks/baseline-0.3.3-provenance.json')
    reports = {name:read(f'benchmarks/perf-034-{name}.json') for name in DATASETS}
    proof = {'version':'0.3.4','datasets':{},'summaries':{},'inherited_archive_checks':{}}
    for name,report in reports.items():
        proof['datasets'][name] = audit(report,DATASETS[name],key_fields=('variant','round','scenario'))
        assert report['binary_sha256']['candidate']==build['bridge_sha256']
        assert report['binary_sha256']['baseline']==base['baseline_binary_sha256']['kestrel-stress.exe']
        assert report['seed_binary_sha256']['candidate']==build['receipt_seed_sha256']
        for case in report['cases']:
            if case['engine']!='kestrel':
                continue
            after,before = case['live_state_before_reopen']['ingest'],case['ingest_state_before_load']
            assert after['flush_delay_ms']==(case['configured_group_delay_ms'] or 0)
            assert case['load_group_commits']==after['durable_group_commits']-before['durable_group_commits']
            assert 0<=after['queued_payload_bytes']<=64*1024*1024 and 1<=case['live_state_before_reopen']['catalog_chain_files']<=32
            assert case['host_telemetry']['error'] is None
            if case['variant']!='baseline':
                assert after['group_delay_ns']==after['flush_delay_ms']*1_000_000
                assert 1<=after['max_group_requests']<=64
            if case['scenario'].startswith('receipt-'):
                assert case['seed_replay_passed']
                assert case['final_receipt_count']==report['prefill_receipt_ids']+case['reconciliation']['published_batches']
        proof['summaries'][name] = list(rows(report))
    proof['completed_cases'] = sum(d['completed_cases'] for d in proof['datasets'].values())
    proof['offered_operations'] = sum(d['offered_operations'] for d in proof['datasets'].values())
    proof['unacknowledged_committed_batches_in_stress'] = sum(c['reconciliation']['unacknowledged_but_committed'] for report in reports.values() for c in report['cases'])
    assert (proof['completed_cases'],proof['offered_operations'])==(59,1_936_800)
    unchanged = ['src/archive.rs','src/query.rs','src/sql.rs','src/scale.rs','src/wal.rs','src/lib.rs','src/main.rs']
    for relative in unchanged:
        digest = hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
        assert digest == build['source_sha256'][relative] == base['core_source_sha256'][relative]
        proof['inherited_archive_checks'][relative] = digest
    proof['archive_evidence'] = 'Unchanged storage/query/WAL source; CAT4 cut points, corruption/format tests, 500-query differential and retained 100M/NYC checks are inherited from verification-v033.json, not re-executed or counted as fresh 0.3.4 checks.'
    recovery = read('benchmarks/group-034-recovery.json')
    assert recovery['binary_sha256']==build['bridge_sha256'] and len(recovery['cycles'])==32 and not recovery['failed_cases']
    for cycle in recovery['cycles']:
        assert all(cycle[k] for k in ['acknowledged_data_present','whole_batches_and_sums','original_receipt_generations_preserved','retry_exactly_once_after_second_reopen','full_scrubs_passed'])
    proof['concurrent_kill_cycles_passed'] = 32
    proof['unacknowledged_committed_batches_in_kill_cycles'] = sum(c['unacknowledged_committed_batches'] for c in recovery['cycles'])
    demo = read('portfolio/live-pipeline-034-results.json')
    assert demo['binary_sha256']==build['bridge_sha256'] and demo['engine_version']=='0.3.4'
    assert demo['configured_group_delay_ms']==8 and demo['exact_sql_cases_against_duckdb']==42
    assert demo['replayed_sources_not_duplicated'] and demo['changed_content_rejected']
    proof['delayed_parquet_pipeline_exact_sql_cases'] = 42
    proof['service_target_definition'] = 'Each policy must pass zero lost offers and successful scheduled-arrival p99 <=100 ms in all nine independent 2K/s confirmation cases (three rounds of anonymous mixed, receipt mixed and receipt write). Tuning, references, overload screens and one-minute cases are separate evidence.'
    proof['policy_target_passed'] = {variant:all(c['unsuccessful_or_unexecuted']==0 and c['latency_ms']['p99']<=100 for c in reports['confirmation']['cases'] if c['variant']==variant) for variant in ['delay0','delay2','delay8']}
    proof['service_target_passed_for_all_measured_policies'] = all(proof['policy_target_passed'].values())
    proof['service_qualification'] = 'failed; experimental optional tuning, production envelope unqualified' if not proof['service_target_passed_for_all_measured_policies'] else 'local short-workload target passed; production envelope still unqualified'
    write_summaries = {r['variant']:r for r in rows(reports['confirmation']) if r['scenario']=='receipt-write'}
    zero,eight = write_summaries['delay0'],write_summaries['delay8']
    proof['policy_decision'] = 'Keep zero delay as the default. Offer the explicit bounded window for measured application tuning; retain every initial and confirmed regression. No setting passes the repeated normal-load target.'
    (ROOT/'benchmarks/perf-034-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    grouping = ['| Scenario | Policy | Median durable groups | Median batches/group | Median run mean collection, ms |','|---|---|---:|---:|---:|']
    for r in rows(reports['confirmation']):
        grouping.append(f"| {r['scenario']} | {LABELS[r['variant']]} | {r['median_group_commits']:.0f} | {r['median_batches_per_group']:.2f} | {r['median_mean_collection_ms']:.3f} |")
    document = f'''# KestrelSQL 0.3.4: bounded group-commit policy experiment

The release adds an explicit coalescing window and group-collection diagnostics. In three independent 50K-ID / 25%-write confirmation rounds, the 8 ms policy's median success rate was {eight['median_rps']:.2f}/s versus {zero['median_rps']:.2f}/s at zero delay. Its median run p99 was {eight['median_p99_ms']:.2f} versus {zero['median_p99_ms']:.2f} ms, with {eight['lost_offers']} versus {zero['lost_offers']} lost offers out of 90,000 per policy. The initial tuning run regressed with 8 ms; other scenarios also have mixed results. The default remains **0 ms**. Every setting and failure is retained; no policy qualifies the repeated normal-load target.

## Contract and hypothesis

The 0.3.3 retained 50K-ID profiles spend most publication time in segment/catalog synchronization rather than preparation. Fewer publications might amortize those waits. [PostgreSQL WAL settings](https://www.postgresql.org/docs/18/runtime-config-wal.html) document the throughput/latency tradeoff of commit delays; Kestrel has a different immutable two-file publication design.

`LiveOptions.max_group_delay` allows 0..20 ms. One deadline starts when the writer receives its first request and never slides. It collects at most 64 requests; the existing 256-request / 64 MiB queue remains. A disconnected queue drains without a timer wait. Intentional collection waiting is bounded; scheduler, queued work, synchronization and compaction are not acknowledgment-time bounds. A single write and an exact retry can pay the full optional window. Statistics report exact configured nanoseconds, collection time, collected groups and maximum group requests. Readers receive the committed snapshot before ACK; flush, segment/catalog sync and atomic publication are unchanged.

## Initial tuning evidence

One fresh run per old build / new 0/2/8 ms setting and scenario. These runs informed a separate confirmation; they are not pooled to inflate its repetition count.

{table(reports['tuning'])}

## Independent policy confirmation

Same final 0.3.4 binary, 0/2/8 ms, three rotating rounds, fresh 1M-row fixtures, 64 clients, 2,000 offers/s, 15 seconds. Anonymous mixed uses 5% writes; receipt mixed and receipt write use 5% and 25% writes respectively with 50K initial retained IDs. Each append contains 100 rows. Fixture seed and full scrub are outside arrivals. The seed receipt replays with original generation 1. Every ACK reconciles after reopen; 20 NumPy windows/case and full payload scrubs pass.

{table(reports['confirmation'])}

![Policy comparisons](portfolio/perf-034-policies.png)

{'\n'.join(grouping)}

Group counts and batches/group show whether an explicit window actually changes publication frequency. Actual mean collection can exceed the configured window on this host; the counter includes collection execution and scheduling, and does not isolate an overshoot cause. A deadline prevents intentional sliding waits, but cannot ensure wall-clock wakeup. Whole-host observations and publication-stage counters are retained. Shared-desktop order rotation reduces one source of bias; these are descriptive measurements without controlled storage isolation or statistical confidence intervals.

## Fresh anonymous reference

0/8 ms policies and DuckDB, three rotated 15-second anonymous mixed runs. DuckDB uses its native Python binding, one thread per connection and 256 MB configured memory; Kestrel uses the Rust loopback test bridge. This is an aggregate workload with different API boundaries and SQL coverage. Earlier six-engine results remain historical in [HARD_TESTS.md](HARD_TESTS.md) and [PERFORMANCE_031.md](PERFORMANCE_031.md).

{table(reports['reference'])}

## Boundary and sustained checks

One fresh 8-second case/policy/scenario: single client at 500/s, 64-client 10K/s burst, and 64-client generic scans at 200/s. These are regression screens, not repeated qualification. Scans contain 10% appends. Single-client cases disclose the batching/serialization cost.

{table(reports['boundaries'])}

One fresh 60-second anonymous mixed case per 0/8 ms policy, 64 clients at 2K/s. This is one minute, not long endurance or distributed activity.

{table(reports['soak'])}

**Service qualification:** {proof['service_qualification']}. The target requires zero loss and successful scheduled-arrival p99 ≤100 ms in each policy's nine independent 2K/s confirmation cases; tuning, references, burst screens and the minute screen are separate evidence. Scheduled-arrival latency includes queueing; percentiles cover successes including drain. All failures, queue drops and two-second expiries are separate. Socket deadlines remain eight seconds. The user-visible server adapter remains test-only and unauthenticated.

## Correctness and evidence boundaries

- 38 Rust tests pass in debug/release; format and Clippy pass. New checks cover option limits, zero default, 64-request cap, closed-queue draining, concurrent receipts/retries, ACK snapshot visibility, pinned views and reopen scrubs.
- 32 new forced process-kill cycles: sixteen simultaneous producers, 0/2/8/20 ms policies and eight kill delays. Acknowledged data remains present; every recovered batch is whole; exact retry and original receipt generations survive a second reopen. Unknown unacknowledged commits are disclosed. These are live-filesystem process deaths, not physical power cuts.
- The 8 ms Parquet pipeline ingests 30K rows, replays both sources without duplication, rejects changed content under an existing ID, and matches 42 DuckDB SQL results.
- Storage, query planner, query kernels, original WAL and CLI source hashes exactly match 0.3.3. Its 56 exact publication-cut cases, 22 extra corruption rejections, format upgrades, 500-query differential and 100M/NYC checks are inherited evidence, not new 0.3.4 tests. CAT4/SEG2 are unchanged. The 0.3.3 writer reads 0.3.4 stores in the packaged smoke.
- {proof['completed_cases']} new stress cases / {proof['offered_operations']:,} offers; every retained raw sample, percentile and loss account is audited. No compilation or other task-heavy workload overlaps timed arrivals. Each task-owned bridge stops after its case.

The 100K receipt ceiling, checkpoint stalls, restricted BIGINT aggregate SQL, missing backup/retention/orphan cleanup, physical power loss and Windows directory-entry durability remain limits. No universal superiority, Facebook-scale or production-ready claim follows from this experiment.

## Reproduce

```powershell
cargo test --release --locked
cargo build --release --locked --bins --examples
python benchmarks/group_commit_compare.py --baseline bin/baseline-0.3.3/kestrel-stress.exe --candidate bin/kestrel-stress.exe --baseline-seed bin/baseline-0.3.3/receipt-seed.exe --candidate-seed bin/receipt-seed.exe --variants delay0,delay2,delay8 --rounds 3 --seconds 15 --output benchmarks/my-policy-confirmation.json
python benchmarks/group_commit_recovery.py --binary bin/kestrel-stress.exe --output benchmarks/my-policy-recovery.json
python benchmarks/live_pipeline_demo.py --binary bin/kestrel-stress.exe --group-delay-ms 8 --output portfolio/my-delayed-pipeline.json
python benchmarks/report_034.py --plot
```

Use the existing requirements in [stress_requirements.txt](benchmarks/stress_requirements.txt). Run timing suites serially. For the initial evidence use `--rounds 1 --variants baseline,delay0,delay2,delay8`; for fresh references use `--profiles anonymous-mixed --variants delay0,delay8,duckdb --rounds 3`; for boundary checks use `--profiles single-mixed,burst,scan --variants delay0,delay2,delay8 --rounds 1 --seconds 8`; for the minute screen use `--profiles anonymous-mixed --variants delay0,delay8 --rounds 1 --seconds 60`. Use new output paths to preserve retained evidence.

Reports: [tuning](benchmarks/perf-034-tuning.json), [confirmation](benchmarks/perf-034-confirmation.json), [reference](benchmarks/perf-034-reference.json), [boundaries](benchmarks/perf-034-boundaries.json), [minute screen](benchmarks/perf-034-soak.json), [sample audit](benchmarks/perf-034-audit.json), [concurrent recovery](benchmarks/group-034-recovery.json), [delayed pipeline](portfolio/live-pipeline-034-results.json), [build proof](benchmarks/rust-checks-034.json).
'''
    (ROOT/'PERFORMANCE_034.md').write_text(document,encoding='utf-8')
    if args.plot:
        plot(reports['confirmation'])
    print(json.dumps({'cases':proof['completed_cases'],'offers':proof['offered_operations'],'service_qualification':proof['service_qualification']}))


if __name__ == '__main__':
    main()
