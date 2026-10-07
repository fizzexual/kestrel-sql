from pathlib import Path
import datetime, hashlib, json, math, os, statistics, struct, zlib

W = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('KESTREL_REPOSITORY', str(W.parents[1] / 'outputs/kestrel-sql'))).resolve()

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def save(n, j):
    (W / n).write_text(json.dumps(j, indent=2) + '\n', encoding='utf-8')

def quantile(values, q):
    v = sorted(values)
    p = (len(v) - 1) * q
    lo, hi = math.floor(p), math.ceil(p)
    return v[lo] + (v[hi] - v[lo]) * (p - lo)

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

def check_frame(frame, seq, size):
    assert len(frame) == size + 48 and frame[:8] == b'KIO056F1'
    sequence, length, crc, complement, header_crc = struct.unpack('<QIIII', frame[8:32])
    assert sequence == seq and length == size and complement == (~size & 0xffffffff)
    assert header_crc == zlib.crc32(frame[:28]) and crc == zlib.crc32(frame[32:-16])
    assert frame[-16:-8] == b'IOCOMMIT'
    footer_crc, complement = struct.unpack('<II', frame[-8:])
    assert footer_crc == zlib.crc32(frame[:-16]) and complement == (~footer_crc & 0xffffffff)
    if seq in (1, 256):
        assert frame[32:-16] == independent_payload(seq, size)

policy = json.loads((W / 'policy.json').read_text())
results = json.loads((W / 'model-results.json').read_text())
build = json.loads((W / 'build-provenance.json').read_text())
assert results['complete'] and len(results['cases']) == 12 and not results['failures']
assert sha(W / 'policy.json') == results['policy_sha256']
assert sha(W / 'reservation_probe.rs') == policy['source_sha256'] == build['source_sha256']
assert sha(W / 'reservation-probe.exe') == policy['binary_sha256'] == build['binary_sha256']
old_inventory = json.loads((ROOT / 'benchmarks/publication-056-io-model/fixture-inventory.json').read_text())
old_by_size = {size: next(v['sha256'] for n, v in old_inventory.items() if f'-{size}-journal/journal.bin' in n) for size in (2400, 153600)}
rows, inventory = [], {}
for i, case in enumerate(results['cases']):
    spec, label = case['spec'], case['label']
    assert spec == policy['cases'][i]
    raw = W / 'raw' / (label + '.stdout.json')
    assert sha(raw) == case['stdout_sha256']
    status = json.loads((W / 'raw' / (label + '.status.json')).read_text())
    assert status['spec'] == spec and status['exit_code'] == 0 and not status.get('timeout')
    assert build['compiled_utc'] < policy['declared_utc'] < status['started_utc']
    assert status['free_bytes_before_case'] > policy['free_space_guard_bytes']
    data = json.loads(raw.read_text())
    assert data['mode'] == spec['mode'] and data['payload_bytes'] == spec['payload_bytes']
    assert data['sync_all_each_commit'] and data['bootstrap_sync_before_commits']
    assert data['cold_exact_frame_bytes_verified'] and data['bootstrap_cost_reported_and_charged']
    assert data['no_set_len_or_privileged_valid_data_skip'] and not data['sql_source_receipt_checkpoint_retention_and_crash_qualification']
    samples = data['raw_samples']
    assert len(samples) == 256
    for seq, s in enumerate(samples, 1):
        assert s['seq'] == seq
        assert all(math.isfinite(s[k]) and s[k] >= 0 for k in ['write_ms', 'sync_ms', 'total_ms'])
        assert s['write_ms'] + s['sync_ms'] <= s['total_ms'] + 1e-7
    bootstrap = data['bootstrap']
    assert all(math.isfinite(bootstrap[k]) and bootstrap[k] >= 0 for k in ['create_ms', 'fill_ms', 'sync_ms', 'seek_ms', 'total_ms'])
    assert sum(bootstrap[k] for k in ['create_ms', 'fill_ms', 'sync_ms', 'seek_ms']) <= bootstrap['total_ms'] + 1e-7
    expected_zero_bytes = 256 * (spec['payload_bytes'] + 48) if spec['mode'] == 'reserved' else 0
    assert bootstrap['zero_fill_bytes'] == expected_zero_bytes
    total = sum(s['total_ms'] for s in samples)
    assert math.isfinite(data['setup_and_commit_wall_ms']) and data['setup_and_commit_wall_ms'] >= bootstrap['total_ms'] + total - 1e-7
    timings = [s['total_ms'] for s in samples]
    path = W / 'fixtures' / label / 'journal.bin'
    assert set(path.parent.iterdir()) == {path}
    size = spec['payload_bytes']
    with path.open('rb') as f:
        assert f.read(16) == b'KIO056J1' + struct.pack('<Q', 256)
        for seq in range(1, 257):
            check_frame(f.read(size + 48), seq, size)
        assert not f.read(1)
    digest = sha(path)
    assert digest == old_by_size[size]
    inventory[label + '/journal.bin'] = {'bytes': path.stat().st_size, 'sha256': digest}
    rows.append({**case, 'p50_ms': quantile(timings, .5), 'p99_ms': quantile(timings, .99),
                 'max_ms': max(timings), 'commit_total_ms': total, 'bootstrap': bootstrap,
                 'charged_total_ms': bootstrap['total_ms'] + total,
                 'setup_and_commit_wall_ms': data['setup_and_commit_wall_ms'],
                 'above_500ms': sum(t > 500 for t in timings), 'above_1000ms': sum(t > 1000 for t in timings),
                 'stage_totals_ms': {k: sum(s[k] for s in samples) for k in ['write_ms', 'sync_ms']},
                 'final_file_sha256': digest})
paired = []
metrics = ['p50_ms', 'p99_ms', 'max_ms', 'commit_total_ms', 'charged_total_ms', 'setup_and_commit_wall_ms']
for size in (2400, 153600):
    pairs = []
    for turn in range(3):
        a = next(r for r in rows if r['spec'] == {'round': turn, 'mode': 'growing', 'payload_bytes': size, 'repetitions': 256})
        b = next(r for r in rows if r['spec'] == {'round': turn, 'mode': 'reserved', 'payload_bytes': size, 'repetitions': 256})
        assert a['final_file_sha256'] == b['final_file_sha256']
        pairs.append({'round': turn, 'growing_label': a['label'], 'reserved_label': b['label'],
                      'ratios_reserved_over_growing': {k: b[k] / a[k] for k in metrics}})
    ratios = {k: statistics.median(p['ratios_reserved_over_growing'][k] for p in pairs) for k in metrics}
    checks = {'commit_total_at_most_0_85': ratios['commit_total_ms'] <= .85,
              'bootstrap_plus_commit_at_most_0_90': ratios['charged_total_ms'] <= .90,
              'setup_and_commit_wall_at_most_0_90': ratios['setup_and_commit_wall_ms'] <= .90,
              'commit_p99_at_most_0_95': ratios['p99_ms'] <= .95,
              'commit_p50_guard_at_most_1_05': ratios['p50_ms'] <= 1.05}
    paired.append({'payload_bytes': size, 'pairs': pairs, 'paired_median_ratios': ratios,
                   'hypothesis_checks': checks})
    paired[-1]['medians_by_mode'] = {mode: {**{k: statistics.median(r[k] for r in rows if r['spec']['mode'] == mode and r['spec']['payload_bytes'] == size) for k in metrics},
                                           'bootstrap_total_ms': statistics.median(r['bootstrap']['total_ms'] for r in rows if r['spec']['mode'] == mode and r['spec']['payload_bytes'] == size)} for mode in ['growing', 'reserved']}
baseline = json.loads((W / 'default-engine-baseline.json').read_text())
for n, d in baseline['core_source_sha256'].items():
    assert sha(ROOT / n) == d
for n, d in baseline['baseline_binary_sha256'].items():
    assert sha(ROOT / 'bin' / n) == d
proof = {'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'model_only': True,
         'complete_cases': 12, 'independently_recomputed_samples': 3072,
         'independently_crc_verified_frames': 3072, 'independently_crc_verified_frame_bytes': 239763456,
         'independent_first_and_last_payload_vectors': 24, 'byte_identical_mode_pairs': 6,
         'all_twelve_final_files_match_frozen_056_bytes': True,
         'all_policy_raw_source_binary_hashes_verified': True, 'type7_quantiles_recomputed': True,
         'all_stages_finite_nonnegative_and_bounded': True, 'bootstrap_cost_charged_in_total': True,
         'setup_and_commit_wall_includes_bootstrap_and_equal_encoding': True,
         'all_header_footer_crc_complement_sequence_bounds_and_eof_checks_passed': True,
         'no_timing_ratio_against_historical_056': True, 'every_model_hypothesis_check_passed': all(all(p['hypothesis_checks'].values()) for p in paired),
         'failed_hypothesis_checks': sum(not v for p in paired for v in p['hypothesis_checks'].values()),
         'full_fixture_files': len(inventory), 'full_fixture_bytes': sum(v['bytes'] for v in inventory.values()),
         'sql_or_archive_wal_or_crash_qualification': False, 'default_sql_engine_source_and_bins_unchanged': True,
         'new_engine_release': False, 'trial_promoted': False, 'morning_report_reissued': False, 'paired': paired, 'cases': rows}
save('model-audit.json', proof)
save('fixture-inventory.json', inventory)
print(json.dumps({k: v for k, v in proof.items() if k != 'cases'}))
