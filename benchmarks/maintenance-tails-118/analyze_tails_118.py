"""Untimed complete-population post-hoc classification of trial117 live ACKs."""
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict,Counter
import csv,gzip,hashlib,json,math,statistics,traceback
R=Path('D:/Codex/Kestrel/work');OLD=R/'perf-117';W=R/'perf-118'
def utc():return datetime.now(timezone.utc).isoformat()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,indent=2)+'\n')
def quantile(values,n):
 if not values:return None
 return sorted(values)[math.ceil(len(values)*n/100)-1]
assert not W.exists()
guard=load(sorted(R.glob('guard-final-117-*.json'))[-1]);assert guard['verified_idle_terminal_reset'] and not guard['active_processes']
assert (datetime.now(timezone.utc)-datetime.fromisoformat(guard['utc'])).total_seconds()<1800
report=load(OLD/'paired-native.json');audit=load(OLD/'native-audit.json');assert report['complete'] and audit['correctness_passed'] and not audit['performance_qualified']
cases=[c for c in report['cases'] if c['kind']=='live'];assert len(cases)==216 and {c['round'] for c in cases}==set(range(1,13))
inputs={'paired-native.json':sha(OLD/'paired-native.json'),'native-audit.json':sha(OLD/'native-audit.json'),
 'complete-audit-proof.json':sha(OLD/'complete-audit-proof.json'),'policy.json':sha(OLD/'policy.json')}
for config in ['source-v3','baseline-v3']:
 for name in ['src/live.rs','src/archive.rs','examples/adaptive_perf_probe_106.rs']:
  inputs[config+'/'+name]=sha(OLD/config/name)
for c in cases:
 assert c['returncode']==0 and c['actual_wait_completed']
 for k in ['stdout','stderr']:
  assert sha(OLD/c[k])==c[k+'_sha256'];inputs[c[k]]=c[k+'_sha256']
W.mkdir()
save(W/'policy.json',{'trial':118,'declared_utc':utc(),'before_reading_raw_ACK_records_in_this_diagnostic':True,
 'kind':'Post-hoc untimed diagnostic; existing rejected trial117 timings, not new performance qualification.',
 'scope':'ALL216 live cases /479232 ACKs; six workloads x12 balanced rounds x baselineA/baselineB/candidate; full and original six-round halves.',
 'input_root':str(OLD),'all_inputs_SHA256':inputs,'all_fresh117_prerequisites_and_existing_native_audit_reused_not_rerun':True,
 'generation_model':'Fresh archive generation0; one generation per successful nonempty append group; compact_small publishes another generation without changing original receipts. Driver has no other publishes/retries before cold stats. Reconcile missing generations with observed compaction counter and trailing join race.',
 'classes':['before_first_gap','after_gap_0','after_gap_1','after_gap_2','after_gap_3plus'],
 'class_definition':'Sort distinct ACK publication generations. after_gap_0 is first acknowledged publication following one or more unacknowledged generations; following first/second publication classes have distance1/2; distance3+ thereafter. All ACKs in a publication inherit its class.',
 'tail_definition':'Nearest-rank p95/p99; include every ACK >= cutoff, including ties. Record denominators and complete CSV classification, not just slow records.',
 'acceptance':'Complete immutable raw input/identity/quantile validation; exact group counter/missing generation conservation including cold final generation; all ACK records classified once; independent CSV reconstruction; every result and failure retained.',
 'limitations':'Correlation with generation gaps cannot establish exclusive compaction CPU/disk cause, absolute timing alignment or account for queued requests in later groups. Derived conditional classes mix group sizes and are descriptive. Stats sampled before last-owner join; final cold generation covers trailing maintenance.',
 'no_engine_source_edit_build_Native_timer_service_gate_change_or_release':True})
try:
 # Check the maintenance generation semantics are identical in baseline and candidate.
 archives=[(OLD/config/'src/archive.rs').read_text(encoding='utf-8') for config in ['baseline-v3','source-v3']]
 block=lambda s:s[s.index('    pub fn compact_small('):s.index('    /// Reclaim superseded catalogs')]
 assert block(archives[0])==block(archives[1])
 rows=[];total=0;classes=['before_first_gap','after_gap_0','after_gap_1','after_gap_2','after_gap_3plus']
 with gzip.open(W/'all-ACK-classifications.csv.gz','xt',encoding='utf-8',newline='') as f:
  writer=csv.writer(f);writer.writerow(['case','producer','batch','generation','elapsed_ns','class','p95_tail','p99_tail'])
  for c in cases:
   raw=load(OLD/c['stdout']);ack=raw['raw_acknowledgements'];n=c['producers']*c['batches']
   assert len(ack)==n and n in [512,2048,4096] and raw['producers']==c['producers'] and raw['batches_each']==c['batches']
   assert len({(r['producer'],r['batch']) for r in ack})==n
   assert {(r['producer'],r['batch']) for r in ack}=={(p,b) for p in range(c['producers']) for b in range(c['batches'])}
   assert all(r['rows']==100 and r['generation']>0 and r['elapsed_ns']>0 for r in ack)
   assert all(r['id']==(f"native:{r['producer']}:{r['batch']}" if c['named'] else None) for r in ack)
   for p in range(c['producers']):
    seq=sorted((r for r in ack if r['producer']==p),key=lambda r:r['batch'])
    assert all(a['generation']<b['generation'] for a,b in zip(seq,seq[1:]))
   grouped=defaultdict(list)
   for r in ack:grouped[r['generation']].append(r)
   gens=sorted(grouped);ing=raw['ingest'];cold=raw['cold_stats']['generation']
   assert gens[0]==1 and len(gens)==ing['durable_group_commits']==ing['collected_groups'] and ing['committed_batches']==n
   assert raw['actual_writer_join_and_pin_release'] and cold>=gens[-1]
   gaps=[];labels={};last_gap=None
   for index,generation in enumerate(gens):
    previous=gens[index-1] if index else 0;missing=generation-previous-1
    if missing:
     gaps.append({'previous_receipt_generation':previous,'next_receipt_generation':generation,'unacknowledged_generation_count':missing,'next_group_ACKs':len(grouped[generation])})
     last_gap=index
    distance=None if last_gap is None else index-last_gap
    labels[generation]='before_first_gap' if distance is None else ('after_gap_'+str(distance) if distance<3 else 'after_gap_3plus')
   interior=sum(g['unacknowledged_generation_count'] for g in gaps);trailing=cold-gens[-1];missing_total=cold-len(gens)
   assert missing_total==interior+trailing and missing_total-ing['compactions'] in [0,1]
   lat=[r['elapsed_ns'] for r in ack];q={k:quantile(lat,num) for k,num in [('p50',50),('p95',95),('p99',99)]};q['max']=max(lat)
   assert q==raw['latency_ns']==c['result_summary']['latency_ns']
   class_values={tag:[r['elapsed_ns'] for r in ack if labels[r['generation']]==tag] for tag in classes}
   summary={tag:{'ACK_count':len(v),'p50_ns':quantile(v,50),'p95_ns':quantile(v,95),'p99_ns':quantile(v,99),'max_ns':max(v) if v else None} for tag,v in class_values.items()}
   assert sum(v['ACK_count'] for v in summary.values())==n
   tails={}
   for metric in ['p95','p99']:
    tail=[r for r in ack if r['elapsed_ns']>=q[metric]];counts=Counter(labels[r['generation']] for r in tail)
    tails[metric]={'cutoff_ns':q[metric],'total_ACKs_including_ties':len(tail),'class_counts':{tag:counts[tag] for tag in classes},
     'direct_after_gap_share':counts['after_gap_0']/len(tail),
     'within_three_groups_after_gap_share':sum(counts[tag] for tag in classes[1:4])/len(tail)}
   for r in ack:writer.writerow([c['index'],r['producer'],r['batch'],r['generation'],r['elapsed_ns'],labels[r['generation']],int(r['elapsed_ns']>=q['p95']),int(r['elapsed_ns']>=q['p99'])])
   row={'case_index':c['index'],'round':c['round'],'workload':c['name'],'variant':c['variant'],'ACKs':n,'unique_receipt_generations':len(gens),
    'max_group_ACKs':max(map(len,grouped.values())),'cold_generation':cold,'observed_prejoin_compactions':ing['compactions'],
    'unacknowledged_interior_generations':interior,'trailing_unacknowledged_generations':trailing,'unobserved_final_compaction_count':missing_total-ing['compactions'],
    'gaps':gaps,'whole_latency_ns':q,'class_summary':summary,'tails':tails}
   rows.append(row);total+=n
   if len(rows)%36==0:print(json.dumps({'classified_cases':len(rows),'of':216,'ACKs':total}),flush=True)
 assert total==479232
 summaries=[]
 for scope,roundset in [('full',set(range(1,13))),('half_1',set(range(1,7))),('half_2',set(range(7,13)))]:
  for workload in sorted({c['name'] for c in cases}):
   by_variant={v:[r for r in rows if r['round'] in roundset and r['workload']==workload and r['variant']==v] for v in ['baseline_a','baseline_b','candidate']}
   assert all(len(v)==len(roundset) for v in by_variant.values())
   summaries.append({'scope':scope,'workload':workload,'cases_per_variant':len(roundset),
    'descriptive_variant_medians':{v:{'direct_gap_ACK_fraction':statistics.median(r['class_summary']['after_gap_0']['ACK_count']/r['ACKs'] for r in rs),
      'p95_tail_direct_gap_share':statistics.median(r['tails']['p95']['direct_after_gap_share'] for r in rs),
      'p99_tail_direct_gap_share':statistics.median(r['tails']['p99']['direct_after_gap_share'] for r in rs),
      'p99_tail_within_three_groups_share':statistics.median(r['tails']['p99']['within_three_groups_after_gap_share'] for r in rs),
      'direct_gap_group_p99_ns':statistics.median(r['class_summary']['after_gap_0']['p99_ns'] for r in rs),
      'maintenance_publications':statistics.median(r['unacknowledged_interior_generations']+r['trailing_unacknowledged_generations'] for r in rs)} for v,rs in by_variant.items()},
    'original_whole_p95_p99_control_and_guard_outcomes':[r for r in audit['controls']+audit['guards'] if r['scope']==scope and r['workload']==workload and r['metric'] in ['p95','p99']]})
 assert all(sha(OLD/n)==h for n,h in inputs.items())
 proof={'complete':True,'utc':utc(),'existing117_native_correctness_and_performance_outcomes_unchanged':True,
  'posthoc_untimed_reused216_cases_and479232_ACKs':True,'all216_generation_group_cold_counter_and_compaction_conservation_checks_pass':True,
  'all_original_quantiles_recomputed_exact':True,'all_original_input_hashes_unchanged':True,'case_count':216,'ACK_count':total,
  'baseline_candidate_maintenance_generation_semantics_identical':True,'classification_csv_sha256':sha(W/'all-ACK-classifications.csv.gz'),
  'cases':rows,'summaries':summaries,'new_engine_tests_builds_or_timers':0,'new_speed_or_release_qualification':False}
 save(W/'analysis.json',proof)
 print(json.dumps({k:v for k,v in proof.items() if k not in ['cases','summaries']}),flush=True)
except BaseException:
 save(W/'failure.json',{'utc':utc(),'error':traceback.format_exc(),'all_original_inputs_unchanged':all(sha(OLD/n)==h for n,h in inputs.items()),'no_timer_or_engine_changes':True});raise
