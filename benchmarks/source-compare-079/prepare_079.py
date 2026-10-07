"""Prepare a fresh, predeclared 076/076/078 comparison; never reuse timers."""
import ast, hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path

BASE=Path(__file__).resolve().parent; W=BASE/'perf-079'; PREV=BASE/'perf-077'
OLD=BASE/'perf-076'; NEW=BASE/'perf-078'; ROOT=BASE.parent/'outputs/kestrel-sql'
assert not W.exists(); W.mkdir()
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v): p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def now(): return datetime.now(timezone.utc).isoformat()
helpers=['catalog_oracle.py','page_oracle.py','hybrid_oracle.py','process_memory.py','canonical_audit.py','order_plan.py','check_processes.ps1']
for name in helpers: shutil.copyfile(PREV/name,W/name)
for src,dst in [(OLD/'model',W/'control-model'),(NEW/'model',W/'candidate-model'),(NEW/'locked-registry-crates',W/'locked-registry-crates')]: shutil.copytree(src,dst)
(W/'bin').mkdir()
shutil.copyfile(OLD/'bin/recovery-model.exe',W/'bin/control-076.exe')
shutil.copyfile(NEW/'bin/source-state-model.exe',W/'bin/candidate-078.exe')
(W/'prerequisites').mkdir(); proofs={}
for prefix,source,names in [
    ('076',OLD,['build-proof.json','source-finalization.json','qualification-policy.json','qualification-results.json','publication-byte-equivalence.json']),
    ('078',NEW,['build-proof.json','source-finalization.json','qualification-policy.json','qualification-results.json','publication-byte-equivalence.json','qualification-audit.json']),
    ('077',PREV,['policy.json','model-audit.json','bottleneck-profile.json']),
    ('078-final',BASE/'perf-078-finalization',['git-publication-check.json'])]:
    for name in names:
        src=source/name
        # File names are checked before assembly; do not synthesize missing evidence.
        assert src.is_file(),src
        dst=W/'prerequisites'/f'{prefix}-{name}'; shutil.copyfile(src,dst)
        proofs[dst.relative_to(W).as_posix()]={'source':str(src),'sha256':sha(dst)}
inputs=load(PREV/'input-provenance.json'); (W/'inputs').mkdir()
for item in inputs['inputs']:
    src=Path(item['path']); dst=W/'inputs'/src.name
    assert sha(src)==item['sha256']; shutil.copyfile(src,dst)
    item.update(source_077=str(src),path=str(dst)); assert sha(dst)==item['sha256']
inputs.update(copied_utc=now(),all_original_068_checkpoint_bytes_unchanged=True)
save(W/'input-provenance.json',inputs)
baseline=load(NEW/'baseline.json'); baseline.update(prepared_utc=now(),repository_commit_before_079='78762a9424450b3610e5137694d7f5ae52fad843')
save(W/'baseline.json',baseline); shutil.copyfile(ROOT/'MANIFEST.sha256',W/'repository-manifest-pre-079.sha256')
for n,d in baseline['core_source_sha256'].items(): assert sha(ROOT/n)==d,n
for n,d in baseline['baseline_binary_sha256'].items(): assert sha(ROOT/'bin'/n)==d,n
builds={}
for label,source,model,binary in [('control_076',OLD,'control-model','control-076.exe'),('candidate_078',NEW,'candidate-model','candidate-078.exe')]:
    proof=load(source/'build-proof.json'); assert proof['complete'] and proof['format_and_strict_clippy_passed']
    for n,d in proof['source_sha256'].items(): assert sha(W/model/n)==d,n
    assert sha(W/'bin'/binary)==proof['binary_sha256']
    builds[label]={'binary':f'bin/{binary}','source_directory':model,'binary_sha256':proof['binary_sha256'],'source_sha256':proof['source_sha256'],'previous_native_test_counts':proof['counts']}
assert builds['control_076']['binary_sha256']=='e9ef281a10ce46370b169ae8a6a98632837820b0fcc081c969fabd60f88ab37b'
assert builds['candidate_078']['binary_sha256']=='f22b8fd8bb4e798d3aa69cc54f49a0d6fc757659c729a0aefafc786ffda54f6a'
save(W/'binary-provenance.json',{'complete':True,'prepared_utc':now(),'reused_unchanged_binaries_no_rebuild':True,'variants':{'baseline_a':'control_076','baseline_b':'control_076','hybrid':'candidate_078'},'builds':builds,'prerequisite_proofs':proofs,'no_engine_change':True})

# Keep the logical full-file decoder and all workload invariants byte-identical.
s=(PREV/'audit_model.py').read_text(encoding='utf-8')
s=s.replace("'source_validation_full_clone_charged_in_all_modes',",'')
needle="    key=(seed,mode)"
assert s.count(needle)==1
s=s.replace(needle,"    assert x['source_validation_full_clone_charged_in_all_modes']==(spec['variant']!='hybrid')\n    if spec['variant']=='hybrid':\n        assert x['source_validation_is_fully_charged'] and x['hybrid_source_validation']=='validated_incremental_state078'\n"+needle)
needle="    path_metrics={}"
s=s.replace(needle,"    ordinary=[s['outer_ms'] for s in x['samples'] if not s['source_interval']]\n"+needle)
needle="    cases.append({**path_metrics,"
s=s.replace(needle,"    cases.append({'ordinary_p50_ms':quantile(ordinary,.5),'ordinary_p99_ms':quantile(ordinary,.99),'ordinary_max_ms':max(ordinary),'source_p50_ms':quantile(source,.5),**path_metrics,")
s=s.replace("metrics=['total_ms'","metrics=['ordinary_p50_ms','ordinary_p99_ms','ordinary_max_ms','source_p50_ms','total_ms'")
s=s.replace("    for metric,limit in (lim['large_anchor_goals'] if seed else lim['small_anchor_guards']).items():add('goal' if seed else 'guard',seed,metric,c[metric],limit)","    for metric,limit in lim['all_anchor_guards'].items():add('guard',seed,metric,c[metric],limit)\n    if seed:\n        for metric,limit in lim['large_publication_goals'].items():add('goal',seed,metric,c[metric],limit)")
s=s.replace('large_anchor_recovery_goals_calibrated_and_passed','large_source_publication_goals_calibrated_and_passed')
s=s.replace('no_fresh_cuts_076_prerequisite_retained','no_fresh_cuts_078_prerequisite_retained')
s=s.replace("'calibrated_anchor_goals'","'calibrated_publication_goals'")
s=s.replace("'previous_075_adoption_failures_unchanged_and_not_superseded':True,","'previous_075_adoption_failures_unchanged_and_not_superseded':True,'previous_077_failures_unchanged_and_not_superseded':True,")
(W/'audit_model.py').write_text(s,encoding='utf-8')
s=(PREV/'qualify_integration.py').read_text(encoding='utf-8')
s=s.replace("'control_075':W/'bin/control-075.exe','candidate_076':W/'bin/candidate-076.exe'","'control_076':W/'bin/control-076.exe','candidate_078':W/'bin/candidate-078.exe'")
needle="        files,reachable=ns['full_canonical_audit']"
s=s.replace(needle,"        assert x['source_validation_full_clone_charged_in_all_modes']==(variant=='control_076')\n        if variant=='candidate_078':assert x['source_validation_is_fully_charged'] and x['hybrid_source_validation']=='validated_incremental_state078'\n"+needle)
s=s.replace("'protocol_074_tests_kills_not_rerun':True","'078_57_native_tests_each_15_errors_15_kills_30_corruptions_reused_not_rerun':True")
(W/'qualify_integration.py').write_text(s,encoding='utf-8')
s=(PREV/'run_model.py').read_text(encoding='utf-8')
s=s.replace("'baseline.json']","'baseline.json','verify_sources.py']")
(W/'run_model.py').write_text(s,encoding='utf-8')
s=(PREV/'profile_model.py').read_text(encoding='utf-8').replace('batch/digest/source clone validation','batch/digest/source validation and state installation')
(W/'profile_model.py').write_text(s,encoding='utf-8')

identity=['total_ms','p50_ms','p99_ms','max_ms','encode_total_ms','fresh_recovery_p99_ms','migration_ms','stored_directory_bytes','peak_working_set_bytes','peak_commit_bytes','source_p99_ms','source_p50_ms','ordinary_p50_ms','ordinary_p99_ms','ordinary_max_ms','current_reachable_bytes']+[p+'_'+q+'_ms' for p in ['anchor31','checkpoint32','checkpoint_delta63','checkpoint64'] for q in ['p50','p99']]
common={'total_ms':1.10,'p50_ms':1.05,'p99_ms':1.10,'max_ms':1.10,'fresh_recovery_p99_ms':1.10,'migration_ms':1.35,'source_p99_ms':1.10,'ordinary_p50_ms':1.05,'ordinary_p99_ms':1.10,'ordinary_max_ms':1.10,'peak_working_set_bytes':1.35,'peak_commit_bytes':1.35,'stored_directory_bytes':1.0,'current_reachable_bytes':1.0}
checkpoint={p+'_'+q+'_ms':1.10 for p in ['checkpoint32','checkpoint_delta63','checkpoint64'] for q in ['p50','p99']}
anchor={'anchor31_p50_ms':1.10,'anchor31_p99_ms':1.10}
policy={'trial':79,'declared_utc':now(),'before_first_cohort_timer':True,'model_only':True,'default_engine_changed':False,
    'method':{'rounds':6,'cases':54,'variants':['baseline_a','baseline_b','hybrid'],'all_variants_protocol':'hybrid','baseline_a_and_b':'exact qualified076 binary','hybrid_label':'exact qualified078 bounded source-state binary','original_receipts':[126,50126,99126],'publications_per_case':64,'complete_32_publication_cycles':2,'ordinary_receipts_per_case':56,'source_intervals_per_case':8,'source_keys_per_case':2,'fresh_recoveries_per_case':12,'recovery_after_publications':[31,32,63,64],'all_six_orders_per_size':True,'each_variant_and_size_each_position':2,'AB_relative_order_each_direction':3,'all_files_retained':True,'no_observed_case_reruns':True},
    'checks':{'large_publication_goals':{'total_ms':.80,'source_p99_ms':.80},'all_anchor_guards':anchor,'publication_and_common_guards':common,'unchanged_checkpoint_guards':checkpoint,'identity_metrics':identity,'identity_interval':[.90,1.10]},
    'expected_check_count':4+3*(len(common)+len(checkpoint)+len(anchor))+3*len(identity),
    'qualification':'All goals/guards and their matching identical-control calibrations must pass. Preserve every failure. This model trial cannot promote the supported engine or supersede075/077.',
    'timing':'Both binaries fully charge batch/digest/source preflight, source-state installation, serialization/CRC, writes/flushes/syncs/closes/renames and ledger edits. Candidate removes full-ledger source clone; two output metadata substitutions occur outside timers. Summary SHA is outside timers.',
    'recovery':'Same-process fresh opens after dropping writer, three per boundary; OS cache may be warm. Anchor31, checkpoint32, checkpoint+31deltas63 and checkpoint64 are individually guarded.',
    'memory':'Full process peaks include candidate projection. This workload has two source keys; the4096-key bound is functional qualification, not measured maximum-fanout memory evidence.',
    'minimum_free_bytes':3000000000,'timeout_per_case_seconds':600,
    'process_policy':'One owned child at a time; no compilation/tests/audit/package/Git concurrent with timed workload.',
    'scope':'Metadata model only, opaque unchanged segments; no SQL/network/DuckDB/PostgreSQL comparison, cold cache, real segment IO, exclusive writer lock, physical power-loss or reclamation qualification.',
    'prerequisite_078':'57 debug+57 release,15 errors+15 controlled kills,30 corruptions completed separately; reused, not rerun in079.',
    'previous_075_and_077_failures_retained':True,'language':'English','morning_report_frozen':True}
save(W/'policy.json',policy)
(W/'DESIGN.md').write_text('''# Fresh source-state comparison079

Two identical qualified076 controls versus qualified078, unchanged bench075 hybrid64. Original generation129 inputs, actual126/50126/99126 receipts,64 real edits with56 ordinary and8 source publications for two sources, two complete checkpoint cycles and12 fresh opens per case. Six balanced permutations,54 cases. No source edits, rebuild or reused timed sample.

Before the first timer, declare large-history charged publication-total and source p99 goals of0.80, requiring corresponding A/A ratios within0.90..1.10. Guard ordinary p50/p99/max, all-publication p50/p99/max, small-store total/source tail, migration, process peaks, exact metadata bytes, all-open tail and every recovery termination path. The additional source map is charged in full process peaks, but this workload has only two keys and does not establish maximum4096-key memory performance.

The canonical full-file decoder remains byte-identical. Only truthful candidate flags and additional descriptive/gated metrics change the benchmark auditor. Independently decode all67 files for three canonical sizes and SHA-check every replica; all edits, generations, positions, retries, sync counts, input anchors, stages and balanced order must agree. Candidate and control wire bytes must match. Qualification078's native tests/process cuts/corruption checks are prerequisites, not rerun or counted as new079 tests.

One task-owned native child at a time. No compilation, tests, audits, packaging or Git during timed workloads. A3GB guard precedes each unstarted case,600-second owned-child timeout kills and waits, and all observed evidence survives. Report every policy failure, no trimming or rerun. Warm same-process opens, opaque unchanged segment references and native metadata calls do not support real SQL throughput, competitor superiority, production readiness or supported adoption. Keep075 and077 failures visible and morning report frozen.
''',encoding='utf-8')
save(W/'helper-derivation.json',{'prepared_utc':now(),'unchanged_python_helpers':{n:sha(W/n) for n in helpers if n.endswith('.py')},'original_077_auditor_sha256':sha(PREV/'audit_model.py'),'full_canonical_decoder_byte_identical':(W/'canonical_audit.py').read_bytes()==(PREV/'canonical_audit.py').read_bytes(),'audit_prefix_byte_identical':(W/'audit_model.py').read_text(encoding='utf-8').split("policy=load(W/'policy.json')",1)[0]==(PREV/'audit_model.py').read_text(encoding='utf-8').split("policy=load(W/'policy.json')",1)[0],'new_policy_not_retrospective':True})
for p in W.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
print(json.dumps({'assembled':True,'expected_checks':policy['expected_check_count'],'identity_checks':3*len(identity),'no_compilation':True,'reused_binaries_verified':True}))
