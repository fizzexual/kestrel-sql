"""Fast-forward the verified private source/report history; no raw deletion/adoption."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess
R=Path('D:/Codex/Kestrel/work');REPO=Path('D:/Codex/Kestrel/outputs/kestrel-sql')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,timeout=120):
 p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(REPO),*args],env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'},capture_output=True,timeout=timeout)
 assert p.returncode==0,(args,p.returncode,p.stdout,p.stderr);return p.stdout.decode('utf-8')
privacy=load(R/'repo-privacy-117-proof.json');assert privacy['metadata']=={'isPrivate':True,'url':'https://github.com/fizzexual/kestrel-sql'} and privacy['actual_gh_exit_code']==0
assert (datetime.now(timezone.utc)-datetime.fromisoformat(privacy['utc'])).total_seconds()<300
status=load(R/'status-117-proof.json');commit=load(R/'commit-117-proof.json')
assert status['repository_clean'] and status['head']==commit['head'] and status['local_commits_not_on_verified_remote_main']==32
guard=load(sorted(R.glob('guard-final-117-*.json'))[-1]);assert not guard['active_processes'] and guard['verified_idle_terminal_reset']
assert git('remote','get-url','origin').strip() in ['https://github.com/fizzexual/kestrel-sql.git','https://github.com/fizzexual/kestrel-sql','git@github.com:fizzexual/kestrel-sql.git']
assert git('rev-parse','HEAD').strip()==commit['head'] and not git('status','--porcelain=v1','--untracked-files=all')
remote=git('ls-remote','--exit-code','origin','refs/heads/main').split()[0];assert remote==status['private_origin_main_head_actually_read'];git('merge-base','--is-ancestor',remote,commit['head'])
protected={n:sha(REPO/n) for n in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
print('Verified private repository, exact origin, clean supported016 and fast-forward ancestry; source/report history backup starts',flush=True)
p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(REPO),'push','--porcelain','origin','HEAD:refs/heads/main'],env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'},capture_output=True,timeout=600)
for name,data in [('push-history-117.stdout',p.stdout),('push-history-117.stderr',p.stderr)]:
 path=R/name;assert not path.exists();path.write_bytes(data)
assert p.returncode==0,(p.returncode,p.stdout,p.stderr)
observed=git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]
assert observed==commit['head'] and int(git('rev-list','--count',observed+'..HEAD'))==0
assert git('rev-parse','HEAD').strip()==commit['head'] and not git('status','--porcelain=v1','--untracked-files=all') and all(sha(REPO/n)==h for n,h in protected.items())
proof={'utc':datetime.now(timezone.utc).isoformat(),'actual_git_push_exit':p.returncode,'remote_main_before':remote,'remote_main_after_actually_read':observed,'backed_up_source_report_commits':32,'local_commits_not_on_remote_main':0,'uncommitted_or_untracked_repository_paths':0,'repository_clean':True,'private_repo_verified_before_push':True,'source_report_history_backup_only':True,'full_recent_raw_remote_backup_verified':False,'no_force_push_tag_release_visibility_change_or_deletion':True,'supported_source_byte_exact016':True,'release017_qualified':False}
path=R/'push-history-117-proof.json';assert not path.exists();path.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof),flush=True)
