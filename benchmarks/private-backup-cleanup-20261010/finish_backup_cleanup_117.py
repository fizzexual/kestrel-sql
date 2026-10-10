"""Retain original CRLF evidence bytes while making text views pass strict Git whitespace checks."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,os,re,shutil,subprocess
R=Path('D:/Codex/Kestrel/work');REPO=Path('D:/Codex/Kestrel/outputs/kestrel-sql');D=REPO/'benchmarks/private-backup-cleanup-20261010'
PARENT='6aae0a3994fad1eef1b6267346212a3b094078a4'
GH='C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
def utc():return datetime.now(timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,indent=2)+'\n')
def rawgit(*args):
 return subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0',
  '-c','maintenance.auto=false','-C',str(REPO),*args],capture_output=True,
  env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'},timeout=300)
def git(*args):
 p=rawgit(*args);assert p.returncode==0,(args,p.returncode,p.stderr);return p.stdout.decode('utf-8')
def privacy(label):
 p=subprocess.run([GH,'repo','view','fizzexual/kestrel-sql','--json','isPrivate,url'],capture_output=True,timeout=60)
 for suffix,data in [('stdout',p.stdout),('stderr',p.stderr)]:
  path=R/f'backup-cleanup117-finish-{label}.{suffix}';assert not path.exists();path.write_bytes(data)
 assert p.returncode==0 and json.loads(p.stdout)=={'isPrivate':True,'url':'https://github.com/fizzexual/kestrel-sql'}
 return {'utc':utc(),'actual_gh_exit':0,'metadata':json.loads(p.stdout)}
assert git('rev-parse','HEAD').strip()==PARENT
guard=json.loads(sorted(R.glob('guard-final-117-*.json'))[-1].read_text(encoding='utf-8-sig'))
assert guard['verified_idle_terminal_reset'] and not guard['active_processes']
assert (datetime.now(timezone.utc)-datetime.fromisoformat(guard['utc'])).total_seconds()<1800
assert 'diff\', \'--cached\', \'--check' in (R/'close-backup-cleanup-117.log').read_text(encoding='utf-8-sig')
protected={n:sha(REPO/n) for n in git('ls-files','src','tests','examples','Cargo.toml','Cargo.lock','verification.json','OVERNIGHT_2026-10-07.md').splitlines()}
check=rawgit('diff','--cached','--check');assert check.returncode==2 and not check.stderr
err=D/'first-strict-whitespace-check.stdout.gz';assert not err.exists();err.write_bytes(gzip.compress(check.stdout,mtime=0))
assert gzip.decompress(err.read_bytes())==check.stdout
paths=set()
for line in check.stdout.decode('utf-8').splitlines():
 m=re.match(r'^(.*):\d+: (?:trailing whitespace\.|new blank line at EOF\.)$',line)
 if m:paths.add(m[1])
assert paths and all(n.startswith('benchmarks/private-backup-cleanup-20261010/') for n in paths)
original_map=json.loads((D/'evidence-copy-map.json').read_text(encoding='utf-8'))
conversions=[]
for name in sorted(paths):
 p=REPO/name;rel=p.relative_to(D).as_posix();original=p.read_bytes()
 assert hashlib.sha256(original).hexdigest()==original_map[rel]['stored_sha256'],rel
 archive=p.with_name(p.name+'.original-bytes.gz');assert not archive.exists();archive.write_bytes(gzip.compress(original,mtime=0))
 assert gzip.decompress(archive.read_bytes())==original
 view=original.replace(b'\r\n',b'\n').rstrip(b'\r\n')+b'\n'
 assert view.decode('utf-8') and view!=original
 if p.suffix=='.json':assert json.loads(view)==json.loads(original)
 p.write_bytes(view)
 conversions.append({'text_view':rel,'original_bytes_gzip':archive.relative_to(D).as_posix(),'original_SHA256':hashlib.sha256(original).hexdigest(),
  'view_SHA256':sha(p),'conversion':'CRLF to LF and one final newline; no semantic payload changes','original_byte_exact_recoverable':True})
p=D/'first-closure-failed.log.gz';raw=(R/'close-backup-cleanup-117.log').read_bytes();p.write_bytes(gzip.compress(raw,mtime=0));assert gzip.decompress(p.read_bytes())==raw
shutil.copy2(Path(__file__),D/Path(__file__).name)
save(D/'text-view-preservation.json',{'original_closure_actual_API_exit':1,'failure_before_commit_or_push':True,
 'strict_Git_check_rejected_CRLF_evidence_text_views':True,'original_helpers_logs_proofs_retained_byte_exact_in_gzip':True,
 'no_whitespace_check_bypass':True,'conversions':conversions})
paths=['STORAGE_CLEANUP_20261010.md','ADAPTIVE_ENGINE_117.md','STORAGE_CLEANUP_20261009.md','README.md','BENCHMARK_HISTORY.md','benchmarks/private-backup-cleanup-20261010']
git('add','--',*paths);assert all(n in paths or n.startswith('benchmarks/private-backup-cleanup-20261010/') for n in git('diff','--cached','--name-only').splitlines())
git('diff','--cached','--check');assert all(sha(REPO/n)==h for n,h in protected.items())
privacy('before-commit');assert git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==PARENT
git('commit','-m','Verify private trial117 backup and remove its redundant restore')
head=git('rev-parse','HEAD').strip();assert git('rev-parse','HEAD^').strip()==PARENT
assert not git('status','--porcelain=v1','--untracked-files=all') and all(sha(REPO/n)==h for n,h in protected.items())
save(R/'backup-cleanup117-commit-proof.json',{'utc':utc(),'head':head,'parent':PARENT,'supported_source_exact016':True,'repository_clean':True})
p=rawgit('push','--porcelain','origin',head+':refs/heads/main')
for suffix,data in [('stdout',p.stdout),('stderr',p.stderr)]:
 path=R/f'backup-cleanup117-finish-push.{suffix}';assert not path.exists();path.write_bytes(data)
assert p.returncode==0,(p.returncode,p.stderr)
remote=git('ls-remote','--exit-code','origin','refs/heads/main').split()[0];assert remote==head
after=privacy('after-push');assert not git('status','--porcelain=v1','--untracked-files=all')
proof={'complete':True,'utc':utc(),'head':head,'remote_main_actually_read':remote,
 'local_unpushed_commits':int(git('rev-list','--count',remote+'..HEAD')),'uncommitted_and_untracked_paths':[],
 'actual_git_push_exit':p.returncode,'private_after_push':after,'source_exact016':True,'release017_qualified':False,
 'trial117_raw_remote_backup_verified_and_only_unused_restore_deleted':True,
 'first_closure_API_exit1_retained_and_no_check_bypass':True}
save(R/'backup-cleanup117-final-proof.json',proof);print(json.dumps(proof),flush=True)
