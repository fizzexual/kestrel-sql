"""Preserve full verified ZIP through authorized private Git after upload HTTP500s."""
import ast,hashlib,json,os,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';D=ROOT/'benchmarks/anchor-reuse-076-finalization'
os.environ.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix())
def now():return datetime.now(timezone.utc).isoformat()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert load(D/'publication-attempt-2-status.json')['exit']==1 and load(D/'publication-attempt-3-api-status.json')['exit']==1
assert load(D/'remote-state-after-third-500.json')['new_attempt_asset_state']==[]
bundle=load(ROOT/'benchmarks/anchor-reuse-076-bundle-check.json');archive=ROOT.parent/bundle['artifact']
assert sha(archive)==bundle['sha256'] and archive.stat().st_size<50*1024*1024
repo_artifacts=[]
for source in [archive,archive.with_suffix('.zip.sha256')]:
    dest=ROOT/'benchmarks'/source.name;assert not dest.exists();shutil.copy2(source,dest);assert sha(dest)==sha(source)
    repo_artifacts.append({'repository_path':dest.relative_to(ROOT).as_posix(),'bytes':dest.stat().st_size,'sha256':sha(dest),
                          'git_blob_sha':subprocess.check_output(['git','hash-object',str(dest)],cwd=ROOT,text=True).strip(),
                          'repository_url':'https://github.com/fizzexual/kestrel-sql/blob/main/'+dest.relative_to(ROOT).as_posix()})
sources=['inspect_remote.py','inspect_remote_second.py','inspect_remote_third.py','retry_publish.py','api_publish.py','complete_via_git.py']
for name in sources:
    p=D/name;assert not p.exists();shutil.copy2(W/name,p);ast.parse(p.read_text(encoding='utf-8-sig'))
old=load(ROOT/'repository-publication.json');assert old['uploaded_assets']==122
old['anchor_reuse_076']={'report':'ANCHOR_REUSE_076.md','development_only':True,'untimed_qualification_complete':True,'promoted':False,
                        'full_evidence_method':'private Git repository blob','repository_artifacts':repo_artifacts,
                        'release_asset_upload_pending':True,'failed_release_upload_attempts':3,'prepared_utc':now()}
save(ROOT/'repository-publication.json',old)
pub={'private':True,'actions_disabled':True,'new_assets':[],'repository_artifacts':repo_artifacts,'remote_assets_verified':122,
     'previous_assets_unchanged':122,'historical_engine_tags_releases_unchanged':20,'no_timed_cohort':True,
     'new_engine_release':False,'default_engine_changed':False,'release_asset_upload_pending':True,'prepared_for_git_utc':now()}
save(ROOT/'benchmarks/anchor-reuse-076-publication.json',pub)
nav=ROOT/'repository-navigation-audit.json';snapshot=ROOT/'repository-navigation-pre-anchor-reuse-076.json'
assert not snapshot.exists();shutil.copy2(nav,snapshot)
data=load(nav);data.update(anchor_reuse_reader_report='ANCHOR_REUSE_076.md',anchor_reuse_evidence_method='private Git repository blob',updated_at_utc=now());save(nav,data)
result={'first_two_release_cli_and_third_binary_api_upload_http500_preserved':True,'all_three_remote_queries_found_no_new_attempt_asset':True,
        'all122_previous_asset_bytes_digests_and_recorded_ids_verified':True,'no_clobber_or_asset_delete_used':True,
        'full_verified_archive_and_sidecar_copied_to_private_repository':True,'repository_artifacts':repo_artifacts,
        'original_archive_and_preserved_qualification_payload_unchanged':True,'no_native_or_timed_case_rerun':True,
        'release_asset_upload_pending':True,'git_remote_commit_verification_follows_push':True}
save(D/'completion.json',result)
p=ROOT/'ANCHOR_REUSE_076.md';text=p.read_text(encoding='utf-8')
note='\nComplete private repository evidence:\n\n'+''.join('- ['+a['repository_path'].split('/')[-1]+']('+a['repository_path']+').\n' for a in repo_artifacts)
note+='\nTwo gh release uploads and one direct binary API upload returned HTTP 500. Each authoritative remote query found no new asset and verified all 122 older assets. The complete unchanged ZIP and sidecar are therefore preserved directly through private Git storage; the separate release-asset upload remains pending. [Failure/recovery evidence](benchmarks/anchor-reuse-076-finalization/completion.json), raw upload logs and recovery helper sources are retained. The original archive/source/binary/policy/raw/fixture evidence is unchanged; no observed case was rerun. These finalization files and archive links are repository additions after the immutable ZIP. All 20 supported engine releases/tags stay unchanged.\n'
assert note not in text;p.write_text(text+note,encoding='utf-8')
print(json.dumps({'prepared_git_artifacts':repo_artifacts,'release_assets_unchanged':122,'release_upload_pending':True}))
