"""Add only post-package remote-verification tooling; immutable078 payload stays frozen."""
import ast,hashlib,json,shutil
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';D=ROOT/'benchmarks/source-state-078-finalization'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
bundle=json.loads((ROOT/'benchmarks/source-state-078-bundle-check.json').read_text(encoding='utf-8'))
assert bundle['parts']==3 and bundle['all_full_fixtures_bundled']
assert not D.exists();D.mkdir()
sources={}
for n in ['verify_git_remote.py','finalize_repository.py']:
    ast.parse((W/n).read_text(encoding='utf-8'),filename=n);shutil.copy2(W/n,D/n);assert sha(D/n)==sha(W/n);sources[n]=sha(D/n)
(D/'finalization-proof.json').write_text(json.dumps({'added_after_immutable_packages':True,'source_sha256':sources,'complete_archive_parts':3,'all_original_primary_payload_source_binary_policy_results_and_fixtures_unchanged':True,'purpose':'post-push remote blob/catalog verification, not a workload or candidate change','no_native_or_timed_rerun':True},indent=2)+'\n',encoding='utf-8')
p=ROOT/'SOURCE_STATE_078.md';p.write_text(p.read_text(encoding='utf-8')+'\n[Post-package remote verifier](benchmarks/source-state-078-finalization/verify_git_remote.py) and [addition proof](benchmarks/source-state-078-finalization/finalization-proof.json) are repository-only additions after the three immutable ZIPs. They check matching local/remote main, archive and sidecar blob SHA/size, private repository status, unchanged older release digests/tags, supported core and the frozen morning report. They introduce no native or timed workload and do not change the original qualification payload.\n',encoding='utf-8')
print(json.dumps({'post_package_helpers_added':True,'sources':sources}))
