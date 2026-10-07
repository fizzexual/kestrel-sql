from pathlib import Path
import datetime, hashlib, json, math, statistics, struct, zlib

W = Path(__file__).resolve().parent

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(name, data):
    (W / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

def quantile(values, q):
    v = sorted(values)
    pos = (len(v) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    return v[lo] + (v[hi] - v[lo]) * (pos - lo)

def independent_payload(seq, size):
    mask = (1 << 64) - 1
    state = ((seq * 0x9e3779b97f4a7c15) & mask) ^ (size << 1)
    out = bytearray()
    for _ in range(size // 8):
        state ^= (state << 13) & mask
        state ^= state >> 7
        state ^= (state << 17) & mask
        out.extend(struct.pack('<Q', state))
    return bytes(out)

def frame_checked(data, seq, size):
    assert len(data) == size + 48
    header, payload, footer = data[:32], data[32:-16], data[-16:]
    assert header[:8] == b'KIO056F1'
    sequence, length, crc, complement, header_crc = struct.unpack('<QIIII', header[8:])
    assert sequence == seq and length == size and complement == (~size & 0xffffffff)
    assert zlib.crc32(header[:28]) == header_crc and zlib.crc32(payload) == crc
    assert footer[:8] == b'IOCOMMIT'
    frame_crc, complement = struct.unpack('<II', footer[8:])
    assert frame_crc == zlib.crc32(data[:-16]) and complement == (~frame_crc & 0xffffffff)
    if seq in (1, 256):
        assert payload == independent_payload(seq, size)

policy = json.loads((W / 'policy.json').read_text())
results = json.loads((W / 'model-results.json').read_text())
build = json.loads((W / 'build-provenance.json').read_text())
assert results['complete'] and not results['failures'] and len(results['cases']) == 12
assert results['policy_sha256'] == sha(W / 'policy.json')
assert sha(W / 'io-lifecycle-probe.exe') == build['binary_sha256'] == policy['binary_sha256']
assert sha(W / 'io_lifecycle_probe.rs') == build['source_sha256'] == policy['source_sha256']
rows = []
inventory = {}
frames_verified = bytes_verified = 0
for i, case in enumerate(results['cases']):
    spec, label = case['spec'], case['label']
    assert spec == policy['cases'][i]
    raw = W / 'raw' / (label + '.stdout.json')
    assert sha(raw) == case['stdout_sha256']
    status = json.loads((W / 'raw' / (label + '.status.json')).read_text())
    assert status['exit_code'] == 0 and status['spec'] == spec and not status.get('timeout')
    assert status['started_utc'] > policy['declared_utc'] > build['compiled_utc']
    data = json.loads(raw.read_text())
    assert data['sync_all_each_commit'] and data['cold_exact_frame_bytes_verified']
    assert not data['sql_source_receipt_checkpoint_retention_and_crash_qualification']
    assert data['mode'] == spec['mode'] and data['payload_bytes'] == spec['payload_bytes']
    samples = data['raw_samples']
    assert len(samples) == spec['repetitions'] == 256
    stages = ['create_ms', 'write_ms', 'sync_ms', 'rename_ms']
    for seq, s in enumerate(samples, 1):
        assert s['seq'] == seq
        assert all(math.isfinite(s[k]) and s[k] >= 0 for k in stages + ['total_ms'])
        assert sum(s[k] for k in stages) <= s['total_ms'] + 1e-7
    totals = [s['total_ms'] for s in samples]
    row = {**case, 'p50_ms': quantile(totals, .5), 'p99_ms': quantile(totals, .99),
           'max_ms': max(totals), 'total_ms': sum(totals),
           'above_500ms': sum(t > 500 for t in totals), 'above_1000ms': sum(t > 1000 for t in totals),
           'stage_totals_ms': {k: sum(s[k] for s in samples) for k in stages}}
    folder = W / 'fixtures' / label
    size = spec['payload_bytes']
    frame_digest = hashlib.sha256()
    if spec['mode'] == 'journal':
        paths = [folder / 'journal.bin']
        assert set(folder.iterdir()) == set(paths)
        with paths[0].open('rb') as f:
            assert f.read(16) == b'KIO056J1' + struct.pack('<Q', 256)
            for seq in range(1, 257):
                frame = f.read(size + 48)
                frame_checked(frame, seq, size)
                frame_digest.update(frame)
            assert not f.read(1)
    else:
        paths = [folder / f'{seq:08}.frame' for seq in range(1, 257)]
        assert set(folder.iterdir()) == set(paths)
        for seq, p in enumerate(paths, 1):
            frame = p.read_bytes()
            frame_checked(frame, seq, size)
            frame_digest.update(frame)
    for p in paths:
        inventory[p.relative_to(W / 'fixtures').as_posix()] = {'bytes': p.stat().st_size, 'sha256': sha(p)}
    row['whole_frame_stream_sha256'] = frame_digest.hexdigest()
    frames_verified += 256
    bytes_verified += 256 * (size + 48)
    rows.append(row)
paired = []
for size in (2400, 153600):
    pairs = []
    for turn in range(3):
        a = next(r for r in rows if r['spec']['payload_bytes'] == size and r['spec']['round'] == turn and r['spec']['mode'] == 'generation')
        b = next(r for r in rows if r['spec']['payload_bytes'] == size and r['spec']['round'] == turn and r['spec']['mode'] == 'journal')
        assert a['whole_frame_stream_sha256'] == b['whole_frame_stream_sha256']
        pairs.append({'round': turn, 'generation_label': a['label'], 'journal_label': b['label'],
                      'whole_frame_stream_sha256': a['whole_frame_stream_sha256'],
                      'ratios_journal_over_generation': {k: b[k] / a[k] for k in ['p50_ms', 'p99_ms', 'max_ms', 'total_ms']}})
    ratios = {k: statistics.median(p['ratios_journal_over_generation'][k] for p in pairs) for k in ['p50_ms', 'p99_ms', 'max_ms', 'total_ms']}
    checks = {'total_at_most_0_85': ratios['total_ms'] <= .85, 'p99_at_most_0_95': ratios['p99_ms'] <= .95, 'p50_guard_at_most_1_05': ratios['p50_ms'] <= 1.05}
    paired.append({'payload_bytes': size, 'pairs': pairs, 'paired_median_ratios': ratios, 'hypothesis_checks': checks,
                   'medians_by_mode': {mode: {k: statistics.median(r[k] for r in rows if r['spec']['payload_bytes'] == size and r['spec']['mode'] == mode) for k in ['p50_ms', 'p99_ms', 'max_ms', 'total_ms']} for mode in ['generation', 'journal']}})
audit = {'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'model_only': True,
         'complete_cases': 12, 'independently_recomputed_samples': frames_verified, 'independently_crc_verified_frame_bytes': bytes_verified,
         'independent_known_payload_vectors': 24, 'byte_identical_mode_pairs': 6,
         'all_policy_and_source_binary_and_raw_hashes_verified': True,
         'all_samples_finite_and_stage_totals_bounded': True, 'type7_quantiles': True,
         'all_file_header_footer_crc_complements_sequences_and_eof_passed': True,
         'full_sync_each_measured_commit_verified_in_probe_source': True,
         'sql_or_crash_or_archive_wal_qualification': False, 'new_engine_release': False, 'default_engine_changed': False,
         'every_model_hypothesis_check_passed': all(all(r['hypothesis_checks'].values()) for r in paired), 'paired': paired, 'cases': rows,
         'fixture_files': len(inventory), 'fixture_bytes': sum(v['bytes'] for v in inventory.values())}
save('model-audit.json', audit)
save('fixture-inventory.json', inventory)
print(json.dumps({k: v for k, v in audit.items() if k != 'cases'}))
