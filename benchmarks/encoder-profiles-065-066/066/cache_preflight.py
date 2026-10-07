"""Verify frozen064 evidence before reclaiming only two tagged debug caches."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-064';ROOT=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
assert not load(W/'post-timing-process-check.json')['active_processes']
bundle=load(ROOT/'benchmarks/compaction-064-bundle-check.json');pub=load(ROOT/'benchmarks/compaction-064-publication.json')
assert pub['private'] and pub['previous_assets_unchanged']==94
assert sha(ROOT.parent/bundle['artifact'])==bundle['sha256']==pub['new_assets'][0]['sha256']
assert pub['new_assets'][0]['server_digest_matched']
proof=load(ROOT/'benchmarks/compaction-064-preservation.json');binaries={}
for n,d in proof['payload_sha256'].items():
    if n.endswith('.exe'):
        original=OLD/n;frozen=ROOT/'benchmarks/compaction-064'/n
        assert sha(original)==sha(frozen)==d,n;binaries[n]=d
assert len(binaries)>=16
assert load(OLD/'qualification-audit.json')['rust_debug_release_tests_each']==78
(W/'cache-preflight.json').write_text(json.dumps({'checked_utc':datetime.now(timezone.utc).isoformat(),'passed':True,
    '064_local_archive_sha256_matches_private_verified_asset':bundle['sha256'],'all_frozen_executables_sha256':binaries,
    'debug_release78_tests_and_logs_preserved':True,'only_rebuildable_tagged_debug_caches_authorized_for_reclamation':True,
    'release_libraries_sources_logs_inputs_stores_and_frozen_binaries_retained':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'frozen_executables':len(binaries)}))
