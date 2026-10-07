from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';REPO='fizzexual/kestrel-sql'
def gh(*args):return json.loads(subprocess.check_output(['gh',*args],cwd=ROOT,text=True,encoding='utf-8'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert gh('repo','view',REPO,'--json','isPrivate')['isPrivate']
assert not gh('api',f'repos/{REPO}/actions/permissions')['enabled']
old=json.loads((ROOT/'repository-publication.json').read_text())
expected={(v['tag'],a['name']):a for v in old['releases'] for a in v['assets']};assert len(expected)==74
releases=gh('api',f'repos/{REPO}/releases?per_page=100');actual={(v['tag_name'],a['name']):a for v in releases for a in v['assets']}
assert len(releases)==20 and set(actual)==set(expected)
for key,a in expected.items():assert actual[key]['size']==a['bytes'] and actual[key]['digest']=='sha256:'+a['sha256'],key
paths=[]
for check in json.loads((ROOT/'benchmarks/native-054-service-055-bundle-check.json').read_text()):
    p=ROOT.parent/check['artifact'];assert sha(p)==check['sha256'] and p.stat().st_size==check['bytes'];paths.extend([p,p.with_suffix('.zip.sha256')])
assert all(('v0.3.16',p.name) not in actual for p in paths)
backup=ROOT/'repository-publication-pre-native-054-service-055.json';assert not backup.exists();shutil.copy2(ROOT/'repository-publication.json',backup)
subprocess.run(['gh','release','upload','v0.3.16',*map(str,paths),'--repo',REPO],cwd=ROOT,check=True)
releases=gh('api',f'repos/{REPO}/releases?per_page=100');actual={(v['tag_name'],a['name']):a for v in releases for a in v['assets']}
assert len(releases)==20 and len(actual)==78
for key,a in expected.items():assert actual[key]['size']==a['bytes'] and actual[key]['digest']=='sha256:'+a['sha256'],key
added=[]
for p in paths:
    a=actual['v0.3.16',p.name];assert a['size']==p.stat().st_size and a['digest']=='sha256:'+sha(p)
    added.append({'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'server_digest_matched':True,'download_url':a['browser_download_url'],'asset_id':a['id'],
        'role':'Unreleased fixed-binary native054 or failed CAT6 service055 evidence, including complete database fixtures; no engine upgrade'})
refs=dict(line.split()[::-1] for line in subprocess.check_output(['git','ls-remote','origin','refs/tags/*'],cwd=ROOT,text=True).splitlines())
for v in json.loads((ROOT/'release-history.json').read_text())['snapshots']:
    key='refs/tags/'+v['tag'];assert refs.get(key+'^{}',refs.get(key))==v['commit'],v['tag']
next(v for v in old['releases'] if v['tag']=='v0.3.16')['assets'].extend(added)
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
old.update(uploaded_assets=78,all_78_server_digests_matched=True,completed_at_utc=now,
    native_repeat_054={'report':'PUBLICATION_054.md','new_engine_code':False,'promoted':False},
    failed_service_055={'report':'SERVICE_TRIAL_055.md','failed_performance_gates':4,'original_preflight_failures_preserved':7,'promoted':False,'default_engine_changed':False})
(ROOT/'repository-publication.json').write_text(json.dumps(old,indent=2)+'\n')
proof={'repository':REPO,'private':True,'actions_disabled':True,'new_assets':added,'all_remote_asset_sizes_and_digests_verified':78,
    'original_assets_unchanged':74,'historical_engine_tags_releases_and_archives_unchanged':20,'new_engine_release':False,'trial_promoted':False,
    'default_engine_changed':False,'prior_publication_sha256':sha(backup),'published_utc':now,'morning_report_issued':False}
(ROOT/'benchmarks/native-054-service-055-publication.json').write_text(json.dumps(proof,indent=2)+'\n')
nav=ROOT/'repository-navigation-audit.json';shutil.copy2(nav,ROOT/'repository-navigation-pre-native-054-service-055.json')
j=json.loads(nav.read_text());j.update(verified_server_asset_digests=78,native_diagnostic_report='PUBLICATION_054.md',development_trial_report='SERVICE_TRIAL_055.md',
    development_trial_promoted=False,development_trial_tests_each_mode=88,development_trial_release_tests=88,updated_at_utc=now)
nav.write_text(json.dumps(j,indent=2)+'\n')
for name,assets in [('PUBLICATION_054.md',added[:2]),('SERVICE_TRIAL_055.md',added[2:])]:
    p=ROOT/name;s=p.read_text(encoding='utf-8');s+='\nPrivate immutable [full evidence and database fixtures]('+assets[0]['download_url']+') and [SHA-256]('+assets[1]['download_url']+'). This distinct supplemental asset preserves the report before this final upload-link paragraph and does not replace any supported engine archive.\n';p.write_text(s,encoding='utf-8')
print(json.dumps(proof))
