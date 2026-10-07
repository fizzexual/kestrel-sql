"""Package supplemental service evidence without replacing any engine release ZIP."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT.parent / 'kestrel-sql-0.3.16-service-047-evidence.zip'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    assert not PACKAGE.exists(), 'Supplemental archives are immutable too'
    audit = json.loads((ROOT / 'benchmarks/service-047-audit.json').read_text(encoding='utf-8'))
    assert audit['cases'] == 52 and audit['raw_samples_accounting_and_quantiles_recomputed']
    assert not audit['engine_changed']
    files = {ROOT / 'SERVICE_047.md', ROOT / 'PUBLICATION_EXPERIMENT.md', ROOT / 'verification-v046.json'}
    files.update(p for p in (ROOT / 'benchmarks').glob('service-047-*') if p.is_file())
    for name in ['service_047.py', 'audit_service_047.py', 'preserve_047.py', 'package_service_047.py',
                 'stress_compare.py', 'host_telemetry.py', 'portable_servers.py', 'reference-packages.json']:
        files.add(ROOT / 'benchmarks' / name)
    files.add(ROOT / 'benchmarks/baseline-0.3.16-provenance.json')
    for relative in ['benchmarks/baseline-0.3.16-source', 'bin/baseline-0.3.16',
                     'benchmarks/service-047-baseline-samples', 'benchmarks/service-047-policy-samples',
                     'benchmarks/service-047-reference-samples']:
        files.update(p for p in (ROOT / relative).rglob('*') if p.is_file())
    for p in files:
        assert p.is_file() and p.resolve().is_relative_to(ROOT.resolve())
    inventory = {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)}
    manifest = ''.join(digest + '  ' + name + '\n' for name, digest in sorted(inventory.items()))
    with zipfile.ZipFile(PACKAGE, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in sorted(inventory):
            archive.write(ROOT / name, ROOT.name + '/' + name)
        archive.writestr(ROOT.name + '/SERVICE_047_MANIFEST.sha256', manifest)
        archive.writestr(ROOT.name + '/SERVICE_047_BUNDLE.md',
                         '# Supplement to released KestrelSQL 0.3.16\n\n'
                         'This contains post-release service evidence, all new raw samples, harnesses '
                         'and the frozen 0.3.16 baseline. It contains no replacement engine or default policy. '
                         'Use it alongside the immutable 0.3.16 engine ZIP for prior reports and complete repository context. '
                         'SERVICE_047_MANIFEST.sha256 covers every copied payload file; the two generated bundle '
                         'description/manifest files are not self-hashed.\n')
    with zipfile.ZipFile(PACKAGE) as archive:
        assert archive.testzip() is None
        for name, digest in inventory.items():
            assert hashlib.sha256(archive.read(ROOT.name + '/' + name)).hexdigest() == digest
            assert sha(ROOT / name) == digest
        assert len(archive.namelist()) == len(inventory) + 2
    digest = sha(PACKAGE)
    PACKAGE.with_suffix('.zip.sha256').write_text(digest + '  ' + PACKAGE.name + '\n', encoding='utf-8')
    result = {'artifact': PACKAGE.name, 'bytes': PACKAGE.stat().st_size, 'sha256': digest,
              'payload_files': len(inventory), 'zip_entries': len(inventory) + 2,
              'all_payload_bytes_and_zip_crc_verified': True, 'engine_changed': False,
              'original_release_archive_replaced': False, 'source_version': '0.3.16',
              'offered_operations': audit['offered_operations'], 'cases': audit['cases']}
    (ROOT / 'benchmarks/service-047-bundle-check.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
