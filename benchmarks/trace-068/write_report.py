"""Write verified stage diagnostics, deliberately not a before/after speed claim."""
import json
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
a=load(W/'diagnostic-audit.json');q=load(W/'qualification-audit.json');b=load(W/'byte-equivalence.json')
assert a['passed'] and q['passed'] and b['passed']
rows=[]
for c in a['cases']:
    s=c['append']
    rows.append(f"| {c['label']} | {c['spec']['seed_receipts']:,} | {s['p50_ms']:.4f} | {s['p99_ms']:.4f} | {s['max_ms']:.4f} | {s['slow_over_500ms']} |")
slow=[]
for e in a['slow_events_over_500ms']:
    slow.append(f"| {e['label']} | {e['batch']} | {e['generation']} | {'checkpoint' if e['checkpoint'] else 'delta'} | {e['outer_ms']:.4f} | {e['largest_measured_stage']} | {e['largest_stage_ms']:.4f} | {e['largest_stage_fraction_of_outer']*100:.2f}% |")
stages=[];summary=a['all_append']
for stage,total in summary['stage_total_ms'].items():stages.append(f"| {stage} | {total:.4f} | {total/summary['outer_total_ms']*100:.2f}% |")
report=f'''# Individual publication-stage diagnostics: development 068

Measured {a['audited_utc']}. **Development 0.3.17-dev.68** is the exact released **0.3.16** core with an opt-in one-slot trace. It remains development-only. Supported source and binaries remain unchanged; no engine release or performance promotion occurs.

**Ten appends exceeded500 ms. Eight checkpoint appends spent91.88–98.01% of the call in `catalog_sync`. Two delta appends were dominated by `catalog_write` or `segment_write`.** The slowest append took1935.4281 ms:1896.9459 ms in catalog synchronization, while encoding took29.9631 ms. These per-call observations identify the measured stage, not a physical device, filesystem, OS or antivirus cause.

This fresh cohort has **768 durable appends ×100 rows**,18 compactions and18 separately timed reclaims, across six serial cases: two rounds with0/50K/99K existing receipts/rows. There is no default-versus-trace, competing-engine or before/after speed comparison. Feature overhead remains unmeasured. All six stores and every event are preserved; no stalled case was discarded or retried.

## What changed

| Before: released016 | After: opt-in diagnostic068 |
|---|---|
| Aggregate stage totals, maxima and histograms across attempts | One current publication record correlates all seven existing stage durations with the same attempt/generation |
| Totals cannot say which stage dominated a particular long call | Per-call outer latency and recorded stages identify the largest measured stage and its fraction of that call |
| Released stats and snapshots | Same stats JSON and snapshot contract; the feature adds a writer-only getter and one144-byte `Option<PublicationTrace>` |
| Same sync calls, receipt rules and disk format | Identical sync calls, receipt/checkpoint rules, output ordering, compaction fan-in and exact files |

The feature is disabled by default and its field/getter are absent in normal builds. It copies the durations already collected by the released engine rather than adding per-stage clocks or a history buffer. The probe buffers observations in memory and prints JSON once after the calls and validation. It creates no per-call diagnostic disk log.

`completed=false` represents an unknown durable outcome. No-op retries and calls rejected before publication leave the prior trace unchanged; callers must compare attempt/generation. Cold reopen resets the slot. Byte fields describe intended encoded payload/envelope sizes, not independently confirmed persisted bytes. The three new tests cover success/checkpoint/delta/compaction, failed publication/poison/reopen, bounded storage and unchanged stats schema. The original commentary's premature136-byte estimate was corrected before timing; the measured slot is144 bytes, under the predeclared192-byte bound.

## Fresh measurements

Each case contains128 named100-row appends, maintenance at64 live small runs, and the released32-run merge cap. Input generation, getter/event capture, stats, SQL checks, CRC scrubs and cold reopen are outside append/compaction timers. The feature assignment itself is inside the engine call. Reclaim is timed separately. Prefill is captured separately and excluded from the786 diagnostic publication events. No compilation, qualification, audit, packaging or Git work overlaps these timed calls; structured pre/post checks record no active task-owned processes.

The table is descriptive. All128 append samples are included, and p99 uses Type7 interpolation. The same executable produces markedly different tails in the two rounds; these are not paired speedup ratios or latency guarantees.

| Case | Starting receipts/rows | Append p50, ms | Append p99, ms | Append max, ms | Appends >500 ms |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

All18 compactions remain below500 ms, with maximum{a['all_compact']['max_ms']:.4f} ms. None of the18 reclaims exceeds500 ms. Cold reopen and full setup/validation runtime are recorded separately in each raw case.

Every slow append follows. Each named largest stage occupies more than half of its own outer call. The two delta stalls show why attributing every tail to large checkpoint serialization would be wrong.

| Case | Batch | Generation | Catalog | Outer, ms | Largest measured stage | Stage, ms | Fraction of this call |
|---|---:|---:|---|---:|---|---:|---:|
{chr(10).join(slow)}

Across all768 appends, synchronization stages account for{summary['sync_fraction_of_outer']*100:.2f}% of summed outer time, encoding{summary['encode_fraction_of_outer']*100:.2f}%, and unmeasured residual work{summary['residual_fraction_of_outer']*100:.2f}%. These are sums over this cohort, not a decomposition of a quantile or evidence of a physical cause. `segment_write` and `catalog_write` include creation/opening and writes; `catalog_sync` measures the existing catalog `sync_all` call.

| Stage | Summed append time, ms | Fraction of summed outer time |
|---|---:|---:|
{chr(10).join(stages)}

## Correctness and durability

- ✅ **80 tests in debug and80 in release**, format check, strict Clippy for default/trace/fault-only/trace+fault. All77 existing tests execute with the three new feature tests in both modes. Default mode is compiled/linted; its77 tests were not repeated without tracing.
- ✅ Full13-suite qualification: **4,000 varied SQL cases per reference**,56 publication cuts,22 rejected corruptions,32 concurrent forced-kill cycles,14 source cuts,8 source forced kills,30,000 Parquet rows/300 source intervals/42 DuckDB oracles,104 reader oracles and wide JSON/sparse-reopen checks.
- ✅ Every timed append and compaction passes. Exact COUNT/SUM, full CRC validation before and after cold reopen, and **18 known retries** preserve original generations. Cold retries leave the trace slot empty. **{a['crc_scrubbed_bytes']:,} bytes** scrubbed across both passes.
- ✅ Every event conserves stage counts, totals, maxima and histograms against the released aggregate profile, plus catalog byte/checkpoint/delta counters. Seven stage durations fit within the corresponding outer call.
- ✅ Untimed released/default/traced archive comparison: **six full stores**,76 catalog and76 segment names byte-identical across all three builds; grouped receipt order, compaction, collisions, cold retries and catalogs over16 MiB pass. Released/default code reopens traced files. The released control executable is reused from067, not rebuilt.
- ✅ All **236 final diagnostic file instances / {a['full_file_bytes']:,} bytes** independently hashed; both rounds at each history produce identical retained files. All32 group-kill stores and surviving qualification/test stores are retained in the private ZIP.
- ❌ No feature-overhead, end-to-end speed, service-load, competing-engine, physical power-loss or production qualification was attempted in068. No supported promotion.

## Older performance evidence remains separate

[Buffer067](BUFFER_067.md) previously measured17.1% less catalog encoding time at50K receipts and19.8% less at99K. It failed one of four speed goals, four of19 candidate guards and11 of24 identical-baseline checks, so it did not advance. Its writer buffer is absent from068. [Encoder models065/066](ENCODER_PROFILES_065_066.md) and [compaction064](COMPACTION_064.md) also remain separate with every failed calibration/outlier preserved.

DuckDB wins/losses have **no new performance update** here; DuckDB is a correctness oracle in068. Use the preserved [supported analytical comparison046](PERFORMANCE_046.md), [60-shape development061 result](CORE_READ_PATH_061.md) and [six-engine service047 wins/losses](SERVICE_047.md). Do not infer a PostgreSQL replacement or universal SQL victory from these diagnostics. [Adoption assessment](ADOPTION_STATUS.md).

## Reproduce and inspect

[Predeclared policy](benchmarks/trace-068/policy.json), [frozen case order/hashes](benchmarks/trace-068/diagnostic-policy.json), [raw case index](benchmarks/trace-068/diagnostic-results.json), [independent per-event audit](benchmarks/trace-068/diagnostic-audit.json), [final full-file inventory](benchmarks/trace-068/diagnostic-file-inventory.json), [qualification audit](benchmarks/trace-068/qualification-audit.json), [byte/reopen oracle](benchmarks/trace-068/byte-equivalence.json), [exact source provenance](benchmarks/trace-068/source-provenance.json), [runtime provenance](benchmarks/trace-068/runtime-provenance.json), [reproduction steps](benchmarks/trace-068/REPRODUCE.md) and [next work](benchmarks/trace-068/NEXT_WORK.md).

Individual stdout/status records, all build/qualification logs, original released core source and frozen normal/trace/fault/control binaries sit alongside these reports. Full stores are in the immutable private evidence ZIP. Earlier benchmarks, releases and the frozen morning report remain accessible through [history](BENCHMARK_HISTORY.md) and [archive](ARCHIVE.md).

The next performance experiment should reduce the work identified by individual events while preserving every synchronization and receipt guarantee, then pass independently declared calibration, tail, memory, cold-reopen and service gates. The tracer itself needs an independent overhead comparison before supported adoption. English only; this computer only; no deployment or messages to others.
'''
# Make prose readable without changing raw numbers or metadata.
for old,new in [('exceeded500','exceeded 500'),('spent91','spent 91'),('took1935','took 1935'),('ms:1896','ms: 1896'),('took29','took 29'),('appends ×100','appends × 100'),('appends**,18','appends**, 18'),('and18','and 18'),('with0','with 0'),('released016','released 016'),('diagnostic068','diagnostic 068'),('one144','one 144'),('premature136','premature 136'),('is144','is 144'),('predeclared192','predeclared 192'),('contains128','contains 128'),('named100','named 100'),('at64','at 64'),('released32','released 32'),('the786','the 786'),('All128','All 128'),('All18','All 18'),('maximum112','maximum 112'),('the18','the 18'),('all768','all 768'),('for82','for 82'),('encoding1','encoding 1'),('work1','work 1'),('and80','and 80'),('All77','All 77'),('its77','its 77'),('Full13','Full 13'),('**,56','**, 56'),(',22',', 22'),(',32',', 32'),(',14',', 14'),(',8',', 8'),(',30',', 30'),('/300','/300'),(',104',', 104'),('over16','over 16'),('from067','from 067'),('in068','in 068'),('models065','models 065'),('measured17','measured 17'),('at50','at 50'),('and19','and 19'),('at99','at 99'),('of19','of 19'),('and11','and 11'),('of24','of 24')]:report=report.replace(old,new)
for name in ['CORE_READ_PATH_061.md','COMPACTION_064.md','PERFORMANCE_046.md']:assert (ROOT/name).exists(),name
p=ROOT/'TRACE_068.md';assert not p.exists();p.write_text(report,encoding='utf-8')
print(json.dumps({'report_written':True,'bytes':p.stat().st_size,'slow_appends':10,'largest_catalog_sync':8,'trace_option_bytes':144}))
