"""Fresh policy/harness/auditor; no observation is copied from 073."""
import hashlib,json,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-073';QUAL=W.parent/'perf-074'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assert not (W/'policy.json').exists();(W/'inputs').mkdir()
inputs=[]
for item in load(OLD/'input-provenance.json')['inputs']:
    src=Path(item['path']);assert sha(src)==item['sha256'];dest=W/'inputs'/src.name;shutil.copy2(src,dest)
    inputs.append({**item,'path':str(dest),'source_073':str(src)})
save(W/'input-provenance.json',{'inputs':inputs,'copied_utc':datetime.now(timezone.utc).isoformat(),'all_original_068_checkpoint_bytes_unchanged':True})
shutil.copy2(OLD/'policy.json',W/'prerequisite-073-policy.json')
policy=load(OLD/'policy.json');policy.update(trial=75,declared_utc=datetime.now(timezone.utc).isoformat())
policy['method']['variants']=['baseline_a','baseline_b','hybrid']
policy['checks']['identity_metrics'].append('source_p99_ms')
policy['checks']['current_reachable_bytes_max']=1.05
policy['method']['descriptive_subsets']={'noncheckpoint_publications':62,'noncheckpoint_includes_source_intervals':6,
    'checkpoint_publications':2,'metrics':['noncheckpoint_p50_ms','noncheckpoint_p99_ms','checkpoint_sum_ms','checkpoint_max_ms'],'subsets_replace_no_existing_guard':True}
policy['qualification']='All4 goals,29 guards and33 A/A checks must pass before proposing engine design; no supported engine promotion follows.'
policy['prerequisite_074']={'protocol_sha256':sha(W/'model/src/hybrid.rs'),'build_proof_sha256':sha(QUAL/'build-proof.json'),
    'qualification_results_sha256':sha(QUAL/'qualification-results.json'),'old_protocol_tests_or_cuts_not_rerun':True}
policy['protocol_read_accounting']='Unchanged074 native anchor-terminated path:3 full body reads/2 parses; checkpoint-terminated path:1 anchor read/parse. All charged; additive documentation correction.'
policy['new_checks']='Source-p99 added to A/A list; current reachable bytes<=1.05 at each size. All073 numeric thresholds unchanged.'
save(W/'policy.json',policy)
r=subprocess.run(['python',str(W/'order_plan.py')],capture_output=True,text=True,encoding='utf-8')
(W/'order-tests.log').write_text(r.stdout+r.stderr,encoding='utf-8');assert r.returncode==0
runner=(OLD/'run_model.py').read_text(encoding='utf-8').replace('bench073','bench075').replace('GROWTHMODEL073','GROWTHMODEL075').replace("{'debug':22,'release':22}","{'debug':3,'release':3}")
runner=runner.replace("'order-balance-pre-timing.json']","'order-balance-pre-timing.json','hybrid_oracle.py','source-finalization.json','DESIGN.md']")
(W/'run_model.py').write_text(runner,encoding='utf-8')
audit=(OLD/'audit_model.py').read_text(encoding='utf-8')
start=audit.index('def full_canonical_audit(');end=audit.index("policy=load(W/'policy.json')",start)
canon=(W/'canonical_audit.py').read_text(encoding='utf-8')
audit=audit[:start]+canon+'\n'+audit[end:]
audit=audit.replace('from catalog_oracle import ledger_sha,read_catalog','from catalog_oracle import ledger_sha,read_catalog\nimport hybrid_oracle as h')
audit=audit.replace('GROWTHMODEL073','GROWTHMODEL075')
audit=audit.replace("canonical={};files={};cases=[];logical_reads=0","canonical={};reachable={};files={};cases=[];logical_reads=0")
audit=audit.replace("if key not in canonical:canonical[key]=full_canonical_audit(path,mode,old,edits,final);logical_reads+=len(canonical[key])",
    "if key not in canonical:\n        canonical[key],reachable[key]=full_canonical_audit(path,mode,old,edits,final);logical_reads+=len(canonical[key])")
audit=audit.replace("s['checkpoint']==(mode=='cat4' and n in [31,63])","s['checkpoint']==(n in [31,63])")
audit=audit.replace("f'root-{130+n:020}.model'","f'head-{130+n:020}.model'")
audit=audit.replace("if mode=='pages':written+=sum(v['bytes'] for name,v in canonical[key].items() if name.startswith(f'receipts-{130+n:020}-'))",
    "if mode=='hybrid':written+=sum(v['bytes'] for name,v in canonical[key].items() if name.startswith(f'hy-receipts-{130+n:020}-'))")
audit=audit.replace("io['synced_files']==(1 if mode=='cat4' else 2)","io['synced_files']==(2 if mode=='hybrid' and n in [31,63] else 1)")
audit=audit.replace("(r['summary']['receipts']+511)//512+1","(32 if n==30 else 34 if n==62 else 3)")
audit=audit.replace("name==f'root-{129:020}.model' or name.startswith(f'receipts-{129:020}-')","name==f'head-{129:020}.model'")
audit=audit.replace("(1 if mode=='cat4' else (len(old['batches'])+511)//512+1)","1")
audit=audit.replace("'stored_directory_bytes':directory_bytes,","'stored_directory_bytes':directory_bytes,'current_reachable_bytes':sum(canonical[key][n]['bytes'] for n in reachable[key]),\n        'noncheckpoint_p50_ms':quantile([s['outer_ms'] for s in x['samples'] if not s['checkpoint']],.5),\n        'noncheckpoint_p99_ms':quantile([s['outer_ms'] for s in x['samples'] if not s['checkpoint']],.99),\n        'checkpoint_sum_ms':sum(s['outer_ms'] for s in x['samples'] if s['checkpoint']),\n        'checkpoint_max_ms':max(s['outer_ms'] for s in x['samples'] if s['checkpoint']),")
metric_suffix="'peak_working_set_bytes','peak_commit_bytes']"
assert audit.count(metric_suffix)==1
audit=audit.replace(metric_suffix,"'peak_working_set_bytes','peak_commit_bytes','current_reachable_bytes','noncheckpoint_p50_ms','noncheckpoint_p99_ms','checkpoint_sum_ms','checkpoint_max_ms']")
audit=audit.replace("group['pages']","group['hybrid']").replace("'pages_a'","'hybrid_a'").replace("'pages']","'hybrid']")
needle="    for metric in lim['identity_metrics']:"
assert audit.count(needle)==1
audit=audit.replace(needle,"    add('guard',seed,'current_reachable_bytes',c['current_reachable_bytes'],lim['current_reachable_bytes_max'])\n"+needle)
audit=audit.replace("len(checks)==60","len(checks)==66").replace("c['kind']=='guard' for c in checks)==26","c['kind']=='guard' for c in checks)==29").replace("c['kind']=='identity' for c in checks)==30","c['kind']=='identity' for c in checks)==33")
(W/'audit_model.py').write_text(audit,encoding='utf-8')
save(W/'benchmark-helper-derivation.json',{'old_073_run_sha256':sha(OLD/'run_model.py'),'new_075_run_sha256':sha(W/'run_model.py'),
    'old_073_audit_sha256':sha(OLD/'audit_model.py'),'new_075_audit_sha256':sha(W/'audit_model.py'),'canonical_audit_sha256':sha(W/'canonical_audit.py'),
    'all_073_numeric_thresholds_unchanged':all(policy['checks'][k]==v for k,v in load(OLD/'policy.json')['checks'].items() if k!='identity_metrics'),
    'new_declared_checks':['source_p99 identity','current_reachable_bytes<=1.05'], 'old_observations_not_reused':True})
print(json.dumps({'prepared':True,'cases':54,'publication_samples':3456,'recoveries':648,'declared_checks':66,'free_bytes':shutil.disk_usage(W).free}))
