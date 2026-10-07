"""One final non-forced branch update to the exact fully prepared/verified078 commit."""
import hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';REPO='fizzexual/kestrel-sql'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True,encoding='utf-8').strip()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def gh(path):return json.loads(subprocess.check_output(['gh','api',f'repos/{REPO}'+('/'+path if path else '')],cwd=ROOT))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
prepared=load(W/'atomic-api-prepared.json');assert prepared['complete'] and prepared['all_blob_sha_and_complete_tree_match_local'] and prepared['exact_original_commit_hash_matched']
original=prepared['original_verified_commit'];previous=prepared['previous_remote_main']
assert git('rev-parse','HEAD')==original and git('status','--porcelain')==''
assert git('ls-remote','origin','refs/heads/main').split()[0]==previous and gh('git/ref/heads/main')['object']['sha']==previous
assert gh('')['private'] and gh('actions/permissions')['enabled'] is False
remote=gh('git/commits/'+original);assert remote['sha']==original and remote['tree']['sha']==git('rev-parse','HEAD^{tree}') and [p['sha'] for p in remote['parents']]==[previous]
pub=load(ROOT/'repository-publication.json');releases=gh('releases?per_page=100');actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']};expected={(r['tag'],a['name']):a for r in pub['releases'] for a in r['assets']}
assert len(releases)==20 and len(actual)==122 and set(actual)==set(expected)
for k,a in expected.items():
    assert actual[k]['size']==a['bytes'] and actual[k]['digest']=='sha256:'+a['sha256']
    if 'asset_id' in a:assert actual[k]['id']==a['asset_id']
for a in load(ROOT/'benchmarks/source-state-078-publication.json')['repository_artifacts']:
    p=ROOT/a['repository_path'];assert sha(p)==a['sha256'] and p.stat().st_size==a['bytes']
assert not (W/'atomic-final-update.json').exists()
started=datetime.now(timezone.utc).isoformat();body=json.dumps({'sha':original,'force':False}).encode('utf-8')
r=subprocess.run(['gh','api','--method','PATCH',f'repos/{REPO}/git/refs/heads/main','--input','-'],cwd=ROOT,input=body,capture_output=True)
(W/'atomic-final-update.stdout').write_bytes(r.stdout);(W/'atomic-final-update.stderr').write_bytes(r.stderr)
after=git('ls-remote','origin','refs/heads/main').split()[0]
result={'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),'exit':r.returncode,'remote_before':previous,'remote_after':after,'exact_verified_commit':original,'single_final_branch_update':True,'force':False,'no_intermediate_main_states':True,'all_objects_and_complete_tree_preverified':True,'remote_updated':after==original,'source_binary_fixture_or_benchmark_policy_changed':False,'native_or_timed_rerun':False,'all122_older_release_digests_and20_releases_checked':True}
(W/'atomic-final-update.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
assert result['remote_updated'],r.stderr.decode('utf-8',errors='replace')
assert git('status','--porcelain')==''
