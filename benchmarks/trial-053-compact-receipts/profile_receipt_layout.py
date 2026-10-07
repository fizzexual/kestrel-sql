"""Post-benchmark wire-footprint model; reads fixtures without changing them."""
from pathlib import Path
import datetime, hashlib, json, struct, zlib
W = Path(__file__).resolve().parent
WORK = W.parent

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def compact(data):
    return json.dumps(data, separators=(',', ':'), ensure_ascii=False).encode()

policy = {
    'declared_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'purpose': 'Measure receipt checkpoint byte footprint before implementing a new isolated format',
    'read_only': True, 'engine_benchmark': False, 'new_engine_format': 'Proposed CAT6 receipt tuple [lowercase SHA-256 hex, rows, original generation]',
    'compatibility_plan': 'Reader accepts existing CAT2/3/4/5; new writers emit CAT6; old writers reject CAT6 before data access; no downgrade promise',
    'unchanged': 'SHA-256 domain, identifier map, original generation, receipt rows, file sync_all, pending/rename publication, segment frame and payload CRCs',
    'limits': 'Same 100000-ID map and 32-catalog chain; duplicates, bad digest length/characters, wrong tuple shape and invalid generations must fail closed',
    'retention': 'No frozen fixture or rejected 052 source is modified; derive next candidate only from frozen 050',
}
assert not (W / 'layout-policy.json').exists()
(W / 'layout-policy.json').write_text(json.dumps(policy, indent=2) + '\n')
cases = []
for size in [0, 50000, 99000]:
    folder = WORK / 'perf-051/fixtures' / f"{[0,2,4][[0,50000,99000].index(size)]:02d}-r0-{size}-released_016"
    headers = []
    for p in folder.glob('catalog-*.ks2'):
        with p.open('rb') as f:
            header = f.read(16)
        headers.append((struct.unpack('<I', header[8:12])[0], p))
    _, p = max(headers, key=lambda v: v[0])
    original_sha = sha(p)
    with p.open('rb') as f:
        header = f.read(16)
        data = f.read(struct.unpack('<I', header[8:12])[0])
    assert header[:8] == b'KSQLCAT4' and zlib.crc32(data) == struct.unpack('<I', header[12:16])[0]
    body = json.loads(data)
    assert compact(body) == data, 'Byte model must reproduce the original compact JSON'
    transformed = {**body, 'batches': {key: [bytes(v['digest']).hex(), v['rows'], v['generation']]
                                     for key, v in body['batches'].items()}}
    encoded = compact(transformed)
    restored = {key: {'digest': list(bytes.fromhex(v[0])), 'rows': v[1], 'generation': v[2]}
                for key, v in json.loads(encoded)['batches'].items()}
    assert restored == body['batches'] and sha(p) == original_sha
    cases.append({'starting_receipts': size, 'checkpoint_receipts': len(body['batches']),
                  'fixture': str(p), 'fixture_sha256': original_sha, 'original_json_bytes': len(data),
                  'proposed_tuple_hex_json_bytes': len(encoded), 'byte_ratio': len(encoded)/len(data),
                  'saved_bytes': len(data)-len(encoded), 'old_digest_array_bytes': sum(len(compact(v['digest'])) for v in body['batches'].values()),
                  'proposed_digest_string_bytes': len(body['batches']) * 66,
                  'all_ids_digests_rows_and_original_generations_roundtrip': True})
out = {'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'cases': cases,
       'exact_original_json_reproduced': True, 'source_fixtures_unchanged': True,
       'measured_engine_speedup': False, 'model_only': True}
(W / 'layout-footprint.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out))
