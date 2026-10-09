"""Record every adaptive110 before/after and exact restored negative evidence."""
from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, json, shutil, subprocess

R = Path('D:/Codex/Kestrel')
WORK = R / 'work'
REPO = R / 'outputs/kestrel-sql'
W = WORK / 'perf-110'
OUT = REPO / 'benchmarks/adaptive-speed-110'

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

guard = sorted(WORK.glob('guard-final-110-*.json'))[-1]
assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
parent = load(WORK / 'commit-109-proof.json')['head']
assert git('rev-parse', 'HEAD').strip() == parent
assert not git('diff', '--name-only') and not git('diff', '--cached', '--name-only')
preserved = load(OUT / 'preservation-proof.json')
restored = load(OUT / 'restored-audit-proof.json')
complete = load(OUT / 'complete-audit-proof.json')
native = complete['native']
assert preserved['complete'] and preserved['all_originals_and_frozen_inputs_retained_unchanged']
assert restored['replay_equals_original_complete_audit'] and complete == load(W / 'complete-audit-proof.json')
assert complete['correctness_passed'] and not complete['release017_qualified']
assert (native['identity_failed'], native['candidate_guards_failed'], native['goals_failed']) == (93, 35, 11)
assert complete['service']['unstarted_cases'] == 252 and not complete['service']['performance_tested']
assert len(native['goals']) == 30
protected = {name: sha(REPO / name) for name in git(
    'ls-files', 'src', 'tests', 'examples', 'Cargo.toml', 'Cargo.lock',
    'verification.json', 'OVERNIGHT_2026-10-07.md').splitlines()}
assert all(sha(REPO / name) == expected for name, expected in load(
    WORK / 'perf-105/policy.json')['baseline_source_sha256'].items())

closed = OUT / 'closed-continuation'
assert not closed.exists()
closed.mkdir()
logs = {}
for name in ['build-110.log', 'build-v2-110.log', 'preflight-v2-110.log', 'preperformance-v2-110.log', 'native-v2-110.log', 'complete-audit-110-v3.log', 'preserve-v3-110.log', 'prepare-rejection-110.log', 'profile-native-110.log', 'record-rejection-110.log', 'prepare-negative-closure-110.log', 'prepare-preserver-110-v3.log', 'repair-test-checker-110-v2.log', 'check-complete-prefix-110-v2.log', 'update-next-rejected110.log']:
    raw = (WORK / name).read_bytes()
    path = closed / (name + '.gz')
    path.write_bytes(gzip.compress(raw, mtime=0))
    assert gzip.decompress(path.read_bytes()) == raw
    logs[name] = {'raw_sha256': hashlib.sha256(raw).hexdigest(),
                  'gzip_sha256': sha(path), 'byte_exact': True}
(closed / 'raw-log-proof.json').write_text(json.dumps(logs, indent=2) + '\n', encoding='utf-8', newline='\n')
assert json.loads((WORK / 'preserve-v3-110.log').read_text(encoding='utf-8-sig').splitlines()[-1])['complete']
shutil.copy2(Path(__file__), closed / Path(__file__).name)
shutil.copy2(guard, closed / guard.name)
for name in ['README.md', 'BENCHMARK_HISTORY.md']:
    shutil.copy2(REPO / name, closed / (name + '.before-110'))

report = '# Adaptive engine trial 110\n\nThe candidate implements workload-dependent collection, query dispatch and\nverified duplicate replay. **Release qualification fails.** Supported main\nremains0.3.16; candidate0.3.17 metadata is unreleased. This is not a fresh\ncompetitor comparison or a claim of winning every benchmark.\n\nThe exact trial107 collector chooses immediate sparse work, bounded small-group\nlookahead or ready pressure draining. Trial109 query dispatch chooses prefix\nindexes first, eligible fused single-column ungrouped COUNT/SUM/AVG next, and\nexisting general selection/dense/sparse grouping otherwise. Trial110 adds a\nborrowed lookup for already durable batch IDs, retaining the healthy-writer,\nshape/budget/ID/full submitted-content checks and original receipt generation.\nUnknown IDs keep the existing publication path. The optional adaptive-engine\nfeature enables adaptive-collection,adaptive-filter and adaptive-replay.\nPublication,source/WAL/ACK semantics,formats and maintenance remain protected.\n\n748 fresh tests across eight complete debug/release configurations,five strict\nall-target lints and independent normal/fault artifact builds passed. Fresh\n359-command external recovery passed28 publication interruptions,10 corruptions,\nCAT2/CAT3 reads,two byte fixtures,256 concurrent anonymous ACKs,two named scenarios\nand300 cold SQLite-model SQL checks. Physical power-loss and resource-exhaustion\nguarantees were not tested. Native CPU/peak memory were not measured; service\nresource/loss/capacity checks remain unstarted.\n\nAll324 predeclared Native cases completed exactly once. All479,232 ACKs and\n2,921,356,800 full checksum bytes independently pass row,receipt,index,query,\nquantile,order and provenance replay. All30 goals and every prior gate remain;\nsix required replay goals were added before code/copy/build. There were no\nnumerical retries,selected rounds or loosened gates. Performance fails93/153\nA/A controls,35/171 regression guards and11/30 goals. All252 service specs are\npreserved as UNSTARTED/UNTESTED because mandatory Native qualification failed.\n\n## Promising full-run results, inconclusive across the required halves\n\n| Replay metric | Before | After | Paired candidate/A | Full A/A | Required halves |\n| --- | ---: | ---: | ---: | ---: | --- |\n| p95 |2.35us|1.95us|0.82575758|0.96085859|half2 control FAIL|\n| p99 |2.90us|2.35us|0.83501684|1.03146853|both half controls FAIL;half1 goal FAIL|\n\nPaired ratios use within-round comparisons and can differ from quotients of\ndisplayed medians. No improvement goal passes its target and baseline control\nin full and both halves. The initial commentary claim that replayp95 passed\nboth half controls was incorrect and immediately corrected. Half2 p95 A/A\nis0.93996416,outside the unchanged0.95..1.05 gate. These are not robust verified\nwins. Calibrated regressions include sparse-writep95,pressure-namedp50/completion\nand late-data grouped/extrema queries. Exclusive causes are not established.\n\nThe first build failed only in a new shared test checker,which tried to read the\nheld Windows lease file. Every original source,failed test,log,target and store\nis preserved. The exact checker-only repair verifies the lease length is zero,\nproving its complete empty bytes,and reads every other file byte. No runtime,\nCargo,file exclusion or gate change occurred. The full build was run afresh.\n\n## Every before/after, control, regression check and goal\n\nAll171 full/half comparisons follow. Live operation units are milliseconds,\nqueries/replay are microseconds,and disk is bytes. A/A passes within0.95..1.05;\nregression limits remain1.05. Goals remain0.95 for small-writep99 and0.90 for\nsmall-write completion,filter and replay targets. Maxima/raw stalls are retained.\n\n| Scope | Workload | Metric | Unit | Before median | After median | A/A | Control | Candidate/A | Regression | Goal |\n| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | --- | --- |\n'
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

Next engineering target: bounded sequential per-column read-ahead for long
streamed scans. Diagnostic108 attributes roughly5.5ms of8ms grouped wall to
page work,with0.21ms selection and2.2ms aggregation; its grouped timing controls
fail,so this supports a stage-cost hypothesis rather than a speed or causal
claim. The actual reader alternates seek/read calls per column and4096-row block.
New work requires a new number,predeclared controls,unchanged fallback/CRC,
bounded memory,and complete qualification before adoption. Older106/107 rejection
and108 diagnostic archives remain pending; every original and failure is safe.

See [complete reproduction](benchmarks/adaptive-speed-110/REPRODUCE.md),
[complete original audit](benchmarks/adaptive-speed-110/complete-audit-proof.json),
[restored audit](benchmarks/adaptive-speed-110/restored-audit-proof.json),
[all native results](benchmarks/adaptive-speed-110/native-audit.json) and
[decision and unstarted service specs](benchmarks/adaptive-speed-110/native-rejection-decision.json).
Borrowed receipt lookup follows [Rust's BTreeMap API](https://doc.rust-lang.org/std/collections/struct.BTreeMap.html#method.get);
that documentation supports the design, not a Kestrel speed claim.
'''
path = REPO / 'ADAPTIVE_ENGINE_110.md'
assert not path.exists()
path.write_text(report, encoding='utf-8', newline='\n')
for name in ['README.md', 'BENCHMARK_HISTORY.md']:
    path = REPO / name
    before = path.read_bytes()
    first, rest = before.split(b'\n', 1)
    path.write_bytes(first + b'\n\nLatest adaptive engine trial: [110 complete before/after results](ADAPTIVE_ENGINE_110.md) fails93 A/A controls,35 guards and11 goals. Replay full-run gains fail required half controls and remain inconclusive. Correctness/recovery and exact restored evidence pass; 0.3.17 remains unreleased and 0.3.16 supported.\n' + rest)

git('add', '--', 'ADAPTIVE_ENGINE_110.md', 'README.md', 'BENCHMARK_HISTORY.md', 'benchmarks/adaptive-speed-110')
git('diff', '--cached', '--check')
names = git('diff', '--cached', '--name-only').splitlines()
assert all(name in ['ADAPTIVE_ENGINE_110.md', 'README.md', 'BENCHMARK_HISTORY.md'] or name.startswith('benchmarks/adaptive-speed-110/') for name in names)
git('commit', '-m', 'Preserve adaptive replay trial110 rejection and exact restored evidence')
assert protected == {name: sha(REPO / name) for name in protected}
assert not git('status', '--porcelain').strip()
proof = {'complete': True, 'head': git('rev-parse', 'HEAD').strip(), 'parent': parent,
         'repository_clean': True, 'supported_engine_tests_examples_Cargo_verification_and_overnight_byte_exact': True,
         'candidate_implemented_and_correctness_qualified': True, 'performance_qualified': False,
         'release017_qualified': False, 'all_failed_and_raw_evidence_retained': True,
         'all_full_and_half_before_after_metrics_reported': len(native['summaries']),
         'utc': datetime.now(timezone.utc).isoformat()}
path = WORK / 'commit-110-proof.json'
assert not path.exists()
path.write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8', newline='\n')
print(json.dumps(proof))
