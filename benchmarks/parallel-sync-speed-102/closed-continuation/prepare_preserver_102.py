"""Prepare exact qualified chunk/ZIP engine with complete102 replay envelope."""
from pathlib import Path
import ast,hashlib,json
H=Path('D:/Codex/Kestrel/work')
old=(H/'preserve_101.py').read_text(encoding='utf-8')
engine=old[old.index('directories=[];'):old.index('# Import only the restored pure auditors')]
basis=(H/'preserve_098.py').read_text(encoding='utf-8')
assert engine==basis[basis.index('directories=[];'):basis.index('# Load every pure audit dependency')]
prefix='''"""Complete fixed native/service102 preservation and zero-Native restored replay."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,shutil,sys,zipfile,zlib
sys.dont_write_bytecode=True
ROOT=Path('D:/Codex/Kestrel');W=ROOT/'work/perf-102'
OUT=ROOT/'outputs/kestrel-sql/benchmarks/parallel-sync-speed-102'
RESTORE=ROOT/'work/restored-parallel-sync-speed-102'
CHUNK=64*1024*1024;PART=80*1024*1024
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):
 assert not p.exists(),p
 p.write_text(json.dumps(v,indent=2)+'\\n',encoding='utf-8',newline='\\n')
def excluded(p):
 rel=p.relative_to(W);return rel.parts[0]=='target-build' or '__pycache__' in rel.parts or p.suffix=='.pyc'
assert not OUT.exists() and not RESTORE.exists()
guards=sorted((ROOT/'work').glob('guard-prepreserve-102v2-*.json'));assert guards;guard=load(guards[-1])
assert guard['active_processes']==[] and guard['verified_idle_terminal_reset'] and guard['reset_phase']=='wait-expired-no-source-mutated'
assert guard['reset_status_utc']=='2026-10-09T10:33:06.6265823Z' and guard['fresh_task_state']=='Ready' and guard['fresh_task_last_result']==2 and guard['old_task_state']=='Disabled'
expected=load(W/'complete-audit-proof.json');assert expected['complete_original_and_restored_semantic_audit_passed'] and not expected['performance_qualified'] and not expected['adoption_qualified']
assert expected['native']['cases']==expected['service']['cases']==144 and expected['service']['offered']==expected['service']['successful']==1872000 and expected['service']['lost']==0
assert expected['native']['identity_failed']==7 and expected['native']['candidate_guards_failed']==2 and expected['native']['goals_failed']==1
freeze=load(W/'timing-freeze.json')['sha256']|load(W/'timing-operational-supplement.json')['sha256'];assert all(sha(W/n)==h for n,h in freeze.items())
helpers=W/'continuation-helpers';assert not helpers.exists();helpers.mkdir()
for p in sorted((ROOT/'work').iterdir()):
 if p.is_file() and '102' in p.name and p.name!='preserve-102.log':shutil.copy2(p,helpers/p.name)
assert sha(ROOT/'work/check_processes_102_v2.ps1')==sha(W/'check_processes_102_v2.ps1')
save(W/'preservation-plan.json',{'declared_utc':datetime.now(timezone.utc).isoformat(),'before_copy_hash_packaging_or_restoration':True,'chunk_bytes':CHUNK,'part_logical_bytes_max':PART,'complete_native_and_service_raw_outcomes_stalls_samples_source_binaries_receipts_failed_setup_and_empty_directories':True,'tmp_and_unit_stores_included':True,'all_originals_including_regenerable_caches_retained':True,'no_native_or_timer_launches':True,'no_GitHub_upload_or_local_cleanup':True})
save(W/'decision-summary.json',expected)
'''
suffix='''# All restored pure dependencies; no original auditors, Native or timers.
sys.path.insert(0,str(RESTORE));name='audit_complete_102'
spec=importlib.util.spec_from_file_location(name,RESTORE/(name+'.py'));module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
assert Path(module.__file__).resolve().is_relative_to(RESTORE.resolve())
replayed=module.audit(RESTORE);assert replayed==expected
check_exact();assert all(sha(W/n)==h for n,h in freeze.items())
assert {p.relative_to(W).as_posix() for p in W.rglob('*') if p.is_dir() and not excluded(p)}==set(directories)
save(OUT/'restored-audit-proof.json',{'passed':True,'utc':datetime.now(timezone.utc).isoformat(),'native_launches':0,'performance_timer_launches':0,'restored_tree':str(RESTORE),'all144native_and144service_full_and_halves_full_history_CRC_NumPy_ACK_conservation_quantiles_resources_lifecycle_backlog_smokes_SQLite_and_frozen_failed_setup_recomputed':True,'all_dependencies_imported_from_restored_tree':True,'every_file_SHA_size_set_and_original_and_restored_directory_set_exact_after_audit':True,'replay_equals_original_complete_audit':True})
save(OUT/'preservation-proof.json',{'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'parts':parts,'files':len(entries),'directories':len(directories),'logical_bytes':sum(v['bytes'] for v in entries.values()),'archive_layout_sha256':entries['archive-layout.json']['sha256'],'chunks':chunk_records,'all_member_CRC_sizes_order_offsets_complete_file_SHA_and_exact_file_directory_sets_passed':True,'all_originals_and_frozen_inputs_retained_unchanged':True,'tmp_and_fresh_unit_stores_included':True,'only_regenerable_target_and_python_caches_excluded':True,'remote_backup_verified':False,'no_recent_raw_deleted':True})
for n in ['policy.json','service-policy.json','declaration-proof.json','decision-summary.json','complete-audit-proof.json','source-derivation.json','preparation-proof.json','build-proof.json','preperformance-proof.json','backlog-harness-derivation.json','helper-validation.json','validator-derivation.json','reset-expiry-guard-derivation.json','timing-operational-supplement.json','evidence-inventory.json','directory-inventory.json','preservation-plan.json','audit_complete_102.py','audit_native_102.py','audit_service_102.py','audit_backlog_102.py','archive_audit_095.py','archive_audit_096.py','archive_audit_099.py','audit_service_095.py','audit_publication_100.py','outcomes_098.py','run_native_102.py','run_native_102_v2.py','run_service_102.py','run_service_102_v2.py','hardware.json','toolchain.json']:
 shutil.copy2(W/n,OUT/n)
(OUT/'REPRODUCE.md').write_text("""# Scoped synchronization speed102: rejected

Supported0.3.16 is unchanged and0.3.17 remains pending. The42 source files are exactly101. NormalA/B are the same binary, async-reclaim plus benchmark-shutdown; C adds onlyparallel-sync-101. Both originalsync_all calls and join-before-rename/ACK remain. This is an isolatedasync baseline, not a direct supported0.3.16 comparison. No061/tracing/fault/profile feature or dependency change in timed artifacts.

The original policy was declared before source/build/timing. Native144 cases use24 rounds/two independently balanced12-round halves, both anonymous/named histories and everyA/B/C permutation twice perhistory/half. The exact uninstrumented100 probe performs512 durable100-row appends percase; all513 historical catalogs/receipts and current full data/CRC are audited. All thirtyA/A andcandidate guards and twelve goals remain fixed. Native rejects with7 identity,2 candidate and1 goal failure. Service144 cases use24 rounds/two independently balanced12-round halves, everypermutation twice perprofile/half,1M startingrows,64clients,100-row appends,read2000offers/s8s and25%-write500/s20s. Original093 arrival/drain/request/connection/ACK/resource boundaries and literal gates remain. All1,872,000offers reconcile with raw rows/late data/receipts/CRC/NumPy and actual graceful initial+cold joins. Numerical misses are qualification failures, never deleted or selectively rerun. Complete service decisions remain in decision-summary and archivedaudit.json.

Four exact feature suites executed390 fresh tests and two strict lints. Four finite12000-group backlog cases, four native and two service excluded smokes,24 fresh SQLite/cold CLI controls and29 pretime synthetic invalid controls pass. Prior101 recovery682tests/576coupled/72publication/18source/22corruption/oldformat/byte controls are explicitly reused, not rerun or recounted. Real physical powerloss/diskexhaustion and broad integrated .17 gates remain unqualified.

Every full source/binary/stdin/stdout/stderr/controller/process/lifecycle/resource/raw sample/store/history/receipt/emptydirectory and failed setup/guard/startup is retained. The old reset worker expired at2026-10-09T10:33:06.6265823Z without source mutation. Originalwaiting-state guards/runners and exact stopped startup remain; v2 only validates this actualterminal state. No rearm or reset/task/source mutation and no numeric or semantic change. All13630 original frozen files plus8 operational inputs retain their hashes. Hash/copy/package/audit work happens only after the complete timed controller exits.

Verify ZIP SHA sidecars and every member CRC/order/size; archive-layout defines ordered64MiB chunks in80MiB logical bounded parts. Reassemble exact offsets and directory-inventory includingempty directories. Verify each completeSHA/size and exact original/restored file+directory sets. Only inventoried target-build/Python caches are excluded, with originals retained. tmp and all fresh unit stores are included. Closed packager stdout is separately hashed after actualexit.

With recordedPython3.12.10 andNumPy2.2.5, import audit_complete_102 only from the restoredtree and call audit(ABSOLUTE_RESTORED_PATH). It recomputes nativefull+smoke/backlog/servicefull+half/rawquantiles/conservation/resources/gracefuljoin/completehistoricalandcurrentCRC/ACK/NumPy and SQLite controls, sources/buildlogs/artifacts/frozenfailures and input provenance. The original service auditor's sole attemptedJSON output is captured in memory; all checks and gates remain exact. Return must equal complete-audit-proof.json. No Native/timer launches or existing-file writes. Recheck completeSHA/size/file+directory sets after replay.

All evidence is private/local onD. No102remote backup verified or rawcleanup occurred. No performance adoption, competitor sweep, allbenchmark win, supportedengine change or .17release follows. New work needs a separately justified code hypothesis and new number; do not add rounds/select passing scopes/change gates or reinterpret rejected098/099/100/102.
""",encoding='utf-8',newline='\\n')
print(json.dumps({'complete':True,'parts':len(parts),'files':len(entries),'directories':len(directories),'logical_bytes':sum(v['bytes'] for v in entries.values()),'exact_restored_audit':True}),flush=True)
'''
target=H/'preserve_102.py';assert not target.exists();text=prefix+engine+suffix;ast.parse(text);target.write_text(text,encoding='utf-8',newline='\n')
p=H/'preserver-engine-102-proof.json';assert not p.exists();p.write_text(json.dumps({'qualified_engine_source':str(H/'preserve_098.py'),'engine_sha256':hashlib.sha256(engine.encode()).hexdigest(),'engine_reused_byte_exact':True,'changes':'complete102 native/service decisions and terminal reset envelope/restored pure audit only','target_sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'prepared':str(target),'engine_byte_exact':True}))
