"""Narrow test-only compile repair; preserve original source and failed build."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, shutil
ROOT = Path('D:/Codex/Kestrel/work')
WORK = ROOT / 'perf-127'
def sha(path):
    with path.open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def load(path): return json.loads(path.read_text(encoding='utf-8-sig'))
assert load(WORK / 'build-failure.json')['records'][0]['actual_exit'] != 0
original = load(WORK / 'preparation-proof.json')['candidate_source_sha256']
assert all(sha(WORK / 'candidate' / name) == digest for name, digest in original.items())
assert not (WORK / 'candidate-v2').exists()
shutil.copytree(WORK / 'candidate', WORK / 'candidate-v2')
test = WORK / 'candidate-v2/tests/compaction_127.rs'
text = test.read_text(encoding='utf-8')
before = '        let columns = vec![\n            (0..size).map(|row| first + row as i64).collect(),'
after = '        let columns: Vec<Vec<i64>> = vec![\n            (0..size).map(|row| first + row as i64).collect(),'
assert text.count(before) == 1
test.write_text(text.replace(before, after, 1), encoding='utf-8', newline='\n')
inventory = {path.relative_to(WORK / 'candidate-v2').as_posix(): sha(path) for path in (WORK / 'candidate-v2').rglob('*') if path.is_file()}
changed = [name for name in original if original[name] != inventory[name]]
assert changed == ['tests/compaction_127.rs']
proof = {'complete': True, 'utc': datetime.now(timezone.utc).isoformat(), 'candidate_source_sha256': inventory,
         'changed_only_test_type_annotation': True, 'engine_algorithm_unchanged': True, 'original_failed_source_and_logs_retained': True,
         'timed_cases_declared': 0, 'no_timer_started': True}
(WORK / 'preparation-proof-v2.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
source = (ROOT / 'build_phase_127.py').read_text(encoding='utf-8')
for before, after in [("WORK / 'candidate'", "WORK / 'candidate-v2'"),
                      ('preparation-proof.json', 'preparation-proof-v2.json'),
                      ('build-proof.json', 'build-proof-v2.json'),
                      ('build-declaration.json', 'build-declaration-v2.json'),
                      ('build-step-', 'build-v2-step-'),
                      ('build-failure.json', 'build-failure-v2.json'),
                      ("WORK / 'logs'", "WORK / 'logs-v2'"),
                      ("WORK / 'test-stores'", "WORK / 'test-stores-v2'"),
                      ("WORK / 'binary'", "WORK / 'binary-v2'")]:
    assert before in source, before
    source = source.replace(before, after)
ast.parse(source)
for name in ['logs-v2', 'test-stores-v2', 'binary-v2']:
    (WORK / name).mkdir()
(ROOT / 'build_phase_127_v2.py').write_text(source, encoding='utf-8', newline='\n')
print('Only the new test column type annotated; original failed source retained; full prerequisites will run.')
