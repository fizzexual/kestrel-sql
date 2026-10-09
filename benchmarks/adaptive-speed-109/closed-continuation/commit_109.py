"""Record every adaptive109 before/after and exact restored negative evidence."""
from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, json, shutil, subprocess

R = Path('D:/Codex/Kestrel')
WORK = R / 'work'
REPO = R / 'outputs/kestrel-sql'
W = WORK / 'perf-109'
OUT = REPO / 'benchmarks/adaptive-speed-109'

def sha(p):
    with p.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))

def git(*args):
    result = subprocess.run([
        'git', '--no-optional-locks', '-c', 'safe.directory=' + REPO.as_posix(),
        '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
        '-c', 'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
        '-C', str(REPO), *args], capture_output=True, text=True)
    assert result.returncode == 0, (args, result.stdout, result.stderr)
    return result.stdout

guard = sorted(WORK.glob('guard-final-109-*.json'))[-1]
assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
parent = load(WORK / 'commit-105-proof.json')['head']
assert git('rev-parse', 'HEAD').strip() == parent
assert not git('diff', '--name-only') and not git('diff', '--cached', '--name-only')
preserved = load(OUT / 'preservation-proof.json')
restored = load(OUT / 'restored-audit-proof.json')
complete = load(OUT / 'complete-audit-proof.json')
native = complete['native']
assert preserved['complete'] and preserved['all_originals_and_frozen_inputs_retained_unchanged']
assert restored['replay_equals_original_complete_audit'] and complete == load(W / 'complete-audit-proof.json')
assert complete['correctness_passed'] and not complete['release017_qualified']
assert (native['identity_failed'], native['candidate_guards_failed'], native['goals_failed']) == (27, 8, 1)
assert complete['service']['unstarted_cases'] == 252 and not complete['service']['performance_tested']
assert len(native['goals']) == 24
protected = {name: sha(REPO / name) for name in git(
    'ls-files', 'src', 'tests', 'examples', 'Cargo.toml', 'Cargo.lock',
    'verification.json', 'OVERNIGHT_2026-10-07.md').splitlines()}
assert all(sha(REPO / name) == expected for name, expected in load(
    WORK / 'perf-105/policy.json')['baseline_source_sha256'].items())

closed = OUT / 'closed-continuation'
assert not closed.exists()
closed.mkdir()
logs = {}
for name in [
    'build-109.log', 'preflight-109.log', 'preperformance-109.log',
    'native-109.log', 'complete-audit-109-v3.log', 'preserve-v3-109.log',
    'prepare-rejection-109.log', 'profile-native-109.log', 'record-rejection-109.log',
    'prepare-negative-closure-109.log', 'prepare-preserver-109-v3.log',
    'update-next-ready109.log']:
    raw = (WORK / name).read_bytes()
    path = closed / (name + '.gz')
    path.write_bytes(gzip.compress(raw, mtime=0))
    assert gzip.decompress(path.read_bytes()) == raw
    logs[name] = {'raw_sha256': hashlib.sha256(raw).hexdigest(),
                  'gzip_sha256': sha(path), 'byte_exact': True}
(closed / 'raw-log-proof.json').write_text(json.dumps(logs, indent=2) + '\n', encoding='utf-8', newline='\n')
assert json.loads((WORK / 'preserve-v3-109.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
shutil.copy2(Path(__file__), closed / Path(__file__).name)
shutil.copy2(guard, closed / guard.name)
for name in ['README.md', 'BENCHMARK_HISTORY.md']:
    shutil.copy2(REPO / name, closed / (name + '.before-109'))

report = '''# Adaptive engine trial 109

The isolated candidate implements workload-dependent write collection and query
execution. It passes correctness and recovery, and several improvements hold
across the full cohort and both balanced halves. **Release qualification fails.**
Supported main remains 0.3.16; this candidate's 0.3.17 metadata is unreleased.

The writer uses the exact trial 107 collector: immediate sparse work, bounded
small-group lookahead, or draining ready pressure work. Lookahead is capped at
the minimum of the configured cap, half observed successful publication cost,
100 microseconds and 1,024 empty polls. It uses a fixed deadline and the existing
64-command limit. Ordinary queries choose the existing prefix path first,
then fused filtering/aggregation for eligible ungrouped single-column COUNT,
SUM and AVG, otherwise the existing general selection or grouping path.
The public adaptive-engine feature enables adaptive-collection and adaptive-filter.

The fused scan avoids selected-position storage and a second aggregate traversal.
Signed predicates, exact i128 totals, CRC-checked pages, immutable snapshots,
publication, source/WAL/ACK semantics, disk formats and maintenance stay protected.
Default/fixed paths remain available. Native CPU and peak memory were not measured;
the service resource and loss checks remain unstarted because Native qualification
failed. No new competitor or universal benchmark victory is claimed.

724 fresh test executions across eight full debug/release configurations, five
strict all-target lints and independent normal/fault artifact builds passed.
The fresh 359-command external cohort passed 28 publication interruptions,
10 corruptions, CAT2/CAT3 reads, two byte fixtures, 256 concurrent anonymous ACKs,
two named scenarios and 300 cold SQLite-model SQL checks. This does not establish
physical power-loss or resource-exhaustion guarantees.

All 324 predeclared Native cases completed once, with 479,232 acknowledged batches
and 2,921,356,800 full checksum bytes independently verified. All rows, receipts,
indexes, query answers, timing quantiles, raw samples, order and provenance were
replayed. Original gates and 12 small-write goals were retained; 12 required
filter goals were added before source, copies or builds. There were no selected
rounds, extra timers or relaxed gates.

## Measured gains with controls passing in the full run and both halves

The improvement percentages below use the median of within-round candidate/A
ratios. Displayed before/after values are separate medians and their quotient
can differ from that paired comparison.

| Workload and metric | Before | After | Paired improvement |
| --- | ---: | ---: | ---: |
| Small anonymous writes, completion | 2.498380 s | 1.766688 s | 26.32% |
| Small named writes, completion | 2.524958 s | 1.734931 s | 32.58% |
| Small anonymous writes, p99 | 18.597800 ms | 16.615500 ms | 7.03% |
| Ordered data, value-filter median | 2.814350 ms | 2.464050 ms | 11.87% |
| Late data, value-filter median | 2.819800 ms | 2.480050 ms | 12.15% |
| Late data, value-filter p95 | 3.249000 ms | 2.798200 ms | 14.47% |

These individual gains do not qualify the complete candidate. It fails 27 A/A
controls, eight regression guards and one of 24 improvement goals. The ordered
filter p95 half-1 target fails, with its baseline control also failing. Named
write p99 has a failed half-2 control. Calibrated regressions include full-run
receipt replay p95, paired ratio 1.09375, and late-data grouped-query half-2 p95,
ratio 1.08289641. Their exclusive causes are not established. Every failure and
all 252 service specifications remain preserved; those service cases are UNSTARTED
and their correctness/performance are untested.

The first auditor invocation omitted its workspace argument and exited 1 before
audit() ran. The corrected invocation used the exact same frozen auditor and
gates, exited 0 and retained the rejected performance result. Its failed log
remains. No benchmark was rerun for this correction.

## Every before/after, control, regression check and goal

All full-run and half-run metrics follow. Timing units are milliseconds for live
operations, microseconds for queries and receipt replay, and bytes for disk.
A/A passes only within 0.95..1.05. Candidate/A regression limits remain 1.05.
Improvement targets remain 0.95 for small-write p99 and 0.90 for small-write
completion and filter metrics. Raw samples and maxima remain in the archive.

| Scope | Workload | Metric | Unit | Before median | After median | A/A | Control | Candidate/A | Regression | Goal |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- |
'''
for row in native['summaries']:
    keys = ['scope', 'workload', 'metric']
    control = next((item for item in native['controls'] if all(item[key] == row[key] for key in keys)), None)
    guard_row = next(item for item in native['guards'] if all(item[key] == row[key] for key in keys))
    goal = next((item for item in native['goals'] if all(item[key] == row[key] for key in keys)), None)
    if row['metric'] == 'disk': unit, scale = 'bytes', 1
    elif row['workload'].startswith('queries-'): unit, scale = 'us', 1
    elif row['workload'] == 'identified-replay': unit, scale = 'us', 1000
    else: unit, scale = 'ms', 1 / 1_000_000
    control_status = 'n/a' if control is None else ('pass' if control['passed'] else 'FAIL')
    regression = 'pass' if guard_row['passed'] else 'FAIL'
    goal_status = '-' if goal is None else f"{'pass' if goal['passed'] else 'FAIL'} <= {goal['limit']:.2f}"
    report += f"| {row['scope']} | {row['workload']} | {row['metric']} | {unit} | {row['before_median'] * scale:.6f} | {row['after_median'] * scale:.6f} | {row['AA']:.8f} | {control_status} | {row['CA']:.8f} | {regression} | {goal_status} |\n"
report += f'''
## Exact preservation and next work

The archive contains {preserved['files']:,} files, {preserved['directories']:,}
directories, {len(preserved['parts'])} bounded ZIP parts and
{preserved['logical_bytes']:,} logical bytes. All member checksums, order,
offsets, sizes, complete original/restored file hashes and directory sets passed
before and after the complete independent restored audit. It launched no Native
processes or timers and changed no existing files. Only inventoried regenerable
build/Python caches are excluded; all originals remain. Closed raw logs are
byte-exact gzip supplements with both raw and encoded hashes. No complete
verified private GitHub backup or recent raw deletion is claimed.

Next engineering target: avoid general publication-buffer allocation for a
verified duplicate receipt while retaining full submitted-content validation,
the unhealthy-writer check, original generations and the normal publication path
for new IDs. Diagnose grouping separately before attributing or changing it.
New work requires a new experiment number and predeclared controls. Older
106/107 rejection and 108 diagnostic exact-archive closures remain pending;
their original raw data, source and every failure remain stored on D:.

See [complete reproduction](benchmarks/adaptive-speed-109/REPRODUCE.md),
[complete original audit](benchmarks/adaptive-speed-109/complete-audit-proof.json),
[restored audit](benchmarks/adaptive-speed-109/restored-audit-proof.json),
[all native results](benchmarks/adaptive-speed-109/native-audit.json) and
[decision and unstarted service specs](benchmarks/adaptive-speed-109/native-rejection-decision.json).
Borrowed receipt lookup follows [Rust's BTreeMap API](https://doc.rust-lang.org/std/collections/struct.BTreeMap.html#method.get);
that documentation supports the design, not a Kestrel speed claim.
'''
path = REPO / 'ADAPTIVE_ENGINE_109.md'
assert not path.exists()
path.write_text(report, encoding='utf-8', newline='\n')
for name in ['README.md', 'BENCHMARK_HISTORY.md']:
    path = REPO / name
    before = path.read_bytes()
    first, rest = before.split(b'\n', 1)
    path.write_bytes(first + b'\n\nLatest adaptive engine trial: [109 complete before/after results](ADAPTIVE_ENGINE_109.md) shows controlled filter and small-write gains, but fails 27 A/A controls, eight guards and one goal. Correctness/recovery and exact restored evidence pass; 0.3.17 remains unreleased and 0.3.16 supported.\n' + rest)

git('add', '--', 'ADAPTIVE_ENGINE_109.md', 'README.md', 'BENCHMARK_HISTORY.md', 'benchmarks/adaptive-speed-109')
git('diff', '--cached', '--check')
names = git('diff', '--cached', '--name-only').splitlines()
assert all(name in ['ADAPTIVE_ENGINE_109.md', 'README.md', 'BENCHMARK_HISTORY.md'] or name.startswith('benchmarks/adaptive-speed-109/') for name in names)
git('commit', '-m', 'Preserve adaptive engine trial109 gains, failures and exact restored evidence')
assert protected == {name: sha(REPO / name) for name in protected}
assert not git('status', '--porcelain').strip()
proof = {'complete': True, 'head': git('rev-parse', 'HEAD').strip(), 'parent': parent,
         'repository_clean': True, 'supported_engine_tests_examples_Cargo_verification_and_overnight_byte_exact': True,
         'candidate_implemented_and_correctness_qualified': True, 'performance_qualified': False,
         'release017_qualified': False, 'all_failed_and_raw_evidence_retained': True,
         'all_full_and_half_before_after_metrics_reported': len(native['summaries']),
         'utc': datetime.now(timezone.utc).isoformat()}
path = WORK / 'commit-109-proof.json'
assert not path.exists()
path.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(proof))
