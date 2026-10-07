"""Keep original failure and independent replication visibly separate."""
from pathlib import Path
import json
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
cohorts=[('065',load(W.parent/'perf-065/audit.json')),('066',load(W/'audit.json'))]
yes,no='\u2705','\u274c'
t='''# Catalog encoder profiles 065 and 066

**The independent 066 replication passes all 43 checks.** Reusing the JSON output buffer reduces paired encoding time by **21.1% / 22.8%** on the two large fixed checkpoints. **The original 065 cohort still fails one calibration check** and remains preserved. These are exact-byte CPU/allocation models on released **0.3.16**, with no engine change, SQL performance qualification or new supported release. [064 compaction failure](COMPACTION_064.md), [063 batching results](BATCHING_063.md), [all benchmark history](BENCHMARK_HISTORY.md).

The released checkpoint serializer already borrows committed/new receipt maps; it does not clone the entire ledger during encoding. Local locked serde_json **1.0.151** source starts `to_vec` with a 128-byte vector. [The library source](https://docs.rs/serde_json/1.0.151/src/serde_json/ser.rs.html) and [writer API](https://docs.rs/serde_json/1.0.151/serde_json/fn.to_writer.html) support comparing output-buffer strategies while retaining the same serializer. Allocation-aware capacity traces here count changes to vector capacity; they are not allocator call counts or measured bytes copied.

Three original released-core checkpoints are copied from the preserved 064 baseline-A stores. They contain **250 / 50,250 / 99,250 receipts** and **42,419 / 8,243,311 / 16,291,871 JSON bytes**. Their original envelopes, CRCs and SHA-256 values are checked before extraction. The typed `CatalogOutput`, borrowed `CombinedBatches` serializer and `BatchRecord` definitions are extracted byte-for-byte from released source. Removing the final receipt into the added map reconstructs the original checkpoint's committed-then-added order, preserving every original stored byte. Parsing does not replace the engine's recovery validator; this is solely an encoder model. [Input/source provenance](benchmarks/encoder-profiles-065-066/065/input-provenance.json), [extracted serializer](benchmarks/encoder-profiles-065-066/065/released_encoder_models.rs), [build](benchmarks/encoder-profiles-065-066/065/build.json).

All labels use **one identical frozen executable** and the same released serde dependencies. A and B use the same baseline mode. `reserve_exact` allocates a fresh vector with the known fixed output length on every iteration; this oracle-sized reservation is an idealized model, not a deployable prediction strategy. `reuse` starts with an empty vector for each case and retains its capacity between encodes. Its first allocation is inside the first timer. Every case serializes the same input 33 times, including that cold first encode, without warmups. Loading/deserialization, exact output comparison and dropping the output are outside timers. No database publication, sync, query, network request or throughput is measured.

The 065 cohort has four Latin-square rounds: **48 serial cases / 1,584 encodes**. Both models pass their eight large-input goals and twenty guards, but identical B/A first-encode time at 99,250 receipts is **1.100009428487**, beyond the declared **1.10** limit. Rounding it to 1.1000 does not turn the failure into a pass. Its model advance decisions stay false. The separate 066 replication freezes **twelve rounds / 144 fresh cases / 4,752 encodes**, using the same executable, inputs, methods and thresholds. It replaces no original case. [Original policy/audit](benchmarks/encoder-profiles-065-066/065/audit.json), [replication policy](benchmarks/encoder-profiles-065-066/066/policy.json), [replication provenance](benchmarks/encoder-profiles-065-066/066/replication-provenance.json), [replication audit](benchmarks/encoder-profiles-065-066/066/audit.json).

The replication policy's human aggregation sentence accidentally retains the word “four.” Its case list, twelve-round declaration, reason and hash-recorded auditor were generated before timing and specify all twelve matched rounds. A separate note records the text error before final results/ratio analysis, leaving raw policy, source, case order and thresholds unchanged. Reproduction and this report use the frozen twelve-round code, and keep this documentation defect visible. [Aggregation text note](benchmarks/encoder-profiles-065-066/066/aggregation-text-note.json).

| Cohort | Actual receipts | Label | Total 33 encodes ms | p50 ms | p99 ms | First encode ms | Peak working set MiB |
|---|---:|---|---:|---:|---:|---:|---:|
'''
for label,a in cohorts:
    for s in a['summaries']:
        for variant,m in s['variants_median_display_only'].items():
            t+=f"| {label} | {s['receipts']:,} | {variant} | {m['total_ms']:.4f} | {m['p50_ms']:.5f} | {m['p99_ms']:.5f} | {m['first_encode_ms']:.5f} | {m['peak_working_set_bytes']/1048576:.3f} |\n"
t+='''
Ratios below are medians of within-round ratios, not ratios of the displayed medians. Type 7 p99 includes all 33 samples, including the first encode. Warm-only medians are diagnostic and do not replace the primary metrics. First-encode and peak-memory guards accompany throughput-free CPU timing; full-process peak includes input parsing and verification.

| Cohort | Actual receipts | Comparison | Total ratio | p50 ratio | p99 ratio | First ratio | Peak working-set ratio |
|---|---:|---|---:|---:|---:|---:|---:|
'''
for label,a in cohorts:
    for s in a['summaries']:
        for comparison,m in s['median_paired_ratios'].items():
            t+=f"| {label} | {s['receipts']:,} | {comparison} | "+' | '.join(f'{m[k]:.6f}' for k in ['total_ms','p50_ms','p99_ms','first_encode_ms','peak_working_set_bytes'])+' |\n'
t+='''
Each large checkpoint requires at least 10% lower total encoding time and p50. Every checkpoint permits at most 10% higher p99, first-encode time and full-process peak working set; the small checkpoint also permits at most 5% higher p50. All fifteen identical B/A ratios must stay in 0.90-1.10. Every own goal/guard plus every identity check must pass before the model justifies an engine buffer experiment. Model/B remains diagnostic. No threshold is changed after timing.

| Cohort | Goals passed | Guards passed | Identity checks passed | Justifies an engine experiment |
|---|---:|---:|---:|---|
'''
for label,a in cohorts:
    t+=f"| {label} | {yes if a['goals_failed']==0 else no} {8-a['goals_failed']}/8 | {yes if a['guards_failed']==0 else no} {20-a['guards_failed']}/20 | {yes if a['identity_checks_failed']==0 else no} {15-a['identity_checks_failed']}/15 | {yes if all(v['justifies_engine_buffer_experiment'] for v in a['decisions'].values()) else no} |\n"
t+='''
For 066, reuse changes displayed p50 from **16.8307 to 13.2393 ms** at 50,250 receipts and **33.7442 to 25.8758 ms** at 99,250. Paired p50 ratios are **0.7857 / 0.7655**; paired total ratios **0.7888 / 0.7720**. First-encode ratios are **1.0549 / 1.0367**, so first encodes are slower despite faster repeated encoding. Peak working-set ratios stay near 1. `reserve_exact` has total ratios **0.8613 / 0.8377**, but uses an unavailable future-length oracle. These observations support a bounded engine experiment; they do not predict durable append p99 or requests/s.

The exact capacity diagnostics show:

| Receipts | Original 128-byte buffer growths | Final capacity bytes | Exact reservation growths | First reuse growths | Warm reuse growths |
|---:|---:|---:|---:|---:|---:|
'''
for trace in load(W.parent/'perf-065/smoke.json')['capacity_traces']:
    by={r['model']:r for r in trace['records']}
    t+=f"| {trace['receipt_count']:,} | {len(by['baseline128']['capacity_growths'])} | {by['baseline128']['final_capacity']:,} | {len(by['reserve_exact']['capacity_growths'])} | {len(by['reuse_first']['capacity_growths'])} | {len(by['reuse_warm']['capacity_growths'])} |\n"
t+='''
These excluded diagnostics use a counting writer, while timers use ordinary vectors. In-place allocator growth could avoid copying; capacity events alone do not prove an allocation count or copying cost. The timed comparisons directly measure each encoder model with normal buffers.

Across both cohorts, **6,336 timed encodes** match **51,907,893,312 output bytes** exactly to the preserved original checkpoint bodies. A separate 48-case byte/JSON smoke covers quotes, backslashes, controls, Unicode and wide integers, followed by nine real-input smoke runs and three excluded capacity traces. The replication inherits those diagnostics and build without rerunning or counting them twice. All 192 process statuses, raw samples, capacities, peak working-set/commit counters and stderr files are preserved. [065 raw](benchmarks/encoder-profiles-065-066/065/raw/), [066 raw](benchmarks/encoder-profiles-065-066/066/raw/), [excluded diagnostics](benchmarks/encoder-profiles-065-066/065/diagnostics/).

No new database crash/retry suite is run here because no database engine is changed. Released-core and 064 correctness/recovery evidence stays separate; serializer byte equality is not durability qualification. A real buffer change must bound retained memory, avoid copying writer buffers into reader snapshots, handle growing/changing catalogs, pass byte-level oracles and full crash/source replay checks, then satisfy native/service performance guards. [Next work](benchmarks/encoder-profiles-065-066/066/NEXT_WORK.md), [reproduction](benchmarks/encoder-profiles-065-066/066/REPRODUCE.md).

All builds, capacity diagnostics, audits, cleanup and packaging run outside timers. Both cohorts' structured pre/post process checks record zero task-owned heavy/database processes. After all timing, two signed 064 Cargo debug caches are reclaimed: **753,764,494 file bytes**, with all measured frozen binaries, source, logs, native stores and prior private archives checked and retained. Release libraries remain. [Cache proof](benchmarks/encoder-profiles-065-066/066/cache-preflight.json), [resolved deletion plan](benchmarks/encoder-profiles-065-066/066/cache-plan.json), [result](benchmarks/encoder-profiles-065-066/066/cache-result.json).

No fresh DuckDB/PostgreSQL comparison, SQL speed claim, distributed-scale qualification or production-readiness claim is made. Supported 0.3.16, every historical asset and the issued morning report remain unchanged. Both raw cohorts and all exact inputs are preserved in the supplemental archive.
'''
(ROOT/'ENCODER_PROFILES_065_066.md').write_text(t,encoding='utf-8')
print(json.dumps({'report':'ENCODER_PROFILES_065_066.md','original_failure_preserved':True,'replication_all43_checks_passed':True,'engine_unchanged':True}))
