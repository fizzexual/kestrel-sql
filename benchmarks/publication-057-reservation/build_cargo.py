"""Independent reproduction build; never overwrites frozen original evidence."""
from pathlib import Path
import datetime, hashlib, json, os, shutil, subprocess

W = Path(__file__).resolve().parent

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

assert not (W / 'build-provenance.json').exists() and not (W / 'reservation-probe.exe').exists()
source = W / 'reservation_probe.rs'
assert source.is_file() and (W / 'Cargo.lock').is_file()
assert (W / 'default-engine-baseline.json').is_file()
env = dict(os.environ)
env['CARGO_TARGET_DIR'] = str(W / 'target')
env['RUSTFLAGS'] = '-D warnings'
command = ['cargo', 'build', '--release', '--locked', '--manifest-path', str(W / 'Cargo.toml')]
with (W / 'build.txt').open('w') as log:
    status = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
assert status == 0, 'Reproduction build failed; preserve build.txt'
name = 'reservation-probe.exe' if os.name == 'nt' else 'reservation-probe'
binary = W / 'target/release' / name
# The historical runner's path retains .exe; executable content is platform-specific.
shutil.copy2(binary, W / 'reservation-probe.exe')
proof = {'compiled_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'method': 'Independent Cargo reproduction, not original cached-rustc binary',
         'command': command, 'strict_warnings_passed': True, 'unsafe_code_forbidden': True,
         'source_sha256': sha(source), 'binary_sha256': sha(W / 'reservation-probe.exe'),
         'cargo_lock_sha256': sha(W / 'Cargo.lock'), 'cargo_manifest_sha256': sha(W / 'Cargo.toml'),
         'toolchain': subprocess.check_output(['rustc', '--version'], text=True).strip(),
         'model_only': True, 'no_sql_engine_source_changed': True}
(W / 'build-provenance.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof))
