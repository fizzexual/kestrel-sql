"""Complete pure trial116 replay; imports must resolve within the supplied tree."""
from pathlib import Path
import contextlib,hashlib,io,json,statistics,sys
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).parent))
import audit_prefix_116 as prefix
import audit_native_116_v2 as native
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def encoded(v):return (json.dumps(v,indent=2)+'\n').encode()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
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
  'full_and_half_replay_metrics':[s for s in audit['summaries'] if s['workload']=='identified-replay'],
  'full_and_half_grouped_metrics':[s for s in audit['summaries'] if s['metric'].startswith('grouped/')],
  'identity_failed':audit['identity_failed'],'candidate_guards_failed':audit['candidate_guards_failed'],'goals_failed':audit['goals_failed'],'performance_qualified':audit['performance_qualified'],'zero_native_or_timer_reruns':True}
 return out

def audit(w):
 assert w.resolve()==w and all(Path(m.__file__).resolve().is_relative_to(w) for m in [prefix,native])
 with contextlib.redirect_stdout(io.StringIO()):
  first=prefix.audit(w);n=native.audit(w)
 assert first==load(w/'prefix-audit-proof.json') and n==load(w/'native-audit.json')
 assert first['fresh_tests']==796 and first['strict_lints']==5 and first['negative_conservation_controls']==6
 assert n['complete'] and n['correctness_passed'] and not n['performance_qualified']
 assert (n['cases'],n['identity_failed'],n['candidate_guards_failed'],n['goals_failed'])==(324,21,5,3)
 assert n['live_acknowledgements']==479232 and n['full_crc_bytes']==2921356800
 assert len(n['controls'])==153 and len(n['guards'])==len(n['summaries'])==171 and len(n['goals'])==42
 policy=load(w/'policy.json');decision=load(w/'native-rejection-decision.json');keys=['scope','workload','metric'];verified=[];robust=[]
 assert sha(w/'policy.json')==decision['policy_sha256']==load(w/'declaration-proof.json')['policy_sha256']
 assert sha(w/'native-audit.json')==decision['native_audit_sha256']
 for goal in n['goals']:
  c=next(c for c in n['controls'] if all(c[k]==goal[k] for k in keys))
  if c['passed'] and goal['passed']:verified.append({k:goal[k] for k in [*keys,'AA','CA','before_median','after_median']})
 for workload,metric in sorted({(g['workload'],g['metric']) for g in n['goals']}):
  rows=[g for g in verified if g['workload']==workload and g['metric']==metric]
  if {g['scope'] for g in rows}==set(policy['scopes']):robust.append({'workload':workload,'metric':metric,'scopes':rows})
 assert len(robust)==7 and robust==decision['all_scope_controlled_goal_results'] and verified==decision['individually_controlled_goal_results']
 assert len(policy['service_cases'])==252 and decision['all252_service_cases_unstarted']==policy['service_cases']
 for name in ['paired-service.json','service-fixtures','raw-samples','service-audit.json']:assert not (w/name).exists()
 profile=profile_replay(w);assert profile==load(w/'native-profile-proof.json')
 build=load(w/'build-proof-v2.json');expected=['benchmark-shutdown','benchmark-shutdown','benchmark-shutdown','benchmark-shutdown','benchmark-shutdown,adaptive-engine','benchmark-shutdown,adaptive-engine','benchmark-shutdown,adaptive-engine,fault-injection','benchmark-shutdown,adaptive-engine,fault-injection']
 tests=[r for r in build['records'] if r['argv'][1]=='test'];assert len(tests)==8
 assert [r['argv'][r['argv'].index('--features')+1] for r in tests]==expected
 binaries=[r for r in build['records'] if r['argv'][1]=='build'];assert len(binaries)==3
 assert [r['argv'][r['argv'].index('--features')+1] for r in binaries]==[expected[0],expected[4],expected[6]]
 observation=load(w/'controller-exit-observation.json');assert observation['all_current116_controller_API_exits_observed'] and all(observation[k]['actual_tool_exit_code']==0 for k in ['build','recovery_controller','excluded_smoke_controller','native_controller','native_audit'])
 return {'complete':True,'correctness_passed':True,'native_correctness_passed':True,'fresh_tests':796,'strict_lints':5,'fresh_recovery_commands':359,'prefix':first,'native':n,'profile':profile,'all_scope_controlled_goal_results':robust,'service':{'status':'UNSTARTED_UNTESTED','cases':252,'all_specs':policy['service_cases']},'controller_observation':observation,'actual_build_features_crosschecked':True,'historical_policy_features_field_is_inherited_context_actual_build_argv_authoritative':True,'all42_goals_all153_controls_all171_guards_recomputed':True,'performance_qualified':False,'release017_qualified':False,'supported':'0.3.16','candidate':'0.3.17','zero_Native_or_timer_reruns':True,'all_failures_and_originals_retained':True,'candidate_vs_supported016_not_isolated116_vs112_effect':True,'fresh_competitor_or_universal_benchmark_claim':False}
if __name__=='__main__':
 w=Path(sys.argv[1]);result=audit(w);p=w/'complete-audit-proof.json';assert not p.exists();p.write_bytes(encoded(result));print(json.dumps({'complete':True,'cases':324,'fresh_tests':796,'failed_controls':21,'failed_guards':5,'failed_goals':3,'robust_goals':7,'service_unstarted':252,'release017_qualified':False}))
