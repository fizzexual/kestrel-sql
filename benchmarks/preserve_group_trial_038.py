"""Keep initial candidate source, binaries and checks before the next iteration."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / 'work'
proof = json.loads((ROOT / 'benchmarks/rust-checks-038.json').read_text())
destination = ROOT / 'benchmarks/trial-038-cell-source'
assert not destination.exists()
for relative, digest in proof['source_sha256'].items():
    source = ROOT / relative
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    target = destination / relative; target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
shutil.copy2(ROOT / 'benchmarks/rust-checks-038.json', ROOT / 'benchmarks/rust-checks-038-cell-trial.json')
shutil.copytree(WORK / 'perf-038/candidate', WORK / 'perf-038/cell-trial')
audit = {'initial_source_and_binary_preserved': True, 'comparison': 'group-038-comparison.json',
    'fixture_correction': 'sparse17 generated (i*17)%17, always zero; it is a single-key case, not a sparse-17-key result. Replaced with domain19 and checked actual distinct keys.',
    'next_iteration': 'typed aggregate arrays, shared SUM/AVG reductions'}
(ROOT / 'benchmarks/group-038-cell-trial-audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
