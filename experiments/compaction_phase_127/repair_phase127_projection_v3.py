"""Use supported Archive SQL; independent exact wire decode follows suites."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, shutil
ROOT = Path('D:/Codex/Kestrel/work')
WORK = ROOT / 'perf-127'
def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
assert load(WORK / 'build-failure-v2.json')['records'][0]['actual_exit'] != 0
original = load(WORK / 'preparation-proof-v2.json')['candidate_source_sha256']
assert all(sha(WORK / 'candidate-v2' / name) == digest for name, digest in original.items())
assert not (WORK / 'candidate-v3').exists()
shutil.copytree(WORK / 'candidate-v2', WORK / 'candidate-v3')
test = WORK / 'candidate-v3/tests/compaction_127.rs'
text = test.read_text(encoding='utf-8')
text = text.replace('use kestrel_sql::{Database, Value};', 'use kestrel_sql::Database;')
assert text.count('    let mut expected = Vec::new();') == 1
text = text.replace('    let mut expected = Vec::new();\n', '')
before = '''        expected.extend(columns[0].iter().zip(&columns[1]).zip(&columns[2])
            .map(|((&key, &value), &device)| (i128::from(key), i128::from(value), i128::from(device))));
'''
assert text.count(before) == 1
text = text.replace(before, '')
assert text.count('    expected.sort_unstable();') == 1
text = text.replace('    expected.sort_unstable();\n', '')
before = '''    let mut actual = Vec::new();
    for row in archive.query("SELECT ts, value, device FROM events").unwrap().result.rows {
        let [Value::Int(key), Value::Int(value), Value::Int(device)] = row.as_slice() else { panic!("expected three BIGINT columns"); };
        actual.push((*key, *value, *device));
    }
    actual.sort_unstable();
    assert_eq!(actual, expected);'''
after = '''    let sql = "SELECT ts, COUNT(*), SUM(value), SUM(device), MIN(value), MAX(value), MIN(device), MAX(device) FROM events GROUP BY ts ORDER BY ts";
    assert_eq!(archive.query(sql).unwrap().result.rows, db.query(sql).unwrap().rows);'''
assert text.count(before) == 1
test.write_text(text.replace(before, after), encoding='utf-8', newline='\n')
inventory = {path.relative_to(WORK / 'candidate-v3').as_posix(): sha(path) for path in (WORK / 'candidate-v3').rglob('*') if path.is_file()}
assert [name for name in original if original[name] != inventory[name]] == ['tests/compaction_127.rs']
(WORK / 'preparation-proof-v3.json').write_text(json.dumps({'complete': True, 'utc': datetime.now(timezone.utc).isoformat(), 'candidate_source_sha256': inventory,
    'changed_only_test_unsupported_projection': True, 'engine_algorithm_unchanged': True, 'all_failed_sources_and_logs_retained': True,
    'independent_exact_wire_audit_required_after_suites': True, 'timed_cases_declared': 0}, indent=2) + '\n', encoding='utf-8')
source = (ROOT / 'build_phase_127_v2.py').read_text(encoding='utf-8')
for before, after in [('candidate-v2', 'candidate-v3'), ('preparation-proof-v2', 'preparation-proof-v3'),
                      ('build-proof-v2', 'build-proof-v3'), ('build-declaration-v2', 'build-declaration-v3'),
                      ('build-v2-step-', 'build-v3-step-'), ('build-failure-v2', 'build-failure-v3'),
                      ('logs-v2', 'logs-v3'), ('test-stores-v2', 'test-stores-v3'), ('binary-v2', 'binary-v3')]:
    assert before in source, before
    source = source.replace(before, after)
ast.parse(source)
for name in ['logs-v3', 'test-stores-v3', 'binary-v3']:
    (WORK / name).mkdir()
(ROOT / 'build_phase_127_v3.py').write_text(source, encoding='utf-8', newline='\n')
print('New test now compares supported grouped aggregates; engine unchanged; exact wire audit still required.')
