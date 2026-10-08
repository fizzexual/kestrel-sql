"""Fresh D: service release-blocker check; never overwrite previous trials."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, itertools, json, os, platform, shutil, sys
import numpy

ROOT = Path('D:/Codex/Kestrel')
REPO = ROOT / 'outputs/kestrel-sql'
W = ROOT / 'work/perf-086'
OLD = ROOT / 'work/perf-062'

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(p, v):
    p.write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8', newline='\n')

def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

assert not W.exists(), 'Use a new trial; preserve all earlier attempts'
base = load(OLD / 'baseline.json')
for n, d in base['core_source_sha256'].items():
    assert sha(REPO / n) == d, n
for n, d in base['baseline_binary_sha256'].items():
    assert sha(REPO / 'bin/baseline-0.3.16' / n) == d, n
assert load(ROOT / 'work/perf-061/audit.json')['correctness_passed']
assert load(ROOT / 'work/perf-061/audit.json')['service_guards_failed'] == 10
W.mkdir()
(W / 'binaries').mkdir()
(W / 'harness').mkdir()
for n in ['baseline.json', '061-source-provenance.json', 'policy.json', 'run.py', 'audit.py']:
    shutil.copy2(OLD / n, W / ('previous-062-' + n))
for src, name in [(REPO / 'bin/baseline-0.3.16/kestrel-stress.exe', 'released-016.exe'),
                  (ROOT / 'work/perf-061/lab/work/perf-061/candidate/kestrel-stress.exe', 'clean-core-061.exe')]:
    shutil.copy2(src, W / 'binaries' / name)
for n in ['stress_compare.py', 'host_telemetry.py']:
    shutil.copy2(REPO / 'benchmarks' / n, W / 'harness' / n)
baseline = sha(W / 'binaries/released-016.exe')
candidate = sha(W / 'binaries/clean-core-061.exe')
assert baseline == '081ed43e56d45f1c57ed10e0bebe80ad59487aa92b3215b13bbde06d74e76024'
assert candidate == 'b9f14feff962217ca8d4792a76b78bba5bebe9a7539eef18541b7338d6ebf8fc'
configs = [['read', 2000, 8], ['write', 500, 8], ['mixed', 500, 60]]
permutations = [list(p) for p in [('baseline_a', 'baseline_b', 'candidate'),
                                ('baseline_b', 'candidate', 'baseline_a'),
                                ('candidate', 'baseline_a', 'baseline_b'),
                                ('baseline_a', 'candidate', 'baseline_b'),
                                ('candidate', 'baseline_b', 'baseline_a'),
                                ('baseline_b', 'baseline_a', 'candidate')]]
cases = []
for turn in range(6):
    # Each three-round block balances slots; all six rounds balance pair order.
    for index, (profile, rate, seconds) in enumerate(configs):
        order = permutations[(turn // 3) * 3 + (turn + index) % 3]
        for variant in order:
            cases.append(dict(round=turn, block=turn // 3, profile=profile,
                              rate=rate, seconds=seconds, variant=variant))
for index, (profile, rate, seconds) in enumerate(configs):
    orders = [[c['variant'] for c in cases if c['round'] == r and c['profile'] == profile] for r in range(6)]
    assert set(map(tuple, orders)) == set(itertools.permutations(permutations[0]))
    for v in permutations[0]:
        assert all(sum(o[slot] == v for o in orders) == 2 for slot in range(3))
        for block in range(2):
            assert all(sum(o[slot] == v for o in orders[block*3:block*3+3]) == 1 for slot in range(3))
policy = load(OLD / 'policy.json')
policy.update(trial=86, declared_utc=datetime.now(timezone.utc).isoformat(), before_timing=True,
    status='Fresh D: release-blocker check of the existing clean query fix; no new engine edit',
    physical_workspace=str(ROOT), numpy_version=numpy.__version__,
    cases=cases, scopes={'full': list(range(6)), 'first_block': [0, 1, 2], 'second_block': [3, 4, 5]},
    acceptance='All original 062 A/A and candidate/A guards must pass in full and both three-round blocks. No comparator selection, selective rerun or promotion.',
    expected_cases=54, expected_offered_operations=900000, expected_numpy_windows=1080,
    hypothesis='Determine whether the existing native query fix can advance on fresh D: service controls without write-tail, throughput or loss regressions.',
    engine_changed=False, supported_promotion_allowed=False,
    reused_correctness='061 full retry/crash qualification retained, not rerun; each fresh anonymous-append service case reconciles ACKs, atomic batches, exact totals, 20 NumPy windows and full CRC after process reopen. No fresh named-retry or kill qualification.',
    runtime={'python': sys.version, 'python_executable': sys.executable, 'python_sha256': sha(Path(sys.executable)),
             'platform': platform.platform(), 'logical_cpu_count': os.cpu_count()},
    native_source_provenance_sha256=sha(W / 'previous-062-061-source-provenance.json'),
    previous_failures_retained={'061_service_guards_failed': 10, '062_identity_failed': 3, '062_candidate_guards_failed': 2},
    limits=['Scoped read/write/minute-mixed service check, not the complete six-profile suite or a competitor comparison.',
            'Six round pairs per profile and two slot-balanced blocks; tolerance checks are not statistical proof.',
            'The two original binaries are reused exactly; no recompilation and no new native query measurements.',
            'No direct C:/D: storage-speed claim; Python/NumPy and storage environment are freshly recorded.',
            'Successful-operation latency must be assessed with every error, dropped and expired request.',
            'No physical power-loss, production, complete release or universal benchmark claim.'])
policy['comparison'].update(rounds=6, configs=configs, disk_preflight_min_free_bytes=5_000_000_000,
    order='Frozen six permutations per profile; all six rounds balance pair order and positions. Each three-round block balances positions.')
save(W / 'policy.json', policy)
save(W / 'preparation.json', dict(complete=True, supported_core_unchanged=True,
    baseline_sha256=baseline, candidate_sha256=candidate, original_062_policy_sha256=sha(OLD / 'policy.json'),
    relocated_harness_sha256={p.name: sha(p) for p in (W / 'harness').iterdir()},
    no_historical_evidence_changed=True))
print(json.dumps({'prepared': True, 'trial': 86, 'cases': 54, 'offered': 900000, 'supported_version': '0.3.16'}))
