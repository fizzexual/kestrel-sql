"""Complete deterministic correctness/recovery replay using only this evidence tree."""
from pathlib import Path
import hashlib, json, sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import audit_coupling_103 as coupled
import audit_oracles_103 as oracles
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def audit(w):
    c=coupled.audit(w);o=oracles.audit(w)
    assert c==load(w/'offline-audit-proof-v2.json') and o==load(w/'oracle-audit-proof-103.json')
    assert c['coupled_cases']==832 and c['native_commands']==12064 and c['ack_batches']==53456
    assert c['owner_rejections']==6240 and c['unacknowledged_committed_batches']==16
    assert o['publication_fault_cases']==104 and o['source_fault_cases']==26 and o['corruption_cases']==22
    assert o['legacy_formats']==2 and o['normal_candidate_byte_fixtures']==4 and o['native_commands']==1065
    assert c['new_native_tests']==916 and c['strict_lint_modes']==6
    assert c['new_worker_unit_stores']==342 and c['new_overlap_unit_stores']==148 and c['new_protocol_unit_stores']==30
    first=load(w/'build-failure.json');assert first['records'][-1]['step']=='candidate-lint'
    first_tests=sum(r.get('tests_passed',0) for r in first['records']);assert first_tests==916
    assert first['records'][-1]['returncode']!=0 and all(r['returncode']==0 for r in first['records'][:-1])
    failure=load(w/'failed-preparation-v1/proof.json')
    assert failure['actual_exit_code']==1 and failure['before_candidate_source_write_build_or_native']
    assert sha(w/'failed-preparation-v1/prepare_103.py')==failure['failed_helper_sha256']
    assert b'AssertionError' in (w/'failed-preparation-v1/actual-stderr.txt').read_bytes()
    repair=load(w/'source-derivation-v3.json')
    assert {n for n in repair['previous'] if repair['previous'][n]!=repair['final'][n]}=={'src/reusable_sync_tests_103.rs'}
    assert repair['all_production_source_bytes_exact_to_first_candidate']
    for name,record in load(w/'recovery-helper-derivation.json')['helpers'].items():
        old=name.replace('_103','_101')
        assert sha(w/'recovery-driver-basis'/old)==record['basis_sha256'] and sha(w/name)==record['generated_sha256']
    pre=load(w/'recovery-preflight-proof.json')
    assert pre['unit_stores']==c['unit_stores'] and pre['overlap_stores']==c['overlap_unit_stores']
    assert pre['protocol_fixtures']==c['protocol_unit_stores']
    assert pre['qualifying_v3_test_executions']==916 and pre['total_new_test_executions_including_first_lint_rejection']==1832
    assert pre['full_reference_crc_bytes']==c['unit_crc_reference_bytes']==342112
    return {'correctness_recovery_passed':True,'trial':103,'supported':'0.3.16',
        'qualifying_current_source_native_tests':916,'preserved_first_build_successful_tests':first_tests,
        'all_new_test_executions_including_first_lint_rejection':916+first_tests,'strict_lint_modes':6,
        'coupled':c,'oracles':o,'qualifying_external_native_commands':c['native_commands']+o['native_commands'],
        'full_reference_crc_bytes':c['case_crc_reference_bytes']+c['unit_crc_reference_bytes']+o['full_reference_crc_bytes'],
        'original_and_all_failed_preparation_build_bytes_retained':True,'performance_qualified':False,
        'adoption_qualified':False,'physical_power_loss_qualified':False,'version017_qualified':False,
        'native_launches':0,'performance_timer_launches':0}
if __name__=='__main__':
    w=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Codex/Kestrel/work/perf-103')
    result=audit(w);p=w/'audit.json';assert not p.exists()
    p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['coupled','oracles']}),flush=True)
