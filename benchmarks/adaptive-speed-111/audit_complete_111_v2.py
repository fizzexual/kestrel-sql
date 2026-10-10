"""Pure complete candidate provenance, recovery and every fixed performance gate."""
from pathlib import Path
import ast, contextlib, hashlib, io, json, re, sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import audit_native_111_v2 as native
import audit_service_111_v2 as service
import audit_preflight_111_v2 as recovery
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inv(p):return {f.relative_to(p).as_posix():sha(f) for f in p.rglob('*') if f.is_file()}
def audit(w):
 policy=load(w/'policy.json');assert policy['trial']==111 and policy['supported']=='0.3.16' and policy['candidate_package_version']=='0.3.17'
 assert sha(w/'policy.json')==load(w/'declaration-proof.json')['policy_sha256']
 build=load(w/'build-proof-v2.json');prep=load(w/'preparation-proof-v2.json')
 assert build['complete'] and build['fresh_native_test_executions']==772 and build['strict_lint_modes']==5
 assert len(build['records'])==16 and sum(r.get('tests_passed',0) for r in build['records'])==772
 assert len({r['target'] for r in build['records'] if r['step'].endswith('-artifacts')})==3
 assert inv(w/'source')==inv(w/'source-v2')==prep['candidate']==build['candidate']
 assert inv(w/'baseline')==inv(w/'baseline-v2')==prep['baseline']==build['baseline']
 assert sorted(n for n,h in policy['baseline_source'].items() if build['baseline'][n]!=h)==['Cargo.toml']
 assert set(build['baseline'])==set(policy['baseline_source'])
 assert sorted(n for n,h in policy['candidate_source'].items() if build['candidate'][n]!=h)==['Cargo.toml','src/archive.rs']
 assert set(build['candidate'])-set(policy['candidate_source'])=={'src/adaptive_scan_111.rs','tests/adaptive_scan_111.rs'}
 assert build['candidate']['src/archive.rs']==prep['new_archive_sha256']
 assert build['candidate']['src/adaptive_live_105.rs']==policy['candidate_source']['src/adaptive_live_105.rs']
 assert prep['all_original_archive_line_endings_preserved']

 # Independently invert every declared Reader edit, including repeated constructors.
 assert prep['all_declared_edits_have_exact_inverse']
 original=(w/'archive-before111.rs').read_bytes()
 assert hashlib.sha256(original).hexdigest()==policy['candidate_source']['src/archive.rs']
 helper=ast.parse((w/'prepare_111.py').read_text())
 assignments=[node for node in helper.body if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='edits']
 assert len(assignments)==1;edits=ast.literal_eval(assignments[0].value)
 recovered=(w/'source/src/archive.rs').read_text()
 for before,after,count in reversed(edits):
  assert recovered.count(after)==count;recovered=recovered.replace(after,before)
 sep='\r\n' if b'\r\n' in original else '\n'
 assert recovered.replace('\n',sep).encode()==original
 flag='adaptive-scan-111 = []\n';alias='adaptive-scan = ["adaptive-scan-111"]\n'
 baseline_cargo=(w/'baseline/Cargo.toml').read_text();candidate_cargo=(w/'source/Cargo.toml').read_text()
 assert baseline_cargo.count(flag)==1 and candidate_cargo.count(flag)==1 and candidate_cargo.count(alias)==1
 assert hashlib.sha256(baseline_cargo.replace(flag,'').encode()).hexdigest()==policy['baseline_source']['Cargo.toml']
 recovered_cargo=candidate_cargo.replace(flag,'').replace(alias,'').replace('adaptive-engine = ["adaptive-collection", "adaptive-filter", "adaptive-replay", "adaptive-scan"]','adaptive-engine = ["adaptive-collection", "adaptive-filter", "adaptive-replay"]')
 assert hashlib.sha256(recovered_cargo.encode()).hexdigest()==policy['candidate_source']['Cargo.toml']
 assert sha(w/'source/src/adaptive_scan_111.rs')==sha(w/'adaptive_scan_111.rs')
 assert sha(w/'source/tests/adaptive_scan_111.rs')==sha(w/'adaptive_scan_111_tests.rs')
 module=(w/'source/src/adaptive_scan_111.rs').read_text()
 assert 'MAX_PAYLOAD_BYTES: usize = 512 * 1024' in module and 'MAX_WINDOW_BLOCKS: usize = 8' in module
 assert 'file.read_exact(&mut window.bytes[..rows * 8])?' in module
 assert 'crc32fast::hash(&self.scratch) != self.segment.metadata.indexes[column].crc[block]' in recovered

 lock=(w/'source/Cargo.lock').read_bytes();sep=b'\r\n' if b'\r\n' in lock else b'\n';old=b'name = "kestrel-sql"'+sep+b'version = "0.3.16"';new=b'name = "kestrel-sql"'+sep+b'version = "0.3.17"'
 assert lock.count(new)==1 and lock.replace(new,old)==(w/'baseline/Cargo.lock').read_bytes()
 cargo=(w/'source/Cargo.toml').read_text();assert 'version = "0.3.17"' in cargo and 'adaptive-collection = ["adaptive-collection-105"]' in cargo
 assert 'adaptive-engine = ["adaptive-collection", "adaptive-filter", "adaptive-replay", "adaptive-scan"]' in cargo
 assert 'adaptive-replay = ["adaptive-replay-110"]' in cargo
 assert 'adaptive-scan = ["adaptive-scan-111"]' in cargo
 assert 'adaptive-filter = ["adaptive-filter-109"]' in cargo
 assert len(build['records'])==16
 for r in build['records']:
  assert r['returncode']==0 and '--offline' in r['argv'] and '--locked' in r['argv'] and sha(w/r['log'])==r['log_sha256']
  if 'tests_passed' in r:assert r['tests_passed']==sum(map(int,re.findall(r'test result: ok\. (\d+) passed;', (w/r['log']).read_text())))
  if r['step'].endswith('-lint'):assert r['argv'][-3:]==['--','-D','warnings']
 assert inv(w/'binaries-v3')==build['binaries']
 for name in ['baseline','candidate']:
  for binary in (w/'binaries-v3'/name).glob('*.exe'):assert b'KESTREL_FAULT_POINT' not in binary.read_bytes() and b'KESTREL_LIVE_PAUSE' not in binary.read_bytes()
 preflight=recovery.audit(w);assert preflight==load(w/'preflight-audit-proof.json') and preflight['correctness_qualified']
 pre=load(w/'preperformance-proof.json');assert pre['complete'] and pre['excluded_from_qualification']
 assert len(pre['native_smokes'])==4 and len(pre['service_smokes'])==2
 for record in pre['native_smokes']:
  assert record['returncode']==0 and record['actual_wait_completed'] and record['correctness_passed']
  label=record['label'];d=w/record['fixture'];result=load(w/'excluded-smokes'/(label+'.stdout'))
  assert sha(w/'excluded-smokes'/(label+'.stdout'))==record['stdout_sha256'] and sha(w/'excluded-smokes'/(label+'.stderr'))==record['stderr_sha256']
  rows=[];receipts={}
  for ack in result['raw_acknowledgements']:
   part=native.data(ack['producer'],ack['batch']);rows+=part
   if result['named']:receipts[ack['id']]=(part,ack['generation'])
  assert native.archive.check(d,rows,receipts)['full_block_crc_bytes']==result['full_crc_bytes'] and result['actual_writer_join_and_pin_release']
 for record in pre['service_smokes']:
  case=load(w/record['report']);assert case['offered_operations']==100 and case['unsuccessful_or_unexecuted']==0
  assert case['reconciliation']['all_acknowledged_batches_present'] and case['reconciliation']['batch_atomicity_and_sums'] and len(case['lifecycle'])==2
  assert all(r['returncode']==0 and r.get('graceful_background_joined') for r in case['lifecycle'])
 freeze=load(w/'timing-freeze.json');assert all(sha(w/n)==h for n,h in freeze['files'].items())
 # Recompute every value from raw evidence. Numerical gate misses are results.
 with contextlib.redirect_stdout(io.StringIO()):
  n=native.audit(w);s=service.audit(w)
 assert n==load(w/'native-audit.json') and s==load(w/'service-audit.json')
 assert n['correctness_passed'] and s['correctness_passed']
 assert len(n['goals'])==42 and sum(g['workload'].startswith('small') for g in n['goals'])==12
 assert sum(g['workload']=='identified-replay' for g in n['goals'])==6
 assert sum(g['metric'] in ['grouped/median_us','grouped/p95_us'] for g in n['goals'])==12
 # An actual duplicate/omission in a balanced order is rejected independently.
 expected=policy['native_cases'];bad=[dict(c) for c in load(w/'paired-native.json')['cases']];bad[0]['variant']=bad[1]['variant']
 try:native.check_order(bad,expected,policy['native_configs'])
 except AssertionError:order_invalid_rejected=True
 else:raise AssertionError('corrupt order control accepted')
 performance=n['performance_qualified'] and s['performance_qualified']
 return {'complete':True,'correctness_passed':True,'supported':'0.3.16','candidate':'0.3.17','fresh_tests':772,'strict_lints':5,
  'source_derivation_and_normal_artifacts_exact':True,'recovery':preflight,'excluded_smokes_replayed':True,'invalid_balanced_order_rejected':order_invalid_rejected,
  'native':n,'service':s,'performance_qualified':performance,'release017_qualified':performance,
  'every_declared_full_and_half_control_guard_and_goal_required':True,'no_Native_timer_or_existing_file_write_during_replay':True,
  'physical_power_loss_and_resource_exhaustion_not_tested':True,'fresh_competitor_or_universal_benchmark_claim':False}
if __name__=='__main__':
 result=audit(Path(sys.argv[1]));print(json.dumps({k:result[k] for k in ['complete','correctness_passed','fresh_tests','strict_lints','performance_qualified','release017_qualified']}))
