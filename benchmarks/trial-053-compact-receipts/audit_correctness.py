from pathlib import Path
import datetime, hashlib, json, re

w = Path(__file__).resolve().parent
root = w.parents[1] / 'outputs/kestrel-sql'
def read(name):
    return json.loads((w / name).read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()
gates = read('correctness-gates.json')
expected = {'semantic-recovery', 'cross-candidate', 'compatibility', 'publication-cuts', 'source-cuts-kills',
            'concurrent-kills', 'general-sql', 'group', 'cache', 'medium', 'dense', 'sparse', 'scan', 'reader'}
assert gates['complete'] and len(gates['steps']) == 14
assert {s['name'] for s in gates['steps']} == expected
for s in gates['steps']:
    assert s['returncode'] == 0 and sha(w / (s['name'] + '.txt')) == s['log_sha256']
build = read('build-provenance.json')
assert len(build['source']) == 28 and len(build['binaries']) == 10
for n,d in build['source'].items(): assert sha(w / 'candidate' / n) == d
for n,d in build['binaries'].items(): assert sha(w / 'bin' / n) == d
assert sha(w / 'bin/source-pipeline.pdb') == build['linker_pdb_sha256']
assert sha(root / 'benchmarks/source_pipeline_probe.rs') == build['adapter_source_sha256']
base = read('baseline.json')
for n,d in base['core_source_sha256'].items(): assert sha(root / n) == d
for n,d in base['baseline_binary_sha256'].items(): assert sha(root / 'bin' / n) == d
old = json.loads((w.parent / 'perf-050/build-provenance.json').read_text(encoding='utf-8'))
changes = sorted(n for n,d in build['source'].items() if old['source'].get(n) != d)
assert changes == sorted(read('trial-policy.json')['candidate_changes'])
for n,d in old['source'].items(): assert sha(w.parent / 'perf-050/candidate' / n) == d
for n,d in old['binaries'].items(): assert sha(w.parent / 'perf-050/bin' / n) == d
testlog = (w / 'release-tests.txt').read_text(encoding='utf-8')
tests = sum(map(int,re.findall(r'test result: ok\. (\d+) passed; 0 failed;',testlog)))
assert tests == 88 and build['release_tests'] == 88 and not build['debug_suite_run']
assert 'error:' in (w / 'test-first-compile-failure/release-tests.txt').read_text(encoding='utf-8')
assert 'file.set_len' not in (w / 'candidate/src/archive.rs').read_text(encoding='utf-8')
semantic = read('semantic-recovery.json')
assert semantic['passed'] and semantic['original_failing_fixture_unchanged'] and len(semantic['cases']) == 2
assert semantic['cases'][0]['rejected_before_data_access'] and semantic['cases'][0]['fixture_files_unchanged']
assert semantic['cases'][1]['distinct_generation_mixed_legacy_upgrade_passed'] and semantic['cases'][1]['original_receipt_generation_preserved']
cross = read('cross-candidate.json')
assert cross['passed'] and len(cross['cases']) == 3 and not cross['downgrade_supported']
for c in cross['cases']:
    assert all(c[k] for k in ['cat5_to_cat6_read_append_and_cold_retry','old_frames_unchanged','source_positions_and_original_generations_preserved','old_writer_and_source_adapter_reject_cat6_without_changes'])
compat = read('compatibility.json')
assert compat['passed'] and {c['legacy_format'] for c in compat['cases']} == {2,3,4}
for c in compat['cases']:
    assert all(c[k] for k in ['frozen_old_reader_accepted_legacy','trial_read_and_upgrade','old_data_bytes_unchanged','old_writer_rejected_upgrade_without_file_changes'])
pub = read('publication-053-faults.json')
assert len(pub['cut_points']) == 64 and len(pub['corruption_cases']) == 22
for c in pub['cut_points']:
    assert all(c[k] for k in ['original_receipts_preserved','atomic_rows_and_sum','retry_deduplication_passed','full_scrub_passed'])
assert all(c['rejected'] for c in pub['corruption_cases'])
source = read('source-053-faults.json')
assert len(source['cases']) == 16 and len(source['kill_cycles']) == 8 and not source['failed_cases']
for c in source['cases']: assert all(c[k] for k in ['output_and_position_atomic','original_generations_preserved','second_reopen_retry_and_scrubs'])
for c in source['kill_cycles']: assert all(c[k] for k in ['data_and_position_match','all_acknowledged_generations_preserved','resume_replay_second_reopen_scrub'])
concurrent = read('group-053-recovery.json')
assert len(concurrent['cycles']) == 32 and not concurrent['failed_cases']
sql_count = read('archive-053-verification.json')['queries_checked_against_each_reference']
for n in ['group','cache','medium','dense','sparse','scan']:
    sql_count += read(n + '-053-differential.json')['queries_checked_against_each_reference']
assert sql_count == 4000
reader = read('reader-053-verification.json')
assert reader['complete'] and reader['manual_sql_oracles'] == len(reader['cases']) == 104
assert all(c.get('exact_python_integer_oracle', True) for c in reader['cases'])
assert all(reader[k] for k in ['fresh_full_scrub_bypasses_handle_reuse','eight_clients_exact_wide_outputs_and_bounded_idle_handles','warm_corruption_rejected_and_idle_handles_invalidated','volatile_reuse_resets_on_reopen_and_known_receipts_survive'])
proof = {'audited_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'trial':'053 isolated compact CAT6, not a supported release', 'release_rust_tests':tests,
    'debug_suite_run':False, 'debug_limitation':'Insufficient local disk space; release suite only in this trial',
    '28_source_and_10_executable_hashes_verified':True, 'changed_source_files_from_050':changes,
    'default_core_and_supported_binaries_unchanged':True, 'rejected_052_not_carried':True,
    'all_14_external_gates_passed':True, 'restore_alias_rejected_before_data_access':True,
    'valid_legacy_upgrade_and_original_receipt_preserved':True, 'cat2_3_4_migrations':3,
    'cat5_to_cat6_migrations':3, 'downgrade_supported':False,
    'publication_cuts':64,'corruptions':22,'source_faults':16,'source_kills':8,'concurrent_kills':32,
    'sql_queries_against_each_duckdb_and_sqlite':4000,'manual_reader_oracles':104,
    'preserved_failures':'First new-test macro compilation failure; executable-count assertion incorrectly included linker PDB, corrected without engine mutation or timed work',
    'raw_description_notice':'Source-fault raw report retains older seven-cut wording; actual case list is eight boundaries, sixteen cases. No raw report rewritten.',
    'fresh_performance_measured':False,'release_gates_completed':False,'trial_promoted':False,'morning_report_issued':False}
(w / 'correctness-audit.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
