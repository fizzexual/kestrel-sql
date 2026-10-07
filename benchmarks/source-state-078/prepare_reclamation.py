"""Verify full private archives before removing only duplicate076/077 working stores."""
import hashlib,json,os,shutil,subprocess,zipfile
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';WORK=W.parent
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def gh(path):return json.loads(subprocess.check_output(['gh','api',path],text=True,encoding='utf-8'))
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();assert subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]==commit
tree=gh(f'repos/fizzexual/kestrel-sql/git/trees/{commit}');assert not tree.get('truncated');bench=next(v for v in tree['tree'] if v['path']=='benchmarks');entries=gh(f'repos/fizzexual/kestrel-sql/git/trees/{bench["sha"]}');assert not entries.get('truncated')
publication=load(ROOT/'repository-publication.json');expected={(r['tag'],a['name']):a for r in publication['releases'] for a in r['assets']};assert len(expected)==122
releases=gh('repos/fizzexual/kestrel-sql/releases?per_page=100');actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']};assert len(releases)==20 and set(actual)==set(expected)
for k,a in expected.items():assert actual[k]['size']==a['bytes'] and actual[k]['digest']=='sha256:'+a['sha256']
archives=[];members={}
for label,key in [('anchor-reuse-076','anchor_reuse_076'),('recovery-compare-077','recovery_compare_077')]:
    for a in publication[key]['repository_artifacts']:
        p=ROOT/a['repository_path'];assert sha(p)==a['sha256'] and p.stat().st_size==a['bytes']
        remote=next(v for v in entries['tree'] if v['path']==p.name);assert remote['sha']==a['git_blob_sha'] and remote['size']==a['bytes']
        if not p.name.endswith('.zip'):continue
        bundle=load(ROOT/f'benchmarks/{label}-bundle-check.json');items=bundle.get('artifacts',[bundle]);item=next(v for v in items if v['artifact']==p.name)
        local=ROOT.parent/p.name;assert sha(local)==item['sha256']==a['sha256']
        with zipfile.ZipFile(local) as z:
            assert z.testzip() is None
            for name in z.namelist():
                prefix='kestrel-sql/benchmarks/'+label+'/'
                if name.startswith(prefix):members[(label,name[len(prefix):])]=(local,name)
        archives.append({'path':str(local),'sha256':a['sha256'],'all_zip_crc_and_private_git_blob_verified':True})
targets=[]
for num,label,folders in [('076','anchor-reuse-076',['fixtures','rust-temp']),('077','recovery-compare-077',['fixtures'])]:
    old=WORK/f'perf-{num}';inventory=load(old/'bundle-fixture-inventory.json')
    for folder in folders:
        target=(old/folder).resolve();assert target==WORK/f'perf-{num}'/folder
        current={p.relative_to(old).as_posix():p for p in target.rglob('*') if p.is_file()}
        selected={n:v for n,v in inventory.items() if n.startswith(folder+'/')};assert set(current)==set(selected),('unexpected file not archived',target)
        files=[]
        by_archive={}
        for n,d in selected.items():
            p=current[n];assert p.stat().st_size==d['bytes'] and sha(p)==d['sha256']
            archive,member=members[(label,n)];by_archive.setdefault(archive,[]).append((member,d))
            files.append({'path':str(p.resolve()),'bytes':d['bytes'],'sha256':d['sha256']})
        for archive,items in by_archive.items():
            with zipfile.ZipFile(archive) as z:
                for member,d in items:
                    with z.open(member) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==d['sha256']
        targets.append({'target':str(target),'files':files,'logical_bytes':sum(v['bytes'] for v in files)})
result={'verified_utc':datetime.now(timezone.utc).isoformat(),'local_remote_commit':commit,'targets':targets,'archives':archives,'private_server_assets_verified':122,'only_archived_duplicate_working_stores':True,'all_full_archives_raw_logs_policies_inputs_source_and_binaries_retained':True,'free_bytes_before':shutil.disk_usage(W).free}
(W/'reclamation-plan.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verified':True,'targets':len(targets),'files':sum(len(t['files']) for t in targets),'logical_bytes':sum(t['logical_bytes'] for t in targets),'all_private_archives':len(archives),'free_bytes_before':result['free_bytes_before']}))
