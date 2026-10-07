from pathlib import Path
import datetime, hashlib, json, shutil, zipfile

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
DEST = ROOT / 'benchmarks/publication-056-io-model'

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(p, j):
    p.write_text(json.dumps(j, indent=2) + '\n', encoding='utf-8')

audit = json.loads((W / 'model-audit.json').read_text())
assert not audit['every_model_hypothesis_check_passed'] and audit['complete_cases'] == 12
assert audit['fixture_files'] == 1542 and audit['independently_recomputed_samples'] == 3072
post = json.loads((W / 'post-timing-process-check.json').read_text(encoding='utf-8-sig'))
assert not post['active_processes'] and post['timing_completed']
baseline = json.loads((W.parent / 'perf-055/baseline.json').read_text())
for n, d in baseline['core_source_sha256'].items():
    assert sha(ROOT / n) == d
for n, d in baseline['baseline_binary_sha256'].items():
    assert sha(ROOT / 'bin' / n) == d
assert not DEST.exists()
DEST.mkdir()
payload = {}
for p in W.rglob('*'):
    if p.is_file() and 'fixtures' not in p.relative_to(W).parts and p.suffix != '.pdb':
        rel = p.relative_to(W)
        out = DEST / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)
        assert sha(out) == sha(p)
        payload[rel.as_posix()] = sha(out)
preservation = {'preserved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'source_work_directory': str(W), 'model_only': True, 'new_engine_release': False,
                'default_source_and_binaries_unchanged': True, 'every_model_check_passed': False,
                'full_fixture_files_preserved_in_work_and_zip': 1542, 'payload_sha256': payload}
save(ROOT / 'benchmarks/publication-056-preservation.json', preservation)
intro = ('**Morning report, October 7:** [Bulgarian before/after, wins/losses, recovery and every failed trial](OVERNIGHT_2026-10-07.md). '
         '[056 tests a persistent-file primitive and fails two hypothesis checks](PUBLICATION_056.md); it changes no SQL engine. '
         'Supported 0.3.16 and all earlier releases remain unchanged.\n\n')
for name in ['README.md', 'BENCHMARK_HISTORY.md', 'ARCHIVE.md', 'PORTFOLIO.md']:
    p = ROOT / name
    text = p.read_text(encoding='utf-8')
    first, remaining = text.split('\n\n', 1)
    p.write_text(first + '\n\n' + intro + remaining, encoding='utf-8')
files = {p.relative_to(ROOT).as_posix(): p for p in DEST.rglob('*') if p.is_file()}
for name in ['PUBLICATION_056.md', 'benchmarks/publication-056-preservation.json']:
    files[name] = ROOT / name
fixtures = json.loads((W / 'fixture-inventory.json').read_text())
for rel, values in fixtures.items():
    p = W / 'fixtures' / rel
    assert sha(p) == values['sha256'] and p.stat().st_size == values['bytes']
    files['benchmarks/publication-056-io-model/local-model-fixtures/' + rel] = p
archive = ROOT.parent / 'kestrel-sql-development-io-056-model-evidence.zip'
assert not archive.exists()
inventory = {name: sha(p) for name, p in files.items()}
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
    for name, p in files.items():
        z.write(p, 'kestrel-sql/' + name)
    z.writestr('kestrel-sql/PUBLICATION_056_MANIFEST.sha256', ''.join(f'{d}  {n}\n' for n, d in sorted(inventory.items())))
    z.writestr('kestrel-sql/MODEL_ONLY.md', 'Storage primitive model, not SQL/Archive WAL. All frames sync before each measured commit. Two declared checks fail. No SQL, source/receipt, checkpoint, concurrency or crash qualification. All slower series are retained. Read PUBLICATION_056.md.\n')
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None and len(z.namelist()) == len(inventory) + 2
    for name, digest in inventory.items():
        with z.open('kestrel-sql/' + name) as f:
            assert hashlib.file_digest(f, 'sha256').hexdigest() == digest
digest = sha(archive)
archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n')
check = {'artifact': archive.name, 'bytes': archive.stat().st_size, 'sha256': digest,
         'zip_entries': len(inventory) + 2, 'payload_files': len(inventory), 'full_model_fixture_files': len(fixtures),
         'all_payload_and_fixture_hashes_verified': True, 'zip_crc_verified': True,
         'model_only': True, 'new_engine_release': False, 'default_engine_changed': False,
         'packaged_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
save(ROOT / 'benchmarks/publication-056-bundle-check.json', check)
print(json.dumps(check))
