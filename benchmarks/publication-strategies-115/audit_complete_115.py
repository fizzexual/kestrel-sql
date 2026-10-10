"""Complete pure115 replay; compares existing experimental serial112 and concurrent114."""
from pathlib import Path
import contextlib,hashlib,io,json,statistics,sys
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).parent))
import audit_prefix_115 as prefix
import audit_native_115 as native
from publication_checks_115 import STAGES
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def profile(w,n):
 cases=load(w/'paired-native.json')['cases'];policy=load(w/'policy.json');records={x['index']:x for x in n['stage_records']};rows=[]
 for config in policy['native_configs']:
  for variant in ['baseline_a','baseline_b','candidate']:
   cohort=[records[c['index']] for c in cases if c['name']==config['name'] and c['variant']==variant]
   assert len(cohort)==12;ack_count=config['producers']*config['batches']
   total=[c['publication_stage_total_ms'] for c in cohort]
   row={'workload':config['name'],'variant':variant,'ACKs_per_case':ack_count,'stage_total_median_ms':statistics.median(total),'stage_total_median_ms_per_ACK':statistics.median(t/ack_count for t in total),'durable_groups_median':statistics.median(c['durable_groups'] for c in cohort),'final_compactions_median':statistics.median(c['post_join_compactions'] for c in cohort),'stages':[]}
   for stage in STAGES:
    amounts=[c['profile'][stage]['total_ms'] for c in cohort]
    controlled=next(r for r in n['summaries'] if r['workload']==config['name'] and r['scope']=='full' and r['metric']=='stage/'+stage+'/ms_per_ACK')
    halves=[r for r in n['controls'] if r['workload']==config['name'] and r['metric']==controlled['metric']]
    row['stages'].append({'stage':stage,'median_total_ms':statistics.median(amounts),'median_ms_per_ACK':statistics.median(t/ack_count for t in amounts),'median_share_percent':statistics.median(a/t*100 for a,t in zip(amounts,total)),'full_AA':controlled['AA'],'full_CA':controlled['CA'],'controls_pass_full_and_both_halves':all(r['passed'] for r in halves),'max_observed_ms':max(c['profile'][stage]['max_ms'] for c in cohort),'all12_round_totals_ms':amounts})
   rows.append(row)
 return {'rows':rows,'stage_includes_publication_prepare_and_final_compaction_maintenance':True,'aggregate_cost_not_exclusive_CPU_physical_IO_or_ACK_tail_causality':True,'no_new_engine_change_or_release_claim':True}
def audit(w):
 assert w.resolve()==w and all(Path(m.__file__).resolve().is_relative_to(w) for m in [prefix,native])
 first=prefix.audit(w);assert first==load(w/'prefix-audit-proof.json')
 with contextlib.redirect_stdout(io.StringIO()):n=native.audit(w)
 assert n==load(w/'native-audit.json') and n['complete'] and n['correctness_passed']
 assert (n['cases'],n['identity_failed'],n['candidate_guards_failed'],n['goals_failed'])==(144,12,39,0)
 assert len(n['controls'])==144 and len(n['guards'])==len(n['summaries'])==156 and not n['goals']
 assert n['live_acknowledgements']==331776 and n['full_crc_bytes']==796262400
 policy=load(w/'policy.json');p112=load(w/'parent112-policy.json');p114=load(w/'parent114-policy.json');required=policy['parent_release_requirements']
 assert p112['service_cases']==p114['service_cases'] and len(p112['native_cases'])==len(p114['native_cases'])==324 and len(p114['service_cases'])==252
 assert len(required['serial112_native_all42_goals'])==len(required['concurrent114_native_all42_goals'])==42
 for name in ['paired-service.json','service-fixtures','raw-samples','service-audit.json']:assert not (w/name).exists()
 observation=load(w/'controller-exit-observation.json');assert observation['native_controller']['actual_tool_exit_code']==observation['native_audit']['actual_tool_exit_code']==0 and observation['build']['actual_tool_exit_code']==0
 rows=[]
 for config in policy['native_configs']:
  for metric in ['p50','p95','p99','wall']:
   cohort=[r for r in n['summaries'] if r['workload']==config['name'] and r['metric']==metric]
   assert len(cohort)==3
   controls=all(.95<=r['AA']<=1.05 for r in cohort)
   rows.append({'workload':config['name'],'metric':metric,'full':next(r for r in cohort if r['scope']=='full'),'all_scopes':cohort,'AA_pass_full_and_both_halves':controls,'candidate_faster_full_and_both_halves_with_passing_AA':controls and all(r['CA']<1 for r in cohort),'guard_pass_full_and_both_halves':all(r['CA']<=1.05 for r in cohort)})
 return {'complete':True,'correctness_passed':True,'native_correctness_passed':True,'diagnostic_only_existing112_and114_engines_unchanged':True,'baseline_is_experimental_serial112_not016':True,'all_three_variants017_adaptive_true':True,'fresh_tests':4,'strict_lints':2,'reused_parent_core_tests':772,'reused_concurrent114_core_tests':796,'reused_parent_core_lints_each':5,'reused_recovery_commands_each':359,'prefix':first,'native':n,'cost_profile':profile(w,n),'latency_comparison':rows,'concurrent_stage_durations_overlap_sum_is_aggregate_cost_not_serial_wall_or_exclusive_cause':True,'both_parents_complete324_native252_service_and_all42_release_goals_unchanged':True,'service':{'status':'UNSTARTED_UNTESTED','cases':252,'all_specs':p114['service_cases']},'controller_observation':observation,'performance_qualified':False,'diagnostic_comparison_gates_passed':n['performance_qualified'],'release017_qualified':False,'supported':'0.3.16','no_Native_timer_or_existing_file_write_during_replay':True,'all_failed_controls_guards_and_raw_retained':True,'fresh_competitor_or_universal_benchmark_claim':False}
if __name__=='__main__':
 w=Path(sys.argv[1]);result=audit(w);p=w/'complete-audit-proof.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({'complete':True,'cases':144,'ACKs':331776,'CRC_bytes':796262400,'failed_controls':12,'failed_guards':39,'diagnostic_only':True,'release017_qualified':False}))
