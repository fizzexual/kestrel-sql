"""Audit the declared cohort, reference fingerprint and every numerical scope.

The native driver verifies complete canonical row equality each iteration.
This separate Python check recomputes the fingerprint/sum; it is not an
independent decode of all native output rows, and does not check Archive CRCs.
"""
from pathlib import Path
import hashlib, itertools, json, math, statistics

ROOT = Path('D:/Codex/Kestrel/work')
WORK = ROOT / 'perf-126'
def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
def percentile(values, quantile):
    return sorted(values)[max(0, math.ceil(len(values) * quantile) - 1)]
def reference(name, seed):
    triples = []
    for run in range(32):
        part = (run * 13 + seed * 7) % 32
        for row in range(1024):
            if name == 'ordered': key = run * 1024 + row
            elif name in ['clustered', 'extreme']: key = row // 64 * 2048 + part * 64 + row % 64
            elif name == 'interleaved': key = row * 32 + part
            elif name == 'duplicates': key = row // 64 * 64 + row % 8
            elif name == 'late': key = part % 8 * 512 + row - part // 8 * 8192
            else: raise AssertionError(name)
            value = [-2**63, -7, 0, 11, 2**63 - 1][row % 5] if name == 'extreme' else (run * 1024 + row) * 37 % 1000 - 500
            triples.append((key, value, run - 16))
    triples.sort()
    digest = 14695981039346656037
    for triple in triples:
        for item in triple:
            digest = ((digest ^ (item & ((1 << 64) - 1))) * 1099511628211) & ((1 << 64) - 1)
    return digest, sum(triple[1] for triple in triples)

assert load(WORK / 'cohort-completion.json')['complete']
policy = load(WORK / 'policy.json'); freeze = load(WORK / 'freeze.json')
assert all(sha(WORK / name) == digest for name, digest in freeze['files'].items())
assert sha(Path(__file__)) == freeze['auditor_sha256']
cases = [json.loads(line) for line in (WORK / 'component-cases.jsonl').read_text(encoding='utf-8').splitlines()]
assert len(cases) == len(policy['cases']) == 648
metrics = {}; reference_cache = {}; arranged = {}; operations = 0
for record, spec in zip(cases, policy['cases']):
    assert all(record[key] == value for key, value in spec.items())
    assert record['actual_exit'] == 0 and record['actual_wait_completed'] and record['identity']['affinity_mask'] == 256 and not record.get('timeout')
    result = load(WORK / record['stdout'])
    assert result['trial'] == 126 and result['diagnostic_only'] and result['all_checks_passed']
    assert result['workload'] == spec['name'] and result['seed'] == spec['seed']
    assert result['candidate'] == (spec['variant'] == 'candidate_122')
    assert result['iterations'] == result['full_native_multiset_checks'] == result['sortedness_checks'] == 32
    assert result['rows_per_iteration'] == 32768
    key = (spec['name'], spec['seed'])
    if key not in reference_cache: reference_cache[key] = reference(*key)
    digest, total = reference_cache[key]
    assert result['canonical_fingerprint'] == digest and result['value_sum_i128'] == total
    if not result['candidate']: assert result['arranged_iterations'] == 0
    arranged[(spec['name'], spec['round'])] = result['arranged_iterations'] if result['candidate'] else arranged.get((spec['name'], spec['round']), 0)
    wall = result['wall_ns']; cycles = result['thread_cycles']
    assert len(wall) == len(cycles) == 32 and all(value > 0 for value in wall + cycles)
    metrics[(spec['name'], spec['variant'], spec['round'])] = {
        'batch_wall_ns': sum(wall), 'batch_thread_cycles': sum(cycles),
        'within_case_p95_wall_ns': percentile(wall, .95), 'within_case_p95_thread_cycles': percentile(cycles, .95)}
    operations += 32
summaries = []
variants = ['baseline_a', 'baseline_b', 'candidate_122']
for name in policy['configs']:
    for scope, rounds in [('full', range(1, 37)), ('first_half', range(1, 19)), ('second_half', range(19, 37))]:
        actual_order = [tuple(row['variant'] for row in cases if row['name'] == name and row['round'] == number) for number in rounds]
        assert sorted(actual_order) == sorted(list(itertools.permutations(variants)) * (len(rounds) // 6))
        for metric in policy['metrics']:
            values = {variant: [metrics[(name, variant, number)][metric] for number in rounds] for variant in variants}
            aa = statistics.median(b / a for a, b in zip(values['baseline_a'], values['baseline_b']))
            ca = statistics.median(c / a for a, c in zip(values['baseline_a'], values['candidate_122']))
            summaries.append({'workload': name, 'scope': scope, 'metric': metric, 'AA_paired': aa, 'CA_paired': ca,
                              'AA_pass': .90 <= aa <= 1.10, 'guard_pass': ca <= 1.10,
                              'variants': {variant: {'p50': statistics.median(samples), 'p95': percentile(samples, .95),
                                                     'p99': percentile(samples, .99), 'max': max(samples), 'all_samples': samples}
                                           for variant, samples in values.items()}})
goals = [row | {'goal_pass': row['CA_paired'] <= .90 and row['AA_pass']} for row in summaries
         if row['workload'] in ['clustered', 'extreme'] and row['metric'] in ['batch_wall_ns', 'batch_thread_cycles']]
audit = {'complete': True, 'cases': len(cases), 'fresh_native_layout_operations': operations,
         'native_exact_multiset_rows_checked': operations * 32768,
         'independent_reference_fingerprints_checked': len(cases), 'independent_full_native_output_decode_claimed': False,
         'Archive_CRC_or_recovery_checks': 0, 'diagnostic_only': True, 'release017_qualified': False,
         'summaries': summaries, 'AA_failed': [row for row in summaries if not row['AA_pass']],
         'guards_failed': [row for row in summaries if not row['guard_pass']], 'goals': goals,
         'goals_failed': [row for row in goals if not row['goal_pass']],
         'candidate_arranged_iteration_counts_by_case': [{'name': name, 'round': number, 'count': count} for (name, number), count in sorted(arranged.items())],
         'journal_sha256': sha(WORK / 'component-cases.jsonl'), 'original_release_gates_unchanged': True}
assert not (WORK / 'audit.json').exists()
(WORK / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in audit.items() if key not in ['summaries', 'AA_failed', 'guards_failed', 'goals', 'goals_failed', 'candidate_arranged_iteration_counts_by_case']}))
print(json.dumps({'AA_failed': len(audit['AA_failed']), 'guards_failed': len(audit['guards_failed']), 'goals_failed': len(audit['goals_failed'])}))
