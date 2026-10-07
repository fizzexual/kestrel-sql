"""Use gh's supported binary request body after two verified empty outcomes."""
import hashlib,json,subprocess,sys
from urllib.parse import quote
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';D=ROOT/'benchmarks/anchor-reuse-076-finalization'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert load(D/'publication-attempt-2-status.json')['exit']==1
assert load(D/'remote-state-after-second-500.json')['new_attempt_asset_state']==[]
release=json.loads(subprocess.check_output(['gh','api','repos/fizzexual/kestrel-sql/releases/tags/v0.3.16'],text=True,encoding='utf-8'))
endpoint=release['upload_url'].split('{')[0]
assert release['id']==405218650 and endpoint=='https://uploads.github.com/repos/fizzexual/kestrel-sql/releases/405218650/assets'
bundle=load(ROOT/'benchmarks/anchor-reuse-076-bundle-check.json');archive=ROOT.parent/bundle['artifact']
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==bundle['sha256']
argv=['gh','api',endpoint+'?name='+quote(archive.name,safe=''),'--method','POST','--input',str(archive),'--header','Content-Type: application/zip']
r=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',timeout=120)
(D/'publication-attempt-3-api.stdout').write_text(r.stdout,encoding='utf-8')
(D/'publication-attempt-3-api.stderr').write_text(r.stderr,encoding='utf-8')
status={'argv':argv,'exit':r.returncode,'same_verified_zip':True,'previous_assets_never_replaced':True,'remote_checked_before_request':True}
(D/'publication-attempt-3-api-status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
if r.returncode:print(r.stderr);sys.exit(r.returncode)
asset=json.loads(r.stdout);assert asset['size']==archive.stat().st_size and asset['digest']=='sha256:'+bundle['sha256']
print(json.dumps({'api_archive_uploaded':True,'asset_id':asset['id'],'digest':asset['digest'],'bytes':asset['size']}),flush=True)
# Original idempotent completion verifies existing archive, uploads only missing sidecar.
r=subprocess.run([sys.executable,str(W/'maintain_evidence.py'),'--publish'],capture_output=True,text=True,encoding='utf-8')
(D/'publication-completion.stdout').write_text(r.stdout,encoding='utf-8')
(D/'publication-completion.stderr').write_text(r.stderr,encoding='utf-8')
(D/'publication-completion-status.json').write_text(json.dumps({'exit':r.returncode,'archive_not_reuploaded':True,'no_clobber_used':True},indent=2)+'\n',encoding='utf-8')
print(r.stdout);print(r.stderr);sys.exit(r.returncode)
