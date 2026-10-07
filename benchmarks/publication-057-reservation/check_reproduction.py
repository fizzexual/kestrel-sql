from pathlib import Path
import datetime, hashlib, json, subprocess

W = Path(__file__).resolve().parent
R = W.parent / 'perf-057-cargo-reproduction-check'

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

proof = json.loads((R / 'build-provenance.json').read_text())
original = json.loads((W / 'build-provenance.json').read_text())
assert proof['source_sha256'] == original['source_sha256'] == sha(R / 'reservation_probe.rs')
assert proof['binary_sha256'] == sha(R / 'reservation-probe.exe')
assert proof['binary_sha256'] != original['binary_sha256']
old = json.loads((W.parent / 'perf-056/fixture-inventory.json').read_text())
expected = next(v['sha256'] for n, v in old.items() if '-2400-journal/journal.bin' in n)
cases = []
for mode in ['growing', 'reserved']:
    store = R / ('fixture-' + mode)
    assert not store.exists()
    raw, err = R / (mode + '.stdout.json'), R / (mode + '.stderr.txt')
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with raw.open('w') as out, err.open('w') as errors:
        status = subprocess.run([str(R / 'reservation-probe.exe'), str(store), mode, '2400', '256'], stdout=out, stderr=errors, timeout=300).returncode
    record = {'mode': mode, 'exit_code': status, 'started_utc': started,
              'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'stdout_sha256': sha(raw), 'stderr_sha256': sha(err), 'included_in_competitive_timings': False}
    (R / (mode + '.status.json')).write_text(json.dumps(record, indent=2) + '\n')
    assert status == 0
    j = json.loads(raw.read_text())
    assert j['cold_exact_frame_bytes_verified'] and j['sync_all_each_commit'] and j['bootstrap_sync_before_commits']
    assert j['mode'] == mode and len(j['raw_samples']) == 256
    assert sha(store / 'journal.bin') == expected
    record.update(final_file_sha256=expected, final_bytes=(store / 'journal.bin').stat().st_size)
    cases.append(record)
checked = {'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'independent_cargo_build_and_execution_passed': True, 'strict_warnings_passed': True,
           'same_frozen_probe_source': True, 'different_independent_binary': True,
           'original_binary_sha256': original['binary_sha256'], 'independent_binary_sha256': proof['binary_sha256'],
           'two_small_volume_modes_checked': True, 'samples_excluded_from_competitive_results': 512,
           'complete_files_byte_identical_to_frozen_056': True, 'full_fixture_bytes': sum(c['final_bytes'] for c in cases),
           'no_full_independent_performance_repeat': True, 'no_sql_or_crash_qualification': True,
           'no_build_overlapped_native_execution': True, 'cases': cases}
(W / 'cargo-reproduction-check.json').write_text(json.dumps(checked, indent=2) + '\n')
print(json.dumps(checked))
