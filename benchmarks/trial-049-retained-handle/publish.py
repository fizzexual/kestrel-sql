from pathlib import Path
import subprocess,hashlib,json,datetime,shutil
w=Path(__file__).parent;r=w.parents[1]/'outputs/kestrel-sql';repo='fizzexual/kestrel-sql'
def gh(*args):return json.loads(subprocess.check_output(['gh',*args],cwd=r,text=True,encoding='utf-8'))
def sha(p):return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
assert gh('repo','view',repo,'--json','isPrivate')['isPrivate']
assert not gh('api',f'repos/{repo}/actions/permissions')['enabled']
old=json.loads((r/'repository-publication.json').read_text(encoding='utf-8'))
expected={(v['tag'],a['name']):a for v in old['releases'] for a in v['assets']};assert len(expected)==62
releases=gh('api',f'repos/{repo}/releases?per_page=100');actual={(v['tag_name'],a['name']):a for v in releases for a in v['assets']}
assert len(releases)==20 and set(actual)==set(expected)
for key,a in expected.items():assert actual[key]['size']==a['bytes'] and actual[key]['digest']=='sha256:'+a['sha256'],key
package=r.parent/'kestrel-sql-development-cat5-049-evidence.zip';paths=[package,package.with_suffix('.zip.sha256')]
check=json.loads((r/'benchmarks/trial-049-bundle-check.json').read_text(encoding='utf-8'));assert sha(package)==check['sha256'] and package.stat().st_size==check['bytes']
assert all(('v0.3.16',p.name) not in actual for p in paths)
backup=r/'repository-publication-pre-trial-049.json';assert not backup.exists();shutil.copy2(r/'repository-publication.json',backup)
subprocess.run(['gh','release','upload','v0.3.16',*[str(p) for p in paths],'--repo',repo],cwd=r,check=True)
releases=gh('api',f'repos/{repo}/releases?per_page=100');actual={(v['tag_name'],a['name']):a for v in releases for a in v['assets']};assert len(releases)==20 and len(actual)==64
for key,a in expected.items():assert actual[key]['size']==a['bytes'] and actual[key]['digest']=='sha256:'+a['sha256'],key
added=[]
for p in paths:
    a=actual['v0.3.16',p.name];assert a['size']==p.stat().st_size and a['digest']=='sha256:'+sha(p)
    added.append({'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'server_digest_matched':True,'download_url':a['browser_download_url'],'asset_id':a['id'],'role':'Unreleased CAT5 trial evidence; no replacement supported engine'})
refs=dict(line.split()[::-1] for line in subprocess.check_output(['git','ls-remote','origin','refs/tags/*'],cwd=r,text=True).splitlines())
for v in json.loads((r/'release-history.json').read_text(encoding='utf-8'))['snapshots']:
    key='refs/tags/'+v['tag'];assert refs.get(key+'^{}',refs.get(key))==v['commit'],v['tag']
next(v for v in old['releases'] if v['tag']=='v0.3.16')['assets'].extend(added)
old.update(uploaded_assets=64,all_64_server_digests_matched=True,completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),development_trial_049={'report':'TRIAL_049.md','promoted':False,'default_engine_changed':False,'new_engine_release':False})
(r/'repository-publication.json').write_text(json.dumps(old,indent=2)+'\n',encoding='utf-8')
proof={'repository':repo,'private':True,'actions_disabled':True,'new_assets':added,'all_remote_asset_sizes_and_digests_verified':64,'original_assets_unchanged':62,'historical_tags_and_releases_unchanged':20,'new_engine_release':False,'default_engine_changed':False,'trial_promoted':False,'prior_publication_sha256':sha(backup),'completed_utc':old['completed_at_utc']}
(r/'benchmarks/trial-049-publication.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
nav=r/'repository-navigation-audit.json';shutil.copy2(nav,r/'repository-navigation-pre-trial-049.json');v=json.loads(nav.read_text(encoding='utf-8'));v.update(verified_server_asset_digests=64,development_trial_report='TRIAL_049.md',development_trial_promoted=False,development_trial_tests_each_mode=82,updated_at_utc=old['completed_at_utc']);nav.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
p=r/'TRIAL_049.md';s=p.read_text(encoding='utf-8');s+='\nPrivate immutable [development evidence download]('+added[0]['download_url']+') and [SHA-256]('+added[1]['download_url']+'); this supplements the [supported 0.3.16 release](https://github.com/fizzexual/kestrel-sql/releases/tag/v0.3.16) without replacing it. The bundle contains the report as written before upload; this final download-link paragraph and server publication proof live in the repository.\n';p.write_text(s,encoding='utf-8')
print(json.dumps(proof))
