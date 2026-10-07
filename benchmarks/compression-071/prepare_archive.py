"""Additive four-part preservation; keep old raw evidence and reports immutable."""
import ast, hashlib, json
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-070'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
s=(OLD/'maintain_evidence.py').read_text().replace('070','071')
s=s.replace('(36,432,3)','(54,648,3)')
start=s.index('    intro=');end=s.index("    for name in ['README.md'",start)
s=s[:start]+'''    intro='**Latest checkpoint model and benchmark correction:** [071 uses verified balanced order; fast Zstandard still fails adoption gates](COMPRESSION_071.md). All 54 cases and 648 frames are preserved. Read the [069/070 order correction](MODEL_ORDER_AUDIT_071.md): their size rotation cancelled variant rotation. Original reports/raw evidence remain unchanged. In 071, large bytes fall about 46%, but two goals, five guards and four A/A checks fail. Supported 0.3.16 remains unchanged.\\n\\n'
'''+s[end:]
start=s.index("    p=ROOT/'ADOPTION_STATUS.md'");end=s.index('    print(json.dumps',start)
s=s[:start]+'''    p=ROOT/'ADOPTION_STATUS.md';p.write_text(p.read_text(encoding='utf-8')+'\\n[Balanced fast-Zstandard model 071](COMPRESSION_071.md) fails both speed goals and five guards; four calibration checks fail. All 54 cases/648 frames remain preserved. The [069/070 order correction](MODEL_ORDER_AUDIT_071.md) documents their fixed per-size variant order, without rewriting their raw results. No engine integration or supported promotion.\\n',encoding='utf-8')
'''+s[end:]
start=s.index('def package():');end=s.index('def gh(*args):',start)
replacement=(W/'archive_operations.txt').read_text(encoding='utf-8')
s=s[:start]+replacement+s[end:]
start=s.index('def publish():');end=s.index('def verify():',start)
s=s[:start]+(W/'publish_operations.txt').read_text(encoding='utf-8')+s[end:]
s=s.replace("bundle=load(ROOT/'benchmarks/compression-071-bundle-check.json');assert sha(ROOT.parent/bundle['artifact'])==bundle['sha256']", "bundle=load(ROOT/'benchmarks/compression-071-bundle-check.json')\n    for part in bundle['artifacts']:assert sha(ROOT.parent/part['artifact'])==part['sha256']")
s=s.replace("['remote_assets_verified']==106","['remote_assets_verified']==114").replace("'private_remote_assets_verified':106","'private_remote_assets_verified':114")
s=s.replace("for name in [REPORT,'README.md'", "for name in [REPORT,'MODEL_ORDER_AUDIT_071.md','README.md'")
assert 'per_page=100' in s and 'per_page=106' not in s and 'per_page=114' not in s
ast.parse(s);(W/'maintain_evidence.py').write_text(s,encoding='utf-8')
(W/'maintenance-derivation.json').write_text(json.dumps({'original_sha256':sha(OLD/'maintain_evidence.py'),'derived_sha256':sha(W/'maintain_evidence.py'),
    'old_assets':106,'new_assets':114,'model_only':True,'full_case_stores':54,'frames':648,'canonical_inputs':3,
    'four_parts':'core+inputs, raw A, raw B, compressed frames; exact disjoint payload union verified'},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'assembled':True,'old_assets':106,'new_assets':114,'bundle_parts':4}))
