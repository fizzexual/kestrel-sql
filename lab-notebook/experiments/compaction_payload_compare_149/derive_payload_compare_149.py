"""New complete149 cohort after closed148; no selected prefix retiming."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json
R=Path('D:/Codex/Kestrel/work');P=R.parent/'outputs/kestrel-sql';prior=P/'experiments/compaction_payload_compare_148'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):
    assert not p.exists(),p
    if p.suffix=='.py':ast.parse(s)
    p.write_text(s.rstrip()+'\n',encoding='utf-8',newline='\n')
assert load(R/'phase148-storage-cleanup-proof.json')['completed148_prefix_stores_closed']
assert load(R/'phase148-cleanup-review-actual-exits.json')['actual_exit']==0
assert not (R/'perf-148').exists() and not (R/'perf-149').exists()
parents={}
for name in ['prepare_phase_compare_148.py','run_phase_compare_148.py','audit_phase_compare_148.py','smoke_phase_compare_148.py',
    'activity_worker_148.ps1','launch_phase_compare_148.ps1','audit_lifecycle_receipts_148.py','launch_preflight_phase148.ps1','launch_audits_phase148.ps1']:
    src=prior/name;parents[name]=sha(src);old=src.read_text(encoding='utf-8');new=old.replace('148','149')
    if name=='prepare_phase_compare_148.py':
        new=new.replace("load(R/'payload147-publication-proof.json')['private_main']","load(R/'phase148-publication-proof.json')['private_main']")
        new=new.replace('derive_payload_compare_149.py','derive_payload_compare_149.py')
    if name=='audit_phase_compare_148.py':
        assert old[old.index('def rows('):old.index('def nearest(')]==new[new.index('def rows('):new.index('def nearest(')]
        new=new.replace('phase149-preflight-quiet-v2-proof.json','phase149-preflight-quiet-proof.json')
    if name=='smoke_phase_compare_148.py':
        new=new.replace('import json,subprocess,sys,traceback','import json,subprocess,sys,traceback,time')
        needle="    for name in ['ordered','clustered']:\n"
        assert new.count(needle)==1
        quiet='''    # All preparations/protocol checks precede a fresh continuous quiet interval.
    # This uses the already-approved smoke controller owner, not another helper.
    began=namespace['utc']();start=time.monotonic();quiet_since=None;resets=0
    while True:
        assert time.monotonic()-start<7200,'Quiet deadline before any preflight native case'
        probe=worker.check('preflight_continuous_quiet');now=time.monotonic()
        if probe['exit']==0:
            if quiet_since is None:quiet_since=now
            if now-quiet_since>=120:break
        else:quiet_since=None;resets+=1
        time.sleep(10)
    quiet_proof={'started_utc':began,'completed_utc':namespace['utc'](),'continuous_quiet_seconds':now-quiet_since,'busy_resets':resets,'no_native_cases_started':True,'worker_identity':worker.identity}
    for dest in [R/'phase149-preflight-quiet-proof.json',W/'preflight-quiet-proof.json']:
        assert not dest.exists();dest.write_text(json.dumps(quiet_proof,indent=2)+'\\n',encoding='utf-8',newline='\\n')
'''
        new=new.replace(needle,quiet+needle)
        new=new.replace("    stopped=worker.stop();worker=None;assert stopped['actual_exit']==0 and not stopped['forced_owned_worker_kill']", "    stopped=worker.stop();worker=None;assert stopped['actual_exit']==0 and not stopped['forced_owned_worker_kill']\n    quiet_proof['metadata_worker_actual_exit']=0\n    for dest in [R/'phase149-preflight-quiet-proof.json',W/'preflight-quiet-proof.json']:dest.write_text(json.dumps(quiet_proof,indent=2)+'\\n',encoding='utf-8',newline='\\n')")
    write(R/name.replace('148','149'),new)
ready=(prior/'append_phase148_ready.py').read_text(encoding='utf-8').replace('148','149')
ready=ready.replace("load(R/'payload147-closed-next-proof.json')['new_sha256']","load(R/'phase148-closed-next-proof.json')['new_sha256']")
ready=ready.replace('Next unused149+','Next unused150+')
write(R/'append_phase149_ready.py',ready)
declared=(prior/'append_phase148_declared.py').read_text(encoding='utf-8').replace('148','149').replace('Nextunused149+','Nextunused150+')
write(R/'append_phase149_declared.py',declared)
write(R/'payload149-controller-derivation.json',json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'parent_sources':parents,'before_any149_native_case':True,'new_complete216_cohort_after148_closed':True,'no_selected148_retiming':True,'same_engine_binaries_inputs_schedule_numerical_gates':True,'all_prerequisites_reused':True,'quiet_wait_embedded_in_exact_verified_smoke_owner':True},indent=2))
print('Fresh complete149 controllers derived; no engine build or native case')
