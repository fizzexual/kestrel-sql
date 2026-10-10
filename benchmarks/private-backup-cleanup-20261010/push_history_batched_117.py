"""Upload existing private history in bounded fast-forward batches, retaining errors."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,traceback
R=Path('D:/Codex/Kestrel/work');REPO=Path('D:/Codex/Kestrel/outputs/kestrel-sql');GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def utc():return datetime.now(timezone.utc).isoformat()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 assert not p.exists(),p
 p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def git(*args,timeout=120):
 p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(REPO),*args],env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'},capture_output=True,text=True,timeout=timeout)
 assert p.returncode==0,(args,p.returncode,p.stderr);return p.stdout
plan=load(R/'history-push-plan-117.json');assert git('rev-parse','HEAD').strip()==plan['head'] and not git('status','--porcelain=v1','--untracked-files=all')
assert git('remote','get-url','origin').strip() in ['https://github.com/fizzexual/kestrel-sql.git','https://github.com/fizzexual/kestrel-sql','git@github.com:fizzexual/kestrel-sql.git']
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==plan['remote_before']
protected={name:sha(REPO/name) for name in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
steps=[];batch=[];size=0;bound=1024**3
for row in plan['all32_existing_commits_no_rewrite_or_new_branch']:
 assert row['new_object_logical_bytes']<bound,row
 if batch and size+row['new_object_logical_bytes']>=bound:steps.append({'commits':batch,'uncompressed_new_objects_upper_bound':size,'tip':batch[-1]});batch=[];size=0
 batch.append(row['commit']);size+=row['new_object_logical_bytes']
if batch:steps.append({'commits':batch,'uncompressed_new_objects_upper_bound':size,'tip':batch[-1]})
for step in steps:git('diff','--quiet',step['tip'],plan['head'],'--','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md')
save(R/'history-push-batches-117.json',{'declared_utc':utc(),'before_any_batched_push':True,'steps':steps,'bound_each_uncompressed_new_object_sum_bytes':bound,'ordinary_fast_forward_existing_commits_only':True,'all_intermediate_tips_supported_source_exact_final016':True,'full_remote_raw_backup_not_yet_verified':True})
records=[];previous=plan['remote_before']
try:
 for i,step in enumerate(steps):
  privacy=subprocess.run([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate,url'],capture_output=True,timeout=60)
  save(R/f'privacy-batch117-{i:02d}.json',{'utc':utc(),'actual_gh_exit':privacy.returncode,'metadata':json.loads(privacy.stdout) if privacy.returncode==0 else None})
  assert privacy.returncode==0 and json.loads(privacy.stdout)=={'isPrivate':True,'url':'https://github.com/fizzexual/kestrel-sql'}
  assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==previous;git('merge-base','--is-ancestor',previous,step['tip'])
  argv=['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(REPO),'push','--porcelain','origin',step['tip']+':refs/heads/main']
  print(json.dumps({'started_batch':i+1,'of':len(steps),'existing_commits':len(step['commits']),'uncompressed_new_object_bound':step['uncompressed_new_objects_upper_bound']}),flush=True)
  p=subprocess.run(argv,env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'},capture_output=True,timeout=600)
  for suffix,data in [('stdout',p.stdout),('stderr',p.stderr)]:path=R/f'history-batch117-{i:02d}.{suffix}';assert not path.exists();path.write_bytes(data)
  record={'index':i,'argv':argv,'actual_git_exit':p.returncode,'before':previous,'expected_after':step['tip'],'utc':utc()};records.append(record);save(R/f'history-batch117-{i:02d}-attempt.json',record)
  assert p.returncode==0,(i,p.returncode,p.stderr)
  after=git('ls-remote','--exit-code','origin','refs/heads/main').split()[0];assert after==step['tip'];previous=after
  save(R/f'history-batch117-{i:02d}-verified.json',record|{'remote_after_actually_read':after,'completed':True})
  print(json.dumps({'verified_batch':i+1,'of':len(steps),'remote_after':after,'remaining_local_commits':int(git('rev-list','--count',after+'..HEAD'))}),flush=True)
 assert previous==plan['head'] and not git('status','--porcelain=v1','--untracked-files=all') and all(sha(REPO/name)==h for name,h in protected.items())
 save(R/'history-batched-117-proof.json',{'complete':True,'utc':utc(),'remote_main_after_actually_read':previous,'backed_up_existing_commits':32,'batches':records,'local_commits_not_on_remote_main':0,'repository_clean':True,'supported_source_byte_exact016':True,'initial_actual_API_and_git_exit1_HTTP500_retained':True,'all_batched_git_exits0_and_remote_each_head_verified':True,'contains_tracked_raw_archive_parts_but_fresh_remote_content_download_verification_not_yet_done':True,'full_recent_raw_backup_verified':False,'no_force_push_history_rewrite_new_branch_tag_release_visibility_change_or_cleanup':True})
 print(json.dumps({'complete':True,'batches':len(steps),'commits':32,'remaining_unpushed':0,'remote_raw_content_download_verification_pending':True}),flush=True)
except BaseException:
 save(R/'history-batched-117-failure.json',{'utc':utc(),'records':records,'last_verified_remote':previous,'error':traceback.format_exc(),'all_local_history_retained':True,'no_benchmark_release_cleanup_or_force_push':True});raise
