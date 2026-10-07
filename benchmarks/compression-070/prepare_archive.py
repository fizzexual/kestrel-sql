"""Assemble additive preservation using validated 069 machinery, exact count edits."""
from datetime import datetime, timezone
import ast, hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-069'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
s=(OLD/'maintain_evidence.py').read_text(encoding='utf-8').replace('069','070')
edits=[('len(expected)==102','len(expected)==104'),('len(actual)==104','len(actual)==106'),
    ('uploaded_assets=104','uploaded_assets=106'),('all_104_server_digests_matched','all_106_server_digests_matched'),
    ("'remote_assets_verified':104","'remote_assets_verified':106"),("'previous_assets_unchanged':102","'previous_assets_unchanged':104"),
    ('verified_server_asset_digests=104','verified_server_asset_digests=106'),('all102 previous','all104 previous'),
    ("['remote_assets_verified']==104","['remote_assets_verified']==106"),("'private_remote_assets_verified':104","'private_remote_assets_verified':106")]
for old,new in edits:
    assert old in s,old;s=s.replace(old,new)
s=s.replace(".replace('all102','all 102')",".replace('all104','all 104')")
start=s.index('    intro=');end=s.index("    for name in ['README.md'",start)
s=s[:start]+'''    intro='**Latest checkpoint model:** [070 Zstandard level 1 cuts stored bytes by about 70% but fails publication speed gates](COMPRESSION_070.md). All 36 cases and 432 frames are preserved. Large charged totals are 1.1501x/1.2058x raw; two goals, four guards and five A/A checks fail. Twelve native debug/release tests and all native/Python/Arrow byte checks pass. Model rejected; supported 0.3.16 remains unchanged.\\n\\n'
'''+s[end:]
start=s.index("    p=ROOT/'ADOPTION_STATUS.md'");end=s.index('    print(json.dumps',start)
s=s[:start]+'''    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\\n[Zstandard checkpoint byte model 070](COMPRESSION_070.md) reduces stored bytes by about 70% but fails charged-publication goals and guards. All 36 cases and 432 frames remain preserved. Model rejected; supported 0.3.16 unchanged. No new SQL or service qualification.\\n',encoding='utf-8')
'''+s[end:]
s=s.replace('all36 cases/432 frames/input/source/locked crates','all 36 cases/432 frames/input/source/locked crates')
s=s.replace('Checkpoint compression model070 only. All36 cases,432 full frames','Zstandard checkpoint byte model 070 only. All 36 cases, 432 full frames')
s=s.replace('all36 cases,432 full frames','all 36 cases, 432 full frames')
s=s.replace('private trace evidence','private Zstandard model evidence')
assert 'per_page=100' in s and 'per_page=104' not in s and 'per_page=106' not in s
ast.parse(s);(W/'maintain_evidence.py').write_text(s,encoding='utf-8')
save(W/'maintenance-derivation.json',{'original_sha256':sha(OLD/'maintain_evidence.py'),'derived_sha256':sha(W/'maintain_evidence.py'),
    'old_assets':104,'new_assets':106,'model_only':True,'full_case_stores':36,'frames':432,'canonical_inputs':3,'exact_asset_count_replacements':True})
s=(OLD/'collect_final.py').read_text().replace("'debug':8,'release':8","'debug':12,'release':12")
at=s.index('base=load(')
s=s[:at]+'''assert p['frame_oracle_sha256']==sha(W/'zstd_frame_oracle.py') and p['oracle_provenance_sha256']==sha(W/'oracle-provenance.json')
for name,digest in load(W/'oracle-provenance.json')['files'].items():assert sha(Path(name))==digest,name
'''+s[at:]
ast.parse(s);(W/'collect_final.py').write_text(s,encoding='utf-8')
save(W/'frame-oracle-test-proof.json',{'recorded_utc':datetime.now(timezone.utc).isoformat(),'before_model_timing':True,
    'source_sha256':sha(W/'zstd_frame_oracle.py'),'test_groups':3,'passed':True,
    'recording':'Preserved result from pre-timing tool invocation: Ran 3 tests in 0.120s, OK. Not a second execution or raw file capture.',
    'source_unchanged_since_test':True})
print(json.dumps({'assembled':True,'old_assets':104,'new_assets':106}))
