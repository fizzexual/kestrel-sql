"""Predeclare identical-binary calibration; no engine edit and no automatic promotion."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import numpy

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
PREVIOUS = W.parent / 'perf-061'
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W / 'policy.json').exists()
assert load(PREVIOUS / 'audit.json')['correctness_passed']
assert load(PREVIOUS / 'audit.json')['service_guards_failed'] == 10
assert load(ROOT / 'benchmarks/core-read-path-061-publication.json')['remote_assets_verified'] == 90
assert not load(PREVIOUS / 'post-qualification-process-check.json')['active_processes']
base = load(PREVIOUS / 'baseline.json')
for n, d in base['core_source_sha256'].items():
    assert sha(ROOT / n) == d, n
for n, d in base['baseline_binary_sha256'].items():
    assert sha(ROOT / 'bin' / n) == d, n
shutil.copy2(PREVIOUS / 'baseline.json', W / 'baseline.json')
shutil.copy2(PREVIOUS / 'source-provenance.json', W / '061-source-provenance.json')
(W / 'binaries').mkdir()
shutil.copy2(ROOT / 'bin/baseline-0.3.16/kestrel-stress.exe', W / 'binaries/released-016.exe')
shutil.copy2(PREVIOUS / 'lab/work/perf-061/candidate/kestrel-stress.exe', W / 'binaries/clean-core-061.exe')
assert sha(W / 'binaries/released-016.exe') == base['baseline_binary_sha256']['kestrel-stress.exe']
assert sha(W / 'binaries/clean-core-061.exe') == load(PREVIOUS / 'lab/outputs/kestrel-sql/benchmarks/rust-checks-061.json')['bridge_sha256']
baseline = sha(W / 'binaries/released-016.exe')
policy = {'trial': 62, 'declared_utc': datetime.now(timezone.utc).isoformat(), 'before_timing': True,
          'status': 'identical released-binary A/A calibration plus unchanged clean-core 061; no engine edit',
          'versions': {'baseline_a': '0.3.16', 'baseline_b': '0.3.16', 'candidate': '0.3.17-dev.61'},
          'binary_sha256': {'baseline_a': baseline, 'baseline_b': baseline, 'candidate': sha(W / 'binaries/clean-core-061.exe')},
          'same_exact_executable_path_for_both_baseline_labels': True,
          'numpy_version': numpy.__version__,
          'comparison': {'rounds': 3, 'base_rows': 1_000_000, 'clients': 64, 'batch_rows': 100,
                         'group_delay_ms': 0, 'queue_capacity': 256, 'worker_expiry_seconds': 2,
                         'configs': [['read', 2000, 8], ['write', 500, 8], ['mixed', 500, 60]],
                         'write_fractions': {'read': 0, 'write': .25, 'mixed': .05},
                         'order': 'Latin-square rotation of baseline_a, baseline_b, candidate by (round + config index) modulo 3',
                         'disk_preflight_min_free_bytes': 800_000_000},
          'identity_calibration': {'comparator': 'baseline_b / baseline_a', 'each_successful_p99_ratio_min': .90,
                                   'each_successful_p99_ratio_max': 1.10, 'window_rps_ratio_min': .90,
                                   'window_rps_ratio_max': 1.10, 'absolute_loss_difference_max_offered_fraction': .01,
                                   'overall_query_and_append_p99_recorded_separately': True},
          'candidate_regression_guards': {'primary_comparator': 'candidate / baseline_a',
                                         'successful_p99_ratio_max': 1.10, 'window_rps_ratio_min': .90,
                                         'loss_increase_max_offered_fraction': .01,
                                         'candidate_over_baseline_b_always_reported_as_diagnostic_only': True},
          'outside_timer': ['seed', 'cold reopen/exact retry', '20 NumPy windows and full CRC per case',
                            'raw compression', 'compilation/audit/packaging/Git/cleanup'],
          'limits': ['27 fresh serial cases; no restart or replacement of any 061 timings',
                     'shared near-full Windows desktop; free bytes and whole-host telemetry retained per case',
                     'three pairs per profile are a calibration, not statistical proof of equivalence or a causal model',
                     'A/A failure does not erase original 061 service failures or permit supported promotion',
                     'finite offered rates, not maximum sustainable capacity; task-owned processes stopped per case',
                     'no new compiler job, SDK change, full competitive matrix or supported release',
                     'no physical power-loss or production qualification; English only; morning already issued']}
(W / 'policy.json').write_text(json.dumps(policy, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'planned_cases': 27, 'offered_operations': 450000, 'engine_changed': False}))
