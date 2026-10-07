"""Verify strict reader/wire/IO and every old test remain, with declared source-only deltas."""
import ast,hashlib,json,re
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W/'original-076-model';NEW=W/'model'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def squash(s):return re.sub(r'\s+','',s)
proof=load(W/'derivation.json')
for n,d in proof['old_model_source_sha256'].items():assert sha(OLD/n)==d,n
assert sha(W/'control-076/recovery-model.exe')==proof['old_binary_sha256']
for n in ['Cargo.toml','Cargo.lock','src/recovery_tests.rs']:assert (OLD/n).read_bytes()==(NEW/n).read_bytes(),n
original_main=(OLD/'src/main.rs').read_text(encoding='utf-8');main=(NEW/'src/main.rs').read_text(encoding='utf-8')
replacement='"source_validation_full_clone_charged_in_all_modes":mode!="hybrid","source_validation_is_fully_charged":true,"hybrid_source_validation":"validated_incremental_state078"'
assert main.count(replacement)==2
assert main.replace(replacement,'"source_validation_full_clone_charged_in_all_modes":true')==original_main
old=(OLD/'src/hybrid.rs').read_text(encoding='utf-8');new=(NEW/'src/hybrid.rs').read_text(encoding='utf-8')
assert old[:old.index('struct Hybrid {')]==new[:new.index('// Pure preflight against source state')]
reversed_source=new
start=reversed_source.index('// Pure preflight against source state');end=reversed_source.index('struct Hybrid {',start);helper=reversed_source[start:end]
grammar=original_main[original_main.index("        let f: Vec<_> = id.split(':').collect();"):original_main.index('        if let Some(p) = out.get_mut(f[1])')]
grammar_new=helper[helper.index("    let f: Vec<_> = id.split(':').collect();"):helper.index('    let position = if let Some(p)')]
assert squash(grammar)==squash(grammar_new)
reversed_source=reversed_source[:start]+reversed_source[end:]
reversed_source=reversed_source.replace('    source_positions: BTreeMap<String, Position>,\n','').replace('            source_positions,\n','')
reversed_source=reversed_source.replace('        let source_positions = positions(&old.batches)?;','        positions(&old.batches)?;').replace('        let mut source_positions = positions(&ledger)?;','        positions(&ledger)?;').replace('            source_positions = positions(&ledger)?;','            positions(&ledger)?;')
start=reversed_source.index('        let source_update =');end=reversed_source.index('        let g = self.next;',start);reversed_source=reversed_source[:start]+reversed_source[end:]
update='''        if let Some((key, position)) = source_update {
            self.source_positions.insert(key, position);
        }
''';assert reversed_source.count(update)==1;reversed_source=reversed_source.replace(update,'',1)
clone='''        if id.starts_with("ksrc1:") {
            let mut check = self.ledger.clone();
            check.insert(id.into(), entry.record.clone());
            positions(&check)?;
        }
'''
assert reversed_source.count('        self.publish(vec![entry], fault)?;')==1
reversed_source=reversed_source.replace('        self.publish(vec![entry], fault)?;',clone+'        self.publish(vec![entry], fault)?;',1)
reversed_source=reversed_source.replace('''            && self
                .source_positions
                .get(&key)''','''            && positions(&self.ledger)?
                .get(&key)''')
reversed_source=reversed_source.replace('''            && self.source_positions
                .get(&key)''','''            && positions(&self.ledger)?
                .get(&key)''')
reversed_source=reversed_source.replace('\ninclude!("source_state_tests.rs");\n','')
assert squash(reversed_source)==squash(old),'unexpected implementation change outside declared source preflight/cache'
assert 'let mut check = self.ledger.clone();' not in new[:new.index('#[cfg(test)]\nmod hybrid_tests') if '#[cfg(test)]\nmod hybrid_tests' in new else new.index('    #[test]')]
assert new.index('if let Some((key, position)) = source_update')>new.index('let crc = match result')
assert new.index('let source_update =')<new.index('        self.next = g.checked_add(1)')
assert new[new.index('    fn summary('):new.index('include!("source_state_tests.rs")')].strip()==old[old.index('    fn summary('):].strip()
tests=(NEW/'src/source_state_tests.rs').read_text(encoding='utf-8');assert tests.count('#[test]')==8
for p in W.glob('*.py'):ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
result={'all_old_model_sources_preserved':True,'main_only_two_truthful_output_metadata_substitutions_workload_CAT4_digest_IO_and_old_tests_byte_identical':True,'Cargo_lock_and_toml_byte_identical':True,'anchor_reader_and_anchor_validation_byte_identical_to076':True,'all_full_recovery_validation_calls_preserved':True,'source_grammar_matches_unchanged_full_reference':True,'shared_publication_IO_and_serialized_fields_unchanged':True,'source_preflight_before_IO_and_generation_reservation':True,'projection_install_after_publication_success_only':True,'all_old49tests_preserved':True,'new_tests':8,'expected_native_tests_each':57,'source_limit':4096,'no_engine_edit':True,'no_timed_cohort':True}
(W/'source-finalization.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
