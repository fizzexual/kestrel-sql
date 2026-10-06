"""Audit cost boundaries, failures, current checks and inherited evidence separately."""
import gzip
import hashlib
import json
import statistics
from pathlib import Path
from stress_compare import percentile
from report_035 import summary

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


def main():
    build = read('benchmarks/rust-checks-036.json')
    base = read('benchmarks/baseline-0.3.5-provenance.json')
    assert build['rust_tests'] == {'debug': 45, 'release': 45, 'passed': True}
    for relative, digest in build['source_sha256'].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
    original = (ROOT / 'benchmarks/baseline-0.3.5-source/src/archive.rs').read_text()
    current = (ROOT / 'src/archive.rs').read_text()
    def storage_and_query(text):
        return text[:text.index('impl BatchRecord {')] + text[text.index('/// An optional durable batch ID'):]
    assert storage_and_query(original) == storage_and_query(current)
    same_core = [p for p, digest in build['source_sha256'].items() if base['core_source_sha256'].get(p) == digest]
    profile = read('benchmarks/digest-036-profile.json')
    assert profile['all_domains_equal'] and len(profile['cases']) == 75
    assert profile['probe_sha256'] == hashlib.sha256((ROOT / 'benchmarks/digest_profile.rs').read_bytes()).hexdigest()
    direct = read('benchmarks/prepared-036-direct.json')
    assert direct['source_sha256'] == build['source_sha256']
    assert len(direct['cases']) == 30 and not direct['failed_cases']
    assert direct['candidate_probe_source_sha256'] == hashlib.sha256((ROOT / 'benchmarks/prepared_retry_inprocess.rs').read_bytes()).hexdigest()
    assert direct['baseline_binary_sha256'] == base['baseline_binary_sha256']['live-retry-inprocess.exe']
    audit = {'version': '0.3.6', 'rust_tests_each_mode': 45, 'cpu_digest_cases': 75, 'embedded_retry_cases': 30,
        'source_sha256': build['source_sha256'], 'unchanged_core_files': same_core,
        'archive_storage_and_query_outside_receipt_helper_byte_identical_to_035': True,
        'groups': {}, 'embedded_retry': {}, 'completed_open_loop_cases': 0, 'offered_operations': 0, 'numpy_windows': 0,
        'service_qualification': 'failed; prepared confirmed retries improve, production envelope unqualified',
        'historical_evidence': '0.3.5 proof/ZIP and previous query, publication, corruption, Parquet and large-scale timing evidence remain unchanged; not counted as fresh 0.3.6 cases'}
    direct_lines = ['| Callers | 0.3.5 ordinary calls/s | 0.3.6 ordinary calls/s | 0.3.6 prepared calls/s | Prepared / baseline | Baseline / prepared sampled p99 us |', '|---:|---:|---:|---:|---:|---:|']
    for clients in [1, 16, 64]:
        values = {}
        for variant in ['baseline', 'ordinary', 'prepared']:
            cases = [c for c in direct['cases'] if c['clients'] == clients and c['variant'] == variant]
            assert len(cases) == 3
            values[variant] = {'median_calls_per_second': statistics.median(c['successful_rps_in_window'] for c in cases),
                'calls_per_second_range': [min(c['successful_rps_in_window'] for c in cases), max(c['successful_rps_in_window'] for c in cases)],
                'median_sampled_run_p99_us': statistics.median(c['sampled_latency_us']['p99'] for c in cases)}
        ratio = values['prepared']['median_calls_per_second'] / values['baseline']['median_calls_per_second']
        audit['embedded_retry'][str(clients)] = {**values, 'prepared_ratio': ratio}
        direct_lines.append(f"| {clients} | {values['baseline']['median_calls_per_second']:,.0f} | {values['ordinary']['median_calls_per_second']:,.0f} | {values['prepared']['median_calls_per_second']:,.0f} | {ratio:.2f}x | {values['baseline']['median_sampled_run_p99_us']:.2f} / {values['prepared']['median_sampled_run_p99_us']:.2f} |")
    for case in direct['cases']:
        assert case['all_receipts_valid'] and case['no_publications_during_load'] and case['full_scrub_passed']
        assert 0 < case['completed_in_window'] <= case['successful_calls']
        assert case['successful_rps_in_window'] == case['completed_in_window'] / case['scheduled_seconds']
        assert case['ingest_after']['duplicate_batches'] - case['ingest_before']['duplicate_batches'] == case['successful_calls']
        assert case['ingest_after']['fast_retry_hits'] - case['ingest_before']['fast_retry_hits'] == case['successful_calls']
        if case['variant'] != 'baseline':
            assert case['caller_retained_payload_bytes'] == 2400 and case['preparation_ns'] > 0
            assert case['ingest_after']['prepared_retry_hits'] - case['ingest_before']['prepared_retry_hits'] == (0 if case['variant'] == 'ordinary' else case['successful_calls'])
            assert case['successful_rps_including_one_preparation'] == case['completed_in_window'] / (case['scheduled_seconds'] + case['preparation_ns'] / 1e9)
        with gzip.open(ROOT / 'benchmarks' / case['raw_latency_samples'], 'rt') as stream: raw = json.load(stream)
        assert len(raw) == case['sampled_calls']
        assert case['sampled_latency_us'] == {name: percentile(raw, p)/1000 for name, p in [('p50', .5), ('p95', .95), ('p99', .99)]}
    each = [c for c in direct['cases'] if c['variant'] == 'prepare_each']
    assert len(each) == 3
    audit['prepare_each'] = {'median_calls_per_second': statistics.median(c['successful_rps_in_window'] for c in each),
        'median_sampled_run_p99_us': statistics.median(c['sampled_latency_us']['p99'] for c in each)}
    audit['one_time_preparation_median_ns'] = statistics.median(c['preparation_ns'] for c in direct['cases'] if c['variant'] == 'prepared')
    intervals = []
    for label, filename, count in [('retry_control', 'prepared-036-retry-control.json', 6), ('write_controls', 'prepared-036-write-controls.json', 12)]:
        report = read('benchmarks/' + filename)
        assert len(report['cases']) == count and not report['failed_cases']
        assert report['binary_sha256']['candidate'] == build['bridge_sha256']
        assert report['binary_sha256']['baseline'] == base['baseline_binary_sha256']['kestrel-stress.exe']
        for case in report['cases']:
            start = case['arrival_start_monotonic_ns']
            intervals.append((start, start + int(case['including_drain_seconds'] * 1e9)))
            with gzip.open(ROOT / 'benchmarks' / case['raw_samples_file'], 'rt', encoding='utf-8') as stream: samples = [json.loads(line) for line in stream]
            good = [s for s in samples if s['ok']]
            assert len(samples) + case['queue_dropped'] + case['queue_expired'] == case['offered_operations']
            assert len(good) == case['successful_operations']
            assert len({s['sequence'] for s in samples}) == len(samples)
            assert all(0 <= s['sequence'] < case['offered_operations'] for s in samples)
            assert len(set(case['expired_sequences'])) == case['queue_expired']
            assert not set(case['expired_sequences']).intersection(s['sequence'] for s in samples)
            assert case['offered_operations'] - len(good) == case['unsuccessful_or_unexecuted']
            latencies = [s['latency_ms'] for s in good]
            assert case['latency_ms'] == {'p50': percentile(latencies, .5), 'p95': percentile(latencies, .95), 'p99': percentile(latencies, .99), 'max': max(latencies)}
            assert case['completed_in_arrival_window'] == sum(s['finished_ns'] <= start + int(case['scheduled_seconds'] * 1e9) for s in good)
            assert case['successful_rps_in_arrival_window'] == case['completed_in_arrival_window'] / case['scheduled_seconds']
            case['operation_call_ms'] = {kind: {'p99': percentile([s['service_ms'] for s in good if s['operation'] == kind], .99)} for kind in ['append', 'query', 'replay']}
            oracle = case['reconciliation']
            assert oracle['all_acknowledged_batches_present'] and oracle['batch_atomicity_and_sums'] and oracle['numpy_reference_windows'] == 20
            assert oracle['full_kestrel_scrub']['verified_bytes'] == oracle['rows'] * 24
            after = case['live_state_before_reopen']['ingest']
            assert after['queued_payload_bytes'] == 0 and after['max_group_requests'] <= 64
            assert not after['writer_poisoned'] and not after['writer_stopped']
            assert case['live_state_before_reopen']['retained_page_cache_bytes'] <= 32 * 1024 * 1024
            if case['version'] == '0.3.6': assert after['prepared_retry_hits'] == 0
            if label == 'retry_control': assert case['known_receipts_after_reopen'] == 128 and case['seed_replay_passed']
            audit['completed_open_loop_cases'] += 1
            audit['offered_operations'] += case['offered_operations']
            audit['numpy_windows'] += 20
        for scenario in sorted({c['scenario'] for c in report['cases']}):
            for variant in sorted({c['variant'] for c in report['cases'] if c['scenario'] == scenario}):
                matching = [c for c in report['cases'] if (c['scenario'], c['variant']) == (scenario, variant)]
                value = summary(matching)
                stages = ['prepare', 'segment_write', 'segment_sync', 'catalog_encode', 'catalog_write', 'catalog_sync', 'catalog_rename']
                totals = {stage: sum(c['live_state_before_reopen']['publication_profile'][stage]['total_ms'] - c['publication_profile_before_load'][stage]['total_ms'] for c in matching) for stage in stages}
                assert all(v >= 0 for v in totals.values())
                value['publication_stage_totals_ms'] = totals
                value['synchronization_share_percent'] = (totals['segment_sync'] + totals['catalog_sync']) / sum(totals.values()) * 100
                audit['groups'][label + '/' + scenario + '/' + variant] = value
    intervals.sort()
    assert all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:]))
    assert (audit['completed_open_loop_cases'], audit['offered_operations'], audit['numpy_windows']) == (18, 540000, 360)
    faults = read('benchmarks/prepared-036-faults.json')
    assert len(faults['cases']) == 15 and not faults['failed_cases']
    assert faults['binary_sha256'] == build['bridge_sha256'] and faults['driver_sha256'] == build['live_retry_driver_sha256']
    assert all(all(c[f] for f in ['recovery_original_receipt', 'atomic_rows_and_sum', 'retry_deduplication', 'full_scrub']) for c in faults['cases'])
    crashes = read('benchmarks/group-036-recovery.json')
    assert len(crashes['cycles']) == 32 and not crashes['failed_cases'] and crashes['binary_sha256'] == build['bridge_sha256']
    assert all(all(c[f] for f in ['acknowledged_data_present', 'whole_batches_and_sums', 'original_receipt_generations_preserved', 'retry_exactly_once_after_second_reopen', 'full_scrubs_passed']) for c in crashes['cycles'])
    differential = read('benchmarks/archive-036-verification.json')
    assert differential['queries_checked_against_each_reference'] == 500 and differential['binary_sha256'] == build['cli_sha256']
    audit.update(prepared_fault_cases=15, concurrent_kill_cycles=32, differential_cases_each_reference=500)
    timed = read('benchmarks/timed-036-run-order.json')
    correct = read('benchmarks/correctness-036-run-order.json')
    assert len(timed) == 2 and len(correct) == 3 and all(r['returncode'] == 0 for r in timed + correct)
    for records in [timed, correct]:
        assert all(a['completed_monotonic_ns'] <= b['started_monotonic_ns'] for a, b in zip(records, records[1:]))
        for record in records:
            for filename, digest in record['harness_sha256'].items(): assert hashlib.sha256((ROOT / 'benchmarks' / filename).read_bytes()).hexdigest() == digest
    order = direct['run_order']
    assert all(a['completed_at_utc'] <= b['started_at_utc'] for a, b in zip(order, order[1:]))
    assert profile['timing_completed_at_utc'] <= build['build_run_order'][0]['started_at_utc']
    assert build['build_run_order'][-1]['completed_at_utc'] <= direct['build_run_order'][0]['started_at_utc']
    assert direct['build_run_order'][-1]['completed_at_utc'] <= order[0]['started_at_utc']
    assert order[-1]['completed_at_utc'] <= timed[0]['started_at_utc']
    assert timed[-1]['completed_at_utc'] <= correct[0]['started_at_utc']
    audit.update(timed_database_workloads_no_overlap=True, compilation_and_correctness_outside_timed_loads=True)
    (ROOT / 'benchmarks/prepared-036-audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    controls = ['| Scenario / variant | Median req/s | Median run p99 ms | p99 range ms | Loss / offers | Runs zero loss + p99 <=100ms |', '|---|---:|---:|---:|---:|---:|']
    for label, value in audit['groups'].items():
        lo, hi = value['run_p99_range_ms']
        controls.append(f"| {label} | {value['median_successful_rps']:.2f} | {value['median_run_p99_ms']:.2f} | {lo:.2f}-{hi:.2f} | {value['unsuccessful_or_unexecuted']:,} / {value['offered_operations']:,} | {value['zero_loss_p99_100ms_runs']} / 3 |")
    operation_lines = ['| Scenario / variant | Median new-append arrival p99 ms | Median replay call p99 ms | Segment/catalog sync share of publication stages |', '|---|---:|---:|---:|']
    for label, value in audit['groups'].items():
        replay = '-' if value['median_replay_call_p99_ms'] is None else f"{value['median_replay_call_p99_ms']:.2f}"
        operation_lines.append(f"| {label} | {value['median_append_p99_ms']:.2f} | {replay} | {value['synchronization_share_percent']:.2f}% |")
    document = f'''# KestrelSQL 0.3.6: reusable immutable embedded batches

`PreparedBatch` hashes an owned, validated payload once; `LiveArchive::append_prepared(&batch)` can reuse that fingerprint against the optional confirmed receipt index. On three rotating comparisons, 64 callers complete a median {audit['embedded_retry']['64']['prepared']['median_calls_per_second']:,.0f} confirmed retry calls/s versus {audit['embedded_retry']['64']['baseline']['median_calls_per_second']:,.0f} for the frozen 0.3.5 ordinary API ({audit['embedded_retry']['64']['prepared_ratio']:.2f}x). These calls acknowledge already committed data and ingest **zero new rows during timing**. This is an embedded replay optimization, with explicit preparation costs; it does not establish new-write capacity, network throughput, production readiness or superiority to other databases.

![Embedded reuse gain and variable ordinary protocol controls](portfolio/perf-036-prepared.png)

## Contract and cost boundaries

The public type has private immutable state behind Arc. Construction accepts a valid 1..128-byte ASCII batch ID and 1..10K rows in 1..64 equal-length columns, consumes the caller's vectors and computes the same SHA-256 domain as ordinary ingestion. It exposes only borrowed columns and metadata; it has no digest input, mutable payload accessor or deserialization. Clones share the payload. A prepared value is process-local reusable input, **not a durable receipt, cache of successful ACKs, or permission to skip publication**.

Archive width is checked at submission. Known IDs compare rows and the library-computed digest with the durable original receipt. Changed content, row order, shape or width fails; equality returns the original generation. Writer health is checked before and after lookup validation. Unknown and pending IDs copy into the ordinary bounded writer path, which validates/hashes again and synchronizes before ACK. The first submission therefore adds preparation work; it has no claimed fresh-write advantage. Construction can be repeated after restart; the lookup comes from the durable ledger. Prepared values work across separate archives as ordinary input, with each archive's own ledger and publication.

The index remains **off by default**, collection delay remains zero, and CAT4/SEG2 are unchanged. The index stores only receipts, not prepared payloads. Callers own and budget prepared buffers; `payload_bytes()` is logical i64 bytes and excludes spare Vec capacity, IDs, metadata and allocator overhead. The benchmark's retained logical payload is 2,400 bytes shared across callers. Admission limits cover queued payloads rather than all caller allocations. `prepared_retry_hits` is a subset of `fast_retry_hits`.

## Measured bottleneck and rejected experiment

Five rotated CPU-only rounds over five payload shapes compared the original per-i64 SHA-256 updates with portable 512-byte and 4KiB staging. All 75 cases matched the byte domain. For the usual 3-column/100-row payload, 4KiB staging improved only {profile['medians'][1]['chunk4096_speedup']:.3f}x (8,956.88 to 8,778.56 ns median); a 3-column/1-row digest slowed from 246.90 to 284.91 ns. Wider and larger cases gained at most about 6%. This experiment is preserved and **not promoted**. SHA-256 processing remains substantial on this machine, so the new API amortizes a library-computed fingerprint over immutable reuses. Ordinary ingestion retains its original digest loop.

The design uses immutable ownership to avoid repeated work. Arrow documents immutable column arrays and shallow batch operations, providing useful context for batch-oriented APIs; this release has no Arrow adapter. [Arrow in-memory data model](https://arrow.apache.org/docs/python/data.html), [sha2 0.10.9](https://docs.rs/crate/sha2/0.10.9).

## Embedded comparison

Fresh 1M-row / 50K-ID fixtures per case; one additional known 100-row batch is committed before timing. 1/16/64 caller threads, five-second closed loops, three rotated rounds. Every receipt is checked; full scrubs and compression run after callers stop. All calls/within-window completions are counted; last-drain completions are excluded from calls/s. Latencies sample every 64 calls per worker; sub-microsecond values reflect Windows timer granularity and are descriptive, not precise nanosecond qualification. No JSON, network or Python request loop runs inside timing.

Frozen 0.3.5 ordinary probe and current ordinary control clone/hash every call. Current prepared mode reuses one constructed immutable batch per fixture, shared by callers, with no payload clone or hash inside retries. These are different input cost contracts. Median one-time construction was {audit['one_time_preparation_median_ns']/1000:.2f} us; raw reports also include throughput with that one preparation added to the five-second denominator. Construction/copy costs are explicitly included on every call in `prepare_each`, whose one-caller median is {audit['prepare_each']['median_calls_per_second']:,.0f} calls/s and sampled p99 {audit['prepare_each']['median_sampled_run_p99_us']:.2f} us. Reconstructing a batch for each retry does not deliver the reuse gain. The baseline probe source is preserved; the current probe adds mode selection and preparation counters, and ordinary controls expose its overhead.

{chr(10).join(direct_lines)}

## Protocol and fresh-write controls

The loopback JSON adapter uses ordinary ingestion and cannot receive trusted prepared fingerprints. Three rotating 15-second runs at 2,000 offers/s compare old/new **enabled** retry-heavy variants, then old/new **default** anonymous 5%-write and identified 25%-write variants. Each case has fresh 1M-row fixtures; identified cases retain 50K IDs. Retry controls commit 128 known batches outside arrivals. 64 client workers, 256 queue slots, two-second expiry and eight-second socket timeout; raw successful/errors/drop/expiry accounting is retained. Percentiles use successful requests; medians summarize runs rather than pooled samples. No extra database benchmark is inferred from the embedded result.

{chr(10).join(controls)}

{chr(10).join(operation_lines)}

Operation-specific tails prevent a favorable combined p99 from concealing slow new writes. Replay call time includes client encoding, network and database work after worker dispatch, not shared-worker queueing or server-only time. Synchronization shares sum the seven process-local publication stages across three loads after subtracting setup counters; they include writer maintenance and do not identify the device-level cause. The ordinary enabled retry median combined p99 regresses from 10.10 to 28.89ms, while both versions have one lossy/stalled run. Default identified-write controls improve in these short repeats, but the new API is unused and storage/publication code is unchanged; those observations do not establish a causal write-performance fix.

The prepared optimization cannot remove ordinary protocol payload hashing or storage synchronization. Write/control failures remain part of the release evidence. Previous DuckDB, SQLite, PostgreSQL, MariaDB and other comparisons remain historical in their own reports; this pass compares the measured Kestrel bottleneck with its previous version.

## Correctness, recovery and provenance

- 45 Rust tests pass in debug/release, including validation boundaries, shared immutable ownership, order/content/shape conflicts, width mismatch, original generations, default queued behavior, cross-archive submission, reopen and 32 concurrent first submissions publishing exactly once. Format and Clippy pass for default and fault builds.
- Fifteen prepared-path cases cover a deterministic stalled writer, seven injected disk-full errors and seven exact publication process exits. Known ordinary/prepared retries and conflicts finish before stall release; poisoned writers reject known and new prepared input. Reopening preserves whole batches, original generations and exact retry identity, with full scrubs.
- Thirty-two concurrent ordinary process-kill cycles on the current writer at 0/2/8/20ms check acknowledged data, whole batches/sums, original receipt generations, retries after a second reopen and scrubs. Five hundred current SQL cases match each of DuckDB and SQLite.
- Thirty embedded cases and 18 open-loop cases / 540,000 offers / 360 independent NumPy windows reconcile. Every receipt, sample percentile and counter delta is audited; build/timing/correctness order proves serial workloads. Only task-owned local processes are used and stopped.
- The 0.3.5 ZIP, core source, supported binaries, direct probe and verification are preserved. Archive storage/query code outside the small receipt-validation helper is byte-identical; unchanged source hashes are recorded. Earlier 56 publication cut cases, 22 corruptions, Parquet/100M results and their timings remain prior evidence, not fresh test counts.

**Service qualification remains failed.** No physical power-loss qualification, long endurance, retention contract, full SQL types, native Parquet/Arrow, authentication, distributed execution or Facebook-scale evidence is supplied by this improvement.

## Reproduction and next work

Preserve the preceding immutable package with `python benchmarks/preserve_035.py` before edits. Run `python benchmarks/profile_digest.py`, then `python benchmarks/checks_036.py`, then `python benchmarks/direct_prepared_compare.py`, then `python benchmarks/run_036.py timed`, then `python benchmarks/run_036.py correctness`, then `python benchmarks/report_036.py`. Use pinned local comparison dependencies. Runners refuse to overwrite prior attempts. Run one timed workload at a time; compile/check/package after timed work has stopped.

Continue profiling new-ID synchronization/checkpoint tails; keep index-off defaults while write controls fail. Add a practical source-checkpoint/consumer-fencing contract and bounded receipt retention before broader adapters. Use the ordinary control and preparation-inclusive control when extending batch reuse; do not equate millions of confirmed retries with millions of durable writes.

[Audit](benchmarks/prepared-036-audit.json), [build proof](benchmarks/rust-checks-036.json), [CPU trial](benchmarks/digest-036-profile.json), [embedded comparisons](benchmarks/prepared-036-direct.json), [retry protocol control](benchmarks/prepared-036-retry-control.json), [fresh-write controls](benchmarks/prepared-036-write-controls.json), [prepared faults](benchmarks/prepared-036-faults.json), [concurrent recovery](benchmarks/group-036-recovery.json), [SQL differential](benchmarks/archive-036-verification.json), [timed order](benchmarks/timed-036-run-order.json), [correctness order](benchmarks/correctness-036-run-order.json), [baseline provenance](benchmarks/baseline-0.3.5-provenance.json), [preceding release](PERFORMANCE_035.md).
'''
    (ROOT / 'PERFORMANCE_036.md').write_text(document, encoding='utf-8')
    print(json.dumps({'embedded': audit['embedded_retry'], 'controls': audit['groups']}))


if __name__ == '__main__': main()
