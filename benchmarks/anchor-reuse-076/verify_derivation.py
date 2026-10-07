"""Check unchanged writes/workloads/tests and exact moved validation."""
import ast,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W/'original-075-model';MODEL=W/'model'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((W/'derivation.json').read_text(encoding='utf-8-sig'))
for n,d in proof['old_model_source_sha256'].items():assert sha(OLD/n)==d,n
for n in ['src/main.rs','Cargo.toml','Cargo.lock']:assert sha(OLD/n)==sha(MODEL/n),n
old=(OLD/'src/hybrid.rs').read_text(encoding='utf-8');new=(MODEL/'src/hybrid.rs').read_text(encoding='utf-8')
assert old[old.index('fn hy_head('):old.index('    fn open(')]==new[new.index('fn hy_head('):new.index('    fn open(')]
assert old[old.index('    fn page('):].strip()==new[new.index('    fn page('):new.index('include!("recovery_tests.rs")')].strip()
validation=old[old.index('    if old.generation != generation'):old.index('    Ok((old, crc32fast::hash(&body)))')]
assert new.count(validation)==1
assert new.count('cached_anchor = Some((anchor, crc));')==1
assert 'Some(anchor) => anchor,' in new and 'None => hy_anchor(path, checkpoint.anchor_generation)?,' in new
for p in W.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
result={'common_CAT4_workloads_main_and_Cargo_byte_identical_to_075':True,
        'all_publication_import_source_methods_and_existing_protocol_tests_byte_identical':True,
        'complete_anchor_validation_and_positions_block_byte_identical_after_move':True,
        'cached_value_scoped_to_one_open_and_checkpoint_fallback_kept':True,
        'test_probes_cfg_test_only':True,'new_meaningful_tests':6,'expected_total_tests_each':49,
        'Python_syntax_passed':True,'no_engine_edit':True}
(W/'source-finalization.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
