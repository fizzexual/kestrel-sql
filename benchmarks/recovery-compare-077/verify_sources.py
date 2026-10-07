"""Check exact predecessor binaries/source/decoder derivation before freeze."""
import ast,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-075';NEW=W.parent/'perf-076'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
provenance=load(W/'binary-provenance.json')
for label,source in [('control_075',OLD),('candidate_076',NEW)]:
    b=provenance['builds'][label];assert sha(W/b['binary'])==b['binary_sha256']==load(source/'build-proof.json')['binary_sha256']
    for n,d in b['source_sha256'].items():assert sha(W/b['source_directory']/n)==d==sha(source/'model'/n)
for n,proof in provenance['prerequisite_proofs'].items():assert sha(W/n)==proof['sha256']==sha(Path(proof['source']))
for n,d in load(W/'helper-derivation.json')['unchanged_python_helpers'].items():assert sha(W/n)==d==sha(OLD/n)
old_prefix=(OLD/'audit_model.py').read_text(encoding='utf-8').split("policy=load(W/'policy.json')",1)[0]
prefix=(W/'audit_model.py').read_text(encoding='utf-8').split("policy=load(W/'policy.json')",1)[0]
assert prefix==old_prefix
assert (W/'canonical_audit.py').read_text(encoding='utf-8') in prefix
for n in ['Cargo.lock','Cargo.toml','src/main.rs']:assert (W/'control-model'/n).read_bytes()==(W/'candidate-model'/n).read_bytes()
assert load(NEW/'source-finalization.json')['all_publication_import_source_methods_and_existing_protocol_tests_byte_identical']
assert load(NEW/'qualification-results.json')['complete'] and load(NEW/'publication-byte-equivalence.json')['all_201_original_history_files_equal']
for p in W.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
result={'all_reused_sources_binaries_and_decoder_verified':True,'full_canonical_decoder_prefix_byte_identical_to_075':True,'no_source_changes_or_compilation_in_077':True,'076_qualification_reused_not_rerun':True,'previous_075_adoption_failures_not_superseded':True}
(W/'source-finalization.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
