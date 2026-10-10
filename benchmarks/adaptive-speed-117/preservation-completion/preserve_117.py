"""Exact rejected117 raw preservation and restored Native-only decision replay."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,re,shutil,sys,zipfile,zlib
sys.dont_write_bytecode=True
ROOT=Path('D:/Codex/Kestrel');W=ROOT/'work/perf-117'
OUT=ROOT/'outputs/kestrel-sql/benchmarks/adaptive-speed-117'
RESTORE=ROOT/'work/restored-adaptive-speed-117'
CHUNK=64*1024*1024;PART=80*1024*1024
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):
 assert not p.exists(),p
 p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
def excluded(p):
 rel=p.relative_to(W);return rel.parts[0].startswith('target-build') or '__pycache__' in rel.parts or p.suffix=='.pyc'
assert not OUT.exists() and not RESTORE.exists()
guard_path=sorted((ROOT/'work').glob('guard-prepreserve-117-*.json'))[-1];guard=load(guard_path)
assert not guard['active_processes'] and guard['verified_idle_terminal_reset']
assert guard['reset_phase']=='wait-expired-no-source-mutated' and guard['reset_status_utc']=='2026-10-09T10:33:06.6265823Z'
assert guard['fresh_task_state']=='Ready' and guard['fresh_task_last_result']==2 and guard['old_task_state']=='Disabled'
expected=load(W/'complete-audit-proof.json');assert expected['complete'] and expected['native_correctness_passed']
assert expected['fresh_tests']==820 and expected['strict_lints']==5 and expected['native']['cases']==324 and expected['service']['cases']==252 and expected['service']['all_specs']==load(W/'policy.json')['service_cases']
assert not expected['release017_qualified'] and not expected['performance_qualified'] and expected['service']['status']=='UNSTARTED_UNTESTED'
freeze=load(W/'timing-freeze.json')['files'];assert all(sha(W/n)==h for n,h in freeze.items())
helpers=W/'continuation-helpers';assert not helpers.exists();helpers.mkdir()
for p in sorted((ROOT/'work').iterdir()):
 if p.is_file() and re.search(r'(?<!\d)117(?!\d)',p.name) and p.name not in ['preserve-117.log']:shutil.copy2(p,helpers/p.name)
save(W/'preservation-plan.json',{'declared_utc':datetime.now(timezone.utc).isoformat(),'before_copy_hash_packaging_or_restoration':True,
 'chunk_bytes':CHUNK,'part_logical_bytes_max':PART,'all_raw_failed_partial_source_binary_helper_test_store_tmp_and_empty_directory_material':True,
 'all_originals_retained':'Only inventoried regenerable target and Python caches excluded from archive, originals remain.',
 'all252_service_cases_unstarted_preserved':True,'no_Native_timer_GitHub_or_cleanup':True})
save(W/'decision-summary.json',expected)
directories=[]; excluded_files=[]; entries={}
assert not W.is_junction() and not W.is_symlink()
for p in sorted(W.rglob('*')):
    assert not p.is_symlink() and not p.is_junction() and p.resolve().is_relative_to(W.resolve()),p
    if excluded(p):
        if p.is_file():excluded_files.append({'path':p.relative_to(W).as_posix(),'bytes':p.stat().st_size})
        continue
    if p.is_dir():directories.append(p.relative_to(W).as_posix())
save(W/'directory-inventory.json',{'directories':directories,'including_empty_markers':True,
    'only_regenerable_target_and_python_caches_excluded':True})
for p in sorted(W.rglob('*')):
    if p.is_file() and not excluded(p):entries[p.relative_to(W).as_posix()]={'bytes':p.stat().st_size,'sha256':sha(p)}
save(W/'evidence-inventory.json',{'entries':entries,'files':len(entries),
    'logical_bytes':sum(v['bytes'] for v in entries.values()),'excluded_regenerable_files':excluded_files,
    'all_originals_retained':True,'complete_outcomes_and_unmodified_failed_helpers_retained':True})
entries['evidence-inventory.json']={'bytes':(W/'evidence-inventory.json').stat().st_size,'sha256':sha(W/'evidence-inventory.json')}
units=[]
for file_index,(name,v) in enumerate(sorted(entries.items())):
    count=max(1,(v['bytes']+CHUNK-1)//CHUNK)
    for chunk in range(count):
        units.append({'member':f'payload/{file_index:08d}/{chunk:06d}','path':name,'offset':chunk*CHUNK,
            'bytes':min(CHUNK,max(0,v['bytes']-chunk*CHUNK)),'chunk_index':chunk,'chunks':count})
save(W/'archive-layout.json',{'chunk_bytes':CHUNK,'part_logical_bytes_max':PART,'units':units,
    'metadata_layout_member_added_separately_to_avoid_self_reference':True,
    'source_logical_file_metadata_in_evidence_inventory_plus_layout_SHA_in_preservation_proof':True})
layout=W/'archive-layout.json'; entries[layout.name]={'bytes':layout.stat().st_size,'sha256':sha(layout)}
assert layout.stat().st_size<CHUNK
units=[{'member':'metadata/archive-layout.json','path':layout.name,'offset':0,'bytes':layout.stat().st_size,'chunk_index':0,'chunks':1},*units]
groups=[]; current=[]; logical=0
for unit in units:
    assert unit['bytes']<=CHUNK
    if current and logical+unit['bytes']>PART:groups.append(current);current=[];logical=0
    current.append(unit);logical+=unit['bytes']
if current:groups.append(current)
OUT.mkdir();RESTORE.mkdir();parts=[]; restored_offsets={}; chunk_records=[]
for name in sorted(directories,key=lambda x:(len(Path(x).parts),x)):
    dest=(RESTORE/name).resolve(); assert dest.is_relative_to(RESTORE.resolve());dest.mkdir(exist_ok=True)
shutil.copy2(layout,OUT/layout.name)
for index,group in enumerate(groups):
    package=OUT/f'evidence-{index+1:03d}.zip'
    with zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as z:
        for unit in group:
            with (W/unit['path']).open('rb') as src,z.open(unit['member'],'w',force_zip64=True) as dest:
                src.seek(unit['offset']); remaining=unit['bytes']
                while remaining:
                    block=src.read(min(1024*1024,remaining));assert block
                    dest.write(block);remaining-=len(block)
    with zipfile.ZipFile(package) as z:
        assert z.namelist()==[u['member'] for u in group]
        for unit in group:
            dest=(RESTORE/unit['path']).resolve();assert dest.is_relative_to(RESTORE.resolve())
            offset=restored_offsets.get(unit['path'],0);assert offset==unit['offset']
            if unit['chunk_index']==0:assert not dest.exists()
            else:assert dest.exists() and dest.stat().st_size==offset
            dest.parent.mkdir(parents=True,exist_ok=True); digest=hashlib.sha256();crc=0;read=0
            with z.open(unit['member']) as src,dest.open('ab') as out:
                while block:=src.read(1024*1024):
                    out.write(block);read+=len(block);digest.update(block);crc=zlib.crc32(block,crc)
            assert read==unit['bytes'] and crc==z.getinfo(unit['member']).CRC
            restored_offsets[unit['path']]=offset+read
            chunk_records.append({**unit,'package':package.name,'sha256':digest.hexdigest(),'crc32':crc})
    assert sum(u['bytes'] for u in group)<=PART
    h=sha(package);(OUT/(package.name+'.sha256')).write_text(h+'  '+package.name+'\n')
    parts.append({'name':package.name,'sha256':h,'bytes':package.stat().st_size,'logical_bytes':sum(u['bytes'] for u in group),'members':len(group)})
    print(json.dumps({'verified_part':index+1,'of':len(groups),'member_CRC_size_and_order':True}),flush=True)
def check_exact():
    assert {p.relative_to(RESTORE).as_posix() for p in RESTORE.rglob('*') if p.is_file()}==set(entries)
    assert {p.relative_to(RESTORE).as_posix() for p in RESTORE.rglob('*') if p.is_dir()}==set(directories)
    assert {p.relative_to(W).as_posix() for p in W.rglob('*') if p.is_file() and not excluded(p)}==set(entries)
    for name,v in entries.items():
        assert (W/name).stat().st_size==v['bytes'] and sha(W/name)==v['sha256'],name
        assert (RESTORE/name).stat().st_size==v['bytes'] and sha(RESTORE/name)==v['sha256'],name
print(json.dumps({'phase':'exact_original_and_restored_inventory_checks_before_audit'}),flush=True)
check_exact()
# All restored pure dependencies; no original auditors, Native or timers.
sys.path.insert(0,str(RESTORE));name='audit_complete_117'
spec=importlib.util.spec_from_file_location(name,RESTORE/(name+'.py'));module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
assert Path(module.__file__).resolve().is_relative_to(RESTORE.resolve())
print(json.dumps({'phase':'restored_complete_pure_audit_started'}),flush=True)
replayed=module.audit(RESTORE);assert replayed==expected
print(json.dumps({'phase':'restored_complete_pure_audit_passed_final_exact_inventory_pending'}),flush=True)
check_exact();assert all(sha(W/n)==h for n,h in freeze.items())
assert {p.relative_to(W).as_posix() for p in W.rglob('*') if p.is_dir() and not excluded(p)}==set(directories)
save(OUT/'restored-audit-proof.json',{'passed':True,'utc':datetime.now(timezone.utc).isoformat(),'native_launches':0,'performance_timer_launches':0,
 'restored_tree':str(RESTORE),'complete_source_build_recovery_all324native_raw_CRC_ACK_SQL_quantiles_full_and_half42_goals_profile_and_all252_service_unstarted_recomputed':True,
 'all_dependencies_imported_from_restored_tree':True,'every_file_SHA_size_set_and_original_and_restored_directory_set_exact_after_audit':True,'replay_equals_original_complete_audit':True})
save(OUT/'preservation-proof.json',{'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'parts':parts,'files':len(entries),'directories':len(directories),
 'logical_bytes':sum(v['bytes'] for v in entries.values()),'archive_layout_sha256':entries['archive-layout.json']['sha256'],'chunks':chunk_records,
 'all_member_CRC_sizes_order_offsets_complete_file_SHA_and_exact_file_directory_sets_passed':True,'all_originals_and_frozen_inputs_retained_unchanged':True,
 'tmp_and_fresh_unit_stores_included':True,'only_regenerable_target_and_python_caches_excluded':True,'remote_backup_verified':False,'no_recent_raw_deleted':True})
for name in ['policy.json','declaration-proof.json','complete-audit-proof.json','decision-summary.json','build-proof-v2.json','preparation-proof-v2.json','build-proof-v3.json','preparation-proof-v3.json','build-repair-v3.json','repaired-prefix-proof.json','preflight-audit-proof.json','preperformance-proof.json','timing-freeze.json','native-audit.json','native-rejection-decision.json','native-profile-proof.json','prefix-audit-proof.json','closure-preparation-proof.json','controller-exit-observation.json','harness-derivation-proof.json','evidence-inventory.json','directory-inventory.json','preservation-plan.json','audit_complete_117.py','audit_native_117_v3.py','audit_prefix_117_v4.py','audit_service_117_v3.py','audit_preflight_117_v3.py','archive_audit_099.py','outcomes_098.py']:
 shutil.copy2(W/name,OUT/name)
(OUT/'REPRODUCE.md').write_text(f'''# Byte-buffered receipt hashing trial117: rejected release qualification

Supported main remains0.3.16. Candidate is serial116 plus private
adaptive-digest-117:identical receipt header,column-major submitted signed-i64
little-endian bytes streamed through a fixed64-byte stack buffer. Only SHA
update chunking changes. No unsafe,digest cache,reduced validation,new backend/
dependency,wire/format/receipt budgets/ACK/lock/flush/collector/API change.
Original scalar feature-disabled fallback and every other116 query/Reader/
live/source/group-range byte remain exact. Archive/Cargo inverses pass.
The locked sha2 0.10.9 incremental API is documented at
https://docs.rs/sha2/0.10.9/sha2/ . Four units cover independent Python hashlib
goldens,flat message oracles,empty/partial/cross-column boundaries,signed limits,
shape/order and large/wide/repeated input. Two integrations verify durable
receipt digests,retry/mismatch/reopen,Live prepared/indexed/unindexed and
SourceArchive recovery identity. This candidate-vs016 comparison does not
isolate117-versus116;retained116 grouping gains are combined.

Original build_v2 actually exited1 on a new test'su64/usize assertion mismatch,
after324 baseline/fixed test executions. All original failed source/proofs/logs/
targets remain. New source-repaired117 fixes only that assertion conversion;
fresh v3 targets/logs/source copies/binaries required the complete820 fresh
executions/eight modes/five strict lints. Every helper/source repair byte inverse
is independently checked. All corrected build/recovery/smoke/timed controller
API exits observed0;the failed original exit1 remains explicit. No numerical
rerun. All359 fresh recovery commands pass:28 injected error/owned process
exit cases,ten corruptions,two old formats,two exact byte fixtures,256 concurrent
ACKs,two named scenarios,300 cold SQL checks and69360 CRC bytes. These are not
physical power-loss claims. Four Native/two service excluded smokes,48 order
checks,six outcome negatives andtwo invalid orders pass. Normal binaries have
no fault hooks. All corrected/failed inputs remain frozen. Historical112
unobserved recovery API return is not reclassified.

All324 fixed balanced D: Native cases ran once in12 rounds/all sixorders,
full/both halves. All479232 ACKs/2921356800 CRC bytes pass full rows/indexes/
receipt generations/digests/current metadata/cold SQLite SQL/raw quantiles.
Qualification fails{expected['native']['identity_failed']}/153 A/A controls,
{expected['native']['candidate_guards_failed']}/171 guards and
{expected['native']['goals_failed']}/42 goals. All252 service cases remain
UNSTARTED/UNTESTED. Every stall/max/failing scope remains. Individually
controlled gains must pass corresponding controls/targets full and both halves;
see all_scope_controlled_goal_results and complete171 before/after report.
No changed gate,selected timing,adoption or new competitor/universal ranking.

Verify every ZIP SHA/member CRC/order/offset/size. Reconstruct64MiB chunks
from80MiB logical parts using archive-layout.json and all directories.
Every original/restored whole-file SHA/size/file and directory set passes
before/after importing audit_complete_117 solely from the restored tree.
audit(ABSOLUTE_RESTORED_PATH) equals complete-audit-proof.json with no Native,
timers or existing-file writes. Full failed/corrected source/build/recovery/
smokes/raw/profile/all153 controls/171 guards/42 goals/252 unstarted service
specifications independently replay. Only inventoried regenerable target/Python
caches excluded;originals remain. Closed logs supplemented after actual exit.
No verified complete recent private remote raw backup/recent deletion claim.
0.3.17 remains unqualified/unreleased with no reliable ETA.
''',encoding='utf-8',newline='\n')
print(json.dumps({'complete':True,'parts':len(parts),'files':len(entries),'directories':len(directories),'logical_bytes':sum(v['bytes'] for v in entries.values()),'exact_restored_audit':True,'performance_qualified':False}),flush=True)
