"""Independently reconstruct every trial118 CSV annotation from preserved original117 JSON."""
from pathlib import Path
from collections import Counter
from bisect import bisect_left,bisect_right
import csv,gzip,hashlib,json,statistics,sys
W=Path(sys.argv[1]);BASE=W/'inputs'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def q(v,n):
 return sorted(v)[(len(v)*n+99)//100-1] if v else None
policy=load(W/'policy.json');result=load(W/'analysis.json');native=load(BASE/'paired-native.json');audit=load(BASE/'native-audit.json')
assert result['complete'] and not result['new_speed_or_release_qualification'] and result['new_engine_tests_builds_or_timers']==0
assert all(sha(BASE/n)==h for n,h in policy['all_inputs_SHA256'].items())
assert sha(W/'all-ACK-classifications.csv.gz')==result['classification_csv_sha256']
assert len(result['cases'])==216 and len(result['summaries'])==18
classes=policy['classes'];cases=[c for c in native['cases'] if c['kind']=='live'];verified=0;trailing=0
with gzip.open(W/'all-ACK-classifications.csv.gz','rt',encoding='utf-8',newline='') as f:
 reader=csv.DictReader(f)
 for case,derived in zip(cases,result['cases']):
  raw=load(BASE/case['stdout']);records=raw['raw_acknowledgements'];gens=sorted(set(r['generation'] for r in records))
  assert derived['case_index']==case['index'] and derived['round']==case['round'] and derived['variant']==case['variant'] and derived['workload']==case['name']
  gap_indices=[i for i in range(1,len(gens)) if gens[i]-gens[i-1]>1]
  def label(g):
   index=bisect_left(gens,g);prior=bisect_right(gap_indices,index)-1
   if prior<0:return 'before_first_gap'
   distance=index-gap_indices[prior]
   return 'after_gap_'+str(distance) if distance<3 else 'after_gap_3plus'
  assert gens[0]==1 and raw['cold_stats']['generation']-len(gens)==derived['unacknowledged_interior_generations']+derived['trailing_unacknowledged_generations']
  assert raw['cold_stats']['generation']-len(gens)-raw['ingest']['compactions']==derived['unobserved_final_compaction_count'] in [0,1]
  assert len(gens)==derived['unique_receipt_generations']==raw['ingest']['durable_group_commits']
  assert derived['ACKs']==len(records)
  values=[r['elapsed_ns'] for r in records];whole={k:q(values,p) for k,p in [('p50',50),('p95',95),('p99',99)]};whole['max']=max(values)
  assert whole==raw['latency_ns']==derived['whole_latency_ns']
  for record in records:
   annotation=next(reader)
   expected={'case':case['index'],'producer':record['producer'],'batch':record['batch'],'generation':record['generation'],'elapsed_ns':record['elapsed_ns'],
    'p95_tail':int(record['elapsed_ns']>=whole['p95']),'p99_tail':int(record['elapsed_ns']>=whole['p99'])}
   assert all(int(annotation[k])==v for k,v in expected.items())
   assert annotation['class']==label(record['generation']);verified+=1
  for tag in classes:
   vs=[r['elapsed_ns'] for r in records if label(r['generation'])==tag]
   expected={'ACK_count':len(vs),'p50_ns':q(vs,50),'p95_ns':q(vs,95),'p99_ns':q(vs,99),'max_ns':max(vs) if vs else None}
   assert derived['class_summary'][tag]==expected
  for metric in ['p95','p99']:
   counts=Counter(label(r['generation']) for r in records if r['elapsed_ns']>=whole[metric]);n=sum(counts.values());tail=derived['tails'][metric]
   assert tail['cutoff_ns']==whole[metric] and tail['total_ACKs_including_ties']==n
   assert tail['class_counts']=={tag:counts[tag] for tag in classes}
   assert tail['direct_after_gap_share']==counts['after_gap_0']/n
   assert tail['within_three_groups_after_gap_share']==sum(counts[tag] for tag in classes[1:4])/n
  expected_gaps=[{'previous_receipt_generation':gens[i-1],'next_receipt_generation':gens[i],'unacknowledged_generation_count':gens[i]-gens[i-1]-1,
      'next_group_ACKs':sum(r['generation']==gens[i] for r in records)} for i in gap_indices]
  assert expected_gaps==derived['gaps']
  trailing+=derived['trailing_unacknowledged_generations']>0
 assert next(reader,None) is None
assert verified==479232 and len(cases)==216
for summary in result['summaries']:
 scope=summary['scope'];rounds=range(1,13) if scope=='full' else range(1,7) if scope=='half_1' else range(7,13)
 assert summary['cases_per_variant']==len(rounds)
 for variant,actual in summary['descriptive_variant_medians'].items():
  rs=[r for r in result['cases'] if r['round'] in rounds and r['workload']==summary['workload'] and r['variant']==variant]
  assert len(rs)==len(rounds)
  expected={'direct_gap_ACK_fraction':statistics.median(r['class_summary']['after_gap_0']['ACK_count']/r['ACKs'] for r in rs),
   'p95_tail_direct_gap_share':statistics.median(r['tails']['p95']['direct_after_gap_share'] for r in rs),
   'p99_tail_direct_gap_share':statistics.median(r['tails']['p99']['direct_after_gap_share'] for r in rs),
   'p99_tail_within_three_groups_share':statistics.median(r['tails']['p99']['within_three_groups_after_gap_share'] for r in rs),
   'direct_gap_group_p99_ns':statistics.median(r['class_summary']['after_gap_0']['p99_ns'] for r in rs),
   'maintenance_publications':statistics.median(r['unacknowledged_interior_generations']+r['trailing_unacknowledged_generations'] for r in rs)}
  assert expected==actual
 expected=[r for r in audit['controls']+audit['guards'] if r['scope']==scope and r['workload']==summary['workload'] and r['metric'] in ['p95','p99']]
 assert expected==summary['original_whole_p95_p99_control_and_guard_outcomes']
assert all(sha(BASE/n)==h for n,h in policy['all_inputs_SHA256'].items())
proof={'complete':True,'all479232_CSV_annotations_independently_reconstructed':True,'all216_whole_quantiles_groups_gaps_compaction_cold_counters_exact':True,
 'all_class_quantiles_tail_denominators_counts_and18_full_half_summaries_exact':True,'all_original117_guard_and_control_outcomes_preserved':True,
 'trailing_compaction_cases':trailing,'all_preserved_input_SHA256_unchanged':True,'zero_engine_build_or_Native_timer_or_source_changes':True,
 'posthoc_only_no_new_performance_qualification':True}
print(json.dumps(proof))
