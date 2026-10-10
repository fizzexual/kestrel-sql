"""Record the closed private-history upload, fresh raw download and exact duplicate cleanup."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,os,shutil,subprocess,traceback
R=Path('D:/Codex/Kestrel/work');REPO=Path('D:/Codex/Kestrel/outputs/kestrel-sql')
DEST=REPO/'benchmarks/private-backup-cleanup-20261010'
DOWN=R/'github-verified-trial117-20261010';CLEAN=R/'cleanup-verified-restore-117-v3'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
PARENT='6aae0a3994fad1eef1b6267346212a3b094078a4'
def utc():return datetime.now(timezone.utc).isoformat()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,indent=2)+'\n')
def git(*args,timeout=120):
 p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0',
  '-c','maintenance.auto=false','-C',str(REPO),*args],capture_output=True,
  env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'},timeout=timeout)
 assert p.returncode==0,(args,p.returncode,p.stderr);return p.stdout.decode('utf-8')
def privacy(label):
 p=subprocess.run([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate,url'],capture_output=True,timeout=60)
 (R/f'backup-cleanup117-{label}.stdout').write_bytes(p.stdout);(R/f'backup-cleanup117-{label}.stderr').write_bytes(p.stderr)
 assert p.returncode==0 and json.loads(p.stdout)=={'isPrivate':True,'url':'https://github.com/fizzexual/kestrel-sql'}
 return {'utc':utc(),'actual_gh_exit0':True,'metadata':json.loads(p.stdout)}
assert git('rev-parse','HEAD').strip()==PARENT and not git('status','--porcelain=v1','--untracked-files=all')
assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==PARENT
guard=sorted(R.glob('guard-final-117-*.json'))[-1];g=load(guard)
assert g['verified_idle_terminal_reset'] and not g['active_processes']
assert (datetime.now(timezone.utc)-datetime.fromisoformat(g['utc'])).total_seconds()<1800
upload=load(R/'history-batched-117-proof.json');raw=load(DOWN/'proof.json');removed=load(CLEAN/'proof.json')
assert upload['complete'] and upload['backed_up_existing_commits']==32 and upload['local_commits_not_on_remote_main']==0
assert raw['complete'] and raw['fresh_remote_downloaded_files']==166 and raw['all_actual_gh_exits0']
assert removed['complete'] and removed['logical_bytes_removed']==4075316365
assert not (R/'restored-adaptive-speed-117').exists() and (R/'perf-117').is_dir() and (DOWN/'files').is_dir()
before=privacy('before-commit')
protected={n:sha(REPO/n) for n in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
git('diff','--quiet','51f6484ea7be574e21b5ad989cd909f520b92b54',PARENT,'--','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md')
assert not DEST.exists();DEST.mkdir()
copied={}
def copy(p,rel=None):
 target=DEST/(rel or p.name);target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
 if p.suffix in ['.log','.stdout','.stderr'] or p.name.startswith('metadata-'):
  data=p.read_bytes();target=target.with_name(target.name+'.gz');target.write_bytes(gzip.compress(data,mtime=0))
  assert gzip.decompress(target.read_bytes())==data
 else:shutil.copy2(p,target);assert sha(p)==sha(target)
 copied[target.relative_to(DEST).as_posix()]={'source':p.as_posix(),'original_bytes':p.stat().st_size,'original_sha256':sha(p),'stored_sha256':sha(target)}
names=['push_history_117.py','plan_history_push_117.py','push_history_batched_117.py','history-push-plan-117.json',
 'history-push-batches-117.json','history-batched-117-proof.json','push-history-117.log','push-history-117.stdout',
 'push-history-117.stderr','push-history-batched-117.log','status-after-push-117-proof.json',
 'repo-privacy-after-push-117-proof.json','verify_remote_raw_117.py','verify-remote-raw-117.log',
 'cleanup_verified_restore_117.ps1','cleanup_verified_restore_117_v2.ps1','cleanup_verified_restore_117_v3.ps1',
 'repair_cleanup_117.py','diagnose_cleanup_117.py','cleanup-repair-117-proof.json','cleanup-diagnostic-117-proof.json',
 'cleanup-verified-restore-117.log','cleanup-verified-restore-117-v2.log','cleanup-verified-restore-117-v3.log']
for name in names:copy(R/name)
for pattern in ['history-batch117-*','privacy-batch117-*']:
 for p in sorted(R.glob(pattern)):copy(p,'history-batches/'+p.name)
for root,sub in [(DOWN,'fresh-download-verification'),(R/'cleanup-verified-restore-117','failed-cleanup-v2'),(CLEAN,'completed-cleanup-v3')]:
 for p in root.rglob('*'):
  if p.is_file() and not (root==DOWN and p.relative_to(root).parts[0]=='files'):
   copy(p,sub+'/'+p.relative_to(root).as_posix())
copy(guard);copy(Path(__file__))
save(DEST/'actual-api-exits.json',{'observed_actual_API_exits':[
 {'operation':'single large git history upload','session':3446,'exit':1},
 {'operation':'14 bounded history batches','session':63911,'exit':0},
 {'operation':'fresh remote raw verification','session':41392,'exit':0},
 {'operation':'initial cleanup guard','exit':1,'mutation':'none'},
 {'operation':'cleanup repair preparation sandbox attempt','exit':1,'error':'PermissionError writing separate .ps1; subsequent approved execution0'},
 {'operation':'full-hash cleanup v2','session':80806,'exit':1,'mutation':'none; final directory metadata guard stopped'},
 {'operation':'instrumented full-hash cleanup v3','session':5696,'exit':0}],
 'v2_directory_metadata_change_cause_not_established':True,
 'v3_kept_all_metadata_guards_and_preserved_before_after_snapshots':True,
 'no_timing_gate_change_or_new_benchmark_run':True})
save(DEST/'summary.json',{'utc':utc(),'private_before_commit':before,'original_pending32_history_upload_completed':True,
 'whole_trial117_fresh_remote_backup_verified':True,'other_recent_trial_raw_download_verification_not_claimed':True,
 'fresh_download_files':166,'fresh_download_bytes':523926609,'bounded_zip_parts':53,'raw_logical_files':38336,
 'raw_logical_bytes':4075316365,'removed_only_unused_restore':removed,'supported_source_exact016':True,
 'release017_qualified':False,'no_force_push_or_history_rewrite_or_tags_or_visibility_change':True})
doc=f'''# Private backup and verified duplicate cleanup — October 10, 2026

All 32 previously pending commits, including tracked raw archives, reached private GitHub main at `{PARENT}` through 14 ordinary fast-forward batches. The original single large push failed with HTTP 500; its logs and actual exit1 remain. Smaller batches each exited0 and independently verified their remote heads. No history was rewritten, and no tag, release or visibility changed.

Trial117's complete immutable `benchmarks/adaptive-speed-117` tree was independently fetched using fresh authenticated GitHub API requests: **166 files / 523,926,609 bytes**, including all **53 ZIP parts**. Every download exited0 and matched the local file's full SHA-256, size and Git blob SHA-1. The remote commit/root/scope tree matched exactly; all downloaded ZIP member CRCs passed; privacy was verified before and after. This verifies trial117's raw backup. Other recent trials still need their own fresh content verification before deletion.

Only `D:\\Codex\\Kestrel\\work\\restored-adaptive-speed-117` was removed: **38,336 files, 5,222 directories, 4,075,316,365 logical bytes (3.80 GiB)**. Native PowerShell checked the exact absolute target and every ancestor/descendant for reparse points, exact complete sets, every current file size/SHA-256 and unchanged metadata immediately before deletion. The observed D: free-space increase was **4,121,587,712 bytes (3.84 GiB)**; it can include unrelated background activity.

The first cleanup stopped before mutation because automatic JSON date conversion misread the UTC guard. A separate helper retained UTC strings. The next attempt completed every file hash but stopped on a directory metadata difference; its cause is not established. A separately instrumented third attempt preserved both full metadata snapshots and passed **all the same checks**, then exited0 after removal. Both failures and exact helper derivations remain evidence.

Original `work/perf-117`, every failed attempt, local repository ZIPs and the fresh downloaded files at `work/github-verified-trial117-20261010/files` remain. Recovery: fetch the immutable GitHub tree/blob OIDs in [the declared manifest](benchmarks/private-backup-cleanup-20261010/fresh-download-verification/policy.json), verify SHA-256 and size, then follow trial117's [reproduction instructions](benchmarks/adaptive-speed-117/REPRODUCE.md). Downloaded whole restored-audit proofs are byte-identical to the archived originals; a newly restored full audit was not rerun during this download step.

Supported **0.3.16** source/tests/examples/Cargo/verification/overnight bytes remain exact. **0.3.17 remains unqualified and unreleased**. This operation adds no speed measurement. Trial117 still fails15 A/A controls, six guards and four goals; all252 service cases remain unstarted. The prepared reset remains expired with shared C: profile intact; no app shutdown, reset rearm or old-task/automation activation occurred.

See [complete download verification](benchmarks/private-backup-cleanup-20261010/fresh-download-verification/proof.json), [exact cleanup result](benchmarks/private-backup-cleanup-20261010/completed-cleanup-v3/proof.json) and [actual API exits](benchmarks/private-backup-cleanup-20261010/actual-api-exits.json).
'''
report=REPO/'STORAGE_CLEANUP_20261010.md';assert not report.exists();report.write_text(doc,encoding='utf-8',newline='\n')
for name in ['ADAPTIVE_ENGINE_117.md','STORAGE_CLEANUP_20261009.md','README.md','BENCHMARK_HISTORY.md']:
 p=REPO/name;old=p.read_bytes();copy(p,'document-preimages/'+name)
 addition='\n\n- October10 continuation: [private backup and exact unused-restore cleanup](STORAGE_CLEANUP_20261010.md). All32 pending commits uploaded; complete trial117 raw tree freshly downloaded/hash-verified. Only its unused restored duplicate was removed after full current hashes; original raw data and failures remain. Other recent raw download verification is still pending. Supported016 and trial117 performance outcome are unchanged.\n'
 p.write_bytes(old+addition.encode('utf-8'));assert p.read_bytes().startswith(old)
save(DEST/'evidence-copy-map.json',copied)
paths=['STORAGE_CLEANUP_20261010.md','ADAPTIVE_ENGINE_117.md','STORAGE_CLEANUP_20261009.md','README.md','BENCHMARK_HISTORY.md','benchmarks/private-backup-cleanup-20261010']
assert all(sha(REPO/n)==h for n,h in protected.items())
git('add','--',*paths)
assert all(n in paths or n.startswith('benchmarks/private-backup-cleanup-20261010/') for n in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check')
git('commit','-m','Verify private trial117 backup and remove its redundant restore')
head=git('rev-parse','HEAD').strip();assert git('rev-parse','HEAD^').strip()==PARENT
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(REPO/n)==h for n,h in protected.items())
save(R/'backup-cleanup117-commit-proof.json',{'utc':utc(),'head':head,'parent':PARENT,'supported_source_exact016':True,'repository_clean':True})
privacy('before-push');assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==PARENT
p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false',
 '-C',str(REPO),'push','--porcelain','origin',head+':refs/heads/main'],capture_output=True,
 env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'},timeout=300)
(R/'backup-cleanup117-push.stdout').write_bytes(p.stdout);(R/'backup-cleanup117-push.stderr').write_bytes(p.stderr)
assert p.returncode==0,(p.returncode,p.stderr)
remote=git('ls-remote','--exit-code','origin','refs/heads/main').split()[0];assert remote==head
after=privacy('after-push');assert not git('status','--porcelain=v1','--untracked-files=all')
save(R/'backup-cleanup117-final-proof.json',{'complete':True,'utc':utc(),'head':head,'remote_main_actually_read':remote,
 'local_unpushed_commits':int(git('rev-list','--count',remote+'..HEAD')),'uncommitted_and_untracked_paths':[],
 'actual_git_push_exit':p.returncode,'private_after_push':after,'source_exact016':True,'release017_qualified':False,
 'trial117_raw_remote_backup_verified_and_only_unused_restore_deleted':True})
print(json.dumps(load(R/'backup-cleanup117-final-proof.json')),flush=True)
