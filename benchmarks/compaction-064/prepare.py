"""Derive compaction-only dev.64 from released 0.3.16; freeze all policies first."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'
LAB=W/'lab/outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
assert not (W/'policy.json').exists()
base=load(W.parent/'perf-063/baseline.json')
for n,d in base['core_source_sha256'].items():
    assert sha(ROOT/n)==d,n
    p=LAB/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,p)
for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
shutil.copy2(W.parent/'perf-063/baseline.json',W/'baseline.json')
p=LAB/'src/archive.rs';text=p.read_text()
assert text.count('if selected.len() == 32 {')==1 and text.count('Merge up to 32 small runs')==1
p.write_text(text.replace('if selected.len() == 32 {','if selected.len() == 64 {').replace('Merge up to 32 small runs','Merge up to 64 small runs'),encoding='utf-8')
p=LAB/'tests/archive.rs';text=p.read_text()
for old,new in [('assert_eq!(archive.compact_small().unwrap(), 31);','assert_eq!(archive.compact_small().unwrap(), 63);'),('assert_eq!(archive.stats().unwrap().retained_stream_handles, 96);','assert_eq!(archive.stats().unwrap().retained_stream_handles, 64);'),('assert_eq!(archive.stats().unwrap().retained_stream_handles, 99);','assert_eq!(archive.stats().unwrap().retained_stream_handles, 67);')]:
    assert text.count(old)==1,old
    text=text.replace(old,new)
p.write_text(text,encoding='utf-8')
shutil.copy2(W/'fanin_test.rs',LAB/'tests/compaction_fanin.rs')
shutil.copy2(W/'fanin_seed_probe.rs',LAB/'examples/fanin_seed_probe.rs')
for n in ['Cargo.toml','Cargo.lock']:
    p=LAB/n;text=p.read_text();assert text.count('version = "0.3.16"')==1
    p.write_text(text.replace('version = "0.3.16"','version = "0.3.17-dev.64"'),encoding='utf-8')
(LAB/'bin/baseline-0.3.16').mkdir(parents=True)
for n in base['baseline_binary_sha256']:shutil.copy2(ROOT/'bin'/n,LAB/'bin/baseline-0.3.16'/n)
(LAB/'benchmarks').mkdir();(LAB/'portfolio').mkdir()
for name in ['rust-temp-032','cargo-tests']:(W/'lab/work'/name).mkdir(parents=True)
names=['checks_046.py','build_source_adapter_046.py','archive_verify.py','compare.py','stress_compare.py','host_telemetry.py','group_compare_046.py','group_verify_046.py','cache_verify_046.py','medium_verify_046.py','dense_verify_046.py','sparse_verify_046.py','scan_verify_046.py','publication_faults.py','group_commit_recovery.py','source_faults.py','source_pipeline_demo.py','source_pipeline_probe.rs','wire_046.py','reader_verify_046.py']
harnesses={}
for name in names:
    target_name=name.replace('_046','_064')
    text=(ROOT/'benchmarks'/name).read_text()
    if '046' in name:text=text.replace('046','064').replace('0.3.16','0.3.17-dev.64')
    if name=='checks_046.py':
        text=text.replace('expected=77','expected=78')
        text=text.replace("'receipt-seed':'receipt_seed_sha256'","'receipt-seed':'receipt_seed_sha256','fanin-seed-probe':'fanin_seed_sha256'")
        text=text.replace("'publication-probe','receipt-seed']","'publication-probe','receipt-seed','fanin-seed-probe']")
    dest=LAB/'benchmarks'/target_name;dest.write_text(text,encoding='utf-8')
    harnesses[target_name]={'original_sha256':sha(ROOT/'benchmarks'/name),'adapted_sha256':sha(dest)}
qualify=(W.parent/'perf-061/qualify.py').read_text().replace('061','064').replace('dev.61','dev.64').replace('77','78')
(W/'qualify.py').write_text(qualify,encoding='utf-8')
policy={'trial':64,'declared_utc':datetime.now(timezone.utc).isoformat(),'before_timing':True,'baseline':'0.3.16','candidate':'0.3.17-dev.64',
    'core_change':'compact_small fan-in cap 32 to 64; same 65536-row/64MiB ceilings and live threshold64',
    'based_on_released_core':True,'parser_and_sdk_changes_included':False,'default_engine_unchanged':True,'rust_tests_each_mode_expected':78,
    'native':{'rounds':3,'variants':['baseline_a','baseline_b','candidate'],'same_exact_released_probe_path_for_both_baselines':True,
        'starting_receipt_counts':[0,50000,99000],'appends':256,'batch_rows':100,'maintenance_every_appends':32,
        'order':'Latin square by round plus size index; all labels occupy every position once',
        'primary_comparator':'candidate/baseline_a','identity_comparator':'baseline_b/baseline_a',
        'candidate_over_baseline_b_diagnostic_only':True,'primary_goals':{'append_plus_maintenance_ratio_max':.90,'append_p99_ratio_max':.90},
        'guards':{'append_p50_ratio_max':1.05,'append_max_ratio_max':1.10,'reopen_ratio_max':1.10},
        'identity_calibration_ratio_interval':[.90,1.10],
        'advance':'service only if all predeclared native goals, guards and identity checks pass; retain all outcomes otherwise',
        'setup_checks_stats_reclaim_and_cold_reopen_outside_append_timers':True,'maintenance_timers_charged_separately_to_primary_total':True},
    'qualification':['78 debug/release tests, format and strict default/fault Clippy','13 full correctness/recovery suites adapted from061',
        'additional14 publication cuts over a direct64-run store with default cold reopen/receipts/sums/CRC'],
    'limits':['this computer only; no build/audit/package/Git during timed workloads','no source-format/durability change or supported promotion',
        'shared near-full Windows host; no causal p99, physical power loss or production claims','all older results and morning report preserved; English only']}
save(W/'policy.json',policy)
candidate_paths=sorted({*base['core_source_sha256'],'tests/compaction_fanin.rs','examples/fanin_seed_probe.rs'})
save(W/'source-provenance.json',{'baseline':base['core_source_sha256'],'candidate':{n:sha(LAB/n) for n in candidate_paths},'harnesses':harnesses,
    'known_test_changes':'retirement/handle expectations for wider merge plus independent64-run/row-ceiling/pinned/receipt test'})
print(json.dumps({'prepared':True,'candidate':policy['candidate'],'tests_expected':78,'timed_cases_planned':27,'default_unchanged':True}))
