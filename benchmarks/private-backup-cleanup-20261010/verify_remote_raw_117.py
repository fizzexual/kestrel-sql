"""Fresh authenticated GitHub blob downloads for the complete immutable trial117 tree."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib, json, os, stat, subprocess, traceback, zipfile

R = Path('D:/Codex/Kestrel/work')
REPO = Path('D:/Codex/Kestrel/outputs/kestrel-sql')
SCOPE = 'benchmarks/adaptive-speed-117'
DEST = R / 'github-verified-trial117-20261010'
GH = 'C:/Users/Frizer/AppData/Local/Microsoft/WinGet/Packages/GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe/bin/gh.exe'
HEAD = '6aae0a3994fad1eef1b6267346212a3b094078a4'

def utc(): return datetime.now(timezone.utc).isoformat()
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p, value):
    with p.open('x', encoding='utf-8', newline='\n') as f: f.write(json.dumps(value, indent=2) + '\n')
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def real(p):
    for q in [p, *p.parents]:
        assert q.exists() and not q.is_symlink() and not q.is_junction(), q
        assert not (q.stat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT), q
    assert p.resolve() == p, p
def git(*args):
    p = subprocess.run(['git', '--no-optional-locks', '-c', 'safe.directory='+REPO.as_posix(),
         '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '-C', str(REPO), *args],
         capture_output=True, env={**os.environ, 'GIT_TERMINAL_PROMPT':'0', 'GCM_INTERACTIVE':'never'}, timeout=120)
    assert p.returncode == 0, (args, p.returncode, p.stderr)
    return p.stdout
def api(endpoint, name):
    p = subprocess.run([GH, 'api', '--method', 'GET', endpoint,
        '-H', 'Accept: application/vnd.github+json', '-H', 'Cache-Control: no-cache'], capture_output=True, timeout=120)
    (DEST/'api'/f'{name}.stdout').write_bytes(p.stdout)
    (DEST/'api'/f'{name}.stderr').write_bytes(p.stderr)
    save(DEST/'api'/f'{name}.exit.json', {'actual_gh_exit':p.returncode, 'utc':utc(), 'endpoint':endpoint})
    assert p.returncode == 0, (name, p.returncode, p.stderr)
    return json.loads(p.stdout)

assert not DEST.exists()
real(REPO); real(R)
guard=load(sorted(R.glob('guard-final-117-*.json'))[-1])
assert guard['verified_idle_terminal_reset'] and not guard['active_processes']
assert (datetime.now(timezone.utc)-datetime.fromisoformat(guard['utc'])).total_seconds() < 1800
push=load(R/'history-batched-117-proof.json')
assert push['complete'] and push['local_commits_not_on_remote_main']==0
assert git('rev-parse', 'HEAD').decode().strip()==HEAD and not git('status', '--porcelain=v1', '--untracked-files=all')
assert git('ls-remote', '--exit-code', 'origin', 'refs/heads/main').split()[0].decode()==HEAD
root_oid=git('rev-parse', HEAD+'^{tree}').decode().strip()
scope_oid=git('rev-parse', HEAD+':'+SCOPE).decode().strip()
entries={}
for record in git('ls-tree', '-r', '-z', HEAD, '--', SCOPE).split(b'\0'):
    if not record: continue
    left, rawpath=record.split(b'\t',1); mode, typ, oid=left.decode().split(); path=rawpath.decode('utf-8')
    assert typ=='blob' and mode=='100644' and path.startswith(SCOPE+'/'), (mode,typ,path)
    rel=path[len(SCOPE)+1:]; parts=PurePosixPath(rel).parts
    assert parts and all(x not in ('..','.','') and ':' not in x and '\\' not in x for x in parts)
    source=REPO/path; real(source)
    entries[rel]={'git_blob_oid':oid, 'bytes':source.stat().st_size, 'sha256':sha(source)}
assert entries and len([n for n in entries if n.startswith('evidence-') and n.endswith('.zip')])==53
DEST.mkdir(); (DEST/'api').mkdir(); (DEST/'logs').mkdir(); (DEST/'files').mkdir()
policy={'declared_utc':utc(), 'before_any_remote_raw_download':True, 'private_repository':'https://github.com/fizzexual/kestrel-sql',
    'immutable_commit':HEAD, 'root_tree_oid':root_oid, 'scope_tree_oid':scope_oid, 'scope':SCOPE, 'entries':entries,
    'workers':4, 'fresh_authenticated_GET_no_cli_cache':True, 'raw_media_type':'application/vnd.github.raw+json',
    'primary_documentation':'https://docs.github.com/en/rest/git/blobs#get-a-blob',
    'acceptance':'Actual exit0 for every fresh download; exact size, SHA256 and Git blob SHA1; exact remote complete tree; all53 ZIP member CRCs; unchanged local inputs; private before and after.',
    'no_cleanup_or_engine_build_or_benchmark_in_this_helper':True}
save(DEST/'policy.json',policy)
try:
    privacy=api('repos/fizzexual/kestrel-sql','privacy-before')
    assert privacy['private'] and privacy['html_url']=='https://github.com/fizzexual/kestrel-sql'
    commit=api('repos/fizzexual/kestrel-sql/git/commits/'+HEAD,'immutable-commit')
    assert commit['sha']==HEAD and commit['tree']['sha']==root_oid
    tree=api('repos/fizzexual/kestrel-sql/git/trees/'+scope_oid+'?recursive=1','complete-scope-tree')
    assert tree['sha']==scope_oid and not tree['truncated']
    remote={row['path']:{'git_blob_oid':row['sha'],'bytes':row['size']} for row in tree['tree'] if row['type']=='blob'}
    assert all(row['mode']=='100644' for row in tree['tree'] if row['type']=='blob')
    assert remote=={n:{'git_blob_oid':v['git_blob_oid'],'bytes':v['bytes']} for n,v in entries.items()}
    def download(item):
        index,(name,v)=item; dest=DEST/'files'/name; dest.parent.mkdir(parents=True,exist_ok=True)
        stderr=DEST/'logs'/f'{index:04d}.stderr'; endpoint='repos/fizzexual/kestrel-sql/git/blobs/'+v['git_blob_oid']
        with dest.open('xb') as out, stderr.open('xb') as err:
            child=subprocess.run([GH,'api','--method','GET',endpoint,'-H','Accept: application/vnd.github.raw+json',
                    '-H','Cache-Control: no-cache'],stdout=out,stderr=err,timeout=300)
        result={'index':index,'name':name,'endpoint':endpoint,'actual_gh_exit':child.returncode,'utc':utc()}
        save(DEST/'logs'/f'{index:04d}.exit.json',result)
        assert child.returncode==0,(name,child.returncode)
        assert dest.stat().st_size==v['bytes'] and sha(dest)==v['sha256'],name
        h=hashlib.sha1(); h.update(('blob '+str(v['bytes'])+'\0').encode())
        with dest.open('rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
        assert h.hexdigest()==v['git_blob_oid'],name
        result.update(v); result['fresh_download_SHA256_size_git_oid_exact']=True
        save(DEST/'logs'/f'{index:04d}.verified.json',result)
        return result
    results=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(download,item) for item in enumerate(sorted(entries.items()))]
        for f in as_completed(futures):
            results.append(f.result())
            if len(results)%25==0 or len(results)==len(entries):
                print(json.dumps({'downloaded_verified_files':len(results),'of':len(entries)}),flush=True)
    preserved=load(DEST/'files'/'preservation-proof.json'); assert preserved['complete']
    for part in preserved['parts']:
        p=DEST/'files'/part['name']; assert sha(p)==part['sha256'] and p.stat().st_size==part['bytes']
        with zipfile.ZipFile(p) as z: assert z.testzip() is None,part['name']
    assert len(preserved['parts'])==53
    assert {p.relative_to(DEST/'files').as_posix() for p in (DEST/'files').rglob('*') if p.is_file()}==set(entries)
    assert git('rev-parse','HEAD').decode().strip()==HEAD and not git('status','--porcelain=v1','--untracked-files=all')
    for name,v in entries.items():
        p=REPO/SCOPE/name; real(p); assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],name
    privacy=api('repos/fizzexual/kestrel-sql','privacy-after')
    assert privacy['private'] and privacy['html_url']=='https://github.com/fizzexual/kestrel-sql'
    proof={'complete':True,'utc':utc(),'immutable_remote_commit':HEAD,'scope':SCOPE,'private_before_and_after':True,
        'remote_commit_root_and_complete_scope_tree_exact':True,'fresh_remote_downloaded_files':len(entries),
        'downloaded_bytes':sum(v['bytes'] for v in entries.values()),'all_actual_gh_exits0':True,
        'every_download_size_SHA256_git_oid_exact':True,'all53_remote_downloaded_ZIP_member_CRCs_pass':True,
        'original_source_tree_unchanged':True,'remote_backed_logical_raw_files':preserved['files'],
        'remote_backed_raw_logical_bytes':preserved['logical_bytes'],
        'original_whole_restored_audit_proof_byte_identical_no_fresh_full_restored_audit_claimed':True,
        'only_trial117_raw_backup_verified_not_all_recent_trials':True,'cleanup_not_performed':True,
        'downloads':sorted(results,key=lambda x:x['index'])}
    save(DEST/'proof.json',proof)
    print(json.dumps({k:v for k,v in proof.items() if k!='downloads'}),flush=True)
except BaseException:
    save(DEST/'failure.json',{'utc':utc(),'error':traceback.format_exc(),'partials_and_originals_retained':True,'no_cleanup_performed':True})
    raise
