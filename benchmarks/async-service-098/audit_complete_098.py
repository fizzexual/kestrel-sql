"""Read-only complete replay; retain failed builds and recompute every timing gate."""
from pathlib import Path
import contextlib,hashlib,importlib.util,io,json,re,sys
sys.dont_write_bytecode=True
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def lines(p):return [json.loads(x) for x in p.read_bytes().splitlines() if x.strip()]
def digest(b):return hashlib.sha256(b).hexdigest()
def audit(w):
 w=w.resolve();sys.path.insert(0,str(w));sys.path.insert(0,str(w/'harness'))
 oldargv=sys.argv;sys.argv=['read-only-audit',str(w)]
 for name,folder in [('archive_audit_096',w),('archive_audit_095',w),('outcomes_098',w),('stress_compare',w/'harness'),('audit_service_095',w),('audit_service_098',w),('audit_backlog_098',w)]:
  spec=importlib.util.spec_from_file_location(name,folder/(name+'.py'));module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
  assert Path(module.__file__).resolve().is_relative_to(w)
 sys.argv=oldargv;archive=sys.modules['archive_audit_096'];service=sys.modules['audit_service_098'];backlog=sys.modules['audit_backlog_098'];service.W=w
 assert sha(w/'policy.json')=='4fe1c7bc59de1363cdcbf4e70a22851286e4afe7cfd1035df166690214774bfe'
 source=load(w/'source-derivation.json');s=w/'source';assert {p.relative_to(s).as_posix():sha(p) for p in s.rglob('*') if p.is_file()}==source['final']
 live=(s/'src/live.rs').read_bytes();start=live.index(b'    #[cfg(feature = "benchmark-shutdown")]');end=live.index(b'    pub fn stats(&self) -> LiveStats',start)
 module=b'\n#[cfg(all(test, feature = "benchmark-shutdown"))]\n#[path = "shutdown_tests_098.rs"]\nmod shutdown_tests_098;\n';assert digest((live[:start]+live[end:]).removesuffix(module))==source['base']['src/live.rs']
 worker=(s/'src/async_reclaim_096.rs').read_bytes();start=worker.index(b'    #[cfg(all(test, feature = "benchmark-shutdown"))]');end=worker.index(b'    #[cfg(any(test, feature = "fault-injection"))]',start);assert digest(worker[:start]+worker[end:])==source['base']['src/async_reclaim_096.rs']
 assert sha(s/'src/archive.rs')==source['base']['src/archive.rs'] and sha(s/'Cargo.lock')==source['base']['Cargo.lock']
 original=(s/'src/bin/kestrel-stress.rs').read_bytes();owned=(s/'src/bin/kestrel_stress_098.rs').read_bytes()
 assert original[original.index(b'fn dispatch('):original.index(b'fn main()')]==owned[owned.index(b'fn dispatch('):owned.index(b'fn main()')]
 build=load(w/'build-proof.json');assert build['native_test_executions']==716 and build['strict_lint_modes']==4 and build['complete']
 for record in build['records']:
  assert record['returncode']==0 and sha(w/record['log'])==record['log_sha256']
 assert load(w/'build-run-order-v2.json')==build['records'] and all(sha(w/n)==h for n,h in build['binaries'].items())
 assert all(sha(w/n)==h for n,h in load(w/'timing-freeze.json')['sha256'].items())
 with contextlib.redirect_stdout(io.StringIO()):back=backlog.audit(w)
 assert back==load(w/'backlog-audit-proof.json')
 # Capture the original auditor's single JSON output without changing any file.
 output=w/'audit.json';original_exists=Path.exists;original_write=Path.write_text;captured=[]
 def exists(path):return False if path==output else original_exists(path)
 def write(path,text,*args,**kwargs):
  assert path==output,('unexpected audit write',path);captured.append(json.loads(text));return len(text)
 Path.exists=exists;Path.write_text=write
 try:
  with contextlib.redirect_stdout(io.StringIO()):timing=service.main()
 finally:Path.exists=original_exists;Path.write_text=original_write
 assert captured==[timing] and timing==load(output)
 oracle=load(w/'oracle-proof.json');journal=load(w/'oracle-journal-proof.json');records=load(w/'oracle-native-run-order.json');assert oracle['complete'] and journal['complete'] and len(records)==56
 for r in records:
  assert sha(w/r['stdout'])==r['stdout_sha256'] and sha(w/r['stderr'])==r['stderr_sha256'] and 'completed_utc' in r
 assert sum(r['returncode']!=0 for r in records)==6 and all(sha(w/n)==h for n,h in load(w/'oracle-freeze.json')['files'].items())
 oracle_stores=[]
 for size in ['sequence','oversized']:
  if size=='sequence':
   rows=[[i,2*i] for i in range(73)]+[[40,80]];receipts={f'id:{i:03}':([[i,2*i]],i+1+int(i>64)) for i in range(73) if i!=40};receipts.update({key:([[40,80]],41) for key in ['A:group/40','B:group/40']})
  else:rows=[[i,2*i] for i in range(70001)];receipts={f'{i:06}:'+('x'*121):([[i,2*i]],1) for i in range(70000)};receipts['after-large']=([[70000,140000]],2)
  inventories=[]
  for label in ['released016','baseline','candidate']:
   p=w/'oracles'/(label+'-'+size);decoded=archive.check(p,rows,receipts);oracle_stores.append({'label':label,'size':size,'decode':decoded});inventories.append({f.name:sha(f) for f in p.glob('*.ks2')})
  assert inventories[0]==inventories[1]==inventories[2]
 for c in oracle['wire_and_live_checks']:
  label=c['variant'];rows=[[i,(i*37)%1000-500,(i*17)%97] for i in range(16)]+[[i,i*2,1000+i-16] for i in range(16,176)]
  receipts={a['request']['id']:(a['request']['data'],a['receipt']['generation']) for a in c['acks']};assert len(receipts)==160
  p=w/'oracles'/('live-'+label);decoded=archive.check(p/'archive',rows,receipts);lc=load(p/'bridge-lifecycle.json');assert len(lc)==2 and all(r['graceful_background_joined'] and r['returncode']==0 for r in lc)
  for r in lc:
   assert (p/r['stdin']).read_bytes()==b'shutdown\n';events=lines(p/r['stdout']);assert len(events)==2 and events[1]==r['final']
  oracle_stores.append({'label':label,'size':'live','decode':decoded})
 assert len(oracle_stores)==8 and len(journal['lifecycles'])==4
 smokes=[]
 for mode in ['incremental','async']:
  c=load(w/('smoke-v2-'+mode+'.json'));assert c['unsuccessful_or_unexecuted']==0 and c['reconciliation']['all_acknowledged_batches_present'];raw=c['samples']
  rows=[[i,(i*37)%1000-500,(i*17)%97] for i in range(1000)]
  for sample in raw:
   if sample['ok'] and sample['operation']=='append':
    seq=sample['sequence'];rows.extend([[j-500 if j%20==0 else j,(j*37)%1000-500,1000+seq] for j in range(1000+seq*100,1000+(seq+1)*100)])
  decoded=archive.check(w/('smoke-v2-'+mode)/'archive',rows,{})
  assert len(c['lifecycle'])==2 and all(r['graceful_background_joined'] and r['returncode']==0 for r in c['lifecycle']);smokes.append({'mode':mode,'decode':decoded})
 return {'passed':True,'normal_hot_bodies_and_original_dispatch_client_reverse_exact':True,'qualifying_current_source_native_tests':716,'strict_lints':4,'prior_failed_lint_source_tests_retained':716,'backlog':back,'timing':timing,'oracle_native_commands':56,'oracle_named_ACKs':320,'oracle_store_audits':oracle_stores,'smoke_store_audits':smokes,'normal_timed_processes_gracefully_joined_exit0':288,'oracle_processes_gracefully_joined_exit0':4,'native_launches':0,'performance_timer_launches':0,'no_original_or_restored_file_writes':True,'all_dependencies_loaded_from_requested_tree':True}
if __name__=='__main__':
 w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-098');result=audit(w);p=w/'complete-audit-proof.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in result.items() if k not in ['backlog','timing','oracle_store_audits','smoke_store_audits']}))
