"""Generate report only from frozen/audited values, with every failed gate visible."""
import json
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
a=load(W/'model-audit.json');assert a['complete'] and not a['advance_to_engine_design']
r=load(W/'model-results.json');s50,s99=a['summaries'][1:]
rows=[]
for s in a['summaries']:
    display=s['median_display_only'];ratios=s['median_paired_ratios']
    for metric,label in [('stored_bytes_per_frame','Stored frame bytes'),('total_ms','12 charged publications, ms'),
        ('p50_ms','Publication p50, ms'),('p99_ms','Publication p99, ms'),('max_ms','Publication max, ms'),
        ('encode_total_ms','Charged encode/compress, ms'),('fresh_read_decode_p99_ms','Fresh-open read/decode p99, ms'),
        ('peak_working_set_bytes','Full-process peak working set, bytes'),('peak_commit_bytes','Full-process peak commit, bytes')]:
        rows.append(f"| {s['actual_receipts']:,} | {label} | {display['baseline_a'][metric]:.4f} | {display['compressed'][metric]:.4f} | {ratios['compressed_a'][metric]:.6f} | {ratios['identity_b_a'][metric]:.6f} |")
gates=[]
for c in a['checks']:
    required=f"[{c['interval'][0]}, {c['interval'][1]}]" if c['interval'] else f"≤ {c['limit']}"
    gates.append(f"| {'✅' if c['passed'] else '❌'} | {c['size']:,} | {c['kind']} | {c['metric']} | {c['paired_ratio_or_absolute']:.9f} | {required} |")
rounds=[]
for s in a['summaries']:
    for p in s['pairs']:
        rounds.append(f"| {s['actual_receipts']:,} | {p['round']} | {p['compressed_a']['total_ms']:.6f} | {p['compressed_a']['p50_ms']:.6f} | {p['compressed_a']['p99_ms']:.6f} | {p['compressed_a']['max_ms']:.6f} | {p['identity_b_a']['total_ms']:.6f} |")
report=f'''# Zstandard checkpoint byte model: development 070

Timed {r['started_utc']} to {r['completed_utc']}; audited {a['audited_utc']}. **Model only, configuration rejected.** Supported KestrelSQL 0.3.16, its engine source/dependencies/binaries, the morning report and all earlier results remain unchanged.

**Zstandard level 1 cuts large stored frame bytes by about 70%, but increases matched charged publication time by 15.0% at 50,126 receipts and 20.6% at 99,126.** Both large time goals fail, with four latency guard failures and five A/A control failures. It does not advance to engine design or integration. All native/Python/Arrow byte checks and six memory guards pass. Smaller files do not establish a faster SQL engine.

This follows [069's rejected zlib trial](COMPRESSION_069.md), motivated by [068's per-call catalog synchronization diagnostics](TRACE_068.md). All inputs, cost accounting and acceptance thresholds are identical, but 070 uses a new frozen executable and independently measured raw controls. The older zlib total ratios 1.7061/1.8874 come from a different cohort; comparing them with 070's 1.1501/1.2058 is historical context, not a paired codec speedup. Shared host/storage behavior varies between rounds.

## Workload, costs and limits

Three actual retained generation-129 CAT4 checkpoint files from 068/069 contain **126/50,126/99,126 receipts**, occupying **21,904/8,222,890/16,271,376 bytes**. Input CRC, JSON/checkpoint type, receipt count and SHA-256 pass. No database workload was repeated to create these inputs.

Four rotated rounds x three sizes x raw A/raw B/Zstandard C = **36 serial cases**. Each performs twelve publications and twelve subsequent fresh-open checks. All **432 full frames / {a['stored_bytes_total']:,} stored bytes** remain preserved, with **{a['independent_decoded_bytes']:,} decoded bytes** exactly equal to canonical inputs. One executable and the same raw mode/input path serve both A/B labels. Every round and stall counts.

Compression is **zstd-safe exactly 7.2.4, locked zstd-sys 2.0.16+zstd.1.5.7, native Zstandard 1.5.7, level 1**, built offline with default wrapper features disabled and std enabled. The executable checks the linked native version. One-shot context creation, compressor CPU, buffers, CRCs, frame copies and releases are charged on every publication; no dictionary, multi-worker codec or reused context is combined with this trial. Both modes use the same 32-byte model envelope and create_new/write/flush, one sync_all, close and rename. The outer timer includes all that work. Canonical input read and exact result comparison are excluded. The inherited policy's phrase "both CRCs" refers to stored/decoded payload CRCs; source code also computes and charges the header CRC in both modes.

The native wrapper checks standard magic, exactly one complete frame and a known frame content size equal to its outer declared length before allocating the bounded output. Encoded/decoded payloads are capped at 64 MiB; one-shot decompression receives a destination of exactly the validated raw length. Header, stored and decoded CRCs are checked. [Pinned frame-size API](https://docs.rs/zstd-safe/7.2.4/zstd_safe/fn.find_frame_compressed_size.html), [content-size API](https://docs.rs/zstd-safe/7.2.4/zstd_safe/fn.get_frame_content_size.html) and [native 1.5.7 API](https://github.com/facebook/zstd/blob/v1.5.7/lib/zstd.h) informed the wrapper; the preserved code and tests establish its checks.

A separate Python parser validates exact frame termination, known content size, dictionary-free framing and block bounds from the [pinned format specification](https://github.com/facebook/zstd/blob/v1.5.7/doc/zstd_compression_format.md). Apache Arrow **25.0.1** decodes each compressed payload through [its Python Codec API](https://arrow.apache.org/docs/python/generated/pyarrow.Codec.html), followed by exact original-byte and CRC comparison. This is a separate language/binding and independent framing oracle; Arrow can share the upstream codec implementation, so it is not claimed to be a separately implemented codec. Its original module/DLL hashes are recorded; its installed binary distribution is not part of the evidence ZIP.

`KCMP0701` is a standalone model format, not accepted by Kestrel's archive reader. It excludes SQL, serde serialization, growing receipts, source positions, old-format migration, Archive retries/recovery, concurrent readers, compaction, service traffic and physical power-loss qualification. Model files use `.model`, so filesystem behavior need not transfer to `.ks2`. Fresh-open read/decode runs in the same process after publication with potentially warm OS cache; it is not cold Archive reopen. Full-process peak memory includes setup and validation, not isolated codec allocations. The decoder takes an already loaded frame; its output bound is not a full hostile-file ingestion qualification.

No compilation, tests, audit, packaging or Git overlaps timed workloads. Only one task-owned child runs at a time, and structured post-timing checks show none left active.

## Before/after measurements

Display columns are medians of per-case values; decision ratios are medians of **four matched per-round ratios**, not ratios of the display medians. A ratio above 1 takes more time/bytes/memory. Type7 p99 uses only twelve samples per case and cannot qualify service tails.

| Actual checkpoint receipts | Metric | Raw A display median | Zstandard display median | Zstandard/A matched | Identical B/A matched |
|---:|---|---:|---:|---:|---:|
{chr(10).join(rows)}

At 50K, publication total/p50 A/A controls pass, while p99/max controls fail at 1.103985/1.114489. At 99K, all eight A/A checks pass and candidate total/p50/p99/max still regress. Small total/p50/fresh-open decode A/A controls fail. The small candidate's apparent gains are not qualified by those controls. Every compressed case passes the absolute fresh-open p99 ≤200 ms guard, but large fresh-open ratios are 1.7318/2.1131 versus raw.

The first 50K round favors compression at total ratio 0.324414, while later rounds are 1.099552/1.331299/1.200701. The first 99K candidate stalls at ratio 2.827412; later rounds remain slower at 1.214141/1.197523/1.188890. Both favorable and unfavorable stalls remain visible:

| Actual receipts | Round | C/A total | C/A p50 | C/A p99 | C/A max | Identical B/A total |
|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(rounds)}

## All 47 predeclared checks

Failures: **2/4 goals, 4/19 guards, 5/24 A/A checks**. Large byte goals ≤0.65 and charged-total goals ≤0.90; small total guard ≤1.10, p50 ≤1.05, p99/max ≤1.10, peak working set/commit ≤1.35. Every compressed case's fresh-open p99 must be ≤200 ms. A/A intervals are 0.90–1.10 for eight metrics at each size. None were relaxed.

| Result | Starting history | Kind | Metric | Matched ratio or absolute ms | Required |
|---|---:|---|---|---:|---|
{chr(10).join(gates)}

## Correctness, failures and benchmark status

- ✅ Twelve native tests pass in debug and release, plus formatting and strict Clippy. Coverage includes raw/compressed roundtrip, all truncations/trailing file data, header/payload corruption, unsupported codec, decoded-size/budget/CRC errors, trailing compressed bytes, concatenated valid frames, skippable frames, unknown content size and damage with recomputed outer CRCs.
- ✅ Three Python framing test groups pass before timing: handmade raw/RLE frames and truncation/concatenation, malformed headers/blocks, and Arrow-produced frames across size transitions.
- ✅ All 432 frames pass native exact decoding, Python frame boundaries, Arrow decoding and every outer CRC. Fixed-input bytes are identical across sequences and rounds for each mode. All input/frame/raw/policy/source/executable/oracle hashes pass; memory counters are available for all 36 cases.
- ❌ Both charged-publication time goals, four latency guards and five A/A checks fail. This configuration is rejected.
- The initial debug build's API comparison failed because ContentSizeError lacks PartialEq. Initial source, logs and build order are preserved; the fixed checks passed before any timer. No case was restarted or replaced.

**No new DuckDB, PostgreSQL or other SQL benchmark ran in 070.** Previous wins/losses remain in [analytical 046](PERFORMANCE_046.md), [development 061](CORE_READ_PATH_061.md), [six-engine service 047](SERVICE_047.md) and [complete history](BENCHMARK_HISTORY.md). Existing SQL/source retry/crash qualification in 068 is separate; this byte model does not extend it. No supported promotion, universal superiority, Facebook-scale qualification, PostgreSQL replacement or production-readiness claim follows. [Adoption assessment](ADOPTION_STATUS.md).

[Declared policy](benchmarks/compression-070/policy.json), [frozen case order](benchmarks/compression-070/cohort-policy.json), [raw case index](benchmarks/compression-070/model-results.json), [every round and gate](benchmarks/compression-070/model-audit.json), [full frame inventory](benchmarks/compression-070/fixture-inventory.json), [input provenance](benchmarks/compression-070/input-provenance.json), [build/test proof](benchmarks/compression-070/build-proof.json), [oracle provenance](benchmarks/compression-070/oracle-provenance.json), [parser-test proof](benchmarks/compression-070/frame-oracle-test-proof.json), [runtime provenance](benchmarks/compression-070/runtime-provenance.json), [locked crates](benchmarks/compression-070/dependency-provenance.json), [pre-timing notes](benchmarks/compression-070/PRE_TIMING_NOTES.md), [reproduction](benchmarks/compression-070/REPRODUCE.md) and [next work](benchmarks/compression-070/NEXT_WORK.md). Raw stdout/status/error files, compiler logs, initial failed source, final source and frozen executable are alongside them. Every frame and all three inputs are retained in the immutable ZIP.

Further codec configurations require a fresh independently declared trial with all costs, bounds, synchronization and gates retained. Only passing all model checks motivates a separately designed engine candidate; that candidate still needs format compatibility and full SQL/durable retry/crash/concurrency/service qualification. English only; this computer only; no deployment or messages to others.
'''
target=ROOT/'COMPRESSION_070.md';assert not target.exists();target.write_text(report,encoding='utf-8')
print(json.dumps({'report_written':True,'bytes':target.stat().st_size,'model_rejected':True}))
