from pathlib import Path
import datetime, hashlib, json, shutil, subprocess
W=Path(__file__).resolve().parent
ROOT=W.parents[1]/'outputs/kestrel-sql'; REPO='fizzexual/kestrel-sql'
def gh(*args): return json.loads(subprocess.check_output(['gh',*args],cwd=ROOT,text=True,encoding='utf-8'))
def sha(p):
    with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
assert gh('repo','view',REPO,'--json','isPrivate')['isPrivate']
assert not gh('api',f'repos/{REPO}/actions/permissions')['enabled']
old=json.loads((ROOT/'repository-publication.json').read_text(encoding='utf-8'))
expected={(v['tag'],a['name']):a for v in old['releases'] for a in v['assets']}
assert len(expected)==72
releases=gh('api',f'repos/{REPO}/releases?per_page=100')
actual={(v['tag_name'],a['name']):a for v in releases for a in v['assets']}
assert len(releases)==20 and set(actual)==set(expected)
for key,a in expected.items(): assert actual[key]['size']==a['bytes'] and actual[key]['digest']=='sha256:'+a['sha256'],key
check=json.loads((ROOT/'benchmarks/trial-053-bundle-check.json').read_text())
p=ROOT.parent/check['artifact']
assert sha(p)==check['sha256'] and p.stat().st_size==check['bytes']
paths=[p,p.with_suffix('.zip.sha256')]
assert all(('v0.3.16',p.name) not in actual for p in paths)
backup=ROOT/'repository-publication-pre-trial-053.json'; assert not backup.exists()
shutil.copy2(ROOT/'repository-publication.json',backup)
subprocess.run(['gh','release','upload','v0.3.16',*map(str,paths),'--repo',REPO],cwd=ROOT,check=True)
releases=gh('api',f'repos/{REPO}/releases?per_page=100')
actual={(v['tag_name'],a['name']):a for v in releases for a in v['assets']}
assert len(releases)==20 and len(actual)==74
for key,a in expected.items(): assert actual[key]['size']==a['bytes'] and actual[key]['digest']=='sha256:'+a['sha256'],key
added=[]
for p in paths:
    a=actual['v0.3.16',p.name]
    assert a['size']==p.stat().st_size and a['digest']=='sha256:'+sha(p)
    added.append({'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'server_digest_matched':True,
                  'download_url':a['browser_download_url'],'asset_id':a['id'],
                  'role':'Isolated compact CAT6 trial 053, failed p50 guard; full native fixtures included; no engine upgrade'})
refs=dict(line.split()[::-1] for line in subprocess.check_output(['git','ls-remote','origin','refs/tags/*'],cwd=ROOT,text=True).splitlines())
for v in json.loads((ROOT/'release-history.json').read_text())['snapshots']:
    key='refs/tags/'+v['tag']; assert refs.get(key+'^{}',refs.get(key))==v['commit'],v['tag']
next(v for v in old['releases'] if v['tag']=='v0.3.16')['assets'].extend(added)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
old.update(uploaded_assets=74,all_74_server_digests_matched=True,completed_at_utc=now,
           compact_trial_053={'report':'TRIAL_053.md','native_gates_passed':5,'native_gates_failed':1,'promoted':False,'default_engine_changed':False})
(ROOT/'repository-publication.json').write_text(json.dumps(old,indent=2)+'\n',encoding='utf-8')
proof={'repository':REPO,'private':True,'actions_disabled':True,'new_assets':added,
       'all_remote_asset_sizes_and_digests_verified':74,'original_assets_unchanged':72,
       'historical_engine_tags_releases_and_archives_unchanged':20,'new_engine_release':False,
       'default_engine_changed':False,'trial_promoted':False,'prior_publication_sha256':sha(backup),
       'published_utc':now,'morning_report_issued':False}
(ROOT/'benchmarks/trial-053-publication.json').write_text(json.dumps(proof,indent=2)+'\n')
nav=ROOT/'repository-navigation-audit.json'; shutil.copy2(nav,ROOT/'repository-navigation-pre-trial-053.json')
v=json.loads(nav.read_text()); v.update(verified_server_asset_digests=74,development_trial_report='TRIAL_053.md',
    development_trial_promoted=False,development_trial_tests_each_mode=None,development_trial_release_tests=88,updated_at_utc=now)
nav.write_text(json.dumps(v,indent=2)+'\n')
p=ROOT/'TRIAL_053.md'; s=p.read_text(encoding='utf-8')
s+='\nPrivate immutable [full development evidence and native database fixtures]('+added[0]['download_url']+') and [SHA-256]('+added[1]['download_url']+'). This distinct supplemental asset preserves the report before this final upload-link paragraph and does not replace any supported engine archive.\n'
p.write_text(s,encoding='utf-8')
print(json.dumps(proof))
