"""Assemble fresh all-hybrid old/old/new comparison, retaining predecessor provenance."""
import ast,hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path
BASE=Path(__file__).resolve().parent;W=BASE/'perf-077';OLD=BASE/'perf-075';NEW=BASE/'perf-076';ROOT=BASE.parent/'outputs/kestrel-sql'
assert not W.exists();W.mkdir()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def now():return datetime.now(timezone.utc).isoformat()
for name in ['catalog_oracle.py','page_oracle.py','hybrid_oracle.py','process_memory.py','canonical_audit.py']:
    shutil.copyfile(OLD/name,W/name)
for src,dst in [(OLD/'model',W/'control-model'),(NEW/'model',W/'candidate-model'),(NEW/'locked-registry-crates',W/'locked-registry-crates')]:
    shutil.copytree(src,dst)
(W/'bin').mkdir();shutil.copyfile(OLD/'bin/growth-model.exe',W/'bin/control-075.exe');shutil.copyfile(NEW/'bin/recovery-model.exe',W/'bin/candidate-076.exe')
(W/'prerequisites').mkdir()
proofs={}
for prefix,source,names in [('075',OLD,['build-proof.json','policy.json','cohort-policy.json','model-audit.json','input-provenance.json']),('076',NEW,['build-proof.json','source-finalization.json','qualification-policy.json','qualification-results.json','operation-count-check.json','publication-byte-equivalence.json','git-publication-check.json'])]:
    for name in names:
        dst=W/'prerequisites'/f'{prefix}-{name}';shutil.copyfile(source/name,dst);proofs[dst.relative_to(W).as_posix()]={'source':str(source/name),'sha256':sha(dst)}
inputs=load(OLD/'input-provenance.json');(W/'inputs').mkdir()
for item in inputs['inputs']:
    src=Path(item['path']);dst=W/'inputs'/src.name;assert sha(src)==item['sha256'];shutil.copyfile(src,dst)
    item.update(source_075=str(src),path=str(dst));assert sha(dst)==item['sha256']
inputs.update(copied_utc=now(),all_original_068_checkpoint_bytes_unchanged=True);save(W/'input-provenance.json',inputs)
baseline=load(NEW/'baseline.json');baseline.update(prepared_utc=now(),repository_commit_before_077='a479d76e9bc41be9cd5e7032d4b2b69ecbcebe1d')
save(W/'baseline.json',baseline);shutil.copyfile(ROOT/'MANIFEST.sha256',W/'repository-manifest-pre-077.sha256')
for n,d in baseline['core_source_sha256'].items():assert sha(ROOT/n)==d
for n,d in baseline['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d
builds={}
for label,source,model,binary in [('control_075',OLD,'control-model','control-075.exe'),('candidate_076',NEW,'candidate-model','candidate-076.exe')]:
    proof=load(source/'build-proof.json');assert proof['complete'] and proof['format_and_strict_clippy_passed']
    for n,d in proof['source_sha256'].items():assert sha(W/model/n)==d
    assert sha(W/'bin'/binary)==proof['binary_sha256']
    builds[label]={'binary':f'bin/{binary}','source_directory':model,'binary_sha256':proof['binary_sha256'],'source_sha256':proof['source_sha256'],'previous_native_test_counts':proof['counts']}
assert load(NEW/'source-finalization.json')['common_CAT4_workloads_main_and_Cargo_byte_identical_to_075']
save(W/'binary-provenance.json',{'complete':True,'prepared_utc':now(),'reused_unchanged_binaries_no_rebuild':True,'variants':{'baseline_a':'control_075','baseline_b':'control_075','hybrid':'candidate_076'},'builds':builds,'prerequisite_proofs':proofs,'no_engine_change':True})
original_order=(OLD/'order_plan.py').read_text(encoding='utf-8')
s=original_order.replace("'mode':'hybrid' if v=='hybrid' else 'cat4'","'mode':'hybrid'").replace("c['mode']==('hybrid' if c['variant']=='hybrid' else 'cat4')","c['mode']=='hybrid'")
(W/'order_plan.py').write_text(s,encoding='utf-8')
s=(OLD/'qualify_integration.py').read_text(encoding='utf-8').replace("EXE=W/'bin/growth-model.exe'","BINARIES={'control_075':W/'bin/control-075.exe','candidate_076':W/'bin/candidate-076.exe'}")
s=s.replace("assert sha(EXE)==load(W/'build-proof.json')['binary_sha256']","for variant,exe in BINARIES.items():assert sha(exe)==load(W/'binary-provenance.json')['builds'][variant]['binary_sha256']")
s=s.replace("for mode in ['cat4','hybrid']:","for variant,EXE in BINARIES.items():\n        mode='hybrid'").replace("label=f'{n}-{mode}'","label=f'{n}-{variant}'")
s=s.replace("'binary_sha256':sha(EXE)","'binary_sha256':{k:sha(p) for k,p in BINARIES.items()}")
(W/'qualify_integration.py').write_text(s,encoding='utf-8')
# The full logical decoder is unchanged; only all-hybrid binary selection and new gates differ.
s=(OLD/'audit_model.py').read_text(encoding='utf-8')
s=s.replace("assert sha(W/'bin/growth-model.exe')==cohort['binary_sha256'] and not load(W/'post-timing-process-check.json')['active_processes']", "for n,d in cohort['binary_sha256'].items():assert sha(W/n)==d,n\nassert not load(W/'post-timing-process-check.json')['active_processes']")
s=s.replace("    cases.append({'label':label", "    path_metrics={}\n    for seq,path_name in [(30,'anchor31'),(31,'checkpoint32'),(62,'checkpoint_delta63'),(63,'checkpoint64')]:\n        times=[r['recovery_ms'] for r in x['fresh_recovery'] if r['after_sequence']==seq]\n        assert len(times)==3\n        path_metrics.update({path_name+'_p50_ms':quantile(times,.5),path_name+'_p99_ms':quantile(times,.99)})\n    cases.append({**path_metrics,'label':label")
s=s.replace("checks=[];summaries=[];metrics=", "checks=[];summaries=[];metrics=")
start=s.index('checks=[];summaries=[];metrics=');s=s[:start]+'''checks=[];summaries=[]
metrics=['total_ms','p50_ms','p99_ms','max_ms','encode_total_ms','fresh_recovery_p99_ms','migration_ms','source_p99_ms','stored_directory_bytes','peak_working_set_bytes','peak_commit_bytes','current_reachable_bytes','noncheckpoint_p50_ms','noncheckpoint_p99_ms','checkpoint_sum_ms','checkpoint_max_ms']+[p+'_'+q+'_ms' for p in ['anchor31','checkpoint32','checkpoint_delta63','checkpoint64'] for q in ['p50','p99']]
def add(kind,seed,metric,ratio,limit=None,interval=None):
    passed=math.isfinite(ratio) and (interval[0]<=ratio<=interval[1] if interval else ratio<=limit)
    checks.append({'kind':kind,'seed_receipts':seed,'metric':metric,'paired_ratio':ratio,'limit':limit,'interval':interval,'passed':passed})
for seed in [0,50000,99000]:
    pairs=[]
    for turn in range(6):
        group={c['spec']['variant']:c for c in cases if c['spec']['round']==turn and c['spec']['seed_receipts']==seed}
        a=group['baseline_a'];b=group['baseline_b'];p=group['hybrid']
        pairs.append({'round':turn,'candidate_a':{k:p[k]/a[k] for k in metrics},'identity_b_a':{k:b[k]/a[k] for k in metrics}})
    ratios={label:{k:statistics.median(p[label][k] for p in pairs) for k in metrics} for label in ['candidate_a','identity_b_a']}
    c=ratios['candidate_a'];lim=policy['checks']
    for metric,limit in lim['publication_and_common_guards'].items():add('guard',seed,metric,c[metric],limit)
    for metric,limit in lim['unchanged_checkpoint_guards'].items():add('guard',seed,metric,c[metric],limit)
    for metric,limit in (lim['large_anchor_goals'] if seed else lim['small_anchor_guards']).items():add('goal' if seed else 'guard',seed,metric,c[metric],limit)
    for metric in lim['identity_metrics']:add('identity',seed,metric,ratios['identity_b_a'][metric],interval=lim['identity_interval'])
    display={label:{k:statistics.median(c[k] for c in cases if c['spec']['seed_receipts']==seed and c['spec']['variant']==label) for k in metrics} for label in ['baseline_a','baseline_b','hybrid']}
    summaries.append({'seed_receipts':seed,'actual_receipts':len(expected[seed][0]['batches']),'pairs':pairs,'median_paired_ratios':ratios,'median_display_only':display})
assert len(checks)==policy['expected_check_count']
assert sum(c['kind']=='goal' for c in checks)==4
save(W/'fixture-inventory.json',files)
goal_checks=[c for c in checks if c['kind']=='goal'];identity={(c['seed_receipts'],c['metric']):c['passed'] for c in checks if c['kind']=='identity'}
audit={'complete':True,'audited_utc':datetime.now(timezone.utc).isoformat(),'model_only':True,'publication_samples':3456,'fresh_recovery_samples':648,'cases':cases,'summaries':summaries,'checks':checks,
    'failed_checks':[c for c in checks if not c['passed']],
    'large_anchor_recovery_goals_calibrated_and_passed':all(c['passed'] and identity[(c['seed_receipts'],c['metric'])] for c in goal_checks),
    'all_fresh_comparison_checks_passed':all(c['passed'] for c in checks),'advance_to_engine_design':False,
    'file_instances':len(files),'stored_bytes_total':sum(v['bytes'] for v in files.values()),
    'independent_full_decoded_canonical_cases':3,'independent_full_decoded_canonical_files':logical_reads,
    'all_replica_full_file_hashes_equal_independently_validated_canonical':True,
    'all_logical_edits_recovery_hashes_sources_bounds_stage_counts_and_order_passed':True,
    'no_engine_edit_or_promotion':True,'all_raw_and_frozen_hashes_unchanged':True,
    'previous_075_adoption_failures_unchanged_and_not_superseded':True,'no_fresh_cuts_076_prerequisite_retained':True}
save(W/'model-audit.json',audit)
print(json.dumps({'complete':True,'files':len(files),'publication_samples':3456,'recoveries':648,'failed':{kind:sum(c['kind']==kind for c in audit['failed_checks']) for kind in ['goal','guard','identity']},'calibrated_anchor_goals':audit['large_anchor_recovery_goals_calibrated_and_passed'],'engine_advance':False}))
'''
(W/'audit_model.py').write_text(s,encoding='utf-8')
identity=['total_ms','p50_ms','p99_ms','max_ms','encode_total_ms','fresh_recovery_p99_ms','migration_ms','stored_directory_bytes','peak_working_set_bytes','peak_commit_bytes','source_p99_ms','current_reachable_bytes']+[p+'_'+q+'_ms' for p in ['anchor31','checkpoint32','checkpoint_delta63','checkpoint64'] for q in ['p50','p99']]
common={'total_ms':1.10,'p50_ms':1.05,'p99_ms':1.10,'max_ms':1.10,'fresh_recovery_p99_ms':1.10,'migration_ms':1.35,'source_p99_ms':1.10,'peak_working_set_bytes':1.35,'peak_commit_bytes':1.35,'stored_directory_bytes':1.0,'current_reachable_bytes':1.0}
checkpoint={p+'_'+q+'_ms':1.10 for p in ['checkpoint32','checkpoint_delta63','checkpoint64'] for q in ['p50','p99']}
policy={'trial':77,'declared_utc':now(),'before_first_cohort_timer':True,'model_only':True,'default_engine_changed':False,
    'method':{'rounds':6,'cases':54,'variants':['baseline_a','baseline_b','hybrid'],'all_variants_protocol':'hybrid','baseline_a_and_b':'exact unchanged075 hybrid binary','hybrid_label':'exact qualified076 reader binary','original_receipts':[126,50126,99126],'publications_per_case':64,'complete_32_publication_cycles':2,'ordinary_receipts_per_case':56,'source_intervals_per_case':8,'fresh_recoveries_per_case':12,'recovery_after_publications':[31,32,63,64],'all_six_orders_per_size':True,'each_variant_and_size_each_position':2,'AB_relative_order_each_direction':3,'all_files_retained':True,'no_observed_case_reruns':True},
    'checks':{'large_anchor_goals':{'anchor31_p50_ms':.80,'anchor31_p99_ms':.85},'small_anchor_guards':{'anchor31_p50_ms':1.10,'anchor31_p99_ms':1.10},'publication_and_common_guards':common,'unchanged_checkpoint_guards':checkpoint,'identity_metrics':identity,'identity_interval':[.90,1.10]},
    'expected_check_count':4+3*(len(common)+len(checkpoint))+2+3*len(identity),
    'qualification':'Each metric needs its corresponding identical-control calibration. Report all goals/guards/A-A including failures; even a narrow recovery success does not supersede075 rejection or adopt engine.',
    'timing':'Actual batch/digest/source full-clone validation, serialization/CRC, all writes/flushes/syncs/closes/renames and ledger edits charged unchanged; summary SHA outside timers.',
    'recovery':'Same-process fresh opens after dropping writer, three per boundary; OS cache may be warm. after31 terminates at anchor, after32/64 at checkpoint, after63 is checkpoint plus31 deltas, not anchor termination.',
    'minimum_free_bytes':3000000000,'timeout_per_case_seconds':600,
    'process_policy':'One owned child at a time; no compilation/tests/audit/package/Git concurrent with timed workload.',
    'scope':'Metadata model only, opaque unchanged segments; no SQL/network/DuckDB/PostgreSQL comparison, full legacy migration, exclusive locking, physical power-loss or reclamation qualification.',
    'prerequisite_076':'49 debug+49 release,15 errors+15 controlled kills,30 corruptions completed separately; reused, not rerun in077.',
    'language':'English','morning_report_frozen':True}
save(W/'policy.json',policy)
(W/'DESIGN.md').write_text('''# Fresh recovery comparison077

Two identical075 hybrid controls versus the already qualified076 reader, all using unchanged bench07564. Original gen129 inputs, actual126/50126/99126 receipts,64 real edits and two complete checkpoint cycles. Six fully balanced permutations. No source or supported engine changes, no rebuild, no reused timer controls. The hybrid label selects the candidate binary; every case uses hybrid protocol, unlike075 CAT4 comparisons.

Anchor-terminated opens after31 are separated from checkpoint32, checkpoint+31deltas63 and checkpoint64. Predeclared meaningful large anchor p50/p99 goals are0.80/0.85, each requiring its A/A calibration0.90..1.10. Small anchor and unchanged checkpoint paths are guarded at1.10. Publication, source p99, migration, full process memory, exact retained/currentbytes and all-open p99 remain guarded. Full checks and drift retained; narrow recovery does not erase075 failures or authorize adoption.

Each recovery sample is a fresh native open in the same process, potentially warm OS cache. Three opens per boundary and six paired rounds yield descriptive medians; no cold-cache or statistical population guarantee. Full ledger SHA is outside recovery timers. All shared publication/source/digest/clone/file sync behavior is charged. Only native metadata model IO is profiled; no real data-segment/SQL/network comparison.

Independent frozen Python canonical decoder reconstructs every one of67 files for three sizes, then SHA-checks all54 stores across both binaries. Receipt digests, generations, source positions, retries, sync counts, exact input anchors, per-sample stage sums and balanced order must pass. No hashing/audit/package work during timers. One owned child, wait/kill+wait on timeout; preserve each observed case and stop at3GB disk guard. A frozen cohort may resume only unstarted cases after a separately preserved process check, no changes to policy, source, binaries, inputs or oracle.
''',encoding='utf-8')
save(W/'helper-derivation.json',{'prepared_utc':now(),'unchanged_python_helpers':{n:sha(W/n) for n in ['catalog_oracle.py','page_oracle.py','hybrid_oracle.py','process_memory.py','canonical_audit.py']},'original_075_auditor_sha256':sha(OLD/'audit_model.py'),'full_canonical_decoder_byte_identical':(W/'canonical_audit.py').read_bytes()==(OLD/'canonical_audit.py').read_bytes(),'audit_prefix_sha256':hashlib.sha256(s.split("policy=load(W/'policy.json')",1)[0].encode()).hexdigest(),'new_policy_not_retrospective':True})
for p in W.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
print(json.dumps({'assembled':True,'expected_checks':policy['expected_check_count'],'identity_checks':3*len(identity),'no_compilation':True,'reused_binaries_verified':True}))
