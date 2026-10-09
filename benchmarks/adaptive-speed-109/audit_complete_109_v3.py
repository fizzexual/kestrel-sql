"""Pure complete candidate provenance, recovery and every fixed performance gate."""
from pathlib import Path
import contextlib, hashlib, io, json, re, statistics, sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import audit_native_109 as native
import audit_preflight_109 as recovery
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def inv(p):return {f.relative_to(p).as_posix():sha(f) for f in p.rglob('*') if f.is_file()}
def audit(w):
 policy=load(w/'policy.json');assert policy['trial']==109 and policy['supported']=='0.3.16' and policy['candidate_package_version']=='0.3.17'
 assert sha(w/'policy.json')==load(w/'declaration-proof.json')['policy_sha256']
 build=load(w/'build-proof-v1.json');prep=load(w/'preparation-proof.json')
 assert build['complete'] and build['fresh_native_test_executions']==724 and build['strict_lint_modes']==5
 assert len(build['records'])==16 and sum(r.get('tests_passed',0) for r in build['records'])==724
 assert len({r['target'] for r in build['records'] if r['step'].endswith('-artifacts')})==3
 assert inv(w/'source')==inv(w/'source-v1')==prep['candidate']==build['candidate']
 assert inv(w/'baseline')==inv(w/'baseline-v1')==prep['baseline']==build['baseline']
 assert sorted(n for n,h in policy['baseline_source'].items() if build['baseline'][n]!=h)==['Cargo.toml']
 assert set(build['baseline'])==set(policy['baseline_source'])
 assert sorted(n for n,h in policy['candidate_source'].items() if build['candidate'][n]!=h)==['Cargo.toml','src/archive.rs']
 assert set(build['candidate'])-set(policy['candidate_source'])=={'tests/adaptive_filter_109.rs'}
 assert build['candidate']['src/archive.rs']==prep['new_archive_sha256']
 assert build['candidate']['src/adaptive_live_105.rs']==policy['candidate_source']['src/adaptive_live_105.rs']
 assert prep['all_original_archive_line_endings_preserved']
 lock=(w/'source/Cargo.lock').read_bytes();sep=b'\r\n' if b'\r\n' in lock else b'\n';old=b'name = "kestrel-sql"'+sep+b'version = "0.3.16"';new=b'name = "kestrel-sql"'+sep+b'version = "0.3.17"'
 assert lock.count(new)==1 and lock.replace(new,old)==(w/'baseline/Cargo.lock').read_bytes()
 cargo=(w/'source/Cargo.toml').read_text();assert 'version = "0.3.17"' in cargo and 'adaptive-collection = ["adaptive-collection-105"]' in cargo
 assert 'adaptive-engine = ["adaptive-collection", "adaptive-filter"]' in cargo
 assert 'adaptive-filter = ["adaptive-filter-109"]' in cargo
 assert len(build['records'])==16
 for r in build['records']:
  assert r['returncode']==0 and '--offline' in r['argv'] and '--locked' in r['argv'] and sha(w/r['log'])==r['log_sha256']
  if 'tests_passed' in r:assert r['tests_passed']==sum(map(int,re.findall(r'test result: ok\. (\d+) passed;', (w/r['log']).read_text())))
  if r['step'].endswith('-lint'):assert r['argv'][-3:]==['--','-D','warnings']
 assert inv(w/'binaries-v2')==build['binaries']
 for name in ['baseline','candidate']:
  for binary in (w/'binaries-v2'/name).glob('*.exe'):assert b'KESTREL_FAULT_POINT' not in binary.read_bytes() and b'KESTREL_LIVE_PAUSE' not in binary.read_bytes()
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
 with contextlib.redirect_stdout(io.StringIO()): n=native.audit(w)
 assert n==load(w/'native-audit.json') and n['correctness_passed'] and not n['performance_qualified']
 assert (n['identity_failed'],n['candidate_guards_failed'],n['goals_failed'])==(27,8,1)
 assert len(n['goals'])==24 and sum(g['workload'].startswith('small') for g in n['goals'])==12
 decision=load(w/'native-rejection-decision.json')
 assert decision['all252_service_cases_unstarted']==policy['service_cases'] and decision['service_correctness_or_performance_not_tested']
 assert sha(w/'native-audit.json')==decision['native_audit_sha256'] and sha(w/'native-profile-proof.json')==decision['profile_sha256']
 controlled=[]
 for goal in n['goals']:
  control=next(c for c in n['controls'] if all(c[k]==goal[k] for k in ['scope','workload','metric']))
  if goal['passed'] and control['passed']: controlled.append({k:goal[k] for k in ['scope','workload','metric','AA','CA']})
 assert len(controlled)==20 and controlled==decision['individually_controlled_goal_results']
 for name in ['paired-service.json','service-fixtures','raw-samples','service-audit.json']: assert not (w/name).exists()
 for case in load(w/'paired-native.json')['cases']:
  if case['kind']=='live' and case['variant']=='candidate': assert case['result_summary']['adaptive']['max_selected_delay_ns']<=100_000
 assert profile_replay(w)==load(w/'native-profile-proof.json')
 invocation=load(w/'native-audit-invocation-v2-proof.json')
 assert invocation['first_audit_invocation_actual_exit']==1 and invocation['corrected_actual_exit']==0
 assert invocation['no_auditor_source_or_gate_change'] and invocation['zero_native_or_timer_reruns']
 assert sha(w/'audit_native_109.py')==invocation['auditor_source_sha256']
 assert sha(w/'audit-native-109.log')==invocation['failed_invocation_log_sha256']
 assert sha(w/'audit-native-109-v2.log')==invocation['corrected_log_sha256']
 failed=(w/'audit-native-109.log').read_text()
 assert 'IndexError: list index out of range' in failed and "w=Path(sys.argv[1])" in failed
 expected=policy['native_cases'];bad=[dict(c) for c in load(w/'paired-native.json')['cases']];bad[0]['variant']=bad[1]['variant']
 try: native.check_order(bad,expected,policy['native_configs'])
 except AssertionError: order_invalid_rejected=True
 else: raise AssertionError('corrupt order control accepted')
 return {'complete':True,'correctness_passed':True,'native_correctness_passed':True,'supported':'0.3.16','candidate':'0.3.17','fresh_tests':724,'strict_lints':5,
  'source_derivation_and_normal_artifacts_exact':True,'recovery':preflight,'excluded_smokes_replayed':True,'invalid_balanced_order_rejected':order_invalid_rejected,
  'native':n,'service':{'unstarted_cases':252,'all_specs':policy['service_cases'],'correctness_tested':False,'performance_tested':False},
  'failed_auditor_invocation_retained_source_and_gates_exact':True,
  'performance_qualified':False,'release017_qualified':False,'rejected_at_mandatory_complete_native_gates':True,
  'every_declared_full_and_half_native_control_guard_and24_goal_recomputed':True,'no_Native_timer_or_existing_file_write_during_replay':True,
  'physical_power_loss_and_resource_exhaustion_not_tested':True,'fresh_competitor_or_universal_benchmark_claim':False}

def encoded(v): return (json.dumps(v,indent=2)+'\n').encode()

def profile_replay(w):
 audit=load(w/'native-audit.json');report=load(w/'paired-native.json')
 assert audit['complete'] and audit['correctness_passed'] and report['complete'] and len(report['cases'])==324
 assert encoded(report)==(w/'paired-native.json').read_bytes()
 initial=dict(report);initial.update(complete=False,cases=[]);initial.pop('completed_utc');initial.pop('unstarted_case_indices')
 journal=b''.join((json.dumps(c,separators=(',',':'))+'\n').encode() for c in report['cases'])
 assert journal==(w/'native-case-journal.jsonl').read_bytes()
 progress=[]
 for i,c in enumerate(report['cases']):
  label=f"{c['index']:03d}-r{c['round']:02d}-{c['name']}-{c['variant']}"
  progress.append({'completed':i+1,'total':324,'last_label':label,'actual_owned_exit0':True})
 assert encoded(progress[-1])==(w/'native-progress.json').read_bytes()
 profiles=[]
 for config in load(w/'policy.json')['native_configs']:
  if config['kind']!='live':continue
  for variant in ['baseline_a','baseline_b','candidate']:
   cases=[c for c in report['cases'] if c['name']==config['name'] and c['variant']==variant]
   stats=[c['result_summary']['ingest'] for c in cases];phases=[c['result_summary']['adaptive'] for c in cases]
   profiles.append({'workload':config['name'],'variant':variant,'all_case_indices':[c['index'] for c in cases],
    'median_ingest_fields':{k:statistics.median(s[k] for s in stats) for k,v in stats[0].items() if isinstance(v,(int,float)) and not isinstance(v,bool)},
    'median_adaptive_fields':None if phases[0] is None else {k:statistics.median(s[k] for s in phases) for k,v in phases[0].items() if isinstance(v,(int,float)) and not isinstance(v,bool)}})
 out={'complete':True,'source_report_sha256':hashlib.sha256(encoded(report)).hexdigest(),'final_report_bytes':len(encoded(report)),
  'aggregate_report_write_count':2,'exact_logical_aggregate_report_bytes_written':len(encoded(initial))+len(encoded(report)),
  'exact_case_journal_bytes_written':len(journal),'exact_logical_progress_report_bytes_written':sum(len(encoded(p)) for p in progress),
  'all_raw_stdout_and_stderr_bytes_saved_once':sum((w/c[k]).stat().st_size for c in report['cases'] for k in ['stdout','stderr']),
  'logical_bytes_are_not_physical_disk_IO_or_proof_of_an_exclusive_cause':True,'profiles':profiles,
  'full_and_half_small_group_metrics':[s for s in audit['summaries'] if s['workload'].startswith('small') and s['metric'] in ['p50','p95','p99','wall']],
  'full_and_half_filter_metrics':[s for s in audit['summaries'] if s['metric'].startswith('unordered_filter/')],
  'identity_failed':audit['identity_failed'],'candidate_guards_failed':audit['candidate_guards_failed'],'goals_failed':audit['goals_failed'],'performance_qualified':audit['performance_qualified'],'zero_native_or_timer_reruns':True}
 return out
