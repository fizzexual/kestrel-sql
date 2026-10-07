"""Independently freeze all qualification coverage before performance timers."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
LAB=W/'lab/outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
base=load(W/'baseline.json'); source=load(W/'source-provenance.json'); build=load(LAB/'benchmarks/rust-checks-067.json')
for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d,n
for n,d in source['candidate'].items():assert sha(LAB/n)==d==build['source_sha256'][n],n
for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
for n in base['core_source_sha256']:
    if n not in ['Cargo.toml','Cargo.lock','src/archive.rs']:assert (ROOT/n).read_text(encoding='utf-8')==(LAB/n).read_text(encoding='utf-8'),n
assert build['rust_tests']=={'debug':81,'release':81,'passed':True}
assert all(build[n]=='passed' for n in ['format_check','clippy_warnings_as_errors','feature_clippy_warnings_as_errors'])
q=load(W/'qualification.json'); assert q['complete'] and len(q['commands'])==13
assert all(c['exit']==0 and sha(Path(c['argv'][1]))==c['harness_sha256'] for c in q['commands'])
counts={};total=0
for stem in ['archive','group','cache','medium','dense','sparse','scan']:
    r=load(LAB/f"benchmarks/{stem}-067-{'verification' if stem=='archive' else 'differential'}.json")
    total+=r['queries_checked_against_each_reference']
    if stem!='archive':assert r['complete']
assert total==4000;counts['varied_sql_per_reference']=total
pub=load(LAB/'benchmarks/publication-067-faults.json')
assert len(pub['cut_points'])==56 and len(pub['corruption_cases'])==22
assert all(all(c[n] for n in ['original_receipts_preserved','atomic_rows_and_sum','retry_deduplication_passed','full_scrub_passed']) for c in pub['cut_points'])
assert all(c['rejected'] for c in pub['corruption_cases'])
counts.update(publication_cuts=56,corruptions_rejected=22)
kills=load(LAB/'benchmarks/group-067-recovery.json')
assert not kills['failed_cases'] and len(kills['cycles'])==32
assert all(all(c[n] for n in ['acknowledged_data_present','whole_batches_and_sums','original_receipt_generations_preserved','retry_exactly_once_after_second_reopen','full_scrubs_passed']) for c in kills['cycles'])
counts['concurrent_forced_kills']=32
s=load(LAB/'benchmarks/source-067-faults.json')
assert not s['failed_cases'] and len(s['cases'])==14 and len(s['kill_cycles'])==8
assert all(all(c[n] for n in ['output_and_position_atomic','original_generations_preserved','second_reopen_retry_and_scrubs']) for c in s['cases'])
assert all(all(c[n] for n in ['data_and_position_match','all_acknowledged_generations_preserved','resume_replay_second_reopen_scrub']) for c in s['kill_cycles'])
counts.update(source_faults=14,source_forced_kills=8)
p=load(LAB/'portfolio/source-pipeline-067-results.json')
assert p['exact_sql_cases_against_duckdb']==42 and p['stats']['archive']['rows']==30000 and p['stats']['source']['committed_source_batches']==300
assert all(p[n] for n in ['full_scrub_passed','source_positions_and_data_reopen_together','replay_and_invalid_intervals_passed'])
counts.update(parquet_oracles=42,parquet_rows=30000,parquet_source_intervals=300)
r=load(LAB/'benchmarks/reader-067-verification.json');assert r['complete'] and r['manual_sql_oracles']==104
assert all(r[n] for n in ['fresh_full_scrub_bypasses_handle_reuse','eight_clients_exact_wide_outputs_and_bounded_idle_handles','warm_corruption_rejected_and_idle_handles_invalidated','volatile_reuse_resets_on_reopen_and_known_receipts_survive'])
counts['reader_oracles']=104
wire=load(LAB/'benchmarks/wire-067-audit.json')
assert all(wire[n] for n in ['exact_positive_and_negative_wide_archive_json','exact_wide_ram_json','sparse_bridge_error_continuity_retry_reopen_and_scrub','signed_extrema_and_repeated_sum_avg_outputs'])
byte=load(W/'byte-equivalence.json');assert byte['passed'] and byte['archives_byte_identical'] and byte['released_reopen_candidate_passed']
assert kills['cycles'] and all(Path(c['directory']).is_dir() for c in kills['cycles'])
counts['byte_equivalence_catalogs']=byte['catalogs_compared']
counts['byte_equivalence_segments']=byte['segments_compared']
counts['group_kill_stores_retained']=32
for p in (W/'lab/work/perf-067/candidate').glob('*.exe'):
    assert b'KESTREL_FAULT_POINT' not in p.read_bytes() and b'KESTREL_LIVE_PAUSE' not in p.read_bytes()
morning=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json')
assert sha(ROOT/morning['report_file'])==morning['report_sha256']
a={'checked_utc':datetime.now(timezone.utc).isoformat(),'passed':True,'rust_debug_release_tests_each':81,'counts':counts,
    'source_change_only_bounded_writer_buffer_four_tests_and_version':True,'supported_core_binaries_and_morning_unchanged':True,
    'qualification_sha256':sha(W/'qualification.json'),'byte_equivalence_sha256':sha(W/'byte-equivalence.json'),'rust_build_sha256':sha(LAB/'benchmarks/rust-checks-067.json')}
(W/'qualification-audit.json').write_text(json.dumps(a,indent=2)+'\n',encoding='utf-8');print(json.dumps(a))
