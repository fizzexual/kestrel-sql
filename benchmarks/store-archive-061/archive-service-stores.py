"""Verify duplicate uncompressed stores against the published archive before removal."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

W = Path(__file__).resolve().parent
ROOT = W.parents[1] / 'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
bundle = load(ROOT / 'benchmarks/core-read-path-061-bundle-check.json')
publication = load(ROOT / 'benchmarks/core-read-path-061-publication.json')
archive = ROOT.parent / bundle['artifact']
assert sha(archive) == bundle['sha256']
asset = next(a for a in publication['new_assets'] if a['name'] == archive.name)
assert asset['server_digest_matched'] and asset['sha256'] == bundle['sha256']
assert not load(W / 'post-qualification-process-check.json')['active_processes']
directory = (W / 'service-fixtures').resolve()
assert directory.is_relative_to(W.resolve()) and directory.name == 'service-fixtures'
inventory = load(W / 'fixture-inventory.json')
expected = {n: d for n, d in inventory.items() if n.startswith('service-fixtures/')}
actual = {p.relative_to(W).as_posix() for p in directory.rglob('*') if p.is_file()}
assert actual == set(expected)
assert len([p for p in directory.iterdir() if p.is_dir()]) == 36
assert not any(p.is_symlink() or p.is_junction() for p in directory.rglob('*'))
total = 0
with zipfile.ZipFile(archive) as z:
    for n, d in expected.items():
        p = W / n
        assert p.resolve().is_relative_to(directory) and p.stat().st_size == d['bytes'] and sha(p) == d['sha256']
        member = 'kestrel-sql/benchmarks/core-read-path-061/' + n
        assert z.getinfo(member).file_size == d['bytes']
        with z.open(member) as f:
            assert hashlib.file_digest(f, 'sha256').hexdigest() == d['sha256']
        total += d['bytes']
proof = {'checked_utc': datetime.now(timezone.utc).isoformat(), 'directory': str(directory),
         'store_count': 36, 'files': len(expected), 'uncompressed_bytes': total,
         'archive': str(archive), 'archive_sha256': bundle['sha256'], 'private_release_url': asset['download_url'],
         'each_file_size_crc_and_sha256_matches_local_and_published_archive': True,
         'all_raw_measurements_source_and_original_results_retained': True,
         'restore_member_prefix': 'kestrel-sql/benchmarks/core-read-path-061/service-fixtures/',
         'removal_not_yet_performed': True}
(W / 'store-archive-plan.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'validated_files': len(expected), 'uncompressed_bytes': total}))
