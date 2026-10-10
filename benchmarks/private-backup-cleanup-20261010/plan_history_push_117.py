"""Size actual new objects per existing commit; never rewrite/split history."""
from pathlib import Path
from datetime import datetime,timezone
import json,os,subprocess
R=Path('D:/Codex/Kestrel/work');REPO=Path('D:/Codex/Kestrel/outputs/kestrel-sql')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def git(*args,input=None):
 p=subprocess.run(['git','--no-optional-locks','-c','safe.directory='+REPO.as_posix(),'-c','gc.auto=0','-c','maintenance.auto=false','-C',str(REPO),*args],input=input,env={**os.environ,'GIT_TERMINAL_PROMPT':'0','GCM_INTERACTIVE':'never'},capture_output=True,text=True,timeout=120)
 assert p.returncode==0,(args,p.returncode,p.stderr);return p.stdout
s=load(R/'status-after-push-117-proof.json');assert s['local_commits_not_on_verified_remote_main']==32 and s['repository_clean']
assert git('rev-parse','HEAD').strip()==s['head'] and git('ls-remote','--exit-code','origin','refs/heads/main').split()[0]==s['private_origin_main_head_actually_read']
commits=git('rev-list','--reverse','--topo-order',s['private_origin_main_head_actually_read']+'..'+s['head']).splitlines();assert len(commits)==32
previous=s['private_origin_main_head_actually_read'];rows=[]
for commit in commits:
 objects=git('rev-list','--objects','--no-object-names',commit,'^'+previous).splitlines()
 sizes=git('cat-file','--batch-check=%(objectname) %(objecttype) %(objectsize) %(objectsize:disk)',input='\n'.join(objects)+'\n').splitlines()
 parsed=[line.split() for line in sizes];assert len(parsed)==len(objects) and all(len(line)==4 and line[0]==oid for line,oid in zip(parsed,objects))
 row={'commit':commit,'parent_remote_step':previous,'new_objects':len(objects),'new_object_logical_bytes':sum(int(line[2]) for line in parsed),'new_object_stored_bytes':sum(int(line[3]) for line in parsed),'largest_blob_bytes':max([int(line[2]) for line in parsed if line[1]=='blob'],default=0),'under_single_push_2GiB_with_256MiB_margin':sum(int(line[3]) for line in parsed)<(2*1024**3-256*1024**2)}
 rows.append(row);previous=commit
assert all(row['largest_blob_bytes']<100*1024**2 for row in rows)
plan={'utc':datetime.now(timezone.utc).isoformat(),'head':s['head'],'remote_before':s['private_origin_main_head_actually_read'],'all32_existing_commits_no_rewrite_or_new_branch':rows,'total_new_object_stored_bytes':sum(r['new_object_stored_bytes'] for r in rows),'tracked_raw_archive_parts':len(git('ls-files','--','benchmarks/*/evidence-*.zip').splitlines()),'official_primary_documentation':'https://docs.github.com/en/get-started/using-git/troubleshooting-the-2-gb-push-limit','initial_push_actual_API_exit':1,'initial_git_exit':1,'initial_HTTP_500_failure_retained':True,'no_push_or_cleanup_launched':True}
p=R/'history-push-plan-117.json';assert not p.exists();p.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8');print(json.dumps({'commits':32,'tracked_archive_parts':plan['tracked_raw_archive_parts'],'stored_bytes_total':plan['total_new_object_stored_bytes'],'first_four':rows[:4],'commits_above_safe_single_push_size':[r for r in rows if not r['under_single_push_2GiB_with_256MiB_margin']]}))
