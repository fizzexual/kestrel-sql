"""Independent full Native timing, ACK, data, format and balanced-control replay."""
from pathlib import Path
import hashlib,itertools,json,math,sqlite3,statistics,sys
import numpy as np
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).parent))
import archive_audit_099 as archive
from publication_checks_113 import check_profile,check_sql
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def quantile(values,q):return sorted(values)[max(0,math.ceil(len(values)*q)-1)]
def data(producer,batch):
 lo=producer*1_000_000+batch*100
 return [[i,i*37%1000-500,producer] for i in range(lo,lo+100)]
def inventory(p):return {f.name:sha(f) for f in sorted(p.iterdir()) if f.is_file()}
def brief(d):return {k:v for k,v in d.items() if k!='receipts'}|{'receipt_count':len(d['receipts']),'receipts_sha256':hashlib.sha256(json.dumps(d['receipts'],sort_keys=True,separators=(',',':')).encode()).hexdigest()}
def check_order(cases,expected,configs):
 assert len(cases)==len(expected)
 for c,s in zip(cases,expected):assert all(c[n]==v for n,v in s.items())
 permutations=sorted(itertools.permutations(['baseline_a','baseline_b','candidate']))
 for config in configs:
  for rounds in [range(1,13),range(1,7),range(7,13)]:
   orders=[tuple(c['variant'] for c in cases if c['round']==r and c['name']==config['name']) for r in rounds]
   assert sorted(orders)==sorted(permutations*(len(rounds)//6))
def compare(a,b):return statistics.median(y/x for x,y in zip(a,b))
def audit(w):
 policy=load(w/'policy.json');report=load(w/'paired-native.json');freeze=load(w/'timing-freeze.json')
 assert report['complete'] and not report['failed_cases'] and not report['unstarted_case_indices']
 assert report['trial']==113 and [json.loads(line) for line in (w/'native-case-journal.jsonl').read_text().splitlines()]==report['cases']
 assert report['policy_sha256']==sha(w/'policy.json') and report['freeze_sha256']==sha(w/'timing-freeze.json')
 assert all(sha(w/n)==h for n,h in freeze['files'].items());cases=report['cases'];check_order(cases,policy['native_cases'],policy['native_configs'])
 decoded=[];stalls=[];queries={};metrics={};crc=0;acks=0;stage_records=[]
 for c in cases:
  assert c['actual_wait_completed'] and c['returncode']==0 and c['owned_Popen_handle'] and not c.get('timeout') and c['pid']==c['process_identity']['pid']
  for k in ['stdout','stderr']:assert sha(w/c[k])==c[k+'_sha256']
  result=load(w/c['stdout']);assert {k:v for k,v in result.items() if k not in ['raw_acknowledgements','raw_latency_ms','queries']}==c['result_summary'] and result['version']==('0.3.17' if c['variant']=='candidate' else '0.3.16')
  d=w/c['fixture'];values={}
  if c['kind']=='live':
   records=result['raw_acknowledgements'];assert len(records)==c['producers']*c['batches'] and {(r['producer'],r['batch']) for r in records}==set(itertools.product(range(c['producers']),range(c['batches'])))
   assert result['producers']==c['producers'] and result['batches_each']==c['batches'] and result['named']==bool(c['named']) and result['adaptive_enabled']==(c['variant']=='candidate')
   rows=[];receipts={};generations={}
   for r in records:
    part=data(r['producer'],r['batch']);rows+=part;identifier=f"native:{r['producer']}:{r['batch']}" if c['named'] else None
    assert r['id']==identifier and r['rows']==100 and r['generation']>0 and isinstance(r['elapsed_ns'],int) and r['elapsed_ns']>0
    if identifier is not None:receipts[identifier]=(part,r['generation'])
    generations[r['generation']]=generations.get(r['generation'],0)+1
    if r['elapsed_ns']>100_000_000:stalls.append({'case_index':c['index'],**r})
   samples=[r['elapsed_ns'] for r in records]
   for n,q in [('p50',.5),('p95',.95),('p99',.99)]:assert result['latency_ns'][n]==quantile(samples,q);values[n]=result['latency_ns'][n]
   assert result['latency_ns']['max']==max(samples) and result['wall_ns']>0;values['wall']=result['wall_ns'];values['disk']=result['cold_stats']['physical_bytes']
   stats=result['ingest'];assert stats['committed_batches']==len(records) and stats['durable_group_commits']==len(generations)
   assert max(generations.values())==stats['max_group_requests'] and max(generations.values())<=64
   assert stats['queued_payload_bytes']==stats['maintenance_errors']==stats['duplicate_batches']==0 and not stats['writer_poisoned']
   assert result['actual_writer_join_and_pin_release'] and result['all_original_receipt_generations_checked']==bool(c['named'])
   phase=result['adaptive']
   if c['variant']=='candidate':
    assert phase['configured_max_delay_ns']==2_000_000 and phase['max_selected_delay_ns']<=2_000_000
    assert phase['observed_publications']==stats['durable_group_commits'] and sum(phase[k] for k in ['latency_groups','coalescing_groups','pressure_groups'])==stats['collected_groups']
    if c['producers']==1:assert phase['latency_groups']==len(records) and phase['max_selected_delay_ns']==0
   else:assert phase is None and stats['group_delay_ns']==0
   check=archive.check(d,rows,receipts);assert result['full_crc_bytes']==check['full_block_crc_bytes'] and result['cold_stats']['rows']==len(rows) and result['cold_stats']['generation']==check['head'];acks+=len(records)
   stage_values,stage_proof=check_profile(result);values.update(stage_values)
   check_sql(result,rows,queries,('live',c['producers'],c['batches']))
   retained_catalog_bytes=sum(p.stat().st_size for p in d.glob('catalog-*.ks2'))
   assert retained_catalog_bytes<=stage_proof['catalog_bytes_logical']
   stage_records.append({'index':c['index'],**stage_proof})
  elif c['kind']=='replay':
   n=c['ids'];rows=[[i,2*i,i%97] for i in range(n)];receipts={f'probe:{i}':([row],1) for i,row in enumerate(rows)};check=archive.check(d,rows,receipts)
   raw=result['raw_latency_ms'];assert len(raw)==c['repeats'] and all(math.isfinite(x) and x>0 for x in raw)
   for name,q in [('p50',.5),('p95',.95),('p99',.99)]:assert result['latency_ms'][name]==quantile(raw,q);values[name]=result['latency_ms'][name]
   assert result['latency_ms']['max']==max(raw) and result['no_new_publication'] and result['rows_and_sum_match'] and result['full_scrub_passed'] and result['receipt_count']==n
  else:
   n=c['rows'];ts=np.arange(n,dtype=np.int64);value=(ts*37)%1000-500;device=(ts*17)%97
   if c['late']:ts=np.where(ts%20==0,ts-10000,ts)
   rows=np.stack([ts,value,device],axis=1).tolist();check=archive.check(d,rows,{})
   key=bool(c['late'])
   if key not in queries:
    with sqlite3.connect(':memory:') as db:
     db.execute('CREATE TABLE events(ts INTEGER,value INTEGER,device INTEGER)');db.executemany('INSERT INTO events VALUES(?,?,?)',rows)
     queries[key]={item['name']:[list(row) for row in db.execute(item['sql']).fetchall()] for item in result['queries']}
   assert result['rows']==n and result['repeats']==127 and result['warmups']==3 and result['verified_bytes']==n*24 and result['threads']==1
   assert len(result['queries'])==6
   for item in result['queries']:
    samples=item['samples_us'];assert len(samples)==127 and all(math.isfinite(x) and x>0 for x in samples)
    assert item['median_us']==statistics.median(samples) and item['p95_us']==quantile(samples,.95)
    actual=item['result']['rows'];expected=queries[key][item['name']];assert len(actual)==len(expected)
    for row,reference in zip(actual,expected):
     assert len(row)==len(reference)
     for x,y in zip(row,reference):assert math.isclose(x,y,rel_tol=1e-12,abs_tol=1e-12) if isinstance(y,float) else x==y
    for name in ['median_us','p95_us']:values[item['name']+'/'+name]=item[name]
   assert result['verified_bytes']==check['full_block_crc_bytes']
  crc+=check['full_block_crc_bytes'];decoded.append({'index':c['index'],**brief(check)});metrics[c['index']]=values
  print(json.dumps({'native_audited':c['index']+1,'of':144}),flush=True)
 # The direct unchanged Archive fixtures must be exactly identical within each balanced round.
 byte_checks=0
 for config in policy['native_configs']:
  if config['kind']=='live':continue
  for round in range(1,13):
   cohort=[c for c in cases if c['round']==round and c['name']==config['name']];files=[inventory(w/c['fixture']) for c in cohort];assert files[0]==files[1]==files[2];byte_checks+=1
 controls=[];guards=[];goals=[];summaries=[]
 for scope,rounds in policy['scopes'].items():
  for config in policy['native_configs']:
   cohort={v:sorted([c for c in cases if c['round'] in rounds and c['name']==config['name'] and c['variant']==v],key=lambda c:c['round']) for v in ['baseline_a','baseline_b','candidate']}
   for name in metrics[cohort['baseline_a'][0]['index']]:
    by={v:[metrics[c['index']][name] for c in values] for v,values in cohort.items()};aa=compare(by['baseline_a'],by['baseline_b']);ca=compare(by['baseline_a'],by['candidate'])
    row={'scope':scope,'workload':config['name'],'metric':name,'before_median':statistics.median(by['baseline_a']),'after_median':statistics.median(by['candidate']),'AA':aa,'CA':ca,'all_values':by};summaries.append(row)
    if name!='disk':controls.append({**row,'passed':.95<=aa<=1.05})
    guards.append({**row,'passed':ca<=1.05})
    if config['kind']=='live' and config['producers']==4 and name in ['p99','wall']:
     limit=.95 if name=='p99' else .90;goals.append({**row,'limit':limit,'passed':ca<=limit})
    if config['kind']=='queries' and name in ['unordered_filter/median_us','unordered_filter/p95_us']:
     goals.append({**row,'limit':.90,'passed':ca<=.90})
    if config['name']=='identified-replay' and name in ['p95','p99']:
     goals.append({**row,'limit':.90,'passed':ca<=.90})
    if config['kind']=='queries' and name in ['grouped/median_us','grouped/p95_us']:
     goals.append({**row,'limit':.90,'passed':ca<=.90})
 assert acks==policy['expected_ACKs'] and crc==policy['expected_full_crc_bytes']
 assert len(controls)==policy['expected_AA_controls'] and len(guards)==policy['expected_candidate_guards'] and not goals
 return {'complete':True,'correctness_passed':True,'cases':144,'live_acknowledgements':acks,'full_crc_bytes':crc,'current_store_audits':decoded,'direct_Archive_byte_equivalent_rounds':byte_checks,'summaries':summaries,'identity_failed':sum(not x['passed'] for x in controls),'candidate_guards_failed':sum(not x['passed'] for x in guards),'goals_failed':sum(not x['passed'] for x in goals),'controls':controls,'guards':guards,'goals':goals,'events_over100ms':stalls,'performance_qualified':all(x['passed'] for x in controls+guards+goals),'zero_Native_or_timer_reruns':True,'supported':'0.3.16','candidate':'0.3.17','native_CPU_RSS_not_measured':True,'stage_records':stage_records,'release017_qualified':False,'diagnostic_only_no_engine_change_or_adoption':True}

if __name__=='__main__':
 w=Path(sys.argv[1]);result=audit(w);p=w/'native-audit.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:result[k] for k in ['cases','live_acknowledgements','full_crc_bytes','identity_failed','candidate_guards_failed','goals_failed','performance_qualified']}))
