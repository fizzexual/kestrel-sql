"""Declare fresh released/core-061 service controls before arrival timers."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy

W = Path(__file__).resolve().parent
ROOT = W / 'lab/outputs/kestrel-sql'
WORK = W / 'lab/work'
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
assert json.loads((W / 'matrix.json').read_text())['complete']
assert not (W / 'service-policy.json').exists()
bins = {'baseline': ROOT / 'bin/baseline-0.3.16/kestrel-stress.exe',
        'candidate': WORK / 'perf-061/candidate/kestrel-stress.exe'}
assert sha(bins['candidate']) == json.loads((ROOT / 'benchmarks/rust-checks-061.json').read_text())['bridge_sha256']
policy = {'trial': 61, 'declared_utc': datetime.now(timezone.utc).isoformat(), 'before_service_timing': True,
          'status': 'clean borrowed-keyword parser port; full released-core service regression controls; no automatic promotion',
          'baseline': '0.3.16', 'candidate': '0.3.17-dev.61', 'numpy_version': numpy.__version__,
          'binary_sha256': {v: sha(p) for v, p in bins.items()},
          'harness_sha256': {n: sha(ROOT / 'benchmarks' / n) for n in ['stress_compare.py', 'host_telemetry.py']},
          'comparison': {'rounds': 3, 'base_rows': 1_000_000, 'clients': 64, 'batch_rows': 100,
                         'group_delay_ms': 0, 'queue_capacity': 256, 'worker_expiry_seconds': 2,
                         'configs': [['mixed', 2000, 8], ['mixed', 10000, 8], ['write', 500, 8],
                                     ['mixed', 500, 60], ['read', 2000, 8], ['scan', 100, 8]],
                         'write_fractions': {'mixed': .05, 'write': .25, 'read': 0, 'scan': .10},
                         'order': 'alternate variant order by round and configuration; serial fresh stores',
                         'disk_preflight_min_free_bytes': 800_000_000},
          'regression_guards': {'each_profile_successful_p99_paired_ratio_max': 1.10,
                                'each_write_profile_append_p99_paired_ratio_max': 1.10,
                                'each_read_profile_query_p99_paired_ratio_max': 1.10,
                                'each_profile_successful_window_rps_paired_ratio_min': .90,
                                'each_profile_total_loss_increase_max_offered_fraction': .01},
          'production_goal_separate': {'all_candidate_60s_soaks_zero_loss_required': True,
                                      'missing_acknowledged_or_partial_batch_allowed': False},
          'timing': 'scheduled arrival to successful response, including queueing; failures, expiry, drops and drain retained separately',
          'outside_timer': ['seed', '20 independent NumPy windows per case', 'cold reopen and exact retry',
                            'full CRC', 'raw gzip', 'builds/audits/Git/packaging/cache cleanup'],
          'limits': ['shared Windows computer; JSON bridge; 64 client threads',
                     'finite offered schedules, not sustainable maximum capacity',
                     'no competitors freshly measured in this service phase',
                     '059 SDK service failures remain separate; SDK changes not included',
                     'no physical power-loss, distributed-scale or production qualification',
                     'stop task-owned children after every case; preserve all failed/slower cases']}
(W / 'service-policy.json').write_text(json.dumps(policy, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'prepared': True, 'planned_cases': 36, 'offered_operations': 880800}), flush=True)
