from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, importlib.util, json, shutil

ROOT = Path('D:/Codex/Kestrel')
W = ROOT / 'work/perf-086'
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def save(p, v): p.write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8', newline='\n')
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W / 'timing-freeze.json').exists()
assert load(W / 'smoke.json')['complete']
for src, name in [(ROOT / 'work/run_service_086.py', 'run_service_086.py'),
                  (ROOT / 'work/audit_service_086.py', 'audit_service_086.py'),
                  (ROOT / 'work/prepare_086.py', 'prepare_086.py'),
                  (Path(__file__), 'freeze_service_086.py')]:
    shutil.copy2(src, W / name)
for n, d in load(W / 'previous-062-061-source-provenance.json')['candidate'].items():
    assert sha(ROOT / 'work/perf-061/lab/outputs/kestrel-sql' / n) == d, n
spec = importlib.util.spec_from_file_location('audit086', W / 'audit_service_086.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
policy = load(W / 'policy.json')
cases = [dict(round=s['round'], block=s['block'], profile=s['profile'], offered_rps=s['rate'],
              scheduled_seconds=s['seconds'], variant=s['variant'], case_index=i) for i, s in enumerate(policy['cases'])]
m.verify_order(cases, policy)
negative = []
for kind in ['swap_variants', 'duplicate_round', 'missing_case']:
    bad = copy.deepcopy(cases)
    if kind == 'swap_variants': bad[0]['variant'], bad[1]['variant'] = bad[1]['variant'], bad[0]['variant']
    elif kind == 'duplicate_round': bad[9]['round'] = 0
    else: bad.pop()
    try: m.verify_order(bad, policy)
    except AssertionError: negative.append(kind)
    else: raise AssertionError('Bad order escaped audit: ' + kind)
save(W / 'order-validator-check.json', {'valid_schedule_passed': True, 'bad_schedules_rejected': negative,
                                      'no_native_timer_cases_run': True})
paths = ['policy.json', 'run_service_086.py', 'audit_service_086.py', 'prepare_086.py', 'freeze_service_086.py',
         'harness/stress_compare.py', 'harness/host_telemetry.py', 'binaries/released-016.exe', 'binaries/clean-core-061.exe',
         'previous-062-baseline.json', 'previous-062-061-source-provenance.json', 'order-validator-check.json']
save(W / 'timing-freeze.json', {'frozen_utc': datetime.now(timezone.utc).isoformat(), 'before_first_cohort_case': True,
    'sha256': {n: sha(W / n) for n in paths}, 'smoke_excluded': True, 'gates_fixed': True,
    'candidate_frozen_source_matches_original_061': True})
print(json.dumps({'frozen': True, 'cases': len(cases), 'order_negative_checks': len(negative)}))
