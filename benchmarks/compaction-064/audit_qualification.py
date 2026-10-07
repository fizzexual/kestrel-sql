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
base=load(W/'baseline.json'); source=load(W/'source-provenance.json'); build=load(LAB/'benchmarks/rust-checks-064.json')
for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d,n
for n,d in source['candidate'].items():assert sha(LAB/n)==d==build['source_sha256'][n],n
for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
before=(ROOT/'src/archive.rs').read_text(encoding='utf-8'); after=(LAB/'src/archive.rs').read_text(encoding='utf-8')
assert before.replace('if selected.len() == 32 {','if selected.len() == 64 {').replace('Merge up to 32 small runs','Merge up to 64 small runs')==after
for n in base['core_source_sha256']:
    if n not in ['Cargo.toml','Cargo.lock','src/archive.rs','tests/archive.rs']:assert (ROOT/n).read_text(encoding='utf-8')==(LAB/n).read_text(encoding='utf-8'),n
assert build['rust_tests']=={'debug':78,'release':78,'passed':True}
assert all(build[n]=='passed' for n in ['format_check','clippy_warnings_as_errors','feature_clippy_warnings_as_errors'])
q=load(W/'qualification.json'); assert q['complete'] and len(q['commands'])==13
assert all(c['exit']==0 and sha(Path(c['argv'][1]))==c['harness_sha256'] for c in q['commands'])
counts={};total=0
for stem in ['archive','group','cache','medium','dense','sparse','scan']:
    r=load(LAB/f"benchmarks/{stem}-064-{'verification' if stem=='archive' else 'differential'}.json")
    total+=r['queries_checked_against_each_reference']
    if stem!='archive':assert r['complete']
assert total==4000;counts['varied_sql_per_reference']=total
pub=load(LAB/'benchmarks/publication-064-faults.json')
assert len(pub['cut_points'])==56 and len(pub['corruption_cases'])==22
assert all(all(c[n] for n in ['original_receipts_preserved','atomic_rows_and_sum','retry_deduplication_passed','full_scrub_passed']) for c in pub['cut_points'])
assert all(c['rejected'] for c in pub['corruption_cases'])
counts.update(publication_cuts=56,corruptions_rejected=22)
kills=load(LAB/'benchmarks/group-064-recovery.json')
assert not kills['failed_cases'] and len(kills['cycles'])==32
assert all(all(c[n] for n in ['acknowledged_data_present','whole_batches_and_sums','original_receipt_generations_preserved','retry_exactly_once_after_second_reopen','full_scrubs_passed']) for c in kills['cycles'])
counts['concurrent_forced_kills']=32
s=load(LAB/'benchmarks/source-064-faults.json')
assert not s['failed_cases'] and len(s['cases'])==14 and len(s['kill_cycles'])==8
assert all(all(c[n] for n in ['output_and_position_atomic','original_generations_preserved','second_reopen_retry_and_scrubs']) for c in s['cases'])
assert all(all(c[n] for n in ['data_and_position_match','all_acknowledged_generations_preserved','resume_replay_second_reopen_scrub']) for c in s['kill_cycles'])
counts.update(source_faults=14,source_forced_kills=8)
p=load(LAB/'portfolio/source-pipeline-064-results.json')
assert p['exact_sql_cases_against_duckdb']==42 and p['stats']['archive']['rows']==30000 and p['stats']['source']['committed_source_batches']==300
assert all(p[n] for n in ['full_scrub_passed','source_positions_and_data_reopen_together','replay_and_invalid_intervals_passed'])
counts.update(parquet_oracles=42,parquet_rows=30000,parquet_source_intervals=300)
r=load(LAB/'benchmarks/reader-064-verification.json');assert r['complete'] and r['manual_sql_oracles']==104
assert all(r[n] for n in ['fresh_full_scrub_bypasses_handle_reuse','eight_clients_exact_wide_outputs_and_bounded_idle_handles','warm_corruption_rejected_and_idle_handles_invalidated','volatile_reuse_resets_on_reopen_and_known_receipts_survive'])
counts['reader_oracles']=104
wire=load(LAB/'benchmarks/wire-064-audit.json')
assert all(wire[n] for n in ['exact_positive_and_negative_wide_archive_json','exact_wide_ram_json','sparse_bridge_error_continuity_retry_reopen_and_scrub','signed_extrema_and_repeated_sum_avg_outputs'])
wide=load(W/'wide-faults.json');assert wide['complete'] and len(wide['cases'])==14 and not wide['failed_cases']
for i,c in enumerate(wide['cases']):
    assert c['point']==['segment_partial','segment_written','segment_synced','catalog_partial','catalog_written','catalog_synced','catalog_published'][i//2]
    assert c['mode']==['exit','io_error'][i%2]
    assert c['returncode']==(86 if c['mode']=='exit' else 87)
    assert c['generation']==(65 if c['point']=='catalog_published' else 64)
    assert c['segments']==(1 if c['point']=='catalog_published' else 64)
    assert all(c[n] for n in ['original64_receipts_preserved','rows_sums_group_and_range_oracles_passed','full_crc_passed'])
counts['wide64_publication_cuts']=14
for p in (W/'lab/work/perf-064/candidate').glob('*.exe'):
    assert b'KESTREL_FAULT_POINT' not in p.read_bytes() and b'KESTREL_LIVE_PAUSE' not in p.read_bytes()
morning=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json')
assert sha(ROOT/morning['report_file'])==morning['report_sha256']
a={'checked_utc':datetime.now(timezone.utc).isoformat(),'passed':True,'rust_debug_release_tests_each':78,'counts':counts,
    'source_change_only_bounded_compaction_and_explicit_tests_version':True,'supported_core_binaries_and_morning_unchanged':True,
    'qualification_sha256':sha(W/'qualification.json'),'wide_faults_sha256':sha(W/'wide-faults.json'),'rust_build_sha256':sha(LAB/'benchmarks/rust-checks-064.json')}
(W/'qualification-audit.json').write_text(json.dumps(a,indent=2)+'\n',encoding='utf-8');print(json.dumps(a))
