"""Post-push proof of private079 archive blobs and unchanged releases/core."""
import hashlib,json,os,subprocess
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent
ROOT=next(p for p in [W.parents[1]/'outputs/kestrel-sql',W.parents[1]] if (p/'SOURCE_COMPARE_079.md').is_file())
REPO='fizzexual/kestrel-sql'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf-8').strip()
def gh(path):return json.loads(subprocess.check_output(['gh','api',path],cwd=ROOT,text=True,encoding='utf-8'))
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
commit=git('rev-parse','HEAD');assert git('ls-remote','origin','refs/heads/main').split()[0]==commit and git('status','--porcelain')==''
root_tree=git('rev-parse','HEAD^{tree}');tree=gh(f'repos/{REPO}/git/trees/{root_tree}');assert tree['sha']==root_tree and not tree.get('truncated')
bench=next(v for v in tree['tree'] if v['path']=='benchmarks');entries=gh(f'repos/{REPO}/git/trees/{bench["sha"]}');assert not entries.get('truncated')
publication=load(ROOT/'benchmarks/source-compare-079-publication.json');bundle=load(ROOT/'benchmarks/source-compare-079-bundle-check.json')
assert len(publication['repository_artifacts'])==2*bundle['parts']
for a in publication['repository_artifacts']:
    p=ROOT/a['repository_path'];assert p.stat().st_size==a['bytes'] and sha(p)==a['sha256']
    remote=next(v for v in entries['tree'] if v['path']==p.name)
    assert remote['type']=='blob' and remote['sha']==a['git_blob_sha'] and remote['size']==a['bytes']
assert gh(f'repos/{REPO}')['private'] and not gh(f'repos/{REPO}/actions/permissions')['enabled']
pub=load(ROOT/'repository-publication.json');assert pub['uploaded_assets']==122 and pub['anchor_reuse_076']['release_asset_upload_pending']
assert pub['source_compare_079']['fresh_comparison_complete'] and not pub['source_compare_079']['all_checks_passed'] and not pub['source_compare_079']['promoted'] and pub['source_compare_079']['fresh_speed_measurement']
releases=gh(f'repos/{REPO}/releases?per_page=100');actual={(r['tag_name'],a['name']):a for r in releases for a in r['assets']}
expected={(r['tag'],a['name']):a for r in pub['releases'] for a in r['assets']};assert len(releases)==20 and len(actual)==122 and set(actual)==set(expected)
for k,a in expected.items():
    assert actual[k]['size']==a['bytes'] and actual[k]['digest']=='sha256:'+a['sha256']
    if 'asset_id' in a:assert actual[k]['id']==a['asset_id']
refs=dict(line.split()[::-1] for line in git('ls-remote','origin','refs/tags/*').splitlines())
for r in load(ROOT/'release-history.json')['snapshots']:
    key='refs/tags/'+r['tag'];assert refs.get(key+'^{}',refs.get(key))==r['commit']
base=load(ROOT/'benchmarks/source-compare-079/baseline.json')
for n,d in base['core_source_sha256'].items():assert sha(ROOT/n)==d,n
for n,d in base['baseline_binary_sha256'].items():assert sha(ROOT/'bin'/n)==d,n
morning=load(ROOT/'benchmarks/overnight-2026-10-07-report-check.json');assert sha(ROOT/morning['report_file'])==morning['report_sha256']
check=load(ROOT/'benchmarks/source-compare-079-document-check.json');assert check['all_archives_member_crc_and_sha_verified'] and check['all_local_and_release_links_verified']
assert git('hash-object','--no-filters',str(ROOT/'MANIFEST.sha256'))==git('rev-parse','HEAD:MANIFEST.sha256')
result={'verified_utc':datetime.now(timezone.utc).isoformat(),'private':True,'actions_disabled':True,'local_remote_main_commit':commit,'clean_working_tree':True,'complete_archive_parts':bundle['parts'],'all_archive_and_sidecar_remote_blob_sha_and_sizes_match_local_whole_sha256':True,'all122_older_release_sizes_digests_and_recorded_ids_match':True,'all20_engine_tags_and_releases_unchanged':True,'supported_core_source_and_binaries_unchanged':True,'076_upload_pending_unchanged':True,'fresh_comparison_rejected_no_engine_adoption':True,'morning_report_unchanged':True,'local_full_archive_and_prior_payload_checks_passed':True}
(W/'git-publication-check.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result),flush=True)
