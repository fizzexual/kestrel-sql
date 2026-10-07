"""Verify exact binaries, workload derivation and qualified prerequisites."""
import ast,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parent; OLD=W.parent/'perf-076'; NEW=W.parent/'perf-078'; PREV=W.parent/'perf-077'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
provenance=load(W/'binary-provenance.json')
for label,source in [('control_076',OLD),('candidate_078',NEW)]:
    b=provenance['builds'][label]
    assert sha(W/b['binary'])==b['binary_sha256']==load(source/'build-proof.json')['binary_sha256']
    for n,d in b['source_sha256'].items():assert sha(W/b['source_directory']/n)==d==sha(source/'model'/n)
for n,proof in provenance['prerequisite_proofs'].items():assert sha(W/n)==proof['sha256']==sha(Path(proof['source']))
for n,d in load(W/'helper-derivation.json')['unchanged_python_helpers'].items():assert sha(W/n)==d==sha(PREV/n)
old_prefix=(PREV/'audit_model.py').read_text(encoding='utf-8').split("policy=load(W/'policy.json')",1)[0]
prefix=(W/'audit_model.py').read_text(encoding='utf-8').split("policy=load(W/'policy.json')",1)[0]
assert prefix==old_prefix and (W/'canonical_audit.py').read_text(encoding='utf-8') in prefix
for n in ['Cargo.lock','Cargo.toml','src/recovery_tests.rs']:assert (W/'control-model'/n).read_bytes()==(W/'candidate-model'/n).read_bytes()
old=(W/'control-model/src/main.rs').read_text(encoding='utf-8'); new=(W/'candidate-model/src/main.rs').read_text(encoding='utf-8')
original='"source_validation_full_clone_charged_in_all_modes":true'
replacement='"source_validation_full_clone_charged_in_all_modes":mode!="hybrid","source_validation_is_fully_charged":true,"hybrid_source_validation":"validated_incremental_state078"'
assert new.count(replacement)==2 and new.replace(replacement,original)==old
proof=load(NEW/'source-finalization.json')
for key in ['main_only_two_truthful_output_metadata_substitutions_workload_CAT4_digest_IO_and_old_tests_byte_identical','anchor_reader_and_anchor_validation_byte_identical_to076','all_full_recovery_validation_calls_preserved','shared_publication_IO_and_serialized_fields_unchanged','all_old49tests_preserved']:assert proof[key]
q=load(NEW/'qualification-results.json')
assert q['complete'] and q['controlled_kills']==15 and q['injected_errors']==15 and q['independent_corruption_cases_rejected']==30
assert load(NEW/'publication-byte-equivalence.json')['all_201_original_history_files_equal']
assert load(BASE_FINAL:=W.parent/'perf-078-finalization/git-publication-check.json')['complete']
for p in W.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
result={'all_reused_sources_binaries_and_decoder_verified':True,'full_canonical_decoder_prefix_byte_identical_to_077':True,'main_only_two_truthful_output_metadata_substitutions':True,'no_source_changes_or_compilation_in_079':True,'078_qualification_reused_not_rerun':True,'previous_075_and_077_adoption_failures_not_superseded':True}
(W/'source-finalization.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
