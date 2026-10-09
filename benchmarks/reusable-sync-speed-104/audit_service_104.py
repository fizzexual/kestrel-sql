"""Loss-aware original gates, complete ACK-row CRC and graceful lifecycle, zero Native reruns."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,itertools,json,math,random,sys
W=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-104')
sys.dont_write_bytecode=True;sys.path.insert(0,str(W));sys.path.insert(0,str(W/'harness'))
import audit_service_095 as a
from outcomes_098 import outcomes,negatives
from stress_compare import make_task
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify_order(cases,policy):
 assert len(cases)==len(policy['cases'])==144
 for index,(c,s) in enumerate(zip(cases,policy['cases'])):
  assert c['case_index']==s['index']==index
  for n in ['round','block','position','profile','variant','binary']:assert c[n]==s[n]
  assert c['offered_rps']==s['rate'] and c['scheduled_seconds']==s['seconds']
 permutations=sorted(itertools.permutations(['baseline_a','baseline_b','candidate']))
 for profile in ['read','write']:
  for rounds in [list(range(1,25)),list(range(1,13)),list(range(13,25))]:
   orders=[tuple(c['variant'] for c in cases if c['round']==r and c['profile']==profile) for r in rounds]
   assert sorted(orders)==sorted(permutations*(len(rounds)//6))
def lifecycle(case):
 records=load(W/'service-fixtures'/Path(case['fixture']).name/'bridge-lifecycle.json');assert records==case['lifecycle'] and len(records)==2
 for r in records:
  assert r['returncode']==0 and r['graceful_background_joined'] and not r.get('hard_failure') and not r.get('owned_child_killed_after_failure')
  assert r['process_identity']['pid']==r['pid'];stats=r['final']['ingest'];assert stats['writer_stopped'] and not stats['writer_poisoned'] and stats['queued_payload_bytes']==stats['maintenance_errors']==0
  assert r['final']['event']=='graceful_background_joined' and 0<=r['final']['shutdown_ms']<=5000
  p=W/'service-fixtures'/Path(case['fixture']).name;events=[json.loads(x) for x in (p/r['stdout']).read_bytes().splitlines() if x.strip()]
  assert len(events)==2 and events[0]['version']=='0.3.16' and events[1]==r['final'] and (p/r['stdin']).read_bytes()==b'shutdown\n'
 assert records[0]['physical_inventory_before_cold']==case['archive_inventory_bytes'] and records[1]['argv'][2]=='0'
 assert sum(records[0]['physical_inventory_before_cold'].values())==case['archive_disk_bytes']
 return {'case_index':case['case_index'],'native_processes':2,'actual_background_joined_exit0':True,'shutdown_ms_descriptive_only':[r['final']['shutdown_ms'] for r in records]}
def main():
 policy=load(W/'service-policy.json');original=load(W/'policy.json');report=load(W/'paired-service.json')
 assert {k:policy[k] for k in original}==original and sha(W/'policy.json')=='8e06a5d8d0ff0c117f140743a200f35c650753dc610ca879080f1fb10f331c64'
 assert policy['original_pre_build_policy_sha256']==sha(W/'policy.json') and report['complete'] and not report['failed_cases']
 assert report['policy_sha256']==sha(W/'service-policy.json') and report['freeze_sha256']==sha(W/'timing-freeze.json')
 assert all(sha(W/n)==h for n,h in load(W/'timing-freeze.json')['sha256'].items());verify_order(report['cases'],policy);validation=negatives()
 totals={n:0 for n in ['offered','successful','lost','queue_dropped','queue_expired','executed_failed','acknowledged_batches','full_crc_bytes']};native=[];conservation=[];stalls=[];resources=[];joined=[]
 for c in report['cases']:
  p=W/c['raw_samples_file'];assert sha(p)==c['raw_samples_sha256']
  with gzip.open(p,'rt',encoding='utf-8') as f:raw=[json.loads(x) for x in f]
  good,counts=outcomes(c,raw);conservation.append(counts);assert all(s['operation'] in ['query','append'] for s in raw)
  rng=random.Random(20261006);intended={seq:make_task(rng,seq,policy['base_rows'],c['profile'])[1] for seq in range(counts['offered'])}
  assert all(s['operation']==intended[s['sequence']] for s in raw)
  counts['missing_intended_operations_reconstructed_not_executed']=[{'sequence':s,'operation':intended[s]} for s in counts['missing_sequences_reconstructed_from_exact_offer_range']]
  start=c['arrival_start_monotonic_ns'];end=start+int(c['scheduled_seconds']*1e9);within=sum(s['finished_ns']<=end for s in good)
  assert within==c['completed_in_arrival_window'] and within/c['scheduled_seconds']==c['successful_rps_in_arrival_window'] and len(good)/c['including_drain_seconds']==c['successful_rps_including_drain']
  assert sum(s['latency_ms']<=100 for s in good)/counts['offered']==c['offered_fraction_successful_within_100ms']
  for s in raw:
   assert s['arrival_ns']==start+int(s['sequence']*1e9/c['offered_rps']) and math.isclose(s['latency_ms'],(s['finished_ns']-s['arrival_ns'])/1e6,abs_tol=1e-12)
   assert s['service_ms']>=0 and s['latency_ms']+1e-9>=s['service_ms']
   if s['operation']=='append' and s['ok']:
    r=s['append_receipt'];assert r['affected']==100 and not r['duplicate'] and r['generation']>1
   elif s['operation']=='query':assert s['append_receipt'] is None
   if s['latency_ms']>100:stalls.append({'case_index':c['case_index'],**s})
  for op in ['overall','query','append']:
   chosen=good if op=='overall' else [s for s in good if s['operation']==op];m=c['latency_ms'] if op=='overall' else c['operation_latency_ms'][op];values=[s['latency_ms'] for s in chosen]
   for label,q in [('p50',.5),('p95',.95),('p99',.99)]:assert m[label]==a.quantile(values,q)
   assert m['max']==max(values,default=None)
   if op!='overall':assert m['successful']==len(chosen) and m['service_p99']==a.quantile([s['service_ms'] for s in chosen],.99)
  acked=sum(s['operation']=='append' for s in good);assert acked==c['write_successes'] and len(good)-acked==c['read_successes'];rec=c['reconciliation']
  assert rec['acknowledged_batches']==rec['published_batches']==acked and rec['unacknowledged_but_committed']==0 and rec['all_acknowledged_batches_present'] and rec['batch_atomicity_and_sums']
  assert rec['rows']==policy['base_rows']+acked*100 and rec['numpy_reference_windows']==20 and rec['full_kestrel_scrub']['verified_bytes']==rec['rows']*24
  ingest=c['live_state_before_reopen']['ingest'];assert not ingest['writer_poisoned'] and ingest['maintenance_errors']==ingest['queued_payload_bytes']==0
  native.append(a.verify_native_store(W,c,raw,policy['base_rows']));resources.append({'case_index':c['case_index'],**a.trace_check(c,raw,policy['base_rows'])});joined.append(lifecycle(c))
  for n in ['offered','successful','lost','queue_dropped','queue_expired','executed_failed']:totals[n]+=counts[n]
  totals['acknowledged_batches']+=acked;totals['full_crc_bytes']+=rec['full_kestrel_scrub']['verified_bytes']
  print(json.dumps({'audited':c['case_index']+1,'total':144,'lost':counts['lost'],'full_current_store_crc_passed':True,'graceful_joins':2}),flush=True)
 assert totals['offered']==policy['expected_offers']==1872000 and totals['lost']==totals['offered']-totals['successful']
 # The original 095 scope function uses the unchanged 093 literal; only aliases adapt.
 gate_policy={'normal_gates':policy['original_093_gate_literal'],'configs':[['read',2000,8],['write',500,20]]};family={'name':'async20every8_sync104','stage':'normal'}
 scopes=[a.scope(report['cases'],gate_policy,family,name,rounds) for name,rounds in [('full',list(range(1,25))),('half_1',list(range(1,13))),('half_2',list(range(13,25)))]]
 goals=[]
 for s in scopes:
  row=next(r for r in s['summaries'] if r['profile']=='write');ratios=row['comparisons']['primary_candidate_over_a']['paired_ratios']
  goals.extend([{'scope':s['scope'],'criterion':'write_overall_p99<=0.95','ratio':ratios['overall']['median'],'passed':ratios['overall']['median']<=.95},{'scope':s['scope'],'criterion':'write_append_p99<=0.90','ratio':ratios['append']['median'],'passed':ratios['append']['median']<=.90}])
 result={'trial':104,'correctness_passed':True,'loss_aware_raw_audit_passed':True,'cases':144,**totals,'scopes':scopes,'identity_failed_total':sum(s['identity_failed'] for s in scopes),'candidate_failed_total':sum(s['candidate_failed'] for s in scopes),'goal_checks':goals,'goals_failed':sum(not g['passed'] for g in goals),'scoped_candidate_qualified':all(s['passed'] for s in scopes) and all(g['passed'] for g in goals),'conservation':conservation,'native_store_audits':native,'numpy_windows':2880,'independent_complete_ACK_row_and_CRC_bytes':sum(n['full_data_crc_bytes'] for n in native),'resources':resources,'lifecycle':joined,'events_over_100ms':len(stalls),'all_events_over_100ms':stalls,'validation':validation,'no_native_launches_or_timing_reruns':True,'declared104_policy_and_original093_service_gates_unchanged':True,'no_full_release_all_benchmark_or_competitor_claim':True,'supported':'0.3.16'}
 assert not totals['lost'] or not result['scoped_candidate_qualified'];p=W/'audit.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:result[k] for k in ['cases','offered','successful','lost','identity_failed_total','candidate_failed_total','goals_failed','scoped_candidate_qualified']}),flush=True);return result
if __name__=='__main__':main()
