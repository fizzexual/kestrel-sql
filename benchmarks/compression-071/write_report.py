"""Audited balanced comparison; exact original statistics and every failure retained."""
import hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
a=load(W/'model-audit.json');r=load(W/'model-results.json');assert a['complete'] and not a['advance_to_engine_design']
rows=[]
for s in a['summaries']:
    d=s['median_display_only'];p=s['median_paired_ratios']
    for metric,label in [('stored_bytes_per_frame','Stored frame bytes'),('total_ms','12 charged publications, ms'),
        ('p50_ms','Publication p50, ms'),('p99_ms','Publication p99, ms'),('max_ms','Publication max, ms'),
        ('encode_total_ms','Charged encode/compress, ms'),('fresh_read_decode_p99_ms','Fresh-open read/decode p99, ms'),
        ('peak_working_set_bytes','Full-process peak working set, bytes'),('peak_commit_bytes','Full-process peak commit, bytes')]:
        rows.append(f"| {s['actual_receipts']:,} | {label} | {d['baseline_a'][metric]:.4f} | {d['baseline_b'][metric]:.4f} | {d['compressed'][metric]:.4f} | {p['compressed_a'][metric]:.6f} | {p['identity_b_a'][metric]:.6f} |")
gates=[];rounds=[]
for c in a['checks']:
    required=f"[{c['interval'][0]}, {c['interval'][1]}]" if c['interval'] else f"≤ {c['limit']}"
    gates.append(f"| {'✅' if c['passed'] else '❌'} | {c['size']:,} | {c['kind']} | {c['metric']} | {c['paired_ratio_or_absolute']:.9f} | {required} |")
for s in a['summaries']:
    for p in s['pairs']:
        rounds.append(f"| {s['actual_receipts']:,} | {p['round']} | {p['compressed_a']['total_ms']:.6f} | {p['compressed_a']['p50_ms']:.6f} | {p['compressed_a']['p99_ms']:.6f} | {p['compressed_a']['max_ms']:.6f} | {p['identity_b_a']['total_ms']:.6f} |")
text=f'''# Balanced fast-Zstandard checkpoint byte model: development 071

Timed {r['started_utc']} to {r['completed_utc']}; audited {a['audited_utc']}. **Model only, configuration rejected.** Supported KestrelSQL 0.3.16, its engine source/dependencies/binaries, the frozen morning report and all prior raw results/reports/private ZIPs remain unchanged.

**Verified improvement: the benchmark scheduler now checks balanced order independently before and after timing.** The [069/070 correction](MODEL_ORDER_AUDIT_071.md) documents a flaw I introduced: size rotation cancelled variant rotation, leaving one fixed A/B/C order per size in their four rounds. Their original statistics remain visible as descriptive results; that ordering can confound codec, cache, position and host/storage effects. No original evidence was rewritten and neither model was promoted.

**Fast Zstandard level −5 saves about 46% of large stored frame bytes, but fails both charged-publication speed goals and five guards.** Four A/A checks also fail. Matched C/A totals are **0.940531 at 50,126 receipts** (fails the required ≤0.90) and **1.178224 at 99,126**. The small total/p50 and large 99K p50/p99/max guards fail. All six memory guards and absolute fresh-open guards pass. This configuration does not advance to engine design or integration. No SQL speedup follows.

## Workload and corrected method

The three unchanged retained generation-129 CAT4 checkpoints from diagnostic 068 contain **126/50,126/99,126 receipts** in **21,904/8,222,890/16,271,376 bytes**. Input envelope CRC, JSON/checkpoint type, receipt count and SHA pass through the retained 069/070 chain. No database workload recreates them. The frozen input provenance's `original_archive` field points to an intermediate 069 input, rather than directly to 068; the additive [origin note](benchmarks/compression-071/input-origin-note.json) records the verified original 068 path without rewriting frozen provenance.

Six complete permutations x three sizes x raw A/raw B/compressed C = **54 serial cases**, each with twelve publications and twelve fresh-open checks. For each fixed size, every variant occupies every position twice, all six variant orders appear once, and A-before-B/B-before-A occur three times each. Each size occupies each size position twice. A planner validates those counts before the first timer; the auditor verifies them independently of elapsed times afterward. Three regression-test groups reject the earlier cancelling rotation, duplicate variants and malformed size groups. One frozen executable, mode and input path serve both raw A/B labels.

All **648 full frames / {a['stored_bytes_total']:,} stored bytes** remain intact. Native decoding, a separate Python frame-boundary parser and Arrow's separate byte-decoding binding verify **{a['independent_decoded_bytes']:,} exact original decoded bytes**. Fixed-input frame bytes are identical across all sequences/rounds for each mode. Every case and stall is included.

Native **Zstandard 1.5.7 / zstd-safe 7.2.4 / locked zstd-sys 2.0.16+zstd.1.5.7**, level **−5**, is built offline with wrapper default features disabled and std only. The library documents negative levels as a speed/compression tradeoff in its [pinned API](https://github.com/facebook/zstd/blob/v1.5.7/lib/zstd.h). Level −5 was selected independently before timing; no local level sweep or selected-case retuning occurred. The executable checks the linked native version. Twelve meaningful native tests pass in debug/release, formatting and strict Clippy pass.

The one-shot context, compressor CPU, allocations, stored/decoded payload CRCs plus header CRC, frame copies, create_new/write/flush, one sync_all, close, rename and frame release are all charged inside the outer timer. No dictionary, worker threads, reused context or buffer optimization is combined with the codec. Both modes use the same 32-byte model envelope. Canonical input read and final exact-byte comparison are excluded. All 47 thresholds are unchanged from 069/070; the new cohort uses six balanced rounds rather than their four fixed-order rounds. Earlier measurements are historical context, not a paired codec comparison.

Native decoding caps encoded/decoded payload at 64 MiB, validates standard magic, known content size and exactly one complete frame before output allocation, and passes a destination of exactly the validated raw size to one-shot decoding. Header/stored/decoded CRCs must match. Tests reject truncation, trailing/concatenated/skippable frames, unknown content size, corruption, unsupported codecs and invalid expanded lengths/budgets/CRCs. A separate Python parser checks frame limits and exact end against the [pinned format](https://github.com/facebook/zstd/blob/v1.5.7/doc/zstd_compression_format.md); three parser-test groups pass before timing. Apache Arrow **25.0.1** through its [Codec API](https://arrow.apache.org/docs/python/generated/pyarrow.Codec.html) decodes and compares exact original bytes. This separate language/binding can share the upstream codec implementation; it is not a separately implemented codec. Original Arrow binding/DLL hashes are recorded, but its installed distribution is not bundled.

`KCMP0711` is a model format rejected by Kestrel's archive reader. It excludes SQL, serde serialization, actual receipt mutations, source positions, migration, actual Archive retry/crash recovery, concurrent/pinned readers, compaction, service traffic and physical power loss. `.model` file behavior need not transfer to `.ks2`. Fresh-open reads occur in the same process after writes with possibly warm OS cache; they are not cold Archive reopen. Full-process peak memory includes setup and validation; the output bound is not a complete hostile-file ingestion qualification. No compile/test/audit/package/Git overlaps timed cases, and post-timing checks show no task-owned children left.

## Before/after measurements

Display values are medians of per-case metrics; decision ratios are medians of **six matched per-round ratios**, not ratios of display medians. Raw B is shown to expose variation. Type7 p99 uses twelve samples per case and cannot qualify service tails. A ratio above 1 takes more time/bytes/memory.

| Actual checkpoint receipts | Metric | Raw A display median | Identical raw B display median | Compressed display median | C/A matched | Identical B/A matched |
|---:|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

At 99K, all eight A/A aggregate checks pass, but C's total/p50/p99/max ratios are **1.178224/1.116106/1.196421/1.171280**. At 50K, total/p50 controls pass while tail controls fail (p99 0.790605, max 0.780103). The apparent 50K total reduction falls short of the 10% goal and does not establish a general speedup. Its six individual total ratios span **0.528627–28.197634**. Small p99/max controls fail at 1.161377/1.169629. Balanced ordering removes the confirmed fixed-position flaw; it does not remove shared-host variability or qualify every timing metric.

Charged encoding remains **4.3636x/3.9810x raw** at 50K/99K. Large fresh-open read/decode ratios are **1.6396/1.8955**, though all absolute candidate p99 guards ≤200 ms pass. Byte ratios are **0.537573/0.536767**; all six memory guards pass. Keep every stalled and fast round:

| Actual receipts | Round | C/A total | C/A p50 | C/A p99 | C/A max | Identical B/A total |
|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(rounds)}

## Every predeclared gate

Failures: **2/4 goals, 5/19 guards, 4/24 A/A checks**. Large stored-byte goal ≤0.65; large charged-total goal ≤0.90. Small total ≤1.10, p50 ≤1.05, p99/max ≤1.10, peak working set/commit ≤1.35. Every C case's fresh-open p99 must be ≤200 ms. A/A intervals are 0.90–1.10 for eight metrics per size. No threshold changed after timing.

| Result | Starting history | Kind | Metric | Matched ratio or absolute ms | Required |
|---|---:|---|---|---:|---|
{chr(10).join(gates)}

## Verification and preserved evidence

- ✅ Twelve native tests pass in debug/release; formatting and strict Clippy pass. Every malformed-stream/framing case and exact original-byte roundtrip is retained.
- ✅ Three scheduling regression groups and three Python framing groups pass before timers, with logs preserved. Both pre/post balance proofs and frozen code hashes pass.
- ✅ All 648 frame checks, three CRCs, exact native/Arrow decoding, input/raw/frame hashes, stages/counts/order and full-process memory counters pass. No case restarted or overwritten.
- ❌ Both large speed goals, five guards and four calibration checks fail. Model rejected; no engine edit, service qualification or supported promotion.
- The older 069/070 variant-order claim was incorrect. Read [its additive correction](MODEL_ORDER_AUDIT_071.md) alongside their unchanged reports/raw archives. The defect is scoped to those two model cohorts; no inference about other benchmark ordering follows.

**No new DuckDB, PostgreSQL or other SQL benchmark ran here.** Prior wins/losses remain in [analytical 046](PERFORMANCE_046.md), [development 061](CORE_READ_PATH_061.md), [six-engine service 047](SERVICE_047.md) and [complete history](BENCHMARK_HISTORY.md). Existing SQL/source retry/crash evidence in 068 remains separate and is not extended by this byte model. [Adoption assessment](ADOPTION_STATUS.md). No universal-superiority, Facebook-scale, PostgreSQL-replacement or production-readiness claim follows.

[Policy](benchmarks/compression-071/policy.json), [frozen order](benchmarks/compression-071/cohort-policy.json), [balance proof](benchmarks/compression-071/order-balance-pre-timing.json), [raw case index](benchmarks/compression-071/model-results.json), [all ratios and gates](benchmarks/compression-071/model-audit.json), [full frame inventory](benchmarks/compression-071/fixture-inventory.json), [input provenance](benchmarks/compression-071/input-provenance.json), [build/test proof](benchmarks/compression-071/build-proof.json), [oracle provenance](benchmarks/compression-071/oracle-provenance.json), [runtime](benchmarks/compression-071/runtime-provenance.json), [locked crates](benchmarks/compression-071/dependency-provenance.json), [reproduction](benchmarks/compression-071/REPRODUCE.md) and [next work](benchmarks/compression-071/NEXT_WORK.md). Individual raw stdout/status/error files, source, frozen executable and compiler/test logs are preserved alongside these. Core/input and three variant-frame ZIPs together retain every full file.

Further work should investigate a separately specified structural checkpoint approach, preserving durable idempotency/source offsets and explicit format/reader bounds. Do not turn these failures into a blind codec parameter search or trivial unchanged-page reuse comparison. A later engine candidate still needs compatibility and full SQL/source/retry/crash/concurrency/service qualification. English only; this computer only; no deployment/messages to others.
'''
target=ROOT/'COMPRESSION_071.md';assert not target.exists();target.write_text(text,encoding='utf-8')
orig=[]
for item in load(W/'input-provenance.json')['inputs']:
    old=next(i for i in load(W.parent/'perf-069/input-provenance.json')['inputs'] if i['seed_receipts']==item['seed_receipts'])
    source=Path(old['source']);assert hashlib.sha256(source.read_bytes()).hexdigest()==item['sha256']
    orig.append({'seed_receipts':item['seed_receipts'],'sha256':item['sha256'],'verified_original_068_file':str(source),
                 'frozen071_original_archive_field':item['original_archive'],'frozen_field_is_intermediate_copy':True})
(W/'input-origin-note.json').write_text(json.dumps({'frozen_input_provenance_unchanged':True,'no_input_bytes_or_timing_changed':True,'inputs':orig},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report_written':True,'bytes':target.stat().st_size,'model_rejected':True,'origin_note_additive':True}))
