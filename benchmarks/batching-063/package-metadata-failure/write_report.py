"""Report every current policy outcome without replacing previous failures."""
import json
from pathlib import Path
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
a=json.loads((W/'audit.json').read_text())
yes,no='\u2705','\u274c'
t=f'''# Current-release batching experiment 063

**{a['identity_checks_failed']}/10 identical zero-delay calibration checks fail; {a['candidate_criteria_failed']}/26 optional-delay criteria fail.** This experiment uses the same frozen **0.3.16 executable path and SHA-256 for all four labels**. It introduces no engine change or new supported release. The default remains zero delay. [Older batching results](PERFORMANCE_034.md), [061 native gains and service failures](CORE_READ_PATH_061.md), and [062 calibration](SERVICE_CALIBRATION_062.md) remain intact.

Baseline A and B both use zero delay. The options use 1 ms and 4 ms collection windows already supported by `LiveOptions`. Four Latin-square rounds rotate all four labels so every label occupies each position once per profile. Every case starts from a fresh 1M-row store with 64 clients and 100-row identified append batches. The profiles offer 500 requests/s: 25% writes for 15 seconds and 5% writes for 60 seconds. The queue remains 256 requests with two-second worker expiry. Setup, cold reopen, exact retry, 20 NumPy windows per case and full CRC checks are outside arrivals. All 32 cases run serially; task-owned bridges stop after each case. [Predeclared policy](benchmarks/batching-063/policy.json), [all cases](benchmarks/batching-063/paired-service.json), [raw samples](benchmarks/batching-063/paired-service-samples/), [independent audit](benchmarks/batching-063/audit.json).

The primary comparator is always each option/A; option/B remains diagnostic. Ratios are medians of four within-round ratios, rather than ratios of displayed medians. Identical B/A p99 and throughput must stay in 0.90-1.10, with loss difference at most one percentage point. An option must reduce append p99 by at least 10% and publication attempts by at least 15%, preserve overall/query p99 within 10%, retain at least 90% of arrival-window throughput, increase losses by at most one percentage point and lose no request in any minute soak. Every option criterion and every identity check must pass to call it a demonstrated scoped improvement. All outcomes, slower rounds and losses remain visible.

| Profile / seconds | Label / delay ms | Overall p99 ms | Query p99 ms | Append p99 ms | Window req/s | Publication attempts | Lost / offered |
|---|---|---:|---:|---:|---:|---:|---:|
'''
for s in a['summaries']:
    for name,v in s['variants'].items():
        m=v['medians']
        t+=f"| {s['profile']} / {s['seconds']} | {name} / {v['delay_ms']} | {m['overall']:.4f} | {m['query']:.4f} | {m['append']:.4f} | {m['rps']:.2f} | {m['attempts']:.1f} | {v['lost']:,} / {v['offered']:,} |\n"
t+='''
| Profile | Comparison | Overall ratio | Query ratio | Append ratio | Window req/s ratio | Publication ratio | Predeclared checks |
|---|---|---:|---:|---:|---:|---:|---|
'''
for s in a['summaries']:
    for name,c in s['comparisons'].items():
        p={n:v['median'] for n,v in c['paired_ratios'].items()}
        checks=c.get('calibration_checks',c.get('candidate_criteria'))
        decision=f"{yes if all(checks.values()) else no} {sum(checks.values())}/{len(checks)}" if checks else 'diagnostic only'
        t+=f"| {s['profile']} | {name} | {p['overall']:.4f} | {p['query']:.4f} | {p['append']:.4f} | {p['rps']:.4f} | {p['attempts']:.4f} | {decision} |\n"
t+='\n'
for name,d in a['decisions'].items():
    t+=f"- {yes if d['demonstrated_scoped_improvement'] else no} **{name}**: option criteria {'pass' if d['own_criteria_passed'] else 'fail'}; identical-binary calibration {'passes' if d['all_identity_controls_passed'] else 'fails'}; demonstrated scoped improvement **{'yes' if d['demonstrated_scoped_improvement'] else 'no'}**.\n"
t+='''
| Profile | Label | Durable groups | Batches/group | Mean actual collection ms | Compactions | Compaction fraction of measured writer work |
|---|---|---:|---:|---:|---:|---:|
'''
for s in a['summaries']:
    for name,v in s['variants'].items():
        d=v['collection_diagnostics_medians']
        t+=f"| {s['profile']} | {name} | {d['durable_group_commits']:.1f} | {d['batches_per_durable_group']:.3f} | {d['mean_collection_ms']:.4f} | {d['compactions']:.1f} | {100*d['compaction_fraction_of_measured_writer_work']:.2f}% |\n"
t+='\nActual collection includes code execution and OS scheduling. The compaction fraction divides measured compaction time by measured append-publication plus compaction time; it excludes collection, queueing and other work and is not a p99 decomposition. These posthoc diagnostics do not identify a scheduling cause or change the predeclared criteria. Publication attempts above include compaction publications.\n'
t+=f'''
All **{a['totals']['offered']:,} offered requests** are accounted for, with {a['totals']['samples']:,} executed raw samples and {a['totals']['acknowledged_batches']:,} acknowledged append batches preserved after cold reopen. Whole-batch counts/sums, exact retry, **{a['totals']['numpy_windows']:,} NumPy windows** and **{a['totals']['scrubbed_bytes']:,} CRC-scrubbed bytes** pass. Unacknowledged committed batches in the service runs: **{a['totals']['uncertain_committed_batches']:,}**. All minute cases have zero loss: **{yes if a['all_soaks_all_four_labels_zero_loss'] else no}**. Losses, expiry, service/dispatch distributions and publication stage counters accompany successful-request quantiles; summed stage counters are not a causal explanation of p99.

Before performance timing, **24 new process-kill cycles** test zero, 1 and 4 ms with sixteen simultaneous producers and eight kill delays. Every acknowledged batch survives, all recovered batches are whole, exact retry retains original receipt generations after a second reopen, and full scrubs pass. Attempted / acknowledged / initially published batches: **{a['recovery_totals']['attempted_batches']:,} / {a['recovery_totals']['acknowledged_batches']:,} / {a['recovery_totals']['published_batches']:,}**; initially committed without an ACK: **{a['recovery_totals']['unacknowledged_committed_batches']:,}**. Those uncertain outcomes are disclosed and reconciled, not counted as successful ACKs. Every recovery store is retained. [Recovery results](benchmarks/batching-063/recovery.json), [adaptation provenance](benchmarks/batching-063/recovery-provenance.json).

These are current option measurements, not before/after engine-code improvements or competitor timings. Four pairs on a shared Windows desktop and finite offered schedules do not qualify maximum sustainable capacity. The collection deadline bounds intentional waiting, not OS wakeup, queued work, synchronization or ACK latency. Sync and publication are unchanged. Process kills on a live filesystem do not qualify physical power loss. No compiler, other heavy task, audit, packaging or cleanup overlaps timed workloads. All task-owned database processes stop after comparison; the supported source, binaries and already-issued morning report remain unchanged. [Process check](benchmarks/batching-063/post-qualification-process-check.json), [reproduction](benchmarks/batching-063/REPRODUCE.md), [full history](BENCHMARK_HISTORY.md).

The next scoped engine experiment is [bounded compaction fan-in](benchmarks/batching-063/NEXT_WORK.md), with unchanged row/byte ceilings and full independent correctness and service qualification. This is a measured motivation and a future test plan, not an implemented or verified speedup.
'''
(ROOT/'BATCHING_063.md').write_text(t,encoding='utf-8')
