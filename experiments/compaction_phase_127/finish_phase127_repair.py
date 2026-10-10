from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, json, shutil
ROOT = Path('D:/Codex/Kestrel/work')
WORK = ROOT / 'perf-127'
proof = json.loads((WORK / 'preparation-proof-v2.json').read_text(encoding='utf-8'))
for name, digest in proof['candidate_source_sha256'].items():
    assert hashlib.sha256((WORK / 'candidate-v2' / name).read_bytes()).hexdigest() == digest
assert proof['changed_only_test_type_annotation'] and proof['engine_algorithm_unchanged']
shutil.copy2(ROOT / 'repair_phase127_test_v2.py', WORK / 'failed-repair-controller-v1.py')
(WORK / 'repair-controller-failure.json').write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
    'actual_exit': 1, 'error': "AssertionError: WORK / 'binary'", 'cause': 'Artifact path is one binary/candidate127.exe string, not a standalone binary directory literal.',
    'engine_source_and_test_repair_already_preserved': True, 'no_v2_build_or_timing_started': True}, indent=2) + '\n', encoding='utf-8')
source = (ROOT / 'build_phase_127.py').read_text(encoding='utf-8')
for before, after in [("WORK / 'candidate'", "WORK / 'candidate-v2'"),
                      ('preparation-proof.json', 'preparation-proof-v2.json'), ('build-proof.json', 'build-proof-v2.json'),
                      ('build-declaration.json', 'build-declaration-v2.json'), ('build-step-', 'build-v2-step-'),
                      ('build-failure.json', 'build-failure-v2.json'), ("WORK / 'logs'", "WORK / 'logs-v2'"),
                      ("WORK / 'test-stores'", "WORK / 'test-stores-v2'"), ('binary/candidate127.exe', 'binary-v2/candidate127.exe')]:
    assert before in source, before
    source = source.replace(before, after)
ast.parse(source)
for name in ['logs-v2', 'test-stores-v2', 'binary-v2']:
    assert not (WORK / name).exists()
    (WORK / name).mkdir()
(ROOT / 'build_phase_127_v2.py').write_text(source, encoding='utf-8', newline='\n')
print('Corrected artifact-path controller derivation; all failed source retained; full v2 build now prepared.')
