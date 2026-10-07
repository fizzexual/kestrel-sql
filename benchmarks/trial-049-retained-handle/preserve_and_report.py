"""Run only after all timed work, independent audit and the semantic probe."""
from pathlib import Path
import json, shutil, hashlib, datetime

w = Path(__file__).parent
root = w.parents[1] / 'outputs/kestrel-sql'
audit = json.loads((w / 'paired-service-audit.json').read_text(encoding='utf-8'))
probe = json.loads((w / 'generation-alias-probe.json').read_text(encoding='utf-8'))
assert audit['cases'] == 36 and audit['raw_quantiles_accounting_uniqueness_and_hashes_recomputed']
assert not audit['trial_promoted']
bug = probe.get('accepted_wrong_partial_sum', False)
dest = root / 'benchmarks/trial-049-retained-handle'
assert not dest.exists()
dest.mkdir()
for name in ['candidate', 'bin', 'harness', 'paired-service-samples', 'alias-bundle', 'alias-legacy']:
    if (w / name).exists():
        shutil.copytree(w / name, dest / name, ignore=shutil.ignore_patterns('__pycache__'))
for p in w.iterdir():
    if p.is_file():
        shutil.copy2(p, dest / p.name)

def f(v):
    return '\u2014' if v is None else f'{v:.4f}'

rows = []
for s in audit['summaries']:
    b, t = s['variants']['baseline'], s['variants']['bundle_trial']
    rows.append(f"| {s['profile']}, {s['rate']}/s, {s['seconds']} s | {f(b['p99']['mixed'])} \u2192 {f(t['p99']['mixed'])} | {f(b['p99']['append'])} \u2192 {f(t['p99']['append'])} | {f(s['paired_ratios']['append']['median'])} | {b['lost']} \u2192 {t['lost']} / {b['offered']} |")
gate_lines = '\n'.join(f"- {'\u2705' if passed else '\u274c'} `{name}`" for name, passed in audit['predeclared_performance_gates'].items())
tot = audit['totals']
decision = ('additional correctness probe failed; candidate blocked from promotion' if bug else
            'performance gates failed; candidate rejected for promotion' if not audit['performance_gates_passed'] else
            'short performance gates passed; full release qualification incomplete, candidate not promoted')
semantic = (f"**Additional semantic recovery probe failed.** A checksum-valid mixed restore references `catalog-1.ks2` and `segment-1.ks2`, whose distinct payloads share generation 1. The cache identifies pages by generation, column and block, so a partial SUM returned **{probe.get('partial_sum')} instead of [[2000]]**, although a fresh full payload scrub verified {probe.get('verified_bytes')} bytes and the metadata full SUM returned {probe.get('full_sum')}. This is a catalog identity validation defect in the isolated CAT5 design shared by 048/049, not evidence of a failure in released 0.3.16. Normal writers allocate unique generations; the failing fixture models an inconsistent checksum-valid restore. The exact failing frames, binary and reproducible probe are retained. A passing CRC is insufficient to establish correct semantic identity. An isolated successor must reject duplicate physical generations before any data/cache access and pass a regression test plus all recovery gates. The completed 048 ZIP remains immutable; this finding supplements it."
            if bug else
            f"The additional mixed-generation restore probe did not reproduce a wrong result: `{probe}`. Its fixture and exact output remain preserved.")
text = f'''# Retained-handle CAT5 trial 049: unreleased development evidence

The supported engine remains **0.3.16**. This isolated successor to [trial 048](TRIAL_048.md) opens the pending bundle for read/write, flushes and synchronizes the complete catalog/metadata/payload, then retains that file handle across rename. It removes the extra post-rename reopen measured at 46,661.287 ms in 048, without changing the CAT5 bytes or moving acknowledgment ahead of synchronization. Unix directory synchronization is unchanged. Candidate binaries inherit a 0.3.16 version string and are explicitly marked development trials.

**Decision: {decision}.** The repository's default source and supported binaries remain unchanged. No new supported engine, broad database superiority or production qualification is claimed.

## Fresh paired service measurements

Each case starts with **1,000,000 rows**, 64 clients, 100-row append batches, synchronized acknowledgment and zero coalescing delay. Mixed traffic is 95% reads/5% appends; write traffic is 75% reads/25% appends; scan traffic includes 10% appends. Six configurations each have three alternating baseline/candidate pairs on this Windows computer. P99s are medians of three run p99s in milliseconds. Paired ratios are medians of within-round candidate/baseline ratios, not quotients of the displayed medians. Successful-request latency includes scheduled-arrival queue time; overload losses are separate. Fresh 049 versus released 0.3.16 measurements cannot be treated as a paired comparison with historical 048 or 047 runs.

| Workload | Overall p99, baseline \u2192 trial (ms) | Append p99, baseline \u2192 trial (ms) | Paired append ratio | Lost, baseline \u2192 trial / offered per variant |
|---|---:|---:|---:|---:|
{chr(10).join(rows)}

[All 36 cases](benchmarks/trial-049-retained-handle/paired-service.json), [independent raw-sample audit and per-round ratios](benchmarks/trial-049-retained-handle/paired-service-audit.json), [raw samples](benchmarks/trial-049-retained-handle/paired-service-samples/), [predeclared policy](benchmarks/trial-049-retained-handle/policy.json). No compilation, correctness job or packaging overlapped timed workloads. Passive host sampling does not identify a physical storage or filter-driver cause.

{gate_lines}

## Correctness and recovery

- **82 debug and 82 release Rust tests** pass. Strict Clippy passes for ordinary and fault builds.
- **64 publication cut-point cases and 22 corruption/truncation cases** pass, including flush, synchronization, rename, retained handle and memory publication. **16 source faults, 8 source forced kills and 32 concurrent ingestion forced kills** preserve whole batches, acknowledged data, original identified retry generations and source positions.
- **4,000 SQL differential queries per DuckDB and SQLite**, plus **104 independent/manual reader oracles** including 96 concurrent requests, pass. Full scrubs bypass page caches, detect corruption and recover after repair/reopen.
- CAT2/3/4 upgrade fixtures pass; frozen 0.3.16 rejects CAT5 without file mutation. **Both 048-to-049 and 049-to-048 cold reopen/source receipt checks** pass.
- All **{tot['acknowledged_batches']:,} acknowledged batches** and **{tot['uncertain_committed_batches']:,} unacknowledged but committed batches** reconcile after the 36 timed cases. **{tot['numpy_windows']} NumPy windows** and **{tot['scrubbed_bytes']:,} fresh CRC-verified payload bytes** pass. Anonymous timeout still does not imply an uncommitted append or permit a safe anonymous retry.

{semantic}

[Correctness commands/results](benchmarks/trial-049-retained-handle/correctness-gates.json), [cross-candidate compatibility](benchmarks/trial-049-retained-handle/cross-candidate.json), [publication faults](benchmarks/trial-049-retained-handle/publication-049-faults.json), [source recovery](benchmarks/trial-049-retained-handle/source-049-faults.json), [concurrent kills](benchmarks/trial-049-retained-handle/group-049-recovery.json), [semantic probe](benchmarks/trial-049-retained-handle/generation-alias-probe.json), [reproducer](benchmarks/trial-049-retained-handle/harness/check_generation_alias.py), [source/binary provenance](benchmarks/trial-049-retained-handle/build-provenance.json), [complete isolated source](benchmarks/trial-049-retained-handle/candidate/).

## Unfinished work and preserved evidence

Automatic approval review rejected the first correctness-gate launch because its view still contained the prior compiler session. No gate process started. An explicit process inventory proved the compiler and all task-owned database processes had exited before the accepted retry. [Inventory evidence](benchmarks/trial-049-retained-handle/pre-gate-process-check.json). No test/build or performance evidence was overwritten.

CAT5 remains an experimental format with a shared catalog/data failure domain. Removing the only/latest catalog can be indistinguishable from empty/older state; crash orphans still require inspection. Physical power loss, extreme filesystem/device failures, the full fresh 60-shape analytical matrix, supported migration and longer sustained service qualification remain unfinished. Historical [released 60-shape analytical wins](PERFORMANCE_046.md) and [six-engine service wins/losses](SERVICE_047.md) remain separate results; this trial adds no fresh DuckDB speed comparison.
'''
(root / 'TRIAL_049.md').write_text(text, encoding='utf-8')
for name in ['README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']:
    p = root / name
    s = p.read_text(encoding='utf-8')
    pos = s.index('\n') + 1
    link = '\n**Unreleased trial 049:** [retained-handle service measurements and recovery evidence](TRIAL_049.md). Supported 0.3.16 remains unchanged; all rounds, failures and raw data are preserved.\n'
    p.write_text(s[:pos] + link + s[pos:], encoding='utf-8')
if bug:
    p = root / 'TRIAL_048.md'
    s = p.read_text(encoding='utf-8')
    s += '\n**Later correctness finding:** the shared CAT5 catalog/cache identity accepts two physical file kinds with the same generation in a checksum-valid mixed restore, producing a wrong partial SUM. [Trial 049 reproducer and failing fixture](TRIAL_049.md) document the defect. Both trials remain unpromoted; the previously uploaded 048 evidence ZIP is preserved unchanged.\n'
    p.write_text(s, encoding='utf-8')
proof = {'trial': '049 retained-handle CAT5, not promoted', 'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'default_core_unchanged': True, 'additional_semantic_probe_failed': bug,
         'copied_files': {p.relative_to(dest).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file()}}
(root / 'benchmarks/trial-049-preservation.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'preserved_files': len(proof['copied_files']), 'semantic_failure': bug, 'decision': decision}))
