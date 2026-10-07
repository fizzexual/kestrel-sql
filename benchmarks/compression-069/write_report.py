"""Verified byte savings and paid-latency regression; retain every raw round."""
import json
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
a=load(W/'model-audit.json');assert a['complete'] and not a['advance_to_engine_design']
rows=[]
for s in a['summaries']:
    display=s['median_display_only'];ratio=s['median_paired_ratios']['compressed_a'];identity=s['median_paired_ratios']['identity_b_a']
    for metric,label in [('stored_bytes_per_frame','Stored frame bytes'),('total_ms','12 charged publications, ms'),('p50_ms','Publication p50, ms'),('p99_ms','Publication p99, ms'),('max_ms','Publication max, ms'),('encode_total_ms','Charged encode/compress, ms'),('fresh_read_decode_p99_ms','Fresh-open read/decode p99, ms')]:
        rows.append(f"| {s['actual_receipts']:,} | {label} | {display['baseline_a'][metric]:.4f} | {display['compressed'][metric]:.4f} | {ratio[metric]:.6f} | {identity[metric]:.6f} |")
gates=[]
for c in a['checks']:
    required=f"[{c['interval'][0]}, {c['interval'][1]}]" if c['interval'] else f"≤ {c['limit']}"
    gates.append(f"| {'✅' if c['passed'] else '❌'} | {c['size']:,} | {c['kind']} | {c['metric']} | {c['paired_ratio_or_absolute']:.9f} | {required} |")
report=f'''# Checkpoint compression byte model: development 069

Measured {a['audited_utc']}. **Model only, configuration rejected.** This is not a new SQL engine or production catalog format. Supported KestrelSQL0.3.16, its source/dependencies/binaries, all previous benchmarks and the frozen morning report remain unchanged.

**Large checkpoint frames are62.8% smaller, but the median matched charged-publication ratios are1.7061 at50,126 receipts and1.8874 at99,126.** Encoding/compression costs8.62×/8.69× the raw frame encoder. Both total-time goals and all six large-history p50/p99/max guards fail. This codec configuration does not advance to engine design or integration. Memory guards and exact decoding pass; smaller files alone do not establish a faster database.

The hypothesis follows [068 per-call diagnostics](TRACE_068.md): eight large-checkpoint stalls spent91.88–98.01% of their call in catalog synchronization. Reducing bytes was worth testing, but that observation does not prove a physical cause or predict whether extra codec CPU pays off. Increasing checkpoint spacing would also exceed the released reader's32-catalog receipt-chain budget; this model leaves it unchanged.

## Scope and accounting

Three exact retained CAT4 checkpoint files from068, generation129, contain **126/50,126/99,126 receipts**, occupying **21,904 /8,222,890 /16,271,376 bytes**. Input envelope CRC, JSON/checkpoint type, retained per-event metadata and SHA-256 all pass. The zero-seed checkpoint is a compaction, with126 receipts after batch125. An initial preparation assertion incorrectly expected127, stopped before policy/timers, and was corrected using preserved metadata; its original code and copied input remain preserved. No database workload was rerun.

Four rotated rounds ×three sizes ×raw A/raw B/zlib C = **36 serial cases**. Each publishes12 fixed-input frames; all **432 frames / {a['stored_bytes_total']:,} stored bytes** remain intact. One frozen executable and one raw mode/input path serve both A/B labels. Each case then performs12 fresh-open read/decode checks. All **{a['independent_decoded_bytes']:,} decoded bytes** independently match the canonical original checkpoint files using Python zlib; every native check also passes.

The raw and compressed modes use the same32-byte model envelope and publication lifecycle: frame/checksum/allocate/copy, create_new/write/flush, one sync_all, close, rename and buffer release. Compression is **miniz_oxide exactly0.8.9, zlib level1**, available in the local offline cache. Every codec and frame-assembly cost is charged inside the outer publication. Canonical input read and final byte comparisons are outside the publication timer. All samples, including stalls, are included.

The model's `KCMP0691` frame is **not** a Kestrel archive format. It excludes SQL, serde serialization, growing receipt ledgers, source positions, migration, actual Archive recovery, pinned/concurrent readers, compaction, service load and physical power-loss qualification. Files end in `.model`, rather than actual archive `.ks2`; filesystem behavior need not transfer. Fresh-open read/decode timing runs in the same process after writes with a potentially warm OS cache. It is not cold Archive reopen. Full-process peak memory includes input read and validation, not isolated codec allocations. No compilation, test/audit, packaging or Git work overlaps timers; task-owned children are stopped afterward.

The standalone decoder validates header, stored and decoded CRCs, caps encoded and decoded payload at64 MiB before output allocation, and requires the exact compressed stream to end with every input byte consumed. [Pinned library source](https://docs.rs/crate/miniz_oxide/0.8.9/source/Cargo.toml) documents the dependency; model code and tests establish this wrapper's bounds and strict checks.

## Before/after model measurements

Display columns are medians of per-case values. Decision ratios are medians of **four matched per-round ratios**, not ratios of display medians. p99 uses Type7 interpolation over only12 samples per case; these descriptive model tails cannot qualify a service.

| Actual receipts in fixed checkpoint | Metric | Raw A display median | Compressed display median | Compressed/A matched | Identical B/A matched |
|---:|---|---:|---:|---:|---:|
{chr(10).join(rows)}

The first large-history round favors compression (total ratios0.3491 at50K and0.4227 at99K), while the three later rounds have total ratios **1.6923–1.8355** and **1.8791–1.9294**. All rounds remain visible. Large-history A/A publication total/p50/p99/max checks pass; the candidate's large latency regression is not hidden by selecting the stalled raw first round. Across all sizes, three of24 calibration checks still fail: small p50, small fresh-open decode p99 and50K fresh-open decode p99. No claim of calibrated universal behavior follows.

## Every predeclared check

Failures: **2/4 goals,6/19 guards,3/24 A/A checks**. Large byte goals require a ratio≤0.65 and total-time goals≤0.90. Small total guard≤1.10; p50≤1.05; p99/max≤1.10; peak working set/commit≤1.35. Every compressed case's fresh-open read/decode p99 must stay≤200 ms. A/A intervals are0.90–1.10 for eight metrics at each size. These were declared before the first case and were not relaxed.

| Result | Starting history | Kind | Metric | Matched ratio or absolute decode ms | Required |
|---|---:|---|---|---:|---|
{chr(10).join(gates)}

## Verification and preserved evidence

- ✅ Eight meaningful decoder/framing tests pass in debug and release, plus format and strict Clippy. Tests cover exact raw/compressed roundtrip, all truncation points and trailing file data, corrupted header/payload, unsupported codec, bounded expansion, incorrect decoded length/CRC and compressed trailing bytes with valid outer checksums.
- ✅ Every432 frame passes native exact decoding and independent Python zlib decoding, all three CRCs, size/type/budget/stream-end checks. Fixed-input frame bytes are identical across all sequences and rounds for each mode. Every frame and input is retained in the private ZIP.
- ✅ Raw hashes, frozen policies/executable/auditor, case order, all432 publication samples, stage sums and432 fresh-open checks are independently verified. Full-process memory counters are available for every case.
- ❌ Both large charged-total goals and six large latency guards fail; three A/A checks fail. No engine integration, service qualification or supported promotion.

**No new DuckDB, PostgreSQL or other SQL performance comparison occurred.** Prior wins and losses remain accessible in [analytical046](PERFORMANCE_046.md), [development061](CORE_READ_PATH_061.md), [six-engine service047](SERVICE_047.md) and [complete history](BENCHMARK_HISTORY.md). Existing SQL/source retry/crash checks in068 remain separate; this model does not repeat or extend them. [Adoption assessment](ADOPTION_STATUS.md).

[Declared policy](benchmarks/compression-069/policy.json), [frozen case order](benchmarks/compression-069/cohort-policy.json), [raw case index](benchmarks/compression-069/model-results.json), [independent audit including every round](benchmarks/compression-069/model-audit.json), [full frame inventory](benchmarks/compression-069/fixture-inventory.json), [input provenance](benchmarks/compression-069/input-provenance.json), [build/test proof](benchmarks/compression-069/build-proof.json), [runtime provenance](benchmarks/compression-069/runtime-provenance.json), [locked crate archives](benchmarks/compression-069/dependency-provenance.json), [reproduction](benchmarks/compression-069/REPRODUCE.md) and [next work](benchmarks/compression-069/NEXT_WORK.md). Individual raw stdout/status/error files and compiler logs are alongside them; full frames and three canonical inputs are in the immutable ZIP.

A new codec hypothesis must charge its CPU and memory costs against the same raw controls, preserve all synchronization guarantees and pass independently declared gates before any real engine design. No inference of Facebook-scale, PostgreSQL replacement or production readiness is supported here. English only; this computer only; no deployment/messages to others.
'''
corrections=[('KestrelSQL0','KestrelSQL 0'),('are62','are 62'),('are1','are 1'),('at50','at 50'),('at99','at 99'),('costs8','costs 8'),('spent91','spent 91'),("reader's32","reader's 32"),('from068','from 068'),('generation129','generation 129'),('with126','with 126'),('after batch125','after batch 125'),('expected127','expected 127'),('publishes12','publishes 12'),('performs12','performs 12'),('same32','same 32'),('exactly0','exactly 0'),('level1','level 1'),('at64','at 64'),('only12','only 12'),('ratios0','ratios 0'),('and0','and 0'),('of24','of 24'),('and50','and 50'),('goals,6','goals, 6'),('guards,3','guards, 3'),('ratio≤','ratio ≤'),('goals≤','goals ≤'),('guard≤','guard ≤'),('p50≤','p50 ≤'),('max≤','max ≤'),('commit≤','commit ≤'),('stay≤','stay ≤'),('are0','are 0'),('Every432','All 432'),('all432','all 432'),('and432','and 432'),('analytical046','analytical 046'),('development061','development 061'),('service047','service 047'),('in068','in 068')]
for old,new in corrections:report=report.replace(old,new)
p=ROOT/'COMPRESSION_069.md';assert not p.exists();p.write_text(report,encoding='utf-8')
print(json.dumps({'report_written':True,'bytes':p.stat().st_size,'model_rejected':True}))
