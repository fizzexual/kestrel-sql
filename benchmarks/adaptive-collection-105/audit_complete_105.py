"""Complete pure adaptive correctness provenance, failure and raw replay."""
from pathlib import Path
import json,re,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import audit_adaptive_105_v3 as current

def rejected(call):
 try:call()
 except AssertionError:return True
 raise AssertionError('invalid independent reference accepted')

def audit(w):
 load=current.load;sha=current.sha
 policy=load(w/'policy.json');assert sha(w/'policy.json')=='003791518bae03507296bf36e4de91429e1bee9833d2330984fb60b38ed30f67'
 assert policy['trial']==105 and policy['supported_version']=='0.3.16' and not policy['release017_qualified']
 prep=load(w/'preparation-proof.json');assert len(prep['common_baseline'])==29
 build=load(w/'build-proof-v2.json');assert build['complete'] and build['fresh_native_test_executions']==684 and build['strict_lint_modes']==5
 assert current.inventory(w/'source-v2')==build['candidate']==current.inventory(w/'source')
 assert current.inventory(w/'baseline-v2')==build['baseline']==current.inventory(w/'baseline')
 derivation=load(w/'source-derivation-v2.json');assert derivation['candidate']==build['candidate'] and derivation['baseline']==build['baseline']
 original=policy['baseline_source_sha256'];assert derivation['supported']==original
 for n,h in original.items():
  if n not in ['src/live.rs','Cargo.toml']:assert build['baseline'][n]==h and build['candidate'][n]==h
 assert derivation['candidate_changed_files']==['Cargo.toml','examples/adaptive_probe_105.rs','src/adaptive_live_105.rs','src/bin/kestrel_stress_098.rs','src/live.rs','tests/adaptive_105.rs']
 assert len(build['records'])==16
 for r in build['records']:
  assert r['returncode']==0 and sha(w/r['log'])==r['log_sha256'] and '--offline' in r['argv'] and '--locked' in r['argv']
  if 'tests_passed' in r:assert r['tests_passed']==sum(map(int,re.findall(r'test result: ok\. (\d+) passed;', (w/r['log']).read_text())))
  if r['step'].endswith('-lint'):assert r['argv'][-3:]==['--','-D','warnings']
 assert current.inventory(w/'binaries-v2')==build['binaries']
 for folder in ['baseline','candidate']:
  for p in (w/'binaries-v2'/folder).glob('*.exe'):assert b'KESTREL_FAULT_POINT' not in p.read_bytes() and b'KESTREL_LIVE_PAUSE' not in p.read_bytes()
 failed=load(w/'build-failure-v1.json');assert len(failed['records'])==5 and failed['records'][-1]['step']=='candidate-adaptive-debug' and failed['records'][-1]['returncode']!=0
 assert "associated function `new` is private" in failed['error'] and 'mismatched types' in failed['error']
 for r in failed['records']:assert sha(w/r['log'])==r['log_sha256']
 first=load(w/'source-derivation-v1.json');assert current.inventory(w/'source-v1')==first['candidate'] and current.inventory(w/'baseline-v1')==first['baseline']
 assert [n for n in build['candidate'] if build['candidate'][n]!=first['candidate'][n]]==['examples/adaptive_probe_105.rs']
 failures=[]
 for prefix,count in [('external',319),('external-v2',359)]:
  f=load(w/(prefix+'-failure.json'));records=f['records'];assert len(records)==count
  for i,r in enumerate(records):
   assert r['index']==i and r['actual_wait_completed'] and r['owned_Popen_handle'] and not r.get('timeout')
   assert r['returncode']==(87 if r['fault_environment'].get('KESTREL_FAULT_MODE')=='io_error' else 86 if r['fault_environment'] else 1 if 'corruption-' in ' '.join(r['argv']) else 0)
   for kind in ['stdout','stderr']:assert sha(w/r[kind])==r[kind+'_sha256']
  frozen=load(w/(prefix+'-freeze.json'));assert all(sha(w/n)==h for n,h in frozen['files'].items())
  assert len(f['scenarios'])==2 and len(f['faults'])==28 and len(f['corruptions'])==10
  for c in f['faults']:
   published=c['spec']['point']=='catalog_published'
   assert current.brief(current.archive.check(w/c['before_directory'],*current.fault_model(published)))==c['before']
   assert current.brief(current.archive.check(w/c['directory'],*current.fault_model(published,True)))==c['after']
  if prefix=='external':assert f['current']=={'legacy':'KSQLCAT2'} and 'np.array_equal' in f['error']
  else:assert f['current'] is None and "stats['prepared_retry_hits']==512" in f['error']
  failures.append({'attempt':prefix,'closed_commands':count,'all_raw_and_frozen_exact':True,'all28_failure_recovery_models_replayed':True})
 qualified=current.audit(w);assert qualified==load(w/'external-audit-proof-v3.json')
 repair=load(w/'external-audit-repair-v3.json');assert repair['no_Native_or_performance_timer_launches'] and repair['new_auditor_sha256']==sha(w/'audit_adaptive_105_v3.py')
 seed=w/load(w/'external-seed.json')['directory'];rows,receipts=current.fault_model(False)
 controls=[rejected(lambda:current.archive.check(seed,rows[:-1],receipts)),
  rejected(lambda:current.archive.check(seed,rows,{})),
  rejected(lambda:current.archive.check(seed,rows,{'adaptive:seed':(current.data(-9),1)})),
  rejected(lambda:current.archive.check(seed,rows,{'adaptive:seed':(rows,2)}))]
 assert all(controls)
 return {'complete':True,'correctness_passed':True,'supported':'0.3.16','release017_qualified':False,'performance_qualified':False,
  'fresh_tests':684,'strict_lints':5,'source_archive_query_source_WAL_lock_dependency_bytes_exact':True,
  'external':qualified,'failed_preparation_build_and_oracle_material_retained':True,'failed_oracle_attempts':failures,
  'invalid_reference_controls_rejected':len(controls),'no_Native_timer_or_existing_file_write_during_replay':True}

if __name__=='__main__':print(json.dumps(audit(Path(sys.argv[1])),indent=2))
