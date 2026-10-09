"""Record the complete rejected104 cohort after actual preservation exit."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess

ROOT = Path('D:/Codex/Kestrel')
WORK = ROOT / 'work'
REPO = ROOT / 'outputs/kestrel-sql'
OUT = REPO / 'benchmarks/reusable-sync-speed-104'
W = WORK / 'perf-104'
PARENT = '532c8a33234323a780cdc9e3ed0544d6ef93ba70'

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def save(path, value):
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')

def git(*args):
    result = subprocess.run(['git', '--no-optional-locks', '-c', 'safe.directory=' + REPO.as_posix(),
        '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
        '-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
        '-C', str(REPO), *args], capture_output=True, text=True)
    assert result.returncode == 0, (args, result.returncode, result.stdout, result.stderr)
    return result.stdout

guard = sorted(WORK.glob('guard-final-104-*.json'))[-1]
assert load(guard)['active_processes'] == [] and load(guard)['verified_idle_terminal_reset']
assert git('rev-parse', 'HEAD').strip() == PARENT
assert not git('diff', '--name-only') and not git('diff', '--cached', '--name-only')
preserved = load(OUT / 'preservation-proof.json')
restored = load(OUT / 'restored-audit-proof.json')
complete = load(OUT / 'complete-audit-proof.json')
assert preserved['complete'] and preserved['all_originals_and_frozen_inputs_retained_unchanged']
assert restored['passed'] and restored['replay_equals_original_complete_audit']
assert complete['correctness_passed'] and not complete['performance_qualified']
assert complete == load(W / 'complete-audit-proof.json')
closed = OUT / 'closed-continuation'
assert not closed.exists()
closed.mkdir()
for name in ['preserve-104.log', 'audit-complete-104.log', 'audit-service-104.log', 'commit_104.py']:
    shutil.copy2(WORK / name, closed / name)
assert json.loads((closed / 'preserve-104.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
shutil.copy2(guard, closed / guard.name)
for name in ['README.md', 'BENCHMARK_HISTORY.md']:
    shutil.copy2(REPO / name, closed / (name + '.before-104'))

native = load(W / 'native-audit.json')
service = load(W / 'audit.json')
assert [native[k] for k in ['identity_failed', 'candidate_guards_failed', 'goals_failed']] == [10, 1, 2]
assert [service[k] for k in ['lost', 'identity_failed_total', 'candidate_failed_total', 'goals_failed']] == [2782, 3, 9, 4]
rows = []
for scope in native['scopes']:
    if scope['scope'] == 'full':
        for item in scope['checks']:
            if item['metric'] in ['append_p50_ns', 'append_p99_ns']:
                rows.append(f"| {scope['history']} {item['metric'].replace('append_', '').replace('_ns', '')} | {item['before_median_ns']/1e6:.6f} | {item['after_median_ns']/1e6:.6f} | {item['CA_median']:.9f} | {item['AA_median']:.9f} |")
service_rows = []
for scope in service['scopes']:
    if scope['scope'] == 'full':
        for row in scope['summaries']:
            before = row['variants']['baseline_a']['median_case_p99_ms']
            after = row['variants']['candidate']['median_case_p99_ms']
            comparisons = row['comparisons']
            for key in (['overall'] if row['profile'] == 'read' else ['overall', 'append']):
                ca = comparisons['primary_candidate_over_a']['paired_ratios'][key]['median']
                aa = comparisons['identity_b_over_a']['paired_ratios'][key]['median']
                service_rows.append(f"| {row['profile']} {key} p99 | {before[key]:.6f} | {after[key]:.6f} | {ca:.9f} | {aa:.9f} |")

report = f'''# Combined overlap/reusable synchronization speed104 — October9,2026

**Rejected.** Native qualification fails10/30 identical-baseline controls,1/30 candidate guard and2/12 improvement goals. Service qualification fails3/45 controls,9/51 guards and4/6 goals, with **2,782 lost offers**. Supported0.3.16 stays byte-exact;0.3.17 remains unqualified. No scope is selected to overturn the complete decision.

All44 source files match final103. Fresh normal A/B use the same `async-reclaim,benchmark-shutdown` binary; C adds `reusable-sync-103`, including101 overlap. This measures the combined change versus isolated normal async, rather than pure worker reuse or a direct supported0.3.16 comparison. No061/tracing/fault/profile features enter timed artifacts. Both original synchronization calls, completed matching job, rename-before-ACK, actual worker join, receipts, pins and lease remain intact.

Both fixed cohorts completed144 cases:24 rounds, two independently balanced12-round halves, all six permutations twice per history/profile per half. Native seed10410 uses two histories and512 durable100-row appends per case. Service seed10411 uses1M starting rows,64 clients,100-row appends, read2000offers/s for8s and25%-write500/s for20s. Ratios are medians of within-round C/A and B/A; displayed medians are descriptive and their quotient need not equal the paired ratio. All stalls, numerical misses, raw losses and slower rounds remain. No added rounds, selective reruns, changed gates or durability reduction occurred.

| Native full-cohort metric | Before ms | After ms | Paired C/A | Identical B/A |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

Full native p50/p99 signals do not qualify the complete native change:10 repeatability failures, a half-cohort maximum guard of1.156145922 and two tail goals fail. All73,728 publications,73,872 historical catalogs/original receipt generations,290,193,408 independently checked CRC bytes and same-round current/historical file bytes pass. Two append events above100ms remain.

| Service full-cohort metric | Before ms | After ms | Paired C/A | Identical B/A |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(service_rows)}

Service accounts for1,872,000 offers:1,869,218 successful,2,526 producer-queue drops,256 expiries and0 executed errors. Baseline B loses81 in case20/round4; candidate loses2,701 in case27/round5. Baseline A loses0. Candidate case27 append p99 is5,789.5685ms, maximum5,943.5444ms. These are failed/unexecuted offered requests, not acknowledged data loss. All178,581 acknowledged batches survive independent cold reopen, full3,884,594,400-byte CRC/index/NumPy row references and2,880 query windows. All288 initial/cold native processes actually join and exit0. Every4,309 request event above100ms stays in raw populations. No exclusive physical disk/OS cause is established.

Full write-overall C/A0.936587183 numerically meets5%, but append C/A1.040837570 regresses about4.1%. Half1 overall0.985255017 and append1.040837570 miss both goals; half2 overall0.876210546 meets5% and append1.060792339 misses10%. Read full paired p99 is1.062785102, exceeding its5% guard. CPU is diagnostic only. NativeCPU/RSS were not measured.

Fresh exact-feature debug/release suites execute406 tests and two strict lints. Four finite12,000-group backlog controls verify48,000 ACKs, physical ceilings, pins and original named receipts. Four native/two service smokes,24 cold CLI-versus-SQLite controls and29 synthetic invalid controls pass before the frozen cohort. Full103 correctness916 tests/832 coupled/104 publication/26 source/22 corruption/old-format/byte/restoration checks are **reused**, not recounted as fresh104 tests. Every13,744 pre-timing frozen input remains exact.

Preservation is complete: **{len(preserved['parts'])} bounded ZIP parts,{preserved['files']:,} files,{preserved['directories']:,} directories,{preserved['logical_bytes']:,} logical bytes**. Every memberCRC/order/offset/size, full original/restored fileSHA and exact file/directory set passes before and after complete independent restored replay. The replay recomputes original gates, outcomes, quantiles, historical/current references, resources, ownership/lifecycle, backlog, smokes, SQLite and frozen provenance with zero Native/timer launches or existing-file changes. Only inventoried regenerable targets/Python caches are excluded; originals, tmp/unit stores, failures and empty directories remain. Closed packager stdout is a separately hashed supplement after actual exit. No privateGitHub backup of104 is verified and no raw data is deleted.

Evidence: [policy](benchmarks/reusable-sync-speed-104/policy.json), [complete decision](benchmarks/reusable-sync-speed-104/complete-audit-proof.json), [preservation](benchmarks/reusable-sync-speed-104/preservation-proof.json), [restored replay](benchmarks/reusable-sync-speed-104/restored-audit-proof.json), [reproduction](benchmarks/reusable-sync-speed-104/REPRODUCE.md). OriginalD:/Codex/Kestrel/work/perf-104; restorationD:/Codex/Kestrel/work/restored-reusable-sync-speed-104.

The user's new direction is an optional adaptive execution policy, starting from the exact supported engine in a separately declared105 or later experiment. Sparse/concurrent/pressure collection may choose different bounded behavior; that is a new code hypothesis, not a104 gain. Actual integration and relevant analytical/service/sustained/overload/source/retry/recovery/compatibility/competitor/restoration checks still precede0.3.17 adoption. Work remains private on this computer. The reset is expired without mutation; no force-quit, abandoned-chat resume or old task/automation activation occurs.
'''
destination = REPO / 'REUSABLE_SYNC_SPEED_104.md'
assert not destination.exists()
destination.write_text(report, encoding='utf-8', newline='\n')
for name in ['README.md', 'BENCHMARK_HISTORY.md']:
    path = REPO / name
    before = (closed / (name + '.before-104')).read_bytes()
    first = before.index(b'\n') + 1
    addition = b'\n[104 complete native/service rejection and exact restoration](REUSABLE_SYNC_SPEED_104.md): 2,782 lost offers; all ACKs preserved. Supported0.3.16 unchanged; adaptive work is next.\n\n'
    path.write_bytes(before[:first] + addition + before[first:])
    assert before[first:] in path.read_bytes()
save(closed / 'closed-log-proof.json', {'utc': datetime.now(timezone.utc).isoformat(),
    'files': {p.name: sha(p) for p in closed.iterdir() if p.is_file()},
    'actual_preserver_exit0_observed_before_execution': True,
    'no_frozen_evidence_normalization': True})
git('add', '--', 'README.md', 'BENCHMARK_HISTORY.md', 'REUSABLE_SYNC_SPEED_104.md', 'benchmarks/reusable-sync-speed-104')
names = git('diff', '--cached', '--name-only').splitlines()
assert all(n in ['README.md', 'BENCHMARK_HISTORY.md', 'REUSABLE_SYNC_SPEED_104.md'] or n.startswith('benchmarks/reusable-sync-speed-104/') for n in names)
git('diff', '--cached', '--check')
print(git('commit', '-m', 'Preserve complete native and service104 rejection and restored evidence'), flush=True)
head = git('rev-parse', 'HEAD').strip()
assert not git('status', '--porcelain')
assert not git('diff', '--name-only', PARENT, head, '--', 'src', 'tests', 'examples', 'Cargo.toml', 'Cargo.lock', 'verification.json', 'OVERNIGHT_2026-10-07.md')
save(WORK / 'commit-104-proof.json', {'utc': datetime.now(timezone.utc).isoformat(), 'complete': True,
    'parent': PARENT, 'head': head, 'staged_files': len(names), 'repository_clean': True,
    'supported_source_tests_examples_Cargo_verification_and_overnight_byte_exact': True,
    'performance_or_adoption_not_qualified': True, 'no_remote_upload_or_raw_deletion': True})
print(json.dumps({'complete': True, 'head': head, 'staged_files': len(names)}), flush=True)
