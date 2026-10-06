"""Audit retained CAT4 evidence and regenerate the report/plots, without timings."""
import argparse
import hashlib
import json
import math
import statistics as st
from pathlib import Path

from report_v03 import audit
from report_031 import summaries

ROOT = Path(__file__).resolve().parents[1]
LABELS = {'baseline':'Kestrel 0.3.2', 'candidate':'Kestrel 0.3.3', 'duckdb':'DuckDB'}


def read(name):
    return json.loads((ROOT/'benchmarks'/name).read_text(encoding='utf-8'))


def pub_summary(report, size, variant):
    cases = [c for c in report['cases'] if c['prefill_receipt_count'] == size and c['variant'] == variant]
    assert len(cases) == 3
    return {'median_ms':st.median(st.median(c['raw_latency_ms']) for c in cases),
            'max_ms':max(max(c['raw_latency_ms']) for c in cases),
            'catalog_bytes':st.median(sum(c['raw_catalog_bytes']) for c in cases),
            'reopen_ms':st.median(c['reopen_ms'] for c in cases)}


def service_table(report, profile):
    lines = ['| Build/engine | Median success/s | Median run p99, ms | Run p99 range, ms | Failed/unexecuted offers | Zero-loss / 100 ms passes |',
             '|---|---:|---:|---:|---:|---:|']
    for r in summaries(report, profile):
        lines.append(f"| {LABELS[r['variant']]} | {r['median_rps']:.2f} | {r['median_p99']:.2f} | {r['p99_min']:.2f} - {r['p99_max']:.2f} | {r['loss']} / {r['offered']} | {r['slo_passes']} / 3 |")
    return '\n'.join(lines)


def plot(publication):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1,2,figsize=(11,5.8))
    fig.subplots_adjust(bottom=.27,top=.81,wspace=.32)
    fig.suptitle('Kestrel 0.3.3: less catalog rewriting for new retry IDs',fontsize=15,weight='bold')
    for axis,field,title in [(axes[0],'catalog_bytes','Catalog bytes for 96 appends (MB)'),
                              (axes[1],'median_ms','Median of run median append latency (ms)')]:
        for offset,variant in [(-.19,'baseline'),(.19,'candidate')]:
            values = [pub_summary(publication,s,variant)[field]/(1_000_000 if field=='catalog_bytes' else 1) for s in [0,10000,50000]]
            bars = axis.bar([n+offset for n in range(3)],values,width=.36,
                            label=LABELS[variant],color='#8395a7' if variant=='baseline' else '#247765')
            for b,v in zip(bars,values):
                axis.text(b.get_x()+b.get_width()/2,v+max(values)*.025,f'{v:.2f}',ha='center',fontsize=8)
        axis.set_xticks(range(3),['0','10,000','50,000'])
        axis.set_xlabel('Retained receipt IDs before new appends')
        axis.set_title(title);axis.set_ylim(0,axis.get_ylim()[1]*1.2)
        axis.spines[['right','top']].set_visible(False)
    axes[0].legend(fontsize=9)
    fig.text(.5,.035,'3 alternating fresh runs/build/size | 96 identified 100-row appends/run | sync-before-ACK retained\nSetup, maintenance and reopen excluded from append timers; maintenance catalog bytes excluded from bars.\nShared Windows desktop. Checkpoint/fsync stalls remain; this is not a production service qualification.',ha='center',fontsize=9)
    for ext in ['png','svg']:
        fig.savefig(ROOT/'portfolio'/f'perf-033-publication.{ext}',dpi=160,bbox_inches='tight')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser();parser.add_argument('--plot',action='store_true');args = parser.parse_args()
    build, base = read('rust-checks-033.json'), read('baseline-0.3.2-provenance.json')
    final, mixed, receipts = read('perf-033-final.json'),read('perf-033-interleaved.json'),read('perf-033-receipts.json')
    publication, core = read('publication-033-paired.json'),read('perf-033-core.json')
    fields = ('variant','round','profile','clients','offered_rps','scheduled_seconds')
    proof = {'final':audit(final,11), 'interleaved':audit(mixed,18,key_fields=fields),
             'receipts':audit(receipts,12,key_fields=fields)}
    assert final['bridge_sha256'] == build['bridge_sha256']
    for r in [mixed,receipts]:
        assert r['binary_sha256']['candidate'] == build['bridge_sha256']
        assert r['binary_sha256']['baseline'] == base['baseline_binary_sha256']['kestrel-stress.exe']
        for c in r['cases']:
            assert c['host_telemetry']['error'] is None and len(c['host_telemetry']['samples']) >= 3
            if c['variant'] == 'candidate':
                assert 1 <= c['live_state_before_reopen']['catalog_chain_files'] <= 32
    for c in receipts['cases']:
        assert c['seed_replay_passed'] and c['final_receipt_count'] == 50_000 + c['reconciliation']['published_batches']
    for name,field in [('publication-probe','publication_probe_sha256'),('receipt-seed','receipt_seed_sha256')]:
        r = publication if name=='publication-probe' else receipts
        hashes = r['binary_sha256'] if name=='publication-probe' else r['seed_binary_sha256']
        assert hashes['candidate'] == build[field]
        assert hashes['baseline'] == base['baseline_binary_sha256'][name+'.exe']
    assert publication['probe_source_sha256'] == build['source_sha256']['examples/publication_probe.rs'] == base['new_probe_source_sha256']
    assert receipts['seed_source_sha256'] == build['source_sha256']['examples/receipt_seed.rs'] == base['new_seed_source_sha256']
    assert len(publication['cases']) == 18 and not publication['failed_cases']
    keys = {(c['variant'],c['round'],c['prefill_receipt_count']) for c in publication['cases']}
    assert len(keys) == 18
    for c in publication['cases']:
        assert c['rows_and_sum_match'] and c['reopen_retry_and_full_scrub_passed']
        assert len(c['raw_latency_ms']) == len(c['raw_catalog_bytes']) == 96
        assert c['after']['rows'] == c['prefill_receipt_count'] + 9600
        assert c['after']['recorded_batch_ids'] == c['prefill_receipt_count'] + 96
        if c['variant'] == 'candidate':
            assert c['after']['catalog_chain_files'] <= 32
            p = c['after']['publication_profile'];b = c['before']['publication_profile']
            assert p['catalog_bytes_published']-b['catalog_bytes_published'] >= sum(c['raw_catalog_bytes'])
            assert p['catalog_deltas']+p['catalog_checkpoints'] == p['completed']
    assert core['binary_sha256']['candidate'] == build['cli_sha256']
    assert core['binary_sha256']['baseline'] == base['baseline_binary_sha256']['kestrel.exe']
    expected = None
    for c in core['cases']:
        assert c['version'] == {'baseline':'0.3.2','candidate':'0.3.3'}[c['variant']] and c['verified_bytes'] == 24_000_000
        rows = {q['sql']:q['result']['rows'] for q in c['queries']}
        if expected is None:expected = rows
        assert rows == expected
        for q in c['queries']:
            assert len(q['samples_us']) == 31 and st.median(q['samples_us']) == q['median_us']
            assert sorted(q['samples_us'])[math.ceil(31*.95)-1] == q['p95_us']
    assert len(core['cases']) == 6
    faults = read('publication-033-faults.json')
    assert faults['binary_sha256'] == build['bridge_sha256'] and faults['fault_driver_sha256'] == build['fault_driver_sha256']
    assert len(faults['cut_points']) == 56 and len(faults['corruption_cases']) == 22
    assert all(c['original_receipts_preserved'] and c['atomic_rows_and_sum'] and c['retry_deduplication_passed'] and c['full_scrub_passed'] for c in faults['cut_points'])
    assert all(c['rejected'] for c in faults['corruption_cases'])
    recovery = read('perf-033-recovery.json');compat = read('format-033.json')
    assert len(recovery['cycles']) == 24 and all(c['sum_and_full_scrub_passed'] and c['retry_deduplication_passed'] for c in recovery['cycles'])
    assert compat['legacy_catalog_read'] and compat['cat3_catalog_read_and_upgrade'] and compat['cat3_binary_rejects_cat4']
    differential = read('archive-verification-033.json')
    assert differential['binary_sha256'] == build['cli_sha256'] and differential['queries_checked_against_each_reference'] == 500
    assert all(q['passed'] for q in differential['queries'])
    assert read('release-recheck-033.json')['all_retained_results_match']
    demo = json.loads((ROOT/'portfolio/live-pipeline-033-results.json').read_text())
    assert demo['exact_sql_cases_against_duckdb'] == 42 and demo['replayed_sources_not_duplicated']
    proof.update(publication={'completed_cases':18,'raw_append_timings':1728,'reopen_retry_and_scrub_passed':True},
        cut_points={'cases_passed':56,'corruption_cases_rejected':22,'test_only_feature':True,'physical_power_loss_tested':False},
        core={'cases':6,'sql_cases':36,'timings_checked':1116,'all_results_equal':True})
    offered = sum(proof[k]['offered_operations'] for k in ['final','interleaved','receipts'])
    assert offered == 800000
    targets = [c for r in [mixed,receipts] for c in r['cases'] if c['variant'] == 'candidate']
    proof['service_target_passed'] = all(c['unsuccessful_or_unexecuted'] == 0 and c['latency_ms']['p99'] <= 100 for c in targets)
    proof['service_target'] = 'all repeated candidate mixed/scan and retained-receipt mixed/write runs: zero loss, p99 <=100 ms'
    (ROOT/'benchmarks/perf-033-audit.json').write_text(json.dumps(proof,indent=2)+'\n')
    rows = ['| Retained IDs | Build | Median of run medians, ms | Worst append, ms | Catalog MB for 96 appends | Median reopen, ms |','|---:|---|---:|---:|---:|---:|']
    for size in [0,10000,50000]:
        for v in ['baseline','candidate']:
            s = pub_summary(publication,size,v)
            rows.append(f"| {size} | {LABELS[v]} | {s['median_ms']:.3f} | {s['max_ms']:.3f} | {s['catalog_bytes']/1_000_000:.3f} | {s['reopen_ms']:.3f} |")
    a,b = [pub_summary(publication,50000,v) for v in ['baseline','candidate']]
    sweep = ['| Profile | Clients | Offers/s | Seconds | Success/s | p99, ms | Failed/unexecuted |','|---|---:|---:|---:|---:|---:|---:|']
    for c in final['cases']:
        sweep.append(f"| {c['profile']} | {c['clients']} | {c['offered_rps']} | {c['scheduled_seconds']} | {c['successful_rps_in_arrival_window']:.2f} | {c['latency_ms']['p99']:.2f} | {c['unsuccessful_or_unexecuted']} |")
    core_rows = ['| Query | 0.3.2 median of run medians, ms | 0.3.3 median of run medians, ms |','|---|---:|---:|']
    for q in core['cases'][0]['queries']:
        values = [st.median(next(x['median_us'] for x in c['queries'] if x['name'] == q['name'])/1000 for c in core['cases'] if c['variant'] == v) for v in ['baseline','candidate']]
        core_rows.append(f"| {q['name']} | {values[0]:.4f} | {values[1]:.4f} |")
    text = '\n'.join(['# KestrelSQL 0.3.3: bounded receipt deltas and checkpoints','',
        f"At 50,000 retained retry IDs, 96 new 100-row appends wrote {a['catalog_bytes']/1_000_000:.2f} MB of catalogs in 0.3.2 and {b['catalog_bytes']/1_000_000:.2f} MB in 0.3.3 ({(1-b['catalog_bytes']/a['catalog_bytes'])*100:.2f}% fewer bytes). Median-of-run-median append latency was {a['median_ms']:.3f} versus {b['median_ms']:.3f} ms. These three alternating runs measure a focused improvement; service results and failures below remain separate.",'',
        '## Format and acknowledgment contract','',
        'CAT4 stores a full current segment list and either the complete receipt map (checkpoint) or only new receipts with a reference to the previous committed catalog (delta). At most 32 catalog files participate in recovery. The next publication after that bound writes a checkpoint; compactions also consume chain slots. Empty ledgers use checkpoints directly. New writes do not clone the committed in-memory ledger; checkpoints serialize borrowed old/new maps.','',
        'Segments still use SEG2. Buffer flush, segment sync, catalog sync and atomic rename remain before successful return/ACK. Recovery checks each envelope, schema, filename/generation, strictly earlier parent, receipt generation, uniqueness and total ID budget. Missing, truncated or corrupt dependencies fail closed without falling back to an older committed catalog. Reclaim retains every current dependency; pinned readers retain payloads separately.','',
        '**Upgrade boundary:** reads CAT2/CAT3/CAT4; the first successful write creates CAT4. Older releases reject CAT4. There is no downgrade writer/converter. Work on a copy for an upgrade evaluation. This remains an experimental format, with physical power loss and Windows directory-entry durability unqualified.','',
        'This is a checkpointed chain of immutable catalog generations, not an append-in-place WAL. The snapshot/edit design is informed by [RocksDB MANIFEST](https://github.com/facebook/rocksdb/wiki/MANIFEST). [SQLite WAL](https://www.sqlite.org/wal.html) separately documents commit/checkpoint durability tradeoffs. Kestrel retains its existing file-sync acknowledgment boundary; these systems do not establish Kestrel correctness.','',
        '## Sequential durable publication','',
        'Fresh prefill of 0, 10K or 50K one-row receipt batches in one publication; then 96 identified 100-row appends. Three runs/build/size, old/new order alternates. Append timings exclude prefill, stats, maintenance, full scrubs and reopen. Every 32 appends the probe compacts/reclaims outside the append timer. Catalog byte totals below cover appends, excluding those three maintenance catalogs and initial prefill; stage profiles include maintenance. All raw samples are retained.','',
        '\n'.join(rows),'','![Publication comparison](portfolio/perf-033-publication.png)','',
        'Checkpoint commits still rewrite the full ledger and can have long tails. Small-file synchronization/rename stalls also remain. Shared-desktop absolute timings vary; compare the fresh paired builds, not earlier release timings. Reopen validates up to 32 catalogs and may cost more. The 100K receipt ceiling remains and no IDs are evicted. Long unique-ID endurance remains unqualified.','',
        '## Concurrent service with 50K retained IDs','',
        'Each fresh fixture has 1M standard rows and 50K identified seed batches. New appends also carry unique IDs. 64 clients, 2,000 offers/s, 15 seconds, three alternating rounds/build. Mixed has 5% writes; write profile has 25% writes. Each write is a durable 100-row batch. This specifically includes receipt maintenance rather than assuming anonymous-ingest performance applies. Every acknowledged batch and 20 independent NumPy windows per case reconcile after reopen; seed IDs replay with their original receipt generation.','',
        service_table(receipts,'mixed'),'',service_table(receipts,'write'),'','## Anonymous mixed and generic scans','',
        'Three rotated runs/engine, fresh 1M fixtures: mixed at 2,000/s for 15 seconds (5% appends); scans at 200/s for eight seconds (10% appends). DuckDB is the fresh reference in this focused release; the preceding six-engine comparison remains historical.','',
        service_table(mixed,'mixed'),'',service_table(mixed,'scan'),'','## Complete candidate sweep','',
        '\n'.join(sweep),'',
        f"The repeated zero-loss / 100 ms target across candidate mixed, scan and receipt write cases {'passed locally' if proof['service_target_passed'] else 'failed'}. Even passing short local targets would not establish production readiness. All loss/expiry/errors and slow cases are retained. Latency starts at scheduled arrival and percentiles describe successes including drain; throughput counts successes in the arrival window. Queue: 256 slots, two-second expiry, eight-second connection/statement deadlines. Whole-host CPU/memory observations do not identify a storage-stall cause.",'',
        '## Core query regression checks','',
        'Original 0.3.2 release CLI versus final default-feature 0.3.3 CLI, one thread, three fresh alternating 1M-row archives per build, three warmups and 31 samples/query. All 36 query results match and every payload passes a full scrub.','',
        '\n'.join(core_rows),'','## Correctness and fault evidence','',
        '- 35 Rust tests pass in debug and release; formatting and Clippy warnings-as-errors pass. New tests cover checkpoint/reclaim/reopen, all original receipt generations, damaged chain semantics and a real pending-file creation failure.',
        '- 56 exact cut-point cases pass: seven points, process exit and injected disk-full OS error, append/compaction and delta/checkpoint. A separate feature-enabled driver fails before/after segment writes/sync, catalog writes/sync and publication. Default binaries recover. All original receipts, atomic rows/sums, retry decisions and full scrubs pass. Injected errors poison the writer while the old pinned view stays readable. This is not actual device exhaustion or physical power loss.',
        '- 22 additional corruption cases reject every truncated envelope-header prefix, selected body truncations, excess chain depth and duplicate JSON receipt keys. Ten semantic/dependency corruption cases are also in the Rust regression.',
        '- 24 random-delay forced-kill/retry cycles pass acknowledged data, atomic batches, exact sums and full scrubs. 500 fresh queries match each of DuckDB and SQLite; the Parquet replay/backfill demo passes 42 exact checks; 153 retained large/real-data queries match, including 100M-row archives.',
        '- CAT2/CAT3 reads, CAT4 upgrade, original CAT3 receipt generations and older-binary rejection pass. Payload format remains SEG2.',
        f'- Audit covers 41 stress cases, {offered:,} offers and 820 independent NumPy windows, plus 1,728 append timings and 1,116 core query timings. No compilation, plotting, packaging or other heavy job overlapped timed workloads. All task-owned bridge/reference processes stop after each comparison.','',
        '## Reproduce','',
        'The first retained-receipt service setup failed before any timed offers: a preparation-script path variable was reused and provenance JSON overwrote the copied baseline seed executable. It was restored from the isolated build, provenance was regenerated with distinct variables, and executable headers were checked before the accepted runs. Completed publication/core/anonymous comparisons were unaffected. [Setup failure evidence](benchmarks/perf-033-receipt-setup-failure.json) is excluded from speed measurements.','',
        'Build historical and candidate crates in separate target directories. The added publication and seed probe sources are identical in both crates and their hashes are recorded. Run commands sequentially after installing pinned benchmark dependencies.','',
        '```powershell','cargo test --release --locked','cargo build --release --locked --bins --example publication_probe --example receipt_seed',
        'python benchmarks/publication_compare.py --baseline bin/baseline-0.3.2/publication-probe.exe --candidate bin/publication-probe.exe --output benchmarks/publication-033-paired.json',
        'python benchmarks/receipt_service_compare.py --baseline bin/baseline-0.3.2/kestrel-stress.exe --candidate bin/kestrel-stress.exe --baseline-seed bin/baseline-0.3.2/receipt-seed.exe --candidate-seed bin/receipt-seed.exe --output benchmarks/perf-033-receipts.json',
        'python benchmarks/report_033.py --plot','```','',
        'Fault driver: build `cargo build --release --locked --features fault-injection --example publication_fault_probe` in a separate target directory. Default shipped CLI/bridge use no features and contain no failure environment hooks. Test-only driver is labeled in `bin/test-only`. Source and binary hashes: [build proof](benchmarks/rust-checks-033.json), [baseline provenance](benchmarks/baseline-0.3.2-provenance.json).','',
        'Evidence: [publication timings](benchmarks/publication-033-paired.json), [initial baseline](benchmarks/publication-033-baseline-initial.json), [cut points](benchmarks/publication-033-faults.json), [receipt loads](benchmarks/perf-033-receipts.json), [mixed/scans](benchmarks/perf-033-interleaved.json), [full sweep](benchmarks/perf-033-final.json), [core](benchmarks/perf-033-core.json), [audit](benchmarks/perf-033-audit.json), [random kills](benchmarks/perf-033-recovery.json), [format](benchmarks/format-033.json).','',
        'Archive remains a restricted BIGINT aggregate engine. Arrow/types/NULL/decimal semantics, backups/retention/orphan cleanup, resource governance, long endurance, Linux execution, power-loss behavior and replication remain work. No universal superiority, production certification or Facebook-scale qualification is established.',''])
    (ROOT/'PERFORMANCE_033.md').write_text(text,encoding='utf-8')
    if args.plot:plot(publication)
    print(json.dumps({'stress_cases':41,'offered_requests':offered,'service_target_passed':proof['service_target_passed'],'audit':'benchmarks/perf-033-audit.json'},indent=2))


if __name__ == '__main__':
    main()
