"""Pure source/provenance/smoke replay; no native launches or existing-file writes."""
from pathlib import Path
import copy,hashlib,json,math,sys
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).parent))
import archive_audit_099 as archive
from publication_checks_113 import check_profile,check_sql
from audit_native_113 import check_order,data,quantile
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inv(p):return {f.relative_to(p).as_posix():sha(f) for f in p.rglob('*') if f.is_file()}
def smoke(w,record,cache):
 assert record['returncode']==0 and record['actual_wait_completed'] and record['owned_Popen_handle'] and record['pid']==record['process_identity']['pid'] and not record.get('timeout')
 for n in ['stdout','stderr']:assert sha(w/record[n])==record[n+'_sha256']
 c=record['spec'];result=load(w/record['stdout']);acks=result['raw_acknowledgements']
 assert result['version']==('0.3.17' if c['variant']=='candidate' else '0.3.16') and result['adaptive_enabled']==(c['variant']=='candidate')
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
 if c['variant']=='candidate':
  phase=result['adaptive'];assert phase['observed_publications']==len(groups) and sum(phase[n] for n in ['latency_groups','coalescing_groups','pressure_groups'])==stats['collected_groups']
  assert phase['configured_max_delay_ns']==2000000 and phase['max_selected_delay_ns']<=2000000
 else:assert result['adaptive'] is None and stats['group_delay_ns']==0
 checked=archive.check(w/record['fixture'],rows,receipts)
 assert checked['full_block_crc_bytes']==result['full_crc_bytes'] and checked['head']==result['cold_stats']['generation'] and checked['rows']==result['cold_stats']['rows']
 stage_values,stage=check_profile(result);check_sql(result,rows,cache,(c['producers'],c['batches']))
 return {'ACKs':len(acks),'CRC_bytes':checked['full_block_crc_bytes'],'stage':stage,'cold_SQLite_replayed':True}
def audit(w):
 policy=load(w/'policy.json');prep=load(w/'preparation-proof.json');build=load(w/'build-proof.json');pre=load(w/'preperformance-proof.json')
 assert sha(w/'policy.json')==load(w/'declaration-proof.json')['policy_sha256'] and policy['trial']==113
 assert prep['complete'] and build['complete'] and pre['complete']
 driver='examples/adaptive_perf_probe_106.rs';assert inv(w/'baseline')==prep['baseline']==build['baseline'] and inv(w/'source')==prep['candidate']==build['candidate']
 for folder,key in [('baseline','baseline_source'),('source','candidate_source')]:
  expected=policy[key]|{driver:prep['driver_sha256']};assert inv(w/folder)==expected
  inverse=(w/folder/driver).read_text()
  for a,b in reversed(load(w/'driver-edits.json')):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
  assert inverse==(w/'driver-before113.rs').read_text() and sha(w/'driver-before113.rs')==policy[key][driver]
 assert (w/'baseline'/driver).read_bytes()==(w/'source'/driver).read_bytes()
 for prefix,original in [('baseline','baseline_source'),('candidate','candidate_source')]:assert load(w/'parent112-build-proof-v2.json')[prefix]==policy[original]
 assert sha(w/'parent112-build-proof-v2.json')==policy['parent_build_proof_sha256'] and sha(w/'parent112-complete-audit-proof.json')==policy['parent_complete_audit_sha256']
 parent=load(w/'parent112-complete-audit-proof.json');assert parent['complete'] and parent['native_correctness_passed'] and not parent['release017_qualified'] and parent['fresh_tests']==772 and parent['strict_lints']==5
 assert parent['native']['goals']==policy['parent112_all42_native_goals'] and len(parent['native']['goals'])==42
 recovery=load(w/'parent112-preflight-audit-proof.json');assert recovery['correctness_qualified'] and recovery['every_native_actual_exit_checked']
 assert load(w/'parent112-preflight-controller-observation.json')['original_controller_tool_return_unobserved_across_context_compaction']
 for r in build['records']:
  assert r['returncode']==0 and sha(w/r['log'])==r['log_sha256']
  assert '--offline' in r['argv'] and '--locked' in r['argv']
  if r['step'].endswith('-lint'):assert r['argv'][-2:]==['-D','warnings']
 assert len(build['records'])==8 and sum(r.get('fresh_driver_tests_passed',0) for r in build['records'])==4 and sum(r['step'].endswith('-lint') for r in build['records'])==2
 assert inv(w/'binaries')==build['binaries']
 for p in (w/'binaries').rglob('*.exe'):assert b'KESTREL_FAULT_POINT' not in p.read_bytes() and b'KESTREL_LIVE_PAUSE' not in p.read_bytes()
 derivation=load(w/'harness-derivation-proof.json')
 for key,name,oldname in [('controller','run_native_113.py','run_native_112_v2.py'),('auditor','audit_native_113.py','audit_native_112_v2.py')]:
  proof=derivation[key];assert sha(w/name)==proof['derived_sha256'] and sha(w/('parent112-'+oldname))==proof['parent_sha256']
  inverse=(w/name).read_text()
  for a,b in reversed(proof['edits']):assert inverse.count(b)==1;inverse=inverse.replace(b,a)
  assert inverse==(w/('parent112-'+oldname)).read_text()
 check_order(policy['native_cases'],policy['native_cases'],policy['native_configs'])
 bad=copy.deepcopy(policy['native_cases']);bad[0]['variant']='candidate'
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
 return {'complete':True,'source_and_three_driver_inverses_exact':True,'core_parent772_tests5_lints359_recovery_reused_not_rerun':True,'fresh_driver_tests':4,'fresh_strict_lints':2,'excluded_smokes':results,'invalid_order_and_stage_mutations_rejected':4,'freeze_sha256':sha(w/'timing-freeze.json'),'all_frozen_inputs_exact':True,'no_Native_launch_timer_or_existing_file_write':True,'release017_qualified':False}
if __name__=='__main__':
 w=Path(sys.argv[1]);result=audit(w);p=w/'prefix-audit-proof.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({'complete':True,'excluded_smokes':8,'fresh_driver_tests':4,'fresh_lints':2,'parent_core_prerequisites_reused':True}))
