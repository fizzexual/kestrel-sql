"""Create a separate replay directory; never overwrite any original evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

source = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--destination', type=Path, required=True)
parser.add_argument('--phase', choices=['primary', 'matrix', 'service'], required=True)
args = parser.parse_args()
dest = args.destination.resolve()
assert not dest.exists(), 'Choose a fresh replay directory'
assert not dest.is_relative_to(source) and not source.is_relative_to(dest), 'Replay must be separate'
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
inventory = json.loads((source / 'analytical-input-inventory.json').read_text())
for name, d in inventory['files'].items():
    if args.phase == 'service':
        continue
    if args.phase == 'primary' and not name.startswith('inputs/primary/'):
        continue
    if args.phase == 'matrix' and not name.startswith('inputs/analytical/'):
        continue
    assert sha(source / name) == d['sha256']
    p = dest / name
    p.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / name, p)
shutil.copytree(source / 'lab/outputs/kestrel-sql', dest / 'lab/outputs/kestrel-sql')
shutil.copytree(source / 'lab/work/perf-061/candidate', dest / 'lab/work/perf-061/candidate')
for name in ['matrix.py', 'primary.py', 'paired_service.py', 'policy.json', 'service-policy.json',
             'qualification.json', 'baseline.json']:
    shutil.copy2(source / name, dest / name)
policy = json.loads((dest / 'policy.json').read_text())
for f in policy['analytical_matrix']['fixtures']:
    folder = dest / 'inputs/analytical' / (f['scope'] + '-' + f['label'])
    f['archive'] = str(folder / 'archive')
    f['reference'] = str(folder / 'reference.duckdb')
policy['primary_range_goal']['fixture'] = str(dest / 'inputs/primary/archive')
policy['replay_of_policy_sha256'] = sha(source / 'policy.json')
policy['original_samples_not_replaced'] = True
(dest / 'policy.json').write_text(json.dumps(policy, indent=2) + '\n', encoding='utf-8')
script = {'primary': 'primary.py', 'matrix': 'matrix.py', 'service': 'paired_service.py'}[args.phase]
# The caller supplies the native-library PYTHONPATH and owns this serial process.
environment = dict(os.environ)
environment['PYTHONPATH'] = str(dest / 'lab/outputs/kestrel-sql/benchmarks') + os.pathsep + environment.get('PYTHONPATH', '')
subprocess.run([sys.executable, '-u', str(dest / script)], env=environment, check=True)
