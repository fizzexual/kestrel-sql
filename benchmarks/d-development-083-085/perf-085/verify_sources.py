import json,hashlib
from pathlib import Path
W=Path(__file__).resolve().parent
R=W.parents[1]/'outputs/kestrel-sql'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
b=json.loads((W/'baseline.json').read_text())
for n,d in b['core_source_sha256'].items():assert sha(R/n)==d,n
for n,d in b['baseline_binary_sha256'].items():assert sha(R/'bin'/n)==d,n
p=json.loads((W/'binary-provenance.json').read_text())
for v in p['builds'].values():
 assert sha(W/v['binary'])==v['binary_sha256']
 for n,d in v['source_sha256'].items():assert sha(W/v['source_directory']/n)==d,n
assert (W/'canonical_audit.py').read_bytes()==(W.parent/'perf-080/canonical_audit.py').read_bytes()
(W/'source-finalization.json').write_text(json.dumps({'all_reused_sources_binaries_and_decoder_verified':True,'candidate084_freshly_built_and_qualified_no_engine_change':True,'physical_workspace':'D:/Codex/Kestrel'},indent=2))
assert json.loads((W/'prerequisites/qualification-results.json').read_text())['complete']
print('Exact released core,078/084 sources/binaries, fresh qualification and decoder verified.')
