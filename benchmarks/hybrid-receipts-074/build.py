"""Sequential model-only native qualification; retain every failed attempt."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

work = Path(__file__).resolve().parent
root = work.parents[1] / 'outputs/kestrel-sql'
model = work / 'model'
def now(): return datetime.now(timezone.utc).isoformat()
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def save(p, v): p.write_text(json.dumps(v, indent=2) + '\n', encoding='utf-8')
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (work / 'build-proof.json').exists()
assert shutil.disk_usage(work).free >= 2_500_000_000
base = load(work / 'baseline.json')
for n, d in base['core_source_sha256'].items(): assert sha(root / n) == d, n
for n, d in base['baseline_binary_sha256'].items(): assert sha(root / 'bin' / n) == d, n
temp = work / 'rust-temp'; temp.mkdir(exist_ok=True)
env = {**os.environ, 'CARGO_TARGET_DIR': str(work / 'build-cache'), 'TMP': str(temp), 'TEMP': str(temp)}
logs = work / 'build-logs'; logs.mkdir(exist_ok=True)
attempt = logs / ('attempt-' + str(len(list(logs.glob('attempt-*'))) + 1)); attempt.mkdir()
shutil.copytree(model, attempt / 'source-before-build')
records = []; counts = {}
jobs = [('fmt', ['cargo', 'fmt', '--check']),
        ('fmt-hybrid', ['rustfmt', '--edition', '2024', '--check', 'src/hybrid.rs']),
        ('debug', ['cargo', 'test', '--offline', '--locked']),
        ('release', ['cargo', 'test', '--release', '--offline', '--locked']),
        ('clippy', ['cargo', 'clippy', '--all-targets', '--offline', '--locked', '--', '-D', 'warnings']),
        ('build', ['cargo', 'build', '--release', '--offline', '--locked'])]
for name, argv in jobs:
    print('starting', name, flush=True); started = now()
    r = subprocess.run(argv, cwd=model, env=env, text=True, encoding='utf-8', errors='strict', capture_output=True)
    (attempt / (name + '.log')).write_text(r.stdout + r.stderr, encoding='utf-8')
    records.append({'name': name, 'argv': argv, 'exit': r.returncode, 'started_utc': started, 'ended_utc': now()})
    save(attempt / 'run-order.json', records)
    if r.returncode:
        (attempt / 'FAILURE.txt').write_text(name + ' failed; exact source and logs retained\n', encoding='utf-8')
        print((r.stdout + r.stderr)[-6000:]); sys.exit(r.returncode)
    if name in ['debug', 'release']:
        counts[name] = sum(map(int, re.findall(r'test result: ok\. (\d+) passed;', r.stdout)))
assert counts == {'debug': 40, 'release': 40}, counts
(work / 'bin').mkdir(exist_ok=True)
out = work / 'bin/hybrid-model.exe'
shutil.copy2(work / 'build-cache/release/kestrel-receipt-page-model.exe', out)
assert out.read_bytes()[:2] == b'MZ'
vendor = work / 'locked-registry-crates'; vendor.mkdir(exist_ok=True)
packages = []; cache = Path.home() / '.cargo/registry/cache'
for p in tomllib.loads((model / 'Cargo.lock').read_text(encoding='utf-8'))['package']:
    if 'source' not in p: continue
    name = f"{p['name']}-{p['version']}.crate"; found = list(cache.glob('*/' + name))
    assert len(found) == 1 and sha(found[0]) == p['checksum']
    shutil.copy2(found[0], vendor / name); packages.append({'name': name, 'sha256': p['checksum']})
assert len(packages) == 22
save(work / 'build-proof.json', {'complete': True, 'model_only': True, 'counts': counts,
    'format_and_strict_clippy_passed': True, 'binary_sha256': sha(out),
    'source_sha256': {p.relative_to(model).as_posix(): sha(p) for p in sorted(model.rglob('*')) if p.is_file()},
    'locked_crates': packages, 'commands': records, 'native_fixture_files_retained': True,
    'no_engine_edit_or_build': True, 'no_timed_cohort': True})
print(json.dumps({'build_complete': True, 'tests_each': 40, 'binary_sha256': sha(out)}))
