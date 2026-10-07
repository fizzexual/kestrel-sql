"""Predeclare current-release batching controls; no engine build or edit."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W / 'policy.json').exists()
assert load(ROOT / 'benchmarks/service-calibration-062-document-check.json')['default_source_binaries_and_morning_unchanged']
base = load(W.parent / 'perf-062/baseline.json')
for n, d in base['core_source_sha256'].items():
    assert sha(ROOT / n) == d, n
for n, d in base['baseline_binary_sha256'].items():
    assert sha(ROOT / 'bin' / n) == d, n
shutil.copy2(W.parent / 'perf-062/baseline.json', W / 'baseline.json')
(W / 'binaries').mkdir()
binary = W / 'binaries/released-016.exe'
shutil.copy2(ROOT / 'bin/baseline-0.3.16/kestrel-stress.exe', binary)
assert sha(binary) == base['baseline_binary_sha256']['kestrel-stress.exe']
policy = {'trial': 63, 'declared_utc': datetime.now(timezone.utc).isoformat(), 'before_timing': True,
    'status': 'current released binary 0/1/4ms optional batching experiment with identical zero-delay controls',
    'version': '0.3.16', 'binary_sha256': sha(binary), 'engine_changed': False,
    'same_exact_executable_path_for_all_labels': True,
    'variants': {'baseline_a': 0, 'baseline_b': 0, 'delay1': 1, 'delay4': 4},
    'comparison': {'rounds': 4, 'base_rows': 1_000_000, 'clients': 64, 'batch_rows': 100,
        'configs': [['write', 500, 15], ['mixed', 500, 60]],
        'write_fractions': {'write': .25, 'mixed': .05}, 'queue_capacity': 256, 'worker_expiry_seconds': 2,
        'order': 'Latin square: rotate four labels by (round + config index) modulo four; each label occupies every position once',
        'disk_preflight_min_free_bytes': 800_000_000},
    'identity_calibration': {'comparator': 'baseline_b / baseline_a', 'p99_and_window_rps_ratio_interval': [.90, 1.10],
        'absolute_loss_difference_max_offered_fraction': .01},
    'candidate_criteria': {'primary_comparator': 'each delay / baseline_a', 'append_p99_ratio_max': .90,
        'overall_and_query_p99_ratio_max': 1.10, 'window_rps_ratio_min': .90,
        'loss_increase_max_offered_fraction': .01, 'soak_loss_must_be_zero_each_round': True,
        'publication_attempt_ratio_max': .85,
        'delay_over_baseline_b_always_reported_diagnostic_only': True,
        'decision': 'a delay is a demonstrated scoped improvement only if all its criteria and all identity calibration checks pass; no default promotion'},
    'recovery': {'group_delays_ms': [0, 1, 4], 'kill_delays_seconds': [.0005, .002, .008, .012, .03, .08, .2, .5],
        'simultaneous_producers': 16, 'identified_batches_per_producer': 4, 'batch_rows': 100,
        'all_fixtures_retained': True, 'before_performance_timers': True},
    'outside_timer': ['seed', 'cold reopen, ACK reconciliation and exact retry', '20 NumPy windows and full CRC per case',
        'raw compression', 'recovery, compilation, audit, packaging, Git and cleanup'],
    'limits': ['all prior 034 policy results and 061/062 failures remain intact; these are new measurements on 0.3.16',
        'shared Windows desktop; finite offered rates, four pairs and whole-host telemetry are not statistical or capacity qualification',
        'collection deadline bounds intentional waiting, not OS wakeup, queueing, sync or ACK latency',
        'no sync disabled, no new storage format, engine build, analytical/competitor performance run or supported release',
        'crash model is process death on a live filesystem, not physical power loss', 'English only; morning report already issued']}
(W / 'policy.json').write_text(json.dumps(policy, indent=2) + '\n', encoding='utf-8')
original = ROOT / 'benchmarks/group_commit_recovery.py'
text = original.read_text(encoding='utf-8')
text = text.replace("ROOT = Path(__file__).resolve().parents[1]", "ROOT = Path(__file__).resolve().parents[2] / 'outputs/kestrel-sql'")
text = text.replace("work = ROOT.parent.parent/'work'/f'group-recovery-{time.time_ns()}'", "work = Path(__file__).resolve().parent / 'recovery-fixtures'")
text = text.replace('for group_delay in [0,2,8,20]:', 'for group_delay in [0,1,4]:')
text = text.replace("shutil.rmtree(resolved)", "# Retain every recovery store for independent review.")
text = text.replace("len(report['cycles'])==32", "len(report['cycles'])==24")
text = text.replace("'cycles':[], 'failed_cases':[]}", "'cycles':[], 'failed_cases':[], 'fixture_root':str(work), 'policy_sha256':hashlib.sha256((Path(__file__).resolve().parent/'policy.json').read_bytes()).hexdigest()}")
(W / 'recovery.py').write_text(text, encoding='utf-8')
(W / 'recovery-provenance.json').write_text(json.dumps({'original_source':str(original), 'original_sha256':sha(original),
    'adapted_sha256':sha(W/'recovery.py'), 'changes':['trial-owned fixture path', '0/1/4ms current options', '24 cycle count',
    'retain full fixtures', 'policy hash and fixture path in report'], 'oracle_and_kill_logic_unchanged':True}, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'planned_service_cases':32, 'offered_operations':600000, 'planned_recovery_cycles':24, 'engine_changed':False}))
