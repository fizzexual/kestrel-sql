"""Calibration report; original failures and phase boundaries stay explicit."""
import json
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
a = json.loads((W / 'audit.json').read_text())
yes, no = '\u2705', '\u274c'
text = f'''# Service calibration 062: identical executable controls

**{a['identity_checks_failed']} of 14 identical-binary tolerance checks fail; {a['primary_candidate_guards_failed']} of 14 predeclared candidate/A regression guards fail.** This is a new scoped measurement control, with **no engine change**. Supported 0.3.16 remains unchanged. The [061 clean parser gain and fresh DuckDB matrix](CORE_READ_PATH_061.md), including **all ten 061 service failures**, remain intact. This calibration does not replace those results or permit supported promotion.

Baseline A and B use the **same exact frozen 0.3.16 executable path and SHA-256**, not two source rebuilds. Candidate C is the unchanged `0.3.17-dev.61` executable already qualified in 061. Three fresh cases per label/profile use a Latin-square order, rotating all three labels by round and configuration so every label occupies each position once. Three profiles cover read-only 2,000 offered req/s for eight seconds, 25%-write 500/s for eight seconds, and 5%-write mixed 500/s for 60 seconds. Every store starts with 1M rows; there are 64 clients, 100-row batches, a 256-request queue, two-second expiry and zero intentional group delay. Each case runs alone and its task-owned bridge stops afterward. [Policy declared before timers](benchmarks/service-calibration-062/policy.json), [all current cases](benchmarks/service-calibration-062/paired-service.json), [independent audit](benchmarks/service-calibration-062/audit.json).

The identity comparison is B/A, with a symmetric 0.90-1.10 tolerance for paired successful p99 and arrival-window throughput, and an absolute loss difference of at most one percentage point. Candidate regression guards use **C/A as the predeclared primary comparator**: successful overall/query/append p99 at most 1.10, window throughput at least 0.90 and loss increase at most one percentage point. C/B is always shown as diagnostic evidence and cannot be chosen afterward because it looks better. Ratios are medians of the three within-round ratios, not ratios of displayed medians. Successful-request quantiles are accompanied by all losses; offered schedules are not a capacity qualification.

| Profile / offered req/s / seconds | A overall p99 ms | B overall p99 ms | C overall p99 ms | Paired B/A | Paired C/A, primary | Paired C/B, diagnostic |
|---|---:|---:|---:|---:|---:|---:|
'''
for s in a['summaries']:
    v, c = s['variants'], s['comparisons']
    text += (f"| {s['profile']} / {s['rate']:,} / {s['seconds']} | {v['baseline_a']['p99_ms']['overall']:.4f} | "
             f"{v['baseline_b']['p99_ms']['overall']:.4f} | {v['candidate']['p99_ms']['overall']:.4f} | "
             f"{c['identity_b_over_a']['paired_ratios']['overall']['median']:.4f} | "
             f"{c['primary_candidate_over_a']['paired_ratios']['overall']['median']:.4f} | "
             f"{c['diagnostic_candidate_over_b']['paired_ratios']['overall']['median']:.4f} |\n")
text += '''
| Write-containing profile | A append p99 ms | B append p99 ms | C append p99 ms | Paired B/A | Paired C/A, primary | Paired C/B, diagnostic |
|---|---:|---:|---:|---:|---:|---:|
'''
for s in a['summaries']:
    if s['profile'] == 'read':
        continue
    v, c = s['variants'], s['comparisons']
    text += (f"| {s['profile']} / {s['rate']:,} / {s['seconds']} | {v['baseline_a']['p99_ms']['append']:.4f} | "
             f"{v['baseline_b']['p99_ms']['append']:.4f} | {v['candidate']['p99_ms']['append']:.4f} | "
             f"{c['identity_b_over_a']['paired_ratios']['append']['median']:.4f} | "
             f"{c['primary_candidate_over_a']['paired_ratios']['append']['median']:.4f} | "
             f"{c['diagnostic_candidate_over_b']['paired_ratios']['append']['median']:.4f} |\n")
text += '''
| Profile | Losses A / B / C | Offered per label | Identity checks | Primary candidate guards |
|---|---:|---:|---|---|
'''
for s in a['summaries']:
    v, c = s['variants'], s['comparisons']
    identity = c['identity_b_over_a']['calibration_checks']
    candidate = c['primary_candidate_over_a']['regression_guards']
    text += (f"| {s['profile']} | {v['baseline_a']['lost']:,} / {v['baseline_b']['lost']:,} / {v['candidate']['lost']:,} | "
             f"{v['baseline_a']['offered']:,} | {yes if all(identity.values()) else no} {sum(identity.values())}/{len(identity)} | "
             f"{yes if all(candidate.values()) else no} {sum(candidate.values())}/{len(candidate)} |\n")
text += f'''
All {a['totals']['offered']:,} offered arrivals are accounted for, with {a['totals']['samples']:,} executed raw request samples. **{a['totals']['acknowledged_batches']:,} acknowledged append batches** are present after cold reopen, and atomic batch sums, exact retries and **540 NumPy 2.5.3 windows** pass. The stores scrub {a['totals']['scrubbed_bytes']:,} logical bytes in total. All minute-long soaks across all three labels have zero loss: **{yes if a['all_soaks_all_three_labels_zero_loss'] else no}**. New compilation, SQL differential suites, publication fault suites and competitor performance runs are not repeated in 062; their qualified 061 evidence is linked separately. Every raw sample, all slower rounds, stage counters and worker-dispatch/service distributions are retained. Quantiles and aggregate publication stages do not form a causal decomposition of p99.

The original control stops after eight completed timed cases when the ninth case's disk preflight reports **779,792,384 bytes**, below the unchanged 800MB threshold. That case never creates a store or starts an engine. The original eight case objects, raw hashes, policy, driver and failed-run output are frozen before continuation. Only the 19 unstarted cases resume after verified storage maintenance. **Round-zero mixed B/A and C/B cross that maintenance pause** and remain included and explicitly marked. The primary C/A comparison has no pair across the pause. Later complete rounds and the original pre-pause read/write controls remain distinct. Do not treat this as a continuous run or silently exclude the mixed crossing pair. The cause of additional host disk usage is **unattributed**; no unrelated files or processes are modified. [Original failure and preserved-case proof](benchmarks/service-calibration-062/preflight-failure-preservation.json), [original failed run](benchmarks/service-calibration-062/disk-space-preflight-failure/paired-service.json).

Storage maintenance verifies every duplicate 055 and 059 service-store file against its existing local ZIP and server-verified private asset before reclaiming the uncompressed copies. All their raw results, sources, failed experiments and full restoreable stores remain intact in those archives. Earlier 061 duplicate service copies were archived with the same per-file verification. Two signature-checked old Cargo cache subdirectories are also reclaimed, rescuing all 95 cached executables for forensics; those executables are **not benchmark labels**, and are stored in the supplemental ZIP. Source, logs and database evidence are preserved. [055 archive proof](benchmarks/service-calibration-062/old-store-archive-plan.json), [055 completion](benchmarks/service-calibration-062/old-store-archive-result.json), [059 archive proof](benchmarks/service-calibration-062/sdk-store-archive-plan.json), [059 completion](benchmarks/service-calibration-062/sdk-store-archive-result.json), [cache proof](benchmarks/service-calibration-062/cache-result.json).

Three pairs on a shared Windows desktop are a tolerance calibration, not statistical proof of equivalence or a causal attribution to the parser. Identical-binary variation, the maintenance boundary, finite traffic and the near-full host constrain the results. Candidate/B diagnostics cannot erase the predeclared candidate/A decision. No outcome retroactively changes 061's ten failures. The next write improvement should use calibrated durable publication/compaction measurements, preserve durable ACK and be requalified independently; no supported promotion occurs here. The morning report is unchanged. [Full benchmark history](BENCHMARK_HISTORY.md), [adoption assessment](ADOPTION_STATUS.md), [reproduction notes](benchmarks/service-calibration-062/REPRODUCE.md).
'''
(ROOT / 'SERVICE_CALIBRATION_062.md').write_text(text, encoding='utf-8')
print(json.dumps({'report': 'SERVICE_CALIBRATION_062.md', 'identity_checks_failed': a['identity_checks_failed'],
                  'primary_candidate_guards_failed': a['primary_candidate_guards_failed'], 'engine_changed': False}))
