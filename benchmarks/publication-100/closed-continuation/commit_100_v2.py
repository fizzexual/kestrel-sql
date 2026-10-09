"""Report the fixed diagnostic rejection and commit preserved evidence privately."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess

ROOT = Path('D:/Codex/Kestrel')
WORK = ROOT / 'work'
R = ROOT / 'outputs/kestrel-sql'
W = WORK / 'perf-100'
O = R / 'benchmarks/publication-100'
RESTORE = WORK / 'restored-publication-100'
PARENT = '876b4ac8303ccecd30b83ee1b2f8ffc28278b89b'
PATHS = ['PUBLICATION_COST_100.md', 'README.md', 'BENCHMARK_HISTORY.md', 'RELEASE_TARGET_0_3_17.md', 'benchmarks/publication-100']


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')


def command(*args):
    return subprocess.run(['git', '--no-optional-locks', '-c', f'safe.directory={R.as_posix()}',
        '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '-C', str(R), *args], capture_output=True)


def git(*args, binary=False):
    result = command(*args)
    assert result.returncode == 0, (args, result.stdout[-3000:], result.stderr[-3000:])
    return result.stdout if binary else result.stdout.decode().strip()


guard_path = sorted(WORK.glob('guard-precommit-100-*.json'))[-1]
guard = load(guard_path)
assert not guard['active_processes'] and guard['reset_phase'] == 'waiting-for-full-codex-exit'
assert git('rev-parse', 'HEAD') == PARENT
assert git('status', '--porcelain') == '?? benchmarks/publication-100/'
preserved = load(O / 'preservation-proof.json')
restored = load(O / 'restored-audit-proof.json')
audit = load(W / 'audit.json')
assert preserved['complete'] and restored['passed']
assert restored['native_launches'] == restored['performance_timer_launches'] == 0
assert audit['correctness_passed'] and (audit['identity_failed'], audit['profile_guards_failed']) == (1, 0)
assert not audit['profile_controls_qualified'] and not audit['material_sync_stage_hypothesis_supported']
for part in preserved['parts']:
    assert sha(O / part['name']) == part['sha256']

core = {p.relative_to(R).as_posix(): sha(p)
    for folder in ['src', 'tests', 'examples'] for p in (R / folder).rglob('*') if p.is_file()}
for name in ['Cargo.toml', 'Cargo.lock', 'OVERNIGHT_2026-10-07.md']:
    core[name] = sha(R / name)
assert set(core) == set(git('ls-tree', '-r', '--name-only', PARENT, '--',
    'src', 'tests', 'examples', 'Cargo.toml', 'Cargo.lock', 'OVERNIGHT_2026-10-07.md').splitlines())
for name, digest in core.items():
    assert hashlib.sha256(git('show', PARENT + ':' + name, binary=True)).hexdigest() == digest

basis = load(WORK / 'publication-basis-100-proof.json')
assert basis['same_publication_body_byte_exact'] and basis['qualified_source_trial'] == 91
old_records = {}
for name in ['decision-summary.json', 'bottleneck-summary.json', 'timing-freeze.json']:
    old_path = WORK / 'perf-091' / name
    committed_path = R / 'benchmarks/trace-controls-091' / name
    assert sha(old_path) == sha(committed_path)
    old_records[name] = sha(old_path)
save(WORK / 'qualified-basis-reuse-100-proof.json', {
    'older_091_records_exact_committed_bytes': old_records,
    'current_and_old_publication_body_exact': basis['publication_body_sha256'],
    'new_100_controls_remain_unqualified': True,
    'no_new_native_or_performance_timer_launches': True,
})
cost_rows = []
for row in audit['cost_criteria']:
    cost_rows.append(f"| {row['history']} | {row['scope']} | {row['median_case_sync_stage_fraction']:.9f} | "
        f"{row['median_case_tail_sync_over_outer_fraction']:.9f} | {'pass' if row['matching_scope_calibrated'] else 'fail'} |")
misses = [(s, c) for s in audit['scopes'] for c in s['checks'] if not c['AA_passed']]
assert len(misses) == 1 and misses[0][0]['history'] == 'named' and misses[0][0]['scope'] == 'half_0'
assert misses[0][1]['metric'] == 'append_p99_ns'
stalls = []
for event in audit['events_over_100ms']:
    case = audit['case_metrics'][event['case_index']]
    stalls.append(f"| {event['case_index']} | {case['history']} | {case['variant']} | {event['group']} | {event['outer_ns'] / 1e6:.4f} |")
assert len(stalls) == 4
report = f"""# Append publication diagnostic 100 — October 9, 2026

**Trial 100 is unqualified: one of 24 identical-baseline checks fails; all 24 profiling guards pass.** All 144 cases and independent data/history/lifecycle checks pass. First-half named append p99 B/A is **1.1144882804632776**, exceeding the fixed 1.10 limit. The complete rule requires both histories, full cohort and both halves, so passing other scopes does not qualify attribution or a code adoption. Supported 0.3.16 remains byte-exact; .17 has no qualification or justified date. No competitor or all-benchmark win is claimed.

This is a new append-only fixture, distinct from rejected 099 retirement polling. Existing original segment/catalog sync clocks show approximately 61% of summed seven publication stages and 62–70% of outer time in case p99-tail groups. All six numerical material-cost criteria pass, but their complete calibration prerequisite fails. These are descriptive wall-clock signals, with no exclusive physical disk/OS wait/CPU explanation or service p99 decomposition. No new inner clock or engine algorithm is introduced.

| History | Scope | Median case sync / seven stages | Median case tail sync / outer append | Scope calibration |
| --- | --- | ---: | ---: | --- |
{chr(10).join(cost_rows)}

The policy was declared before implementation/build/Native/timing, SHA256 `1d6bf0787eaf04ace6f9581a1407d3e9d64b7aebb79d1d973c403ec9a99d8347`. The 144 cases form 24 rounds and two independently balanced 12-round halves, seed 10010, all six permutations twice per half/history and alternating history order. A/B repeat the same normal release probe with async-reclaim enabled. C additionally enables only the preexisting publication-trace feature and reads its last record after each append. No fault or writer-trace feature enters timed artifacts. All Archive/Live/worker/publication bodies remain exact 099 bytes; only a new example and Cargo declaration are added.

The API is original append_group with one IngestBatch. ID/columns are prepared outside the outer clock; command-vector construction and returned receipt are included uniformly in every variant. Every fresh three-column store seeds 32,768 rows, publishes 512 durable 100-row groups and ends with 83,968 rows/generation 513. There is no compaction, reclamation or async worker submission. All 513 catalog and segment generations are retained. Metadata/trace getters, queries, inventories, CRC, retries/collisions, snapshot/lease/cold-open controls and journal serialization/flushing occur outside append clocks; flushing is fixed every 128 groups. OS cache may be warm. This is finite native publication, not a Live service, CPU/RSS/resource-tail, sustained throughput or maximum capacity comparison.

Controls reuse the native diagnostic band of 092/099: B/A 0.90–1.10 and C/A <=1.10 for summed append and p50/p95/p99 in each history/full/half. Ratios are medians of per-round ratios; C/B remains diagnostic. Nearest-rank p99 selects the sixth largest of 512 samples, including every stall. The material criteria require median case sync-stage fraction >=0.50 and median case sync/outer fraction >=0.50 over every group at or above that case's outer p99, including ties, in all six scopes. No gate, comparator, durability, sample selection, round count or budget changes after observation.

| Completed checks | Result |
| --- | --- |
| Fresh normal debug/release suites | 90 + 90 tests pass |
| Fresh profile debug/release suites | 93 + 93 tests pass |
| Strict default/normal/profile/combined lints | All four pass |
| Main durable append publications / C stage records | 73,728 / 24,576 |
| Independent current payload CRC/index/NumPy references | 290,193,408 bytes; every final store passes |
| Main historical catalog envelopes/CRCs/references | 73,872 exact generations pass |
| Named current receipt records | 36,864 original generations and full digests pass, with all historical checkpoint/delta receipts checked |
| Existing profile reconciliation | All C stage sums/counts/histograms and published catalog byte totals reconcile exactly |
| Real snapshot/owner/reopen controls | Seed pin remains readable and retains writer lease after owner drop; actual last-owner drop permits cold reopen |
| Named retry/collision | Exact original generation 18, no new publication/data files; stale trace stays unchanged |
| Complete excluded native smokes / CLI-vs-SQLite queries | Four / 16 pass; all original/profile final data bytes identical |
| Independent smoke histories/current payload | 2,052 catalog generations / 8,060,928 CRC bytes pass |
| Invalid stage/clock/receipt/lifecycle/order fixtures | All 21 rejected with zero Native/performance timers |

All four append events above 100 ms remain in the raw cohort and quantiles:

| Zero-based case | History | Variant | Group | Outer ms |
| --- | --- | --- | ---: | ---: |
{chr(10).join(stalls)}

The traced 134.2308 ms event includes segment write 45.6297 ms, segment sync 45.0279 ms and catalog sync 42.6157 ms. Those observed operation intervals do not establish a physical-device cause, and the untraced stalls cannot be decomposed. No additional rounds or selective reruns were used. There were no build, Native, original audit or preservation failures; harmless guessed report/output listing read errors are retained separately and did not affect any source/raw/timing operation. Prior 096/097/094 fault matrices are reused explicitly, not counted as fresh 100 recovery tests. A production pipeline change would need fresh controlled recovery.

All 13,723 frozen pre-timing inputs remain unchanged. **{len(preserved['parts'])} bounded ZIP parts preserve {preserved['files']:,} files / {preserved['directories']:,} directories / {preserved['logical_bytes']:,} logical bytes**. All original source/artifacts/Native journals/stdio/identities/statuses/history/stores/locks/unit fixtures/validators/helpers and closed logs remain D:. Only inventoried regenerable target/Python caches are omitted, with originals retained. The verified 64 MiB chunk / 80 MiB logical part engine is reused byte-exact. Every member CRC/order/offset/size, full original/restored SHA and exact file/directory set passes before and after a complete restored pure audit. Replay exactly recomputes all raw metrics/controls/stage/profile reconciliations/criteria, every historical catalog/current reference and smoke/SQL check with zero Native/performance-timer launches or existing-file changes. Closed packager stdout and post-cohort source-basis/read records are copied and hashed only after actual closure in closed-continuation.

Evidence: [policy](benchmarks/publication-100/policy.json), [complete decision](benchmarks/publication-100/decision-summary.json), [preservation](benchmarks/publication-100/preservation-proof.json), [restored replay](benchmarks/publication-100/restored-audit-proof.json), [reproduction](benchmarks/publication-100/REPRODUCE.md). Originals: D:\\Codex\\Kestrel\\work\\perf-100. Restoration: D:\\Codex\\Kestrel\\work\\restored-publication-100.

The next code hypothesis has a separate verified basis in qualified 091. A post-cohort static comparison verifies both frozen source hashes and proves the whole current publication body byte-identical to that earlier source (body SHA256 `7a260c1a0269fbd0b0d9cedf6d163fdac0f2e5a153a04d9e0e58054927be01a0`). 091 passed all 39 A/A and 39 profiling controls, and its recorded pooled synchronization fraction is {basis['recorded_091_sync_fraction_of_summed_stages']:.9f} of summed stages. This reuses qualified earlier diagnostic scope and never reclassifies 100. A separately numbered candidate could test scoped overlap of independent segment synchronization with catalog preparation/write/synchronization, joining both before catalog rename and ACK. Both original sync calls, atomic publication, snapshots/lease, poison/unknown-outcome handling, source/receipt/retry contracts and bounded ownership must remain. Thread creation overhead and same-device contention may erase gains. It is only a hypothesis, not declared/implemented/measured/adopted by 100.

Declare a new experiment >=101 before implementation. Preserve the exact feature-disabled path, verify actual error/panic/join/lease behavior and execute fresh coupled publication/worker recovery, old formats/corruption/source/retries plus fair normal same-D native and service A/A/performance/resource checks before considering adoption. Do not repeat 098/099/100, select passing histories/halves, change limits or drop synchronization. Full native analytical/scan, six service profiles, mixed/write/minute/overload/competitor/source/retry/recovery/ownership/pins/resource/restoration and justified isolated 061 integration still precede .17. Repository/history remain private/local on this computer; the prepared reset stays waiting, no app force-quit or old task/automation reactivation, and completed C cleanup is not repeated.
"""
report += '\nPre-commit inspection caught an old packager-log filename in the first generated commit draft. That draft was never executed and changed no report, navigation, staged file, commit, Native/source/raw/policy or gate. Its exact helper/generator/derivation bytes are retained in closed-continuation/draft-commit-v1. The corrected v2 helper copies the actual closed preserve-100.log and all post-cohort basis/read records; numerical rejection and frozen evidence are unchanged.\n'
report_path = R / 'PUBLICATION_COST_100.md'
assert not report_path.exists()
report_path.write_text(report, encoding='utf-8', newline='\n')

nav = b'\n\n## Append publication diagnostic 100\n\n[PUBLICATION_COST_100.md](PUBLICATION_COST_100.md): all 144 cases, historical/current data and lifecycle checks pass, but one named p99 repeatability gate fails. All stages, stalls and unchanged decisions are restored exactly. Unqualified, no adoption; supported 0.3.16 stays unchanged and .17 is pending. A separate static proof retains qualified 091 as the basis for a future code hypothesis.\n'
prior_nav = {}
for name in PATHS[1:4]:
    path = R / name
    old = path.read_bytes()
    prior_nav[name] = hashlib.sha256(old).hexdigest()
    assert old == git('show', PARENT + ':' + name, binary=True)
    path.write_bytes(old + nav)
    assert path.read_bytes().startswith(old)

supplement = O / 'closed-continuation'
assert not supplement.exists()
supplement.mkdir()
for path in [WORK / 'preserve-100.log', Path(__file__), guard_path, WORK / 'prepare_commit_100.py', WORK / 'commit-derivation-100.json', WORK / 'repair_commit_helper_100_v2.py', WORK / 'commit-helper-repair-100-v2-proof.json', WORK / 'inspect_publication_basis_100.py', WORK / 'publication-basis-100-proof.json', WORK / 'publication-basis-100.log', WORK / 'qualified-basis-reuse-100-proof.json', WORK / 'initial-read-errors-100.json']:
    shutil.copy2(path, supplement / path.name)
shutil.copytree(WORK / 'draft-commit-100-v1', supplement / 'draft-commit-v1')
save(supplement / 'proof.json', {
    'utc': datetime.now(timezone.utc).isoformat(),
    'files': {p.relative_to(supplement).as_posix(): sha(p) for p in supplement.rglob('*') if p.is_file()},
    'packager_stdout_copied_after_actual_exit': True,
    'supported_core': core, 'parent': PARENT, 'navigation_prior_sha256': prior_nav,
    'private_only': True,
})
git('add', '--', *PATHS)
staged = git('diff', '--cached', '--name-only').splitlines()
expected_paths = set(PATHS[:4]) | {p.relative_to(R).as_posix() for p in O.rglob('*') if p.is_file()}
assert set(staged) == expected_paths and len(staged) == len(expected_paths)
git('-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
    'diff', '--cached', '--check', '--', *PATHS)
git('commit', '-m', 'Preserve publication 100 control rejection and complete historical evidence')
head = git('rev-parse', 'HEAD')
assert git('merge-base', '--is-ancestor', PARENT, head) == '' and git('status', '--porcelain') == ''
assert all(sha(R / name) == digest for name, digest in core.items())
save(WORK / 'commit-100-proof.json', {
    'complete': True, 'clean': True, 'head': head, 'parent': PARENT,
    'supported_core': core, 'navigation_prior_sha256': prior_nav,
    'private_only': True, 'remote_not_modified': True,
    'diagnostic_unqualified_not_adopted': True,
})
print(json.dumps({'private_commit': head, 'clean': True, 'supported_core_byte_exact': True,
    'trial100_unqualified_no_adoption': True}))
