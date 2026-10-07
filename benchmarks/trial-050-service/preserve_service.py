"""Run only after all timing and the independent raw-sample audit have finished."""
from pathlib import Path
import datetime, hashlib, json, shutil

w = Path(__file__).parent
root = w.parents[1] / 'outputs/kestrel-sql'
a = json.loads((w / 'paired-service-audit.json').read_text(encoding='utf-8'))
assert a['cases'] == 36 and a['raw_quantiles_accounting_uniqueness_and_hashes_recomputed']
assert not a['trial_promoted']
dest = root / 'benchmarks/trial-050-service'
assert not dest.exists()
dest.mkdir()
shutil.copytree(w / 'paired-service-samples', dest / 'paired-service-samples')
for name in ['paired_service.py', 'audit.py', 'policy.json', 'baseline.json', 'build-provenance.json',
             'paired-service.json', 'paired-service-audit.json', 'paired-service-run.txt', 'service-audit-run.txt',
             'pre-timing-process-check.json', 'post-service-process-check.json', 'cache-reclamation.json',
             'preserve_service.py', 'package_service.py', 'publish_service.py', 'verify_service.py']:
    shutil.copy2(w / name, dest / name)
shutil.copy2(w / 'profile_service_follow_up.py', dest / 'profile_service_follow_up.py')
for name in ['stress_compare.py', 'host_telemetry.py']:
    shutil.copy2(root / 'benchmarks' / name, dest / name)
rows = []
for s in a['summaries']:
    b, t = s['variants']['baseline'], s['variants']['bundle_trial']
    def f(v):
        return '\u2014' if v is None else f'{v:.4f}'
    marker = '\u2705' if t['p99']['mixed'] < b['p99']['mixed'] else '\u274c'
    rows.append(f"| {marker} | {s['profile']}, {s['rate']}/s, {s['seconds']} s | {f(b['p99']['mixed'])} \u2192 {f(t['p99']['mixed'])} | {f(b['p99']['append'])} \u2192 {f(t['p99']['append'])} | {f(s['paired_ratios']['append']['median'])} | {b['lost']} \u2192 {t['lost']} / {b['offered']} |")
gate_lines = '\n'.join(f"- {'\u2705' if value else '\u274c'} `{name}`" for name, value in a['predeclared_performance_gates'].items())
decision = ('Short service gates pass; full release qualification remains unfinished, candidate not promoted.'
            if a['performance_gates_passed'] else 'Performance gates fail; candidate not promoted.')
t = a['totals']
text = f'''# Fresh service qualification of isolated CAT5 trial 050

**{decision}** The [generation identity fix and full correctness qualification](TRIAL_050.md) preceded all timing. The supported engine remains **0.3.16**; the isolated candidate retains the synchronized pending-file handle across rename and rejects duplicate physical generation IDs during reopen. No reader kernel or acknowledgment rule changes in 050. Every fresh round and slower case is retained.

## Fresh before/after results

Each of **36 fresh cases** starts with **1,000,000 rows**, 64 clients, 100-row batches, synchronized acknowledgment and zero coalescing delay. Six configurations have three alternating baseline/candidate pairs. Mixed traffic is 95% reads/5% appends, write traffic 75%/25%, and scan traffic includes 10% appends. Values below are medians of three successful-operation run p99s, including scheduled-arrival queue time, in milliseconds. Paired ratios are medians of within-round candidate/baseline ratios, not quotients of the displayed medians. Queue drops, expiry and errors are counted separately.

| Successful overall p99 win | Workload | Overall p99, baseline \u2192 trial (ms) | Append p99, baseline \u2192 trial (ms) | Paired append ratio | Lost, baseline \u2192 trial / offered per variant |
|---|---|---:|---:|---:|---:|
{chr(10).join(rows)}

{gate_lines}

The one-minute trial append p99s are **3343.4336, 2662.3453 and 32.7568 ms**; paired baselines are **103.9917, 6117.9243 and 93.4523 ms**. Trial losses are **412, 63 and 0**, versus baseline **0, 3644 and 0**. The median trial p99 is much worse than the median baseline p99 even though two within-round append ratios favor the trial. Both statistics and every round are preserved: the mandatory zero-loss soak gate fails. The earlier 049 three zero-loss soaks did not reproduce here. These are separate temporal measurements; the startup identity check cannot be assigned as a cause of the live stalls.

[All fresh cases](benchmarks/trial-050-service/paired-service.json), [independent raw audit, per-round ratios and stage deltas](benchmarks/trial-050-service/paired-service-audit.json), [raw samples](benchmarks/trial-050-service/paired-service-samples/), [predeclared policy](benchmarks/trial-050-service/policy.json). This is a fresh 050-versus-released-0.3.16 comparison. It is not a paired comparison with historical [049](TRIAL_049.md), [048](TRIAL_048.md) or [six-engine 047](SERVICE_047.md). It adds no fresh DuckDB speed claim.

## Correctness after the timed workloads

The audit recomputes every raw p50/p95/p99, scheduled-window throughput, sequence uniqueness, sample hash and overload-accounting total. **{t['offered']:,} offered operations** produce **{t['samples']:,} raw executed samples**. All **{t['acknowledged_batches']:,} acknowledged batches** and **{t['uncertain_committed_batches']:,} unacknowledged but committed batches** reconcile as complete 100-row batches after cold process reopen. **{t['numpy_windows']} independent NumPy windows** and **{t['scrubbed_bytes']:,} fresh CRC-verified payload bytes** pass. Anonymous timeouts still do not permit safe anonymous retries.

The frozen binaries/source match the independently audited [050 correctness provenance](benchmarks/trial-050-generation-identity/build-provenance.json): 85 debug/release tests, three failing-then-passing alias regressions, 64 publication cuts, 22 corruptions, 16 source faults, 8 source forced kills, 32 concurrent kills, 4,000 SQL checks per DuckDB/SQLite and 104 manual/concurrent reader oracles. The exact 048/049 restore defect is rejected before data access while valid mixed legacy upgrades preserve original receipts.

No compilation, correctness job, audit, packaging or Git publication overlapped the timed workloads. Only task-owned database processes ran and all were stopped. [Pre-timing inventory](benchmarks/trial-050-service/pre-timing-process-check.json), [post-timing inventory](benchmarks/trial-050-service/post-service-process-check.json). Before timing, only verified Cargo debug caches were reclaimed; frozen binaries, source, logs, all benchmark fixtures and every prior release were preserved. [Exact maintenance record](benchmarks/trial-050-service/cache-reclamation.json).

The full fresh 60-shape analytical matrix, repeated/longer sustained service, supported format migration, physical power-loss and extreme device qualification remain unfinished. Host sampling is passive and does not identify physical storage causes. Earlier read regressions, overload losses and failed CAT5 trials remain visible. This local Windows qualification does not establish universal superiority, distributed or Facebook-scale capacity, or production readiness.

Post-timing publication counters show **70,997.335 ms in synchronization, 83.60%** of 84,927.445 ms combined writer/compaction time. Extra retained-file reopen calls remain zero. Stage counts and commit groups differ across variants, so aggregate counters are not paired per-request speed ratios. [All counter deltas and follow-up decision](benchmarks/trial-050-service-follow-up.json). The next step is isolated native publication profiling with fully synchronized acknowledgment preserved.
'''
(root / 'SERVICE_TRIAL_050.md').write_text(text, encoding='utf-8')
for name in ['README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']:
    p = root / name
    s = p.read_text(encoding='utf-8')
    pos = s.index('\n') + 1
    p.write_text(s[:pos] + '\n**Fresh isolated 050 service results:** [all 36 paired cases, wins/losses, raw samples and recovery audit](SERVICE_TRIAL_050.md). Supported 0.3.16 remains unchanged; older measurements and rejected trials remain visible.\n' + s[pos:], encoding='utf-8')
p = root / 'TRIAL_050.md'
s = p.read_text(encoding='utf-8')
s = s.replace('with fresh performance qualification still pending.', 'whose subsequent fresh service measurements are reported separately.')
s = s.replace('There are **no fresh 050 speed results yet**.', 'At this correctness milestone, there were **no fresh 050 speed results**; subsequent [36-case service results](SERVICE_TRIAL_050.md) are separate.')
s += '\nThe immutable correctness ZIP preserves this report as written before service timing. [The later service phase](SERVICE_TRIAL_050.md) has its own raw samples, audit and evidence asset; neither phase promotes the candidate or replaces the supported engine.\n'
p.write_text(s, encoding='utf-8')
proof = {'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'stage': 'fresh service comparisons after frozen 050 correctness qualification',
         'performance_gates_passed': a['performance_gates_passed'], 'trial_promoted': False,
         'copied_files': {p.relative_to(dest).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in dest.rglob('*') if p.is_file()}}
(root / 'benchmarks/trial-050-service-preservation.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'preserved_files': len(proof['copied_files']), 'decision': decision, 'totals': t}))
