"""Pure120 source/build/recovery/smoke/freeze proof before any qualification timer."""
from pathlib import Path
import copy,hashlib,json,re,sys
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).parent))
import audit_preflight_120_v3 as recovery
from audit_native_120_v3 import check_order
import archive_audit_099 as archive
from outcomes_098 import negatives
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inv(p):return {f.relative_to(p).as_posix():sha(f) for f in p.rglob('*') if f.is_file()}
def audit(w):
 assert all(sha(w/n)==h for n,h in load(w/'preflight-freeze.json')['files'].items())
 policy=load(w/'policy.json');prep=load(w/'preparation-proof-v3.json');build=load(w/'build-proof-v3.json');pre=load(w/'preperformance-proof.json');freeze=load(w/'timing-freeze.json')
 assert policy['trial']==120 and sha(w/'policy.json')==load(w/'declaration-proof.json')['policy_sha256']
 repair=load(w/'build-repair-v2.json')
 assert repair['preserved_failed_build_actual_exit']==1 and repair['fresh_baseline_and_all_candidate_configs_required']
 assert inv(w/'source')==inv(w/'source-v1')==load(w/'preparation-proof-v1.json')['candidate']
 assert sha(w/'build-failure-v1.json')==repair['failed_build_proof_sha256'] and not (w/'build-proof-v1.json').exists()
 assert inv(w/'baseline-v1')==policy['baseline_source']
 assert sha(w/'logs-v1/candidate-fixed-debug.log')==repair['failed_compiler_log_sha256']
 setup=load(w/'build-setup-repair-v3.json')
 assert setup['preserved_v2_controller_actual_exit']==1 and setup['no_v2_compiler_or_tests_launched']
 assert sha(w/'build-failure-v2.json')==setup['v2_failure_sha256'] and not (w/'build-proof-v2.json').exists()


 assert prep['complete'] and build['complete'] and pre['complete']
 assert inv(w/'baseline')==inv(w/'baseline-v3')==prep['baseline']==build['baseline']==policy['baseline_source']
 assert inv(w/'source-repaired120')==inv(w/'source-v3')==prep['candidate']==build['candidate']
 for folder in ['source-repaired120','source-v3']:
  current=inv(w/folder);allowed=['src/archive.rs','Cargo.toml','src/adaptive_index_120.rs','tests/index_120.rs']
  assert set(current)==set(policy['candidate_source'])|{'src/adaptive_index_120.rs','tests/index_120.rs'}
  assert all(current[n]==h for n,h in policy['candidate_source'].items() if n not in allowed)
  for name,edits,preimage in [('src/archive.rs',prep['archive_edits'],'archive-before120.rs'),('Cargo.toml',prep['cargo_edits'],'Cargo-before120.toml')]:
   inverse=(w/folder/name).read_bytes()
   for a,b in reversed(edits):assert inverse.count(b.encode())==1;inverse=inverse.replace(b.encode(),a.encode())
   assert inverse==(w/preimage).read_bytes() and sha(w/preimage)==policy['candidate_source'][name]
  assert current['src/adaptive_index_120.rs']==sha(w/'adaptive_index_120.rs') and current['tests/index_120.rs']==sha(w/'index_tests_120.rs')
 driver='examples/adaptive_perf_probe_106.rs';assert sha(w/'baseline-v3'/driver)==sha(w/'source-v3'/driver)==policy['native_driver_sha256']
 records=build['records'];assert len(records)==16 and all(r['returncode']==0 for r in records)
 count=0;lints=0
 for r in records:
  assert sha(w/r['log'])==r['log_sha256'] and '--offline' in r['argv'] and '--locked' in r['argv']
  if r['argv'][1]=='test':
   actual=sum(map(int,re.findall(r'test result: ok\. (\d+) passed;',(w/r['log']).read_text())))
   assert actual==r['tests_passed'];count+=actual
  if r['argv'][1]=='clippy':assert r['argv'][-2:]==['-D','warnings'];lints+=1
 assert count==build['fresh_native_test_executions']==836 and lints==build['strict_lint_modes']==5
 assert inv(w/'binaries-v3')==build['binaries']
 for folder in ['baseline','candidate']:
  for p in (w/'binaries-v3'/folder).glob('*.exe'):assert b'KESTREL_FAULT_POINT' not in p.read_bytes() and b'KESTREL_LIVE_PAUSE' not in p.read_bytes()
 replayed=recovery.audit(w);assert replayed==load(w/'preflight-audit-proof.json') and replayed['fresh_test_executions']==836 and replayed['every_native_actual_exit_checked'] and replayed['fault_cases']==28 and replayed['cold_sql_commands']==300
 derivation=load(w/'harness-derivation-proof-v3.json')
 assert inv(w/'harness')==derivation['shared_harness']
 for name,p in derivation['files'].items():
  assert sha(w/name)==p['derived_sha256']
  old=(w/'controller-parents-v3'/p['parent']).read_text(encoding='utf-8')
  assert sha(w/'controller-parents-v3'/p['parent'])==p['parent_sha256']
  expected=old
  for a,b in p['edits']:expected=expected.replace(a,b)
  expected=re.sub(r'(?<!\d)120(?!\d)','120',expected)
  assert expected==(w/name).read_text(encoding='utf-8')
 for name,h in derivation['additional_dependencies_exact119'].items():assert sha(w/name)==h
 for prefix in ['native','service']:
  cases=policy[prefix+'_cases'];assert [c['index'] for c in cases]==list(range(len(cases)))
  check_order(cases,cases,policy[prefix+'_configs'])
  bad=copy.deepcopy(cases);bad[0]['variant']='candidate' if bad[0]['variant']!='candidate' else 'baseline_a'
  try:check_order(bad,cases,policy[prefix+'_configs']);raise RuntimeError('invalid order accepted')
  except AssertionError:pass
 negative_proof=negatives()
 assert pre['balanced_full_and_half_order_controls']==48 and pre['invalid_conservation_controls']==negative_proof and len(negative_proof['six_invalid_outcome_records_rejected'])==6 and len(pre['native_smokes'])==4 and len(pre['service_smokes'])==2
 for rec in pre['native_smokes']:
  assert rec['returncode']==0 and rec['actual_wait_completed'] and rec['correctness_passed']
  stem=w/'excluded-smokes'/rec['label'];assert sha(stem.with_suffix('.stdout'))==rec['stdout_sha256'] and sha(stem.with_suffix('.stderr'))==rec['stderr_sha256']
  result=load(stem.with_suffix('.stdout'));rows=[];receipts={}
  for a in result['raw_acknowledgements']:
   lo=a['producer']*1000000+a['batch']*100;part=[[i,i*37%1000-500,a['producer']] for i in range(lo,lo+100)];rows+=part
   if result['named']:receipts[a['id']]=(part,a['generation'])
  checked=archive.check(w/rec['fixture'],rows,receipts);assert checked['full_block_crc_bytes']==result['full_crc_bytes'] and checked['head']==result['cold_stats']['generation']
 for rec in pre['service_smokes']:
  result=load(w/rec['report']);assert result['offered_operations']==100 and result['unsuccessful_or_unexecuted']==0 and result['reconciliation']['all_acknowledged_batches_present'] and result['reconciliation']['batch_atomicity_and_sums']
  assert len(result['lifecycle'])==2 and all(c['returncode']==0 and c['graceful_background_joined'] for c in result['lifecycle'])
 assert all(sha(w/n)==h for n,h in freeze['files'].items())
 return {'complete':True,'exact_archive_Cargo_inverses_and_unchanged_other_corrected117_core':True,'fresh_tests':836,'strict_lints':5,'recovery':replayed,'excluded_native_smokes':4,'excluded_service_smokes':2,'balanced_full_and_half_order_controls':48,'negative_conservation_controls':6,'invalid_order_rejections':2,'frozen_files':len(freeze['files']),'all_frozen_inputs_exact':True,'no_Native_or_timer_launched_by_pure_replay':True,'release017_qualified':False}
if __name__=='__main__':
 w=Path(sys.argv[1]);result=audit(w);p=w/'prefix-audit-proof.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:result[k] for k in ['complete','fresh_tests','strict_lints','frozen_files','release017_qualified']}))
