"""Write the measured native-buffer result with every predeclared failure visible."""
from datetime import datetime, timezone
import hashlib, json, re, shutil, sys
from pathlib import Path
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
a=load(W/'native-audit.json');q=load(W/'qualification-audit.json');b=load(W/'byte-equivalence.json')
assert a['complete'] and q['passed'] and b['passed']
failed={k:sum(c['kind']==k for c in a['failed_checks']) for k in ['goal','guard','identity']}
total={k:sum(c['kind']==k for c in a['checks']) for k in failed}
rows=[]
for s in a['summaries']:
    v=s['variants_median_display_only'];r=s['median_paired_ratios']['candidate_a']
    aa=s['median_paired_ratios']['identity_b_a']
    for key,label in [('append_plus_maintenance_ms','Append + maintenance'),('catalog_encode_ms','Catalog encode stages'),('p50_ms','Append p50'),('p99_ms','Append p99'),('max_ms','Append max'),('reopen_ms','Cold reopen')]:
        rows.append(f"| {s['seed_receipts']:,} | {label} | {v['baseline_a'][key]:.4f} | {v['candidate'][key]:.4f} | {r[key]:.6f} | {aa[key]:.6f} |")
    for key,label in [('peak_working_set_bytes','Peak working set'),('peak_commit_bytes','Peak commit')]:
        rows.append(f"| {s['seed_receipts']:,} | {label}, MiB | {v['baseline_a'][key]/1048576:.3f} | {v['candidate'][key]/1048576:.3f} | {r[key]:.6f} | {aa[key]:.6f} |")
checkrows=[]
for c in a['checks']:
    bound=f"{c['interval'][0]}–{c['interval'][1]}" if 'interval' in c else f"≤ {c['limit']}"
    ratio='unavailable' if c['paired_ratio'] is None else f"{c['paired_ratio']:.9f}"
    checkrows.append(f"| {'✅' if c['passed'] else '❌'} | {c['size']:,} | {c['kind']} | {c['metric']} | {ratio} | {bound} |")
decision='All native gates pass; service qualification is still required.' if a['advance_to_service'] else 'The candidate does not advance to service qualification or the supported release.'
report=f'''# Bounded writer catalog buffer: development 067

Measured {a['audited_utc']}. Baseline **released 0.3.16**, candidate **0.3.17-dev.67**. {decision} Supported source and binaries remain 0.3.16.

The engine shows **17.1% less catalog encoding time at 50K receipts and 19.8% less at 99K**, using matched ratios; the corresponding unchanged-engine encoding ratios are 1.0055 and 1.0048. All six candidate memory guards pass. End-to-end qualification fails: the 50K total ratio is 1.5189 and multiple latency/calibration checks fail. The large 99K apparent total win is also unqualified because its A/A total ratio is 0.5751. These outcomes do not establish a reliable overall speedup or attribute a slowdown solely to the code change.

This is the first real engine test after the fixed-input encoder models in [065/066](ENCODER_PROFILES_065_066.md). It excludes the parser, SDK and larger-compaction experiments. Every prior result, failed trial, asset and frozen morning report remains accessible in [history](BENCHMARK_HISTORY.md) and [archive navigation](ARCHIVE.md).

The writer uses the same serde JSON serializer with reusable private scratch memory. It clears the buffer after successful and failed publication, retains capacity at most **16 MiB**, and drops larger allocations. Reader snapshots never own the buffer. On-disk signatures, catalog ordering, receipt generations, checkpoint/delta rules, metadata budget, synchronization and merge fan-in are unchanged. Oversized valid catalog output still works; the cap limits retained memory, not output size.

## Fresh before/after measurements

Six matched Latin-square rounds × three starting receipt histories × A/B/candidate = **54 sequential native cases**. A and B execute one exact released binary at one path. Each case appends **256 identified batches × 100 rows**, then uses the existing live64-small-run trigger with released **32-run** compaction. All labels perform seven maintenance calls and end with39 small runs, plus one prefill segment for nonempty histories.

The exact released native driver is reused from 064, SHA-256 `75467d1f1fb7558aedac6c28fc2fbc78fd61de0778a46dc22f72595335ef544a`; the candidate links the same driver source to its freshly qualified library. No baseline rebuild occurred in 067. The preserved auditor's inherited scope phrase "newly linked identical driver" describes shared driver logic; [build provenance](benchmarks/buffer-067/native-driver-build.json) records the reuse explicitly. All raw metadata remains unchanged.

**13,824 durable append samples; 1,382,400 new rows; 162 cold duplicate retries; {a['crc_scrubbed_bytes']:,} bytes CRC scrubbed.** Setup, receipt prefill, stats, reference checks and cold reopen sit outside append timers. The primary total charges all append and compact/reclaim timings. Large-history buffers may already be allocated by prefill; this is not a cold-start encoding claim. Full-process peak memory and process wall time include setup and validation. No compilation, qualification, audit, package or Git work overlaps the timed cohort. No sample is dropped or overwritten.

Times below are milliseconds unless marked MiB. Before/after display columns are medians of per-case measurements. Decision ratios are **medians of six matched per-round ratios**, rather than ratios of the display medians. Quantiles use Type7 interpolation over all256 samples, including tails.

| Starting receipts/rows | Metric | Released A | Candidate | Candidate/A paired | Identical B/A paired |
|---:|---|---:|---:|---:|---:|
{chr(10).join(rows)}

All per-round values, stage counters, histograms, oversized tails and raw bytes are in [native audit](benchmarks/buffer-067/native-audit.json), [case order and frozen hashes](benchmarks/buffer-067/native-policy.json), and [raw records](benchmarks/buffer-067/native-results.json). Individual stdout/status files are retained alongside these reports; the immutable ZIP also holds full stores.

## Predeclared decision

Failures: **{failed['goal']}/{total['goal']} speed goals, {failed['guard']}/{total['guard']} candidate guards, {failed['identity']}/{total['identity']} identical-baseline checks**. {decision}

At50K/99K histories the targets are15% less summed catalog encoding time and3% less append-plus-maintenance time. The small-history total guard is1.05; all histories require p50≤1.05, p99/max/reopen≤1.10 and peak working set/commit≤1.15. A/A calibration must remain within0.90–1.10 on each of eight metrics at each size. Unavailable memory fails the guard. These limits were saved [before execution](benchmarks/buffer-067/policy.json), and the independent auditor was hashed before the first timed case.

The smaller total goal follows the prior measured bottleneck: encoder model066 saved21–23% encoding CPU, while released99K encoding in064 was18.33% of summed publication stages. That predicts a small end-to-end effect, not a23% database speedup. Actual growing catalogs, allocations, disk sync, reclamation and memory must qualify independently. Stage totals do not explain a p99 sample causally.

| Result | Starting receipts | Gate | Metric | Matched ratio | Required |
|---|---:|---|---|---:|---|
{chr(10).join(checkrows)}

## Correctness, durable retries and format compatibility

- ✅ **81 debug +81 release tests**, format and strict default/fault Clippy; four new tests cover byte equivalence across size/order/escaping/extreme values, bounded release after oversized output and serializer errors, checkpoints/deltas/compaction/pinned readers/cold retries, and poisoning/recovery after a real post-encode I/O failure.
- ✅ **4,000 varied SQL cases against each reference**, full expanded/cache/dense/sparse/filter suites, wide integer JSON and104 reader oracles.
- ✅ **56 publication cuts**, **22 rejected corruptions**, **32 concurrent forced kills**, **14 source publication cuts** and **8 source forced kills**. Original receipt generations, whole-batch results, source positions and second-reopen retry deduplication hold. All32 validated group-kill stores are retained by the adapted harness.
- ✅ **30,000 Parquet rows /300 source intervals /42 DuckDB correctness oracles**; this is an oracle check, not a fresh DuckDB performance comparison.
- ✅ **76 catalog +76 segment files byte-for-byte identical** between the released and candidate writers. Both versions reopen each other's stores and preserve receipt generations/reject payload collisions. The four retained format fixtures include checkpoint/delta/compaction sequences and **70,001 receipts with128-byte seed IDs**, producing a valid catalog larger than16 MiB. Buffer reset and capacity bounds are checked inside the Rust tests.
- ✅ A [post-timing exact-file audit](benchmarks/buffer-067/native-format-audit.json) also compares every one of the54 full native stores across all versions, labels and rounds at each history size. This adds correctness evidence and changes no timing decision.

See [independent qualification audit](benchmarks/buffer-067/qualification-audit.json), [all13 suite commands](benchmarks/buffer-067/qualification.json), [Rust build proof](benchmarks/buffer-067/lab/outputs/kestrel-sql/benchmarks/rust-checks-067.json), and [exact format/reopen oracle](benchmarks/buffer-067/byte-equivalence.json). Forced process termination on a live filesystem does not establish physical-power-loss durability.

## DuckDB wins/losses and remaining work

**No fresh competitor timing in067.** ✅/❌ above compare candidate with released Kestrel and unchanged A/A controls. Historical [061 DuckDB comparison](CORE_READ_PATH_061.md) remains separate:60 median analytic wins,59/60 wins in all three rounds; the closest result needs caution. Historical PostgreSQL/network losses remain visible in [multi-engine stress047](SERVICE_047.md) and later service trials. This trial does not change those wins/losses or qualify a production PostgreSQL replacement.

The model-only gain in066 is not an engine-release gain. Native calibration/guard failures, when present, remain disqualifying; selecting a favorable round or ignoring memory is not an upgrade. Further work must follow the actual stage and memory evidence and keep this complete cohort intact. Service results cannot be inferred from sequential closed-loop native latency. The shared Windows host and external activity remain limitations; A/A checks measure repeatability without attributing stalls to another process.

Exact sources, frozen normal/fault executables, all qualification logs and failures, raw54-case reports and every surviving store are preserved. The source in this evidence bundle is development-only. [Preservation inventory](benchmarks/buffer-067-preservation.json) and [bundle checksum/CRC check](benchmarks/buffer-067-bundle-check.json) become available after packaging. [Reproduction instructions](benchmarks/buffer-067/REPRODUCE.md) explain how to build a new independent cohort without overwriting this one.
'''
for old,new in [('live64','live 64'),('with39','with 39'),('all256','all 256'),('At50','At 50'),('are15','are 15'),('and3','and 3'),('is1.05','is 1.05'),('within0.90','within 0.90'),('model066','model 066'),('saved21','saved 21'),('released99','released 99'),('in064','in 064'),('was18','was 18'),('a23','a 23'),('+81','+ 81'),('and104','and 104'),('/300','/ 300'),('/42','/ 42'),('All32','All 32'),('with128','with 128'),('than16','than 16'),('all13','all 13'),('in067','in 067'),('comparison](CLEAN_CORE_061.md) remains separate:60','comparison](CLEAN_CORE_061.md) remains separate: 60'),('all54','all 54'),('and21','and 21')]:report=report.replace(old,new)
report=re.sub(r'\b(at|and|the|large|from|in|are|is|all|than|All|against)(?=\d)',r'\1 ',report)
target=ROOT/'BUFFER_067.md'
if target.exists():
    assert sys.argv[1:]==['--refresh']
    drafts=W/'report-drafts';drafts.mkdir(exist_ok=True)
    snapshot=drafts/'BUFFER_067-first-preview.md';assert not snapshot.exists()
    shutil.copy2(target,snapshot)
    (drafts/'refresh-note.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),
        'first_preview_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        'scope':'Add scoped encode outcome, explicit baseline reuse and post-timing full-store format audit; no raw or policy changes'},indent=2)+'\n',encoding='utf-8')
else:assert not sys.argv[1:]
(ROOT/'BUFFER_067.md').write_text(report,encoding='utf-8')
print(json.dumps({'report_written':True,'failed_checks':failed,'native_service_advance':a['advance_to_service']}))
