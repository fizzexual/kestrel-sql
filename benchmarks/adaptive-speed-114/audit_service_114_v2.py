"""Complete raw loss-aware service replay and all fixed full/half gates."""
from pathlib import Path
import gzip,hashlib,itertools,json,math,random,statistics,sys
sys.dont_write_bytecode=True
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def quantile(values,q):return sorted(values)[max(0,math.ceil(len(values)*q)-1)] if values else None
def metric(c,name):
 if name=='overall':return c['latency_ms']['p99']
 if name=='rps':return c['successful_rps_in_arrival_window']
 if name=='peak':return c['post_load_diagnostic']['peak_working_set_bytes']
 if name=='disk':return c['archive_disk_bytes']
 return c['operation_latency_ms'][name]['p99']
def audit(w):
 sys.path.insert(0,str(w));sys.path.insert(0,str(w/'harness'))
 import audit_service_095 as original
 from outcomes_098 import outcomes,negatives
 from stress_compare import make_task
 policy=load(w/'policy.json');report=load(w/'paired-service.json');freeze=load(w/'timing-freeze.json')
 assert report['complete'] and not report['failed_cases'] and not report['unstarted_case_indices']
 assert report['policy_sha256']==sha(w/'policy.json') and report['freeze_sha256']==sha(w/'timing-freeze.json')
 assert all(sha(w/n)==h for n,h in freeze['files'].items());cases=report['cases'];assert len(cases)==len(policy['service_cases'])==252
 permutations=sorted(itertools.permutations(['baseline_a','baseline_b','candidate']))
 for config in policy['service_configs']:
  for rounds in [range(1,13),range(1,7),range(7,13)]:
   orders=[tuple(c['variant'] for c in cases if c['round']==r and c['workload']==config['name']) for r in rounds];assert sorted(orders)==sorted(permutations*(len(rounds)//6))
 totals={n:0 for n in ['offered','successful','lost','queue_dropped','queue_expired','executed_failed','acknowledged_batches','full_crc_bytes']};stores=[];conservation=[];stalls=[];joins=[]
 for c,spec in zip(cases,policy['service_cases']):
  assert c['case_index']==spec['index']
  for n in ['round','block','position','profile','variant','binary','name','stage']:assert c[n]==spec[n]
  assert c['workload']==spec['name'] and c['offered_rps']==spec['rate'] and c['scheduled_seconds']==spec['seconds'] and c['version']==('0.3.17' if c['variant']=='candidate' else '0.3.16')
  p=w/c['raw_samples_file'];assert sha(p)==c['raw_samples_sha256']
  with gzip.open(p,'rt',encoding='utf-8') as stream:raw=[json.loads(x) for x in stream]
  good,counts=outcomes(c,raw);conservation.append(counts)
  rng=random.Random(20261006);intended={seq:make_task(rng,seq,policy['service_base_rows'],c['profile'])[1] for seq in range(counts['offered'])}
  assert all(sample['operation']==intended[sample['sequence']] for sample in raw)
  counts['missing_intended_operations']=[{'sequence':seq,'operation':intended[seq]} for seq in counts['missing_sequences_reconstructed_from_exact_offer_range']]
  start=c['arrival_start_monotonic_ns'];end=start+int(c['scheduled_seconds']*1e9);within=sum(x['finished_ns']<=end for x in good)
  assert within==c['completed_in_arrival_window'] and within/c['scheduled_seconds']==c['successful_rps_in_arrival_window'] and len(good)/c['including_drain_seconds']==c['successful_rps_including_drain']
  assert sum(x['latency_ms']<=100 for x in good)/counts['offered']==c['offered_fraction_successful_within_100ms']
  for sample in raw:
   assert sample['arrival_ns']==start+int(sample['sequence']*1e9/c['offered_rps']) and math.isclose(sample['latency_ms'],(sample['finished_ns']-sample['arrival_ns'])/1e6,abs_tol=1e-12)
   assert math.isfinite(sample['latency_ms']) and sample['service_ms']>=0 and sample['latency_ms']+1e-9>=sample['service_ms']
   if sample['operation']=='append' and sample['ok']:receipt=sample['append_receipt'];assert receipt['affected']==100 and not receipt['duplicate'] and receipt['generation']>1
   elif sample['operation']=='query':assert sample['append_receipt'] is None
   if sample['latency_ms']>100:stalls.append({'case_index':c['case_index'],**sample})
  for op in ['overall','query','append']:
   selected=good if op=='overall' else [x for x in good if x['operation']==op];m=c['latency_ms'] if op=='overall' else c['operation_latency_ms'][op];values=[x['latency_ms'] for x in selected]
   for n,q in [('p50',.5),('p95',.95),('p99',.99)]:assert m[n]==quantile(values,q)
   assert m['max']==max(values,default=None)
   if op!='overall':assert m['successful']==len(selected) and m['service_p99']==quantile([x['service_ms'] for x in selected],.99)
  acked=sum(x['operation']=='append' for x in good);rec=c['reconciliation'];assert acked==c['write_successes'] and len(good)-acked==c['read_successes']
  assert rec['acknowledged_batches']==rec['published_batches']==acked and rec['unacknowledged_but_committed']==0 and rec['all_acknowledged_batches_present'] and rec['batch_atomicity_and_sums']
  assert rec['rows']==policy['service_base_rows']+acked*100 and rec['numpy_reference_windows']==20 and rec['full_kestrel_scrub']['verified_bytes']==rec['rows']*24
  ingest=c['live_state_before_reopen']['ingest'];assert not ingest['writer_poisoned'] and ingest['queued_payload_bytes']==ingest['maintenance_errors']==0
  phase=c['post_load_diagnostic']['adaptive']
  if c['variant']=='candidate':
   assert phase['configured_max_delay_ns']==2_000_000 and phase['max_selected_delay_ns']<=2_000_000 and phase['observed_publications']==ingest['durable_group_commits']
   assert sum(phase[k] for k in ['latency_groups','coalescing_groups','pressure_groups'])==ingest['collected_groups']
  else:assert phase is None and ingest['group_delay_ns']==0
  original.trace_check(c,raw,policy['service_base_rows']);stores.append(original.verify_native_store(w,c,raw,policy['service_base_rows']))
  d=w/'service-fixtures'/Path(c['fixture']).name;lifecycle=load(d/'bridge-lifecycle.json');assert lifecycle==c['lifecycle'] and len(lifecycle)==2
  for record in lifecycle:
   assert record['returncode']==0 and record['graceful_background_joined'] and not record.get('hard_failure') and not record.get('owned_child_killed_after_failure')
   final=record['final'];assert final['ingest']['writer_stopped'] and not final['ingest']['writer_poisoned'] and final['ingest']['queued_payload_bytes']==final['ingest']['maintenance_errors']==0
   assert 0<=final['shutdown_ms']<=5000 and (d/record['stdin']).read_bytes()==b'shutdown\n'
   events=[json.loads(x) for x in (d/record['stdout']).read_bytes().splitlines() if x.strip()];assert len(events)==2 and events[0]['version']==c['version'] and events[1]==final
  assert lifecycle[0]['physical_inventory_before_cold']==c['archive_inventory_bytes'] and sum(c['archive_inventory_bytes'].values())==c['archive_disk_bytes'] and lifecycle[1]['argv'][2]=='0'
  joins.append({'case_index':c['case_index'],'actual_owned_background_joins_exit0':2})
  for n in ['offered','successful','lost','queue_dropped','queue_expired','executed_failed']:totals[n]+=counts[n]
  totals['acknowledged_batches']+=acked;totals['full_crc_bytes']+=rec['rows']*24
  print(json.dumps({'service_audited':c['case_index']+1,'of':252,'lost':counts['lost']}),flush=True)
 assert totals['lost']==totals['offered']-totals['successful'] and totals['offered']==sum(x['rate']*x['seconds'] for x in policy['service_cases'])
 controls=[];guards=[];goals=[];summaries=[];base=policy['original_standard_service_gates'];capacity=policy['capacity_gates']
 for scope,rounds in policy['scopes'].items():
  for config in policy['service_configs']:
   by={v:sorted([c for c in cases if c['round'] in rounds and c['workload']==config['name'] and c['variant']==v],key=lambda c:c['round']) for v in ['baseline_a','baseline_b','candidate']};assert all(len(values)==len(rounds) for values in by.values())
   ratios={};values={}
   for name in ['overall','query','append','rps','peak','disk']:
    values[name]={v:[metric(c,name) for c in group] for v,group in by.items()}
    if values[name]['baseline_a'][0] is None:continue
    assert all(x is not None and x>0 for group in values[name].values() for x in group)
    ratios[name]={'AA':statistics.median(b/a for a,b in zip(values[name]['baseline_a'],values[name]['baseline_b'])),'CA':statistics.median(b/a for a,b in zip(values[name]['baseline_a'],values[name]['candidate']))}
   peak_aa=statistics.median(metric(b,'peak')-metric(a,'peak') for a,b in zip(by['baseline_a'],by['baseline_b']));peak_ca=statistics.median(metric(b,'peak')-metric(a,'peak') for a,b in zip(by['baseline_a'],by['candidate']))
   disk_ca=statistics.median(metric(b,'disk')-metric(a,'disk') for a,b in zip(by['baseline_a'],by['candidate']))
   loss={v:sum(c['unsuccessful_or_unexecuted'] for c in group) for v,group in by.items()};offers={v:sum(c['offered_operations'] for c in group) for v,group in by.items()};fractions={v:loss[v]/offers[v] for v in by}
   within100={v:statistics.median(c['offered_fraction_successful_within_100ms'] for c in group) for v,group in by.items()}
   lo,hi=base['identity_p99_and_rps_range'];aa={name:(lo<=ratio['AA']<=hi) for name,ratio in ratios.items() if name in ['overall','query','append','rps']}
   ca={name:ratio['CA']<=base['candidate_p99_max'] for name,ratio in ratios.items() if name in ['overall','query','append']};ca['rps']=ratios['rps']['CA']>=base['candidate_window_rps_min']
   lo,hi=base['identity_peak_working_set_ratio_range'];aa['peak_ratio']=lo<=ratios['peak']['AA']<=hi;aa['peak_difference']=abs(peak_aa)<=base['identity_peak_working_set_absolute_difference_max_bytes']
   lo,hi=base['identity_archive_disk_ratio_range'];aa['disk_ratio']=lo<=ratios['disk']['AA']<=hi
   ca.update(peak_ratio=ratios['peak']['CA']<=base['candidate_peak_working_set_ratio_max'],peak_difference=peak_ca<=base['candidate_peak_working_set_difference_max_bytes'],disk_ratio=ratios['disk']['CA']<=base['candidate_archive_disk_ratio_max'],disk_extra_bytes=disk_ca<=base['candidate_archive_disk_extra_bytes_max'])
   if config['stage']=='standard':aa['zero_loss']=loss['baseline_a']==loss['baseline_b']==0;ca['zero_loss']=loss['candidate']==0
   else:
    aa['lost_fraction_difference']=abs(fractions['baseline_a']-fractions['baseline_b'])<=capacity['identity_lost_fraction_absolute_difference_max'];aa['offered_within100ms_difference']=abs(within100['baseline_a']-within100['baseline_b'])<=capacity['identity_offered_fraction_within100ms_difference_max']
    ca['lost_fraction_nonregression']=fractions['candidate']-fractions['baseline_a']<=capacity['candidate_lost_fraction_over_primary_baseline_max'];ca['offered_within100ms_nonregression']=within100['baseline_a']-within100['candidate']<=capacity['candidate_offered_fraction_within100ms_under_primary_baseline_max']
    if not loss['baseline_a'] and not loss['baseline_b']:ca['zero_loss_with_zero_loss_baselines']=loss['candidate']==0
   row={'scope':scope,'workload':config['name'],'ratios':ratios,'median_values':{name:{v:statistics.median(nums) if nums[0] is not None else None for v,nums in by_value.items()} for name,by_value in values.items()},'loss':loss,'offered':offers,'lost_fractions':fractions,'within100ms_fractions':within100,'identity_checks':aa,'candidate_guards':ca,'all_case_indices':{v:[c['case_index'] for c in group] for v,group in by.items()}};summaries.append(row)
   controls.extend({'scope':scope,'workload':config['name'],'criterion':name,'passed':passed} for name,passed in aa.items());guards.extend({'scope':scope,'workload':config['name'],'criterion':name,'passed':passed} for name,passed in ca.items())
 return {'complete':True,'correctness_passed':True,'cases':252,**totals,'summaries':summaries,'identity_failed':sum(not x['passed'] for x in controls),'candidate_guards_failed':sum(not x['passed'] for x in guards),'goals_failed':sum(not x['passed'] for x in goals),'controls':controls,'guards':guards,'goals':goals,'stores':stores,'conservation':conservation,'lifecycle':joins,'events_over100ms':stalls,'invalid_conservation_controls':negatives(),'performance_qualified':all(x['passed'] for x in controls+guards+goals),'old093_104_gates_and_rejections_unchanged':True,'capacity_relative_gates_do_not_claim_zero_loss_or_maximum_capacity':True,'no_Native_or_timer_reruns':True,'supported':'0.3.16','candidate':'0.3.17'}
if __name__=='__main__':
 w=Path(sys.argv[1]);result=audit(w);p=w/'service-audit.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:result[k] for k in ['cases','offered','lost','identity_failed','candidate_guards_failed','goals_failed','performance_qualified']}))
