"""English development report; all current and historical results remain separate."""
import json
from pathlib import Path

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
load = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
a = load(W / 'audit.json')
m = load(W / 'matrix.json')
p = load(W / 'primary.json')
s = load(W / 'paired-service-audit.json')
assert a['correctness_passed']
yes, no = '\u2705', '\u274c'
text = f'''# Clean core read path 061

**The parser optimization now reproduces on released 0.3.16's core, independently of SDK trials 058/060: four native range queries fall from 5.6 to 2.7 microseconds.** Fresh analytical comparisons record **{m['score']['candidate_duckdb_median_wins']}/60 median wins against DuckDB**, {m['score']['native_guards_failed']}/60 failed native regression guards, and **{s['guards_failed']}/29 failed service guards**. This is isolated `0.3.17-dev.61` development evidence. The supported source, binaries and engine releases remain **0.3.16**.

The single semantic engine edit replaces a temporary owned string in `Parser::word` with a borrowed token comparison. Package version changes and line-ending normalization of edited text files are separate. This candidate contains **none of the SDK error-contract/Arc changes** from [058](ERROR_CONTRACT_TRIAL_058.md) and [060](READ_PATH_060.md). No grammar, durability, retry or wire-protocol changes are introduced. [Predeclared analytical/range policy](benchmarks/core-read-path-061/policy.json), [source and harness provenance](benchmarks/core-read-path-061/source-provenance.json), [independent audit](benchmarks/core-read-path-061/audit.json).

Four queries select 100 or 1,000 rows from a preserved 1,000,000-row archive. These are **21 alternating released/candidate pairs**, 101 individual full-query samples per shape/process, and three warmups. Both variants are frozen non-instrumented binaries. Opening archives, JSON framing, assertions and CRC scrubs are outside the Rust `ArchiveSnapshot::query` timer. Every pair, sample and returned result is retained.

| Shape / selected rows | Released 016, microseconds | Clean 061, microseconds | Median paired candidate/base ratio | Outcome |
|---|---:|---:|---:|---|
'''
for q in p['summaries']:
    text += f"| {q['query']} | {q['baseline_median_ms']*1000:.2f} | {q['candidate_median_ms']*1000:.2f} | {q['median_paired_ratio']:.4f} | {yes if q['goal_passed'] else no} 5% goal; {q['candidate_slower_pairs']}/21 slower pairs |\n"
text += '''
The paired ratio is the median of within-round ratios; it can differ from the ratio of displayed variant medians. This phase has 16,968 timed native query samples and 1.008GB of repeated CRC verification, not a 1.008GB unique input. [All range samples and results](benchmarks/core-read-path-061/primary.json).

The fresh competitive matrix repeats **all 60 preserved analytical shapes on 12 fixtures**, including 10M and 100M rows, signed sparse/irregular keys, high cardinality, and the NYC pipeline. Each shape uses three serial rotated released/candidate/DuckDB rounds, 11 timed samples per variant/round, three warmups, one thread and a 256MB DuckDB memory limit. Inputs are reused; old 046 timings are not reused. An untimed DuckDB reference is obtained before each fixture. Native query timers include parsing, resolution, execution and result construction; DuckDB timers include Python `execute/fetchall`. Rust JSON serialization and all reference comparisons are outside its timer. The different API boundaries, warmed queries, selected aggregate subset and Kestrel indexes limit what the score establishes. This is not a ranking of general SQL engines, maximum network throughput, cold I/O or distributed performance.

| Preserved fixture / rows | Query | Released ms | Clean ms | DuckDB ms | Median paired clean/base | 5% native guard | DuckDB median win/loss; round wins |
|---|---|---:|---:|---:|---:|---|---|
'''
for q in m['summaries']:
    v = q['medians_ms']
    text += (f"| {q['fixture']} / {q['rows']:,} | {q['query']} | {v['baseline']:.6f} | {v['candidate']:.6f} | {v['duckdb']:.6f} | "
             f"{q['median_paired_candidate_base_ratio']:.4f} | {yes if q['native_guard_passed'] else no} | "
             f"{yes if q['candidate_duckdb_median_win'] else no}; {q['candidate_round_wins_vs_duckdb']}/3 |\n")
text += f'''
The matrix retains 5,940 timed samples, full returned rows (including wide groups), per-round ratios, query profiles and CRC evidence. **{sum(q['candidate_round_wins_vs_duckdb'] == 3 for q in m['summaries'])}/60 shapes beat DuckDB in all three rounds**; the table retains any slower round. Its native processes scrub {a['matrix_crc_bytes']:,} bytes in total across repeated opens; this is not unique dataset size. A median win is recorded separately from round consistency and the native regression guard. [Complete current matrix](benchmarks/core-read-path-061/matrix.json), [raw responses](benchmarks/core-read-path-061/matrix-raw), [preserved input inventory](benchmarks/core-read-path-061/analytical-input-inventory.json).

The fresh service matrix uses **36 serial cases**, three alternating fresh-store pairs for each of six profiles, 1M starting rows, 64 clients, 100-row batches, no intentional group delay, a bounded 256-request queue and two-second expiry. Mixed/read/write/scan have 5%/0%/25%/10% writes respectively; the profile named `write` is not a pure-write workload. Latency starts at scheduled arrival and includes client queuing. Successful p99 is shown alongside all unsuccessful, expired and dropped arrivals. Offered rates are finite schedules, not measured maximum sustainable capacity.

| Profile / offered req/s / seconds | Released overall p99 ms | Clean overall p99 ms | Median paired overall p99 | Median paired append p99 | Losses released / clean | Regression guards |
|---|---:|---:|---:|---:|---:|---|
'''
for row in s['summaries']:
    b, c = row['variants']['baseline'], row['variants']['candidate']
    ap = row['paired_ratios']['append']['median']
    text += (f"| {row['profile']} / {row['rate']:,} / {row['seconds']} | {b['p99']['overall']:.4f} | {c['p99']['overall']:.4f} | "
             f"{row['paired_ratios']['overall']['median']:.4f} | {ap:.4f}" if ap is not None else
             f"| {row['profile']} / {row['rate']:,} / {row['seconds']} | {b['p99']['overall']:.4f} | {c['p99']['overall']:.4f} | {row['paired_ratios']['overall']['median']:.4f} | n/a")
    passed = sum(row['guards'].values())
    text += f" | {b['lost']:,} / {c['lost']:,} | {yes if all(row['guards'].values()) else no} {passed}/{len(row['guards'])} |\n"
text += f'''
Each profile is judged on paired successful p99 (maximum 1.10), arrival-window throughput (minimum 0.90), total loss increase (maximum one percentage point), query p99 and, where applicable, append p99. Passing a tolerance guard is not proof of faster tails. **{s['guards_failed']} of 29 criteria fail.** Candidate zero-loss completion of every 60-second soak: **{yes if s['candidate_all_60s_soaks_zero_loss'] else no}**. The overloaded finite-rate schedule can still lose requests even if a regression guard passes. All slower rounds and losses remain visible. [Service policy](benchmarks/core-read-path-061/service-policy.json), [every case](benchmarks/core-read-path-061/paired-service.json), [raw accounting, quantiles, per-operation tails and guard decisions](benchmarks/core-read-path-061/paired-service-audit.json).

The independent service audit accounts for **{s['totals']['offered']:,} offered operations**, {s['totals']['samples']:,} executed request samples and {s['totals']['acknowledged_batches']:,} acknowledged append batches. Every acknowledged batch is present after a cold reopen; committed ambiguous outcomes, atomic batch sums, exact retry and 720 NumPy 2.5.3 windows are checked. Its stores scrub {s['totals']['scrubbed_bytes']:,} bytes. These are repeated logical verification bytes. Dispatch/service quantiles are posthoc diagnostics and cannot be added or subtracted to explain p99 or assign a cause.

The minute-soak append p99 is worse in all three pairs, with a 1.6176 median paired ratio. The overloaded candidate loses 25,949 of 240,000 offered arrivals, compared with 11,779 for the released baseline. Read-only p99 has a 1.0253 paired ratio despite the native microsecond improvement. These failures block supported promotion. Recorded publication stages in the minute soak spend about 84.5% of their summed time in segment/catalog sync for both variants; attempts and compactions are nearly equal (4,335/4,345 attempts, 130/131 compactions). Those aggregate counters are not a p99 decomposition and do not identify a causal explanation for the regressions. The next diagnostic should predeclare identical-binary A/A service controls and balanced order before another write-path change; all current outcomes must remain intact. [Reproducible stage analysis](benchmarks/core-read-path-061/publication-profile-analysis.json).

Fresh correctness passes **77 debug + 77 release tests**, format and strict Clippy in default and fault builds, **4,000 varied SQL cases against each of DuckDB 1.5.6 and SQLite 3.49.1**, **56 publication cuts**, **22 rejected corruptions**, **32 concurrent forced kills with exact retry**, **14 source publication faults**, **eight source pipeline kills**, **104 reader reuse/concurrency/corruption oracles**, wide integer JSON checks and a **30,000-row / 300-interval Parquet pipeline with 42 SQL oracles**. Integer checks are exact; AVG uses the existing 1e-12 tolerance. Fault-enabled drivers are built separately; normal query/service binaries contain no fault hooks. Process termination and injected I/O faults occur on a live local filesystem and are not physical power-loss qualification. [All qualification commands/logs](benchmarks/core-read-path-061/qualification.json), [build proof](benchmarks/core-read-path-061/lab/outputs/kestrel-sql/benchmarks/rust-checks-061.json).

The adapted 046 correctness harnesses change trial selectors, expected versions and trial-number-derived seeds; copied helpers also normalize line endings. Both original and executed harness hashes are preserved. Timed competitive inputs and query text are unchanged. Build/test/cache cleanup phases finish before relevant timers; only task-owned bridges/probes run, and each is stopped after its case. Four disposable, signature-checked 061 Cargo cache subdirectories are reclaimed after analytical timings, preserving frozen normal/fault binaries, all source, stores and logs. The earlier 953MB cache reclamation also predates compilation. An initial cache-command sequence exited before starting service preparation because PowerShell's unset native exit-code variable compared unequal to zero; service preparation/load were then launched separately. No completed workload is restarted. [Command-flow note](benchmarks/core-read-path-061/command-flow-note.json), [first cache proof](benchmarks/core-read-path-061/cache-result.json), [post-build cache proof](benchmarks/core-read-path-061/post-build-cache-result.json), [final process check](benchmarks/core-read-path-061/post-qualification-process-check.json).

This port establishes the native range-query improvement independently of the unsuccessful SDK service experiment. It does not establish primary-production suitability, external adoption or a new PostgreSQL win. The 047 six-engine service losses, 059 SDK failures and 060 read controls remain distinct. The supported default remains 0.3.16; supported promotion and wider production qualification are unfinished. The morning report remains unchanged. [Benchmark history](BENCHMARK_HISTORY.md), [adoption assessment](ADOPTION_STATUS.md), [reproduction instructions](benchmarks/core-read-path-061/REPRODUCE.md).
'''
(ROOT / 'CORE_READ_PATH_061.md').write_text(text, encoding='utf-8')
print(json.dumps({'report': 'CORE_READ_PATH_061.md', 'development_only': True,
                  'duckdb_median_wins': m['score']['candidate_duckdb_median_wins'], 'service_guards_failed': s['guards_failed']}))
