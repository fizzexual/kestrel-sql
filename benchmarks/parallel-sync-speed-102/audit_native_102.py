"""Pure full history/CRC/byte replay and fixed native controls, no timers."""
from pathlib import Path
import collections,copy,hashlib,importlib.util,itertools,json,statistics,sys
sys.dont_write_bytecode=True
P='2cfc5325f1097b311ed7c2b3eb9892f5faad470313a21af04696f61b314b5ef3'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dep(w,name):
 spec=importlib.util.spec_from_file_location(name,w/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);assert Path(m.__file__).resolve().is_relative_to(w.resolve());return m
def order(policy,actual):
 assert actual==policy['native']['cases'] and len(actual)==144
 for half in [0,1]:
  for history in ['anonymous','named']:
   groups=[]
   for rnd in range(half*12,(half+1)*12):
    cases=[c for c in actual if c['round']==rnd and c['history']==history]
    assert len(cases)==3 and [c['slot'] for c in cases]==[0,1,2] and all(c['half']==half for c in cases)
    groups.append(tuple(c['variant'] for c in cases))
   assert collections.Counter(groups)=={p:2 for p in itertools.permutations(['baseline_a','baseline_b','candidate'])}
 for rnd in range(24):
  assert [c['history'] for c in actual if c['round']==rnd]==(['anonymous']*3+['named']*3 if rnd%2==0 else ['named']*3+['anonymous']*3)
 assert all(c['binary']==('candidate' if c['variant']=='candidate' else 'normal') and c['probe_variant']==('baseline_b' if c['variant']=='baseline_b' else 'baseline_a') for c in actual)
def audit(w,smoke=False):
 policy=load(w/'policy.json');assert sha(w/'policy.json')==P
 a=dep(w,'audit_publication_100');archive=dep(w,'archive_audit_099');ref=a.reference();digests={g:archive.digest(ref[32768+(g-1)*100:32768+g*100]) for g in range(1,513)}
 report=load(w/('native-smokes.json' if smoke else 'paired-native.json'));assert report['complete'] and not report['failed_cases'] and not report['unstarted_cases']
 assert report['policy_sha256']==P and report['excluded_from_main_gates']==smoke
 if not smoke:
  assert report['freeze_sha256']==sha(w/'timing-freeze.json') and all(sha(w/n)==h for n,h in load(w/'timing-freeze.json')['sha256'].items())
  actual=[{k:r[k] for k in policy['native']['cases'][0]} for r in report['cases']];order(policy,actual)
 else:assert len(report['cases'])==4
 metrics=[];stores=[];stalls=[];file_hashes=[]
 for record in report['cases']:
  raw=w/record['raw'];x=load(raw);assert record['exit_code']==0 and not record.get('timeout') and load(raw.parent/'status.json')==record
  assert record['owned_process_identity']['pid']>0 and record['owned_process_identity']['creation_filetime']>0
  assert [json.loads(s) for s in (raw.parent/'native-journal.jsonl').read_bytes().splitlines()]==[{'append':r} for r in x['append_records']]+[{'complete':x}]
  spec={'variant':record['probe_variant'],'history':record['history']};m=a.validate_raw(spec,x)
  metrics.append({**record,**m});stores.append({'case_index':record['case_index'],**a.audit_store(w,raw,archive,ref,digests)})
  file_hashes.append({p.name:sha(p) for p in (raw.parent/'archive').iterdir() if p.is_file() and p.name!='archive.lockfile'})
  stalls.extend({'case_index':record['case_index'],'group':r['group'],'outer_ns':r['outer_ns']} for r in x['append_records'] if r['outer_ns']>100000000)
  print(json.dumps({'native_audited':len(metrics),'total':len(report['cases']),'full_historical_receipts_and_CRC':True}),flush=True)
 if smoke:
  assert file_hashes[0]==file_hashes[1] and file_hashes[2]==file_hashes[3]
 else:
  for rnd in range(24):
   for history in ['anonymous','named']:
    selected=[file_hashes[i] for i,c in enumerate(metrics) if c['round']==rnd and c['history']==history];assert len(selected)==3 and selected[0]==selected[1]==selected[2]
 scopes=[];goals=[]
 if not smoke:
  for history in ['anonymous','named']:
   for name,rounds in [('full',list(range(24))),('half_0',list(range(12))),('half_1',list(range(12,24)))]:
    checks=[]
    for metric in policy['native']['metrics']:
     pairs=[]
     for rnd in rounds:pairs.append({c['variant']:c[metric] for c in metrics if c['history']==history and c['round']==rnd})
     aa=[p['baseline_b']/p['baseline_a'] for p in pairs];ca=[p['candidate']/p['baseline_a'] for p in pairs];cb=[p['candidate']/p['baseline_b'] for p in pairs]
     aa_m=statistics.median(aa);ca_m=statistics.median(ca)
     checks.append({'metric':metric,'before_median_ns':statistics.median(p['baseline_a'] for p in pairs),'after_median_ns':statistics.median(p['candidate'] for p in pairs),'AA_median':aa_m,'CA_median':ca_m,'CB_diagnostic_median':statistics.median(cb),'AA_passed':.95<=aa_m<=1.05,'candidate_guard_passed':ca_m<=1.05,'AA_all_ratios':aa,'CA_all_ratios':ca,'CB_diagnostic_ratios':cb})
     if metric in policy['native']['goals']:goals.append({'history':history,'scope':name,'metric':metric,'CA_median':ca_m,'limit':policy['native']['goals'][metric],'passed':ca_m<=policy['native']['goals'][metric]})
    scopes.append({'history':history,'scope':name,'checks':checks,'passed':all(c['AA_passed'] and c['candidate_guard_passed'] for c in checks)})
 return {'trial':102,'correctness_passed':True,'excluded_smokes':smoke,'cases':len(metrics),'append_publications':len(metrics)*512,'historical_catalogs_checked':len(metrics)*513,
  'full_case_crc_bytes':sum(s['decode']['full_block_crc_bytes'] for s in stores),'all_normal_candidate_current_and_historical_bytes_equal':True,
  'identity_failed':sum(not c['AA_passed'] for s in scopes for c in s['checks']),'candidate_guards_failed':sum(not c['candidate_guard_passed'] for s in scopes for c in s['checks']),
  'goals_failed':sum(not g['passed'] for g in goals),'scoped_native_qualified':not smoke and all(s['passed'] for s in scopes) and all(g['passed'] for g in goals),
  'scopes':scopes,'goals':goals,'case_metrics':metrics,'stores':stores,'events_over_100ms':stalls,'native_launches':0,'performance_timer_launches':0,'supported':'0.3.16','no_adoption':True}
if __name__=='__main__':
 w=Path(sys.argv[1]);smoke=sys.argv[2:]==['--smoke'];x=audit(w,smoke);p=w/('native-smoke-audit.json' if smoke else 'native-audit.json');assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:x[k] for k in ['cases','identity_failed','candidate_guards_failed','goals_failed','scoped_native_qualified','full_case_crc_bytes']}))
