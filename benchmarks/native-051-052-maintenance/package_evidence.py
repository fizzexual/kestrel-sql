from pathlib import Path
import hashlib, json, zipfile
W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
packages = [
    ('publication-051-native', 'PUBLICATION_051.md', 'publication-051-preservation.json',
     'kestrel-sql-development-publication-051-evidence.zip', 'PUBLICATION_051_MANIFEST.sha256'),
    ('trial-052-pending-length', 'TRIAL_052.md', 'trial-052-preservation.json',
     'kestrel-sql-development-cat5-052-rejected-evidence.zip', 'TRIAL_052_MANIFEST.sha256'),
]
proofs = []
for folder, report, preservation, filename, manifest in packages:
    files = [*sorted(p for p in (ROOT / 'benchmarks' / folder).rglob('*') if p.is_file()),
             ROOT / report, ROOT / 'benchmarks' / preservation]
    archive = ROOT.parent / filename
    assert not archive.exists()
    inventory = {p.relative_to(ROOT).as_posix(): sha(p) for p in files}
    preserved = json.loads((ROOT / 'benchmarks' / preservation).read_text())['payload_sha256']
    for name, digest in preserved.items():
        assert inventory['benchmarks/' + folder + '/' + name] == digest
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in files:
            z.write(p, 'kestrel-sql/' + p.relative_to(ROOT).as_posix())
        z.writestr('kestrel-sql/' + manifest, ''.join(f'{v}  {k}\n' for k, v in sorted(inventory.items())))
        z.writestr('kestrel-sql/DEVELOPMENT_EVIDENCE.md',
                   'This is isolated development/diagnostic evidence, not a supported engine release. Supported 0.3.16 and all historical archives remain unchanged. Read ' + report + ' for all slower rounds, rejected gates, fault model and reproducibility limits. Source and binary provenance references existing immutable released/development snapshots.\n')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist()) == len(inventory) + 2
        for name, digest in inventory.items():
            assert hashlib.sha256(z.read('kestrel-sql/' + name)).hexdigest() == digest
    digest = sha(archive)
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n')
    proofs.append({'artifact': filename, 'bytes': archive.stat().st_size, 'sha256': digest,
                   'payload_files': len(inventory), 'zip_entries': len(inventory) + 2,
                   'all_payload_hashes_and_zip_crc_verified': True, 'new_engine_release': False,
                   'trial_promoted': False, 'default_engine_changed': False})
(ROOT / 'benchmarks/native-051-052-bundle-check.json').write_text(json.dumps(proofs, indent=2) + '\n')
print(json.dumps(proofs))
