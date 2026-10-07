"""Preserved077 verifier-schema correction; frozen timing policy/payload stay unchanged."""
import ast,hashlib,json,shutil,sys
from pathlib import Path
W=Path(__file__).resolve().parent;ROOT=W.parents[1]/'outputs/kestrel-sql';D=ROOT/'benchmarks/recovery-compare-077-finalization'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
source=W/'maintain_evidence.py';original=source.read_text(encoding='utf-8');proof=load(ROOT/'benchmarks/recovery-compare-077-preservation.json')
assert hashlib.sha256(source.read_bytes()).hexdigest()==proof['payload_sha256']['maintain_evidence.py']
substitutions={"actual[k]['id']==a['asset_id']":"('asset_id' not in a or actual[k]['id']==a['asset_id'])","all122_asset_sizes_digests_and_ids_match":"all122_asset_sizes_digests_and_recorded_ids_match","all_three_archive_crc_member_sha_and_disjoint_inventory_verified":"all_six_archive_crc_member_sha_and_disjoint_inventory_verified"}
text=original[:original.index('assert len(sys.argv)==2')]
for old,new in substitutions.items():assert text.count(old)==1; text=text.replace(old,new)
ns={'__file__':str(source),'__name__':'corrected_preservation_contract'};exec(compile(text,str(source),'exec'),ns)
def prepare():
    (D/'initial-catalog-verifier-failure.txt').write_text('First private077 preparation stopped before any artifact copy or publication mutation: KeyError asset_id. Older publication records preserve name/bytes/SHA/download URL but omit optional asset IDs. The corrected in-memory verifier still requires all122 remote sizes/digests and unchanged20 tags, and compares every recorded asset ID when present. No assertion on recorded IDs is dropped. Original maintainer and failed output are retained. No native/timed rerun.\n',encoding='utf-8')
    save(D/'verifier-schema-correction.json',{'original_archived_maintainer_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'only_in_memory_metadata_substitutions':substitutions,'all_old_frozen_raw_fixture_archive_baseline_and_guard_checks_kept':True,'benchmark_policy_unchanged':True,'recorded_release_asset_ids':sum('asset_id' in a for r in load(ROOT/'repository-publication.json')['releases'] for a in r['assets']),'all_release_digests_still_required':122})
    adapter={'__file__':str(W/'finalize_evidence.py'),'__name__':'preservation_adapter'};exec(compile((W/'finalize_evidence.py').read_text(encoding='utf-8'),str(W/'finalize_evidence.py'),'exec'),adapter);adapter['ns']=ns
    adapter['prepare_git']()
    nav=load(ROOT/'repository-navigation-audit.json');nav['recovery_comparison_evidence_method']='six disjoint complete private Git ZIPs plus byte-exact oversized draft chunks';save(ROOT/'repository-navigation-audit.json',nav)
    p=ROOT/'RECOVERY_COMPARE_077.md';content=p.read_text(encoding='utf-8')+'\n[Post-package verifier correction](benchmarks/recovery-compare-077-finalization/verifier-schema-correction.json) preserves the optional-ID catalog failure and checks all122 release sizes/digests plus every recorded ID. These additional finalization records are repository-only additions after the immutable archives. The frozen timing policy, all observations and original maintainer payload remain unchanged.\n';p.write_text(content,encoding='utf-8')
    shutil.copyfile(W/'complete_publication.py',D/'complete_publication.py')
    ast.parse((D/'complete_publication.py').read_text(encoding='utf-8'))
if __name__=='__main__':
    assert len(sys.argv)==2
    {'--prepare':prepare,'--verify':ns['verify']}[sys.argv[1]]()
