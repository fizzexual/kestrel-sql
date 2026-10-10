"""Pure complete candidate provenance, recovery and every fixed performance gate."""
from pathlib import Path
import ast, contextlib, hashlib, io, json, re, sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import audit_native_112_v2 as native
import audit_service_112_v2 as service
import audit_preflight_112_v2 as recovery
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inv(p):return {f.relative_to(p).as_posix():sha(f) for f in p.rglob('*') if f.is_file()}
def audit(w):
 policy=load(w/'policy.json');assert policy['trial']==112 and policy['supported']=='0.3.16' and policy['candidate_package_version']=='0.3.17'
 assert sha(w/'policy.json')==load(w/'declaration-proof.json')['policy_sha256']
 build=load(w/'build-proof-v2.json');prep=load(w/'preparation-proof-v2.json')
 assert build['complete'] and build['fresh_native_test_executions']==772 and build['strict_lint_modes']==5
 assert len(build['records'])==16 and sum(r.get('tests_passed',0) for r in build['records'])==772
 assert len({r['target'] for r in build['records'] if r['step'].endswith('-artifacts')})==3
 assert inv(w/'source')==inv(w/'source-v2')==prep['candidate']==build['candidate']
 assert inv(w/'baseline')==inv(w/'baseline-v2')==prep['baseline']==build['baseline']
 assert sorted(n for n,h in policy['baseline_source'].items() if build['baseline'][n]!=h)==[]
 assert set(build['baseline'])==set(policy['baseline_source'])
 assert sorted(n for n,h in policy['candidate_source'].items() if build['candidate'][n]!=h)==['src/archive.rs']
 assert set(build['candidate'])-set(policy['candidate_source'])=={'src/adaptive_scan_112.rs'}
 assert build['candidate']['src/archive.rs']==prep['new_archive_sha256']
 assert build['candidate']['src/adaptive_live_105.rs']==policy['candidate_source']['src/adaptive_live_105.rs']
 assert prep['all_original_archive_line_endings_preserved']

 # Independently invert112 to the original Reader and111 to that same source.
 original=(w/'archive-before112.rs').read_bytes()
 parent111=(w/'archive-parent111.rs').read_bytes()
 assert hashlib.sha256(original).hexdigest()==policy['original_pre111_archive_sha256']
 assert hashlib.sha256(parent111).hexdigest()==policy['candidate_source']['src/archive.rs']
 assert prep['parent111_archive_sha256']==hashlib.sha256(parent111).hexdigest()
 method=(w/'read_buffered_112.rs').read_text()
 helper=ast.parse((w/'prepare_112.py').read_text())
 assignments=[node for node in helper.body if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='edits']
 assert len(assignments)==1
 def literal(node):
  if isinstance(node,ast.Constant) and isinstance(node.value,(str,int)):return node.value
  if isinstance(node,ast.List):return [literal(n) for n in node.elts]
  if isinstance(node,ast.Tuple):return tuple(literal(n) for n in node.elts)
  if isinstance(node,ast.Name) and node.id=='method':return method
  if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):
   a=literal(node.left);b=literal(node.right);assert isinstance(a,str) and isinstance(b,str);return a+b
  raise AssertionError(ast.dump(node))
 edits=literal(assignments[0].value);assert len(edits)==6
 candidate=(w/'source/src/archive.rs').read_text();recovered=candidate
 for before,after,count in reversed(edits):
  assert recovered.count(after)==count;recovered=recovered.replace(after,before)
 sep='\r\n' if b'\r\n' in original else '\n'
 assert recovered.replace('\n',sep).encode()==original
 parent_helper=ast.parse((w/'parent-prepare111.py').read_text())
 assignment=next(node for node in parent_helper.body if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='edits')
 recovered111=parent111.decode().replace('\r\n','\n')
 for before,after,count in reversed(ast.literal_eval(assignment.value)):
  assert recovered111.count(after)==count;recovered111=recovered111.replace(after,before)
 assert recovered111.replace('\n',sep).encode()==original
 def structure(s):return s[s.index("struct Reader<'a> {"):s.index("impl Reader<'_> {")]
 def block(s):return s[s.index('    fn read_block_into('):s.index('    fn bound(',s.index('    fn read_block_into('))]
 assert structure(candidate)==structure(recovered)
 assert block(candidate).replace(method+'\n','')==block(recovered)
 assert prep['original_pre111_Reader_structure_constructors_and_single_block_method_byte_exact']
 assert prep['Cargo_and_all_parent111_other_sources_and_five_integration_tests_exact']
 assert prep['new_borrowed_views_checked_before_decode_no_window_to_scratch_copy']
 assert sha(w/'source/src/adaptive_scan_112.rs')==sha(w/'adaptive_scan_112.rs')
 assert build['candidate']['src/adaptive_scan_111.rs']==policy['candidate_source']['src/adaptive_scan_111.rs']
 assert build['candidate']['tests/adaptive_scan_111.rs']==policy['candidate_source']['tests/adaptive_scan_111.rs']
 module=(w/'source/src/adaptive_scan_112.rs').read_text()
 assert 'MAX_PAYLOAD_BYTES: usize = 512 * 1024' in module and 'MAX_WINDOW_BLOCKS: usize = 8' in module
 assert 'copy_from_slice' not in module
 assert 'file.read_exact(&mut window.bytes[..rows * 8])?' in module
 assert 'crc32fast::hash(data) != self.segment.metadata.indexes[column].crc[block]' in method
 assert 'data.chunks_exact(8)' in method and 'windows.invalidate(column)' in method
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
