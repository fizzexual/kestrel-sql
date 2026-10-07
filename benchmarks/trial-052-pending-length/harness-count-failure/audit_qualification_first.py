from pathlib import Path
import datetime, hashlib, itertools, json, re
W = Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
p = json.loads((W / 'build-provenance.json').read_text())
for name, digest in p['source'].items():
    assert sha(W / 'candidate' / name) == digest
for name, digest in p['binaries'].items():
    assert sha(W / 'bin' / name) == digest
counts = [int(n) for n in re.findall(r'test result: ok\. (\d+) passed', (W / 'release-tests.txt').read_text())]
assert sum(counts) == 85
f = json.loads((W / 'publication-052-faults.json').read_text())
assert f['binary_sha256'] == p['binaries']['kestrel-stress.exe']
assert f['sql_binary_sha256'] == p['binaries']['kestrel.exe']
assert f['fault_driver_sha256'] == p['binaries']['publication_fault_probe.exe']
points = ['bundle_sized', 'catalog_partial', 'metadata_written', 'segment_partial', 'catalog_written',
          'catalog_synced', 'catalog_published', 'bundle_retained', 'memory_published']
scenarios = ['append_delta', 'append_checkpoint', 'compact_delta', 'compact_checkpoint']
expected = set(itertools.product(scenarios, points, ['exit', 'io_error']))
actual = [(c['scenario'], c['point'], c['mode']) for c in f['cut_points']]
assert len(actual) == 72 and set(actual) == expected and len(set(actual)) == 72
for c in f['cut_points']:
    assert c['returncode'] == (86 if c['mode'] == 'exit' else 87)
    assert all(c[k] for k in ['original_receipts_preserved', 'atomic_rows_and_sum', 'retry_deduplication_passed', 'full_scrub_passed'])
    assert c['writer_poison_and_pinned_read_passed'] == (c['mode'] == 'io_error')
assert len(f['corruption_cases']) == 22 and all(c['rejected'] for c in f['corruption_cases'])
g = json.loads((W / 'group-052-recovery.json').read_text())
assert len(g['cases']) == 32
for c in g['cases']:
    assert all(c[k] for k in ['acknowledged_data_present', 'whole_batches_and_sums',
                              'original_receipt_generations_preserved', 'retry_exactly_once_after_second_reopen', 'full_scrubs_passed'])
out = {'audited_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'release_tests': 85,
       'debug_tests_run': False, 'publication_cuts': 72, 'new_bundle_sized_cuts': 8, 'corruptions': 22,
       'concurrent_forced_kills': 32, 'all_source_binary_hashes_counts_and_case_flags_verified': True,
       'harness_failure_preserved': 'harness-count-failure: all cases passed, final obsolete 64-count assertion failed; corrected to scenarios*points*2 and independently audited without repeating completed engine cases',
       'original_harness_exit_code': 1, 'corrected_coverage_audit_passed': True,
       'fault_model': 'Process termination and injected OS I/O error on live filesystem, not physical power failure or actual device exhaustion',
       'full_050_external_suite_repeated': False, 'default_engine_changed': False, 'release_ready': False}
(W / 'qualification-audit.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out))
