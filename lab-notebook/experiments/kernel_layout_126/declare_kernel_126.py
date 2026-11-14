"""Predeclare a bounded in-memory layout diagnostic before implementation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, itertools, json, random, subprocess

ROOT = Path('D:/Codex/Kestrel')
WORK = ROOT / 'work/perf-126'
REPO = ROOT / 'outputs/kestrel-sql'
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
assert load(ROOT / 'work/controls125-storage-cleanup-proof.json')['completed125_stores_closed']
assert not WORK.exists()
git = ['git', '--no-optional-locks', '-c', 'safe.directory=' + REPO.as_posix(), '-C', str(REPO)]
assert not subprocess.check_output(git + ['status', '--porcelain=v1', '--untracked-files=all']).strip()
head = subprocess.check_output(git + ['rev-parse', 'HEAD'], text=True).strip()
assert head == load(ROOT / 'work/controls125-publication-proof.json')['private_main']
core = load(ROOT / 'work/compaction-kit-122/provenance.json')['source_core_sha256']
assert all(sha(REPO / name) == digest for name, digest in core.items())
configs = ['ordered', 'clustered', 'interleaved', 'duplicates', 'late', 'extreme']
variants = ['baseline_a', 'baseline_b', 'candidate_122']
permutations = list(itertools.permutations(variants))
rng = random.Random(20261010)
cases = []
for block in range(6):
    orders = {name: permutations.copy() for name in configs}
    for name in configs:
        rng.shuffle(orders[name])
    for offset in range(6):
        round_number = block * 6 + offset + 1
        names = configs.copy()
        rng.shuffle(names)
        for name in names:
            for variant in orders[name][offset]:
                cases.append({'index': len(cases), 'round': round_number,
                              'seed': (round_number - 1) % 12 + 1, 'name': name, 'variant': variant})
for name in configs:
    for rounds in [range(1, 37), range(1, 19), range(19, 37)]:
        actual = [tuple(row['variant'] for row in cases if row['round'] == number and row['name'] == name) for number in rounds]
        assert sorted(actual) == sorted(permutations * (len(rounds) // 6))
policy = {
    'trial': 126, 'declared_utc': datetime.now(timezone.utc).isoformat(), 'source_commit': head,
    'hypothesis': '125 failed51/144 identical durable controls. 122 had controlled clustered preparation gains, but reads/CRC/sync and scheduling remain mixed. Isolate the unchanged supported publish monotonic-check/sort/gather kernel versus exact122 merge-plus-final-check/sort. Repeated in-memory calls and thread-cycle counts test the computational mechanism without attributing durable variation to CPU.',
    'diagnostic_only_not_release_or_durable_compaction': True,
    'new_engine_change': False, 'supported_source_sha256': core,
    'candidate_module_sha256': sha(REPO / 'experiments/compaction_merge_122/merge_runs_122.rs'),
    'cases': cases, 'rounds': 36, 'configs': configs, 'iterations_per_case': 32,
    'input': '32 runs of1024 rows/3signed-i64 columns; same6 shapes and12 valid seeds as125. Each run is sorted by the supported append kernel before concatenation, including duplicates. Preserve value/device pairing.',
    'scope': 'Each iteration clones concatenated input before the timer; inside timer all arrange/sort/gather allocations and final monotonic check are charged. Complete sortedness and exact canonical row triples checked after every iteration. No index building, input CRC/read, publication, filesystem, sync, SQL or recovery measured.',
    'metrics': ['batch_wall_ns', 'batch_thread_cycles', 'within_case_p95_wall_ns', 'within_case_p95_thread_cycles'],
    'controls': {'paired_median_lower': 0.90, 'paired_median_upper': 1.10, 'full_and_both_halves': True},
    'guards': {'candidate_paired_median_upper': 1.10, 'all6_shapes_full_and_both_halves': True},
    'goals': {'clustered_and_extreme_batch_wall_and_cycles_upper': 0.90, 'full_and_both_halves': True},
    'all_p50_p95_p99_max_and_samples_reported': True,
    'same_rng_seed_20261010_balanced_schedule': True, 'affinity_mask': 256, 'cooldown_seconds': 120,
    'cycles': 'Windows QueryThreadCycleTime for this current thread only. Record raw cycles; never convert cycles to elapsed time or call them CPU nanoseconds.',
    'prerequisites': 'Serial rustc -Dwarnings debug/release driver+reused-module tests, then optimized driver. Two excluded full-row smoke cases. No build/copy/hash/cleanup/benchmark overlap with timed cohort; fresh task/reset and global build guards.',
    'original_release_gates_unchanged': {'Native': 324, 'service': 252, 'goals': 42, 'AA': 153, 'guards': 171},
    'local_resource_bound_bytes': 50_000_000, 'no_disk_fixture_or_raw_bundle': True,
    'retention': 'Concise full outcomes/failures and useful code privately saved, freshly verified, then regenerable completed artifacts removed.',
    'research': ['https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-querythreadcycletime']
}
WORK.mkdir()
(WORK / 'policy.json').write_text(json.dumps(policy, indent=2) + '\n', encoding='utf-8')
(WORK / 'declaration-proof.json').write_text(json.dumps({'complete': True, 'utc': policy['declared_utc'], 'policy_sha256': sha(WORK / 'policy.json'), 'before_new_driver_implementation_or_build': True, 'all648_cases_balanced': True, 'all_timed_cases_unstarted': True}, indent=2) + '\n', encoding='utf-8')
for name in ['source', 'binary', 'logs', 'tmp', 'raw']:
    (WORK / name).mkdir()
print(json.dumps({'declared': True, 'trial': 126, 'cases': len(cases), 'iterations_per_case': 32, 'maximum_local_bytes': 50_000_000, 'diagnostic_only': True}))
