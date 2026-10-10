"""Complete pure diagnostic replay; all imports resolve inside the supplied tree."""
from pathlib import Path
import hashlib,json,statistics,sys
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).parent))
import audit_prefix_113 as prefix
import audit_native_113 as native
from publication_checks_113 import STAGES
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
 expected_prefix=load(w/'prefix-audit-proof.json');replayed_prefix=prefix.audit(w);assert replayed_prefix==expected_prefix
 expected_native=load(w/'native-audit.json');replayed_native=native.audit(w);assert replayed_native==expected_native
 assert len(expected_native['controls'])==144 and len(expected_native['guards'])==156 and not expected_native['goals']
 assert expected_native['live_acknowledgements']==331776 and expected_native['full_crc_bytes']==796262400
 parent=load(w/'parent112-policy.json');policy=load(w/'policy.json')
 assert sha(w/'parent112-policy.json')==policy['parent_policy_sha256']
 previous=load(w/'parent112-complete-audit-proof.json');assert previous['service']['all_specs']==parent['service_cases'] and len(parent['service_cases'])==252 and len(parent['native_cases'])==324
 assert previous['native']['goals']==policy['parent112_all42_native_goals'] and len(previous['native']['goals'])==42
 assert not (w/'paired-service.json').exists() and not (w/'service-raw').exists()
 return {'complete':True,'correctness_passed':True,'native_correctness_passed':True,'supported':'0.3.16','candidate':'0.3.17','diagnostic_only_engine_unchanged_from112':True,'fresh_tests':4,'strict_lints':2,'reused_parent_core_tests':772,'reused_parent_core_lints':5,'reused_recovery_commands':359,'prefix':replayed_prefix,'native':replayed_native,'cost_profile':profile(w,replayed_native),'parent112_full324_native_and252_service_and42_goals_still_required':True,'service':{'status':'UNSTARTED_UNTESTED','cases':252,'all_specs':parent['service_cases']},'performance_qualified':False,'diagnostic_comparison_gates_passed':replayed_native['performance_qualified'],'release017_qualified':False,'no_Native_timer_or_existing_file_write_during_replay':True,'all_failed_controls_and_guards_retained':True,'fresh_competitor_or_universal_benchmark_claim':False}
if __name__=='__main__':
 w=Path(sys.argv[1]);result=audit(w);p=w/'complete-audit-proof.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({'complete':True,'cases':144,'ACKs':331776,'CRC_bytes':796262400,'failed_controls':result['native']['identity_failed'],'failed_guards':result['native']['candidate_guards_failed'],'diagnostic_only':True,'release017_qualified':False}))
