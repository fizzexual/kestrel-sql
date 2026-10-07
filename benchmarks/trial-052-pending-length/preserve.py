from pathlib import Path
import datetime, hashlib, json, shutil, statistics
W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
D = ROOT / 'benchmarks/trial-052-pending-length'
assert not D.exists()
a = json.loads((W / 'native-audit.json').read_text())
advance = json.loads((W / 'advance-audit.json').read_text())
assert not advance['advance_to_service'] and advance['paired_database_frames_byte_identical']
D.mkdir()
for name in ['raw', 'candidate', 'bin', 'harness', 'harness-count-failure']:
    shutil.copytree(W / name, D / name)
for p in W.iterdir():
    if p.is_file() and p.suffix in ['.py', '.json', '.txt']:
        shutil.copy2(p, D / p.name)
rows = []
for s, paired in zip(a['summaries'], advance['pairs']):
    assert s['seed_receipts'] == paired['seed_receipts']
    b, t = s['variants']['base_050'], s['variants']['presized_052']
    marker = '\u2705' if paired['append_total_ratio'] < 1 else '\u274c'
    rows.append(f"| {s['seed_receipts']:,} | {b['p50_ms']:.4f} \u2192 {t['p50_ms']:.4f} | {b['p99_ms']:.4f} \u2192 {t['p99_ms']:.4f} | {marker} {paired['append_total_ratio']:.6f} | {paired['p99_ratio']:.6f} | {paired['max_ratio']:.6f} |")
gates = '\n'.join(f"- {'\u2705' if value else '\u274c'} `{name}`" for name, value in advance['predeclared_gates'].items())
text = f'''# Rejected pending-file sizing experiment 052

**Rejected: none of the four predeclared native performance gates pass.** This isolated development trial sets the exact CAT5 pending-file length before writing all frames and payloads, then performs the unchanged `sync_all` and rename. It compares against frozen development **050**, rather than supported **0.3.16**. The supported source/binaries, 050 snapshots and all previous evidence remain unchanged.

The preceding [native profile 051](PUBLICATION_051.md) found large receipt-checkpoint synchronization stalls. [`File::set_len`](https://doc.rust-lang.org/std/fs/struct.File.html#method.set_len) preserves the file cursor, but it neither guarantees physical preallocation nor promises faster publication. This bounded experiment tested that hypothesis without altering checksums, file format, acknowledgment semantics or reader kernels. Only `src/archive.rs` changes; the feature-only driver has an additional `bundle_sized` failure boundary.

## Fresh before/after

**18 fresh serial native cases**, three alternating pairs at **0, 50,000 and 99,000 starting receipt IDs**, each adding **256 identified 100-row batches**. Size order rotates. The byte-identical Rust driver's append timers exclude setup, external allocations, compact/reclaim every 32 batches, correctness checks and reopen. All timings complete before audits, hashing and packaging. This is not a sustained open-loop requests/s or 1M-row/64-client service comparison and adds no competitor speed claim.

Values are medians of three run values in milliseconds. Ratios are medians of within-round trial/base values, not ratios of displayed medians. Total time sums all 256 append timers in each run; it does not include the maintenance timers.

| Starting receipt IDs | Append p50, 050 \u2192 052 | Append p99, 050 \u2192 052 | Paired append-total ratio | Paired p99 ratio | Paired maximum ratio |
|---:|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

{gates}

At 99,000 IDs the paired total-time ratios are **0.067943, 1.082421 and 1.150979**. The first round's striking improvement is preserved alongside two slower rounds. The median paired total ratio is **1.082421** (8.24% slower), exceeding the required 0.90. The paired p99 ratio is **0.984587**, exceeding the required 0.90, and the paired maximum ratio is **1.153630**, exceeding the 1.10 guard. The 50,000-ID p50 ratio **1.050395** slightly exceeds the 1.05 guard. These criteria were declared before timing; no favorable rerun replaces a failed round.

All eight trial appends over one second occur in the 50,000-ID first round; the baseline has fourteen such appends across its 50,000/99,000-ID first rounds. The absence of >1s trial appends in this particular 99,000-ID sample does not establish removal of the underlying tail problem. Trial 052 will not advance to service qualification.

## Correctness and preserved failures

- \u2705 **85 release Rust tests**, formatting and strict Clippy for ordinary/fault configurations pass. The debug suite and the complete 050 external SQL/source suite were not repeated for this rejected experiment.
- \u2705 **72 publication-cut cases**: four append/compaction and delta/checkpoint scenarios, nine boundaries, process exit/injected I/O error. Eight cases cover the new `bundle_sized` boundary. Original receipt generations, exact rows/sums, idempotent retry, writer poisoning and pinned readers pass.
- \u2705 **22 corruption/truncation cases** are rejected and **32 concurrent forced-kill cycles** preserve every acknowledged batch and whole-batch sums, including retries after a second reopen.
- \u2705 **4,608 timed native appends / 460,800 rows**, **54 cold duplicate retries** and **65,030,400 fresh CRC-scrubbed bytes** pass. All **84 final database-frame comparisons across nine pairs** are byte-identical between 050 and 052. Every raw result and local fixture is retained.
- Preserved harness failures: the completed cut run exited 1 at its obsolete final 64-case assertion after all 72 cuts and 22 corruptions passed. The corrected harness derives the expected count from its scenarios and boundaries. Independent coverage/hash/flag auditing verifies the completed cases without rerunning them. A first coverage-auditor attempt used `cases` instead of the existing `cycles` field; its source and log are also retained. Neither failure is recorded as an engine failure or hidden as an exit-0 test run.

[Trial policy and advance criteria](benchmarks/trial-052-pending-length/trial-policy.json), [timing policy and binary hashes](benchmarks/trial-052-pending-length/policy.json), [all raw timings/statuses](benchmarks/trial-052-pending-length/raw/), [native quantile/stage audit](benchmarks/trial-052-pending-length/native-audit.json), [all paired ratios and frame equivalence](benchmarks/trial-052-pending-length/advance-audit.json), [independent recovery coverage audit](benchmarks/trial-052-pending-length/qualification-audit.json), [preserved harness failures](benchmarks/trial-052-pending-length/harness-count-failure/), [source and binary provenance](benchmarks/trial-052-pending-length/build-provenance.json).

Fault injection uses the live OS/filesystem, not physical power failure or actual device exhaustion. Only task-owned processes ran and all stopped; [pre-timing](benchmarks/trial-052-pending-length/pre-timing-process-check.json) and [post-timing](benchmarks/trial-052-pending-length/post-timing-process-check.json) inventories are preserved. Stage counters include maintenance and cumulative maxima include prefill, as in 051. No service or production-readiness qualification is claimed.

Next work should reduce the amount of receipt history rewritten and synchronized at checkpoints, with a separately specified format/migration and full recovery qualification. The rejected file-sizing path is not merged into 050 or the supported engine. No new supported release is created.
'''
assert sum(c['slow_over_1000ms'] for c in a['cases'] if c['spec']['variant'] == 'presized_052') == 8
assert sum(c['slow_over_1000ms'] for c in a['cases'] if c['spec']['variant'] == 'base_050') == 14
(ROOT / 'TRIAL_052.md').write_text(text, encoding='utf-8')
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
proof = {'preserved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'trial_promoted': False,
         'advance_to_service': False, 'default_engine_changed': False, 'local_fixtures_retained': 18,
         'payload_sha256': {p.relative_to(D).as_posix(): sha(p) for p in D.rglob('*') if p.is_file()}}
(ROOT / 'benchmarks/trial-052-preservation.json').write_text(json.dumps(proof, indent=2) + '\n')
for name in ['README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']:
    p = ROOT / name
    s = p.read_text(encoding='utf-8')
    i = s.index('\n') + 1
    s = s[:i] + '\n**Latest native publication work:** [051 measured receipt-checkpoint stalls](PUBLICATION_051.md) and [052 file-sizing experiment rejected by all four gates](TRIAL_052.md). Raw results, slower rounds and failure evidence remain accessible; supported 0.3.16 is unchanged.\n' + s[i:]
    p.write_text(s, encoding='utf-8')
print(json.dumps({'preserved_files': len(proof['payload_sha256']), 'decision': advance['decision']}))
