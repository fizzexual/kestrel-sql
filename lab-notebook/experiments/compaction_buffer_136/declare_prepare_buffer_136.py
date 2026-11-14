"""Declare136 before code: isolate bounded buffering after combined135 rejection."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,shutil,subprocess
R=Path('D:/Codex/Kestrel');W=R/'work/perf-136';P=R/'outputs/kestrel-sql'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not W.exists() and load(R/'work/phase135-storage-cleanup-proof.json')['completed135_stores_closed'] and not (R/'work/perf-135').exists()
git=['git','--no-optional-locks','-c','safe.directory='+P.as_posix(),'-c','gc.auto=0','-C',str(P)]
assert not subprocess.check_output(git+['status','--porcelain=v1','--untracked-files=all']).strip()
head=subprocess.check_output(git+['rev-parse','HEAD'],text=True).strip();assert head==load(R/'work/phase135-publication-proof.json')['private_main']
core=load(R/'work/compaction-kit-122/provenance.json')['source_core_sha256'];assert all(sha(P/n)==h for n,h in core.items())
policy={'trial':136,'declared_utc':datetime.now(timezone.utc).isoformat(),'source_commit':head,
 'kind':'Isolated bounded-buffer-only Windows compaction correctness prerequisites; zero performance cases',
 'hypothesis':'135 rejected combined write-through/coalescing: full whole medians0.64-5.21% slower, all6 goals fail, explicit sync shrinks but writes grow3.45-3.77x and candidate tails move into writes. Remove WRITE_THROUGH to isolate bounded buffering alone. It may reduce buffered output overhead, but no speed or syscall-count benefit is presumed.',
 'selection':'Windows COMPACTION only, existing exact wire<=1MiB: exact-size bounded BufWriter. Ordinary append/larger/nonWindows retain64KiB original stream. No custom flags, NO_BUFFERING, padding, unsafe, dependency/API/global-setting change.',
 'durability':'BOTH explicit segment sync_all and catalog sync/rename, original receipts/ACK order/format/faultpoints unchanged; ALL write+flush costs remain charged.',
 'supported_core_sha256':core,'prerequisites':'Four fresh normal/fault debug/release suites86 each=344 tests, two strict lints, original compaction driver release artifact. All16 full ordered/unequal/small/large test stores expected352424 exact rows/8458176 CRC bytes; six exact legacy wire pairs and14 publication recovery cases required before adoption.',
 'baseline131340_and134344_tests_reused_history_not_recounted':True,
 'performance_acceptance':'Future fresh137+ balanced sameD exact131A/B versus136C; complete full/both-half A/A and median/tail/setup/write+sync guards, no selected retiming. Original016 whole-engine324Native/252service/42goals/153AA/171guards plus recovery/sustained service unchanged before release.',
 'timed_cases_declared':0,'local_regenerable_build_cap_bytes':2500000000,'release017_qualified':False,
 'storage':'Short private outcomes/every failure/useful source; freshly verify remote bytes before native scoped completed cleanup. Never delete unsaved candidate; no multiGB raw bundles.'}
W.mkdir();(W/'policy.json').write_text(json.dumps(policy,indent=2)+'\n',encoding='utf-8',newline='\n')
(W/'declaration-proof.json').write_text(json.dumps({'complete':True,'utc':datetime.now(timezone.utc).isoformat(),'policy_sha256':sha(W/'policy.json'),'before_candidate_source_implementation':True,'timed_cases_declared':0},indent=2)+'\n',encoding='utf-8',newline='\n')
C=W/'candidate'
for n in ['src','tests','examples']:shutil.copytree(P/n,C/n)
for n in ['Cargo.toml','Cargo.lock']:shutil.copy2(P/n,C/n)
assert all(sha(C/n)==h for n,h in core.items())
subprocess.run(['git','apply','--unidiff-zero',str(P/'experiments/compaction_write_134/candidate.patch')],cwd=C,capture_output=True,check=True)
for n,dest in [('merge_runs_131.rs','src/merge_runs_131.rs'),('compaction_134.rs','tests/compaction_131.rs')]:shutil.copy2(P/'experiments/compaction_write_134'/n,C/dest)
shutil.copy2(P/'experiments/compaction_merge_121/compaction_stage_121.rs',C/'examples/compaction_stage_121.rs')
f=C/'src/archive.rs';text=f.read_text(encoding='utf-8')
old='''                        use std::os::windows::fs::OpenOptionsExt;
                        // FILE_FLAG_WRITE_THROUGH. Keep sync_all below as an
                        // explicit metadata/data publication barrier too.
                        options.custom_flags(0x8000_0000);
'''
assert text.count(old)==1
text=text.replace(old,'',1).replace('adaptive-segment-write-134','adaptive-segment-buffer-136')
assert 'FILE_FLAG_WRITE_THROUGH' not in text and 'custom_flags(0x8000_0000)' not in text
f.write_text(text,encoding='utf-8',newline='\n')
f=C/'Cargo.toml';text=f.read_text(encoding='utf-8');assert text.count('adaptive-segment-write-134')==1
f.write_text(text.replace('adaptive-segment-write-134','adaptive-segment-buffer-136'),encoding='utf-8',newline='\n')
f=C/'tests/compaction_131.rs';text=f.read_text(encoding='utf-8')
f.write_text(text.replace('adaptive-segment-write-134','adaptive-segment-buffer-136').replace('write134','buffer136'),encoding='utf-8',newline='\n')
for n in ['logs','tmp','test-stores','binary']:(W/n).mkdir()
inventory={f.relative_to(C).as_posix():sha(f) for f in C.rglob('*') if f.is_file()}
(W/'preparation-proof.json').write_text(json.dumps({'complete':True,'candidate_source_sha256':inventory,'policy_sha256':sha(W/'policy.json'),'timed_cases_declared':0,'test_cases_each_suite':86,'explicit_sync_barriers_and_wire_unchanged':True,'write_through_flag_removed':True},indent=2)+'\n',encoding='utf-8',newline='\n')
for src,dest in [('build_write_134.py','build_buffer_136.py'),('check_write134_prerequisite_activity.ps1','check_buffer136_prerequisite_activity.ps1'),('launch_build_write134.ps1','launch_build_buffer136.ps1'),('audit_write134_stores.py','audit_buffer136_stores.py')]:
    assert not (R/'work'/dest).exists(),dest
    s=(R/'work'/src).read_text(encoding='utf-8')
    s=s.replace('build_write_134','build_buffer_136').replace('adaptive-segment-write-134','adaptive-segment-buffer-136').replace('perf-134','perf-136').replace('write134','buffer136').replace('candidate134.exe','candidate136.exe').replace('build-write134','build-buffer136')
    if dest.endswith('.py'):ast.parse(s)
    (R/'work'/dest).write_text(s,encoding='utf-8',newline='\n')
print(json.dumps({'declared':136,'candidate_prepared':True,'write_through_removed':True,'bounded_compaction_buffer_retained':True,'expected_fresh_tests':344,'timed_cases_declared':0}))
