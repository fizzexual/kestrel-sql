from pathlib import Path
import hashlib, json, zipfile

w = Path(__file__).parent
root = w.parents[1] / 'outputs/kestrel-sql'
d = root / 'benchmarks/trial-050-service'
audit = json.loads((d / 'paired-service-audit.json').read_text(encoding='utf-8'))
assert audit['cases'] == 36 and audit['raw_quantiles_accounting_uniqueness_and_hashes_recomputed']
assert not audit['trial_promoted']
package = root.parent / 'kestrel-sql-development-cat5-050-service-evidence.zip'
assert not package.exists()
files = [*sorted(p for p in d.rglob('*') if p.is_file()), root / 'SERVICE_TRIAL_050.md', root / 'TRIAL_050.md',
         root / 'benchmarks/trial-050-service-preservation.json', root / 'benchmarks/baseline-0.3.16-provenance.json',
         root / 'benchmarks/trial-050-generation-identity/correctness-audit.json',
         root / 'benchmarks/trial-050-generation-identity/build-provenance.json',
         root / 'benchmarks/trial-050-service-follow-up.json']
inventory = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with zipfile.ZipFile(package, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in files:
        z.write(p, 'kestrel-sql/' + p.relative_to(root).as_posix())
    z.writestr('kestrel-sql/TRIAL_050_SERVICE_MANIFEST.sha256', ''.join(f'{digest}  {name}\n' for name, digest in sorted(inventory.items())))
    z.writestr('kestrel-sql/TRIAL_050_SERVICE_BUNDLE.md', '# Unreleased CAT5 trial 050: fresh service evidence\n\nAll 36 fresh paired cases and raw samples are retained. This is development evidence, not a supported engine release. Frozen source/binaries and preceding correctness gates are in the separate immutable kestrel-sql-development-cat5-050-correctness-evidence.zip, SHA-256 2db97a6ad655ec6c4113a70c79460d589a9f377e1951a24f2a30368ee260ae33, available under private release v0.3.16. See SERVICE_TRIAL_050.md for every gate, slower case and limitation.\n')
with zipfile.ZipFile(package) as z:
    assert z.testzip() is None
    for name, digest in inventory.items():
        assert hashlib.sha256(z.read('kestrel-sql/' + name)).hexdigest() == digest
    assert len(z.namelist()) == len(inventory) + 2
digest = hashlib.file_digest(package.open('rb'), 'sha256').hexdigest()
package.with_suffix('.zip.sha256').write_text(f'{digest}  {package.name}\n', encoding='utf-8')
proof = {'artifact': package.name, 'bytes': package.stat().st_size, 'sha256': digest,
         'payload_files': len(inventory), 'zip_entries': len(inventory) + 2,
         'all_payloads_and_zip_crc_verified': True, 'trial_promoted': False,
         'default_engine_changed': False, 'original_release_archive_replaced': False,
         'correctness_dependency_sha256': '2db97a6ad655ec6c4113a70c79460d589a9f377e1951a24f2a30368ee260ae33'}
(root / 'benchmarks/trial-050-service-bundle-check.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps(proof))
