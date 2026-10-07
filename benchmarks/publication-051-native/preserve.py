from pathlib import Path
import datetime, hashlib, json, shutil

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
D = ROOT / 'benchmarks/publication-051-native'
assert not D.exists()
a = json.loads((W / 'native-audit.json').read_text(encoding='utf-8'))
assert a['all_raw_hashes_status_counts_histogram_deltas_and_correctness_flags_verified']
D.mkdir()
shutil.copytree(W / 'raw', D / 'raw')
for name in ['native_publication.py', 'audit_native.py', 'policy.json', 'native-results.json', 'native-audit.json',
             'native-run.txt', 'native-audit-run.txt', 'pre-timing-process-check.json', 'post-timing-process-check.json', 'preserve.py']:
    shutil.copy2(W / name, D / name)
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
inventory = {}
for case in a['cases']:
    folder = W / 'fixtures' / case['label']
    inventory[case['label']] = {p.relative_to(folder).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p)}
                              for p in sorted(folder.rglob('*.ks2'))}
(D / 'retained-fixture-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
shutil.copy2(ROOT / 'benchmarks/baseline-0.3.16-provenance.json', D / 'released-build-provenance.json')
shutil.copy2(ROOT / 'benchmarks/trial-050-generation-identity/build-provenance.json', D / 'development-build-provenance.json')
(D / 'bin').mkdir()
for name, source in [('released-016-publication-probe.exe', ROOT / 'bin/baseline-0.3.16/publication-probe.exe'),
                     ('development-050-publication-probe.exe', ROOT / 'benchmarks/trial-050-generation-identity/bin/publication-probe.exe')]:
    shutil.copy2(source, D / 'bin' / name)
shutil.copy2(ROOT / 'examples/publication_probe.rs', D / 'publication_probe.rs')
rows = []
for s in a['summaries']:
    b, t = s['variants']['released_016'], s['variants']['development_050']
    marker = '\u2705' if s['paired_p99_ratio'] < 1 else '\u274c'
    rows.append(f"| {s['seed_receipts']:,} | {b['p50_ms']:.4f} \u2192 {t['p50_ms']:.4f} | {b['p99_ms']:.4f} \u2192 {t['p99_ms']:.4f} | {marker} {s['paired_p99_ratio']:.6f} | {b['slow_over_1000ms']} \u2192 {t['slow_over_1000ms']} / 768 | {b['reopen_ms']:.4f} \u2192 {t['reopen_ms']:.4f} |")
text = f'''# Native durable publication profile 051

**The CAT5 development trial improves typical sequential append latency but does not remove receipt-checkpoint tail stalls. No candidate is promoted.** This fresh diagnostic compares immutable released **0.3.16** with the previously qualified **development 050** binary. The supported engine and all older measurements remain unchanged.

## Before/after, fresh measurements

**18 serial cases**, three alternating pairs at each starting ledger size, rotate size order. Every case adds **256 identified 100-row batches** into a fresh archive. Append timers are inside the same byte-identical native Rust driver; setup, allocations before the call, compact/reclaim every 32 batches, checks, two full scrubs and reopen are outside those timers. This is a closed-loop native diagnostic rather than a 1M-row/64-client service or maximum requests/s test. It compares Kestrel versions and adds no fresh DuckDB or other competitor claim.

Displayed values are medians of three run values in milliseconds. Ratios are medians of within-round development/released p99 ratios; they are not quotients of the displayed medians. All raw samples and every slow run are preserved.

| Starting receipt IDs | Append p50, released \u2192 trial | Append p99, released \u2192 trial | Paired p99 ratio | Appends >1s, released \u2192 trial | Cold reopen, released \u2192 trial |
|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

The paired p50 ratios are **0.569827, 0.610399 and 0.462461**, all favoring the trial. Tail latency is less consistent: the 99,000-ID p99 ratios by round are **26.052162, 1.001593 and 0.052919**. Those large swings are retained rather than treated as a stable speed gain. Median cold reopen is slower in the CAT5 trial at every ledger size; at 99,000 IDs it increases from **115.0247 to 217.9399 ms**.

## Measured bottleneck

Full receipt checkpoints grow to about **8.2 MB at 50,000 IDs and 16.3 MB at 99,000 IDs**. Of the **52 appends exceeding 500 ms**, **50** occur at these large checkpoint writes; two other trial appends write small delta files. In slow checkpoint-heavy runs, synchronization accounts for roughly **96\u201397% of recorded publication-stage time**. Both formats experience multi-second stalls, including a **3168.6316 ms** trial delta append. This local evidence identifies the synchronization stage; it does not establish the physical storage or OS cause.

Stage totals and histogram deltas are after-minus-before counters and **include eight maintenance publications** per case. They must not be labeled append-only. Final stage maxima include prefill and are not subtractable. The audit retains these limits explicitly.

The next controlled experiment sets the exact pending-file length before writing the full CAT5 frame, then performs the same `sync_all` and rename. Rust documents that [`File::set_len`](https://doc.rust-lang.org/std/fs/struct.File.html#method.set_len) preserves the cursor; it does not promise a performance gain or physical preallocation. Trial 052 remains isolated and will be rejected unless new paired measurements justify it. A separate metadata layout or persistent journal remains longer-term work requiring format/recovery qualification.

## Correctness and reproducibility

All **4,608 timed appends / 460,800 rows**, **54 duplicate retries after cold reopen**, exact COUNT/SUM and **65,030,400 CRC-scrubbed payload bytes** pass. No fresh forced-crash test was run in 051; development 050's earlier [crash/semantic qualification](TRIAL_050.md) remains separately labeled. Every fixture is retained locally, with its file sizes and hashes in [the inventory](benchmarks/publication-051-native/retained-fixture-inventory.json).

[Predeclared policy and hashes](benchmarks/publication-051-native/policy.json), [raw outputs and exit statuses](benchmarks/publication-051-native/raw/), [independent audit with per-round pairs and stage histograms](benchmarks/publication-051-native/native-audit.json), [exact harness](benchmarks/publication-051-native/native_publication.py). The preserved native probes link to the complete [released source](benchmarks/baseline-0.3.16-source/) and [development 050 source](benchmarks/trial-050-generation-identity/candidate/) through their build provenance.

All timings finished before this audit, fixture hashing and preservation. No compilation or CPU-heavy job ran concurrently with them. [Before](benchmarks/publication-051-native/pre-timing-process-check.json) and [after](benchmarks/publication-051-native/post-timing-process-check.json) process inventories confirm the database/compiler isolation and stopped task-owned probes. Full service stability, fresh analytical qualification and production readiness remain unproved.
'''
assert sum(c['slow_over_500ms'] for c in a['cases']) == 52
assert sum(t['catalog_file_bytes'] > 1_000_000 for c in a['cases'] for t in c['tail_samples']) == 50
(ROOT / 'PUBLICATION_051.md').write_text(text, encoding='utf-8')
proof = {'preserved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'source_engine_changed': False,
         'trial_promoted': False, 'fixture_hashes_retained': sum(len(v) for v in inventory.values()),
         'payload_sha256': {p.relative_to(D).as_posix(): sha(p) for p in D.rglob('*') if p.is_file()}}
(ROOT / 'benchmarks/publication-051-preservation.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'files': len(proof['payload_sha256']), 'fixture_files': proof['fixture_hashes_retained']}))
