"""Record every adaptive112 before/after and exact restored negative evidence."""
from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, json, shutil, subprocess

R = Path('D:/Codex/Kestrel')
WORK = R / 'work'
REPO = R / 'outputs/kestrel-sql'
W = WORK / 'perf-112'
OUT = REPO / 'benchmarks/adaptive-speed-112'

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

guard = sorted(WORK.glob('guard-final-112-*.json'))[-1]
assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
parent = load(WORK / 'commit-111-proof.json')['head']
assert git('rev-parse', 'HEAD').strip() == parent
assert not git('diff', '--name-only') and not git('diff', '--cached', '--name-only')
preserved = load(OUT / 'preservation-proof.json')
restored = load(OUT / 'restored-audit-proof.json')
complete = load(OUT / 'complete-audit-proof.json')
native = complete['native']
assert preserved['complete'] and preserved['all_originals_and_frozen_inputs_retained_unchanged']
assert restored['replay_equals_original_complete_audit'] and complete == load(W / 'complete-audit-proof.json')
assert complete['correctness_passed'] and not complete['release017_qualified']
assert (native['identity_failed'], native['candidate_guards_failed'], native['goals_failed']) == (25, 13, 1)
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
for name in ['build-112-v2.log', 'preflight-112-v2.log', 'preflight-independent-audit-112-v2.log', 'preflight-observation-112.log', 'preperformance-112-v2.log', 'prefix-audit-112.log', 'native-112-v2.log', 'native-audit-112-v2.log', 'profile-native-112.log', 'record-rejection-112.log', 'complete-audit-112-v3.log', 'preserve-v3-112.log', 'update-next-ready112.log', 'update-next-rejected112.log']:
    raw = (WORK / name).read_bytes()
    path = closed / (name + '.gz')
    path.write_bytes(gzip.compress(raw, mtime=0))
    assert gzip.decompress(path.read_bytes()) == raw
    logs[name] = {'raw_sha256': hashlib.sha256(raw).hexdigest(),
                  'gzip_sha256': sha(path), 'byte_exact': True}
(closed / 'raw-log-proof.json').write_text(json.dumps(logs, indent=2) + '\n', encoding='utf-8', newline='\n')
assert json.loads((WORK / 'preserve-v3-112.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
shutil.copy2(Path(__file__), closed / Path(__file__).name)
shutil.copy2(guard, closed / guard.name)
for name in ['README.md', 'BENCHMARK_HISTORY.md']:
    shutil.copy2(REPO / name, closed / (name + '.before-112'))

report = '# Adaptive engine trial112\n\nThe candidate replaces long-scan window-to-scratch copies with borrowed block\nviews while preserving the original Reader structure and fallback method.\n**Release qualification fails.** Supported main stays0.3.16;the isolated\n0.3.17 candidate remains unreleased. This is not a new competitor comparison\nor a universal benchmark win.\n\nWorkload-dependent collection,query-shape fusion and durable-ID replay remain\nbyte-exact from trials107,109 and110. Long streamed scans select query-local\nread windows from requested range and needed-column count:at least eight\nrequested blocks,at most eight blocks per column,and512KiB total logical\npayload. The new method borrows each block directly from the window and checks\nits CRC before decoding. Short,wide,prefix,verification and compaction paths\nretain their original behavior. The pre111 Reader structure,constructors,Drop\nand single-block method are byte-exact;no new Reader state or global cache was\nadded. Cargo,file format,WAL,ACK and publication contracts stay unchanged.\n\nFresh772 tests across eight configurations,five strict all-target lints and\nall normal/fault artifacts pass. The updated private counting test checks\nexact signed bytes,six read/seek operations for38 consumed blocks,range/tails,\npayload budget,truncation,failure invalidation and recovery;these are Read/\nSeek operations,not an assertion of operating-system syscall counts. The five\nparent scan integration tests and all other inherited tests remain byte-exact.\nAll359 recovery commands,28 fault cases,10 corruptions,CAT2/CAT3,two byte\nfixtures,256 anonymous ACKs,two named scenarios and300 cold SQL checks pass.\nThe original preflight API return was unobserved across context compaction;\nits shell exit is not claimed. A fresh strict idle guard0 and independent\nunchanged pure recovery audit0 reproduce the completed proof and verify every\nnative actual wait/exit without relaunching workloads. The honest observation\nand raw logs are retained. Excluded four Native/two service smokes,48 order\nand29 negative controls pass. The complete80-statement pre-timing prefix\nindependently checks source inverses,fallback equality,build/recovery/smokes\nand all12,735 frozen inputs.\n\nAll324 Native cases ran exactly once and the controller actually exited0.\n479,232 ACKs and2,921,356,800 full CRC bytes independently pass raw rows,\nreceipt generations,indexes,SQL,quantiles,balanced orders and immutable inputs.\nPerformance fails25/153 A/A controls,13/171 regression guards and1/42 goals.\nEvery252 service case remains UNSTARTED/UNTESTED because Native qualification\nfailed. No selected scope/round,extra measurement,numerical retry or loosened\ngate occurred. Native CPU/RSS,physical power loss and resource exhaustion were\nnot measured or tested. Supported0.3.17 remains unqualified.\n\n## Goals verified in full and both halves\n\nEight goals pass targets and baseline controls in all three required scopes.\nPercentages use paired within-round ratios and can differ from quotients of\ndisplayed medians. These are specific Native results against0.3.16.\n\n| Workload | Metric | Unit | Before median | After median | Full A/A | Paired candidate/A | Improvement | Halves |\n| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |\n'
assert len(complete['all_scope_controlled_goal_results'])==8
for item in complete['all_scope_controlled_goal_results']:
    row=next(r for r in native['summaries'] if r['scope']=='full' and r['workload']==item['workload'] and r['metric']==item['metric'])
    if row['workload'].startswith('queries-'):unit,scale='us',1
    elif row['workload']=='identified-replay':unit,scale='us',1000
    else:unit,scale='ms',1/1_000_000
    report+=f"| {row['workload']} | {row['metric']} | {unit} | {row['before_median']*scale:.6f} | {row['after_median']*scale:.6f} | {row['AA']:.8f} | {row['CA']:.8f} | {(1-row['CA'])*100:.2f}% | both pass |\n"
report += "\nGrouped medians now meet their10% goals with passing controls in full and both\nhalves:14.00% ordered and11.36% late. Late group p95 improves10.58% in full,\nand its controls/targets also pass both halves. Ordered group p95/filter and\nreplay p99 gains remain control-inconclusive. This trial does not reclassify\nearlier trials' failed or inconclusive results.\n\nCalibrated guard misses remain:full sparse-named p95/p99 and pressure-anonymous\np99;half1 sparse-named p50/p95 and pressure-anonymous p99;half2 sparse-named,\npressure-anonymous and pressure-named p99,and late all-aggregates p95. Other\nguard misses have failing controls and remain inconclusive. The sole goal\nmiss is small-anonymous p99 half2(C/A .978975,target .95,A/A1.040604).\nNo exclusive failure cause is established. The collector's chosen wait alone\ndoes not explain durable publication,compaction,queueing or scheduling tails.\n\n## Every before/after and gate\n\nAll171 full/half comparisons follow. Live units are milliseconds,queries and\nreplay microseconds,disk bytes. Controls require0.95..1.05;guards require at\nmost1.05. Small-write p99 goals require0.95;completion/filter/replay/grouped\ngoals require0.90. Every original maximum and raw stall remains preserved.\n\n| Scope | Workload | Metric | Unit | Before median | After median | A/A | Control | Candidate/A | Regression | Goal |\n| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- |\n"
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

Next justified investigation: diagnose the remaining sparse/pressure ACK
tails by separating publication,compaction,queueing and scheduling evidence.
Avoid speculative collector tuning or declaring one aggregate phase the sole
cause. Query-shape dispatch and borrowed windows have specific verified gains,
but candidate adoption still needs every mandatory Native/service/correctness/
recovery/restoration gate. New engine work needs a new experiment number and
predeclared balanced baselines,controls,goals and complete raw preservation.
Older106/107 rejection and108 diagnostic archival closures remain pending;
every original and failure is safe.

See [reproduction](benchmarks/adaptive-speed-112/REPRODUCE.md),
[complete audit](benchmarks/adaptive-speed-112/complete-audit-proof.json),
[restored audit](benchmarks/adaptive-speed-112/restored-audit-proof.json),
[Native raw replay](benchmarks/adaptive-speed-112/native-audit.json) and
[decision/unstarted service](benchmarks/adaptive-speed-112/native-rejection-decision.json).
'''
path = REPO / 'ADAPTIVE_ENGINE_112.md'
assert not path.exists()
path.write_text(report, encoding='utf-8', newline='\n')
for name in ['README.md', 'BENCHMARK_HISTORY.md']:
    path = REPO / name
    before = path.read_bytes()
    first, rest = before.split(b'\n', 1)
    path.write_bytes(first + b'\n\nLatest adaptive engine trial: [112 complete before/after results](ADAPTIVE_ENGINE_112.md) fails25 A/A controls,13 guards and1 goal. Eight specific Native goals,including grouped medians,pass full and both halves;write-tail regressions block release. Fresh772 tests,recovery and exact restored evidence pass;0.3.17 remains unreleased and0.3.16 supported.\n' + rest)

git('add', '--', 'ADAPTIVE_ENGINE_112.md', 'README.md', 'BENCHMARK_HISTORY.md', 'benchmarks/adaptive-speed-112')
git('diff', '--cached', '--check')
names = git('diff', '--cached', '--name-only').splitlines()
assert all(name in ['ADAPTIVE_ENGINE_112.md', 'README.md', 'BENCHMARK_HISTORY.md'] or name.startswith('benchmarks/adaptive-speed-112/') for name in names)
git('commit', '-m', 'Preserve borrowed scan trial112 results and exact restored rejection')
assert protected == {name: sha(REPO / name) for name in protected}
assert not git('status', '--porcelain').strip()
proof = {'complete': True, 'head': git('rev-parse', 'HEAD').strip(), 'parent': parent,
         'repository_clean': True, 'supported_engine_tests_examples_Cargo_verification_and_overnight_byte_exact': True,
         'candidate_implemented_and_correctness_qualified': True, 'performance_qualified': False,
         'release017_qualified': False, 'all_failed_and_raw_evidence_retained': True,
         'all_full_and_half_before_after_metrics_reported': len(native['summaries']),
         'utc': datetime.now(timezone.utc).isoformat()}
path = WORK / 'commit-112-proof.json'
assert not path.exists()
path.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(proof))
