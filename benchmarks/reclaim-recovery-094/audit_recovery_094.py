"""Recompute preserved 094 evidence without launching Native binaries or timers."""
from pathlib import Path
import hashlib,json,sys,struct
sys.path.insert(0,str(Path(__file__).parent))
import archive_audit_094 as archive
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def inventory(p):return {q.name:sha(q) for q in p.iterdir() if q.is_file()}
def audit(w):
 proof=load(w/'recovery-proof.json');assert proof['complete'] and proof['fixed_fault_cases']==107 and proof['unstarted']==[]
 policy=load(w/'policy.json');assert hashlib.sha256((w/'policy.json').read_bytes()).hexdigest()=='2fa7850e0eef37cab16d906a5dcec1c21f8bdd12e9c60bf8ab2a96263aedd3b4'
 assert policy['expected_fixed_fault_cases']==107 and proof['093_remains_rejected'] and proof['no_timing_or_adoption']
 freeze=load(w/'recovery-freeze.json')
 for name,digest in freeze['files'].items():assert sha(w/name)==digest,name
 build=load(w/'build-proof.json');assert build['complete'] and build['strict_lint_modes']==3
 assert all(r['returncode']==0 for r in build['records'])
 assert sum(r.get('tests_passed',0) for r in build['records'])==build['native_test_executions']
 original=load(w/'failed-build-v1/failed-version-proof.json');assert original['retained']
 for name,rec in original['files_excluding_regenerable_target'].items():
  p=w/'failed-build-v1'/name;assert p.stat().st_size==rec['bytes'] and sha(p)==rec['sha256']
 records=load(w/'native-run-order.json');assert len(records)==proof['native_commands']
 for i,r in enumerate(records):
  assert r['index']==i and 'completed_utc' in r and not r.get('timeout')
  for kind in ['stdout','stderr']:assert sha(w/r[kind])==r[kind+'_sha256']
 bridges=load(w/'bridge-run-order.json');assert len(bridges)==proof['owned_bridge_launches'] and all('completed_utc' in r for r in bridges)
 wire=[json.loads(x) for x in (w/'native-raw/wire.jsonl').read_text().splitlines()];assert len(wire)==proof['wire_requests']
 assert all(r['index']==i for i,r in enumerate(wire))
 checked=0;stores=0
 for r in proof['seeds']:
  p=w/r['path'];assert inventory(p)==r['inventory'];x=archive.check(p,*archive.maintenance_reference(r['history']));assert x==r['audit'];checked+=x['full_block_crc_bytes'];stores+=1
 for history in ['anonymous','named']:
  pairs=[r['inventory'] for r in proof['seeds'] if r['history']==history];assert len(pairs)==2 and pairs[0]==pairs[1]
 specs=load(w/'maintenance-run-declaration.json');assert len(specs)==36 and len(proof['maintenance'])==36
 for spec,rec in zip(specs,proof['maintenance']):
  assert all(rec[k]==v for k,v in spec.items())
  p=w/rec['path'];directory=p/'archive';assert inventory(directory)==rec['inventory']
  x=archive.check(directory,*archive.maintenance_reference(rec['history']));assert x==rec['audit'];checked+=x['full_block_crc_bytes'];stores+=1
  deletes=[json.loads(line) for line in (p/'deletions.jsonl').read_text().splitlines()]
  boundary=next(i for i,d in enumerate(deletes) if (d['kind'],d['event'],d['ordinal'])==(rec['kind'],rec['event'],rec['ordinal']))
  assert boundary==rec['boundary_index'] and deletes[boundary]==rec['reached_boundary']
  if rec['mode']=='exit':assert boundary==len(deletes)-1 and rec['fault_returncode']==86
  else:assert rec['fault_returncode']==0 and (p/'fault-release').read_bytes()==b'retry with test injection released'
  pre=deletes[:boundary+1];done=[d for d in pre if d['kind']==rec['kind'] and d['event']=='after']
  assert len(done)==rec['successful_selected_kind_before_interrupt']==(0 if rec['event']=='before' else rec['ordinal'])
  if rec['pin']=='held':assert all(d['kind']!='retired' for d in pre)
  completed=[d for d in deletes if d['event']=='after'];assert len(completed)==rec['successful_deletions']
  protected={f'catalog-{g:020d}.ks2' for g in x['chain']}|set(x['segments'])|{'segment-00000000000000000999.ks2','catalog-00000000000000000998.pending'}
  assert sorted(protected)==rec['protected_names'] and all(d['name'] not in protected for d in deletes)
  assert len({d['name'] for d in completed})==len(completed)
  source=w/'maintenance-seeds'/f"{rec['history']}-candidate";old=inventory(source)
  assert set(old)-set(rec['inventory'])=={d['name'] for d in completed}
  assert (directory/'segment-00000000000000000999.ks2').read_bytes()==b'094 untouched crash orphan'
  assert (directory/'catalog-00000000000000000998.pending').read_bytes()==b'094 untouched pending'
  command=records[rec['native_command_start']];assert command['returncode']==rec['fault_returncode']
  events=[json.loads(line) for line in (w/command['stdout']).read_text().splitlines()];assert events==rec['fault_output_events']
  cold=records[rec['native_command_start']+1:rec['native_command_start']+6];assert len(cold)==5
  for r in cold[:2]:assert r['returncode']==0 and json.loads((w/r['stdout']).read_bytes())['passed']
  for r in cold[2:]:assert r['returncode']==0 and json.loads((w/r['stdout']).read_bytes())['result']['rows']==[[6400,6400*6399]]
 assert len(proof['ownership'])==2 and all(r['passed'] for r in proof['ownership'])
 for r in proof['ownership']:
  p=w/'maintenance-fixtures'/f"ownership-{r['history']}";assert json.loads((p/'hold.stdout').read_bytes())['passed']
  x=archive.check(p/'archive',*archive.maintenance_reference(r['history']));checked+=x['full_block_crc_bytes'];stores+=1
 publication=load(w/'publication-proof.json');assert len(publication['cut_points'])==56
 points=policy['publication_cases']['points'];scenarios=['append_delta','append_checkpoint','compact_delta','compact_checkpoint']
 expected=[(s,p,m) for s in scenarios for p in points for m in ['exit','io_error']]
 assert [(r['scenario'],r['point'],r['mode']) for r in publication['cut_points']]==expected
 independent=[]
 for r in publication['cut_points']:
  directory=w/'publication-fixtures'/f"{r['scenario']}-{r['point']}-{r['mode']}"/'archive';x=archive.check(directory,*archive.publication_reference(r['scenario']));checked+=x['full_block_crc_bytes'];stores+=1
  independent.append({'kind':'publication','path':directory.relative_to(w).as_posix(),'audit':x})
 assert len(publication['corruption_cases'])==proof['additional_corruption_rejections']==22
 for i,r in enumerate(publication['corruption_cases']):
  directory=w/'publication-fixtures'/f'corruption-{i}'/'archive'
  try:archive.check(directory,*archive.publication_reference('compact_checkpoint' if r['damage']=='excess_chain' else 'compact_delta'))
  except (AssertionError,KeyError,ValueError,struct.error):pass
  else:raise AssertionError(('corruption accepted',i))
 live=load(w/'live-retry-proof.json');assert len(live['cases'])==15 and not live['failed_cases']
 assert [(r['mode'],r['point']) for r in live['cases']]==[('pause',None),*[('poison',p) for p in points],*[('exit',p) for p in points]]
 for r in live['cases']:
  directory=w/'live-retry-fixtures'/f"{r['mode']}-{r['point']}"/'archive';x=archive.check(directory,*archive.live_reference());checked+=x['full_block_crc_bytes'];stores+=1
  independent.append({'kind':'live','path':directory.relative_to(w).as_posix(),'audit':x})
 assert independent==proof['independent_publication_live_audits']
 oracle=load(w/'oracle-proof.json');assert oracle['complete'] and len(oracle['byte_comparisons'])==2 and len(oracle['cross_reads'])==18 and len(oracle['sqlite_checks'])==24
 for mode in ['baseline','candidate']:
  for p in (w/'binaries'/mode).glob('*.exe'):assert b'KESTREL_RECLAIM_LOG' not in p.read_bytes() and b'KESTREL_FAULT_POINT' not in p.read_bytes()
 return {'passed':True,'native_launches':0,'performance_timer_launches':0,'fixed_fault_cases':107,'additional_corruption_rejections':22,'current_store_full_crc_bytes':checked,'stores_redecoded':stores,'native_test_executions':build['native_test_executions'],'strict_lint_modes':3,'native_commands':len(records),'owned_bridge_launches':len(bridges),'wire_requests':len(wire),'093_still_rejected':True,'supported':'0.3.16'}
if __name__=='__main__':
 w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-094')
 result=audit(w)
 if len(sys.argv)>2:Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result))
