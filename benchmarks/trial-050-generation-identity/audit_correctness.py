from pathlib import Path
import datetime, hashlib, json, re

w = Path(__file__).parent
root = w.parents[1] / 'outputs/kestrel-sql'
def read(name):
    return json.loads((w / name).read_text(encoding='utf-8-sig'))
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
gates = read('correctness-gates.json')
assert gates['complete']
expected = {'semantic-recovery', 'cross-candidate', 'compatibility', 'publication-cuts', 'source-cuts-kills',
            'concurrent-kills', 'general-sql', 'group', 'cache', 'medium', 'dense', 'sparse', 'scan', 'reader'}
passed = [s for s in gates['steps'] if s['returncode'] == 0]
assert len(passed) == len(expected) and {s['name'] for s in passed} == expected
for s in passed:
    assert sha(w / (s['name'] + '.txt')) == s['log_sha256']
build = read('build-provenance.json')
for name, digest in build['source'].items():
    assert sha(w / 'candidate' / name) == digest
for name, digest in build['binaries'].items():
    assert sha(w / 'bin' / name) == digest
base = read('baseline.json')
for name, digest in base['core_source_sha256'].items():
    assert sha(root / name) == digest
for name, digest in base['baseline_binary_sha256'].items():
    assert sha(root / 'bin' / name) == digest
tests = {}
for mode in ['debug', 'release']:
    text = (w / (mode + '-test.txt')).read_text(encoding='utf-8')
    tests[mode] = sum(map(int, re.findall(r'test result: ok\. (\d+) passed; 0 failed;', text)))
    assert tests[mode] == 85, tests
red = (w / 'regression-before-fix.txt').read_text(encoding='utf-8')
green = (w / 'regression-after-fix.txt').read_text(encoding='utf-8')
assert '0 passed; 3 failed;' in red and '3 passed; 0 failed;' in green
original = read('initialization.json')['source_hashes_before_fix']
assert sha(w / 'regression-before-fix/src/archive.rs') == original['src/archive.rs']
old = json.loads((w.parent / 'perf-049/build-provenance.json').read_text(encoding='utf-8'))
assert original['src/archive.rs'] == old['source']['src/archive.rs']
for name, digest in old['source'].items():
    assert sha(w.parent / 'perf-049/candidate' / name) == digest
for name, digest in old['binaries'].items():
    assert sha(w.parent / 'perf-049/bin' / name) == digest
changes = [name for name, digest in build['source'].items() if old['source'].get(name) != digest]
assert sorted(changes) == ['src/archive.rs', 'tests/archive.rs'], changes
semantic = read('semantic-recovery.json')
assert semantic['passed'] and semantic['original_failing_fixture_unchanged'] and len(semantic['cases']) == 5
cross = read('cross-candidate.json')
assert cross['passed'] and len(cross['cases']) == 4
publication = read('publication-050-faults.json')
assert len(publication['cut_points']) == 64 and len(publication['corruption_cases']) == 22
source = read('source-050-faults.json')
assert len(source['cases']) == 16 and len(source['kill_cycles']) == 8 and not source['failed_cases']
concurrent = read('group-050-recovery.json')
assert len(concurrent['cycles']) == 32 and not concurrent['failed_cases']
general = read('archive-050-verification.json')
sql_count = general['queries_checked_against_each_reference']
for name in ['group', 'cache', 'medium', 'dense', 'sparse', 'scan']:
    report = read(name + '-050-differential.json')
    sql_count += report['queries_checked_against_each_reference']
assert sql_count == 4000, sql_count
proof = {'audited_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'trial': '050 isolated restore identity hardening, not a supported release',
         'rust_tests_each_mode': tests, 'focused_regression_before_fix': 'three expected failures on identical 049 engine source',
         'focused_regression_after_fix': 'three passes', 'source_and_ten_binary_hashes_verified': True,
         'changed_source_files_from_049': changes, 'default_core_and_supported_binaries_unchanged': True,
         'all_14_final_external_gates_passed': True, 'semantic_fixture_cases': 5,
         'old_048_and_049_wrong_sum_reproduced': 400, 'expected_correct_sum': 2000,
         '050_rejects_bad_restore_before_data_access': True, 'valid_legacy_migration_and_original_receipt_preserved': True,
         'cross_candidate_directions': 4, 'publication_cuts': 64, 'corruption_cases': 22,
         'source_faults': 16, 'source_kills': 8, 'concurrent_kills': 32,
         'sql_queries_against_each_duckdb_and_sqlite': 4000,
         'preserved_harness_failures': 2,
         'raw_model_description_notice': 'Source fault report retains an older seven-cut description. Its case list proves eight cuts, sixteen error/exit cases; no report bytes rewritten.',
         'fresh_performance_measured': False, 'performance_gates_completed': False,
         'release_gates_completed': False, 'trial_promoted': False, 'morning_report_issued': False}
(w / 'correctness-audit.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof))
