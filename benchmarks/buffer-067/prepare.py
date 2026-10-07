"""Isolate a bounded writer-only buffer trial from the exact released engine."""
from datetime import datetime, timezone
import hashlib, json, shutil
from pathlib import Path

W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
LAB=W/'lab/outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x): p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert not (W/'policy.json').exists()
base=load(W.parent/'perf-066/baseline.json')
for n,d in base['core_source_sha256'].items():
    assert sha(ROOT/n)==d,n
    dest=LAB/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,dest)
for n,d in base['baseline_binary_sha256'].items(): assert sha(ROOT/'bin'/n)==d,n
shutil.copy2(W.parent/'perf-066/baseline.json',W/'baseline.json')
p=LAB/'src/archive.rs'; text=p.read_text(encoding='utf-8')
text=text.replace('const MAX_METADATA_BYTES: usize = 64 * 1024 * 1024;', 'const MAX_METADATA_BYTES: usize = 64 * 1024 * 1024;\nconst MAX_RETAINED_CATALOG_BYTES: usize = 16 * 1024 * 1024;')
marker='pub struct Archive {\n'
assert text.count(marker)==1
text=text.replace(marker,'''// Writer-local scratch storage; immutable reader snapshots never own this buffer.
#[derive(Default)]
struct CatalogBuffer {
    bytes: Vec<u8>,
}
impl CatalogBuffer {
    fn encode<T: Serialize>(&mut self, value: &T) -> Result<&[u8]> {
        self.bytes.clear();
        serde_json::to_writer(&mut self.bytes, value).map_err(|e| Error::new(e.to_string()))?;
        Ok(&self.bytes)
    }
    fn release(&mut self) {
        self.bytes.clear();
        if self.bytes.capacity() > MAX_RETAINED_CATALOG_BYTES {
            self.bytes = Vec::new();
        }
    }
}

pub struct Archive {
''')
old='    poisoned: bool,\n    cache: Arc<PageCache>,'
assert text.count(old)==1
text=text.replace(old,'    poisoned: bool,\n    catalog_buffer: CatalogBuffer,\n    cache: Arc<PageCache>,')
old='            poisoned: false,\n            cache,'
assert text.count(old)==1
text=text.replace(old,'            poisoned: false,\n            catalog_buffer: CatalogBuffer::default(),\n            cache,')
old='                serde_json::to_vec(&CatalogOutput {'
assert text.count(old)==1
text=text.replace(old,'                self.catalog_buffer.encode(&CatalogOutput {')
old='''                })
                .map_err(|e| Error::new(e.to_string()))
            })?;
            catalog_bytes = bytes.len() as u64 + 16;'''
assert text.count(old)==1
text=text.replace(old,'''                })
            })?;
            catalog_bytes = bytes.len() as u64 + 16;''')
text=text.replace('write_envelope(&mut output, CAT_MAGIC, &bytes)?;', 'write_envelope(&mut output, CAT_MAGIC, bytes)?;')
old='''            Ok(segment_file)
        })();
        {
            let mut profile'''
assert text.count(old)==1
text=text.replace(old,'''            Ok(segment_file)
        })();
        // Also clear partial output after errors; oversized allocations are dropped.
        self.catalog_buffer.release();
        {
            let mut profile''')
text += '\n'+(W/'buffer_tests.rs').read_text(encoding='utf-8')
p.write_text(text,encoding='utf-8')
for n in ['Cargo.toml','Cargo.lock']:
    p=LAB/n;text=p.read_text(encoding='utf-8');assert text.count('version = "0.3.16"')==1
    p.write_text(text.replace('version = "0.3.16"','version = "0.3.17-dev.67"'),encoding='utf-8')
(LAB/'bin/baseline-0.3.16').mkdir(parents=True)
for n in base['baseline_binary_sha256']: shutil.copy2(ROOT/'bin'/n,LAB/'bin/baseline-0.3.16'/n)
(LAB/'benchmarks').mkdir();(LAB/'portfolio').mkdir()
for name in ['rust-temp-032','cargo-tests']: (W/'lab/work'/name).mkdir(parents=True)
names=['checks_046.py','build_source_adapter_046.py','archive_verify.py','compare.py','stress_compare.py','host_telemetry.py','group_compare_046.py','group_verify_046.py','cache_verify_046.py','medium_verify_046.py','dense_verify_046.py','sparse_verify_046.py','scan_verify_046.py','publication_faults.py','group_commit_recovery.py','source_faults.py','source_pipeline_demo.py','source_pipeline_probe.rs','wire_046.py','reader_verify_046.py']
harnesses={}
for name in names:
    target_name=name.replace('_046','_067');text=(ROOT/'benchmarks'/name).read_text(encoding='utf-8')
    if '046' in name: text=text.replace('046','067').replace('0.3.16','0.3.17-dev.67')
    if name=='checks_046.py': text=text.replace('expected=77','expected=81')
    if name=='group_commit_recovery.py':
        assert text.count('shutil.rmtree(resolved)')==1
        text=text.replace('shutil.rmtree(resolved)', '# Trial067 preserves every validated store for independent replay.\n            assert resolved.is_dir()')
        text=text.replace("record = {'group_delay_ms':group_delay", "record = {'directory':str(engine.directory.resolve()),'group_delay_ms':group_delay")
    dest=LAB/'benchmarks'/target_name;dest.write_text(text,encoding='utf-8')
    harnesses[target_name]={'original_sha256':sha(ROOT/'benchmarks'/name),'adapted_sha256':sha(dest)}
text=(W.parent/'perf-064/qualify.py').read_text(encoding='utf-8').replace('064','067').replace('dev.64','dev.67').replace('78','81').replace('"trial": 61','"trial": 67').replace('.read_text()',".read_text(encoding='utf-8')")
(W/'qualify.py').write_text(text,encoding='utf-8')
shutil.copy2(W.parent/'perf-064/native_publication_probe.rs',W/'native_publication_probe.rs')
shutil.copy2(W.parent/'perf-065/process_memory.py',W/'process_memory.py')
policy={'trial':67,'declared_utc':datetime.now(timezone.utc).isoformat(),'before_timing':True,'baseline':'0.3.16','candidate':'0.3.17-dev.67',
    'core_change':'Writer-local reusable JSON Vec, retain <=16 MiB capacity, clear/drop after success or error; no snapshot ownership',
    'based_on_released_core':True,'parser_sdk_fanin_changes_included':False,'default_engine_unchanged':True,'rust_tests_each_mode_expected':81,
    'native':{'rounds':6,'variants':['baseline_a','baseline_b','candidate'],'same_exact_released_probe_path_for_both_baselines':True,
        'starting_receipt_counts':[0,50000,99000],'appends':256,'batch_rows':100,'maintenance_trigger_small_runs':64,'merge_fanin':32,
        'order':'Latin square by round plus size index; each label occupies every position twice',
        'primary_comparator':'candidate/baseline_a','identity_comparator':'baseline_b/baseline_a','candidate_over_baseline_b_diagnostic_only':True,
        'primary_goals_large_histories':{'catalog_encode_stage_total_ratio_max':.85,'append_plus_maintenance_ratio_max':.97},
        'small_history_total_guard_max':1.05,
        'guards_all_histories':{'append_p50_ratio_max':1.05,'append_p99_ratio_max':1.10,'append_max_ratio_max':1.10,'reopen_ratio_max':1.10,'peak_working_set_ratio_max':1.15,'peak_commit_ratio_max':1.15},
        'identity_calibration_ratio_interval':[.90,1.10],
        'identity_metrics':['append_plus_maintenance_ms','catalog_encode_ms','p50_ms','p99_ms','max_ms','reopen_ms','peak_working_set_bytes','peak_commit_bytes'],
        'goal_rationale':'066 fixed-input reuse predicts 21-23% encoding savings; 064 released99K encoding is18.33% of summed stages, so total target is3%, not10%. New append inputs/cold allocation/memory must qualify separately.',
        'advance':'Service only if all native goals, guards, correctness and A/A calibration pass; keep every outcome otherwise',
        'setup_checks_stats_reclaim_and_cold_reopen_outside_append_timers':True,'maintenance_charged_in_total':True},
    'qualification':['81 debug/release tests, format and strict default/fault Clippy','13 full correctness/recovery suites','all32 group-kill stores retained','byte-for-byte cross-binary catalogs and segments with checkpoints/deltas/maintenance, cold released reopen and receipt retry'],
    'limits':['this computer only; no build/audit/package/Git during timed workloads','no file-format, serializer order, sync, budget, receipt or supported promotion change','English only; frozen morning report and all older evidence unchanged']}
save(W/'policy.json',policy)
save(W/'source-provenance-before-format.json',{'baseline':base['core_source_sha256'],'candidate':{n:sha(LAB/n) for n in base['core_source_sha256']},'harnesses':harnesses,'added_tests':4})
print(json.dumps({'prepared':True,'tests_expected':81,'native_cases_planned':54,'free_bytes':shutil.disk_usage(W).free}))
