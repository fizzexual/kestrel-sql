"""Transfer exact verified078 tree in three bounded Git steps, preserving original commit."""
import hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
ORIGINAL='859501c70dc62a1d48017d6a0e60c998b36ec5a5';PREVIOUS='6246763cdc6768014f961ef5121f3bdd76130d3b'
def now():return datetime.now(timezone.utc).isoformat()
def git(*a,env=None,input=None):return subprocess.check_output(['git',*a],cwd=ROOT,env=env,input=input,text=True,encoding='utf-8').strip()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assert git('rev-parse','HEAD')==ORIGINAL and git('status','--porcelain')==''
assert git('ls-remote','origin','refs/heads/main').split()[0]==PREVIOUS
assert not (W/'incremental-publication-policy.json').exists()
assert json.loads(subprocess.check_output(['gh','api','repos/fizzexual/kestrel-sql/actions/permissions'],text=True))['enabled'] is False
assert json.loads(subprocess.check_output(['gh','api','repos/fizzexual/kestrel-sql'],text=True))['private']
bundle=json.loads((ROOT/'benchmarks/source-state-078-bundle-check.json').read_text());assert bundle['parts']==3
publication=json.loads((ROOT/'benchmarks/source-state-078-publication.json').read_text())
for a in publication['repository_artifacts']:
    p=ROOT/a['repository_path']
    with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==a['sha256']
    assert p.stat().st_size==a['bytes'] and git('hash-object','--no-filters',str(p))==a['git_blob_sha']
parts=[]
for b in bundle['artifacts']:
    parts.append(['benchmarks/'+b['name'],'benchmarks/'+b['name']+'.sha256'])
index=W/'publication078.index';assert not index.exists();env={**os.environ,'GIT_INDEX_FILE':str(index)}
git('read-tree',ORIGINAL,env=env)
for rel in parts[1]+parts[2]:git('update-index','--force-remove',rel,env=env)
tree_a=git('write-tree',env=env)
a=git('commit-tree',tree_a,'-p',PREVIOUS,env=env,input='Preserve source-state qualification and complete evidence part1\n')
for rel in parts[1]:
    blob=git('rev-parse',ORIGINAL+':'+rel);git('update-index','--add','--cacheinfo','100644,'+blob+','+rel,env=env)
tree_b=git('write-tree',env=env);b=git('commit-tree',tree_b,'-p',a,env=env,input='Preserve complete source-state evidence part2\n')
tree_original=git('rev-parse',ORIGINAL+'^{tree}')
c=git('commit-tree',tree_original,'-p',b,'-p',ORIGINAL,env=env,input='Complete exact verified source-state evidence with part3\n')
assert git('rev-parse',c+'^{tree}')==tree_original
subprocess.run(['git','merge-base','--is-ancestor',ORIGINAL,c],cwd=ROOT,check=True)
policy={'declared_utc':now(),'before_first_incremental_push':True,'original_verified_commit':ORIGINAL,'previous_remote_main':PREVIOUS,'final_tree_sha':tree_original,'final_tree_byte_identical_to_original':True,'original_failed_commit_retained_as_final_parent':True,'incremental_commits':[a,b,c],'archive_parts_by_step':parts,'actions_disabled':True,'private':True,'no_source_binary_fixture_or_benchmark_policy_change':True,'no_native_or_timed_rerun':True,'no_force_push':True}
save(W/'incremental-publication-policy.json',policy);records=[];before=PREVIOUS
for i,commit in enumerate([a,b,c],1):
    assert git('ls-remote','origin','refs/heads/main').split()[0]==before
    started=now();r=subprocess.run(['git','push','origin',commit+':refs/heads/main'],cwd=ROOT,capture_output=True)
    (W/f'incremental-{i}.stdout').write_bytes(r.stdout);(W/f'incremental-{i}.stderr').write_bytes(r.stderr)
    after=git('ls-remote','origin','refs/heads/main').split()[0]
    records.append({'step':i,'commit':commit,'started_utc':started,'ended_utc':now(),'exit':r.returncode,'remote_before':before,'remote_after':after,'remote_updated':after==commit})
    save(W/'incremental-publication-progress.json',records);print(json.dumps(records[-1]),flush=True)
    if r.returncode:print(r.stderr.decode('utf-8',errors='replace')[-3000:]);raise SystemExit(r.returncode)
    assert after==commit;before=commit
assert git('rev-parse','HEAD')==ORIGINAL and git('status','--porcelain')==''
git('update-ref','refs/heads/main',c,ORIGINAL)
assert git('status','--porcelain')=='' and git('rev-parse','HEAD^{tree}')==tree_original
save(W/'incremental-publication-completion.json',{**policy,'complete':True,'completed_utc':now(),'local_remote_main':c,'all_three_remote_steps_passed':True,'clean_identical_final_tree':True})
print('completed exact private tree',c,flush=True)
