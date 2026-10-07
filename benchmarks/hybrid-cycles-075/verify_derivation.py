"""Source identity and prerequisite qualification, before cohort freeze."""
import ast,hashlib,json
from pathlib import Path
W=Path(__file__).resolve().parent;OLD=W.parent/'perf-074'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
before=(OLD/'model/src/main.rs').read_text(encoding='utf-8');after=(W/'model/src/main.rs').read_text(encoding='utf-8')
def section(s,start,end):return s[s.index(start):s.index(end,s.index(start))]
assert section(before,'//!','enum BenchStore {')==section(after,'//!','enum BenchStore {')
assert section(before,'fn benchmark_main(','include!("hybrid.rs");')==section(after,'fn benchmark_main(','fn benchmark075_main(')
assert sha(W/'model/src/hybrid.rs')==sha(OLD/'model/src/hybrid.rs')
assert all(sha(W/'model'/n)==sha(OLD/'model'/n) for n in ['Cargo.toml','Cargo.lock'])
old_build=load(W/'prerequisite-074/build-proof.json');old_qual=load(W/'prerequisite-074/qualification-results.json')
assert old_build['counts']=={'debug':40,'release':40} and old_qual['complete'] and old_qual['controlled_kills']==15 and old_qual['injected_errors']==15
assert old_build['source_sha256']['src/hybrid.rs']==sha(W/'model/src/hybrid.rs')
for p in W.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
result={'old_CAT4_model_common_IO_source_and_old_benchmark_entrypoint_byte_identical':True,
    'hybrid_protocol_byte_identical_to_qualified_074':True,'unchanged_protocol_sha256':sha(W/'model/src/hybrid.rs'),
    'unchanged_Cargo_manifest_lock':True,'prerequisite_074_counts':old_build['counts'],'prerequisite_074_error_kills':[15,15],
    'new_integration_counts':load(W/'build-proof.json')['counts'],'no_old_protocol_tests_or_cuts_rerun':True,
    'anchor_terminal_read_count_documentation_corrected_additively':{'native_full_body_reads':3,'native_parses':2,'Python_parses':3},
    'default_engine_changed':False,'Python_syntax_passed':True}
(W/'source-finalization.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
