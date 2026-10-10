from pathlib import Path
import hashlib,json
R=Path('D:/Codex/Kestrel/work');source=R/'commit_tails_118.py';dest=R/'commit_tails_118_v2.py'
old=source.read_text(encoding='utf-8')
a="assert git('rev-parse','HEAD').strip()==PARENT and not git('status','--porcelain=v1','--untracked-files=all').strip().replace('?? benchmarks/maintenance-tails-118/','').strip()"
b="assert git('rev-parse','HEAD').strip()==PARENT\nassert set(git('status','--porcelain=v1','--untracked-files=all').splitlines())=={'?? '+p.relative_to(REPO).as_posix() for p in OUT.rglob('*') if p.is_file()}"
assert old.count(a)==1;new=old.replace(a,b)
c="for p in [Path(__file__),R/'analyze-tails-118-v2.log',R/'audit-tails-118.log',R/'preserve-tails-118.log']:"
d="for p in [Path(__file__),R/'commit_tails_118.py',R/'repair_commit_tails_118.py',R/'commit-tails-118.log',R/'analyze-tails-118-v2.log',R/'audit-tails-118.log',R/'preserve-tails-118.log']:"
assert new.count(c)==1;new=new.replace(c,d)
e="'no_Native_or_engine_build_or_timing_executed':True})"
f="'no_Native_or_engine_build_or_timing_executed':True,'initial_committer_actual_API_exit':1,'initial_guard_expected_folder_but_requested_untracked_files_all':True,'corrected_guard_checks_exact_expected_file_set':True})"
assert new.count(e)==1;new=new.replace(e,f)
assert new.replace(f,e).replace(d,c).replace(b,a)==old and not dest.exists();dest.write_text(new,encoding='utf-8',newline='\n')
proof={'first_committer_actual_API_exit':1,'failure_before_any_repo_edit_stage_commit_or_push':True,
 'corrected_initial_guard_checks_exact_expected_untracked_file_set_not_collapsed_folder':True,
 'only_other_changes_preserve_failed_helper_log_and_actual_exit_metadata':True,'exact_inverse':True,
 'old_SHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'new_SHA256':hashlib.sha256(dest.read_bytes()).hexdigest()}
p=R/'committer-repair118-proof.json';assert not p.exists();p.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(proof))
