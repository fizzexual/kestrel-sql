"""Prepare complete verified Git objects through the API; never update a branch."""
import base64,hashlib,json,os,re,subprocess
from datetime import datetime,timedelta,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';REPO='fizzexual/kestrel-sql'
ORIGINAL='859501c70dc62a1d48017d6a0e60c998b36ec5a5';PREVIOUS='6246763cdc6768014f961ef5121f3bdd76130d3b'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
def now():return datetime.now(timezone.utc).isoformat()
def git(*a,input=None):return subprocess.check_output(['git',*a],cwd=ROOT,input=input).decode('utf-8').strip()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def gh_get(path):return json.loads(subprocess.check_output(['gh','api',f'repos/{REPO}'+('/'+path if path else '')],cwd=ROOT))
assert git('rev-parse','HEAD')==ORIGINAL and git('status','--porcelain')==''
assert git('ls-remote','origin','refs/heads/main').split()[0]==PREVIOUS
assert gh_get('')['private'] and gh_get('actions/permissions')['enabled'] is False
assert not (W/'atomic-api-policy.json').exists()
tree=git('rev-parse','HEAD^{tree}');base_tree=git('rev-parse',PREVIOUS+'^{tree}')
new_objects=git('rev-list','--objects',ORIGINAL,'^'+PREVIOUS).splitlines()
types=git('cat-file','--batch-check',input=(''.join(line.split(' ',1)[0]+'\n' for line in new_objects)).encode()).splitlines()
blobs=[(v.split()[0],int(v.split()[2])) for v in types if v.split()[1]=='blob']
commit_raw=subprocess.check_output(['git','cat-file','commit',ORIGINAL],cwd=ROOT)
(W/'original-verified-git-commit.raw').write_bytes(commit_raw)
headers,message=commit_raw.decode('utf-8').split('\n\n',1);parsed={}
for line in headers.splitlines():
    key,value=line.split(' ',1);assert key in ['tree','parent','author','committer'] and key not in parsed;parsed[key]=value
assert parsed['tree']==tree and parsed['parent']==PREVIOUS
def signature(value):
    name,email,seconds,offset=re.fullmatch(r'(.*) <([^<>]+)> (\d+) ([+-]\d{4})',value).groups()
    minutes=(int(offset[1:3])*60+int(offset[3:]))*(1 if offset[0]=='+' else -1)
    return {'name':name,'email':email,'date':datetime.fromtimestamp(int(seconds),timezone(timedelta(minutes=minutes))).isoformat(timespec='seconds')}
entries={}
for record in subprocess.check_output(['git','ls-tree','-rz',ORIGINAL],cwd=ROOT).decode('utf-8').split('\0'):
    if not record:continue
    metadata,path=record.split('\t',1);mode,kind,oid=metadata.split();entries[path]={'path':path,'mode':mode,'type':kind,'sha':oid}
diff=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-status','-r','-z',PREVIOUS,ORIGINAL],cwd=ROOT).decode('utf-8').split('\0')
changed=[]
for i in range(0,len(diff)-1,2):
    status,path=diff[i:i+2];assert status in ['A','M'];changed.append(entries[path])
policy={'declared_utc':now(),'original_verified_commit':ORIGINAL,'previous_remote_main':PREVIOUS,'expected_complete_tree':tree,'base_tree':base_tree,'new_blob_count':len(blobs),'new_blob_bytes':sum(b[1] for b in blobs),'changed_files':len(changed),'preparation_only_no_branch_write':True,'no_intermediate_branch_state':True,'supported_source_binary_benchmark_policy_and_all_fixtures_unchanged':True,'no_native_or_timed_rerun':True,'publisher_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'official_api_docs':['https://docs.github.com/en/rest/git/blobs','https://docs.github.com/en/rest/git/trees','https://docs.github.com/en/rest/git/commits','https://docs.github.com/en/rest/git/refs']}
save(W/'atomic-api-policy.json',policy);records=[];serial=0
def post(path,payload):
    global serial
    assert path in ['git/blobs','git/trees','git/commits'],'no branch endpoint permitted'
    serial+=1;body=json.dumps(payload,separators=(',',':')).encode('utf-8');started=now()
    r=subprocess.run(['gh','api','--method','POST',f'repos/{REPO}/'+path,'--input','-'],cwd=ROOT,input=body,capture_output=True)
    (W/f'atomic-{serial:03}.stdout').write_bytes(r.stdout);(W/f'atomic-{serial:03}.stderr').write_bytes(r.stderr)
    records.append({'serial':serial,'method':'POST','path':path,'started_utc':started,'ended_utc':now(),'exit':r.returncode,'request_bytes':len(body),'request_sha256':hashlib.sha256(body).hexdigest()})
    save(W/'atomic-api-progress.json',records)
    if r.returncode:
        save(W/'atomic-api-failure.json',records[-1]);print(r.stderr.decode('utf-8',errors='replace')[-2000:],flush=True);raise SystemExit(r.returncode)
    return json.loads(r.stdout)
for i,(oid,size) in enumerate(blobs,1):
    data=subprocess.check_output(['git','cat-file','blob',oid],cwd=ROOT);assert len(data)==size
    actual=post('git/blobs',{'content':base64.b64encode(data).decode('ascii'),'encoding':'base64'});assert actual['sha']==oid
    if i%10==0 or size>10_000_000:print('prepared exact blobs',i,'of',len(blobs),'last bytes',size,flush=True)
actual_tree=post('git/trees',{'base_tree':base_tree,'tree':changed});assert actual_tree['sha']==tree
actual_commit=post('git/commits',{'message':message,'tree':tree,'parents':[PREVIOUS],'author':signature(parsed['author']),'committer':signature(parsed['committer'])})
assert actual_commit['tree']['sha']==tree and [v['sha'] for v in actual_commit['parents']]==[PREVIOUS]
same_commit=actual_commit['sha']==ORIGINAL
assert git('ls-remote','origin','refs/heads/main').split()[0]==PREVIOUS
save(W/'atomic-api-prepared.json',{**policy,'complete':True,'prepared_utc':now(),'all_blob_sha_and_complete_tree_match_local':True,'created_commit_sha':actual_commit['sha'],'exact_original_commit_hash_matched':same_commit,'author_message_tree_and_parent_derived_from_original_raw':True,'remote_main_still_unchanged':True,'branch_update_not_performed':True})
print(json.dumps({'prepared':True,'new_blobs':len(blobs),'commit':actual_commit['sha'],'exact_original_commit':same_commit,'remote_main_unchanged':True}),flush=True)
