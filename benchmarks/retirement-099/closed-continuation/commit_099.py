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
W = WORK / 'perf-099'
O = R / 'benchmarks/retirement-099'
RESTORE = WORK / 'restored-retirement-099'
PARENT = 'c475c3424f20b260ab9021336fe8146ca3a23433'
PATHS = ['RETIREMENT_099.md', 'README.md', 'BENCHMARK_HISTORY.md', 'RELEASE_TARGET_0_3_17.md', 'benchmarks/retirement-099']


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


guard_path = sorted(WORK.glob('guard-precommit-099-*.json'))[-1]
guard = load(guard_path)
assert not guard['active_processes'] and guard['reset_phase'] == 'waiting-for-full-codex-exit'
assert git('rev-parse', 'HEAD') == PARENT
assert git('status', '--porcelain') == '?? benchmarks/retirement-099/'
preserved = load(O / 'preservation-proof.json')
restored = load(O / 'restored-audit-proof.json')
audit = load(W / 'audit.json')
assert preserved['complete'] and restored['passed']
assert restored['native_launches'] == restored['performance_timer_launches'] == 0
assert audit['correctness_passed'] and (audit['identity_failed'], audit['profile_guards_failed']) == (4, 0)
assert not audit['profile_controls_qualified'] and not audit['material_writer_retirement_hypothesis_supported']
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

cost_rows = []
for row in audit['cost_criteria']:
    cost_rows.append(f"| {row['history']} | {row['scope']} | {row['median_case_inner_poll_p99_ns'] / 1e6:.6f} | "
        f"{row['median_case_append_p50_ns'] / 1e6:.6f} | {row['poll_p99_over_append_p50']:.9f} | "
        f"{'pass' if row['matching_scope_calibrated'] else 'fail'} |")
miss_rows = []
for scope in audit['scopes']:
    for check in scope['checks']:
        if not check['AA_passed']:
            miss_rows.append(f"| {scope['history']} | {scope['scope']} | {check['metric']} | {check['AA_paired_median']:.16f} |")
assert len(miss_rows) == 4 and not audit['events_over_100ms']
report = f'''# Retirement diagnostic 099 — October 9, 2026

**Trial 099 is unqualified. Four of 48 baseline repeatability checks fail; all 48 profiling guards pass.** Every fixed case and independent data/lifecycle check passes, but the declared rule requires calibration across both histories, the full cohort and both halves. The result does not justify implementing handle offload or adopting a speed change. Supported 0.3.16 remains byte-exact. 0.3.17 still needs integrated correctness, recovery and fair performance qualification; no release date or all-benchmark claim follows this diagnostic.

The numerical signal is completed retirement polling around 1.1 ms, about 55% of the median ordinary append duration in this finite fixture. All six numerical material-cost checks exceed both predeclared thresholds (100 microseconds and 5% of ordinary append p50). The prerequisite calibration nevertheless fails. Named-history controls pass, but choosing that history would violate the declared complete decision. These measurements include original tracking reconciliation and retained object/stream destruction; they neither isolate file close cost nor explain service p99 causally.

| History | Scope | Median case inner poll p99, ms | Median case append p50, ms | Poll / append | Scope calibration |
| --- | --- | ---: | ---: | ---: | --- |
{chr(10).join(cost_rows)}

The four identical-baseline B/A misses below are outside the fixed 0.90–1.10 band. They are computed as medians of per-round ratios, including every declared case. Profile C/A must be <=1.10 for each metric and scope; all 48 checks pass. C/B is diagnostic only. No cases were selectively repeated, no extra rounds were added, and no threshold, comparator, budget or durability rule changed.

| History | Scope | Metric | Identical B/A |
| --- | --- | --- | ---: |
{chr(10).join(miss_rows)}

The policy was declared at 2026-10-09T06:33:52.760862Z, before preparation, builds or timers. Its SHA256 is `1853ca1638e9227517f67ff5ce32bd0a18165bb84769505637b530522744170c`. The cohort has 144 cases, 24 rounds and two independently balanced 12-round halves. Each history uses all six permutations twice per half, seed 9910; histories alternate by round. A/B/C use the same normal release executable. A and B call the exact original `Reclaimer.poll` body with a common outer clock; C places one additional inner clock around that same body. The underlying Archive, worker, Live, publication and poll bodies remain byte-exact against the repaired 098 source. Only cfg wrappers/tests, feature/export declarations and the new native driver are added. Neither faults nor traces are compiled into the timed artifacts.

Each fresh native archive has three columns (ts, value, kind), starts with 32,768 rows, and publishes 256 durable groups of 100 rows. Named groups preserve their actual original ACK generations and full digests. Four cycles compact 32 small inputs and retire 32 segments per cycle. A real snapshot pin holds those segments through compaction and public catalog cleanup, which occur outside the poll clocks. After dropping the pin, original worker steps retire 20 then 12 files. Poll timing starts only after done-Acquire and manager-only pending-batch ownership are verified, with exact retained segment references and cached stream counts. Cycles 1/3 clear existing idle handles; cycles 2/4 run a real grouped scan to populate streams. “Cold” means cleared handles, not a cold operating-system cache. No causal cached-versus-cleared comparison is claimed.

There are eight poll windows per case, four in each handle condition. Nearest-rank case p99 is therefore the maximum of eight observations (or four per condition), with limited tail precision. Ordinary append p50/p99 comes from 256 publications per case. All metadata, filesystem inventories, queries, checksums and JSON serialization are outside the poll clocks. This is a native diagnostic, with no full service lifetime RSS/CPU, queue, overload, competitor or sustained service tail qualification.

| Completed checks | Result |
| --- | --- |
| Repaired source debug/release suites | 92 + 92 = 184 fresh tests pass |
| Default, async, profile and combined strict lints | All four pass |
| Fixed cases / original poll windows / inner windows | 144 / 1,152 / 384 |
| Durable append publications / named receipt records | 36,864 / 18,432 |
| Independent full current data CRC checks | 201,719,808 bytes, all pass |
| Final store references | Every 58,368-row store, generation 261, full NumPy rows/indexes and named receipt generations/digests pass |
| Retired files | 18,432 exact deletions; pending/orphan/current files unchanged |
| Actual worker lifecycle | Every native worker joins, pending batches empty, selected/deleted 128 and failures zero per case |
| Lease and snapshot controls | Pin survives owner drop; joined manager retains lock until its actual drop; cold reopen then passes |
| New wrapper / original worker unit stores | 10 / 38 independently decoded |
| Excluded complete native smokes / old-current CLI SQL references | Four / 16 comparisons against SQLite pass |
| Invalid synthetic records and orders | All 17 rejected; zero Native/timer launches in validation |
| Events longer than 100 ms | None in the completed append/poll records |

The first sandbox declaration attempt stopped before directory creation or any Native work; the unchanged declaration was subsequently run with approved filesystem access. The first source build failed on two probe-driver type/API mismatches, before Native tests or external smokes. Every source, helper, policy, log, run order, toolchain record and all 36 compiled executable copies are preserved. The repair changes only the example's integer conversion and original append-result handling; anonymous generation is read outside the append clock. A separate fresh D: target then runs both qualifying suites and four lints. The original target remains untouched. Earlier 096/097/094 external fault/corruption matrices are explicitly reused where applicable, not counted as fresh tests here; this probe adds no production algorithm or fault recovery change.

All 5,227 pre-timing inputs remain exact. Native stdout, stderr, birth identities, exit status, every append/poll journal entry, stores, locks, ownership state, finite failure attempts, helpers and empty directories are preserved. The completed pure audit runs against originals and independently against restoration, recomputing every fixed comparison, both halves, CRC/index/NumPy/receipt/digest/generation reference, unit store, SQL/smoke result and failed-build file set. Both audits agree exactly and launch zero Native processes or performance timers.

Preservation is complete: **{len(preserved['parts'])} bounded ZIP parts / {preserved['files']:,} files / {preserved['directories']:,} directories / {preserved['logical_bytes']:,} logical bytes**. The previously verified 64 MiB chunk / 80 MiB logical part engine is reused byte-exact. Every archive member CRC/order/offset/size, full original/restored file SHA and exact file/directory set passes before and after restored replay. Only inventoried regenerable target/Python caches are excluded, with all originals retained. The packager stdout is copied only after actual exit and retained in a separately hashed closed-continuation supplement.

Evidence: [policy](benchmarks/retirement-099/policy.json), [complete decision](benchmarks/retirement-099/decision-summary.json), [preservation](benchmarks/retirement-099/preservation-proof.json), [restored audit](benchmarks/retirement-099/restored-audit-proof.json), [reproduction](benchmarks/retirement-099/REPRODUCE.md). Original: D:\\Codex\\Kestrel\\work\\perf-099. Restoration: D:\\Codex\\Kestrel\\work\\restored-retirement-099.

The next experiment needs a different measurement hypothesis grounded in this observed variability and the remaining append publication path. Do not repeat 098 or 099, select the passing named history, add rounds, relax gates or implement blind handle offload. A diagnostic recording actual durable append publication stages and operating-system wait behavior could distinguish remaining costs, but its controls must qualify before attribution. The isolated 061 analytical fix remains separate. Broad native analytical/scan, all six service profiles, mixed/write/minute/overload, competitor, source/retry, crash/corruption/old-format, ownership/pins, resources and restoration checks still precede .17 adoption.

Work remains on this computer and in the private repository. The prepared reset is waiting for full Codex exit and is not executed here. No app is force-closed, no abandoned chat resumed, no old migration task/automation enabled and no C: cleanup repeated. Existing migration/history and every failed experiment remain preserved.
'''
report_path = R / 'RETIREMENT_099.md'
assert not report_path.exists()
report_path.write_text(report, encoding='utf-8', newline='\n')

nav = b'\n\n## Retirement diagnostic 099\n\n[RETIREMENT_099.md](RETIREMENT_099.md): all 144 native cases, data and lifecycle checks pass, but four baseline repeatability gates fail. The approximately 1.1 ms retirement signal remains unqualified; no handle offload or speed adoption. All raw and failed attempts are restored exactly, supported 0.3.16 stays unchanged and .17 is pending.\n'
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
for path in [WORK / 'preserve-099.log', Path(__file__), guard_path]:
    shutil.copy2(path, supplement / path.name)
save(supplement / 'proof.json', {
    'utc': datetime.now(timezone.utc).isoformat(),
    'files': {p.name: sha(p) for p in supplement.iterdir() if p.is_file()},
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
git('commit', '-m', 'Preserve retirement 099 control rejection and complete restored evidence')
head = git('rev-parse', 'HEAD')
assert git('merge-base', '--is-ancestor', PARENT, head) == '' and git('status', '--porcelain') == ''
assert all(sha(R / name) == digest for name, digest in core.items())
save(WORK / 'commit-099-proof.json', {
    'complete': True, 'clean': True, 'head': head, 'parent': PARENT,
    'supported_core': core, 'navigation_prior_sha256': prior_nav,
    'private_only': True, 'remote_not_modified': True,
    'diagnostic_unqualified_not_adopted': True,
})
print(json.dumps({'private_commit': head, 'clean': True, 'supported_core_byte_exact': True,
    'trial099_unqualified_no_adoption': True}))
