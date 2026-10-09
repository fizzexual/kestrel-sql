"""Complete101 correctness/recovery replay; no timing, Native or file writes."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import audit_coupling_101 as coupled
import audit_oracles_101 as oracles
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def audit(w):
 c=coupled.audit(w);o=oracles.audit(w);f=oracles.audit(w/'failed-oracles-v1',failed=True)
 assert c==load(w/'offline-audit-proof-v2.json') and o==load(w/'oracle-audit-proof-101.json')
 assert f==load(w/'failed-oracle-audit-proof.json')
 repair_oracle=load(w/'oracle-repair-101.json')
 assert repair_oracle['source_binary_policy_case_order_expectations_unchanged'] and sha(w/'run_oracles_101.py')==repair_oracle['repaired_runner_sha256'] and sha(w/'audit_oracles_101.py')==repair_oracle['repaired_auditor_sha256']
 old_policy=load(w/'failed-oracles-v1/oracle-policy-101.json');new_policy=load(w/'oracle-policy-101.json');assert {k:v for k,v in old_policy.items() if k!='declared_utc'}=={k:v for k,v in new_policy.items() if k!='declared_utc'}
 assert c['new_native_tests']==682 and c['new_worker_unit_stores']==133 and c['new_overlap_unit_stores']==35
 failure=load(w/'coupled-setup-failure.json');repair=load(w/'coupled-setup-completion.json')
 assert failure['actual_exit_code']==1 and failure['external_native_launches']==0 and repair['complete'] and repair['original_failure_retained']
 assert sha(w/'prepare_coupling_101.py')==failure['failed_helper_sha256'] and sha(w/'coupled-policy-101.json')==failure['policy_sha256']==repair['policy_unchanged_sha256']
 for d in load(w/'coupled-helper-derivation.json'):
  assert sha(w/(d['original']+'.original'))==d['original_sha256'] and sha(w/d['derived'])==d['derived_sha256']
 assert load(w/'auxiliary-declaration.json')['existing_engine_worker_and_all_tests_byte_exact']
 return {'correctness_recovery_passed':True,'trial':101,'supported':'0.3.16','fresh_native_tests':682,'strict_lint_modes':5,'coupled':c,'oracles':o,'failed_setup_replay':f,'qualifying_external_native_commands':c['native_commands']+o['native_commands'],'all_external_native_commands_including_failed_setup':c['native_commands']+o['native_commands']+f['native_commands'],'full_qualifying_reference_crc_bytes':c['case_crc_reference_bytes']+c['unit_crc_reference_bytes']+o['full_reference_crc_bytes'],'failed_setup_reference_crc_bytes':f['full_reference_crc_bytes'],'original_and_all_failed_setup_bytes_retained':True,'performance_qualified':False,'adoption_qualified':False,'physical_power_loss_qualified':False,'version017_qualified':False,'native_launches':0,'performance_timer_launches':0}
if __name__=='__main__':
 w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-101');r=audit(w);p=w/'audit.json';assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({k:v for k,v in r.items() if k not in ['coupled','oracles','failed_setup_replay']}))
