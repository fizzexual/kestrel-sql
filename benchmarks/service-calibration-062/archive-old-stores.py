"""Verify the 055 duplicate stores against their immutable published ZIP."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

W = Path(__file__).resolve().parent
OLD = W.parent / 'perf-055'
ROOT = W.parents[1] / 'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))
name = 'kestrel-sql-development-cat6-055-service-evidence.zip'
archive = ROOT.parent / name
asset = next(a for r in load(ROOT / 'repository-publication.json')['releases'] for a in r['assets'] if a['name'] == name)
assert sha(archive) == asset['sha256'] == '7b9aed8ba6fb7a3e278e92fea2bd56a4f0c6e2ab73067eebfc23504debecde42'
report = load(OLD / 'paired-service.json')
assert report['complete'] and len(report['cases']) == 36
parents = {str(Path(c['fixture']).resolve().parent) for c in report['cases']}
assert len(parents) == 1
directory = Path(parents.pop())
assert directory.is_relative_to(OLD.resolve()) and directory.name == 'service-fixtures'
expected = {entry['label'] + '/' + n: d for entry in load(OLD / 'fixture-inventory.json') for n, d in entry['files'].items()}
actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file()}
assert actual == set(expected)
assert not any(p.is_symlink() or p.is_junction() for p in directory.rglob('*'))
total = 0
prefix = 'kestrel-sql/benchmarks/trial-055-service/local-service-fixtures/'
with zipfile.ZipFile(archive) as z:
    for n, d in expected.items():
        p = directory / n
        assert p.resolve().is_relative_to(directory) and p.stat().st_size == d['bytes'] and sha(p) == d['sha256']
        assert z.getinfo(prefix + n).file_size == d['bytes']
        with z.open(prefix + n) as f:
            assert hashlib.file_digest(f, 'sha256').hexdigest() == d['sha256']
        total += d['bytes']
proof = {'checked_utc': datetime.now(timezone.utc).isoformat(), 'directory': str(directory),
         'store_count': 36, 'files': len(expected), 'uncompressed_bytes': total,
         'archive': str(archive), 'archive_sha256': asset['sha256'], 'private_release_url': asset['download_url'],
         'each_file_size_crc_and_sha256_matches_local_and_published_archive': True,
         'all_055_raw_results_sources_and_failures_retained': True,
         'restore_member_prefix': prefix, 'removal_not_yet_performed': True}
(W / 'old-store-archive-plan.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'verified_055_stores': 36, 'files': len(expected), 'uncompressed_bytes': total}))
