"""Exact previously failing bytes, isolated copies and positive legacy migration."""
from pathlib import Path
import hashlib, json, shutil, subprocess, os, datetime
from stress_compare import Engine

w = Path(__file__).resolve().parents[1]
root = w.parents[1] / 'outputs/kestrel-sql'
original = w.parent / 'perf-049/alias-bundle'
out = w / 'semantic-recovery.json'
assert not out.exists()

def hashes(path):
    return {p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob('*') if p.is_file() and p.name not in ['.lock', 'archive.lockfile']}

original_hashes = hashes(original)
cases = []
for trial in ['048', '049']:
    directory = w / ('alias-confirm-final-' + trial)
    shutil.copytree(original, directory)
    binary = w.parent / f'perf-{trial}/bin/kestrel-stress.exe'
    e = Engine('kestrel', directory, 0, binary, {}, existing=True)
    c = e.connect()
    try:
        partial = c.query('SELECT SUM(value) FROM events WHERE ts >= 100 AND ts < 300')
        full = c.query('SELECT SUM(value) FROM events')
        verified = c.call({'op': 'verify'})['verified_bytes']
        assert partial == [[400]] and full == [[5123]] and verified == 24600
        cases.append({'variant': trial, 'wrong_partial_sum': partial, 'expected': [[2000]],
                      'full_sum': full, 'verified_bytes': verified, 'fixture_sha256': hashes(directory),
                      'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest()})
    finally:
        c.close()
        e.finish()

for variant, binary in [('released-0.3.16', root / 'bin/baseline-0.3.16/kestrel-stress.exe'),
                        ('050', w / 'bin/kestrel-stress.exe')]:
    directory = w / ('alias-reject-final-' + variant)
    shutil.copytree(original, directory)
    before = hashes(directory)
    p = subprocess.Popen([str(binary), str(directory / 'archive'), '0', '0', '0'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         creationflags=0x08000000 if os.name == 'nt' else 0)
    try:
        stdout, stderr = p.communicate(timeout=15)
        assert p.returncode != 0, (variant, stdout, stderr)
        if variant == '050':
            assert b'invalid catalog schema or segment references' in stderr, stderr
        else:
            assert any(message in stderr for message in [b'invalid archive format signature', b'catalog has trailing bytes']), stderr
        assert before == hashes(directory)
        cases.append({'variant': variant, 'rejected_before_data_access': True,
                      'returncode': p.returncode, 'stderr': stderr.decode('utf-8'),
                      'fixture_files_unchanged': True,
                      'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest()})
    finally:
        if p.poll() is None:
            p.terminate()
            p.wait(timeout=10)

directory = w / 'valid-unique-generation-legacy-upgrade'
shutil.copytree(w.parent / 'perf-049/alias-legacy', directory)
e = Engine('kestrel', directory, 0, w / 'bin/kestrel-stress.exe', {}, existing=True)
c = e.connect()
try:
    assert c.query('SELECT SUM(value) FROM events WHERE ts >= 100 AND ts < 300') == [[1800]]
    retry = c.call({'op': 'append', 'id': 'b', 'data': [[i, 9, 1] for i in range(512)]})
    assert retry['duplicate'] and retry['generation'] == 1
    receipt = c.call({'op': 'append', 'id': 'unique-next', 'data': [[1000, 3, 1]]})
    assert receipt['generation'] == 2 and not receipt['duplicate']
    assert c.query('SELECT SUM(value) FROM events') == [[4611]]
    assert c.query('SELECT SUM(value) FROM events WHERE ts >= 100 AND ts < 300') == [[1800]]
    assert c.call({'op': 'verify'})['verified_bytes'] == 513 * 24
finally:
    c.close()
    e.finish()
cases.append({'variant': '050', 'distinct_generation_mixed_legacy_upgrade_passed': True,
              'original_receipt_generation_preserved': True, 'partial_sum': [[1800]],
              'full_sum': [[4611]], 'verified_bytes': 513 * 24})
assert hashes(original) == original_hashes
out.write_text(json.dumps({'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          'cases': cases, 'original_failing_fixture_unchanged': True,
                          'original_fixture_sha256': original_hashes, 'passed': True},
                         indent=2) + '\n', encoding='utf-8')
print('048/049 defect reproduced; default 0.3.16 and 050 reject; unique-generation legacy upgrade passes')
