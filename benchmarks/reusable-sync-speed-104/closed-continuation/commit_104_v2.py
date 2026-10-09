"""Close104 with byte-exact compressed copies of whitespace-bearing raw helpers."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,subprocess
R=Path('D:/Codex/Kestrel');WORK=R/'work';REPO=R/'outputs/kestrel-sql';OUT=REPO/'benchmarks/reusable-sync-speed-104';W=WORK/'perf-104';RESTORE=WORK/'restored-reusable-sync-speed-104';PARENT='532c8a33234323a780cdc9e3ed0544d6ef93ba70'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):
 assert not p.exists(),p
 p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8',newline='\n')
def git(*args):
 r=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(REPO),*args],capture_output=True,text=True);assert r.returncode==0,(args,r.stdout,r.stderr);return r.stdout
guard=sorted(WORK.glob('guard-final-104-*.json'))[-1];assert not load(guard)['active_processes'] and load(guard)['verified_idle_terminal_reset']
assert git('rev-parse','HEAD').strip()==PARENT and not (WORK/'commit-104-proof.json').exists()
assert load(OUT/'preservation-proof.json')['complete'] and load(OUT/'restored-audit-proof.json')['replay_equals_original_complete_audit']
assert load(W/'complete-audit-proof.json')==load(OUT/'complete-audit-proof.json')
failure=WORK/'commit-104.log';assert 'new blank line at EOF' in failure.read_text() and 'AssertionError' in failure.read_text()
closed=OUT/'closed-continuation';kept=WORK/'commit-correction-104';assert not kept.exists();kept.mkdir()
records=[]
for name in ['audit_service_095.py','outcomes_098.py']:
 p=OUT/name;dest=kept/name;assert p.resolve().is_relative_to(OUT.resolve()) and dest.resolve().is_relative_to(kept.resolve()) and not p.is_symlink() and not p.is_junction()
 content=p.read_bytes();assert content==(W/name).read_bytes()==(RESTORE/name).read_bytes()
 encoded=OUT/(name+'.gz');assert not encoded.exists();encoded.write_bytes(gzip.compress(content,mtime=0));assert gzip.decompress(encoded.read_bytes())==content
 git('reset','--',p.relative_to(REPO).as_posix())
 shutil.move(str(p),str(dest));assert dest.read_bytes()==content and not p.exists()
 records.append({'path':name,'raw_sha256':hashlib.sha256(content).hexdigest(),'gzip_sha256':sha(encoded),'byte_exact_original_and_restored_and_archived':True,'loose_duplicate_preserved_at':str(dest)})
for name in ['commit-104.log','commit_104_v2.py']:shutil.copy2(WORK/name,closed/name)
save(closed/'raw-helper-format-preservation.json',{'raw_helpers':records,'all_frozen_original_and_restored_bytes_unchanged':True,'only_loose_duplicate_storage_representation_changed':True,'strict_whole_staged_whitespace_checks_retained':True,'failed_commit_attempt_preserved':True})
report=REPO/'REUSABLE_SYNC_SPEED_104.md';report.write_bytes(report.read_bytes()+b'\nTwo whitespace-bearing raw helper supplements are stored as exact gzip copies; their uncompressed bytes remain in the verified archive, original and restored trees. The failed first evidence-commit check is retained. The complete staged whitespace check passes without path exclusions or raw normalization.\n')
git('add','--','REUSABLE_SYNC_SPEED_104.md','benchmarks/reusable-sync-speed-104')
names=git('diff','--cached','--name-only').splitlines();assert all(n in ['README.md','BENCHMARK_HISTORY.md','REUSABLE_SYNC_SPEED_104.md'] or n.startswith('benchmarks/reusable-sync-speed-104/') for n in names)
git('diff','--cached','--check');print(git('commit','-m','Preserve complete native and service104 rejection and restored evidence'),flush=True)
head=git('rev-parse','HEAD').strip();assert not git('status','--porcelain').strip()
assert not git('diff','--name-only',PARENT,head,'--','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md')
save(WORK/'commit-104-proof.json',{'utc':datetime.now(timezone.utc).isoformat(),'complete':True,'parent':PARENT,'head':head,'staged_files':len(names),'repository_clean':True,'supported_source_tests_examples_Cargo_verification_and_overnight_byte_exact':True,'performance_or_adoption_not_qualified':True,'no_remote_upload_or_raw_deletion':True,'first_commit_check_failure_and_exact_raw_helpers_preserved':True})
print(json.dumps({'complete':True,'head':head,'staged_files':len(names)}),flush=True)
