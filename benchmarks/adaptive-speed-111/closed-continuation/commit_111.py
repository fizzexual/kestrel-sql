"""Record every adaptive111 before/after and exact restored negative evidence."""
from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, json, shutil, subprocess

R = Path('D:/Codex/Kestrel')
WORK = R / 'work'
REPO = R / 'outputs/kestrel-sql'
W = WORK / 'perf-111'
OUT = REPO / 'benchmarks/adaptive-speed-111'

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

guard = sorted(WORK.glob('guard-final-111-*.json'))[-1]
assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
parent = load(WORK / 'commit-110-proof.json')['head']
assert git('rev-parse', 'HEAD').strip() == parent
assert not git('diff', '--name-only') and not git('diff', '--cached', '--name-only')
preserved = load(OUT / 'preservation-proof.json')
restored = load(OUT / 'restored-audit-proof.json')
complete = load(OUT / 'complete-audit-proof.json')
native = complete['native']
assert preserved['complete'] and preserved['all_originals_and_frozen_inputs_retained_unchanged']
assert restored['replay_equals_original_complete_audit'] and complete == load(W / 'complete-audit-proof.json')
assert complete['correctness_passed'] and not complete['release017_qualified']
assert (native['identity_failed'], native['candidate_guards_failed'], native['goals_failed']) == (16, 6, 17)
assert complete['service']['cases'] == 252 and complete['service']['status'] == 'UNSTARTED_UNTESTED'
assert len(native['goals']) == 42
protected = {name: sha(REPO / name) for name in git(
    'ls-files', 'src', 'tests', 'examples', 'Cargo.toml', 'Cargo.lock',
    'verification.json', 'OVERNIGHT_2026-10-07.md').splitlines()}
assert all(sha(REPO / name) == expected for name, expected in load(
    WORK / 'perf-105/policy.json')['baseline_source_sha256'].items())

closed = OUT / 'closed-continuation'
assert not closed.exists()
closed.mkdir()
logs = {}
for name in ['build-111-v2.log', 'preflight-111-v2.log', 'preperformance-111-v2.log', 'native-111-v2.log', 'native-audit-111-v2.log', 'prefix-audit-111.log', 'profile-native-111.log', 'record-rejection-111.log', 'complete-audit-111-v3.log', 'preserve-v3-111.log', 'clock-metadata-111-attempt1.log', 'clock-metadata-111.log', 'update-next-built111.log', 'update-next-ready111.log', 'update-next-rejected111.log']:
    raw = (WORK / name).read_bytes()
    path = closed / (name + '.gz')
    path.write_bytes(gzip.compress(raw, mtime=0))
    assert gzip.decompress(path.read_bytes()) == raw
    logs[name] = {'raw_sha256': hashlib.sha256(raw).hexdigest(),
                  'gzip_sha256': sha(path), 'byte_exact': True}
(closed / 'raw-log-proof.json').write_text(json.dumps(logs, indent=2) + '\n', encoding='utf-8', newline='\n')
assert json.loads((WORK / 'preserve-v3-111.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
shutil.copy2(Path(__file__), closed / Path(__file__).name)
shutil.copy2(guard, closed / guard.name)
for name in ['README.md', 'BENCHMARK_HISTORY.md']:
    shutil.copy2(REPO / name, closed / (name + '.before-111'))

report = '# Adaptive engine trial111\n\nThe candidate implements workload-dependent collection, query-shape dispatch,\nvalidated duplicate replay and bounded long-scan read-ahead. **Release\nqualification fails.** Supported main stays0.3.16; isolated0.3.17 metadata is\nunreleased. This is not a new competitor comparison or universal benchmark win.\n\nThe exact107 collector chooses immediate isolated work, finite small-group\nlookahead or pressure draining. Exact109 query fusion and110 durable-ID replay\nremain. Trial111 chooses read-ahead only for at least eight requested blocks,\nwith the window chosen from needed-column count, at most eight blocks per\ncolumn and512KiB total payload. Short/wide/prefix/full-verification fallbacks\nremain; per-consumed-block CRC is checked. Read buffers remain query-local.\nNo source/WAL/ACK, publication, file-format or maintenance contract changes.\n\nFresh772 tests across eight debug/release configurations and five strict\nall-target lints passed, including six new dispatch/correctness/bounds/memory/\ncorruption tests. Fresh359-command recovery,28 fault cases,10 corruptions,\nCAT2/CAT3,two byte fixtures,256 anonymous ACKs,two named scenarios and300 cold\nSQLite SQL checks pass. Excluded four Native/two service smokes,48 order and29\nnegative checks pass. The complete66-statement pre-timing provenance prefix\npasses. All324 Native cases ran once;479,232 ACKs and2,921,356,800 full CRC bytes\nindependently pass exact rows,receipt generations,indexes,SQL,quantiles,balanced\norders and frozen provenance. Native CPU/RSS were not measured. Physical power\nloss and resource exhaustion were not tested.\n\nPerformance fails16/153 A/A controls,6/171 guards and17/42 goals. All prior\ncontrols/guards/goals remain;12 grouped-query goals were added before code.\nAll252 service cases remain UNSTARTED/UNTESTED. No numerical retry, selected\nround/scope or loosened gate occurred. Supported0.3.17 is not qualified.\n\n## Goals verified in full and both halves\n\nFive goals pass their targets and baseline controls in all three required\nscopes. These are specific Native comparisons against0.3.16. Percentages use\npaired within-round ratios and can differ from quotients of displayed medians.\n\n| Workload | Metric | Unit | Before median | After median | Full A/A | Paired candidate/A | Improvement | Halves |\n| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |\n'
for item in complete['all_scope_controlled_goal_results']:
    row=next(r for r in native['summaries'] if r['scope']=='full' and r['workload']==item['workload'] and r['metric']==item['metric'])
    unit,scale=('us',1) if row['workload'].startswith('queries-') else ('ms',1/1_000_000)
    report+=f"| {row['workload']} | {row['metric']} | {unit} | {row['before_median']*scale:.6f} | {row['after_median']*scale:.6f} | {row['AA']:.8f} | {row['CA']:.8f} | {(1-row['CA'])*100:.2f}% | both pass |\n"
report += "\nGrouped full median paired improvements are6.12% ordered and4.92% late. Both\nmiss their10% goals. Group p95 half controls fail; no grouped goal qualifies\nacross all scopes. Calibrated regressions remain in sparse-anonymous p95 half1,\npressure-anonymous p99 half2,late narrow-window median/p95 half2. Their causes\nare not established. Pressure profiles show about143 pressure groups and only\ntwo coalescing groups with at most100us selected wait; this does not justify\nattributing the pressure tail exclusively to intentional collection waiting.\n\nQPC metadata returns10MHz/100ns ticks, and Python perf_counter reports QPC.\nQuantization may affect very short intervals; this is not a causal proof or a\nclaim about Rust's implementation. The first sandbox-denied metadata write,\nunchanged successful helper and both logs are retained. An unexecuted negative\nclosure output draft and exact output-key refinement are also retained. No\nsource, Native result or gate changed.\n\n## Every before/after and gate\n\nAll171 full/half comparisons follow. Live units are milliseconds,queries/replay\nmicroseconds,disk bytes. Controls require0.95..1.05; guards require at most1.05.\nSmall-write p99 goals require0.95; completion/filter/replay/grouped goals0.90.\nAll maxima/raw stalls remain preserved.\n\n| Scope | Workload | Metric | Unit | Before median | After median | A/A | Control | Candidate/A | Regression | Goal |\n| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- |\n"
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

Next justified scan investigation: eliminate the additional window-to-scratch
copy and keep the original Reader/fallback layout and method unchanged. The
present source adds that copy for every consumed block; this motivates a new
bounded borrowed-block path, not an exclusive bottleneck claim. New work needs
a fresh number,predeclared controls and complete qualification. Ingestion tail
causes remain unresolved. Older106/107 rejection and108 diagnostic archival
closures remain pending; every original and failure is safe.

See [reproduction](benchmarks/adaptive-speed-111/REPRODUCE.md),
[complete audit](benchmarks/adaptive-speed-111/complete-audit-proof.json),
[restored audit](benchmarks/adaptive-speed-111/restored-audit-proof.json),
[Native raw replay](benchmarks/adaptive-speed-111/native-audit.json) and
[decision/unstarted service](benchmarks/adaptive-speed-111/native-rejection-decision.json).
The [Rust buffered-reader documentation](https://doc.rust-lang.org/std/io/struct.BufReader.html)
supports batching repeated small reads, not the size of a Kestrel improvement.
'''
path = REPO / 'ADAPTIVE_ENGINE_111.md'
assert not path.exists()
path.write_text(report, encoding='utf-8', newline='\n')
for name in ['README.md', 'BENCHMARK_HISTORY.md']:
    path = REPO / name
    before = path.read_bytes()
    first, rest = before.split(b'\n', 1)
    path.write_bytes(first + b'\n\nLatest adaptive engine trial: [111 complete before/after results](ADAPTIVE_ENGINE_111.md) fails16 A/A controls,6 guards and17 goals. Five specific Native goals pass full and both halves; grouped targets and release qualification fail. Fresh772 tests,recovery and exact restored evidence pass;0.3.17 remains unreleased and0.3.16 supported.\n' + rest)

git('add', '--', 'ADAPTIVE_ENGINE_111.md', 'README.md', 'BENCHMARK_HISTORY.md', 'benchmarks/adaptive-speed-111')
git('diff', '--cached', '--check')
names = git('diff', '--cached', '--name-only').splitlines()
assert all(name in ['ADAPTIVE_ENGINE_111.md', 'README.md', 'BENCHMARK_HISTORY.md'] or name.startswith('benchmarks/adaptive-speed-111/') for name in names)
git('commit', '-m', 'Preserve bounded scan trial111 rejection and exact restored evidence')
assert protected == {name: sha(REPO / name) for name in protected}
assert not git('status', '--porcelain').strip()
proof = {'complete': True, 'head': git('rev-parse', 'HEAD').strip(), 'parent': parent,
         'repository_clean': True, 'supported_engine_tests_examples_Cargo_verification_and_overnight_byte_exact': True,
         'candidate_implemented_and_correctness_qualified': True, 'performance_qualified': False,
         'release017_qualified': False, 'all_failed_and_raw_evidence_retained': True,
         'all_full_and_half_before_after_metrics_reported': len(native['summaries']),
         'utc': datetime.now(timezone.utc).isoformat()}
path = WORK / 'commit-111-proof.json'
assert not path.exists()
path.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(proof))
