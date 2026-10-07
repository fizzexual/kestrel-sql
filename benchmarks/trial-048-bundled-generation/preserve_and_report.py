from pathlib import Path
import json,shutil,hashlib,datetime
w=Path(__file__).parent;root=w.parents[1]/'outputs/kestrel-sql';audit=json.loads((w/'paired-service-audit.json').read_text(encoding='utf-8'))
assert not audit['trial_promoted']
dest=root/'benchmarks/trial-048-bundled-generation';assert not dest.exists()
dest.mkdir()
# Fixtures and Cargo outputs are regenerable, not publication payloads.
for name in ['candidate','bin','harness','trial-first-test-failures','trial-passed-81-tests','first-gate-harness-failure','reader-harness-first-failure','paired-service-samples']:
    shutil.copytree(w/name,dest/name,ignore=shutil.ignore_patterns('__pycache__'))
for p in w.iterdir():
    if p.is_file():shutil.copy2(p,dest/p.name)
rows=[]
for s in audit['summaries']:
    b=s['variants']['baseline'];t=s['variants']['bundle_trial']
    def f(v):return '\u2014' if v is None else f'{v:.4f}'
    rows.append(f"| {s['profile']}, {s['rate']}/s, {s['seconds']} s | {f(b['p99']['mixed'])} \u2192 {f(t['p99']['mixed'])} | {f(b['p99']['append'])} \u2192 {f(t['p99']['append'])} | {f(s['paired_ratios']['append']['median'])} | {b['lost']} \u2192 {t['lost']} / {b['offered']} |")
gate_lines='\n'.join(f"- {'\u2705' if passed else '\u274c'} `{name}`" for name,passed in audit['predeclared_performance_gates'].items())
tot=audit['totals']
text=f'''# CAT5 publication trial 048: unreleased development evidence

The supported engine is still **0.3.16**. The isolated candidate places a generation's catalog frame, segment metadata and column payload in one immutable `catalog-GENERATION.ks2` file, synchronizes that complete file once, then renames it before acknowledgment. It uses a distinct CAT5 magic, reads legacy archives and rejects invalid physical bounds. Shared-file reclamation protects active data, pinned readers and receipt dependencies. The default repository source and supported binaries are unchanged.

**Decision: {'performance gates failed; candidate rejected for promotion' if not audit['performance_gates_passed'] else 'short performance gates passed, but release qualification remains incomplete; candidate not promoted'}.** Reducing synchronization calls did not by itself qualify a service improvement. Every round, queue failure and slower case is retained. This report compares the candidate with released Kestrel, not with fresh DuckDB or other reference performance runs. The prior [60-shape analytical matrix](PERFORMANCE_046.md) and [six-engine service qualification](SERVICE_047.md) remain separate historical measurements.

## Fresh before/after service results

Each case starts with **1,000,000 rows**, 64 clients, synchronized acknowledgment, zero coalescing delay and 100-row append batches. Mixed traffic is 95% reads/5% appends; write traffic is 75% reads/25% appends, with late arrivals under the unchanged harness. Each of six configurations has three alternating baseline/candidate pairs on this Windows computer. P99 values below are **medians of three run p99s**, in milliseconds. Paired ratios are the median of within-round candidate/baseline ratios; they are not the quotient of displayed medians. Latency covers successful operations and includes scheduled-arrival queue time; losses remain explicit.

| Workload | Overall p99, baseline \u2192 trial (ms) | Append p99, baseline \u2192 trial (ms) | Paired append ratio | Lost, baseline \u2192 trial / offered per variant |
|---|---:|---:|---:|---:|
{chr(10).join(rows)}

[All 36 cases](benchmarks/trial-048-bundled-generation/paired-service.json), [independent audit and per-round ratios](benchmarks/trial-048-bundled-generation/paired-service-audit.json), [raw samples](benchmarks/trial-048-bundled-generation/paired-service-samples/), [predeclared policy](benchmarks/trial-048-bundled-generation/policy.json). The baseline is fresh paired 0.3.16, not the older 047 runs. Host sampling is passive and does not identify physical disk or filter-driver causes. No compilation, correctness job or packaging overlapped timed workloads.

The predeclared performance checks are:

{gate_lines}

## Correctness and recovery evidence

- **82 debug and 82 release Rust tests** pass, including five new CAT5 tests for exact frame bounds, signed wide aggregates, legacy upgrade, schema validation outside the current receipt chain, active-file protection, bounded normal compaction/reclamation, pinned readers and owner drop. Both ordinary and fault-feature strict Clippy checks pass.
- **CAT2, CAT3 and CAT4 fixtures** are accepted by frozen 0.3.16 before upgrade. The trial reads them, preserves old data bytes, and appends mixed-format data. Frozen 0.3.16 then rejects upgraded archives without modifying any file.
- **64 publication cut-point cases** cover delta/checkpoint appends and compaction using eight cuts, both forced process exits and injected disk-full OS errors. Cuts include both frames, partial payload, flush, sync, rename, retained-file reopen and in-memory publication. **22 corrupt/truncated catalog cases** reject publication rather than skipping past it.
- **16 source fault cases**, **8 source forced kills** and **32 concurrent ingestion forced kills** preserve acknowledged whole batches, original identified retry generations, source positions and exact output sums. Pinned readers remain readable when an I/O error poisons their writer.
- **4,000 SQL differential queries against each of DuckDB and SQLite**, plus **104 independent/manual reader SQL oracles** including 96 concurrent requests, pass. Full verification bypasses warm cached pages, detects corruption, invalidates retained stream handles and succeeds after repair and reopen.
- In the 36 timed cases, all **{tot['acknowledged_batches']:,} acknowledged append batches** and **{tot['uncertain_committed_batches']:,} unacknowledged but committed batches** reconcile after cold process reopen. **{tot['numpy_windows']} NumPy window oracles** and **{tot['scrubbed_bytes']:,} CRC-scrubbed payload bytes** pass. Timeout still does not mean failed commit; this anonymous benchmark interface cannot promise safe anonymous retry.

The [gates and exact commands](benchmarks/trial-048-bundled-generation/correctness-gates.json), [publication faults](benchmarks/trial-048-bundled-generation/publication-048-faults.json), [source faults/kills](benchmarks/trial-048-bundled-generation/source-048-faults.json), [concurrent kills](benchmarks/trial-048-bundled-generation/group-048-recovery.json), [compatibility](benchmarks/trial-048-bundled-generation/compatibility.json), [source/binary hashes](benchmarks/trial-048-bundled-generation/build-provenance.json) and [complete trial source](benchmarks/trial-048-bundled-generation/candidate/) are retained.

## Failures and remaining work

The first test run failed two legacy fixture expectations: receipt-free retired data must disappear after its last pinned reader, and missing referenced data now needs a later catalog because one bundle carries both roles. A fixture branch then triggered strict Clippy for identical paths. The first fault-harness adaptation accidentally changed `sha256` to `sha264`; the first reader harness still used the old segment filename and first-frame offset. All failures, exact source snapshots, incomplete reports and corrections are preserved alongside final results. No failed evidence was overwritten or selected as a speed win.

This is a format experiment with a larger shared catalog/data failure domain. Removing the only/latest catalog can be indistinguishable from an empty/older state in either design; the tests deliberately cover removal of referenced older payloads. Normal retention is bounded by active segments plus receipt dependencies plus pinned retired files; unreferenced crash orphans still require explicit inspection. Extreme filesystem/device failures, physical power loss, long-duration service, format migration release gates and the full new 60-shape analytical matrix are unfinished. Empty-output source checkpoints, distributed fencing and general SQL coverage remain unchanged limitations. No new engine release or production guarantee is claimed.

The next decision must use the retained publication-stage deltas and sustained service failures. The candidate will not replace 0.3.16 on the basis of one fast round, fewer synchronization calls or recovered timeouts.
'''
(root/'TRIAL_048.md').write_text(text,encoding='utf-8')
for name in ['README.md','BENCHMARK_HISTORY.md','ARCHIVE.md','PORTFOLIO.md']:
    p=root/name;s=p.read_text(encoding='utf-8');pos=s.index('\n')+1
    s=s[:pos]+'\n**Unreleased storage trial 048:** [paired service results, failed gates and full recovery evidence](TRIAL_048.md) test a single synchronized generation file. Supported 0.3.16 remains unchanged; all baseline, slower and failed trial evidence is preserved.\n'+s[pos:];p.write_text(s,encoding='utf-8')
p=root/'PUBLICATION_EXPERIMENT.md';s=p.read_text(encoding='utf-8');s=s.replace('Design proposal only. No format or durability change is implemented or released by this document.', 'The design has now been implemented in an isolated, unreleased [CAT5 development trial 048](TRIAL_048.md). No supported format or durability change is released by this document.');p.write_text(s,encoding='utf-8')
proof={'trial':'CAT5 development experiment, not promoted','captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'default_core_unchanged':True,'copied_files':{p.relative_to(dest).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.rglob('*') if p.is_file()}}
(root/'benchmarks/trial-048-preservation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print('Trial source, binaries, failures, every raw run and report preserved; default source unchanged')
