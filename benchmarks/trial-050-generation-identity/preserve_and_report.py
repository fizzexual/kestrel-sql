from pathlib import Path
import datetime, hashlib, json, shutil

w = Path(__file__).parent
root = w.parents[1] / 'outputs/kestrel-sql'
a = json.loads((w / 'correctness-audit.json').read_text(encoding='utf-8'))
assert a['all_14_final_external_gates_passed'] and not a['trial_promoted']
dest = root / 'benchmarks/trial-050-generation-identity'
assert not dest.exists()
dest.mkdir()
directory_names = ['candidate', 'bin', 'harness', 'regression-before-fix',
                   'semantic-harness-first-failure', 'semantic-harness-second-failure']
directory_names += [p.name for p in w.iterdir() if p.is_dir() and
                    (p.name.startswith('alias-') or p.name == 'valid-unique-generation-legacy-upgrade')]
for name in directory_names:
    shutil.copytree(w / name, dest / name, ignore=shutil.ignore_patterns('__pycache__', '*.lockfile'))
for p in w.iterdir():
    if p.is_file():
        shutil.copy2(p, dest / p.name)
text = '''# Generation identity hardening trial 050

**The reproduced CAT5 restore defect is fixed in this isolated candidate.** Each catalog, including receipt ancestors, now requires unique physical generation IDs across legacy segment files and CAT5 bundles before any segment is loaded. Generation is part of the page-cache key; accepting two different files with the same generation could silently reuse the wrong page despite valid checksums. The supported engine remains **0.3.16**. This is verified development evidence, with fresh performance qualification still pending.

## Concrete before/after

The exact checksum-valid [049 failing fixture](benchmarks/trial-049-retained-handle/alias-bundle/) contains a 512-row CAT5 payload with value 1, a distinct 512-row legacy payload with value 9, both labeled generation 1, and one row with value 3 in generation 2. A window SUM must equal 2000.

| Check | Before: isolated 048/049 | After: isolated 050 |
|---|---|---|
| Partial SUM on inconsistent mixed restore | \u274c 400 instead of 2000 | \u2705 Restore rejected before data access |
| Full payload CRC on that same restore | Passes 24,600 bytes despite wrong cached SUM | Rejected at catalog identity validation |
| Same-generation alias of active/current/receipt-ancestor data | \u274c All three new regressions fail on unchanged 049 engine code | \u2705 All three pass |
| Valid mixed legacy upgrade with distinct generations | Supported | \u2705 Partial SUM 1800, full SUM 4611; original generation-1 receipt survives |
| Previously released 0.3.16 reads CAT5 | Rejects unsupported format | Remains unchanged |

[Exact-frame semantic probe and all five cases](benchmarks/trial-050-generation-identity/semantic-recovery.json), [three-test failing source snapshot](benchmarks/trial-050-generation-identity/regression-before-fix/), [expected failures](benchmarks/trial-050-generation-identity/regression-before-fix.txt), [passing regressions](benchmarks/trial-050-generation-identity/regression-after-fix.txt), [independent correctness audit](benchmarks/trial-050-generation-identity/correctness-audit.json). Both old candidates reproduce 400 on separate copies; the original fixture remains unchanged. This is an inconsistent-restore case: ordinary writers already allocate unique generations.

## Fresh correctness and recovery qualification

- \u2705 **85 debug and 85 release Rust tests**, formatting and strict Clippy for ordinary/fault builds pass. Only catalog validation and the three regression tests change from 049; synchronization, acknowledgment, reader kernels and file bytes remain unchanged.
- \u2705 **64 publication cut cases and 22 corruption/truncation cases**, **16 source fault cases, 8 source forced kills and 32 concurrent ingestion forced kills** pass. Identified retry generations, acknowledged whole batches and source/output positions survive recovery.
- \u2705 **4,000 SQL differential queries per DuckDB and SQLite**, plus the existing **104 manual/concurrent reader oracles**, pass. Cold/full scrubs, warm-cache corruption detection and repair/reopen checks pass.
- \u2705 CAT2/3/4 valid upgrades pass. All **four 048/049-to-050 and 050-to-048/049 interoperability directions** preserve original receipts, cold reopened data and source checkpoints.
- \u2705 Default source and supported binaries still match released 0.3.16 hashes. No new supported engine or production-readiness claim is made.

[Commands and every failed/passing attempt](benchmarks/trial-050-generation-identity/correctness-gates.json), [publication faults](benchmarks/trial-050-generation-identity/publication-050-faults.json), [source faults](benchmarks/trial-050-generation-identity/source-050-faults.json), [concurrent kills](benchmarks/trial-050-generation-identity/group-050-recovery.json), [cross-candidate checks](benchmarks/trial-050-generation-identity/cross-candidate.json), [source/binary hashes](benchmarks/trial-050-generation-identity/build-provenance.json), [complete source](benchmarks/trial-050-generation-identity/candidate/).

## Performance remains a separate gate

There are **no fresh 050 speed results yet**. Historical [049 paired measurements](TRIAL_049.md) showed a 0.5224 median paired append-p99 ratio on the write workload, three zero-loss one-minute soaks, a failed read guard (1.0838) and remaining 10,000/s overload losses. They do not qualify this successor. [The preserved policy](benchmarks/trial-050-generation-identity/policy.json) requires new alternating 36-case comparisons before any performance decision. The full fresh 60-shape analytical matrix and supported format migration remain unfinished. Current [released analytical results](PERFORMANCE_046.md) and [historical six-engine service wins/losses](SERVICE_047.md) remain separately labeled.

The first semantic harness attempted to hash the exclusively locked runtime marker; the second expected a signature error, while the supported reader correctly rejected CAT5 earlier for trailing catalog bytes. Both harness sources, incomplete proofs, logs and fixtures are preserved. No engine correction or performance gate was relaxed to hide those failures. A raw source-fault description retains an older seven-cut label; its actual case list covers eight cuts and sixteen error/exit cases, as the independent audit records.

Physical power loss, extreme filesystem/device failures, longer sustained service, crash-orphan reclamation, empty-output source checkpoints and distributed fencing remain outside this qualification. No compilation or correctness job overlapped timed workloads; no timed workload was run in this hardening stage.
'''
(root / 'TRIAL_050.md').write_text(text, encoding='utf-8')
for name in ['README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']:
    p = root / name
    s = p.read_text(encoding='utf-8')
    pos = s.index('\n') + 1
    p.write_text(s[:pos] + '\n**Verified development hardening 050:** [CAT5 restore identity fix, failing/passing regressions and full recovery checks](TRIAL_050.md). Supported 0.3.16 remains unchanged; fresh performance qualification is pending.\n' + s[pos:], encoding='utf-8')
p = root / 'TRIAL_049.md'
s = p.read_text(encoding='utf-8')
s += '\nPost-timing counters confirm **zero retained-file reopen calls**. Synchronization consumed 44,748.187 ms, **75.29%** of 59,430.855 ms combined writer/compaction time; stage counts and commit groups differ from the baseline, so these totals are not per-request speed ratios. [Measured follow-up](benchmarks/trial-049-follow-up.json). The restore identity defect is fixed and fully correctness-tested in [isolated successor 050](TRIAL_050.md); neither candidate is promoted, and 050 has no fresh speed results yet.\n'
p.write_text(s, encoding='utf-8')
proof = {'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'trial_promoted': False,
         'qualification_stage': 'correctness only; fresh performance pending',
         'runtime_lock_markers_excluded': True,
         'copied_files': {p.relative_to(dest).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in dest.rglob('*') if p.is_file()}}
(root / 'benchmarks/trial-050-preservation.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'preserved_files': len(proof['copied_files']), 'tests_each_mode': 85,
                  'new_performance_claim': False, 'trial_promoted': False}))
