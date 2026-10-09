"""Pure complete 104 replay; fixed decisions, no Native/timers/existing-file writes."""
from pathlib import Path
import contextlib,copy,hashlib,importlib.util,io,json,sqlite3,sys
sys.dont_write_bytecode=True
P='8e06a5d8d0ff0c117f140743a200f35c650753dc610ca879080f1fb10f331c64'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def lines(p):return [json.loads(x) for x in p.read_bytes().splitlines() if x.strip()]
def dep(w,name,folder=None):
 p=(folder or w)/(name+'.py');spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
 assert Path(m.__file__).resolve().is_relative_to(w);return m
def audit(w):
 w=w.resolve();sys.path.insert(0,str(w));sys.path.insert(0,str(w/'harness'));oldargv=sys.argv;sys.argv=['pure-complete104',str(w)]
 try:
  for name in ['archive_audit_095','archive_audit_096','archive_audit_099','outcomes_098','audit_service_095']:dep(w,name)
  dep(w,'native_resources_088');dep(w,'host_telemetry',w/'harness');dep(w,'stress_compare',w/'harness')
  native=dep(w,'audit_native_104');backlog=dep(w,'audit_backlog_104');service=dep(w,'audit_service_104');service.W=w
 finally:sys.argv=oldargv
 assert sha(w/'policy.json')==P
 policy=load(w/'policy.json');freeze=load(w/'timing-freeze.json')
 assert all(sha(w/n)==h for n,h in freeze['sha256'].items())
 source=load(w/'source-derivation.json');actual={p.relative_to(w/'source').as_posix():sha(p) for p in (w/'source').rglob('*') if p.is_file()}
 assert actual==source['final']==load(w/'basis/103-source-derivation-v3.json')['final'] and len(actual)==44
 build=load(w/'build-proof.json');assert build['complete'] and build['source']==actual and build['fresh_native_test_executions']==406 and build['strict_lint_modes']==2
 assert sum(r.get('tests_passed',0) for r in build['records'])==406 and len(build['records'])==8
 for r in build['records']:
  assert r['returncode']==0 and sha(w/r['log'])==r['log_sha256'] and '--offline' in r['argv'] and '--locked' in r['argv']
  feature=r['argv'][r['argv'].index('--features')+1]
  assert feature==('async-reclaim,benchmark-shutdown,reusable-sync-103' if r['step'].startswith('candidate-') else 'async-reclaim,benchmark-shutdown')
 assert all(sha(w/n)==h for n,h in build['binaries'].items())
 prep=load(w/'preparation-proof.json');assert prep['source_exact_103'] and prep['service_original_run_load_and_connections_byte_exact']
 assert all(sha(w/'harness'/n)==h for n,h in prep['harness_hashes'].items() if n!='native_resources_088.py')
 assert sha(w/'native_resources_088.py')==prep['harness_hashes']['native_resources_088.py']
 with contextlib.redirect_stdout(io.StringIO()):
  nt=native.audit(w);ns=native.audit(w,True);back=backlog.audit(w)
 assert nt==load(w/'native-audit.json') and ns==load(w/'native-smoke-audit.json') and back==load(w/'backlog-audit-proof.json')
 # Reuse the qualified098 in-memory output interception: no semantic gate changes.
 output=w/'audit.json';exists_original=Path.exists;write_original=Path.write_text;captured=[]
 def exists(path):return False if path==output else exists_original(path)
 def write(path,text,*args,**kwargs):
  assert path==output,('unexpected audit write',path);captured.append(json.loads(text));return len(text)
 Path.exists=exists;Path.write_text=write
 try:
  with contextlib.redirect_stdout(io.StringIO()):st=service.main()
 finally:Path.exists=exists_original;Path.write_text=write_original
 assert captured==[st] and st==load(output)
 archive=sys.modules['archive_audit_096'];outcome=sys.modules['outcomes_098'];smokes=[]
 for mode in ['normal','candidate']:
  c=load(w/('smoke-v2-'+mode+'.json'));c['case_index']=-1;good,counts=outcome.outcomes(c,c['samples']);assert counts['lost']==0
  folder=w/('smoke-v2-'+mode);records=load(folder/'bridge-lifecycle.json');assert records==c['lifecycle'] and len(records)==2
  for r in records:
   assert r['returncode']==0 and r['graceful_background_joined'] and not r.get('hard_failure')
   stats=r['final']['ingest'];assert stats['writer_stopped'] and not stats['writer_poisoned'] and stats['maintenance_errors']==stats['queued_payload_bytes']==0
   assert lines(folder/r['stdout'])[1]==r['final'] and (folder/r['stdin']).read_bytes()==b'shutdown\n'
  ref=[[i,(i*37)%1000-500,(i*17)%97] for i in range(1000)]
  for event in good:
   if event['operation']=='append':
    seq=event['sequence'];ref.extend([[j-500 if j%20==0 else j,(j*37)%1000-500,1000+seq] for j in range(1000+seq*100,1000+(seq+1)*100)])
  decoded=archive.check(folder/'archive',ref,{})
  assert decoded['rows']==len(ref)==c['reconciliation']['rows'] and c['reconciliation']['all_acknowledged_batches_present']
  assert {p.name:p.stat().st_size for p in (folder/'archive').iterdir() if p.is_file()}==records[0]['physical_inventory_before_cold']
  smokes.append({'mode':mode,'offers':counts['offered'],'lost':0,'decode':decoded,'graceful_joins':2})
 pre=load(w/'preperformance-proof.json');assert pre['passed'] and pre['service_smokes']==smokes and pre['outcome_negative_validation']==outcome.negatives()
 native.order(policy,policy['native']['cases']);bad=copy.deepcopy(policy['native']['cases']);bad[0]['binary']='normal' if bad[0]['binary']=='candidate' else 'candidate'
 try:native.order(policy,bad)
 except AssertionError:pass
 else:raise AssertionError('tampered native binary order accepted')
 compatibility=load(w/'compatibility-proof.json');order=load(w/'compatibility-run-order.json');assert compatibility['complete'] and compatibility['fresh_cli_sqlite_queries']==len(order)==24
 conn=sqlite3.connect(':memory:')
 try:
  conn.execute('CREATE TABLE events(ts INTEGER,value INTEGER,kind INTEGER)');conn.executemany('INSERT INTO events VALUES(?,?,?)',((i,2*i,i%97) for i in range(83968)))
  for r,c in zip(order,compatibility['comparisons']):
   assert r['label']==c['label'] and r['exit_code']==0 and all(sha(w/r[k])==r[k+'_sha256'] for k in ['stdout','stderr'])
   expected=[list(row) for row in conn.execute(c['sql'])];x=load(w/r['stdout']);assert x['ok'] and x['result']['rows']==expected==c['expected']
 finally:conn.close()
 readers={'released016':w/'binaries/released016-kestrel.exe','normal':w/'binaries/normal/kestrel.exe','candidate':w/'binaries/candidate/kestrel.exe'}
 assert {n:sha(p) for n,p in readers.items()}==compatibility['reader_hashes']
 validation=load(w/'helper-validation.json');assert validation['synthetic_validation_only'] and validation['native_launches']==validation['performance_timer_launches']==0
 assert [len(validation[k]) for k in ['invalid_order_rejected','invalid_resource_rejected','invalid_lifecycle_rejected']]==[5,9,9]
 assert validation['invalid_outcomes']==outcome.negatives() and len(validation['invalid_outcomes']['six_invalid_outcome_records_rejected'])==6
 basis=load(w/'basis/103-audit.json');restored=load(w/'basis/103-restored-audit-proof.json')
 assert basis['correctness_recovery_passed'] and basis['qualifying_current_source_native_tests']==916 and not basis['performance_qualified']
 assert restored['passed'] and restored['replay_equals_original_complete_audit']
 assert sha(w/'basis/103-audit.json')==policy['reused_correctness']['audit_sha256']
 assert sha(w/'basis/103-restored-audit-proof.json')==policy['reused_correctness']['restored_proof_sha256']
 assert source['all_source_files_byte_exact_to_final_103'] and source['engine_changes']==[]
 for name in ['archive_audit_095','archive_audit_096','archive_audit_099','audit_publication_100','audit_native_104','audit_backlog_104','audit_service_104','audit_service_095','outcomes_098','stress_compare','native_resources_088','host_telemetry']:
  assert Path(sys.modules[name].__file__).resolve().is_relative_to(w),(name,sys.modules[name].__file__)
 return {'trial':104,'complete_original_and_restored_semantic_audit_passed':True,'correctness_passed':True,'fresh_exact_feature_tests':406,'strict_lints':2,'reused103_tests':916,'reused103_not_reexecuted_or_recounted':True,'original_frozen_files':len(freeze['sha256']),
  'native':{k:nt[k] for k in ['cases','append_publications','historical_catalogs_checked','full_case_crc_bytes','identity_failed','candidate_guards_failed','goals_failed','scoped_native_qualified','events_over_100ms']},
  'service':{k:st[k] for k in ['cases','offered','successful','lost','queue_dropped','queue_expired','executed_failed','acknowledged_batches','full_crc_bytes','identity_failed_total','candidate_failed_total','goals_failed','scoped_candidate_qualified','events_over_100ms']},
  'backlog':{k:back[k] for k in ['backlog_cases','acknowledged_groups','case_full_crc_reference_bytes','all_original_named_generation_receipts_verified','all_four_backlog_gates_passed']},
  'native_smokes':4,'service_smokes':2,'fresh_cli_sqlite_queries':24,'pretime_synthetic_invalid_controls':29,'invalid_outcome_and_native_binary_controls_recomputed':True,
  'reports_recomputed_exact':{n:sha(w/n) for n in ['native-audit.json','native-smoke-audit.json','audit.json','backlog-audit-proof.json']},
  'all_sources_binaries_raw_outcomes_frozen_setup_stops_retained':True,'all_dependencies_from_requested_tree':True,'native_launches':0,'performance_timer_launches':0,'no_original_or_restored_file_writes':True,
  'performance_qualified':nt['scoped_native_qualified'] and st['scoped_candidate_qualified'],'adoption_qualified':False,'supported':'0.3.16','release017_qualified':False,'no_competitor_or_universal_win_claim':True}
if __name__=='__main__':
 w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-104');x=audit(w);p=w/'complete-audit-proof.json';assert not p.exists();p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(x),flush=True)
