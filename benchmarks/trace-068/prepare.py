"""Diagnostic trace only on the exact released core; no performance candidate."""
from datetime import datetime, timezone
import hashlib, json, shutil
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';LAB=W/'lab/outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert not (W/'policy.json').exists()
base=load(W.parent/'perf-067/baseline.json')
for n,d in base['core_source_sha256'].items():
    assert sha(ROOT/n)==d,n
    p=LAB/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p)
for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
shutil.copy2(W.parent/'perf-067/baseline.json',W/'baseline.json')
p=LAB/'Cargo.toml';s=p.read_text(encoding='utf-8');s=s.replace('fault-injection = []','fault-injection = []\n# Opt-in one-slot publication diagnostics; absent in normal builds.\npublication-trace = []')
s+='\n[[example]]\nname = "trace_probe"\nrequired-features = ["publication-trace"]\n'
p.write_text(s,encoding='utf-8')
for n in ['Cargo.toml','Cargo.lock']:
    p=LAB/n;s=p.read_text(encoding='utf-8');assert s.count('version = "0.3.16"')==1
    p.write_text(s.replace('version = "0.3.16"','version = "0.3.17-dev.68"'),encoding='utf-8')
p=LAB/'src/archive.rs';s=p.read_text(encoding='utf-8')
marker='pub struct Archive {\n';assert s.count(marker)==1
s=s.replace(marker,'''/// Ordered stages in the opt-in publication trace; no trace history is retained.
#[cfg(feature = "publication-trace")]
pub const PUBLICATION_TRACE_STAGES: [&str; 7] = [
    "prepare", "segment_write", "segment_sync", "catalog_encode",
    "catalog_write", "catalog_sync", "catalog_rename",
];
/// One process-local publication attempt. `completed == false` is an unknown
/// durable outcome, not proof that no catalog was published. No-op retries do
/// not replace this record; cold reopen resets it. Bytes describe intended
/// payload/envelope sizes, not independently confirmed persisted bytes.
#[cfg(feature = "publication-trace")]
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
pub struct PublicationTrace {
    pub attempt: u64,
    pub generation: u64,
    pub receipt_base: Option<u64>,
    pub checkpoint: bool,
    pub completed: bool,
    pub rows: usize,
    pub receipts_before: usize,
    pub new_receipts: usize,
    pub removed_segments: usize,
    pub segment_payload_bytes: u64,
    pub catalog_envelope_bytes: u64,
    pub stage_ms: [f64; 7],
}

pub struct Archive {
''')
old='    poisoned: bool,\n    cache: Arc<PageCache>,';assert s.count(old)==1
s=s.replace(old,'    poisoned: bool,\n    #[cfg(feature = "publication-trace")]\n    last_publication_trace: Option<PublicationTrace>,\n    cache: Arc<PageCache>,')
old='            poisoned: false,\n            cache,';assert s.count(old)==1
s=s.replace(old,'            poisoned: false,\n            #[cfg(feature = "publication-trace")]\n            last_publication_trace: None,\n            cache,')
old='            profile.catalog_rename.observe(times[6]);\n        }';assert s.count(old)==1
s=s.replace(old,'''            profile.catalog_rename.observe(times[6]);
            #[cfg(feature = "publication-trace")]
            {
                self.last_publication_trace = Some(PublicationTrace {
                    attempt: profile.attempts,
                    generation,
                    receipt_base,
                    checkpoint,
                    completed: publish.is_ok(),
                    rows,
                    receipts_before: self.catalog.batches.len(),
                    new_receipts: new_records.len(),
                    removed_segments: remove.len(),
                    segment_payload_bytes: (rows * columns.len() * 8) as u64,
                    catalog_envelope_bytes: catalog_bytes,
                    stage_ms: times.map(|t| t.as_secs_f64() * 1000.0),
                });
            }
        }''')
marker='    pub fn stats(&self) -> Result<ArchiveStats> {\n        self.snapshot()?.stats()';assert s.count(marker)==1
s=s.replace(marker,'''    /// Latest publication attempt; process-local and available only with the
    /// diagnostic feature. Failed/early validation calls and no-op retries may
    /// leave the previous record, so compare its attempt/generation explicitly.
    #[cfg(feature = "publication-trace")]
    pub fn last_publication_trace(&self) -> Option<PublicationTrace> {
        self.last_publication_trace
    }

    pub fn stats(&self) -> Result<ArchiveStats> {
        self.snapshot()?.stats()''')
s+='\n'+(W/'trace_tests.rs').read_text(encoding='utf-8');p.write_text(s,encoding='utf-8')
shutil.copy2(W/'trace_probe.rs',LAB/'examples/trace_probe.rs')
names=['build_source_adapter_046.py','archive_verify.py','compare.py','stress_compare.py','host_telemetry.py','group_compare_046.py','group_verify_046.py','cache_verify_046.py','medium_verify_046.py','dense_verify_046.py','sparse_verify_046.py','scan_verify_046.py','publication_faults.py','group_commit_recovery.py','source_faults.py','source_pipeline_demo.py','source_pipeline_probe.rs','wire_046.py','reader_verify_046.py']
(LAB/'benchmarks').mkdir();(LAB/'portfolio').mkdir();(LAB/'bin/baseline-0.3.16').mkdir(parents=True)
for n in base['baseline_binary_sha256']:shutil.copy2(ROOT/'bin'/n,LAB/'bin/baseline-0.3.16'/n)
for n in names:
    s=(ROOT/'benchmarks'/n).read_text(encoding='utf-8')
    if '046' in n:s=s.replace('046','068').replace('0.3.16','0.3.17-dev.68')
    if n=='group_commit_recovery.py':
        s=s.replace('shutil.rmtree(resolved)','# Preserve all successful trace-build recovery fixtures.\n            assert resolved.is_dir()')
        s=s.replace("record = {'group_delay_ms':group_delay","record = {'directory':str(engine.directory.resolve()),'group_delay_ms':group_delay")
    if n=='build_source_adapter_046.py':s=s.replace('kestrel-068-build/release/deps','kestrel-068-trace-build/release/deps')
    (LAB/'benchmarks'/n.replace('_046','_068')).write_text(s,encoding='utf-8')
for n in ['cargo-tests','rust-temp-032']:(W/'lab/work'/n).mkdir(parents=True)
s=(W.parent/'perf-067/qualify.py').read_text(encoding='utf-8').replace('067','068').replace('dev.67','dev.68').replace('81','80')
(W/'qualify.py').write_text(s,encoding='utf-8')
policy={'trial':68,'declared_utc':datetime.now(timezone.utc).isoformat(),'before_diagnostic_timers':True,
    'engine_source':'exact released0.3.16 plus feature-gated one-slot trace; version0.3.17-dev.68',
    'writer_buffer_parser_sdk_fanin_changes_included':False,'supported_default_unchanged':True,
    'qualification':{'trace_debug_release_expected':80,'default_existing_tests_not_repeated':77,
        'strict_clippy_modes':['default','trace','fault-only','trace+fault'],'full_trace_build_suites':13,'retain_group_kill_stores':32,
        'untimed_default_trace_exact_store_comparison':True,'new_feature_tests':3},
    'diagnostics':{'cases':6,'rounds':2,'starting_receipts':[0,50000,99000],'appends':128,'batch_rows':100,
        'one_frozen_trace_executable':True,'no_competitor_or_speedup_comparison':True,'maintenance_trigger':64,'merge_fanin':32,
        'operation_elapsed_includes_original_engine_timings_and_feature_capture':True,
        'getter_event_capture_references_reopen_outside_call_timers':True,'output_buffered_in_process_until_end':True,
        'maintenance_reclaim_timed_separately':True,'slow_event_threshold_ms':500,'stage_sum_tolerance_ms':0.000001,
        'diagnostic_label':'dominant measured stage, not physical-device/antivirus/OS cause or production qualification',
        'no_required_slow_event_count':True,'all_events_and_cases_retained_no_retry_or_threshold_change':True,
        'feature_overhead_unmeasured':True,'promotion_allowed':False},
    'limits':['This computer only; one task-owned local process; no compilation/audit/package/Git during timed calls',
        'Trace record <=192 bytes, no history or disk-format/stats-wire/sync/receipt change',
        'All earlier evidence and morning remain immutable; English only; no deployment/messages to others']}
save(W/'policy.json',policy)
save(W/'source-provenance-before-format.json',{'baseline':base['core_source_sha256'],'candidate':{p.relative_to(LAB).as_posix():sha(p) for p in sorted(LAB.rglob('*.rs'))},
    'cargo_sha256':{n:sha(LAB/n) for n in ['Cargo.toml','Cargo.lock']}})
print(json.dumps({'prepared':True,'trace_tests_expected':80,'diagnostic_cases':6,'free_bytes':shutil.disk_usage(W).free}))
