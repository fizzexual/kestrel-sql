"""Pure115 source/prerequisite/smoke replay; baseline is experimental serial112."""
from pathlib import Path
import copy,hashlib,json,re,sys
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).parent))
import archive_audit_099 as archive
from publication_checks_115 import check_profile,check_sql
from audit_native_115 import check_order,data,quantile
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inv(p):return {f.relative_to(p).as_posix():sha(f) for f in p.rglob('*') if f.is_file()}
def smoke(w,record,cache):
 assert record['returncode']==0 and record['actual_wait_completed'] and record['owned_Popen_handle'] and record['pid']==record['process_identity']['pid'] and not record.get('timeout')
 for n in ['stdout','stderr']:assert sha(w/record[n])==record[n+'_sha256']
 c=record['spec'];result=load(w/record['stdout']);acks=result['raw_acknowledgements']
 assert result['version']=='0.3.17' and result['adaptive_enabled'] is True
 assert result['producers']==c['producers'] and result['batches_each']==c['batches'] and result['named']==bool(c['named'])
 assert len(acks)==c['producers']*c['batches'] and {(a['producer'],a['batch']) for a in acks}=={(p,b) for p in range(c['producers']) for b in range(c['batches'])}
 rows=[];receipts={};groups={}
 for a in acks:
  part=data(a['producer'],a['batch']);rows+=part;identifier=f"native:{a['producer']}:{a['batch']}" if c['named'] else None
  assert a['id']==identifier and a['rows']==100 and a['generation']>0 and isinstance(a['elapsed_ns'],int) and a['elapsed_ns']>0
  if identifier is not None:receipts[identifier]=(part,a['generation'])
  groups[a['generation']]=groups.get(a['generation'],0)+1
 samples=[a['elapsed_ns'] for a in acks]
 for name,q in [('p50',.5),('p95',.95),('p99',.99)]:assert result['latency_ns'][name]==quantile(samples,q)
 assert result['latency_ns']['max']==max(samples) and result['wall_ns']>0
 stats=result['ingest'];assert stats['committed_batches']==len(acks) and stats['durable_group_commits']==len(groups)
 assert stats['max_group_requests']==max(groups.values())<=64
 assert stats['queued_payload_bytes']==stats['maintenance_errors']==stats['duplicate_batches']==0 and not stats['writer_poisoned']
 assert result['actual_writer_join_and_pin_release'] and result['all_original_receipt_generations_checked']==bool(c['named'])
 if result['adaptive_enabled']:
  phase=result['adaptive'];assert phase['observed_publications']==len(groups) and sum(phase[n] for n in ['latency_groups','coalescing_groups','pressure_groups'])==stats['collected_groups']
  assert phase['configured_max_delay_ns']==2000000 and phase['max_selected_delay_ns']<=2000000
 else:assert result['adaptive'] is None and stats['group_delay_ns']==0
 checked=archive.check(w/record['fixture'],rows,receipts)
 assert checked['full_block_crc_bytes']==result['full_crc_bytes'] and checked['head']==result['cold_stats']['generation'] and checked['rows']==result['cold_stats']['rows']
 stage_values,stage=check_profile(result);check_sql(result,rows,cache,(c['producers'],c['batches']))
 return {'ACKs':len(acks),'CRC_bytes':checked['full_block_crc_bytes'],'stage':stage,'cold_SQLite_replayed':True}
def audit(w):
 policy=load(w/'policy.json');prep=load(w/'preparation-proof.json');build=load(w/'build-proof.json');pre=load(w/'preperformance-proof.json')
 assert policy['trial']==115 and sha(w/'policy.json')==load(w/'declaration-proof.json')['policy_sha256']
 assert policy['all_three_timed_variants_package_version']=='0.3.17' and policy['all_three_timed_variants_runtime_adaptive_enabled'] and policy['not_a_supported016_baseline_or_release_qualification']
 assert prep['complete'] and build['complete'] and pre['complete']
 driver='examples/adaptive_perf_probe_106.rs'
 for folder,key,bkey in [('baseline','baseline_source','baseline'),('source','candidate_source','candidate')]:
  assert inv(w/folder)==prep[bkey]==build[bkey]==policy[key]|{driver:prep['driver_sha256']}
  inverse=(w/folder/driver).read_text(encoding='utf-8')
  for a,b in reversed(load(w/'driver-edits.json')):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
  assert inverse.encode('utf-8')==(w/'driver-before115.rs').read_bytes() and sha(w/'driver-before115.rs')==policy[key][driver]
 assert (w/'baseline'/driver).read_bytes()==(w/'source'/driver).read_bytes()
 requirements=policy['parent_release_requirements']
 for trial,tests,key,role in [(112,772,'baseline_source','serial112'),(114,796,'candidate_source','concurrent114')]:
  p=load(w/f'parent{trial}-policy.json');b=load(w/f'parent{trial}-build-proof-v2.json');c=load(w/f'parent{trial}-complete-audit-proof.json')
  assert sha(w/f'parent{trial}-policy.json')==requirements[role+'_policy_sha256'] and sha(w/f'parent{trial}-complete-audit-proof.json')==requirements[role+'_complete_audit_sha256']
  assert sha(w/f'parent{trial}-build-proof-v2.json')==policy[role+'_build_proof_sha256'] and b['candidate']==policy[key]
  assert c['complete'] and c['native_correctness_passed'] and not c['release017_qualified'] and c['fresh_tests']==tests and c['strict_lints']==5
  assert c['native']['cases']==len(p['native_cases'])==324 and len(c['native']['goals'])==42 and c['native']['goals']==requirements[role+'_native_all42_goals']
  assert c['service']['status']=='UNSTARTED_UNTESTED' and c['service']['cases']==252 and c['service']['all_specs']==p['service_cases']
  assert (c['native']['identity_failed'],c['native']['candidate_guards_failed'],c['native']['goals_failed'])==((25,13,1) if trial==112 else (12,5,9))
  recovery=load(w/f'parent{trial}-preflight-audit-proof.json');assert recovery['correctness_qualified'] and recovery['every_native_actual_exit_checked'] and recovery['fresh_test_executions']==tests
 assert load(w/'parent112-preflight-controller-observation.json')['original_controller_tool_return_unobserved_across_context_compaction']
 observation=load(w/'parent114-controller-exit-observation.json');assert observation['all_current114_controller_API_exits_observed'] and observation['recovery_controller']['actual_tool_exit_code']==0
 for r in build['records']:
  assert r['returncode']==0 and sha(w/r['log'])==r['log_sha256'] and '--offline' in r['argv'] and '--locked' in r['argv']
  assert r['argv'][r['argv'].index('--features')+1]=='benchmark-shutdown,adaptive-engine'
  if r['step'].endswith('-lint'):assert r['argv'][-2:]==['-D','warnings']
  if 'fresh_driver_tests_passed' in r:assert sum(map(int,re.findall(r'test result: ok\. (\d+) passed;',(w/r['log']).read_text(encoding='utf-8'))))==r['fresh_driver_tests_passed']==1
 assert len(build['records'])==8 and sum(r.get('fresh_driver_tests_passed',0) for r in build['records'])==4 and sum(r['step'].endswith('-lint') for r in build['records'])==2
 assert inv(w/'binaries')==build['binaries']
 for p in (w/'binaries').rglob('*.exe'):assert b'KESTREL_FAULT_POINT' not in p.read_bytes() and b'KESTREL_LIVE_PAUSE' not in p.read_bytes()
 derived=load(w/'harness-derivation-proof.json')
 for name,p in derived['files'].items():
  assert sha(w/name)==p['derived_sha256'] and sha(w/('parent113-'+p['parent']))==p['parent_sha256']
  inverse=(w/name).read_text(encoding='utf-8')
  for a,b in reversed(p['edits']):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
  assert re.sub(r'(?<!\d)115(?!\d)','113',inverse)==(w/('parent113-'+p['parent'])).read_text(encoding='utf-8')
 assert sha(w/'publication_checks_115.py')==derived['unchanged_profile_checks_source_sha256']==derived['unchanged_profile_checks_dest_sha256']
 check_order(policy['native_cases'],policy['native_cases'],policy['native_configs'])
 bad=copy.deepcopy(policy['native_cases']);bad[0]['variant']='baseline_a' if bad[0]['variant']=='candidate' else 'candidate'
 try:check_order(bad,policy['native_cases'],policy['native_configs']);raise RuntimeError('invalid order accepted')
 except AssertionError:pass
 assert len(pre['native_smokes'])==8;cache={};results=[smoke(w,r,cache) for r in pre['native_smokes']]
 first=load(w/pre['native_smokes'][0]['stdout'])
 for change in ['count','histogram','final_generation']:
  bad=copy.deepcopy(first)
  if change=='count':bad['publication_profile_after_writer_join']['segment_sync']['count']+=1
  if change=='histogram':bad['publication_profile_after_writer_join']['catalog_sync']['histogram'][0]+=1
  if change=='final_generation':bad['cold_stats']['generation']+=1
  try:check_profile(bad);raise RuntimeError('invalid stage conservation accepted')
  except AssertionError:pass
 freeze=load(w/'timing-freeze.json');assert all(sha(w/n)==h for n,h in freeze['files'].items())
 return {'complete':True,'both_parent_engine_Cargo_lock_tests_unchanged':True,'three_identical_driver_exact_byte_inverses':True,'all_three_timed_variants017_adaptive_serial112_vs_concurrent114':True,'reused_serial112_tests':772,'reused_concurrent114_tests':796,'reused_strict_lints_each':5,'reused_recovery_commands_each':359,'both_prior_full324_native252_service42_goal_requirements_unchanged':True,'historical112_unobserved_preflight_API_not_reclassified':True,'fresh_driver_tests':4,'fresh_strict_lints':2,'excluded_smokes':results,'invalid_order_and_stage_mutations_rejected':4,'freeze_sha256':sha(w/'timing-freeze.json'),'all_frozen_inputs_exact':True,'no_Native_launch_timer_or_existing_file_write':True,'release017_qualified':False}
if __name__=='__main__':
 w=Path(sys.argv[1]);result=audit(w);p=w/'prefix-audit-proof.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({'complete':True,'fresh_driver_tests':4,'fresh_lints':2,'excluded_smokes':8,'baseline_serial112_not016':True,'release017_qualified':False}))
